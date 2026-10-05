"""Episode04 native picture producer: authored overlays on moving source pixels.

Project stage, not a recorder or a remux composer. Uses formal xar-promo public
process/audio/subtitle/probe APIs. Every render directory is append-only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import re
import shutil
import sys
import wave
from datetime import datetime, timezone
from fractions import Fraction
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from xar_promo import probe_and_write_bound_media
from xar_promo.audio import AudioMixSpec, AudioStem, plan_audio_mix
from xar_promo.process import CommandSpec, run_command
from xar_promo.render import ass_burn_in_filter

# Exact series palette, copied from war_ai_promo/series_palette.py. These colors
# apply to authored packaging only; source game pixels are never recolored.
BG, PANEL, INK, GOLD = '#211813', '#35291F', '#F0E5CF', '#CBA56A'
MUSIC_SHA = 'fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f'
FPS = 30


class PictureInputError(ValueError):
    pass


def require(value, reason):
    if not value:
        raise PictureInputError(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def pin(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def exact(binding):
    require(isinstance(binding, dict) and set(('path', 'bytes', 'sha256')) <= set(binding), 'missing exact file binding')
    actual = pin(binding['path'])
    require(actual['bytes'] == binding['bytes'] and actual['sha256'] == binding['sha256'].lower(), 'changed bound file: ' + binding['path'])
    return Path(binding['path'])


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')


def validate(spec, *, preview=False):
    """Zero-process validation. Unknown sentences and repeated source time fail."""
    require(spec.get('schema') == 'xar.e04.picture-input.v1', 'unknown picture input schema')
    release = read(exact(spec['release_probe']))
    require(release['status'] == 'LATEST_FORMAL_RELEASE_MATCHES_INSTALLED_AND_PINNED', 'latest release was not verified')
    require(importlib.metadata.version('xar-promo-toolchain') == release['explicit_python']['distribution_version'], 'installed wheel changed')
    config = read(exact(spec['project_config']))
    claims = read(exact(spec['claim_ledger']))
    cue_map = {c['id']: c for ch in config['chapters'] for c in ch['cues']}
    claim_map = {c['id']: c for c in claims['claims']}
    require(spec['music']['title'] == 'Quiet Courtly Tension' and spec['music']['gain_db'] == -17 and spec['music']['ducking'] is False and spec['music']['normalize'] is False, 'wrong fixed series music policy')
    require(spec['music']['source']['sha256'].lower() == MUSIC_SHA, 'wrong series music source')
    exact(spec['music']['source'])
    exact(spec['fonts']['zh']); exact(spec['fonts']['en'])
    require(spec.get('output_geometry') == [1920, 1080, 30], 'native picture must be 1920x1080/30fps')
    rows = spec.get('cues')
    require(isinstance(rows, list) and rows, 'no bound picture cues')
    require(len({r['id'] for r in rows}) == len(rows), 'duplicate picture cue')
    used = {}
    origin_samples=spec.get('audio_clock_start_sample',0)
    require(origin_samples==23238144,'C05 must keep its immutable global PCM origin')
    total_samples = origin_samples
    previous_end_frame = math.ceil(Fraction(origin_samples*FPS,24000))
    first_frame=previous_end_frame
    for row in rows:
        key = row['id']
        require(key in cue_map and key in claim_map, 'unbound sentence: ' + key)
        claim = claim_map[key]
        pending_plan = claim['status'] == 'pending-plan'
        require(claim['status'] in ('supported-with-stated-bounds', 'supported') or (preview and key in ('C05-03','C05-15','C05-16') and claim['status']=='supported-actual-A-only-with-stated-bounds' and row.get('A_only_scope')=='actual-A-observation') or (preview and pending_plan and row.get('editorial_role') == 'explicit-plan-or-unknown-boundary' ), 'unknown/pending claim: ' + key)
        if pending_plan:
            require(row.get('record_note') and row.get('actual_outcome_credit') is False, 'planning preview must explicitly label its unknown boundary')
        require(row.get('actual_outcome_credit') is False, 'roughcut cannot manufacture actual outcome credit')
        require(claim.get('source_keys') and all(k in claims['source_catalog'] for k in claim['source_keys']), 'claim sources missing: ' + key)
        cue = cue_map[key]
        require(row.get('text_zh') == cue['narration']['zh'] == claim['claim_summary'], 'sentence does not match frozen claim: ' + key)
        require(row.get('text_en') == cue['subtitles']['en'], 'English does not match frozen sentence: ' + key)
        if key.startswith('C05-'):
            context=read(exact(spec['A_only_audio_delivery']))
            endpoint=read(exact(spec['A_endpoint_acceptance']))
            require(context.get('B') is None and context.get('C') is None and context.get('ABC_winner') is None, 'A-only chapter must preserve B/C/winner unknown')
            require(context['A']['first_observed_elapsed_days']==51 and context['A']['observed_arrival_interval_days']==[49,51] and context['A']['exact_arrival_tick'] is None, 'A-only source boundary differs')
            require(row.get('A_only_scope') in ('actual-A-observation','predeclared-method-or-known-qualification'), 'unbound C05 partial-result role')
            if row.get('A_only_scope')=='actual-A-observation':
                require(key in ('C05-03','C05-15','C05-16') and 'r177-A2-values' in claim['source_keys'], 'unbound A actual result sentence')
            require(row.get('actual_B_C_result_binding') is None and row.get('winner') is None, 'unverified B/C/winner prohibited')
        audio_index = read(exact(row['audio_index']))
        paragraph = next((p for p in audio_index['paragraphs'] if p['id'] == key), None)
        require(paragraph is not None and paragraph['subtitles_zh'] == row['text_zh'] and paragraph['subtitles_en'] == row['text_en'], 'actual audio text differs: ' + key)
        exact(audio_index['audio'])
        require(row['audio_start_sample'] == paragraph['chapter_start_sample'] and row['audio_end_sample'] == paragraph['chapter_end_sample'], 'actual PCM interval differs')
        rate = audio_index['actual_PCM']['sample_rate']
        require((rate,audio_index['actual_PCM']['channels'],audio_index['actual_PCM']['sample_width_bytes'])==(24000,1,2), 'actual source PCM format differs')
        seconds = (row['audio_end_sample'] - row['audio_start_sample']) / rate
        require(seconds > 0 and math.isfinite(seconds), 'invalid actual audio duration')
        total_samples += row['audio_end_sample'] - row['audio_start_sample']
        end_frame = math.ceil(Fraction(total_samples * FPS,rate))
        frames = end_frame - previous_end_frame
        previous_end_frame = end_frame
        require(row['duration_frames'] == frames, 'picture must use the cumulative actual PCM clock, without a per-cue silent grid tail')
        exact(row['subtitles_ass']); timing = read(exact(row['subtitle_timing']))
        require(timing.get('schema') == 'xar.e04.actual-paragraph-subtitles.v1' and timing.get('paragraph_id') == key, 'unknown subtitle timeline schema')
        require(''.join(e['zh'] for e in timing['events']) == row['text_zh'] and ' '.join(e['en'] for e in timing['events']) == row['text_en'], 'subtitle sentence binding missing')
        require(timing['audio_slice']['start_sample'] == row['audio_start_sample'] and timing['audio_slice']['end_sample'] == row['audio_end_sample'] and abs(timing['audio_slice']['exact_seconds'] - seconds) < 1e-8, 'subtitle/audio actual clocks differ')
        require(timing['source_chapter_audio'] == audio_index['audio'], 'subtitle audio source differs')
        require(all(e.get('timing_bindings') for e in timing['events']), 'subtitle timing basis is unknown')
        require(row.get('title') and len(row['title']) <= 22, 'missing or excessive small title')
        require(row.get('source_label') and len(row['source_label']) <= 50, 'missing source label')
        require(row.get('visuals'), 'picture cue has no dynamic sources')
        note=row.get('record_note',[])
        require(isinstance(note,list) and len(note)<=6 and all(isinstance(v,str) and len(v)<=33 for v in note), 'author note is too large')
        if row.get('editorial_role') in ('record-explanation-on-independent-background','explicit-plan-or-unknown-boundary'):
            require(note and '记录说明' in row['source_label'], 'independent background must be explicitly labelled')
        total_frames = 0
        for visual in row['visuals']:
            require(visual.get('kind') == 'sealed-native-video' and visual.get('playback_rate') == 1, 'only real 1x native video supported; stills and padding refused')
            seal_envelope = read(exact(visual['seal_receipt']))
            seal = seal_envelope.get('body',seal_envelope)
            require(seal.get('state') == 'NORMAL_TREE_EMPTY' and seal['job']['returncode'] == 0 and seal['job']['job_active_processes'] == 0, 'raw source is not closed')
            require(visual['source'] == seal['raw'], 'source is not the original sealed raw identity')
            raw_path = Path(visual['source']['path'])
            require(raw_path.stat().st_size == visual['source']['bytes'], 'sealed source size changed')
            # No redundant whole-raw hash/probe: reuse exact closed audit bindings.
            audit = read(exact(visual['existing_media_audit']))
            require(audit.get('source_identity') == visual['source'], 'media audit source differs')
            source_probe = read(exact(audit['probe_receipts']['streams-format']['stdout_identity']))
            source_video = next(s for s in source_probe['streams'] if s['codec_type'] == 'video')
            require([source_video['width'], source_video['height']] == visual['source_geometry'] and source_video['time_base'] == visual['source_time_base'] and source_video['r_frame_rate'] == '30/1', 'declared source metadata differs from the actual closed probe')
            require(visual.get('source_geometry') == [1920, 1080] and visual.get('source_time_base') == '1/1000', 'native source metadata missing')
            require(audit.get('state') in ('PASS', 'GREEN', 'AUTOMATED_MEDIA_PASS') or audit.get('overall') in ('PASS', 'GREEN') or audit.get('status') in ('PASS', 'GREEN'), 'closed media audit not PASS')
            review = read(exact(visual['window_review']))
            require(review.get('source_binding') == visual['source'], 'window review source differs')
            begin, end = visual['source_start_seconds'], visual['source_end_seconds_exclusive']
            require(0 <= begin < end and review['start_seconds'] <= begin and end <= review['end_seconds_exclusive'], 'source exceeds reviewed window')
            require(end <= float(source_probe['format']['duration']), 'source selection exceeds closed recording')
            if preview:
                require(review.get('sampled_content_usable') is True, 'preview window samples have not been reviewed')
            else:
                require(review.get('continuous_clean_review') is True, 'production needs continuous clean window review')
            n = visual['duration_frames']
            require(isinstance(n, int) and n > 0 and end - begin >= n / FPS - 1e-8, 'native span cannot cover picture without freezing')
            file_key = str(raw_path.resolve()).casefold()
            require(all(end <= a or b <= begin for a, b in used.get(file_key, [])), 'repeated/overlapping source time would pad the film')
            used.setdefault(file_key, []).append((begin, end)); total_frames += n
            if visual.get('zoom'):
                z = visual['zoom']; x,y,w,h = z['crop_xywh']; ox,oy,ow,oh = z['output_xywh']
                require(all(isinstance(v, int) for v in [x,y,w,h,ox,oy,ow,oh]) and min(x,y,ox,oy) >= 0 and min(w,h,ow,oh) > 0 and x+w <= 1920 and y+h <= 1080 and ox+ow <= 1920 and oy+oh <= 900, 'invalid source-pixel zoom')
                require(0 <= z['start_seconds'] < z['end_seconds'] <= n / FPS, 'zoom exceeds actual dynamic source')
        require(total_frames == frames, 'visual playlist must cover the actual cue exactly')
    if len(rows)>1:
        require(spec.get('subtitle_master'), 'multiple cues require one actual global subtitle clock')
        exact(spec['subtitle_master']['ass'])
        master=read(exact(spec['subtitle_master']['timeline']))
        require(master.get('schema')=='xar.e04.actual-stable-full-subtitle-timeline.v1' and master['sample_rate']==24000 and master['sample_frames']==total_samples-origin_samples and master['picture_frames_30fps']==previous_end_frame-first_frame, 'master subtitle clock differs from exact selected PCM')
        require([v['id'] for v in master['paragraphs']]==[v['id'] for v in rows], 'master subtitle sentence order differs')
        cursor=0
        for row,paragraph in zip(rows,master['paragraphs']):
            n=row['audio_end_sample']-row['audio_start_sample']
            require(paragraph['global_start_sample']==cursor and paragraph['global_end_sample']==cursor+n, 'master subtitle paragraph sample boundary differs')
            index=read(row['audio_index']['path']);chapter=next(v for v in master['chapters'] if v['chapter_id']==index['chapter_id'])
            require(chapter['source_audio']==index['audio'], 'master subtitle audio source differs')
            cursor+=n
    return {'state': 'PREVIEW_INPUTS_VERIFIED' if preview else 'PRODUCTION_INPUTS_VERIFIED', 'cues': [r['id'] for r in rows], 'duration_frames': previous_end_frame-first_frame, 'actual_PCM_samples':total_samples-origin_samples,'actual_PCM_seconds':(total_samples-origin_samples)/24000,'inserted_silence_samples':0,'audio_source_clock': 'actual-concatenated-PCM', 'unknown_C05_results_accepted': False, 'whole_raw_rehashes': 0}


def plate(path, row, fonts):
    """Series brown/gold small header + a09 four-line subtitle band."""
    image = Image.new('RGBA', (1920,1080), (0,0,0,0))
    draw=ImageDraw.Draw(image)
    # Preserve the main game at native full frame. Packaging is an overlay,
    # not synthetic game UI. Insets split the very same moving source frame.
    draw.rounded_rectangle((28,22,610,90),radius=12,fill=PANEL+'ED')
    draw.text((48,32),row['title'],font=ImageFont.truetype(fonts['zh']['path'],35),fill=INK)
    draw.rectangle((0,900,1920,1080),fill=BG+'FA')
    draw.line((0,900,1920,900),fill=GOLD,width=2)
    draw.rounded_rectangle((1240,24,1890,72),radius=8,fill=PANEL+'ED')
    draw.text((1260,32),row['source_label'],font=ImageFont.truetype(fonts['zh']['path'],23),fill=GOLD)
    if row.get('record_note'):
        lines=row['record_note']; h=64+len(lines)*43
        draw.rounded_rectangle((1060,112,1890,112+h),radius=12,fill=PANEL+'F2',outline=GOLD,width=2)
        draw.text((1084,126),'研究记录 · 独立样本',font=ImageFont.truetype(fonts['zh']['path'],26),fill=GOLD)
        for i,line in enumerate(lines):
            draw.text((1084,172+i*43),line,font=ImageFont.truetype(fonts['zh']['path'],29),fill=INK)
    with path.open('xb') as stream: image.save(stream,format='PNG')


def render(spec, workdir, *, preview=False):
    validation = validate(spec,preview=preview)
    root=Path(workdir); root.mkdir(parents=True,exist_ok=False)
    write_new(root/'input-snapshot.json',spec)
    write_new(root/'preflight.json',validation)
    ffmpeg,ffprobe=exact(spec['tools']['ffmpeg']),exact(spec['tools']['ffprobe'])
    outputs=[]; timeline=[]; start_frame=0
    narration=root/'narration.wav'
    # Concatenate exact already produced samples. No per-cue audio padding,
    # normalization, resampling or AAC segment boundaries can change this clock.
    with wave.open(str(narration),'wb') as destination:
        destination.setnchannels(1);destination.setsampwidth(2);destination.setframerate(24000)
        for row in spec['cues']:
            index=read(row['audio_index']['path'])
            with wave.open(index['audio']['path'],'rb') as source:
                require((source.getframerate(),source.getnchannels(),source.getsampwidth(),source.getnframes())==(24000,1,2,index['actual_PCM']['sample_frames']), 'actual WAV header differs from its frozen PCM index')
                source.setpos(row['audio_start_sample'])
                count=row['audio_end_sample']-row['audio_start_sample']
                samples=source.readframes(count)
                require(len(samples)==count*2,'actual PCM interval is incomplete')
                destination.writeframesraw(samples)
    with wave.open(str(narration),'rb') as check:
        require(check.getnframes()==validation['actual_PCM_samples'],'exact narration splice sample count differs')
    def render_one(pair):
        row,start_frame=pair
        cue_root=root/row['id'];cue_root.mkdir()
        plate_path=cue_root/'packaging.png';plate(plate_path,row,spec['fonts'])
        subtitles=cue_root/'subtitles.ass';shutil.copyfile(exact(row['subtitles_ass']),subtitles)
        index=read(row['audio_index']['path']); rate=index['actual_PCM']['sample_rate']
        duration=row['duration_frames']/FPS
        argv=[ffmpeg,'-hide_banner','-nostdin','-n','-copyts'];filters=[];count=0
        for i,v in enumerate(row['visuals']):
            begin,end=v['source_start_seconds'],v['source_end_seconds_exclusive']
            argv += ['-threads','1','-ss',f'{begin:.6f}','-to',f'{end:.6f}','-i',v['source']['path']]
            tick=Fraction(v['source_time_base']);a=math.ceil(Fraction(str(begin))/tick);b=math.ceil(Fraction(str(end))/tick)
            base=f'[{i}:v]trim=start_pts={a}:end_pts={b},showinfo@source_{i},setpts=PTS-STARTPTS,setsar=1,fps=30,trim=end_frame={v["duration_frames"]}'
            if v.get('zoom'):
                z=v['zoom'];x,y,w,h=z['crop_xywh'];ox,oy,ow,oh=z['output_xywh']
                filters += [base+f',split=2[main{i}][zoomraw{i}]',f'[zoomraw{i}]crop={w}:{h}:{x}:{y}:exact=1,scale={ow}:{oh}:flags=lanczos,format=rgba,fade=t=in:st={z["start_seconds"]:.6f}:d=0.25:alpha=1,fade=t=out:st={max(z["start_seconds"],z["end_seconds"]-.25):.6f}:d=0.25:alpha=1[z{i}]',f'[main{i}][z{i}]overlay=x={ox}:y={oy}:shortest=1:enable=\'between(t,{z["start_seconds"]},{z["end_seconds"]})\',drawbox=x={ox}:y={oy}:w={ow}:h={oh}:color=0x{GOLD[1:]}:t=2:enable=\'between(t,{z["start_seconds"]},{z["end_seconds"]})\',format=yuv420p[v{i}]']
            else: filters += [base+f',format=yuv420p[v{i}]']
            count+=1
        argv += ['-threads','1','-loop','1','-framerate','30','-t',f'{duration:.9f}','-i',plate_path]
        filters += [''.join(f'[v{i}]' for i in range(count))+f'concat=n={count}:v=1:a=0[native]',f'[native][{count}:v]overlay=shortest=1[picture]']
        graph=cue_root/'filter.txt';write_new(graph,';\n'.join(filters))
        output=cue_root/'picture-dry.mov'
        argv += ['-filter_complex_threads','1','-/filter_complex',graph,'-map','[picture]','-an','-frames:v',str(row['duration_frames']),'-t',f'{duration:.9f}','-c:v','libx264','-preset','ultrafast','-crf','22','-threads','2','-r','30','-fps_mode','cfr','-pix_fmt','yuv420p','-movflags','+faststart',output]
        raw_stats=[(Path(v['source']['path']).stat().st_size,Path(v['source']['path']).stat().st_mtime_ns) for v in row['visuals']]
        result=run_command(CommandSpec.create(argv,label='Episode04 actual native picture '+row['id'],cwd=root,partial_artifacts=(output,)),audit_directory=cue_root/'render-command-audit')
        require(raw_stats==[(Path(v['source']['path']).stat().st_size,Path(v['source']['path']).stat().st_mtime_ns) for v in row['visuals']], 'raw changed during render')
        source_reads=[]
        for i,v in enumerate(row['visuals']):
            pts=[int(re.search(r'\bpts:\s*(-?\d+)',line)[1]) for line in result.stderr.splitlines() if 'showinfo@source_'+str(i)+' ' in line and re.search(r'\bpts:\s*(-?\d+)',line)]
            tick=Fraction(v['source_time_base']);a=math.ceil(Fraction(str(v['source_start_seconds']))/tick);b=math.ceil(Fraction(str(v['source_end_seconds_exclusive']))/tick)
            require(len(pts)>=v['duration_frames'] and all(a<=x<b for x in pts) and all(x<y for x,y in zip(pts,pts[1:])), 'actual decoded source PTS differs from the frozen dynamic window')
            source_reads.append({'source_index':i,'decoded_frames':len(pts),'first_actual_pts':pts[0],'last_actual_pts':pts[-1],'time_base':v['source_time_base'],'planned_first_tick_inclusive':a,'planned_end_tick_exclusive':b})
        probe_and_write_bound_media(str(ffprobe),output,output_path=cue_root/'picture.bound-probe.json',audit_directory=cue_root/'probe-command-audit')
        bound=read(cue_root/'picture.bound-probe.json')
        verify_output_probe(bound,row['duration_frames'],pcm=None)
        # Public envelope retains real probe and exact artifact bytes; do not
        # hand-wrap it or create a human review/signoff record.
        output_pin=pin(output)
        entry={'cue_id':row['id'],'start_frame':start_frame,'duration_frames':row['duration_frames'],'duration_seconds':duration,'actual_audio_seconds':(row['audio_end_sample']-row['audio_start_sample'])/rate,'picture_boundary_grid_difference_seconds':duration-(row['audio_end_sample']-row['audio_start_sample'])/rate,'inserted_audio_silence_samples':0,'source_claim':claim_pin(spec,row['id']),'dynamic_source_windows':row['visuals'],'actual_source_decodes':source_reads,'subtitle_timing':row['subtitle_timing'],'output':output_pin,'bound_probe':pin(cue_root/'picture.bound-probe.json')}
        print(json.dumps({'state':'ACTUAL_CUE_PICTURE_RENDERED','cue':row['id'],'frames':row['duration_frames'],'path':str(output)},ensure_ascii=False),flush=True)
        return output_pin,entry
    pairs=[];cursor=0
    for row in spec['cues']:
        pairs.append((row,cursor));cursor+=row['duration_frames']
    with ThreadPoolExecutor(max_workers=2) as workers:
        for output_pin,entry in workers.map(render_one,pairs):
            outputs.append(output_pin);timeline.append(entry)
    start_frame=cursor
    concat_file=root/'picture-concat.txt'
    require(all("'" not in o['path'] and '\n' not in o['path'] for o in outputs),'unsupported concat filename')
    write_new(concat_file,'ffconcat version 1.0\n'+''.join("file '"+Path(o['path']).as_posix()+"'\n" for o in outputs))
    dry=root/'picture-dry.mov'
    run_command(CommandSpec.create([ffmpeg,'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',concat_file,'-map','0:v:0','-an','-c','copy','-movflags','+faststart',dry],label='Episode04 ordered dry picture concat',cwd=root,partial_artifacts=(dry,)),audit_directory=root/'concat-command-audit')
    probe_and_write_bound_media(str(ffprobe),dry,output_path=root/'picture-dry.bound-probe.json',audit_directory=root/'dry-final-probe-command-audit')
    verify_output_probe(read(root/'picture-dry.bound-probe.json'),start_frame,pcm=None)
    report={'schema':'xar.e04.A-only-increment-dry-picture.v1','state':'ACTUAL_C05_DRY_INCREMENT_RENDERED','inputs':pin(root/'input-snapshot.json'),'producer':pin(__file__),'cue_outputs':outputs,'dry_picture':pin(dry),'exact_chapter_narration_PCM':pin(narration),'actual_narration_samples':validation['actual_PCM_samples'],'timeline':timeline,'total_frames':start_frame,'audio_clock_start_sample':23238144,'ABC_B_C_winner':None,'human_signoff':False,'native_UI_or_Game_or_SDK_actions':0}
    write_new(root/'picture-receipt.json',report)
    return report



def verify_output_probe(bound,frames,*,pcm):
    streams=bound['ffprobe']['streams']
    video=next(s for s in streams if s['codec_type']=='video')
    require((video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))==(1920,1080,'30/1',frames),'actual picture geometry/frame clock differs')
    if pcm is not None:
        audio=next(s for s in streams if s['codec_type']=='audio')
        require(audio['sample_rate']=='48000' and audio['channels']==2 and audio['codec_name']==('pcm_s16le' if pcm else 'aac'),'actual picture audio differs')
    else:
        require(not any(s['codec_type']=='audio' for s in streams),'dry picture must not carry padded per-cue audio')
    require(abs(float(video['duration'])-frames/FPS)<0.000002,'actual picture duration differs')


def claim_pin(spec,key):
    claim=next(c for c in read(spec['claim_ledger']['path'])['claims'] if c['id']==key)
    return {'ledger':spec['claim_ledger'],'id':key,'source_keys':claim['source_keys'],'status':claim['status']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['check','render'])
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--workdir',type=Path)
    p.add_argument('--preview-only',action='store_true',help='Allow sample-reviewed windows for an explicitly nonfinal render. Production requires continuous-clean review.')
    args=p.parse_args()
    try:
        spec=read(args.input)
        if args.operation=='check': result=validate(spec,preview=args.preview_only)
        else:
            require(args.workdir is not None,'render needs a fresh --workdir')
            result=render(spec,args.workdir,preview=args.preview_only)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (PictureInputError,KeyError,StopIteration) as error:
        print(json.dumps({'state':'STOP','reason':str(error),'human_signoff':False},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
