"""Authored, NOT human-verified contrastive families. No final-test tuning."""
import re
from schema import LABELS

def marked(text):
    output = ''; spans = []; opened = {}
    for part in re.split(r'(</?[ecs]>)', text):
        if part in ['<e>', '<c>', '<s>']: opened[part[1]] = len(output)
        elif part in ['</e>', '</c>', '</s>']:
            tag = part[2]; spans.append({'start': opened.pop(tag), 'end': len(output), 'kind': tag})
        else: output += part
    return output, spans

def generate():
    rows = []
    def add(group, split, jp, en, labels, domain='constructed'):
        japanese, js = marked(jp); english, es = marked(en)
        rows.append({'id':f'contrast-{len(rows):05}', 'group':group, 'split':split,
                     'japanese':japanese,'english':english,'altered':int(bool(labels)),
                     'labels':[int(l in labels) for l in LABELS], 'source':'authored_contrastive',
                     'human_verified':False,'domain':domain,'system':'constructed',
                     'japanese_spans':[s for s in js if s['kind'] in ['e','c']] if labels else [],
                     'english_spans':[s for s in es if s['kind']=='e'] if labels else [],
                     'scope_spans':[s for s in js if s['kind'] in ['c','s']],
                     'span_supervision':['japanese','english'], 'scope_supervision':any(s['kind'] in ['c','s'] for s in js)})
    # Hold out complete semantic predicate families, including paraphrase variants.
    contexts = [
        ('試験に合格した','passed the exam','train'),('会議に出席した','attended the meeting','train'),
        ('契約に署名した','signed the contract','train'),('計画に賛成した','approved the plan','train'),
        ('薬を飲んだ','took the medicine','train'),('申請書を提出した','submitted the form','train'),
        ('説明を理解した','understood the explanation','validation'),
        ('映画を見た','watched the film','calibration'),
        ('料金を支払った','paid the fee','test'),('招待を受け入れた','accepted the invitation','test')]
    for index,(jp,en,split) in enumerate(contexts):
        group=f'scope-family-{index}'
        original=f'<s>全員が{jp}</s><c>わけではない</c>。'
        for good in [f'Not everyone {en}.',f'It is not the case that everyone {en}.',f'Not all of them {en}.']:
            add(group,split,original,good,[])
        for bad in [f'<e>Nobody</e> {en}.',f'<e>Everyone</e> {en}.',f'<e>All of them</e> {en}.']:
            add(group,split,original,bad,['negation'])
        add(group,split,f'<s>全員が{jp}</s>。',f'Everyone {en}.',[])
        add(group,split,f'<s>全員が{jp}</s>。',f'<e>Nobody</e> {en}.',['negation'])
        add(group,split,f'<s>彼が{jp}</s><c>わけではない</c>。',f'It is not true that he {en}.',[])
        add(group,split,f'<s>彼が{jp}</s><c>わけではない</c>。',f'He {en}.',['negation'])
    events=[('雨が降る','rain','It','train'),('彼が到着する','arrive','He','train'),('店が閉まる','close','The shop','train'),
            ('電車が出発する','depart','The train','train'),('雪が降る','snow','It','validation'),
            ('会議が終わる','end','The meeting','calibration'),('橋が崩れる','collapse','The bridge','test')]
    for i,(jp,verb,subject,split) in enumerate(events):
        for level,(jmode,emodes) in enumerate([('かもしれない',['might','may','could possibly']),('可能性が高い',['will probably','is likely to']),('', ['will','will certainly'])]):
            source=f'<s>{jp}</s><c>{jmode}</c>。' if jmode else jp+'。'
            for target_level,(_,targets) in enumerate([('', ['might','may','could possibly']),('', ['will probably','is likely to']),('', ['will','will certainly'])]):
                for modal in targets:
                    add(f'modal-family-{i}',split,source,f'{subject} '+(f'<e>{modal}</e>' if target_level!=level else modal)+f' {verb}.',[] if level==target_level else ['uncertainty'])
    objects=[('報告書','the report','train'),('申請書','the application','train'),('荷物','the parcel','train'),
             ('請求書','the invoice','validation'),('論文','the paper','calibration'),('見積書','the estimate','test')]
    for i,(jp,en,split) in enumerate(objects):
        for hour in [2,3,5,8]:
            source=f'{jp}を<e>午後{hour}時までに</e>提出してください。'
            add(f'deadline-family-{i}',split,source,f'Please submit {en} <e>at {hour} p.m.</e>.',['temporal'])
            add(f'deadline-family-{i}',split,source,f'Please submit {en} by {hour} p.m.',[])
            add(f'deadline-family-{i}',split,source,f'Please hand in {en} no later than {hour} p.m.',[])
    nouns=[('人','people','train'),('冊','books','train'),('台','machines','train'),('件','cases','validation'),('個','items','calibration'),('匹','animals','test')]
    bounds=[('少なくとも','','at least'),('','以下','at most'),('ちょうど','','exactly'),('約','','about'),('','未満','fewer than')]
    for i,(unit,enunit,split) in enumerate(nouns):
        for count in [3,10,25]:
            for a,(pre,post,eng) in enumerate(bounds):
                for b,(_,_,badeng) in enumerate(bounds):
                    add(f'quantity-family-{i}',split,f'<e>{pre}{count}{unit}{post}</e>が必要だ。',f'We need <e>{badeng} {count}</e> {enunit}.',[] if a==b else ['quantity'])
    actions=[('助けた','helped','train'),('追いかけた','chased','train'),('招待した','invited','train'),('訪ねた','visited','validation'),('押した','pushed','calibration'),('呼んだ','called','test')]
    for i,(ja,en,split) in enumerate(actions):
        for j1,j2,e1,e2 in [('太郎','花子','Taro','Hanako'),('アリス','ボブ','Alice','Bob'),('健','由美','Ken','Yumi')]:
            add(f'agent-family-{i}',split,f'<e>{j1}が{j2}を</e>{ja}。',f'<e>{e2}</e> {en} <e>{e1}</e>.',['agent'])
            add(f'agent-family-{i}',split,f'{j1}が{j2}を{ja}。',f'{e1} {en} {e2}.',[])
    # Diverse development constructions; do not pretend these cover arbitrary syntax.
    special=[
      ('この薬は眠る前に飲んでください。','Take this medicine before sleeping.','Take this medicine <e>after</e> sleeping.','temporal'),
      ('太郎は花子に助けられた。','Hanako helped Taro.','<e>Taro helped Hanako</e>.','agent'),
      ('先生は生徒に本を読ませた。','The teacher made the student read a book.','The <e>student made the teacher</e> read a book.','agent'),
      ('ここで写真を撮ってもよい。','You may take photos here.','You <e>must not</e> take photos here.','uncertainty'),
      ('ここでは喫煙してはいけない。','Smoking is prohibited here.','Smoking is <e>permitted</e> here.','negation'),
      ('雨が降れば試合を中止する。','If it rains, the match will be canceled.','The match will be canceled <e>whether or not it rains</e>.','conditional'),
      ('鍵をなくしたので家に入れなかった。','I could not enter the house because I lost the key.','I <e>lost the key because I could not enter the house</e>.','other'),
      ('東京ではなく大阪に住んでいる。','They live in Osaka, not Tokyo.','They live in <e>Tokyo, not Osaka</e>.','entity_terminology'),
      ('水を500ミリリットル加えてください。','Add half a liter of water.','Add <e>500 liters</e> of water.','quantity'),
      ('彼女は私より背が高い。','She is taller than I am.','She is <e>shorter</e> than I am.','other'),
      ('会議は来週の月曜日に始まる。','The meeting starts next Monday.','The meeting starts <e>next Tuesday</e>.','temporal'),
      ('到着したら電話してください。','Please call when you arrive.','Please call <e>before you arrive</e>.','temporal'),
      ('彼は犯人ではない可能性が高い。','He is probably not the culprit.','He is <e>certainly the culprit</e>.','negation'),
    ]
    for i,(jp,good,bad,category) in enumerate(special):
        add(f'development-construction-{i}','train',jp,good,[])
        add(f'development-construction-{i}','train',jp,bad,[category]+(['uncertainty'] if i==12 else []))
    return rows
