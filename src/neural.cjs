'use strict';
const {spawn}=require('node:child_process');
const {createInterface}=require('node:readline');
const path=require('node:path');
const fs=require('node:fs');
class NeuralWorker {
  constructor(root,packaged=false){this.root=root;this.packaged=packaged;this.pending=new Map();this.sequence=0;}
  manifest(){const p=path.join(this.root,'model/neural/manifest.json');return fs.existsSync(p)?JSON.parse(fs.readFileSync(p,'utf8')):null;}
  async start(){
    if(this.ready)return this.ready;
    this.ready=new Promise((resolve,reject)=>{
      const executable=this.packaged?path.join(this.root,'backend/imi-inference.exe'):path.join(this.root,'.venv/Scripts/python.exe');
      const args=[...(this.packaged?[]:[path.join(this.root,'research/infer.py')]),'--model',path.join(this.root,'model/neural')];
      this.child=spawn(executable,args,{windowsHide:true,stdio:['pipe','pipe','pipe'],env:{...process.env,HF_HUB_OFFLINE:'1',TRANSFORMERS_OFFLINE:'1',PYTHONIOENCODING:'utf-8'}});
      const timer=setTimeout(()=>{reject(new Error('The local model took too long to load. Restart Imi.'));this.close();},90000);
      let diagnostics='';this.child.stderr.on('data',d=>diagnostics=(diagnostics+d.toString()).slice(-2000));
      createInterface({input:this.child.stdout}).on('line',line=>{try{const response=JSON.parse(line);if(response.ready){clearTimeout(timer);resolve();return;}const request=this.pending.get(response.id);if(request){clearTimeout(request.timer);this.pending.delete(response.id);response.ok?request.resolve(response.data):request.reject(new Error(response.error));}}catch{}});
      const fail=error=>{clearTimeout(timer);reject(error);for(const request of this.pending.values()){clearTimeout(request.timer);request.reject(error);}this.pending.clear();this.ready=null;};
      this.child.on('error',()=>fail(new Error('Local inference is unavailable. Install the bundled model and inference runtime.')));
      this.child.on('exit',code=>fail(new Error(`Local inference stopped (${code}). ${diagnostics}`)));
    });return this.ready;
  }
  async analyze(pair){await this.start();return new Promise((resolve,reject)=>{const id=++this.sequence;const timer=setTimeout(()=>{this.pending.delete(id);reject(new Error('Analysis timed out. Please restart Imi.'));},60000);this.pending.set(id,{resolve,reject,timer});this.child.stdin.write(JSON.stringify({id,...pair})+'\n');});}
  close(){this.child?.kill();this.ready=null;}
}
module.exports={NeuralWorker};
