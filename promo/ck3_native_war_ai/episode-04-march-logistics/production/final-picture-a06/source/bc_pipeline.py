"""Episode04 final B/C increment. Default PLAN reads small metadata only.

The render operation is a future explicit action. It does not generate TTS,
discover game state, approve source pixels, upload, or alter an old attempt.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import re
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

FPS = 30
RATE = 24000
SCHEMA = 'xar.e04.final-BC-increment-input.v1'
SMALL_EXTENSIONS = {'.json', '.jsonl', '.py', '.md', '.ass'}
B_DIFF = {'C05-04', 'C05-08', 'C05-10', 'C05-14', 'C05-16'}
ALLOWED_DIFF = {f'C05-{n:02}' for n in range(1,17)} | {'C06-10'}
MEDIA = {'.mp4', '.mov', '.mkv', '.wav', '.mp3', '.png', '.jpg', '.jpeg'}

class Stop(ValueError):
    pass

def require(value, reason):
    if not value:
        raise Stop(reason)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def binding(path):
    p = Path(path)
    require(p.suffix.lower() in SMALL_EXTENSIONS and p.stat().st_size <= 8*1024*1024,
            'small metadata/source only: '+str(p))
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def small_exact(pin):
    require(isinstance(pin, dict) and {'path', 'bytes', 'sha256'} <= pin.keys(),
            'missing small input binding')
    actual = binding(pin['path'])
    require(actual['bytes'] == pin['bytes'] and actual['sha256'] == pin['sha256'].lower(),
            'changed small input: '+pin['path'])
    return Path(pin['path'])

def bound_json(pin):
    return read(small_exact(pin))

def frame(sample):
    return math.ceil(Fraction(sample*FPS, RATE))

def new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        if isinstance(value, str):
            f.write(value)
        else:
            json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def paragraph_map(audio):
    rows, chapters = {}, {}
    cursor = 0
    for ch in audio['chapter_timeline']:
        index = bound_json(ch['index'])
        require(index['chapter_id'] == ch['chapter_id'], 'chapter identity differs')
        require(ch['start_sample'] == cursor and ch['end_sample']-ch['start_sample'] ==
                index['actual_PCM']['sample_frames'], 'actual chapter global PCM differs')
        chapter_cursor = 0
        chapters[ch['chapter_id']] = (ch, index)
        for row in index['paragraphs']:
            require(row['id'] not in rows, 'duplicate audio paragraph')
            require(row['chapter_start_sample'] == chapter_cursor and
                    row['chapter_end_sample'] > chapter_cursor, 'actual paragraph chapter PCM differs')
            chapter_cursor = row['chapter_end_sample']
            rows[row['id']] = (row, ch, index)
        require(chapter_cursor == index['actual_PCM']['sample_frames'], 'chapter paragraph sum differs')
        cursor = ch['end_sample']
    require(cursor == audio['actual_PCM']['sample_frames'], 'full actual chapter sample sum differs')
    return rows, chapters

def metadata_plan(spec):
    require(spec.get('schema') == SCHEMA, 'wrong increment input schema')
    old = bound_json(spec['prior']['A_full_picture_receipt'])
    old_audio = bound_json(spec['prior']['A_audio_delivery'])
    require(len(old['timeline']) == 69 and old['actual_PCM_samples'] == 37900224
            and old['duration_frames'] == 47376, 'historical A source differs')
    required = ('Root_final_story_freeze', 'project_config', 'claim_ledger',
                'audio_delivery', 'subtitle_delivery', 'C05_relative_delivery',
                'C_terminal_receipt', 'C_closed_media_receipt', 'release_probe',
                'picture_rows')
    pending = [key for key in required if spec['final'].get(key) is None]
    return {
        'schema': 'xar.e04.final-BC-file-plan.v1',
        'state': 'FILE_METADATA_PLAN_PENDING' if pending else 'FILE_METADATA_PLAN_BOUND',
        'pending': pending,
        'historical_A_only_clock': {'samples': 37900224, 'seconds': 1579.176,
                                  'frames': 47376},
        'historical_exact_asset_bindings': len(old['timeline']),
        'stable_chapters_reuse': ['E4-01','E4-02','E4-03','E4-04'],
        'C06_first_nine_cues_reuse': True,
        'C06_10_reuse_or_increment': 'conditional on final Chinese/English/overlay diff',
        'B_candidate_audio_changed_ids': sorted(B_DIFF),
        'Root_required_picture_refresh_ids': ['C05-01'],
        'final_changed_ids': None if pending else 'computed by check from actual final audio text',
        'final_samples': None, 'final_seconds': None, 'final_frames': None,
        'new_media_reads': 0, 'new_media_hashes_or_probes': 0,
        'processes_started': 0, 'output_created': False,
        'B_London_comparable': False, 'winner': None,
        'historical_A_exact_audio_PTS_continuity': 'RED',
        'new_movie_exact_audio_PTS_continuity': None,
        'human_full_1x_review': False, 'human_signoff': False,
        'full_film_ready': False,
    }

def audio_fingerprint(row):
    return [{'text_zh':f['text_zh'], 'audio':f['audio'],
             'text_sha256':f['text_sha256'], 'decoded_audio':f['decoded_audio'],
             'decoded_PCM':f['decoded_PCM'], 'metadata':f.get('metadata')}
            for f in row['fragments']]

def validate_ready(spec):
    plan = metadata_plan(spec)
    require(not plan['pending'], 'final inputs pending: '+', '.join(plan['pending']))
    final = spec['final']
    freeze = bound_json(final['Root_final_story_freeze'])
    require(freeze.get('schema') == 'xar.e04.final-story-review-freeze.v1'
            and freeze.get('approved_for_review_render') is True,
            'Root final story review is absent; this is not film signoff')
    for key in ('project_config','claim_ledger','audio_delivery','subtitle_delivery',
                'C05_relative_delivery','C_terminal_receipt','C_closed_media_receipt'):
        require(freeze.get(key) == final[key], 'Root story freeze binding differs: '+key)
        small_exact(final[key])
    require(freeze.get('B_status') == 'STOPPED_GATE_INCOMPLETE'
            and freeze.get('B_London_comparable') is False and freeze.get('winner') is None,
            'B failed its gate; no comparable London or winner allowed')
    require(freeze.get('C_sampling_deviation_review') is not None,
            'actual C sampling deviation must have a bound stated limit')
    small_exact(freeze['C_sampling_deviation_review'])
    release = bound_json(final['release_probe'])
    require(release.get('status') == 'LATEST_FORMAL_RELEASE_MATCHES_INSTALLED_AND_PINNED',
            'new render must query and verify current formal release')
    old_audio = bound_json(spec['prior']['A_audio_delivery'])
    old_rows, old_chapters = paragraph_map(old_audio)
    audio = bound_json(final['audio_delivery'])
    require((audio['actual_PCM']['sample_rate'], audio['actual_PCM']['channels'],
             audio['actual_PCM']['sample_width_bytes']) == (RATE,1,2), 'actual PCM format differs')
    rows, chapters = paragraph_map(audio)
    require(set(rows) == set(old_rows) and len(rows) == 69, 'final 69 paragraph identities differ')
    changed = {key for key in rows if rows[key][0]['subtitles_zh'] !=
               old_rows[key][0]['subtitles_zh']}
    subtitle_changed = {key for key in rows if
               (rows[key][0]['subtitles_zh'], rows[key][0]['subtitles_en']) !=
               (old_rows[key][0]['subtitles_zh'], old_rows[key][0]['subtitles_en'])}
    require(B_DIFF <= changed and changed <= ALLOWED_DIFF,
            'final increment must retain B corrections and touch C05/necessary C06-10 only')
    require(changed == set(freeze['audio_changed_ids']), 'actual text diff differs from final freeze')
    require(subtitle_changed == set(freeze['subtitle_changed_ids']) and
            subtitle_changed <= ALLOWED_DIFF,
            'actual subtitle diff differs from final freeze')
    refresh = set(freeze['picture_refresh_ids'])
    require('C05-01' in refresh and refresh <= ALLOWED_DIFF,
            'old C05-01 A-only/pending burned card must be replaced')
    for key in set(rows)-changed:
        old_row, _, _ = old_rows[key]; row, _, _ = rows[key]
        require(row['chapter_end_sample']-row['chapter_start_sample'] ==
                old_row['chapter_end_sample']-old_row['chapter_start_sample'],
                'unchanged audio duration differs: '+key)
        require(audio_fingerprint(row) == audio_fingerprint(old_row),
                'unchanged audio fragment identities differ: '+key)
    for chapter_id in ('E4-01','E4-02','E4-03','E4-04','E4-06'):
        if chapter_id == 'E4-06' and 'C06-10' in changed|subtitle_changed:
            continue
        require((chapters[chapter_id][0]['index']['bytes'], chapters[chapter_id][0]['index']['sha256'].lower()) == (old_chapters[chapter_id][0]['index']['bytes'], old_chapters[chapter_id][0]['index']['sha256'].lower()),
                'stable chapter index must remain exact: '+chapter_id)
    for key in changed:
        for fragment in rows[key][0]['fragments']:
            metadata = fragment.get('metadata')
            require(metadata is not None and fragment.get('WordBoundary_count',0)>0,
                    'new actual WordBoundary metadata missing: '+key)
            small_exact(metadata)
    config = bound_json(final['project_config'])
    cues = {r['id']:r for ch in config['chapters'] for r in ch['cues']}
    claims = bound_json(final['claim_ledger'])
    claimmap = {r['id']:r for r in claims['claims']}
    require(set(cues) == set(claimmap) == set(rows), 'project/ledger must bind all 69 paragraphs')
    for key in rows:
        row = rows[key][0]; cue = cues[key]; claim = claimmap[key]
        require(cue['narration']['zh'] == cue['subtitles']['zh'] ==
                claim['claim_summary'] == row['subtitles_zh'], 'Chinese source mismatch: '+key)
        require(cue['subtitles']['en'] == row['subtitles_en'], 'English source mismatch: '+key)
        require(claim.get('source_keys') and
                all(k in claims['source_catalog'] for k in claim['source_keys']),
                'missing source catalog: '+key)
        approved = freeze['approved_paragraphs'].get(key)
        require(approved is not None and approved['zh_sha256'] == sha_text(row['subtitles_zh'])
                and approved['en_sha256'] == sha_text(row['subtitles_en'])
                and approved['claim_status'] == claim['status'],
                'unapproved exact final sentence: '+key)
    subdelivery = bound_json(final['subtitle_delivery'])
    master = bound_json(subdelivery['full_global']['timeline'])
    small_exact(subdelivery['full_global']['subtitles'])
    require(master.get('schema') == 'xar.e04.actual-stable-full-subtitle-timeline.v1'
            and master['sample_rate'] == RATE and master['sample_frames'] ==
            audio['actual_PCM']['sample_frames'], 'full subtitle actual PCM clock differs')
    require(master['picture_frames_30fps'] == frame(master['sample_frames']),
            'full picture must use cumulative PCM frame clock')
    relative = bound_json(final['C05_relative_delivery'])
    relative_map = {r['paragraph_id']:r for r in relative['paragraphs']}
    if 'C06-10' in changed|refresh|subtitle_changed:
        c06 = final.get('C06_relative_delivery')
        require(c06 is not None and freeze.get('C06_relative_delivery') == c06,
                'changed C06-10 needs actual relative subtitles bound by Root freeze')
        extra = bound_json(c06)
        for row in extra['paragraphs']:
            require(row['paragraph_id'] not in relative_map, 'duplicate relative subtitle row')
            relative_map[row['paragraph_id']] = row
    old_picture = bound_json(spec['prior']['A_full_picture_receipt'])
    old_picture_map = {r['cue_id']:r for r in old_picture['timeline']}
    picture_rows = {r['id']:r for r in final['picture_rows']}
    require(set(picture_rows) == changed|refresh, 'only necessary changed/refresh pictures expected')
    require([r['id'] for r in master['paragraphs']] == [r['cue_id'] for r in old_picture['timeline']],
            'final global paragraph order differs')
    allocation = []; cursor = 0; sample_cursor = 0
    for paragraph in master['paragraphs']:
        key = paragraph['id']; row, chapter, index = rows[key]
        n = row['chapter_end_sample']-row['chapter_start_sample']
        require(paragraph['global_start_sample'] == sample_cursor and
                paragraph['global_end_sample'] == sample_cursor+n,
                'final global paragraph sample interval differs: '+key)
        start = frame(sample_cursor); end = frame(sample_cursor+n)
        prior = old_picture_map[key]
        old_n = prior['actual_picture_end_frame']-prior['actual_picture_start_frame']
        mode = 'new-native-picture' if key in changed else (
               'derived-picture-card-refresh' if key in refresh else 'exact-dry-picture-reuse')
        count = end-cursor if key in changed|refresh else old_n
        require(count > 0 and abs(cursor-start) <= 1 and abs(cursor+count-end) <= 1,
                'reuse exceeds one-frame cumulative cut bound: '+key)
        allocation.append({'cue_id':key,'mode':mode,'duration_frames':count,
                           'actual_start_frame':cursor,'actual_end_frame':cursor+count,
                           'canonical_start_frame':start,'canonical_end_frame':end,
                           'global_start_sample':sample_cursor,'global_end_sample':sample_cursor+n,
                           'prior':prior})
        if key in changed|refresh:
            visual = picture_rows[key]
            require(visual['text_zh'] == row['subtitles_zh'] and
                    visual['text_en'] == row['subtitles_en'], 'picture sentence mismatch: '+key)
            require(not re.search(r'R0?\d{3,4}', visual['source_label'], re.I),
                    'audience label exposes an internal run ID')
            require(visual.get('record_note') and len(visual['record_note']) <= 6
                    and all(isinstance(v,str) and len(v)<=33 for v in visual['record_note']),
                    'missing/oversize explicit evidence card: '+key)
            require(visual.get('title') and len(visual['title']) <=22 and
                    len(visual['source_label'])<=50, 'packaging text exceeds existing layout')
            item = relative_map.get(key)
            require(item is not None, 'relative subtitle binding missing: '+key)
            small_exact(item['subtitles']); timing = bound_json(item['timeline'])
            require(timing['paragraph_id'] == key and
                    timing['source_chapter_audio'] == index['audio'] and
                    timing['audio_slice']['start_sample'] == row['chapter_start_sample'] and
                    timing['audio_slice']['end_sample'] == row['chapter_end_sample'],
                    'actual relative subtitle source/PCM differs: '+key)
            require(''.join(e['zh'] for e in timing['events']) == row['subtitles_zh'] and
                    ' '.join(e['en'] for e in timing['events']) == row['subtitles_en'] and
                    all(e.get('timing_bindings') for e in timing['events']),
                    'relative subtitles do not bind exact text/actual timing: '+key)
            if key in changed:
                require(visual.get('visuals'), 'changed paragraph needs bounded moving source pixels: '+key)
        cursor += count; sample_cursor += n
    require(sample_cursor == master['sample_frames'], 'global sample sum differs')
    # Stable C06 has one possible final-frame grid excess. Trim one genuine last
    # frame during assembly; never clone, hold, loop, or insert narration silence.
    trim_tail = cursor-frame(sample_cursor)
    require(trim_tail in (0,1), 'final dry reuse cannot fit grid without forbidden hold/padding')
    if trim_tail:
        allocation[-1]['duration_frames'] -= 1
        allocation[-1]['actual_end_frame'] -= 1
        allocation[-1]['tail_real_frames_trimmed_at_assembly'] = 1
    return {'spec':spec,'freeze':freeze,'audio':audio,'master':master,
            'subdelivery':subdelivery,'relative':relative_map,'rows':rows,'claims':claims,
            'picture_rows':picture_rows,'changed':changed,'subtitle_changed':subtitle_changed,'refresh':refresh,
            'allocation':allocation,'trim_tail':trim_tail,'frames':frame(sample_cursor),
            'samples':sample_cursor,'chapter_map':chapters}

def import_base(spec):
    p = small_exact(spec['prior']['actual_A_renderer'])
    module_spec = importlib.util.spec_from_file_location('e4_actual_A_picture_base',p)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module

def validate_native_windows(row, used, prior_used):
    """Metadata checks reuse original audit; no whole original-raw read/hash/probe."""
    total = 0
    for visual in row['visuals']:
        require(visual.get('kind') == 'sealed-native-video' and visual.get('playback_rate') == 1,
                'moving 1x source only; stills cannot fill a paragraph')
        seal = bound_json(visual['seal_receipt']); seal=seal.get('body',seal)
        require(seal.get('state') == 'NORMAL_TREE_EMPTY' and
                seal['job']['returncode'] == 0 and seal['job']['job_active_processes'] == 0,
                'source recording is not normally closed')
        require(seal['raw'] == visual['source'], 'source differs from exact closed receipt')
        audit = bound_json(visual['existing_media_audit'])
        require(audit['source_identity'] == visual['source'], 'existing raw audit source differs')
        require(audit.get('state') in ('PASS','GREEN','AUTOMATED_MEDIA_PASS') or
                audit.get('overall') in ('PASS','GREEN') or audit.get('status') in ('PASS','GREEN'),
                'existing raw machine audit is not PASS')
        probe = bound_json(audit['probe_receipts']['streams-format']['stdout_identity'])
        video = next(s for s in probe['streams'] if s['codec_type']=='video')
        require((video['width'], video['height'], video['r_frame_rate'], video['time_base']) ==
                (1920,1080,'30/1','1/1000'), 'closed native raw geometry/clock differs')
        require(visual['source_geometry'] == [1920,1080] and visual['source_time_base']=='1/1000',
                'declared native source geometry/clock differs')
        review = bound_json(visual['window_review'])
        require(review['source_binding'] == visual['source'] and
                review.get('sampled_content_usable') is True, 'window sample content not reviewed')
        begin, end = visual['source_start_seconds'], visual['source_end_seconds_exclusive']
        n = visual['duration_frames']
        require(isinstance(n,int) and n>0 and 0<=begin<end and
                review['start_seconds']<=begin<end<=review['end_seconds_exclusive'] and
                end<=float(probe['format']['duration'])+float(Fraction(visual['source_time_base']))+1e-8 and end-begin>=n/FPS-float(Fraction(visual['source_time_base']))-1e-8,
                'moving source exceeds sampled/closed bounded window')
        key = str(Path(visual['source']['path']).resolve()).casefold()
        require(all(end<=a or b<=begin for a,b in prior_used.get(key,[])+used.get(key,[])),
                'native source repeats time already retained in final movie')
        used.setdefault(key,[]).append((begin,end)); total += n
        if visual.get('zoom'):
            z=visual['zoom'];x,y,w,h=z['crop_xywh'];ox,oy,ow,oh=z['output_xywh']
            require(all(isinstance(v,int) for v in (x,y,w,h,ox,oy,ow,oh)) and
                    min(x,y,ox,oy)>=0 and min(w,h,ow,oh)>0 and x+w<=1920 and y+h<=1080 and
                    ox+ow<=1920 and oy+oh<=900 and
                    0<=z['start_seconds']<z['end_seconds']<=n/FPS, 'invalid same-source zoom')
    require(total == row['duration_frames'], 'moving playlist must cover exact actual picture budget')
    require(not row.get('evidence_insets'),
            'still inset renderer not admitted here; use separate <=3s evidence-card source workflow')

def check(spec):
    ready = validate_ready(spec)
    used, prior_used = {}, {}
    for entry in ready['allocation']:
        if entry['mode'] != 'new-native-picture':
            for visual in entry['prior']['dynamic_source_windows']:
                key=str(Path(visual['source']['path']).resolve()).casefold()
                prior_used.setdefault(key,[]).append((visual['source_start_seconds'],visual['source_end_seconds_exclusive']))
    for entry in ready['allocation']:
        if entry['mode']=='new-native-picture':
            row=copy.deepcopy(ready['picture_rows'][entry['cue_id']])
            row['duration_frames']=entry['duration_frames']
            validate_native_windows(row,used,prior_used)
    return ready

def sample_clock_mix(graph):
    """Use integer sample N at a declared 48k time base; no seconds roundtrip.

    Formal v0.2.1 produces two 48k stems and a final 48k mix. If a future
    formal implementation changes this graph, refuse rather than guess.
    """
    require(graph.count('asetpts=N/SR/TB') == 3,
            'formal two-stem mix clock changed; review public API output first')
    return graph.replace('asetpts=N/SR/TB','asettb=expr=1/48000,asetpts=N')

def render(spec, workdir):
    # All admission here is project metadata. Final movie audit and human1x
    # remain separate new tasks, regardless of a successful encode returncode.
    ready = check(spec)
    root = Path(workdir).resolve()
    require(not root.exists(), 'fresh output directory required')
    base = import_base(spec)
    import wave
    import importlib.metadata
    from PIL import Image,ImageDraw,ImageFont
    from xar_promo import probe_and_write_bound_media
    from xar_promo.audio import AudioMixSpec,AudioStem,plan_audio_mix
    from xar_promo.process import CommandSpec,run_command
    from xar_promo.render import ass_burn_in_filter
    release=bound_json(spec['final']['release_probe'])
    require(importlib.metadata.version('xar-promo-toolchain') ==
            release['explicit_python']['distribution_version'], 'installed formal wheel differs')
    ffmpeg,ffprobe = base.exact(spec['tools']['ffmpeg']),base.exact(spec['tools']['ffprobe'])
    for name in ('zh','en'):base.exact(spec['fonts'][name])
    music=base.exact(spec['music']['source'])
    require(spec['music']['title']=='Quiet Courtly Tension' and spec['music']['gain_db']==-17
            and spec['music']['ducking'] is False and spec['music']['normalize'] is False
            and spec['music']['source']['sha256'].lower()==base.MUSIC_SHA, 'fixed series music differs')
    narration=base.exact(ready['audio']['stable_audio'])
    with wave.open(str(narration),'rb') as source:
        require((source.getframerate(),source.getnchannels(),source.getsampwidth(),source.getnframes())
                == (RATE,1,2,ready['samples']), 'actual full PCM header differs')
    root.mkdir(parents=True,exist_ok=False)
    new(root/'input-snapshot.json',spec)
    new(root/'allocation-snapshot.json',[{k:v for k,v in e.items() if k!='prior'} for e in ready['allocation']])
    outputs=[]; timeline=[]
    for entry in ready['allocation']:
        key=entry['cue_id'];mode=entry['mode'];prior=entry['prior']
        if mode=='exact-dry-picture-reuse':
            # Do not rehash old 53 MOVs. Exact identities and bound probe were
            # already produced and sealed; current size is a limited check.
            output=prior['output'];p=Path(output['path'])
            require(p.stat().st_size==output['bytes'], 'old dry picture size differs: '+key)
            probe=bound_json(prior['old_or_increment_bound_probe'])
            require(probe['subject']['sha256'].lower()==output['sha256'].lower() and
                    probe['subject']['bytes']==output['bytes'], 'sealed dry probe identity differs')
            base.verify_output_probe(probe,prior['actual_picture_end_frame']-prior['actual_picture_start_frame'],pcm=None)
            record=copy.deepcopy(prior)
            record['media_byte_revalidation']='prior sealed SHA/probe + current size; no new whole MOV hash'
        else:
            row=copy.deepcopy(ready['picture_rows'][key]);row['duration_frames']=entry['duration_frames']
            row['audio_start_sample']=ready['rows'][key][0]['chapter_start_sample']
            row['audio_end_sample']=ready['rows'][key][0]['chapter_end_sample']
            row['subtitle_timing']=ready['relative'][key]['timeline']
            row['subtitles_ass']=ready['relative'][key]['subtitles']
            row['audio_index']=ready['rows'][key][1]['index']
            row['claim_ledger']=spec['final']['claim_ledger']
            cue_root=root/key;cue_root.mkdir()
            plate_path=cue_root/'packaging.png'
            base.plate(plate_path,row,spec['fonts'])
            if mode=='derived-picture-card-refresh':
                # Replace the entire old opaque card, including its rounded
                # corners. No old A-only/pending text is allowed to shine through.
                old_input = spec['prior']['A_C05_picture_input'] if key.startswith('C05-') else spec['prior']['A_stable_picture_input']
                oldrow=next(r for r in bound_json(old_input)['cues'] if r['id']==key)
                h=64+max(len(oldrow['record_note']),len(row['record_note']))*43
                image=Image.open(plate_path).convert('RGBA');draw=ImageDraw.Draw(image)
                draw.rectangle((28,22,610,90),fill=base.PANEL+'FF')
                draw.text((48,32),row['title'],font=ImageFont.truetype(spec['fonts']['zh']['path'],35),fill=base.INK)
                draw.rectangle((1240,24,1890,72),fill=base.PANEL+'FF')
                draw.text((1260,32),row['source_label'],font=ImageFont.truetype(spec['fonts']['zh']['path'],23),fill=base.GOLD)
                draw.rectangle((1060,112,1890,112+h),fill=base.PANEL+'FF')
                draw.text((1084,126),'研究记录 · 独立样本',font=ImageFont.truetype(spec['fonts']['zh']['path'],26),fill=base.GOLD)
                for i,line in enumerate(row['record_note']):
                    draw.text((1084,172+i*43),line,font=ImageFont.truetype(spec['fonts']['zh']['path'],29),fill=base.INK)
                revised=cue_root/'packaging-card-covered.png'
                with revised.open('xb') as f:image.save(f,format='PNG')
                plate_path=revised
                p=Path(prior['output']['path']);require(p.stat().st_size==prior['output']['bytes'],'refresh dry source size differs')
                base.verify_output_probe(bound_json(prior['old_or_increment_bound_probe']),
                    prior['actual_picture_end_frame']-prior['actual_picture_start_frame'],pcm=None)
                require(entry['duration_frames'] <= prior['actual_picture_end_frame']-prior['actual_picture_start_frame'],
                        'card refresh cannot extend/hold old dry source')
                native=['-threads','1','-i',p]
                filters=[f'[0:v]trim=end_frame={entry["duration_frames"]},setpts=PTS-STARTPTS,setsar=1[native]']
                image_index=1;source_reads=copy.deepcopy(prior['actual_source_decodes'])
            else:
                native=[];filters=[]
                for i,v in enumerate(row['visuals']):
                    begin,end=v['source_start_seconds'],v['source_end_seconds_exclusive']
                    native+=['-threads','1','-ss',f'{begin:.6f}','-to',f'{end:.6f}','-i',v['source']['path']]
                    tick=Fraction(v['source_time_base']);a=math.ceil(Fraction(str(begin))/tick);b=math.ceil(Fraction(str(end))/tick)
                    part=f'[{i}:v]trim=start_pts={a}:end_pts={b},showinfo@source_{i},setpts=PTS-STARTPTS,setsar=1,fps=30,trim=end_frame={v["duration_frames"]}'
                    if v.get('zoom'):
                        z=v['zoom'];x,y,w,h=z['crop_xywh'];ox,oy,ow,oh=z['output_xywh']
                        filters += [part+f',split=2[main{i}][zoomraw{i}]',f'[zoomraw{i}]crop={w}:{h}:{x}:{y}:exact=1,scale={ow}:{oh}:flags=lanczos,format=rgba,fade=t=in:st={z["start_seconds"]:.6f}:d=0.25:alpha=1,fade=t=out:st={max(z["start_seconds"],z["end_seconds"]-.25):.6f}:d=0.25:alpha=1[z{i}]',f'[main{i}][z{i}]overlay=x={ox}:y={oy}:shortest=1:enable=\'between(t,{z["start_seconds"]},{z["end_seconds"]})\',format=yuv420p[v{i}]']
                    else:filters+=[part+f',format=yuv420p[v{i}]']
                image_index=len(row['visuals'])
                filters+=[''.join(f'[v{i}]' for i in range(image_index))+f'concat=n={image_index}:v=1:a=0[native]']
                source_reads=[]
            duration=entry['duration_frames']/FPS
            graph=cue_root/'filter.txt'
            filters += [f'[native][{image_index}:v]overlay=shortest=1[packaged]']
            if mode=='new-native-picture':
                clock=0
                font_path=Path(spec['fonts']['zh']['path']).as_posix().replace(':',r'\:').replace("'",r"\'")
                label_filters=[]
                for source_i,visual in enumerate(row['visuals']):
                    label=visual.get('visible_context_label')
                    require(isinstance(label,str) and 0<len(label)<=50 and not re.search(r'R0?\d{3,4}',label,re.I),'missing audience source label')
                    label_path=cue_root/f'context-label-{source_i}.txt'
                    new(label_path,label)
                    begin=clock/FPS;clock+=visual['duration_frames'];end=clock/FPS
                    enable=f"gte(t,{begin:.9f})*lt(t,{end:.9f})"
                    label_filters += [f"drawbox=x=1240:y=24:w=650:h=48:color={base.PANEL}:t=fill:enable='{enable}'",
                        f"drawtext=fontfile='{font_path}':textfile='{key}/context-label-{source_i}.txt':x=1260:y=32:fontsize=23:fontcolor={base.GOLD}:enable='{enable}'"]
                require(clock==entry['duration_frames'],'per-source label clock differs')
                filters += ['[packaged]'+','.join(label_filters)+'[picture]']
            else:filters += ['[packaged]null[picture]']
            new(graph,';\n'.join(filters))
            output_path=cue_root/'picture-dry.mov'
            argv=[ffmpeg,'-hide_banner','-nostdin','-n']+(['-copyts'] if mode=='new-native-picture' else [])+native+['-threads','1','-loop','1','-framerate','30','-t',f'{duration:.9f}','-i',plate_path,'-filter_complex_threads','1','-/filter_complex',graph,'-map','[picture]','-an','-frames:v',str(entry['duration_frames']),'-t',f'{duration:.9f}','-c:v','libx264','-preset','ultrafast','-crf','22','-threads','2','-r','30','-fps_mode','cfr','-pix_fmt','yuv420p','-movflags','+faststart',output_path]
            raw_stats=[(Path(v['source']['path']).stat().st_size,Path(v['source']['path']).stat().st_mtime_ns) for v in row.get('visuals',[])] if mode=='new-native-picture' else []
            result=run_command(CommandSpec.create(argv,label='Episode04 final incremental picture '+key,cwd=root,partial_artifacts=(output_path,)),audit_directory=cue_root/'render-command-audit')
            if mode=='new-native-picture':
                require(raw_stats==[(Path(v['source']['path']).stat().st_size,Path(v['source']['path']).stat().st_mtime_ns) for v in row['visuals']],'closed raw changed during bounded render')
                for i,v in enumerate(row['visuals']):
                    pts=[int(re.search(r'\bpts:\s*(-?\d+)',line)[1]) for line in result.stderr.splitlines() if 'showinfo@source_'+str(i)+' ' in line and re.search(r'\bpts:\s*(-?\d+)',line)]
                    tick=Fraction(v['source_time_base']);a=math.ceil(Fraction(str(v['source_start_seconds']))/tick);b=math.ceil(Fraction(str(v['source_end_seconds_exclusive']))/tick)
                    require(len(pts)>=v['duration_frames'] and all(a<=p<b for p in pts) and all(p<q for p,q in zip(pts,pts[1:])), 'bounded decoded source PTS differs')
                    source_reads.append({'source_index':i,'decoded_frames':len(pts),'first_actual_pts':pts[0],'last_actual_pts':pts[-1],'time_base':v['source_time_base']})
            probe_and_write_bound_media(str(ffprobe),output_path,output_path=cue_root/'picture.bound-probe.json',audit_directory=cue_root/'probe-command-audit')
            base.verify_output_probe(read(cue_root/'picture.bound-probe.json'),entry['duration_frames'],pcm=None)
            output={'path':str(output_path), **read(cue_root/'picture.bound-probe.json')['subject']}
            record={'output':output,'old_or_increment_bound_probe':binding(cue_root/'picture.bound-probe.json'),
                    'dynamic_source_windows':row['visuals'] if mode=='new-native-picture' else prior['dynamic_source_windows'],
                    'actual_source_decodes':source_reads,'packaging':row,
                    'original_render_receipt':spec['prior']['A_full_picture_receipt']}
            print(json.dumps({'state':'ACTUAL_NEW_PICTURE_RENDERED','cue':key,'frames':entry['duration_frames'],'mode':mode}),flush=True)
        record.update({k:v for k,v in entry.items() if k!='prior'})
        timeline.append(record);outputs.append(output)
    concat=root/'picture-concat.txt'
    require(all("'" not in p['path'] and '\n' not in p['path'] for p in outputs),'unsupported concat filename')
    new(concat,'ffconcat version 1.0\n'+''.join("file '"+Path(p['path']).as_posix()+"'\n" for p in outputs))
    dry=root/'picture-dry.mov'
    run_command(CommandSpec.create([ffmpeg,'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',concat,'-map','0:v:0','-an','-c','copy','-movflags','+faststart',dry],label='Final BC exact dry reuse and changed picture concat',cwd=root,partial_artifacts=(dry,)),audit_directory=root/'concat-command-audit')
    ass=small_exact(ready['subdelivery']['full_global']['subtitles']);duration=ready['frames']/FPS
    theme=AudioMixSpec(stems=(AudioStem('narration',narration),AudioStem('series-theme',music,gain_db=-17)),duration_seconds=duration,sample_rate=48000,channels=2,normalize=False,metadata={'ducking':False,'music':'Quiet Courtly Tension','gain_db':-17,'continuous_across_cues':True,'exact_narration_PCM_no_inserted_silence':True})
    mix=plan_audio_mix(theme,input_start_index=1,output_label='mixed')
    exact_mix_graph=sample_clock_mix(mix.filtergraph)
    graph=f'[0:v]trim=end_frame={ready["frames"]},'+ass_burn_in_filter(ass)+'[subtitled];'+exact_mix_graph
    final_path=root/'CK3-War-AI-Episode04-March-Logistics-Review01.mp4'
    run_command(CommandSpec.create([ffmpeg,'-hide_banner','-nostdin','-n','-threads','1','-i',dry,'-i',narration,'-stream_loop','-1','-i',music,'-filter_complex_threads','1','-filter_complex',graph,'-map','[subtitled]','-map','[mixed]','-c:v','libx264','-preset','ultrafast','-crf','22','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-enc_time_base:a','1:48000','-movie_timescale','48000','-video_track_timescale','48000','-frames:v',str(ready['frames']),'-t',f'{duration:.9f}','-movflags','+faststart',final_path],label='Final BC six-chapter review picture with actual global PCM/ASS',cwd=root,partial_artifacts=(final_path,)),audit_directory=root/'final-encode-command-audit')
    probe_and_write_bound_media(str(ffprobe),final_path,output_path=root/'picture.bound-probe.json',audit_directory=root/'final-probe-command-audit')
    final_probe=read(root/'picture.bound-probe.json')
    base.verify_output_probe(final_probe,ready['frames'],pcm=False)
    audio_stream=next(v for v in final_probe['ffprobe']['streams'] if v['codec_type']=='audio')
    require(audio_stream['time_base']=='1/48000' and audio_stream['start_pts']==0, 'encoded AAC sample time base/origin differs')
    report={'schema':'xar.e04.final-BC-review-picture.v1','state':'ACTUAL_FINAL_BC_REVIEW_CANDIDATE_RENDERED',
            'created_utc':datetime.now(timezone.utc).isoformat(),'picture':{'path':str(final_path), **final_probe['subject']},
            'bound_probe':binding(root/'picture.bound-probe.json'),'producer':binding(__file__),
            'input':binding(root/'input-snapshot.json'),'timeline':timeline,
            'actual_PCM_samples':ready['samples'],'actual_PCM_seconds':ready['samples']/RATE,
            'duration_frames':ready['frames'],'actual_video_seconds':duration,
            'final_grid_tail_seconds':duration-ready['samples']/RATE,
            'real_last_frames_trimmed':ready['trim_tail'],'inserted_narration_silence_samples':0,
            'audio_changed_ids':sorted(ready['changed']),'picture_refresh_ids':sorted(ready['refresh']),
            'subtitle_changed_ids':sorted(ready['subtitle_changed']),
            'whole_original_raw_rehashes':0,'old_dry_picture_rehashes':0,
            'exact_audio_clock_policy':{'mix_time_base':'1/48000','asetpts':'N','encoder_time_base':'1:48000','movie_timescale':48000,'video_track_timescale':48000,'AAC_frame_samples':1024,'full_decode_continuity_not_yet_verified':True},
            'expected_AAC_decoded_samples_excluding_priming_and_discard_padding':ready['frames']*1600,
            'expected_AAC_final_packet_discard_padding_samples':math.ceil(ready['frames']*1600/1024)*1024-ready['frames']*1600,
            'stable_dry_reuse_count':sum(e['mode']=='exact-dry-picture-reuse' and not e['cue_id'].startswith('C05-') for e in ready['allocation']),
            'B_status':'STOPPED_GATE_INCOMPLETE','B_London_comparable':False,'winner':None,
            'C_result_receipt':spec['final']['C_terminal_receipt'],
            'C_sampling_deviation_review':ready['freeze']['C_sampling_deviation_review'],
            'continuous_source_clean_review':False,'whole_machine_video_audio_decode':None,
            'exact_audio_PTS_continuity':None,'historical_A_exact_audio_PTS_continuity':'RED',
            'human_full_1x_review':False,'human_signoff':False,'full_film_ready':False,
            'preview_only':True,'Game_SDK_UI_Bus_Git_OneDrive_operations':0}
    new(root/'picture-receipt.json',report)
    return {k:v for k,v in report.items() if k!='timeline'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',nargs='?',choices=('plan','check','render'),default='plan')
    parser.add_argument('--input',type=Path,default=Path(__file__).with_name('input-pending.json'))
    parser.add_argument('--workdir',type=Path)
    args=parser.parse_args()
    try:
        spec=read(args.input)
        if args.operation=='plan': result=metadata_plan(spec)
        elif args.operation=='check':
            checked=check(spec)
            result={'state':'FINAL_METADATA_READY_FOR_EXPLICIT_REVIEW_RENDER',
                    'changed_audio_ids':sorted(checked['changed']),
                    'picture_refresh_ids':sorted(checked['refresh']),
                    'samples':checked['samples'],'frames':checked['frames'],
                    'last_real_frames_to_trim':checked['trim_tail'],
                    'media_reads':0,'processes_started':0,'human_signoff':False}
        else:
            require(args.workdir is not None,'render requires a fresh --workdir')
            result=render(spec,args.workdir)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (Stop,KeyError,StopIteration,OSError,ValueError) as exc:
        print(json.dumps({'state':'STOP','reason':str(exc),'human_signoff':False},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
