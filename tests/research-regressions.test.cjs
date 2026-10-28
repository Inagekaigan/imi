'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {analyzeRules}=require('../src/rules.cjs');
test('not everyone is different from nobody',()=>{
 const r=analyzeRules({japanese:'全員が試験に合格したわけではない。',english:'Nobody passed the exam.'});
 assert.equal(r.findings[0].category,'negation');assert.equal(r.findings[0].origin,'rule');assert.equal(r.findings[0].english.text,'Nobody');
});
test('partial negation paraphrases are not flagged by the scope rule',()=>{
 for(const english of ['Not everyone passed the exam.','Not all of them passed the exam.','It is not the case that everyone passed the exam.'])assert.equal(analyzeRules({japanese:'全員が試験に合格したわけではない。',english}).findings.length,0);
});
test('deadline by versus at is distinguished',()=>{
 const japanese='報告書を午後3時までに提出してください。';
 assert.equal(analyzeRules({japanese,english:'Submit the report at 3 p.m.'}).findings[0].category,'temporal');
 assert.equal(analyzeRules({japanese,english:'Submit the report by 3 p.m.'}).findings.length,0);
 assert.equal(analyzeRules({japanese,english:'Submit the report no later than 3 p.m.'}).findings.length,0);
});
test('no rule match remains uncertain, never preserved',()=>assert.equal(analyzeRules({japanese:'今日は晴れです。',english:'It is sunny today.'}).verdict,'uncertain'));
