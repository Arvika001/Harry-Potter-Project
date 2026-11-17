"""Book 1 dialogue candidates and conservative Gephi network. Requires PyMuPDF."""
import argparse, csv, re
from collections import Counter
from pathlib import Path
import pymupdf

ALIASES = {
 'Harry':['Harry','Harry Potter'], 'Ron':['Ron','Ron Weasley'],
 'Hermione':['Hermione','Hermione Granger'], 'Dumbledore':['Dumbledore','Albus Dumbledore'],
 'Hagrid':['Hagrid'], 'McGonagall':['McGonagall','Professor McGonagall'],
 'Snape':['Snape','Professor Snape'], 'Draco':['Draco','Malfoy','Draco Malfoy'],
 'Vernon':['Vernon','Uncle Vernon','Mr. Dursley'],
 'Petunia':['Petunia','Aunt Petunia','Mrs. Dursley'], 'Dudley':['Dudley'],
 'Quirrell':['Quirrell','Professor Quirrell'], 'Neville':['Neville','Neville Longbottom'],
 'Fred':['Fred'], 'George':['George'], 'Percy':['Percy'], 'Ginny':['Ginny'],
 'Molly':['Mrs. Weasley','Molly'], 'Arthur':['Mr. Weasley','Arthur'],
 'Filch':['Filch'], 'Wood':['Oliver Wood','Wood'], 'Seamus':['Seamus'],
 'Dean':['Dean'], 'Flitwick':['Flitwick'], 'Piers':['Piers'],
 'McGuffin':['Jim McGuffin'], 'Ted':['Ted'],
}
LOOKUP={a.casefold():n for n,aliases in ALIASES.items() for a in aliases}
NAME_RE=re.compile(r'(?<!\w)(?:'+ '|'.join(re.escape(a) for a in sorted(LOOKUP,key=len,reverse=True))+r')(?!\w)',re.I)
VERBS=r'(?:said|asked|replied|shouted|whispered|cried|muttered|yelled|called|snapped|demanded|answered|added|exclaimed|growled|hissed|suggested|murmured|sobbed|grunted|chortled|remarked|continued|began|interrupted|barked|roared|squeaked|stammered|protested|admitted|explained|warned|urged|agreed)'
QUOTE_RE=re.compile(r'[“\"]([^”\"]{2,1200})[”\"]',re.S)
POST_VERB=re.compile(r'^\s*[,!?;:.—–-]*\s*'+VERBS+r'\s+(.{0,75})',re.I|re.S)
POST_NAME=re.compile(r'^\s*[,!?;:.—–-]*\s*(.{1,70}?)\s+'+VERBS+r'\b',re.I|re.S)
PRE_NAME=re.compile(r'([^.!?\n]{1,90}?)\s+'+VERBS+r'\s*[,.:]?\s*$',re.I|re.S)
PRE_VERB=re.compile(VERBS+r'\s+([^.!?\n]{1,65}?)\s*[,.:]?\s*$',re.I|re.S)
CHAPTER_RE=re.compile(r'\bCHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN)\b',re.I)

def name_in(fragment, last=False):
    hits=list(NAME_RE.finditer(fragment))
    return LOOKUP[hits[-1 if last else 0].group().casefold()] if hits else ''

def explicit_speaker(before,after):
    # A quote-ending dialogue tag may be either 'said Harry' or 'Harry said'.
    for regex,fragment,last in [(POST_VERB,after,False),(POST_NAME,after,True),
                                (PRE_NAME,before,True),(PRE_VERB,before,False)]:
        m=regex.search(fragment) if fragment is before else regex.match(fragment)
        if m:
            candidate=name_in(m.group(1),last)
            if candidate:return candidate,'explicit_heuristic'
    return '','unattributed'

def save(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pdf',type=Path)
    p.add_argument('--output',type=Path,default=Path('gephi_output_v2'))
    args=p.parse_args()
    if not args.pdf.is_file():p.error(f'PDF not found: {args.pdf}')
    args.output.mkdir(parents=True,exist_ok=True)
    doc=pymupdf.open(args.pdf)
    start=next((i for i in range(len(doc)) if CHAPTER_RE.search(doc[i].get_text()) and 'THE BOY WHO LIVED' in doc[i].get_text().upper()),None)
    if start is None:raise RuntimeError('Cannot find Book 1 opening chapter')
    end=next((i for i in range(start+1,len(doc)) if 'THE WORST BIRTHDAY' in doc[i].get_text().upper() and CHAPTER_RE.search(doc[i].get_text())),None)
    if end is None:raise RuntimeError('Cannot find Book 2 boundary; refusing to mix books')
    rows=[]; chapter=0
    for page_num in range(start,end):
        page_text=doc[page_num].get_text(sort=True)
        if CHAPTER_RE.search(page_text):chapter+=1
        # Keep each page separate; normalize wrapped lines and soft hyphens.
        page_text=page_text.replace('\u00ad','')
        page_text=re.sub(r'(?<!\n)\n(?!\n)',' ',page_text)
        for match in QUOTE_RE.finditer(page_text):
            before=page_text[max(0,match.start()-110):match.start()]
            after=page_text[match.end():match.end()+110]
            speaker,confidence=explicit_speaker(before,after)
            rows.append({'id':len(rows)+1,'chapter':chapter,'pdf_page':page_num+1,
                'speaker':speaker,'candidate_listener':'','dialogue_excerpt':re.sub(r'\s+',' ',match.group(1))[:240],
                'confidence':confidence,'reviewed':'no'})
    # Only *adjacent* dialogue records in the same chapter and near the same page.
    # Still hypothetical reply links, never certified listener identification.
    edges=Counter()
    for prev,cur in zip(rows,rows[1:]):
        if (prev['chapter']==cur['chapter'] and 0<=cur['pdf_page']-prev['pdf_page']<=1
            and prev['speaker'] and cur['speaker'] and prev['speaker']!=cur['speaker']):
            cur['candidate_listener']=prev['speaker']
            edges[(cur['speaker'],prev['speaker'])]+=1
    fields=['id','chapter','pdf_page','speaker','candidate_listener','dialogue_excerpt','confidence','reviewed']
    save(args.output/'dialogue_review.csv',rows,fields)
    edge_rows=[{'Source':s,'Target':t,'Weight':w,'Type':'Directed',
        'Evidence':'adjacent_explicit_heuristic_turns_UNVERIFIED'} for (s,t),w in sorted(edges.items())]
    nodes=sorted(set(r['speaker'] for r in rows if r['speaker']))
    save(args.output/'nodes.csv',[{'Id':n,'Label':n} for n in nodes],['Id','Label'])
    save(args.output/'edges.csv',edge_rows,['Source','Target','Weight','Type','Evidence'])
    print(f'Book 1: PDF pages {start+1}-{end}; chapters detected: {chapter}')
    print(f'Dialogue candidates: {len(rows)}; attributed: {sum(bool(r["speaker"]) for r in rows)}')
    print(f'Character nodes: {len(nodes)}; candidate directed edges: {len(edge_rows)}')
    print('WARNING: Speaker and listener labels are heuristic; manually review before research claims.')
    print('Output:',args.output.resolve())
if __name__=='__main__':main()
