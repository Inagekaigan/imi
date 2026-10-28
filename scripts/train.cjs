'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {FEATURES, LABELS, extract, sigmoid, analyze} = require('../src/engine.cjs');
const {dataset} = require('./dataset.cjs');
const root = path.join(__dirname, '..');
const sourcePath = process.argv[2];
const rows = sourcePath ? fs.readFileSync(sourcePath,'utf8').trim().split(/\r?\n/).map(JSON.parse) : dataset();
const ids = new Set(), groupSplits = new Map(), sentenceSplits = new Map();
for (const r of rows) {
  if (!r.id || ids.has(r.id) || !r.group || !['train','test'].includes(r.split) || !Array.isArray(r.labels) || r.labels.some(l=>!LABELS.includes(l))) throw new Error('Invalid dataset: unique id, group, train/test split and supported labels are required.');
  ids.add(r.id);
  const previous = groupSplits.get(r.group);
  if (previous && previous !== r.split) throw new Error('A source group leaks between train and test.');
  groupSplits.set(r.group, r.split);
  const previousSentence = sentenceSplits.get(r.japanese);
  if (previousSentence && previousSentence !== r.split) throw new Error('A Japanese source leaks between train and test.');
  sentenceSplits.set(r.japanese, r.split);
  extract(r);
}
const train = rows.filter(r=>r.split==='train'), test = rows.filter(r=>r.split==='test');
if (!train.length || !test.length) throw new Error('Both train and test rows are required.');
for (const label of LABELS) if (!train.some(r=>r.labels.includes(label)) || !train.some(r=>!r.labels.includes(label))) throw new Error(`Training needs positive and negative examples for ${label}.`);
const samples = train.map(r=>({x:[1,...extract(r).x],y:LABELS.map(l=>+r.labels.includes(l))}));
const weights = LABELS.map(()=>Array(FEATURES.length+1).fill(0));
// Deterministic full-batch gradient descent, balanced BCE for rare categories.
for (let label=0; label<LABELS.length; label++) {
  const positive = samples.filter(s=>s.y[label]).length;
  for (let epoch=0;epoch<1600;epoch++) {
    const gradient = weights[label].map(()=>0);
    for (const s of samples) {
      const p = sigmoid(s.x.reduce((sum,v,i)=>sum + v*weights[label][i],0));
      const balance = s.y[label] ? samples.length/(2*positive) : samples.length/(2*(samples.length-positive));
      s.x.forEach((v,i)=>gradient[i] += (p-s.y[label])*v*balance);
    }
    weights[label] = weights[label].map((w,i)=>w - 0.15*(gradient[i]/samples.length + (i ? 0.001*w : 0)));
  }
}
const model = {schemaVersion:1,name:'Imi feature classifier',version:'0.1.0',training:sourcePath?'user-supplied labeled pairs':'authored synthetic templates',architecture:'Four independent logistic regression heads over bilingual cue features',features:FEATURES,labels:LABELS,threshold:0.65,weights,datasetSha256:crypto.createHash('sha256').update(JSON.stringify(rows)).digest('hex'),trainRows:train.length,testRows:test.length};
const metrics = LABELS.map(category=>{
  let tp=0,fp=0,fn=0,tn=0,assessed=0;
  for(const row of test) {
    const result=analyze(row,model), predicted=result.findings.some(f=>f.category===category), expected=row.labels.includes(category);
    if(result.checks.find(c=>c.category===category).status!=='not_assessed')assessed++;
    if(predicted && expected)tp++; else if(predicted)fp++; else if(expected)fn++; else tn++;
  }
  return {category,tp,fp,fn,tn,precision:tp+fp?tp/(tp+fp):null,recall:tp+fn?tp/(tp+fn):null,assessed};
});
fs.mkdirSync(path.join(root,'model'),{recursive:true});
fs.writeFileSync(path.join(root,'model/baseline.json'),JSON.stringify(model,null,2)+'\n');
fs.writeFileSync(path.join(root,'model/evaluation.json'),JSON.stringify({dataset: model.training,warning:'Template-held-out synthetic evaluation is a pipeline check, not evidence of real-world translation accuracy.',trainRows:train.length,testRows:test.length,metrics},null,2)+'\n');
if(!sourcePath)fs.writeFileSync(path.join(root,'data/synthetic.jsonl'),rows.map(r=>JSON.stringify(r)).join('\n')+'\n');
console.log(JSON.stringify({trainRows:train.length,testRows:test.length,metrics},null,2));
