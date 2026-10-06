"""Keep English logistics terms and numeric units together across subtitle lines.

Display breaks only: exact source wording, raw native times and audio remain unchanged.
"""
import argparse
import copy
from datetime import datetime,timezone
from pathlib import Path
import re
import subtitle_producer as p

TERMS=['supply stock','supply capacity','supply limit','current soldiers','maximum soldiers',
       'net gold','Monthly Reinforcement','Reinforcing Men-at-Arms','full strength',
       'soldier count','men-at-arms']

def english_lines(text):
    if len(text)<=100:return p.display_lines(text,'en')
    spans=[m.span() for term in TERMS for m in re.finditer(re.escape(term),text,re.IGNORECASE)]
    spans+=[m.span() for m in re.finditer(r'(?:capacity of|day|about)\s+[+−-]?\d[\d,.]*|[+−-]?\d[\d,.]*\s+(?:soldiers?|supply|days?|gold|percent|seconds?)',text,re.IGNORECASE)]
    options=[]
    for m in re.finditer(' ',text):
        cut=m.start()
        if cut>100 or len(text)-cut-1>100 or any(a<cut<b for a,b in spans):continue
        before=text[:cut].rstrip('”"\'’')
        punctuation=0 if before[-1:] in '.!?' else 1 if before[-1:] in ',;:' else 2
        options.append((punctuation,abs(cut-(len(text)-1)/2),cut))
    if not options:raise ValueError('No two-line English break preserving units')
    cut=min(options)[-1];lines=[text[:cut],text[cut+1:]]
    result=p.display_lines(lines[0],'en')
    result['lines']=lines
    result['widths_px']=[p.display_lines(line,'en')['widths_px'][0] for line in lines]
    assert all(len(line)<=100 for line in lines) and max(result['widths_px'])<=1700
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    source=p.read(args.delivery);chapters=[];edits=[]
    for chapter in source['chapters']:
        p.exact(chapter['timeline']);p.exact(chapter['readability'])
        timeline=copy.deepcopy(p.read(chapter['timeline']['path']))
        timeline['original_timeline']=chapter['timeline']
        for event in timeline['events']:
            original=copy.deepcopy(event['display']['en'])
            new=english_lines(event.get('english_display_text',event['en']))
            assert ' '.join(new['lines'])==event.get('english_display_text',event['en'])
            if original['lines']!=new['lines']:
                event['english_display_line_change']={'before':original['lines'],'after':new['lines'],
                      'basis':'Prefer sentence/clause breaks; protect English logistics terms and numeric units.'}
                edits.append({'id':event['id'],**event['english_display_line_change']})
            event['display']['en']=new
        folder=args.output/chapter['chapter_id'];folder.mkdir()
        p.write(folder/'timeline.json',timeline)
        with (folder/'subtitles.ass').open('xb') as stream:stream.write(p.ass_bytes(timeline['events']))
        report=copy.deepcopy(p.read(chapter['readability']['path']))
        report['original_readability']=chapter['readability']
        report['English_terms_and_numeric_units_protected_across_lines']=True
        p.write(folder/'readability.json',report)
        chapters.append({**chapter,'timeline':p.ref(folder/'timeline.json'),'subtitles':p.ref(folder/'subtitles.ass'),
                         'readability':p.ref(folder/'readability.json')})
    p.write(args.output/'ENGLISH-TERM-LINE-CHANGES.json',{'source_text_unchanged':True,'timing_unchanged':True,
        'protected_terms':TERMS,'changes':edits,'count':len(edits),'audio_reads':0})
    p.write(args.output/'ROOT-DELIVERY.json',{**source,'created_utc':datetime.now(timezone.utc).isoformat(),
        'original_delivery':p.ref(args.delivery),'chapters':chapters,
        'English_line_reflow':p.ref(args.output/'ENGLISH-TERM-LINE-CHANGES.json'),'source_text_and_timing_unchanged':True})
    print(f'PASS: {len(edits)} English display-only two-line reflows,zero text/timing/audio change')

if __name__=='__main__':main()
