"""Train ordinary or scope-auxiliary XLM-R; never access final test data."""
import argparse, hashlib, json, os, random, time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from sklearn.metrics import f1_score
from safetensors.torch import save_file,load_file
from dataset import Pairs,collate,load_rows,ROOT
from model import MeaningModel,masked_bce

def predict(model,loader,device):
    model.eval();logits=[];labels=[];error_tp=error_fp=error_fn=0
    with torch.inference_mode():
        for b in loader:
            b={k:v.to(device) for k,v in b.items()}
            output,errors,_,_=model(b['input_ids'],b['attention_mask'],b['side_ids'])
            logits.extend(output.float().cpu().tolist());labels.extend(b['labels'].cpu().tolist())
            mask=b['error_labels']>=0;p=errors>0;y=b['error_labels']>0
            error_tp+=int((p&y&mask).sum());error_fp+=int((p&~y&mask).sum());error_fn+=int((~p&y&mask).sum())
    return np.array(logits),np.array(labels),{'tp':error_tp,'fp':error_fp,'fn':error_fn}

def train(args):
    config=json.loads(Path(args.config).read_text());seed=args.seed
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    torch.set_num_threads(6)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    device='cuda' if torch.cuda.is_available() else 'cpu'
    base=Path(config['model']).resolve();tokenizer=AutoTokenizer.from_pretrained(base,local_files_only=True)
    data=Pairs(load_rows('train'),tokenizer,config['max_length']);val=Pairs(load_rows('validation'),tokenizer,config['max_length'])
    generator=torch.Generator().manual_seed(seed)
    train_loader=DataLoader(data,batch_size=config['batch_size'],shuffle=True,collate_fn=collate,generator=generator)
    val_loader=DataLoader(val,batch_size=config['batch_size']*2,collate_fn=collate)
    model=MeaningModel(base,config['train_encoder_layers']).to(device)
    encoder_params=[p for p in model.encoder.parameters() if p.requires_grad]
    head_params=[p for n,p in model.named_parameters() if not n.startswith('encoder.')]
    optimizer=torch.optim.AdamW([{'params':encoder_params,'lr':config['learning_rate']},{'params':head_params,'lr':config['head_learning_rate']}],weight_decay=config['weight_decay'])
    labels=np.array([x['labels'] for x in data.encoded]);positive=(labels==1).sum(0);negative=(labels==0).sum(0)
    pos_weight=torch.tensor(np.clip(negative/np.maximum(positive,1),1,12),dtype=torch.float32,device=device)
    scaler=torch.amp.GradScaler('cuda',enabled=device=='cuda')
    out=ROOT/'checkpoints'/f'{args.variant}-seed{seed}';out.mkdir(parents=True,exist_ok=True)
    metadata={'config':config,'variant':args.variant,'seed':seed,'device':device,'gpu':torch.cuda.get_device_name(0) if device=='cuda' else None,
      'trainable_parameters':sum(p.numel() for p in model.parameters() if p.requires_grad),'total_parameters':sum(p.numel() for p in model.parameters()),
      'train_rows':len(data),'validation_rows':len(val),'long_train_excluded':data.excluded_long,'long_validation_excluded':val.excluded_long,
      'dataset_report_sha256':hashlib.sha256((ROOT/'data/dataset-report.json').read_bytes()).hexdigest(),'pretrained_revision':config['revision']}
    (out/'config.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    best=-1;history=[];started=time.perf_counter();acc=config['gradient_accumulation']
    for epoch in range(config['epochs']):
        model.train();total=0;optimizer.zero_grad(set_to_none=True)
        for step,b in enumerate(train_loader):
            b={k:v.to(device) for k,v in b.items()}
            with torch.autocast(device_type=device,dtype=torch.float16,enabled=device=='cuda'):
                logits,error_logits,scope_logits,_=model(b['input_ids'],b['attention_mask'],b['side_ids'])
                loss=masked_bce(logits,b['labels'],pos_weight)+config['span_loss_weight']*masked_bce(error_logits,b['error_labels'],torch.tensor(4.,device=device))
                if args.variant=='scope' and (b['scope_labels']!=-100).any():
                    loss=loss+config['scope_loss_weight']*torch.nn.functional.cross_entropy(scope_logits.flatten(0,1),b['scope_labels'].flatten(),ignore_index=-100)
                scaled=loss/acc
            scaler.scale(scaled).backward();total+=float(loss.detach())
            if (step+1)%acc==0 or step+1==len(train_loader):
                scaler.unscale_(optimizer);torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
                scaler.step(optimizer);scaler.update();optimizer.zero_grad(set_to_none=True)
            if (step+1)%40==0: print(json.dumps({'variant':args.variant,'seed':seed,'epoch':epoch+1,'step':step+1,'steps':len(train_loader),'loss':round(total/(step+1),4),'seconds':round(time.perf_counter()-started)}),flush=True)
        logit,y,spans=predict(model,val_loader,device);score=f1_score(y[:,0],logit[:,0]>0,zero_division=0)
        record={'epoch':epoch+1,'loss':total/len(train_loader),'validation_binary_f1':score,'span_counts':spans,'seconds':time.perf_counter()-started};history.append(record)
        print(json.dumps(record),flush=True)
        if score>best:
            best=score
            # Store only trained tensors; the pinned immutable base supplies frozen weights.
            trainable={n for n,p in model.named_parameters() if p.requires_grad}
            save_file({n:t.detach().cpu().contiguous() for n,t in model.state_dict().items() if n in trainable},str(out/'trained.safetensors'))
            np.savez_compressed(out/'validation.npz',logits=logit,labels=y)
            (out/'validation-ids.json').write_text(json.dumps([r['id'] for r in val.rows]),encoding='utf-8')
        (out/'history.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
    metadata.update({'training_seconds':time.perf_counter()-started,'best_validation_binary_f1':best,'peak_gpu_bytes':torch.cuda.max_memory_allocated() if device=='cuda' else None})
    (out/'config.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print('SAVED '+str(out),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['ordinary','scope'],required=True);parser.add_argument('--seed',type=int,default=17);parser.add_argument('--config',default='research/configs/pilot.json');train(parser.parse_args())
