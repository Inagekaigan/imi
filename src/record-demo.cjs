'use strict';
// A low-frame-rate recording of actual live app rendering, in a temporary profile.
const fs=require('node:fs/promises'),path=require('node:path');
module.exports=async({window,root})=>{
  const directory=path.join(root,'docs/demo-frames');await fs.mkdir(directory,{recursive:true});
  const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  await pause(1000);let count=0;
  async function record(ms){const end=Date.now()+ms;while(Date.now()<end){const capture=await window.webContents.capturePage();await fs.writeFile(path.join(directory,`${String(count++).padStart(4,'0')}.png`),capture.toPNG());await pause(250);}}
  await record(1500);
  await window.webContents.executeJavaScript(`document.querySelector('#engine').value='compare';document.querySelector('[data-example="5"]').click();`);
  await record(2500);
  await window.webContents.executeJavaScript(`(async()=>{while(document.querySelector('#analyze').disabled)await new Promise(r=>setTimeout(r,100));})()`);
  await window.webContents.executeJavaScript(`document.querySelector('#result').scrollIntoView();`);await record(4000);
  await window.webContents.executeJavaScript(`window.scrollTo(0,document.body.scrollHeight);`);await record(3500);
  await window.webContents.executeJavaScript(`window.scrollTo(0,0);document.querySelector('[data-example="6"]').click();`);await record(2000);
  await window.webContents.executeJavaScript(`(async()=>{while(document.querySelector('#analyze').disabled)await new Promise(r=>setTimeout(r,100));})()`);
  await window.webContents.executeJavaScript(`document.querySelector('#result').scrollIntoView();`);await record(3500);
  await window.webContents.executeJavaScript(`window.scrollTo(0,document.body.scrollHeight);`);await record(3500);
  await fs.writeFile(path.join(directory,'recording.json'),JSON.stringify({frames:count,method:'Live Electron capturePage at approximately 4 fps; automated demo inputs; model preloaded before recording; no fabricated predictions.'},null,2));
};
