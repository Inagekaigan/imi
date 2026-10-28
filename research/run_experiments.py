"""Sequential GPU runner. Resume only completed runs; no silent test access."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def run(name,args):
    log=ROOT/'results'/f'{name}.log';print('START '+name,flush=True)
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run([sys.executable,'-X','utf8',*args],stdout=stream,stderr=subprocess.STDOUT,cwd=ROOT.parent)
    if result.returncode:
        print(log.read_text(encoding='utf-8')[-6000:],flush=True);raise SystemExit(result.returncode)
    print('FINISHED '+name,flush=True)
if __name__=='__main__':
    (ROOT/'results').mkdir(exist_ok=True)
    cfg=json.loads((ROOT/'configs/pilot.json').read_text())
    for seed in cfg['seeds']:
        for variant in ['ordinary','scope']:
            name=f'{variant}-seed{seed}';checkpoint=ROOT/'checkpoints'/name
            completed=(checkpoint/'config.json').exists() and 'training_seconds' in json.loads((checkpoint/'config.json').read_text())
            if not completed:run(name,['research/train.py','--variant',variant,'--seed',str(seed)])
            if not (checkpoint/'calibration.json').exists():run(name+'-calibrate',['research/calibrate.py',str(checkpoint)])
    if not (ROOT/'checkpoints/frozen/calibration.json').exists():run('frozen',['research/frozen_baseline.py'])
    print('All configured train/validation/calibration runs completed. Final test remains sealed.',flush=True)
