'use strict';
const {contextBridge,ipcRenderer}=require('electron');
const invoke=async(name,...args)=>{
  const result=await ipcRenderer.invoke(name,...args);
  if(!result.ok)throw new Error(result.error);
  return result.data;
};
contextBridge.exposeInMainWorld('imi',{
  state:()=>invoke('state'),analyze:pair=>invoke('analyze',pair),batch:mode=>invoke('batch',mode),
  feedback:(id,label)=>invoke('feedback',id,label),
  onBatchProgress:callback=>ipcRenderer.on('batch-progress',(_event,value)=>callback(value)),
  setHistory:enabled=>invoke('settings',enabled),clearHistory:()=>invoke('clear-history'),
  export:(ids,format)=>invoke('export',ids,format)
});
