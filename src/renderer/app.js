'use strict';
const $=selector=>document.querySelector(selector);
const examples=[
  {japanese:'彼は犯人ではない可能性が高い。',english:'He is probably the culprit.'},
  {japanese:'明日は雨が降るかもしれない。',english:'It will rain tomorrow.'},
  {japanese:'少なくとも10人が参加した。',english:'Exactly 10 people attended.'},
  {japanese:'太郎が花子を助けた。',english:'Hanako helped Taro.'},
  {japanese:'彼は犯人ではない可能性が高い。',english:'He is probably not the culprit.'},
  {japanese:'全員が試験に合格したわけではない。',english:'Nobody passed the exam.'},
  {japanese:'午後3時までに提出してください。',english:'Please submit it at 3 p.m.'}
];
let current=null, batch=[], state=null, busy=false, toastTimer;
function el(tag,text,className){const element=document.createElement(tag);if(text!==undefined)element.textContent=text;if(className)element.className=className;return element;}
function toast(message,error=false){const box=$('#toast');box.textContent=message;box.classList.toggle('error',error);box.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>box.hidden=true,error?9000:4500);}
async function attempt(fn){try{return await fn();}catch(e){toast(e.message,true);return null;}}
function navigate(page){
  document.querySelectorAll('.page').forEach(s=>s.hidden=s.id!==`page-${page}`);
  document.querySelectorAll('.nav-item').forEach(b=>{b.classList.toggle('active',b.dataset.page===page);b.setAttribute('aria-current',b.dataset.page===page?'page':'false');});
  $('#breadcrumb').textContent={review:'Sentence review',batch:'Batch review',history:'History',model:'About the model'}[page];
  if(page==='history')refreshHistory();
  window.scrollTo({top:0});
}
document.querySelectorAll('[data-page]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.page)));
function counts(){ $('#jp-count').textContent=`${$('#japanese').value.length.toLocaleString()} / 2,000`;$('#en-count').textContent=`${$('#english').value.length.toLocaleString()} / 2,000`;}
function invalidate(){current=null;$('#result').replaceChildren();$('#empty-result').hidden=false;counts();}
for(const id of ['japanese','english'])$('#'+id).addEventListener('input',invalidate);
function setPair(pair){$('#japanese').value=pair.japanese;$('#english').value=pair.english;invalidate();}
$('#clear').addEventListener('click',()=>{setPair({japanese:'',english:''});$('#japanese').focus();});
function evidence(text,span,label){
  const box=el('div',undefined,'evidence');box.append(el('small',label));
  const spans=(Array.isArray(span)?span:span?[span]:[]).filter(s=>s.start>=0&&s.end<=text.length&&s.end>s.start).sort((a,b)=>a.start-b.start);let offset=0;
  for(const s of spans){if(s.start<offset)continue;box.append(document.createTextNode(text.slice(offset,s.start)),el('mark',text.slice(s.start,s.end)));offset=s.end;}
  box.append(document.createTextNode(text.slice(offset)));
  return box;
}
async function exportResults(rows,format){await attempt(async()=>{if(await window.imi.export(rows.map(r=>r.id),format))toast('Analysis exported.');});}
function renderResult(result){
  current=result;$('#empty-result').hidden=true;
  const card=el('div',undefined,'result-card');
  const head=el('div',undefined,'result-head');head.append(el('div',result.findings.length?'!':'≈','result-icon'));
  const verdicts={meaning_altered:'Meaning altered',meaning_preserved:'Meaning preserved',uncertain:'Uncertain'};
  const heading=el('div'),title=el('h2',verdicts[result.verdict]||(result.findings.length?'Potential meaning change':'No targeted mismatch found'));title.id='result-title';
  heading.append(title,el('p',`${result.model.name} · ${result.model.version} · ${Math.round(result.inferenceMs??result.elapsedMs??0)} ms · ${result.origin||'feature classifier'}`));
  if(result.probabilityAltered!==null&&result.probabilityAltered!==undefined)heading.append(el('p',`${(result.probabilityAltered*100).toFixed(1)}% estimated probability of a consequential change · calibrated sentence score`));
  head.append(heading);const exportButton=el('button','Export JSON ↗','secondary');exportButton.addEventListener('click',()=>exportResults([result],'json'));head.append(exportButton);card.append(head);
  const checks=el('div',undefined,'checks');
  (result.checks||[]).forEach(c=>checks.append(el('span',`${c.title.split(' ')[0]} · ${{flagged:'Flagged',not_assessed:'Not assessed',no_mismatch_found:'No mismatch found'}[c.status]}`,`check ${c.status}`)));card.append(checks);
  if(result.neuralSpans){const grid=el('div',undefined,'evidence-grid');grid.append(evidence(result.japanese,result.neuralSpans.japanese,'NEURAL TOKEN EVIDENCE / JAPANESE'),evidence(result.english,result.neuralSpans.english,'NEURAL TOKEN EVIDENCE / ENGLISH'));card.append(grid);}
  result.findings.forEach((f,i)=>{
    const finding=el('article',undefined,'finding');const top=el('div',undefined,'finding-heading');top.append(el('span',`0${i+1} / ${f.origin||'cue evidence'}`),el('h3',f.title));finding.append(top);
    if(f.origin!=='neural'){const grid=el('div',undefined,'evidence-grid');grid.append(evidence(result.japanese,f.japanese,'JAPANESE ORIGINAL'),evidence(result.english,f.english,'ENGLISH TRANSLATION'));finding.append(grid);}finding.append(el('p',f.explanation));card.append(finding);
  });
  const note=el('div',undefined,'result-note');
  if(!result.findings.length)note.append(el('p','No specific error category was identified. Absence of a finding alone does not establish equivalence.'));
  (result.warnings||[]).forEach(w=>note.append(el('p',w)));
  note.append(el('p',result.origin==='neural'?'Highlights come from the trained token head. Category and token scores are uncalibrated; spans are not verified explanations.':'Highlights are linguistic evidence cues, not neural token predictions.'));
  card.append(note);
  for(const comparison of result.comparison||[]){const box=el('div',undefined,'comparison');box.append(el('h3',comparison.model.name),el('p',comparison.findings.length?comparison.findings.map(f=>f.title).join(' · '):'No targeted mismatch found; equivalence not established.'));comparison.findings.forEach(f=>{box.append(evidence(result.japanese,f.japanese,'RULE / JAPANESE'),evidence(result.english,f.english,'RULE / ENGLISH'),el('p',f.explanation));});card.append(box);}
  const feedback=el('div',undefined,'feedback');feedback.append(el('span','Save feedback with this pair locally:'));
  for(const label of ['correct','incorrect','uncertain']){const button=el('button',label,'secondary');button.addEventListener('click',()=>attempt(async()=>{await window.imi.feedback(result.id,label);toast('Feedback saved locally, separate from evaluation data.');}));feedback.append(button);}card.append(feedback);$('#result').replaceChildren(card);
}
async function analyze(){
  if(busy)return;busy=true;$('#analyze').disabled=true;$('#analyze').textContent='Analyzing…';
  const pair={japanese:$('#japanese').value,english:$('#english').value,mode:$('#engine').value};
  try{const result=await window.imi.analyze(pair);if($('#japanese').value===pair.japanese&&$('#english').value===pair.english)renderResult(result);}
  catch(e){toast(e.message,true);}finally{busy=false;$('#analyze').disabled=false;$('#analyze').replaceChildren(document.createTextNode('Analyze meaning '),el('span','↗'));}
}
$('#analyze').addEventListener('click',analyze);
document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key==='Enter'&&!$('#page-review').hidden){event.preventDefault();analyze();}});
document.querySelectorAll('[data-example]').forEach(b=>b.addEventListener('click',()=>{if(busy)return;setPair(examples[Number(b.dataset.example)]);analyze();}));
function renderList(target,rows,empty){
  target.replaceChildren();
  if(!rows.length){const box=el('div',undefined,'empty-result');box.append(el('h2',empty),el('p','Your sentence pairs will appear here after analysis.'));target.append(box);return;}
  const toolbar=el('div',undefined,'list-toolbar');toolbar.append(el('h2',`${rows.length} pair${rows.length===1?'':'s'} · ${rows.filter(r=>r.findings.length).length} flagged`));
  const exports=el('div',undefined,'export-group');for(const format of ['json','csv']){const b=el('button',`Export ${format.toUpperCase()}`,'secondary');b.addEventListener('click',()=>exportResults(rows,format));exports.append(b);}toolbar.append(exports);target.append(toolbar);
  rows.forEach(r=>{const item=el('button',undefined,'list-item');item.append(el('h3',r.japanese),el('p',r.english));const meta=el('div',undefined,'list-meta');meta.append(el('span',r.findings.length?r.findings.map(f=>f.title).join(' · '):'No targeted mismatch found',r.findings.length?'flag':''),el('span',new Date(r.createdAt).toLocaleString()));item.append(meta);item.addEventListener('click',()=>{navigate('review');setPair(r);renderResult(r);});target.append(item);});
}
$('#import-batch').addEventListener('click',async()=>{
  const button=$('#import-batch');button.disabled=true;
  await attempt(async()=>{const rows=await window.imi.batch($('#engine').value);if(rows){batch=rows;renderList($('#batch-results'),batch,'No batch imported yet');toast(`Reviewed ${rows.length} pairs locally.`);}});
  button.disabled=false;
});
async function refreshHistory(){await attempt(async()=>{state=await window.imi.state();$('#save-history').checked=state.settings.saveHistory;renderList($('#history-results'),state.history,'No saved analyses yet');});}
$('#save-history').addEventListener('change',()=>attempt(async()=>{try{await window.imi.setHistory($('#save-history').checked);toast($('#save-history').checked?'Future analyses will be saved locally.':'History is off. Previously saved analyses remain until deleted.');}finally{await refreshHistory();}}));
$('#clear-history').addEventListener('click',()=>attempt(async()=>{if(!state?.history.length){toast('There is no saved history to delete.');return;}if(!window.confirm('Delete all saved analysis history from this device? This cannot be undone.'))return;await window.imi.clearHistory();await refreshHistory();toast('Saved history deleted.');}));
async function initialize(){
  state=await window.imi.state();$('#save-history').checked=state.settings.saveHistory;
  $('#model-description').textContent=state.neural?.architecture||'The neural model is not installed. Only the original cue-feature classifier and linguistic rules are available.';
  $('#model-version').textContent=state.neural?`${state.neural.name} · ${state.neural.version} · ${state.neural.checkpoint}`:'Original baseline · 0.1.0';
  if(!state.neural){$('#engine').value='baseline';for(const option of $('#engine').options)if(['neural','compare'].includes(option.value))option.disabled=true;}
  $('#evaluation-summary').textContent=state.neural?.evaluationSummary||`Original baseline only: ${state.model.trainRows} synthetic training pairs · ${state.model.testRows} held-out pairs. These numbers do not evaluate the neural model.`;
  const table=el('table'),head=el('thead'),hr=el('tr');const neuralRows=state.neural?.evaluationRows;
  (neuralRows?['Model','Mixed F1','Natural MT F1','Decision coverage']:['Original baseline category','True positives','False positives','Missed errors']).forEach(t=>hr.append(el('th',t)));head.append(hr);table.append(head);const body=el('tbody');
  (neuralRows||state.evaluation.metrics).forEach(m=>{const tr=el('tr');(neuralRows?[m.name,m.f1.toFixed(3),m.naturalF1.toFixed(3),(m.coverage*100).toFixed(1)+'%']:[m.category,m.tp,m.fp,m.fn]).forEach(t=>tr.append(el('td',String(t))));body.append(tr);});table.append(body);$('#evaluation-table').append(table);
  renderList($('#batch-results'),batch,'No batch imported yet');counts();
}
window.imi.onBatchProgress(progress=>$('#batch-progress').textContent=`Reviewed ${progress.done} / ${progress.total} pairs`);
$('#engine').addEventListener('change',invalidate);
attempt(initialize);
