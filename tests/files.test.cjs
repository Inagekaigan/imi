'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {parsePairs,csv}=require('../src/files.cjs');
const pair={japanese:'彼は来ない。',english:'He will come.'};
test('JSON and BOM JSONL imports',()=>{assert.deepEqual(parsePairs(JSON.stringify([pair]),'.json'),[pair]);assert.deepEqual(parsePairs('\uFEFF'+JSON.stringify(pair)+'\n','.jsonl'),[pair]);});
test('bad shape, oversize, malformed and empty imports fail',()=>{for(const text of ['{}','[]','not json',JSON.stringify(Array(5001).fill(pair)),JSON.stringify([{japanese:'猫'}]),' '.repeat(10*1024*1024+1)])assert.throws(()=>parsePairs(text,'.json'));});
test('error tells the user which pair is invalid',()=>assert.throws(()=>parsePairs(JSON.stringify([pair,{}]),'.json'),/Pair 2/));
test('CSV quotes, newlines, Unicode and spreadsheet formulas escaped',()=>{const text=csv([{japanese:'日本語',english:'=1+1,"quoted"\nline',verdict:'review_required',findings:[],model:{name:'baseline',version:'1'},note:'Review'}]);assert.ok(text.startsWith('\uFEFF'));assert.ok(text.includes('"\'=1+1,""quoted""\nline"'));assert.ok(text.includes('日本語'));});
