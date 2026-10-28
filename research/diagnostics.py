"""Post-hoc authored diagnostics, never used for fitting or model selection."""
import json
from pathlib import Path
from infer import Inference
root=Path(__file__).resolve().parent
engine=Inference(root.parent/'model/neural');rows=json.loads((root/'data/posthoc-probes.json').read_text(encoding='utf-8'));results=[]
for row in rows:
 prediction=engine.analyze(row['japanese'],row['english']);results.append({**row,'probabilityAltered':prediction['probabilityAltered'],'verdict':prediction['verdict'],'findings':[f['category'] for f in prediction['findings']]})
correct=sum((r['probabilityAltered']>=.5)==r['altered'] for r in results)
report={'status':'Post-hoc, authored, not independently verified; not a new final benchmark. No tuning on these results.','binary_accuracy':correct/len(results),'rows':results,'invariance':[]}
for a,b,label in [(6,8,'name substitution aligned'),(7,9,'name substitution reversed'),(10,12,'number substitution aligned'),(11,13,'number substitution distorted')]:
 report['invariance'].append({'test':label,'absolute_probability_change':abs(results[a]['probabilityAltered']-results[b]['probabilityAltered']),'binary_label_changed':(results[a]['probabilityAltered']>=.5)!=(results[b]['probabilityAltered']>=.5)})
(root/'results/posthoc-diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('Post-hoc accuracy',report['binary_accuracy'])
