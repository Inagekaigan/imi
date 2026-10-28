"""Offline CPU worker. Uses ONNX + tokenizer only; no torch or network client."""
import argparse,json,sys,time
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

def sigmoid(x):return 1/(1+np.exp(-np.clip(x,-40,40)))
def utf16(text,pos):return len(text[:pos].encode('utf-16-le'))//2

class Inference:
    def __init__(self,model_dir):
        self.directory=Path(model_dir);self.meta=json.loads((self.directory/'manifest.json').read_text(encoding='utf-8'))
        self.tokenizer=Tokenizer.from_file(str(self.directory/'tokenizer.json'))
        self.tokenizer.no_truncation();self.tokenizer.no_padding()
        options=ort.SessionOptions();options.intra_op_num_threads=4;options.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(self.directory/self.meta['modelFile']),sess_options=options,providers=['CPUExecutionProvider'])
    def analyze(self,japanese,english):
        started=time.perf_counter();encoded=self.tokenizer.encode(japanese,english)
        common={'model':{'name':self.meta['name'],'version':self.meta['version'],'checkpoint':self.meta['checkpoint'],'training':self.meta['training']},'origin':'neural','tokenCount':len(encoded.ids)}
        if len(encoded.ids)>self.meta['maxTokens']:
            return {**common,'verdict':'uncertain','findings':[],'probabilityAltered':None,'warnings':[f"The pair has {len(encoded.ids)} tokens; the validated limit is {self.meta['maxTokens']}. It was not silently truncated."],'inferenceMs':0,'neuralSpans':{'japanese':[],'english':[]}}
        sides=[-1 if v is None else v for v in encoded.sequence_ids]
        inputs={'input_ids':np.array([encoded.ids],dtype=np.int64),'attention_mask':np.array([encoded.attention_mask],dtype=np.int64),'side_ids':np.array([sides],dtype=np.int64)}
        logits,error_logits,scope_logits=self.session.run(['logits','error_logits','scope_logits'],inputs)
        probability=float(sigmoid(logits[0,0]/self.meta['temperature']));thresholds=self.meta['thresholds']
        verdict='meaning_altered' if probability>=thresholds['altered'] else 'meaning_preserved' if probability<=thresholds['preserved'] else 'uncertain'
        spans={'japanese':[],'english':[]};error_scores=sigmoid(error_logits[0])
        for side,name,text in [(0,'japanese',japanese),(1,'english',english)]:
            merged=[]
            for token,(start,end),token_side,score in zip(encoded.tokens,encoded.offsets,sides,error_scores):
                if token_side!=side or end<=start or score<.65:continue
                if merged and start<=merged[-1]['end']+1:merged[-1]['end']=end;merged[-1]['scores'].append(float(score))
                else:merged.append({'start':start,'end':end,'scores':[float(score)]})
            for s in merged:
                spans[name].append({'start':utf16(text,s['start']),'end':utf16(text,s['end']),'text':text[s['start']:s['end']],
                                   'origin':'neural_token_head','score':float(np.mean(s['scores'])),'calibrated':False})
        categories=sigmoid(logits[0,1:]);findings=[]
        for i,(label,title) in enumerate(zip(self.meta['labels'],self.meta['titles'])):
            if categories[i]<.5 or verdict=='meaning_preserved':continue
            findings.append({'category':label,'title':title,'score':float(categories[i]),'confidence':None,'origin':'neural',
             'japanese':spans['japanese'][0] if spans['japanese'] else None,'english':spans['english'][0] if spans['english'] else None,
             'explanation':f'The trained model predicts a possible {title.lower()} error. Highlighted tokens come from its separate error-localization head; they are not category-specific alignments or a verified explanation.'})
        if verdict=='meaning_altered' and not findings:findings=[{'category':'other','title':'Semantic change, type uncertain','score':None,'origin':'neural','japanese':None,'english':None,'explanation':'The sentence-level head predicts a meaning change, but no category head passed its threshold.'}]
        warnings=[self.meta['calibrationWarning']]
        if thresholds['altered']>1:warnings.append('Calibration did not establish a reliable altered-decision threshold. Suspected changes remain uncertain; review the category findings and compare with rules.')
        return {**common,'verdict':verdict,'findings':findings,'probabilityAltered':probability,'neuralSpans':spans,
          'categoryScores':dict(zip(self.meta['labels'],map(float,categories))),'warnings':warnings,
          'inferenceMs':round((time.perf_counter()-started)*1000,2),'note':'Calibrated sentence-level model estimate, not a guarantee. Category and token scores are uncalibrated. Predictions require human review.'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True);args=parser.parse_args()
    sys.stdin.reconfigure(encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');engine=Inference(args.model)
    print(json.dumps({'ready':True}),flush=True)
    for line in sys.stdin:
        try:
            request=json.loads(line)
            if len(line)>20000:raise ValueError('Request is too large.')
            result=engine.analyze(request['japanese'],request['english']);print(json.dumps({'id':request['id'],'ok':True,'data':result},ensure_ascii=False),flush=True)
        except Exception as error:print(json.dumps({'id':locals().get('request',{}).get('id'),'ok':False,'error':str(error)}),flush=True)

if __name__=='__main__':main()
