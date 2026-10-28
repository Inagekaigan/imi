'use strict';

const LABELS = ['negation', 'uncertainty', 'quantity', 'agent'];
const TITLES = ['Negation reversal', 'Uncertainty distortion', 'Quantity distortion', 'Agent reversal'];
const FEATURES = ['negation_omitted', 'negation_added', 'certainty_strengthened', 'certainty_weakened', 'number_changed', 'bound_changed', 'roles_reversed', 'polarity_agrees', 'certainty_agrees', 'quantity_agrees', 'roles_agree'];
const MAX_LENGTH = 2000;
const span = (text, match) => match ? {start: match.index, end: match.index + match[0].length, text: text.slice(match.index, match.index + match[0].length)} : null;
function matchSpan(text, regex) { return span(text, regex.exec(text)); }
function whole(text) { return {start: 0, end: text.length, text}; }
function validatePair(pair) {
  if (!pair || typeof pair.japanese !== 'string' || typeof pair.english !== 'string') throw new Error('Each pair needs japanese and english text fields.');
  const japanese = pair.japanese.trim(), english = pair.english.trim();
  if (!japanese || !english) throw new Error('Enter both the Japanese original and the English translation.');
  if (japanese.length > MAX_LENGTH || english.length > MAX_LENGTH) throw new Error(`Each sentence must be ${MAX_LENGTH} characters or fewer.`);
  if (!/[\u3040-\u30ff\u3400-\u9fff]/u.test(japanese)) throw new Error('The original must contain Japanese text.');
  if (!/[a-z]/i.test(english)) throw new Error('The translation must contain English text.');
  return {japanese, english};
}
const JP_NEG = /ではなかった|ではありません|ではない|じゃない|なかった|ませんでした|ません|していない|ていない|しない|くない|ない|ずに/u;
const EN_NEG = /\b(?:not|never|no|cannot|neither|without|\w+n['’]t)\b/i;
function certainty(text, jp) {
  const patterns = jp ? [
    [1, /かもしれ(?:ない|ません)|可能性がある|可能性があります|おそれがある/u],
    [2, /可能性が高い|おそらく|たぶん|多分|でしょう|だろう/u],
    [3, /必ず|確実に|絶対に/u]
  ] : [[1, /\b(?:might|may|could|possibly|perhaps|possible)\b/i], [2, /\b(?:probably|likely|probably won't)\b/i], [3, /\b(?:will|definitely|certainly|must|guaranteed)\b/i]];
  for (const [level, regex] of patterns) { const evidence = matchSpan(text, regex); if (evidence) return {level, evidence}; }
  return {level: 3, evidence: null};
}
function polarity(text, jp) {
  // Modal ない is not proposition negation: 行くかもしれない = might go.
  const masked = jp ? text.replace(/かもしれ(?:ない|ません)/gu, m => ' '.repeat(m.length)) : text.replace(/\bno (?:fewer|more) than\b/gi, m => ' '.repeat(m.length));
  return matchSpan(text, {exec: () => (jp ? JP_NEG : EN_NEG).exec(masked)});
}
function quantity(text, jp) {
  const normalized = text.replace(/[０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0));
  const regex = jp ? /(?:(?:少なくとも|最大|最低|ちょうど|約)\s*)?\d+(?:\.\d+)?\s*(?:人|個|件|台|冊|円|回|日|匹|本|枚|%|％)?\s*(?:以上|以下|未満|超|より多い|より少ない)?/gu : /(?:(?:at least|at most|no fewer than|no more than|more than|less than|fewer than|exactly|about|approximately|over|under)\s+)?\d+(?:\.\d+)?(?:\s+(?:or more|or fewer|or less))?/gi;
  const matches = [...normalized.matchAll(regex)];
  if (matches.length !== 1) return null;
  const m = matches[0], s = m[0].toLowerCase();
  let bound = 'unspecified';
  if (/以上|少なくとも|最低|at least|no fewer than|or more/.test(s)) bound = 'gte';
  else if (/以下|最大|at most|no more than|or fewer|or less/.test(s)) bound = 'lte';
  else if (/未満|より少ない|less than|fewer than|under/.test(s)) bound = 'lt';
  else if (/超|より多い|more than|over/.test(s)) bound = 'gt';
  else if (/ちょうど|exactly/.test(s)) bound = 'eq';
  else if (/約|about|approximately/.test(s)) bound = 'approx';
  return {value: Number(s.match(/\d+(?:\.\d+)?/)[0]), bound, evidence: span(text, m)};
}
const NAMES = {太郎:'Taro',花子:'Hanako',健:'Ken',由美:'Yumi',アリス:'Alice',ボブ:'Bob',ジョン:'John',メアリー:'Mary'};
function agents(japanese, english) {
  // Deliberately narrow active-transitive grammar; passive/causative cases abstain.
  if (/られ|された|させ|によって/u.test(japanese) || /\b(?:by|was|were|is|are|been)\b/i.test(english)) return null;
  const names = Object.keys(NAMES).join('|');
  const m = new RegExp(`(${names})(?:は|が)(${names})を(?:助け|押し|追いかけ|呼び|殴っ|見|訪ね)`, 'u').exec(japanese);
  if (!m || m[1] === m[2]) return null;
  const action = /\b(helped|helps|pushed|pushes|chased|chases|called|calls|hit|hits|saw|sees|visited|visits)\b/i.exec(english);
  if (!action) return null;
  const first = new RegExp(`\\b(${Object.values(NAMES).join('|')})\\b`, 'i').exec(english.slice(0, action.index));
  const second = new RegExp(`\\b(${Object.values(NAMES).join('|')})\\b`, 'i').exec(english.slice(action.index + action[0].length));
  if (!first || !second) return null;
  const subject = first[0].toLowerCase(), object = second[0].toLowerCase();
  const expectedSubject = NAMES[m[1]].toLowerCase(), expectedObject = NAMES[m[2]].toLowerCase();
  const reverse = subject === expectedObject && object === expectedSubject;
  const agree = subject === expectedSubject && object === expectedObject;
  if (!reverse && !agree) return null;
  return {reverse, agree, jp: span(japanese, m), en: whole(english), subject: NAMES[m[1]], object: NAMES[m[2]]};
}
function extract(pair) {
  const {japanese: jp, english: en} = validatePair(pair);
  const warnings = [];
  const complex = /わけでは|とは限ら|なくはない|ないことはない|なければ|ないと|ざるを得|しか|だけでなく|ずには|ないよう|ないで|なくても|ないか|^もし|[「」『』]|と言|と思|と考/u.test(jp) || /\b(?:unless|not only|not unlikely|not impossible|if|said|says|thought|thinks)\b/i.test(en) || jp.split(/[。！？!?]/).filter(s => s.trim()).length > 1 || en.split(/[.!?](?:\s|$)/).filter(s => s.trim()).length > 1;
  if (complex) warnings.push('Scope is complex (for example, a conditional, quotation, or multiple clauses). Polarity and certainty checks abstained.');
  const jn = polarity(jp, true), eneg = polarity(en, false), jc = certainty(jp, true), ec = certainty(en, false);
  const jq = quantity(jp, true), eq = quantity(en, false), roles = agents(jp, en);
  const negCoverage = !complex && (!!jn || !!eneg);
  const certaintyCoverage = !complex && (!!jc.evidence || !!ec.evidence);
  // A bare count does not unambiguously assert an exact bound.
  const boundsComparable = jq && eq && jq.bound !== 'unspecified' && eq.bound !== 'unspecified';
  const quantityCoverage = !!(jq && eq);
  if (jq && eq && jq.bound !== eq.bound && !boundsComparable) warnings.push('A quantity bound is implicit on one side. Review the highlighted count manually.');
  const x = [
    +(negCoverage && !!jn && !eneg), +(negCoverage && !jn && !!eneg),
    +(certaintyCoverage && jc.level < ec.level), +(certaintyCoverage && jc.level > ec.level),
    +(quantityCoverage && jq.value !== eq.value), +(boundsComparable && jq.bound !== eq.bound),
    +(!!roles && roles.reverse), +(negCoverage && !!jn === !!eneg),
    +(certaintyCoverage && jc.level === ec.level), +(quantityCoverage && jq.value === eq.value && jq.bound === eq.bound), +(!!roles && roles.agree)
  ];
  const coverage = [negCoverage, certaintyCoverage, quantityCoverage, !!roles];
  const evidence = [
    {japanese: jn || whole(jp), english: eneg || whole(en), explanation: jn ? 'A Japanese negative marker has no matching English negative marker. The translation may reverse the proposition.' : 'The English introduces a negative marker absent from the Japanese. The proposition may be reversed.'},
    {japanese: jc.evidence || whole(jp), english: ec.evidence || whole(en), explanation: jc.level < ec.level ? 'A possibility or likelihood in the original becomes a stronger assertion in English.' : 'A stronger assertion in the original becomes more tentative in English.'},
    {japanese: jq?.evidence || null, english: eq?.evidence || null, explanation: jq && eq ? `The numeric expression changes from ${jq.value} (${jq.bound}) to ${eq.value} (${eq.bound}).` : ''},
    {japanese: roles?.jp || null, english: roles?.en || null, explanation: roles ? `The Japanese names ${roles.subject} as the actor and ${roles.object} as the recipient. The English swaps these roles.` : ''}
  ];
  return {x, coverage, evidence, warnings, pair: {japanese: jp, english: en}};
}
const sigmoid = z => 1 / (1 + Math.exp(-Math.max(-40, Math.min(40, z))));
function analyze(pair, model) {
  if (!model || model.schemaVersion !== 1 || JSON.stringify(model.features) !== JSON.stringify(FEATURES) || !Array.isArray(model.weights) || model.weights.length !== 4) throw new Error('Incompatible model file. Run npm run train to rebuild it.');
  const e = extract(pair);
  const scores = model.weights.map(w => sigmoid(w[0] + e.x.reduce((s, v, i) => s + v * w[i + 1], 0)));
  const findings = LABELS.flatMap((label, i) => e.coverage[i] && scores[i] >= model.threshold ? [{category: label, title: TITLES[i], score: Number(scores[i].toFixed(4)), ...e.evidence[i]}] : []);
  return {schemaVersion: 1, ...e.pair, verdict: findings.length ? 'potential_meaning_change' : 'review_required', findings, checks: LABELS.map((category, i) => ({category, title: TITLES[i], status: !e.coverage[i] ? 'not_assessed' : findings.some(f => f.category === category) ? 'flagged' : 'no_mismatch_found'})), warnings: e.warnings, model: {name: model.name, version: model.version, training: model.training}, note: 'Experimental synthetic-trained baseline. Scores are not calibrated confidence. No finding does not establish translation accuracy. Phrase spans are rule-based evidence, not learned alignments.'};
}
module.exports = {LABELS, TITLES, FEATURES, MAX_LENGTH, validatePair, extract, analyze, sigmoid};
