"""One sealed final evaluation. Never use its results to choose the deployed model."""
import json,hashlib,subprocess,time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoTokenizer
from torch.utils.data import DataLoader
from safetensors.torch import load_file
from dataset import ROOT,load_rows,Pairs,collate
from model import MeaningModel
from train import predict
from evaluation import metrics,bootstrap
from frozen_baseline import embeddings

def main():
    out=ROOT/'results/final-evaluation.json'
    if out.exists():raise RuntimeError('Final evaluation already exists. Preserve it; do not retune against this test.')
    cfg=json.loads((ROOT/'configs/pilot.json').read_text());torch.set_num_threads(6)
    names=[f'{v}-seed{s}' for s in cfg['seeds'] for v in ['ordinary','scope']]+['frozen']
    seal={}
    for name in names:
        d=ROOT/'checkpoints'/name
        seal[name]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [d/'config.json',d/'calibration.json',d/('heads.npz' if name=='frozen' else 'trained.safetensors')]}
    # Record frozen model identities before opening the test split.
    (ROOT/'results/evaluation-seal.json').write_text(json.dumps(seal,indent=2),encoding='utf-8')
    tokenizer=AutoTokenizer.from_pretrained(cfg['model'],local_files_only=True)
    original=load_rows('test',allow_test=True);data=Pairs(original,tokenizer,cfg['max_length']);rows=data.rows
    device='cuda' if torch.cuda.is_available() else 'cpu';report={'protocol':'PROTOCOL.md','test_rows':len(rows),'excluded_long':data.excluded_long,'models':{},'limitations':['Only three held-out natural documents; broad confidence intervals expected.','Conditional class has no test positives. Natural MQM taxonomy does not resolve every semantic category.','Span metrics measure token overlap, not explanation faithfulness.','No external COMET/xCOMET baseline executed. No independent annotation agreement measured.']}
    predictions={}
    def summarize(logits,y,cal,spans=None):
        result=metrics(y,logits,cal['temperature'],cal['thresholds']);result['bootstrap']=bootstrap(rows,y,logits,cfg['bootstrap_samples']);result['subsets']={}
        for source in sorted({r['source'] for r in rows}):
            mask=np.array([r['source']==source for r in rows]);result['subsets'][source]=metrics(y[mask],logits[mask],cal['temperature'],cal['thresholds'])
        for key in ['system','domain']:
            for value in sorted({r[key] for r in rows}):
                mask=np.array([r[key]==value for r in rows]);result['subsets'][key+':'+value]=metrics(y[mask],logits[mask],cal['temperature'],cal['thresholds'])
        for label,mask in [('scope_challenge',np.array([r['group'].startswith('scope-family') for r in rows])),('long_80_plus_tokens',np.array([len(e['input_ids'])>=80 for e in data.encoded]))]:
            if mask.any():result['subsets'][label]=metrics(y[mask],logits[mask],cal['temperature'],cal['thresholds'])
        groups={}
        for i,r in enumerate(rows):
            if r['source']=='authored_contrastive':groups.setdefault(r['japanese'],[]).append(i)
        contrast=[idx for idx in groups.values() if len(set(y[idx,0]))>1]
        result['contrastive']={'groups':len(contrast),'all_variants_correct_fraction':float(np.mean([np.all((logits[idx,0]>=0)==y[idx,0]) for idx in contrast])) if contrast else None}
        if spans:
            tp,fp,fn=[spans[k] for k in ['tp','fp','fn']];result['token_localization']={**spans,'precision':tp/max(1,tp+fp),'recall':tp/max(1,tp+fn),'f1':2*tp/max(1,2*tp+fp+fn),'threshold':.5}
        return result
    for name in names:
        d=ROOT/'checkpoints'/name;cal=json.loads((d/'calibration.json').read_text());started=time.perf_counter()
        model=MeaningModel(cfg['model'],0 if name=='frozen' else cfg['train_encoder_layers'])
        if name!='frozen':model.load_state_dict(load_file(str(d/'trained.safetensors')),strict=False)
        model.to(device).eval()
        if name=='frozen':
            heads=np.load(d/'heads.npz');h=embeddings(model,data,device);logits=((h-heads['mean'])/heads['std'])@heads['weights'].T+heads['intercepts'];y=np.array([e['labels'] for e in data.encoded]);spans=None
        else:logits,y,spans=predict(model,DataLoader(data,batch_size=8,collate_fn=collate),device)
        report['models'][name]=summarize(logits,y,cal,spans);report['models'][name]['seconds']=time.perf_counter()-started
        predictions[name]=(logits.copy(),cal)
        np.savez_compressed(ROOT/f'results/{name}-test.npz',logits=logits,labels=y)
        del model;torch.cuda.empty_cache()
        print(name,report['models'][name]['binary'],flush=True)
    # Original JS baseline and separately authored scope/deadline rules, same rows.
    script="const fs=require('fs');const {analyze}=require('./src/engine.cjs');const {analyzeRules}=require('./src/rules.cjs');const m=require('./model/baseline.json');const rows=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(rows.map(r=>({cue:analyze(r,m),rules:analyzeRules(r)}))));"
    baseline=json.loads(subprocess.run(['node','-e',script],input=json.dumps([{'japanese':r['japanese'],'english':r['english']} for r in rows]),text=True,encoding='utf-8',capture_output=True,check=True,cwd=ROOT.parent).stdout)
    from schema import LABELS
    for name in ['cue','rules']:
        logits=np.full(y.shape,-20.,dtype=float)
        for i,item in enumerate(baseline):
            findings=item[name]['findings'];logits[i,0]=20 if findings else -20
            for f in findings:
                if f['category'] in LABELS:logits[i,1+LABELS.index(f['category'])]=20
        report['models'][name]=summarize(logits,y,{'temperature':1,'thresholds':{'altered':.5,'preserved':-.01}})
        report['models'][name]['calibration']='Not calibrated; pseudo-logits encode rule decisions. Brier/ECE are not confidence estimates.'
        report['models'][name]['binary_decision_policy']='Forced binary comparison only: no finding is encoded as negative. Actual no-finding decisions abstain; see selective metrics for operational performance.'
    # A disagreement-only hybrid: rules can revoke a neural preserved decision,
    # but cannot promote an uncertain neural prediction into a confident one.
    from scipy.special import expit
    for name,(logits,cal) in predictions.items():
        p=expit(logits[:,0]/cal['temperature']);high=p>=cal['thresholds']['altered'];low=p<=cal['thresholds']['preserved']
        rules_flag=np.array([bool(item['rules']['findings']) for item in baseline]);low=low&~rules_flag;accepted=high|low
        report.setdefault('hybrid',{})[name]={'coverage':float(accepted.mean()),'selective_accuracy':float(((high==y[:,0])&accepted).sum()/max(1,accepted.sum())),'abstained':int((~accepted).sum()),'resolved_correct_fraction':float(((high==y[:,0])&accepted).mean())}
    # Evaluate the exact quantized graph distributed with the desktop app.
    import onnxruntime as ort
    deployed=ROOT.parent/'model/neural';manifest=json.loads((deployed/'manifest.json').read_text());options=ort.SessionOptions();options.intra_op_num_threads=4
    session=ort.InferenceSession(str(deployed/manifest['modelFile']),sess_options=options,providers=['CPUExecutionProvider']);values=[]
    for item in data:
        b=collate([item]);values.append(session.run(['logits'],{k:b[k].numpy() for k in ['input_ids','attention_mask','side_ids']})[0][0])
    report['models']['deployed-onnx']=summarize(np.array(values),y,manifest)
    for variant in ['ordinary','scope']:
        values=[report['models'][f'{variant}-seed{s}']['binary']['f1'] for s in cfg['seeds']]
        report.setdefault('across_seed',{})[variant]={'f1_mean':float(np.mean(values)),'f1_sample_std':float(np.std(values,ddof=1)),'seeds':cfg['seeds']}
    out.write_text(json.dumps(report,indent=2),encoding='utf-8');print('Final evaluation saved',flush=True)

if __name__=='__main__':main()
