"""Frozen contextual XLM-R embeddings + independently fitted logistic heads."""
import json
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from sklearn.linear_model import LogisticRegression
from dataset import ROOT,load_rows,Pairs,collate
from model import MeaningModel
from calibrate import fit_calibration

def embeddings(model,data,device):
    values=[]
    with torch.inference_mode():
        for b in DataLoader(data,batch_size=8,collate_fn=collate):
            _,_,_,h=model(*[b[k].to(device) for k in ['input_ids','attention_mask','side_ids']]);values.append(h.cpu().numpy())
    return np.concatenate(values)

def main():
    cfg=json.loads((ROOT/'configs/pilot.json').read_text());base=Path(cfg['model']).resolve();torch.set_num_threads(6)
    tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True);device='cuda' if torch.cuda.is_available() else 'cpu'
    model=MeaningModel(base,0).to(device).eval();out=ROOT/'checkpoints/frozen';out.mkdir(parents=True,exist_ok=True)
    data={split:Pairs(load_rows(split),tokenizer,cfg['max_length']) for split in ['train','validation','calibration']}
    features={split:embeddings(model,ds,device) for split,ds in data.items()}
    mean=features['train'].mean(0);std=features['train'].std(0).clip(min=.01)
    labels=np.array([e['labels'] for e in data['train'].encoded]);weights=[];intercepts=[]
    for i in range(labels.shape[1]):
        mask=labels[:,i]>=0;clf=LogisticRegression(C=.1,class_weight='balanced',max_iter=1000,random_state=17)
        clf.fit((features['train'][mask]-mean)/std,labels[mask,i]);weights.append(clf.coef_[0]);intercepts.append(clf.intercept_[0])
    weights=np.array(weights);intercepts=np.array(intercepts)
    np.savez_compressed(out/'heads.npz',weights=weights,intercepts=intercepts,mean=mean,std=std)
    for split in ['validation','calibration']:
        logits=((features[split]-mean)/std)@weights.T+intercepts;y=np.array([e['labels'] for e in data[split].encoded])
        np.savez_compressed(out/f'{split}.npz',logits=logits,labels=y)
        (out/f'{split}-ids.json').write_text(json.dumps([r['id'] for r in data[split].rows]),encoding='utf-8')
        if split=='calibration':(out/'calibration.json').write_text(json.dumps(fit_calibration(logits,y,cfg),indent=2),encoding='utf-8')
    (out/'config.json').write_text(json.dumps({'config':cfg,'variant':'frozen','seed':17,'architecture':'Frozen joint pair XLM-R embeddings (CLS + source/target mean) with standardized logistic heads; no encoder fine-tuning'},indent=2),encoding='utf-8')
    print('Saved frozen baseline',flush=True)

if __name__=='__main__':main()
