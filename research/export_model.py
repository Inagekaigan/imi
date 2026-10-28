"""Export trained heads + encoder to local CPU ONNX and verify quantization drift."""
import argparse,hashlib,json,shutil,time,tempfile
from pathlib import Path
import numpy as np
import torch
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic,QuantType
from safetensors.torch import load_file
from transformers import AutoTokenizer
from model import MeaningModel
from dataset import ROOT,load_rows,Pairs,collate
from schema import LABELS,TITLES

def export(checkpoint):
    directory=Path(checkpoint);meta=json.loads((directory/'config.json').read_text());cfg=meta['config'];base=Path(cfg['model']).resolve()
    calibration=json.loads((directory/'calibration.json').read_text());out=ROOT.parent/'model/neural';out.mkdir(parents=True,exist_ok=True)
    tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True);model=MeaningModel(base,cfg['train_encoder_layers']);model.load_state_dict(load_file(str(directory/'trained.safetensors')),strict=False);model.eval();torch.set_num_threads(6)
    sample=Pairs(load_rows('validation')[:3],tokenizer,cfg['max_length']);b=collate([sample[0]])
    float_path=ROOT/'cache/model.float.onnx';float_path.parent.mkdir(exist_ok=True)
    tempfile.tempdir=str(float_path.parent)
    inputs=tuple(b[k] for k in ['input_ids','attention_mask','side_ids'])
    torch.onnx.export(model,inputs,str(float_path),input_names=['input_ids','attention_mask','side_ids'],
       output_names=['logits','error_logits','scope_logits','pooled'],
       dynamic_axes={**{k:{0:'batch',1:'sequence'} for k in ['input_ids','attention_mask','side_ids']},'logits':{0:'batch'},'error_logits':{0:'batch',1:'sequence'},'scope_logits':{0:'batch',1:'sequence'},'pooled':{0:'batch'}},
       opset_version=17,dynamo=False)
    # Both uint8 trials exceeded the validation drift limit. Deploy verified FP32.
    shutil.copyfile(float_path,out/'model.onnx')
    shutil.copyfile(base/'tokenizer.json',out/'tokenizer.json')
    options=ort.SessionOptions();options.intra_op_num_threads=6
    session=ort.InferenceSession(str(out/'model.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    difference=[];timings=[]
    validation=Pairs(load_rows('validation')[:24],tokenizer,cfg['max_length'])
    for item in validation:
        b=collate([item]);feed={k:b[k].numpy() for k in ['input_ids','attention_mask','side_ids']}
        with torch.inference_mode():reference=model(*[b[k] for k in feed])[0].numpy()
        start=time.perf_counter();actual=session.run(['logits'],feed)[0];timings.append((time.perf_counter()-start)*1000);difference.append(float(np.max(np.abs(reference-actual))))
    manifest={'schemaVersion':2,'name':'Imi / XLM-R','version':'0.2.0','checkpoint':directory.name,'architecture':'XLM-RoBERTa base, top four encoder layers fine-tuned; binary, multi-label and error-span heads. Variant: '+meta['variant'],
      'labels':LABELS,'titles':TITLES,'maxTokens':cfg['max_length'],'temperature':calibration['temperature'],'thresholds':calibration['thresholds'],
      'calibrationWarning':calibration['warning'],'training':'MTPEdocs-MQM human annotations + authored contrastive data',
      'license':'Research use: MTPEdocs-MQM annotations are CC BY-NC-SA 4.0; pretrained XLM-R is MIT. See research/DATA_LICENSES.md.',
      'localOnly':True,'modelFile':'model.onnx','quantization':{'weightType':'float32','operators':[],'validationMaxLogitDifference':max(difference),'medianCpuMs':float(np.median(timings)),'rejectedTrials':{'uint8_matmul_gather_max_drift':2.184455394744873,'uint8_matmul_max_drift':1.931570053100586}},
      'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [out/'model.onnx',out/'tokenizer.json']},
      'trainingMetadata':meta,'calibrationMetrics':calibration['metrics_after']}
    # Quantization changes logits: calibrate the actual deployment graph separately.
    from calibrate import fit_calibration
    caldata=Pairs(load_rows('calibration'),tokenizer,cfg['max_length']);cal_logits=[];cal_labels=[]
    for item in caldata:
        b=collate([item]);cal_logits.append(session.run(['logits'],{k:b[k].numpy() for k in ['input_ids','attention_mask','side_ids']})[0][0]);cal_labels.append(item['labels'])
    deployed_cal=fit_calibration(np.array(cal_logits),np.array(cal_labels),cfg)
    manifest.update({'temperature':deployed_cal['temperature'],'thresholds':deployed_cal['thresholds'],'calibrationMetrics':deployed_cal['metrics_after']})
    (out/'calibration.json').write_text(json.dumps(deployed_cal,indent=2),encoding='utf-8')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps(manifest['quantization'],indent=2),flush=True)
    # Large drift is a failed export, never silently described as equivalent.
    if max(difference)>.75:raise RuntimeError('Quantization logit drift exceeds 0.75. Evaluate/repair before distribution.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('checkpoint');export(p.parse_args().checkpoint)
