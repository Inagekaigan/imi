const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {NeuralWorker}=require('../src/neural.cjs');

test('source checkout with metadata only does not offer unavailable neural inference',()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'imi-availability-'));
  try{
    const directory=path.join(root,'model/neural');fs.mkdirSync(directory,{recursive:true});
    fs.writeFileSync(path.join(directory,'manifest.json'),JSON.stringify({modelFile:'model.onnx'}));
    assert.equal(new NeuralWorker(root).manifest(),null);
    fs.writeFileSync(path.join(directory,'model.onnx'),'');fs.writeFileSync(path.join(directory,'tokenizer.json'),'{}');
    assert.equal(new NeuralWorker(root).manifest(),null);
    fs.mkdirSync(path.join(root,'.venv/Scripts'),{recursive:true});fs.writeFileSync(path.join(root,'.venv/Scripts/python.exe'),'');
    assert.equal(new NeuralWorker(root).manifest().modelFile,'model.onnx');
  }finally{fs.rmSync(root,{recursive:true,force:true});}
});
