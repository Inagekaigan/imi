'use strict';
// Separate linguistic baseline. These are evidence rules, never neural output.
const {validatePair}=require('./engine.cjs');
function cue(text,re){const m=re.exec(text);return m?{start:m.index,end:m.index+m[0].length,text:m[0]}:null;}
function analyzeRules(pair){
  const {japanese,english}=validatePair(pair);const findings=[];
  function add(category,title,jp,en,explanation){findings.push({category,title,japanese:jp,english:en,explanation,origin:'rule',score:null,confidence:null});}
  const partial=cue(japanese,/(?:全員|すべて|全て|皆).+?わけでは(?:ない|ありません)/u);
  const none=cue(english,/\b(?:nobody|no one|none(?: of (?:them|the\s+\w+))?|not a single\s+\w+)\b/i);
  const all=cue(english,/\b(?:everyone|everybody|all of them|all the\s+\w+)\b/i);
  const partialEnglish=/\bnot (?:everyone|everybody|all)\b|not (?:the case|true) that (?:everyone|everybody|all)/i.test(english);
  if(partial && none)add('negation','Quantifier scope changed',partial,none,'The Japanese denies that everyone satisfies the statement. “Nobody” says that zero people do. These are different claims.');
  else if(partial && all && !partialEnglish && !/\bnot\b/i.test(english))add('negation','Quantifier scope changed',partial,all,'The original says the statement is not true of everyone. The English asserts it of everyone.');
  const deadline=cue(japanese,/(?:午前|午後)?[0-9０-９一二三四五六七八九十]+時(?:[0-9０-９]+分)?までに/u);
  const at=cue(english,/\bat\s+(?:\d{1,2}(?::\d{2})?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?:\s*(?:a\.?m\.?|p\.?m\.?|o['’]clock))?/i);
  if(deadline && at && !/\b(?:by|no later than|on or before)\b/i.test(english))add('temporal','Deadline changed to an exact time',deadline,at,'までに sets a deadline: no later than this time. “At” schedules the action for that time rather than allowing completion earlier.');
  const before=cue(japanese,/前に/u),after=cue(japanese,/後に/u);
  if(before && !after && /\bafter\b/i.test(english) && !/\bbefore\b/i.test(english))add('temporal','Before / after reversal',before,cue(english,/\bafter\b/i),'The source says before; the translation says after. Check the event order in context.');
  if(after && !before && /\bbefore\b/i.test(english) && !/\bafter\b/i.test(english))add('temporal','Before / after reversal',after,cue(english,/\bbefore\b/i),'The source says after; the translation says before. Check the event order in context.');
  return {japanese,english,findings,verdict:findings.length?'potential_meaning_change':'uncertain',origin:'rule',note:'Narrow linguistic evidence rules. Absence of a finding does not establish equivalence.'};
}
module.exports={analyzeRules};
