import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch
from scipy.optimize import minimize_scalar
from scipy.special import expit
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from safetensors.torch import load_file
from dataset import load_rows,Pairs,collate,ROOT
from model import MeaningModel
from train import predict
from evaluation import metrics

def calibrate(checkpoint):
    directory=Path(checkpoint);metadata=json.loads((directory/'config.json').read_text());cfg=metadata['config'];base=Path(cfg['model']).resolve()
    tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True);data=Pairs(load_rows('calibration'),tokenizer,cfg['max_length'])
    model=MeaningModel(base,cfg['train_encoder_layers']);model.load_state_dict(load_file(str(directory/'trained.safetensors')),strict=False)
    device='cuda' if torch.cuda.is_available() else 'cpu';model.to(device);torch.set_num_threads(6)
    logits,y,_=predict(model,DataLoader(data,batch_size=8,collate_fn=collate),device)
    result=fit_calibration(logits,y,cfg)
    result.update({'calibration_ids':[r['id'] for r in data.rows],'excluded_long':data.excluded_long,
                   'checkpoint_sha256':hashlib.sha256((directory/'trained.safetensors').read_bytes()).hexdigest()})
    (directory/'calibration.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    np.savez_compressed(directory/'calibration.npz',logits=logits,labels=y)
    print(json.dumps({'checkpoint':str(directory),**{k:result[k] for k in ['temperature','thresholds','metrics_after']}},indent=2),flush=True)

def fit_calibration(logits,y,cfg):
    def objective(log_temperature):
        z=logits[:,0]/np.exp(log_temperature)
        return float(np.mean(np.logaddexp(0,z)-y[:,0]*z))
    optimization=minimize_scalar(objective,bounds=(-2.3,3),method='bounded')
    temperature=float(np.exp(optimization.x));p=expit(logits[:,0]/temperature);target=y[:,0]
    min_support=cfg['calibration_min_support'];precision=cfg['calibration_precision_target']
    high=1.01;low=-.01
    for t in np.arange(.5,1,.01):
        mask=p>=t
        if mask.sum()>=min_support and target[mask].mean()>=precision:high=float(t);break
    for t in np.arange(.49,0,-.01):
        mask=p<=t
        if mask.sum()>=min_support and (1-target[mask]).mean()>=precision:low=float(t);break
    thresholds={'altered':high,'preserved':low}
    return {'temperature':temperature,'thresholds':thresholds,'method':'scalar temperature on binary logit; empirical calibration-set precision thresholds',
      'warning':'Small mixed-domain calibration set. Threshold precision is empirical, not a guarantee on new domains.',
      'metrics_before':metrics(y,logits),'metrics_after':metrics(y,logits,temperature,thresholds)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('checkpoint');calibrate(p.parse_args().checkpoint)
