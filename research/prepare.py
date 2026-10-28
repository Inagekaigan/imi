"""Create documented document-disjoint data, preserving missing category labels."""
import collections
import hashlib
import json
from pathlib import Path
import re
from schema import LABELS
from contrastive import generate

ROOT=Path(__file__).resolve().parent
SPLITS=['train','validation','calibration','test']
SEMANTIC={1,2,3,4,5,6,17}
def normalize(s): return re.sub(r'[^\w]', '', s.lower())
def grams(s): return {s[i:i+3] for i in range(max(1,len(s)-2))}

def prepare():
    all_rows=[]; excluded=collections.Counter()
    for file in sorted((ROOT/'data/raw/mtpedocs/MT-MQM').glob('*/*.json')):
        doc=int(file.stem); split='train' if doc<=12 else 'validation' if doc<=14 else 'calibration' if doc==15 else 'test'
        for index,row in enumerate(next(iter(json.loads(file.read_text(encoding='utf-8')).values()))):
            errors=row.get('errors',[])
            if any(e['type']==16 for e in errors): excluded['source_error']+=1; continue
            semantic=[e for e in errors if e['type'] in SEMANTIC]
            major=[e for e in semantic if e['severity'] in ['Major','Critical']]
            if semantic and not major: excluded['minor_semantic_ambiguous']+=1; continue
            labels=[0]*len(LABELS) if not major else [-1]*len(LABELS)
            for e in major:
                key={1:'entity_terminology',2:'entity_terminology',3:'other',4:'addition',5:'omission',6:'other',17:'other'}[e['type']]
                labels[LABELS.index(key)]=1
            spans={'japanese':[],'english':[]}
            bad_span=False
            for e in major:
                side='japanese' if e['side']=='src' else 'english'
                text=row['src'] if side=='japanese' else row['mt']
                if text[e['start']:e['end']]!=e['text']:
                    # Never silently attach an annotation to the wrong token.
                    excluded['invalid_annotation_span']+=1;bad_span=True;break
                spans[side].append({'start':e['start'],'end':e['end'],'kind':'e'})
            if bad_span: continue
            all_rows.append({'id':f'mqm-{file.parent.name}-{doc:03}-{index:04}', 'group':f'mtpedocs-{doc:03}',
                'split':split,'japanese':row['src'],'english':row['mt'],'altered':int(bool(major)),
                'labels':labels,'japanese_spans':spans['japanese'],'english_spans':spans['english'],
                'span_supervision':['english']+(['japanese'] if any(e['type']==5 for e in major) else []),'scope_spans':[],'scope_supervision':False,
                'source':'MTPEdocs-MQM','human_verified':True,'domain':'municipal_public_information','system':file.parent.name,
                'original_annotations':major,'label_policy':'major_accuracy_or_terminology; specific_unknown_categories_masked'})
    all_rows.extend(generate())
    kept=[]; seen_pairs=set(); prior_sources={}; prior_grams={}; rejected=[]
    for split in SPLITS:
        # Compare against earlier splits only; system variants within a split are allowed.
        split_sources={}
        for row in (r for r in all_rows if r['split']==split):
            source=normalize(row['japanese']); pair=(source,normalize(row['english']))
            if pair in seen_pairs: excluded['exact_pair_duplicate']+=1; continue
            reason=None
            if source in prior_sources: reason='exact_source_cross_split'
            else:
                g=grams(source)
                for previous,pg in prior_grams.items():
                    if min(len(source),len(previous))/max(len(source),len(previous),1)<.8:continue
                    if len(g&pg)/max(len(g|pg),1)>=.85:reason='near_source_cross_split';break
            if reason:
                excluded[reason]+=1;rejected.append({'id':row['id'],'reason':reason});continue
            seen_pairs.add(pair); split_sources[source]=row['group'];kept.append(row)
        prior_sources.update(split_sources);prior_grams.update({s:grams(s) for s in split_sources})
    destination=ROOT/'data/processed';destination.mkdir(parents=True,exist_ok=True)
    report={'policy':'See PROTOCOL.md','labels':LABELS,'excluded':dict(excluded),'splits':{},'test_sealed':True}
    for split in SPLITS:
        rows=[r for r in kept if r['split']==split]
        content=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
        (destination/f'{split}.jsonl').write_text(content,encoding='utf-8')
        report['splits'][split]={'rows':len(rows),'altered':sum(r['altered'] for r in rows),
          'sources':dict(collections.Counter(r['source'] for r in rows)),
          'categories':{l:{'positive':sum(r['labels'][i]==1 for r in rows),'known':sum(r['labels'][i]>=0 for r in rows)} for i,l in enumerate(LABELS)},
          'sha256':hashlib.sha256(content.encode()).hexdigest()}
    (ROOT/'data/dataset-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (destination/'exclusions.json').write_text(json.dumps(rejected,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':prepare()
