'use strict';

// Authored synthetic templates, not a real-world benchmark. Entire template
// families are reserved for evaluation to avoid source-pair leakage.
function dataset() {
  const rows = [];
  const add = (group, split, japanese, english, labels) => rows.push({id: `synthetic-${rows.length + 1}`, group, split, japanese, english, labels});
  const predicates = [
    ['culprit','彼は犯人','He is the culprit', 'He is not the culprit','train'],
    ['student','彼女は学生','She is a student','She is not a student','train'],
    ['safe','この場所は安全','This place is safe','This place is not safe','train'],
    ['necessary','それは必要','It is necessary','It is not necessary','train'],
    ['doctor','彼は医者','He is a doctor','He is not a doctor','test'],
    ['true','その話は本当','The story is true','The story is not true','test']
  ];
  for (const [group, jp, positive, negative, split] of predicates) {
    for (const jneg of [false,true]) for (const eneg of [false,true]) {
      add(group, split, jp + (jneg ? 'ではない。' : 'だ。'), eneg ? negative + '.' : positive + '.', jneg !== eneg ? ['negation'] : []);
      for (const [js, es] of [['可能性がある','possibly'],['可能性が高い','probably']]) {
        for (const translateModal of [false,true]) {
          const base = (eneg ? negative : positive).replace(' is ', ` is ${translateModal ? es + ' ' : ''}`);
          add(group, split, jp + (jneg ? 'ではない' : 'である') + js + '。', base + '.', [...(jneg !== eneg ? ['negation'] : []), ...(!translateModal ? ['uncertainty'] : [])]);
        }
      }
    }
  }
  const events = [
    ['rain','明日は雨が降る','It','rain tomorrow','train'],
    ['arrive','彼は到着する','He','arrive','train'],
    ['close','店は閉店する','The shop','close','train'],
    ['snow','今夜は雪が降る','It','snow tonight','test'],
    ['depart','電車は出発する','The train','depart','test']
  ];
  const jpModes = ['かもしれない','可能性が高い',''];
  const enModes = ['might','probably will','will'];
  for (const [group, jp, subject, verb, split] of events) for (let a=0;a<3;a++) for(let b=0;b<3;b++) add(group,split,jp + jpModes[a] + '。', `${subject} ${enModes[b]} ${verb}.`,a !== b ? ['uncertainty'] : []);
  const bounds = [['少なくとも','人','at least'],['','人以下','at most'],['','人未満','fewer than'],['ちょうど','人','exactly'],['約','人','about'],['','人超','more than']];
  for (const split of ['train','test']) for (const number of split === 'train' ? [3,10,25,100] : [7,42]) for (let a=0;a<bounds.length;a++) for(let b=0;b<bounds.length;b++) for(const change of [0,2]) {
    const [pre, post] = bounds[a];
    add(`count-${split}`,split,`${pre}${number}${post}が参加した。`,`${bounds[b][2]} ${number + change} people attended.`, a !== b || change ? ['quantity'] : []);
  }
  const names = [['太郎','花子','Taro','Hanako','train'],['アリス','ボブ','Alice','Bob','train'],['健','由美','Ken','Yumi','test']];
  for (const [j1,j2,e1,e2,split] of names) for (const [jverb,everb] of [['助けた','helped'],['押した','pushed'],['呼びました','called'],['見た','saw']]) for(const reversed of [false,true]) add(`roles-${e1}`,split,`${j1}が${j2}を${jverb}。`,`${reversed?e2:e1} ${everb} ${reversed?e1:e2}.`,reversed?['agent']:[]);
  return rows;
}
module.exports = {dataset};
