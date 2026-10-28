"""Explicit one-time network setup. Inference never invokes this script."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REVISION='e73636d4f797dec63c3081bb6ed5c7b0bb3f2089'
WEIGHT_SHA='6fd4797bc397c3b8b55d6bb5740366b57e6a3ce91c04c77f22aafc0c128e6feb'
def main():
    out=ROOT/'models/xlm-roberta-base';out.mkdir(parents=True,exist_ok=True);manifest={}
    for name in ['config.json','tokenizer.json','tokenizer_config.json','sentencepiece.bpe.model','model.safetensors','README.md']:
        target=out/name;url=f'https://huggingface.co/FacebookAI/xlm-roberta-base/resolve/{REVISION}/{name}'
        if not target.exists():subprocess.run(['curl','--fail','--location','--retry','3','--output',str(target),url],check=True)
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        if name=='model.safetensors' and digest!=WEIGHT_SHA:raise ValueError('Pretrained checkpoint checksum mismatch')
        manifest[name]={'url':url,'sha256':digest,'bytes':target.stat().st_size}
    (ROOT/'data/pretrained-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if __name__=='__main__':main()
