'use strict';
const {app,BrowserWindow,ipcMain,dialog,session} = require('electron');
const fs = require('node:fs/promises');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {randomUUID} = require('node:crypto');
const {analyze,validatePair} = require('./engine.cjs');
const {analyzeRules}=require('./rules.cjs');
const {NeuralWorker}=require('./neural.cjs');
const neural=new NeuralWorker(app.isPackaged?process.resourcesPath:app.getAppPath(),app.isPackaged);
const {parsePairs,csv} = require('./files.cjs');
const model = require('../model/baseline.json');
const evaluation = require('../model/evaluation.json');
const smoke = process.argv.includes('--smoke-test');
const recordDemo=process.argv.includes('--record-demo');
if (smoke||recordDemo) app.setPath('userData',path.join(app.getPath('temp'),'imi-smoke-'+process.pid));
let window, history=[], settings={saveHistory:false}, results=[];
let persistence=Promise.resolve();
const pageUrl = pathToFileURL(path.join(__dirname,'renderer/index.html')).href;
const stateFile=()=>path.join(app.getPath('userData'),'state.json');
async function persist() {
  const snapshot=JSON.stringify({settings,history});
  persistence=persistence.catch(()=>{}).then(async()=>{
    await fs.mkdir(app.getPath('userData'),{recursive:true});
    await fs.writeFile(stateFile()+'.tmp',snapshot,'utf8');
    await fs.rename(stateFile()+'.tmp',stateFile());
  });
  return persistence;
}
function register(name,handler) {
  ipcMain.handle(name,async(event,...args)=>{
    if(event.sender!==window.webContents || event.senderFrame!==window.webContents.mainFrame || event.senderFrame.url!==pageUrl) throw new Error('Untrusted request.');
    try {return {ok:true,data:await handler(...args)};} catch(e) {return {ok:false,error:e.message};}
  });
}
async function run(input) {
  const pair=validatePair(input),mode=input.mode|| (smoke?'baseline':'neural');
  if(!['neural','baseline','rules','compare'].includes(mode))throw new Error('Choose a supported model.');
  const started=performance.now();let result;
  const baseline=()=>({...analyze(pair,model),origin:'feature_classifier'});
  const rules=()=>({...analyzeRules(pair),model:{name:'Linguistic rules',version:'0.2.0'},warnings:[],checks:[]});
  if(mode==='baseline')result=baseline();
  else if(mode==='rules')result=rules();
  else {result={...pair,...await neural.analyze(pair),checks:[]};if(mode==='compare')result.comparison=[baseline(),rules()];}
  return {...result,id:randomUUID(),createdAt:new Date().toISOString(),elapsedMs:Math.round(performance.now()-started)};
}
async function saveResults(next) {
  results=[...next,...results].slice(0,5000);
  if(settings.saveHistory){history=[...next,...history].slice(0,100);await persist();}
  return next;
}
app.whenReady().then(async()=>{
  try {const saved=JSON.parse(await fs.readFile(stateFile(),'utf8'));settings.saveHistory=saved.settings?.saveHistory===true;history=Array.isArray(saved.history)?saved.history.slice(0,100):[];} catch{}
  session.defaultSession.setPermissionRequestHandler((_wc,_permission,callback)=>callback(false));
  session.defaultSession.setPermissionCheckHandler(()=>false);
  session.defaultSession.webRequest.onBeforeRequest({urls:['http://*/*','https://*/*','ws://*/*','wss://*/*']},(_details,callback)=>callback({cancel:true}));
  register('state',()=>({history,settings,model:{...model,weights:undefined},neural:neural.manifest(),evaluation,version:app.getVersion()}));
  register('analyze',async pair=>(await saveResults([await run(pair)]))[0]);
  register('feedback',async(id,label)=>{
    if(!['correct','incorrect','uncertain'].includes(label))throw new Error('Invalid feedback.');
    const result=[...results,...history].find(r=>r.id===id);if(!result)throw new Error('Analyze the pair again before saving feedback.');
    await fs.mkdir(app.getPath('userData'),{recursive:true});
    await fs.appendFile(path.join(app.getPath('userData'),'feedback.jsonl'),JSON.stringify({recordedAt:new Date().toISOString(),label,result})+'\n','utf8');return true;
  });
  register('batch',async(mode)=>{
    const chosen=await dialog.showOpenDialog(window,{title:'Import Japanese–English pairs',properties:['openFile'],filters:[{name:'Sentence pairs',extensions:['json','jsonl','csv']}]});
    if(chosen.canceled)return null;
    const file=chosen.filePaths[0];
    if((await fs.stat(file)).size>10*1024*1024)throw new Error('Import must be smaller than 10 MB.');
    const pairs=parsePairs(await fs.readFile(file,'utf8'),path.extname(file).toLowerCase());
    const next=[];for(const pair of pairs){next.push(await run({...pair,mode}));window.webContents.send('batch-progress',{done:next.length,total:pairs.length});}
    return saveResults(next);
  });
  register('settings',async value=>{settings.saveHistory=value===true;await persist();return settings;});
  register('clear-history',async()=>{history=[];await persist();return true;});
  register('export',async(ids,format)=>{
    if(!Array.isArray(ids)||ids.length>5000||!['json','csv'].includes(format))throw new Error('Invalid export request.');
    const available=new Map([...history,...results].map(r=>[r.id,r]));
    const selected=ids.map(id=>available.get(id));
    if(!selected.length||selected.some(r=>!r))throw new Error('These results are no longer available. Analyze the pair again.');
    const chosen=await dialog.showSaveDialog(window,{title:'Export analysis',defaultPath:`imi-analysis.${format}`,filters:[{name:format.toUpperCase(),extensions:[format]}]});
    if(chosen.canceled)return false;
    await fs.writeFile(chosen.filePath,format==='csv'?csv(selected):JSON.stringify(selected,null,2),'utf8');
    return true;
  });
  window=new BrowserWindow({width:1280,height:900,minWidth:920,minHeight:700,title:'Imi — Meaning matters',icon:path.join(__dirname,'assets/icon.png'),backgroundColor:'#f6f7f9',show:!smoke,autoHideMenuBar:true,webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true,webSecurity:true}});
  window.removeMenu();
  window.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  window.webContents.on('will-navigate',event=>event.preventDefault());
  window.webContents.on('will-attach-webview',event=>event.preventDefault());
  await window.loadURL(pageUrl);
  if(recordDemo){try{await neural.start();await require('./record-demo.cjs')({window,root:app.getAppPath()});app.quit();}catch(e){console.error(e);app.exit(1);}return;}
  if(smoke){
    try {
      const result=await window.webContents.executeJavaScript(`(async()=>{
        document.querySelector('#engine').value='baseline';
        document.querySelector('#japanese').value='彼は犯人ではない可能性が高い。';
        document.querySelector('#english').value='He is probably the culprit.';
        document.querySelector('#japanese').dispatchEvent(new Event('input'));
        document.querySelector('#english').dispatchEvent(new Event('input'));
        document.querySelector('#analyze').click();
        for(let i=0;i<100;i++) {if(document.querySelector('#result-title')?.textContent==='Potential meaning change') break; await new Promise(r=>setTimeout(r,50));}
        const text=document.body.innerText;
        if(!text.includes('Negation reversal')||!document.querySelector('mark'))throw new Error('Analysis UI did not render expected evidence.');
        document.querySelector('[data-page="model"]').click();
        if(document.querySelector('#page-model').hidden)throw new Error('Model page navigation failed.');
        document.querySelector('[data-page="review"]').click();
        return {analysis:true,highlighting:true,navigation:true,nodeExposed:typeof window.require!=='undefined',bridgeAvailable:!!window.imi};
      })()`);
      if(result.nodeExposed)throw new Error('Node must not be exposed to renderer.');
      const output=process.env.IMI_SMOKE_DIR || (app.isPackaged?app.getPath('temp'):app.getAppPath());
      const extra=await require('./smoke.cjs')({window,app,dialog});
      await fs.writeFile(path.join(output,'smoke-result.json'),JSON.stringify({...result,...extra},null,2));
      try{await fs.writeFile(path.join(output,'smoke.png'),(await window.webContents.capturePage()).toPNG());}catch(e){await fs.writeFile(path.join(output,'capture-warning.txt'),e.message);}
      app.exit(0);
    }catch(e){
      console.error(e);
      const output=process.env.IMI_SMOKE_DIR || (app.isPackaged?app.getPath('temp'):app.getAppPath());
      await fs.writeFile(path.join(output,'smoke-error.json'),JSON.stringify({error:e.message,stack:e.stack},null,2)).catch(()=>{});
      app.exit(1);
    }
  }
});
app.on('window-all-closed',()=>app.quit());
app.on('before-quit',()=>neural.close());
