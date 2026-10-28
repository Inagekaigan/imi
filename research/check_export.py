import sys,json,numpy as np,torch,onnxruntime as ort
sys.path.insert(0,'research')
from model import MeaningModel
from dataset import Pairs,load_rows,collate
from transformers import AutoTokenizer
from safetensors.torch import load_file
c=json.load(open('research/checkpoints/ordinary-seed29/config.json'))['config'];torch.set_num_threads(4)
m=MeaningModel(c['model']);m.load_state_dict(load_file('research/checkpoints/ordinary-seed29/trained.safetensors'),strict=False);m.eval()
o=ort.SessionOptions();o.intra_op_num_threads=4
s=ort.InferenceSession('research/cache/model.float.onnx',sess_options=o)
d=Pairs(load_rows('validation')[:24],AutoTokenizer.from_pretrained(c['model'],local_files_only=True),192)
diffs=[]
for x in d:
 b=collate([x]);feed={k:b[k].numpy() for k in ['input_ids','attention_mask','side_ids']}
 with torch.inference_mode():ref=m(*[b[k] for k in feed])[0].numpy()
 diffs.append(float(np.max(np.abs(ref-s.run(['logits'],feed)[0]))))
print('FLOAT ONNX MAX DRIFT',max(diffs),flush=True)
