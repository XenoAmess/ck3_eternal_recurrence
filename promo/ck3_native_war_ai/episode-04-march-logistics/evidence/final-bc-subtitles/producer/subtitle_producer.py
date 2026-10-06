"""Build exact-source bilingual ASS from published PCM indices and WordBoundary.

Executable entry: python subtitle_producer.py build --audio-root DIR --output NEW_DIR
Output is chapter-local and retains current C05 pending scope. No provider calls.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import re
import textwrap
import unicodedata
import wave

from PIL import ImageFont

ROOT = Path(__file__).resolve().parent
ZH_FONT = Path('C:/Windows/Fonts/msyh.ttc')
EN_FONT = Path('C:/Windows/Fonts/arial.ttf')
PUNCT_CLOSE = '，。；、：！？）】》〉」』〕”’…,.!?;:%)]}'
PUNCT_OPEN = '（【《〈「『〔“‘(['


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ref(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}


def exact(pin):
    actual = ref(pin['path'])
    if actual['bytes'] != pin['bytes'] or actual['sha256'] != pin['sha256'].lower():
        raise ValueError('Input changed: ' + pin['path'])
    return actual


def write(path, obj):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def normal(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', html.unescape(text)) if c.isalnum())


def word_positions(text, metadata, duration):
    """Map actual provider words to source characters; reject unaligned metadata."""
    projection = [(i, c) for i, c in enumerate(text) if normal(c)]
    source = ''.join(normal(c) for _, c in projection)
    result = []
    cursor = 0
    last_offset = -1
    for row in metadata:
        if row.get('type') != 'WordBoundary':
            continue
        offset, span = row['offset'], row['duration']
        if any(not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in (offset, span)):
            raise ValueError('WordBoundary offset/duration must be nonnegative integer ticks')
        if offset < last_offset:
            raise ValueError('WordBoundary offsets not ordered')
        token = normal(row['text'])
        if not token:
            continue
        # No silently skipped speech characters and no estimated fallback on error.
        if not source.startswith(token, cursor):
            raise ValueError(f'WordBoundary/source mismatch at {cursor}: {token!r}/{source[cursor:cursor+24]!r}')
        end = cursor + len(token)
        start_s, end_s = offset / 1e7, (offset + span) / 1e7
        if end_s > duration + .25:
            raise ValueError('Actual WordBoundary extends beyond PCM +250ms')
        result.append({'char_start': projection[cursor][0], 'char_end': projection[end-1][0]+1, 'start_seconds': start_s, 'end_seconds': end_s, 'native_offset_ticks': offset, 'native_duration_ticks': span, 'text': row['text']})
        cursor, last_offset = end, offset
    if cursor != len(source) or not result:
        raise ValueError(f'WordBoundary does not cover full spoken source: {cursor}/{len(source)}')
    return result


def protected_spans(text):
    tokens = ['补给容量','补给库存','补给上限','每月损耗','每月补员','补员兵士','当前人数','满员人数','兵员损失','净现金变化']
    spans = [m.span() for token in tokens for m in re.finditer(re.escape(token), text)]
    # Preserve numbers with their spoken unit, including decimal/percentage/date.
    spans += [m.span() for m in re.finditer(r'(?:百分之)?[零〇一二两三四五六七八九十百千万亿点]+(?:名士兵|士兵|金币|兵团|人|天|日|月)?|[+−-]?\d[\d,.]*(?:%|/\d+)?', text)]
    return spans


def display_lines(text, language):
    if any(c in text for c in '{}\\\r\n'):
        raise ValueError('Subtitle contains ASS control characters')
    limit = 40 if language == 'zh' else 100
    if language == 'en':
        lines = textwrap.wrap(text, width=limit, break_long_words=False, break_on_hyphens=False)
    elif len(text) <= limit:
        lines = [text]
    else:
        spans = protected_spans(text)
        cuts = [i for i in range(max(1, len(text)-limit), min(limit, len(text)-1)+1)
                if text[i] not in PUNCT_CLOSE and text[i-1] not in PUNCT_OPEN
                and not any(a < i < b for a, b in spans)]
        if not cuts:
            raise ValueError('No safe Chinese two-line break')
        cut = min(cuts, key=lambda i: (text[i-1] not in '，。；、：！？', abs(i-len(text)/2)))
        lines = [text[:cut],text[cut:]]
    if not 1 <= len(lines) <= 2 or any(len(line)>limit for line in lines):
        raise ValueError(f'More than two readable {language} lines: {text}')
    font = ImageFont.truetype(str(ZH_FONT if language=='zh' else EN_FONT), 35 if language=='zh' else 25)
    widths = [float(font.getlength(line)) for line in lines]
    if max(widths) > 1700:
        raise ValueError('Actual subtitle font width exceeds 1700px')
    return {'lines':lines,'widths_px':widths,'font':str(ZH_FONT if language=='zh' else EN_FONT),'font_size':35 if language=='zh' else 25}


HEADER = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Chinese,Microsoft YaHei,35,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00101010,0,0,0,0,100,100,0,0,1,1,0,8,110,110,0,1
Style: English,Arial,25,&H00C8C8C8,&H00FFFFFF,&H00101010,&H00101010,0,0,0,0,100,100,0,0,1,1,0,8,110,110,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''


def at_frame(frame):
    cs = frame * 100 // 30
    return f'{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}'


def ass_bytes(events, offset_frame=0):
    rows=[]
    for event in events:
        begin,end=at_frame(event['start_frame']-offset_frame),at_frame(event['end_frame']-offset_frame)
        for style,lang in [('Chinese','zh'),('English','en')]:
            lines=event['display'][lang]['lines']
            y=(910 if len(lines)==2 else 935) if lang=='zh' else (1008 if len(lines)==2 else 1030)
            text=r'\N'.join(lines)
            position=r'{\an8\pos(960,'+str(y)+')}'
            rows.append(f"Dialogue: 0,{begin},{end},{style},{event['id']},0,0,0,,{position}{text}")
    return (HEADER+'\n'.join(rows)+'\n').encode('utf-8')


def unit_time(unit, fragments):
    matches=[]
    for fragment in fragments:
        lo=max(unit['char_start'],fragment['char_start'])-fragment['char_start']
        hi=min(unit['char_end'],fragment['char_end'])-fragment['char_start']
        if hi<=lo:
            continue
        visible=[i for i in range(lo,hi) if normal(fragment['text_zh'][i])]
        if not visible:
            continue
        if fragment['word_positions'] is not None:
            words=[w for w in fragment['word_positions'] if w['char_end']>visible[0] and w['char_start']<=visible[-1]]
            if not words:
                raise ValueError('Semantic unit has no corresponding actual WordBoundary')
            begin=words[0]['start_seconds'];end=words[-1]['end_seconds']
            grade='actual-provider-WordBoundary'
        else:
            text=fragment['text_zh']
            denom=len(normal(text))
            begin=len(normal(text[:lo]))/denom*fragment['seconds']
            end=len(normal(text[:hi]))/denom*fragment['seconds']
            grade='estimated-within-actual-fragment-duration-no-WordBoundary'
        matches.append({'fragment_id':fragment['fragment_id'],'start_seconds':fragment['chapter_start_seconds']+begin,'end_seconds':min(fragment['chapter_start_seconds']+end,fragment['chapter_end_seconds']),'basis':grade})
    if not matches:
        raise ValueError('Semantic unit has no audio fragment')
    return min(m['start_seconds'] for m in matches),max(m['end_seconds'] for m in matches),matches


def build_chapter(index_path, output, alignment):
    source_index=ref(index_path);index=read(index_path)
    chapter=index['chapter_id'];output.mkdir()
    rate=index['actual_PCM']['sample_rate']
    if rate!=24000 or index['inserted_silence_frames']!=0 or index['ABC_winner'] is not None:
        raise ValueError('Unexpected actual PCM/ABC contract')
    audio=exact(index['audio'])
    with wave.open(audio['path'],'rb') as reader:
        if reader.getframerate()!=rate or reader.getnframes()!=index['actual_PCM']['sample_frames']:
            raise ValueError('Chapter WAV disagrees with actual sample index')
    events=[];timing_sources=[];paragraphs=[]
    expected=[p for p in alignment['paragraphs'] if p['chapter_id']==chapter]
    if [p['id'] for p in index['paragraphs']]!=[p['paragraph_id'] for p in expected]:
        raise ValueError('Chapter paragraph IDs/order differ')
    for paragraph,semantic in zip(index['paragraphs'],expected):
        if paragraph['subtitles_zh']!=''.join(u['zh'] for u in semantic['units']) or paragraph['subtitles_en']!=' '.join(u['en'] for u in semantic['units']):
            raise ValueError('Frozen paragraph translation differs from audio index')
        fragments=[];char_offset=0
        for original in paragraph['fragments']:
            fragment=dict(original)
            text=fragment['text_zh']
            if sha(text.encode('utf-8'))!=fragment['text_sha256']:
                raise ValueError('Fragment text SHA differs')
            fragment['char_start']=char_offset;fragment['char_end']=char_offset+len(text);char_offset+=len(text)
            fragment['chapter_start_seconds']=fragment['chapter_start_sample']/rate
            fragment['chapter_end_seconds']=fragment['chapter_end_sample']/rate
            fragment['seconds']=(fragment['chapter_end_sample']-fragment['chapter_start_sample'])/rate
            if fragment['metadata'] is not None:
                metadata=exact(fragment['metadata'])
                lines=[json.loads(line) for line in Path(metadata['path']).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
                fragment['word_positions']=word_positions(text,lines,fragment['seconds'])
                timing_sources.append({'fragment_id':fragment['fragment_id'],'metadata':metadata,'native_divisor':1e7,'mapped_words':len(fragment['word_positions'])})
            else:
                if fragment['kind']!='existing-exact-text-audio' or fragment['WordBoundary_count'] is not None:
                    raise ValueError('Unknown missing metadata cannot fall back to timing estimate')
                fragment['word_positions']=None
                timing_sources.append({'fragment_id':fragment['fragment_id'],'metadata':None,'basis':'actual PCM fragment bounds; internal duration-proportional estimate, not word-alignment proof'})
            fragments.append(fragment)
        if ''.join(f['text_zh'] for f in fragments)!=paragraph['subtitles_zh']:
            raise ValueError('Fragment roster does not reconstruct paragraph')
        first_event=len(events)
        for unit in semantic['units']:
            start,end,bases=unit_time(unit,fragments)
            # Shared old-fragment estimates can meet at a fractional frame.
            # Floor the end and round the start, retaining all original seconds.
            # This never makes adjacent nonoverlapping intervals overlap.
            start_frame=round(start*30);end_frame=max(start_frame+1,math.floor(end*30))
            if events and start_frame<events[-1]['end_frame']:
                # Adjacent punctuation cuts inside one actual provider word can overlap.
                # Do not shift either word: require a new semantic alignment instead.
                raise ValueError('Subtitle semantic units overlap at provider word boundary')
            seconds=(end_frame-start_frame)/30
            display={lang:display_lines(unit[lang],lang) for lang in ('zh','en')}
            en_wps=len(unit['en'].split())/seconds;zh_cps=len(normal(unit['zh']))/seconds
            events.append({**unit,'paragraph_id':paragraph['id'],'chapter_id':chapter,'start_seconds':start,'end_seconds':end,'start_frame':start_frame,'end_frame':end_frame,'timing_bindings':bases,'display':display,'reading_rate':{'english_words_per_second':en_wps,'Chinese_characters_per_second':zh_cps},'review_flags':(['english_rate_above4.5wps'] if en_wps>4.5 else [])+(['Chinese_rate_above7cps'] if zh_cps>7 else [])+(['duration_below1sec'] if seconds<1 else [])})
        paragraphs.append({'id':paragraph['id'],'chapter_start_sample':paragraph['chapter_start_sample'],'chapter_end_sample':paragraph['chapter_end_sample'],'event_ids':[event['id'] for event in events[first_event:]]})
    timeline={'schema':'xar.e04.actual-bilingual-subtitle-timeline.v1','chapter_id':chapter,'source_audio_index':source_index,'audio':audio,'actual_PCM':index['actual_PCM'],'coordinate_basis':'chapter-local actual concatenated PCM, provider WordBoundary plus explicit6oldfragment estimates; ASS 30fps quantized','paragraphs':paragraphs,'events':events,'timing_sources':timing_sources,'ABC_results':None,'ABC_winner':None,'chapter_story_freeze':'pending_actual_ABC_result' if chapter=='E4-05' else 'stable_a04_text','word_alignment_signoff':False,'film_signoff':False}
    write(output/'timeline.json',timeline)
    with (output/'subtitles.ass').open('xb') as stream:stream.write(ass_bytes(events))
    report={'chapter_id':chapter,'paragraphs':len(paragraphs),'subtitle_units':len(events),'actual_PCM_seconds':index['actual_PCM']['seconds'],'line_limit':'Chinese<=40chars/line;English<=100chars/line;max2lines;measured1700px','layout':'1920x1080 a09; Chinese35 at y910/935, English25 at y1008/1030','provider_WB_units':sum(all(b['basis']=='actual-provider-WordBoundary' for b in e['timing_bindings']) for e in events),'estimated_or_mixed_units':sum(any(b['basis']!='actual-provider-WordBoundary' for b in e['timing_bindings']) for e in events),'reading_rate_flags':[{ 'id':e['id'],'flags':e['review_flags'],'rates':e['reading_rate']} for e in events if e['review_flags']],'final_readability_approved':False,'source_media_hashed':[audio],'game_raw_media_read':0}
    write(output/'readability.json',report)
    return {'chapter_id':chapter,'timeline':ref(output/'timeline.json'),'subtitles':ref(output/'subtitles.ass'),'readability':ref(output/'readability.json'),'audio':audio,'actual_seconds':index['actual_PCM']['seconds'],'paragraphs':len(paragraphs),'events':len(events)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    build=sub.add_parser('build')
    build.add_argument('--audio-root',required=True,type=Path)
    build.add_argument('--output',required=True,type=Path)
    build.add_argument('--alignment',type=Path,default=ROOT/'translation-alignment-a02.json')
    build.add_argument('--chapter',action='append')
    build.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/'argv.json',{'argv':__import__('sys').argv})
    alignment=read(args.alignment)
    exact(alignment['source'])
    chapters=args.chapter or [f'E4-{n:02d}' for n in range(1,7)]
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results=list(pool.map(lambda c:build_chapter(args.audio_root/c/'audio-index.json',args.output/c,alignment),chapters))
        write(args.output/'ROOT-DELIVERY.json',{'schema':'xar.e04.actual-subtitles-delivery.v1','created_utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_CHAPTER_LOCAL_ASS_PENDING_VISUAL_REVIEW','alignment':ref(args.alignment),'chapters':results,'paragraphs':sum(c['paragraphs'] for c in results),'events':sum(c['events'] for c in results),'actual_audio_seconds':sum(c['actual_seconds'] for c in results),'ABC_results':None,'ABC_winner':None,'final_film':False,'provider_calls':0,'game':0,'SDK':0,'UI':0,'Git':0})
        print(json.dumps({'chapters':len(results),'paragraphs':sum(c['paragraphs'] for c in results),'events':sum(c['events'] for c in results),'seconds':sum(c['actual_seconds'] for c in results)},ensure_ascii=False))
    except Exception as error:
        write(args.output/'FAILURE.json',{'error':type(error).__name__+': '+str(error),'partial_assets_retained':True})
        raise


if __name__=='__main__':main()
