'use strict';
const {validatePair} = require('./engine.cjs');
function parsePairs(text, extension) {
  if (Buffer.byteLength(text,'utf8') > 10*1024*1024) throw new Error('Import must be smaller than 10 MB.');
  let values;
  try {values = extension === '.csv' ? parseCsv(text) : extension === '.jsonl' ? text.replace(/^\uFEFF/,'').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse) : JSON.parse(text.replace(/^\uFEFF/,''));}
  catch {throw new Error('Could not read the file. Use a JSON array or one JSON object per line in a .jsonl file.');}
  if (!Array.isArray(values) || !values.length || values.length>5000) throw new Error('Import between 1 and 5000 sentence pairs.');
  return values.map((p,i)=>{try {return validatePair(p);} catch(e) {throw new Error(`Pair ${i+1}: ${e.message}`);}});
}
function parseCsv(text){
  text=text.replace(/^\uFEFF/,'');const rows=[];let row=[],cell='',quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else if(quoted||cell==='')quoted=!quoted;else throw new Error('Invalid CSV quotes.');}
    else if(c===','&&!quoted){row.push(cell);cell='';}else if((c==='\r'||c==='\n')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell='';}else cell+=c;}
  if(quoted)throw new Error('Unclosed CSV quote.');row.push(cell);if(row.some(Boolean))rows.push(row);
  const header=rows.shift()?.map(s=>s.trim().toLowerCase());const ja=header?.indexOf('japanese'),en=header?.indexOf('english');
  if(ja===undefined||ja<0||en<0)throw new Error('CSV requires japanese and english columns.');
  return rows.map(r=>({japanese:r[ja],english:r[en]}));
}
function csv(results) {
  const cell = value => {
    let text = String(value ?? '');
    if (/^[\s]*[=+@\-]/.test(text)) text="'"+text;
    return '"'+text.replaceAll('"','""')+'"';
  };
  const rows = [['Japanese','English','Verdict','Categories','Explanations','Model','Limitations','Probability altered','Origin','Milliseconds','Spans JSON'],...results.map(r=>[r.japanese,r.english,r.verdict,r.findings.map(f=>f.title).join('; '),r.findings.map(f=>f.explanation).join('; '),r.model.name+' '+r.model.version,r.note,r.probabilityAltered,r.origin,r.inferenceMs??r.elapsedMs,JSON.stringify(r.neuralSpans||r.findings.map(f=>({japanese:f.japanese,english:f.english})))])];
  return '\uFEFF'+rows.map(r=>r.map(cell).join(',')).join('\r\n');
}
module.exports={parsePairs,csv};
