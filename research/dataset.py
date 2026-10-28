import json
from pathlib import Path
import torch
from torch.utils.data import Dataset

ROOT=Path(__file__).resolve().parent
def load_rows(split,allow_test=False):
    if split=='test' and not allow_test:raise ValueError('Final test is sealed. Use the final evaluation entrypoint after freezing the experiment.')
    return [json.loads(line) for line in (ROOT/f'data/processed/{split}.jsonl').read_text(encoding='utf-8').splitlines() if line]

class Pairs(Dataset):
    def __init__(self,rows,tokenizer,max_length):
        self.rows=[]; self.encoded=[];self.excluded_long=[]
        for row in rows:
            enc=tokenizer(row['japanese'],row['english'],return_offsets_mapping=True,truncation=False)
            if len(enc['input_ids'])>max_length:
                self.excluded_long.append(row['id']);continue
            sides=enc.sequence_ids();error=[];scope=[]
            for side,(start,end) in zip(sides,enc['offset_mapping']):
                if side is None or end<=start:error.append(-1.);scope.append(-100);continue
                name='japanese' if side==0 else 'english'
                spans=row.get(name+'_spans',[])
                error.append(float(any(start<s['end'] and end>s['start'] for s in spans)) if name in row['span_supervision'] else -1.)
                tag=-100
                if side==0 and row.get('scope_supervision'):
                    tag=0
                    for s in row['scope_spans']:
                        if start<s['end'] and end>s['start']:tag=1 if s['kind']=='c' else 2
                scope.append(tag)
            self.rows.append(row)
            self.encoded.append({'input_ids':enc['input_ids'],'attention_mask':enc['attention_mask'],
                'side_ids':[-1 if s is None else s for s in sides],'labels':[row['altered'],*row['labels']],
                'error_labels':error,'scope_labels':scope})
    def __len__(self):return len(self.rows)
    def __getitem__(self,index):return self.encoded[index]

def collate(batch):
    length=max(len(x['input_ids']) for x in batch)
    out={}
    for key,pad in [('input_ids',1),('attention_mask',0),('side_ids',-1),('error_labels',-1),('scope_labels',-100)]:
        out[key]=torch.tensor([x[key]+[pad]*(length-len(x[key])) for x in batch],dtype=torch.float32 if key=='error_labels' else torch.long)
    out['labels']=torch.tensor([x['labels'] for x in batch],dtype=torch.float32)
    return out
