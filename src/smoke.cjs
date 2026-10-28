'use strict';
// Runs only with --smoke-test, in an isolated profile. Native dialogs are
// substituted with temporary fixture paths to make CI noninteractive.
const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
module.exports=async({window,app,dialog})=>{
  const directory=app.getPath('userData');await fs.mkdir(directory,{recursive:true});
  const fixture=path.join(directory,'pairs.json');
  await fs.writeFile(fixture,JSON.stringify([{japanese:'少なくとも10人が参加した。',english:'Exactly 10 people attended.'},{japanese:'太郎が花子を助けた。',english:'Hanako helped Taro.'}]));
  dialog.showOpenDialog=async()=>({canceled:false,filePaths:[fixture]});
  let exportIndex=0;
  dialog.showSaveDialog=async()=>({canceled:false,filePath:path.join(directory,`export-${++exportIndex}.txt`)});
  const result=await window.webContents.executeJavaScript(`(async()=>{
    const state=await window.imi.state();
    if(state.settings.saveHistory || state.history.length)throw new Error('History must default off.');
    let invalid=false;try{await window.imi.analyze({japanese:'',english:''});}catch{invalid=true;}
    if(!invalid)throw new Error('Invalid input was accepted.');
    const uncertain=await window.imi.analyze({japanese:'明日は雨が降るかもしれない。',english:'It will rain tomorrow.'});
    if(!uncertain.findings.some(f=>f.category==='uncertainty'))throw new Error('Uncertainty inference failed.');
    await window.imi.setHistory(true);
    const batch=await window.imi.batch();
    if(batch.length!==2 || !batch[0].findings.some(f=>f.category==='quantity') || !batch[1].findings.some(f=>f.category==='agent'))throw new Error('Batch inference failed.');
    await window.imi.export(batch.map(r=>r.id),'json');
    await window.imi.export(batch.map(r=>r.id),'csv');
    const saved=await window.imi.state();if(saved.history.length!==2)throw new Error('History save failed.');
    await window.imi.clearHistory();
    if((await window.imi.state()).history.length)throw new Error('History deletion failed.');
    await window.imi.setHistory(false);
    document.querySelector('[data-page="batch"]').click();
    document.querySelector('#import-batch').click();
    for(let i=0;i<100;i++){if(document.querySelectorAll('#batch-results .list-item').length===2)break;await new Promise(r=>setTimeout(r,50));}
    if(document.querySelectorAll('#batch-results .list-item').length!==2)throw new Error('Batch UI failed.');
    document.querySelector('[data-page="review"]').click();
    let neuralTest='model not bundled';
    if(state.neural){
      const neural=await window.imi.analyze({japanese:'全員が試験に合格したわけではない。',english:'Nobody passed the exam.',mode:'compare'});
      if(neural.origin!=='neural'||!Number.isFinite(neural.probabilityAltered)||neural.comparison.length!==2)throw new Error('Bundled neural inference failed.');
      await window.imi.feedback(neural.id,'uncertain');
      neuralTest={origin:neural.origin,model:neural.model.checkpoint,probability:neural.probabilityAltered,milliseconds:neural.inferenceMs,comparison:true,feedback:true};
    }
    return {inputValidation:true,uncertainty:true,batchImport:true,batchUI:true,history:true,exports:true,neural:neuralTest};
  })()`);
  assert.equal(JSON.parse(await fs.readFile(path.join(directory,'export-1.txt'),'utf8')).length,2);
  assert.ok((await fs.readFile(path.join(directory,'export-2.txt'),'utf8')).includes('Quantity distortion'));
  assert.equal(JSON.parse(await fs.readFile(path.join(directory,'state.json'),'utf8')).history.length,0);
  return result;
};
