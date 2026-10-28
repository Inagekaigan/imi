"""Render the recorded pilot report and concise poster. No invented metrics."""
from pathlib import Path
import re,json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfgen import canvas
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet();styles.add(ParagraphStyle('PaperBody',fontName='Times-Roman',fontSize=10.5,leading=14,spaceAfter=8));styles.add(ParagraphStyle('PaperTitle',fontName='Times-Roman',fontSize=25,leading=28,spaceAfter=14));styles.add(ParagraphStyle('PaperHeading',fontName='Helvetica-Bold',fontSize=12,leading=15,spaceBefore=13,spaceAfter=7));styles.add(ParagraphStyle('Cell',fontName='Helvetica',fontSize=7.2,leading=9))
story=[];lines=(ROOT/'docs/PAPER.md').read_text(encoding='utf-8').splitlines();i=0
while i<len(lines):
 line=lines[i].strip()
 if not line:i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   row=[c.strip() for c in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r'[-:]+',c) for c in row):rows.append([Paragraph(html.escape(c),styles['Cell']) for c in row])
   i+=1
  widths=[172]+[(451-172)/(len(rows[0])-1)]*(len(rows[0])-1)
  table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eee9df')),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#555555')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d8d4ca')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story+=[table,Spacer(1,12)];continue
 style='PaperTitle' if line.startswith('# ') else 'PaperHeading' if line.startswith('## ') else 'PaperBody'
 line=re.sub(r'^#+ ','',line).replace('—','-').replace('–','-');story.append(Paragraph(html.escape(line),styles[style]));i+=1

def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#c6c0b4'));c.line(72,48,523,48);c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#77736b'));c.drawString(72,34,'IMI | RESEARCH PILOT | 28 OCTOBER 2026');c.drawRightString(523,34,str(doc.page))
SimpleDocTemplate(str(OUT/'Imi-research-pilot.pdf'),pagesize=(595,842),rightMargin=72,leftMargin=72,topMargin=55,bottomMargin=65,title='Imi: Scope Supervision Research Pilot',author='Imi project - AI-assisted research draft').build(story,onFirstPage=footer,onLaterPages=footer)

W,H=1728,1296;c=canvas.Canvas(str(OUT/'Imi-research-poster.pdf'),pagesize=(W,H));c.setTitle('Imi - Learning the difference, exposing the limits')
paper=colors.HexColor('#f5f2eb');ink=colors.HexColor('#282923');red=colors.HexColor('#af422d');muted=colors.HexColor('#6c6c62')
c.setFillColor(paper);c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(red);c.setFont('Helvetica',16);c.drawString(65,H-65,'IMI / JAPANESE-ENGLISH SEMANTIC ERROR DETECTION / RESEARCH PILOT')
c.setFillColor(ink);c.setFont('Times-Roman',64);c.drawString(65,H-145,'Learning the difference. Exposing the limits.')
c.setFont('Helvetica',20);c.setFillColor(muted);c.drawString(65,H-192,'Real local XLM-R inference. A controlled scope-supervision experiment. An important negative result.')
c.setStrokeColor(ink);c.line(65,H-226,W-65,H-226)
ps=ParagraphStyle('Poster',fontName='Helvetica',fontSize=19,leading=28,textColor=ink,spaceAfter=18)
xs=[65,615,1165];width=495

def block(x,y,title,text):
 c.setFillColor(red);c.setFont('Helvetica-Bold',17);c.drawString(x,y,title.upper());p=Paragraph(text,ps);_,h=p.wrap(width,1000);p.drawOn(c,x,y-26-h);return y-26-h-40

y=H-274
y=block(xs[0],y,'01 / The question','Does auxiliary negation and quantifier-scope supervision improve Japanese-English meaning-error detection, without harming ordinary translations?')
y=block(xs[0],y,'A consequential distinction','<b>Not everyone passed.</b><br/>is not equivalent to<br/><b>Nobody passed.</b><br/><br/>Likewise, a deadline <b>by 3</b> is different from an exact time <b>at 3</b>.')
y=block(xs[0],y,'02 / The experiment','XLM-R base, top four layers fine-tuned. Binary, ten category and error-token heads. Ordinary versus auxiliary scope loss; three seeds each.<br/><br/>Comparators: frozen XLM-R + logistic heads, cue classifier, explicit linguistic rules and a conservative hybrid.')
y=block(xs[0],y,'Data','1,348 training pairs. Natural human-annotated Google/TexTra outputs plus authored contrasts. Separate validation, calibration and final-test documents. Final test: <b>162 natural + 134 authored</b>.')
y=H-274
y=block(xs[1],y,'03 / The central result','The selected neural model performs well on authored contrasts but fails to generalize to natural MT errors. A mixed headline hides this gap.')
for label,value,color in [('Authored contrasts',.857,ink),('Mixed test',.776,muted),('Natural MT',.148,red)]:
 c.setFillColor(ink);c.setFont('Helvetica',18);c.drawString(xs[1],y,label);c.drawRightString(xs[1]+width,y,f'{value:.3f} F1');y-=27;c.setFillColor(colors.HexColor('#e1dbcf'));c.rect(xs[1],y-16,width,16,fill=1,stroke=0);c.setFillColor(color);c.rect(xs[1],y-16,width*value,16,fill=1,stroke=0);y-=57

y=block(xs[1],y,'Scope is not a proven improvement','Mean mixed F1: ordinary <b>0.747 +/- 0.033</b>; scope <b>0.750 +/- 0.029</b> (sample SD, three seeds). The difference is small relative to variability.<br/><br/>Selected-checkpoint grouped 95% F1 interval: <b>[0.452, 0.860]</b>. Only nine test groups.')
y=block(xs[1],y,'A strong simple comparison','Frozen embeddings: natural F1 <b>0.154</b>, versus <b>0.148</b> for selected fine-tuning. Neural superiority is not established.')
y=H-274
y=block(xs[2],y,'04 / Honest uncertainty','The 90% calibration precision target did not support confident positive decisions. Suspected changes remain <b>uncertain</b>.<br/><br/>Test decision coverage: <b>57.8%</b>.<br/>Selective accuracy: <b>88.3%</b>.<br/>All-pair resolved-correct rate: <b>51.0%</b>.<br/><br/>Abstentions are not successes.')
y=block(xs[2],y,'05 / What actually ships','A redesigned Windows desktop app with a local ONNX worker, model comparison, neural and rule highlights, batch imports, exports and separate local feedback.<br/><br/>The verified FP32 graph is used after two uint8 compression trials failed numerical checks.')
y=block(xs[2],y,'06 / The next study','New natural domains and independently annotated error categories. Entirely new templates and test documents. External QE comparisons, annotation agreement and explanation-faithfulness evaluation.<br/><br/><b>Not a validated production detector. No novelty claim.</b>')
c.setStrokeColor(ink);c.line(65,100,W-65,100);c.setFillColor(muted);c.setFont('Helvetica',12)
c.drawString(65,77,'Prior work: XLM-R (Conneau et al., 2020); xCOMET (Guerreiro et al., 2024); negation (Tang et al., 2021); ACES (Moghe et al., 2025).')
c.drawString(65,55,'Natural data: MTPEdocs-MQM. Annotations CC BY-NC-SA 4.0; source rights excluded. Authored examples are not independently verified. AI-assisted pilot, 28 October 2026.')
c.drawString(65,33,'Full protocol, references, per-category results, model hashes and reproduction commands accompany this poster in the Imi source repository.')
c.showPage();c.save();print('Wrote paper and poster PDFs')
