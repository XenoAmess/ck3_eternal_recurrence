"""Bounded episode review assembly, with external immutable inputs and direct artifacts.

No game access or TTS. A plan may contain gaps; a build may not. Direct output
registration deliberately avoids handle_build's intermediate CAS media copies.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys

from xar_promo.model import RunManifest, SourceRecord
from xar_promo.operations import start_run, preserve_artifact, _replace_run
from xar_promo.project import load_document
from xar_promo.render import RenderOptions, execute_render_plan, plan_concat, plan_render
from xar_promo.subtitles import AssCue, AssDocumentConfig, AssStyleConfig, SubtitleTrackConfig, render_ass_document
from xar_promo.layout import FontSpec, WrapPolicy, wrap_text
from xar_promo.audio import AudioMixSpec, AudioStem, plan_audio_mix
from PIL import Image, ImageFont

from .production import fresh_runtime, pin, read, write, project, cue_duration, package_bytes
from .context_composer import font_render_planner

SCHEMA = 'ck3-faith-power-full-edit-v1'
MAX_SECONDS = 1860
MAX_SEGMENTS = 168
VIDEO_RATE = 3_000_000
BUFFER_BITS = 3_000_000
AUDIO_RATE = 192_000
SIDE_BYTES = (64 + 32 + 16 + 32 + 16) * 1024**2
MUSIC_REPO_PATH = 'promo/ck3_native_war_ai/assets/music/quiet-courtly-tension.wav'
MUSIC_BYTES = 30_726_160
MUSIC_SHA256 = 'fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f'


@dataclass(frozen=True)
class RenderProfile:
    id: str
    max_seconds: int
    max_segments: int = MAX_SEGMENTS

    def to_mapping(self):
        return {'schema':'ck3-faith-power-immutable-render-profile-v1','id':self.id,
            'max_seconds':self.max_seconds,'max_segments':self.max_segments,
            'video_maxrate_bps':VIDEO_RATE,'video_bufsize_bits':BUFFER_BITS,'audio_bitrate_bps':AUDIO_RATE,
            'geometry':[2560,1440,30],'crf':21,'preset':'veryfast'}


DEFAULT_PROFILE = RenderProfile('episode01-31m-1440p30-v1', MAX_SECONDS)
EXTENDED_PROFILE = RenderProfile('episode01-35m-1440p30-v1', 2100)
PADDING_PROFILE = RenderProfile('episode01-2101s-1440p30-v1', 2101)


def render_profile(document, bound):
    reference=document.get('render_profile')
    if reference is None:return DEFAULT_PROFILE
    if Path(reference['path']).suffix.lower()!='.json':raise ValueError('Render profile must be pinned JSON')
    actual=read(bound(reference))
    for profile in (DEFAULT_PROFILE,EXTENDED_PROFILE,PADDING_PROFILE):
        if actual==profile.to_mapping():return profile
    raise ValueError('Unknown immutable render profile or changed quality settings')


def background_music(document, bound, *, repo=None):
    reference=document.get('background_music')
    if reference is None:return None
    if (not isinstance(reference,dict) or set(reference)!={'path','bytes','sha256'}
        or reference['bytes']!=MUSIC_BYTES or reference['sha256'].lower()!=MUSIC_SHA256):
        raise ValueError('Use the exact existing Quiet Courtly Tension WAV')
    path=Path(reference['path']).resolve()
    if repo is not None and path!=(Path(repo)/MUSIC_REPO_PATH).resolve():
        raise ValueError('Use the repository music asset directly; do not copy it')
    if tuple(part.lower() for part in path.parts[-len(Path(MUSIC_REPO_PATH).parts):])!=tuple(part.lower() for part in Path(MUSIC_REPO_PATH).parts):
        raise ValueError('Music path is not the canonical repository asset')
    bound(reference)  # Formal metadata-only binding stats this binary; normal build verifies bytes.
    return {'file':reference,'narration_gain_db':0,'music_gain_db':-17,'loop_same_original':True,
        'fade_in_seconds':2,'fade_out_seconds':8,'ducking':False,'normalize':False,
        'sample_rate':48000,'channels':2,'audio_bitrate_bps':AUDIO_RATE,'extra_audio_file_bytes':0}


def validate_burned_in_disclosure(part, bound):
    declared=part.get('burned_in_disclosure')
    if declared is None:return False
    if (part['kind'] not in {'diagram','native-readback'} or not isinstance(declared,dict)
        or set(declared)!={'source_class','text','render_receipt'}
        or declared['source_class']!=part['kind'] or declared['text']!=part['disclosure']):
        raise ValueError('Burned disclosure must bind this exact graphic class and text; raw gameplay cannot hide its label')
    reference=declared['render_receipt']
    if Path(reference['path']).suffix.lower()!='.json':raise ValueError('Disclosure needs a small render receipt')
    receipt=read(bound(reference))
    schemas={'native-readback':{'ck3-faith-power-native-readback-card-v1'},
        'diagram':{'ck3-faith-power-result-source-diagram-v1','ck3-faith-power-micro-source-diagram-v1'}}
    if (receipt.get('schema') not in schemas[part['kind']] or receipt.get('image')!=part['image']
        or receipt.get('permanent_disclosure')!=declared['text']):
        raise ValueError('Burned disclosure differs from the exact image render receipt')
    return 'focus_rect' not in part  # Original full-image receipt cannot prove a cropped label visible.


def focus_geometry(part, bound, *, metadata_only=False):
    """Validate integer xywh; metadata plans defer real PNG geometry."""
    if 'focus_rect' not in part:return None
    if part['kind'] not in {'diagram','native-readback'}:
        raise ValueError('focus_rect is allowed only for diagram/native-readback PNGs')
    rect=part['focus_rect']
    if (not isinstance(rect,(list,tuple)) or len(rect)!=4
        or any(type(value) is not int for value in rect)):
        raise ValueError('focus_rect needs four finite integers; bool/float/NaN/Infinity are invalid')
    x,y,width,height=rect
    if x<0 or y<0 or width<=0 or height<=0:
        raise ValueError('focus_rect needs nonnegative origin and positive width/height')
    path=bound(part['image'])
    if metadata_only:
        return {'focus_rect':list(rect),'source_geometry':None,'source_geometry_checked':False,
            'verification':'deferred to normal PNG prepare; binary stat only'}
    with Image.open(path) as source:
        if source.format!='PNG':raise ValueError('focus_rect requires an actual PNG source')
        actual_width,actual_height=source.size  # Header only; no pixel decode/load.
    if x+width>actual_width or y+height>actual_height:
        raise ValueError('focus_rect is outside the actual source PNG dimensions')
    return {'focus_rect':list(rect),'source_geometry':[actual_width,actual_height],
        'source_geometry_checked':True,'verification':'actual source PNG header'}


def focus_filter(part, bound):
    checked=focus_geometry(part,bound)
    if checked is None:return 'scale=2560:1440:flags=lanczos'
    x,y,width,height=checked['focus_rect']
    return (f'crop={width}:{height}:{x}:{y},'
        'scale=2560:1120:force_original_aspect_ratio=decrease:flags=lanczos,'
        'pad=2560:1440:(ow-iw)/2:0:color=0x211813')


def now(): return datetime.now(timezone.utc).isoformat()


def media_limit(seconds, *, audio):
    return math.ceil(((VIDEO_RATE + (AUDIO_RATE if audio else 0)) * seconds + BUFFER_BITS) / 8 * 1.05)


def peak_budget(seconds=None, segments=MAX_SEGMENTS, *, profile=DEFAULT_PROFILE):
    """New future bytes, not an existing-package cap or measured output size."""
    if profile not in (DEFAULT_PROFILE,EXTENDED_PROFILE,PADDING_PROFILE):raise ValueError('Unknown render profile')
    seconds=profile.max_seconds if seconds is None else seconds
    if not 0 < seconds <= profile.max_seconds or not 0 < segments <= profile.max_segments:
        raise ValueError(f'{profile.max_seconds}-second / {profile.max_segments}-segment limit exceeded')
    visual = math.ceil((VIDEO_RATE * seconds + BUFFER_BITS * segments) / 8 * 1.05)
    narrated = math.ceil(((VIDEO_RATE + AUDIO_RATE) * seconds + BUFFER_BITS * segments) / 8 * 1.05)
    overshoot = math.ceil(BUFFER_BITS / 8) * (2 * segments + 1)
    total = visual + narrated * 2 + SIDE_BYTES + overshoot
    return {'max_seconds':seconds,'segments':segments,'render_profile':profile.to_mapping(),'prepared_visual_bytes':visual,
        'narrated_segment_bytes':narrated,'concat_deliverable_bytes':narrated,
        'graphics_metadata_audio_audit_scratch_bytes':SIDE_BYTES,
        'conservative_packet_overshoot_bytes':overshoot,'peak_new_bytes':total,
        'video_maxrate_bps':VIDEO_RATE,'video_bufsize_bits':BUFFER_BITS,'audio_bitrate_bps':AUDIO_RATE,
        'geometry':[2560,1440,30],'crf':21,'preset':'veryfast','container_allowance_fraction':0.05,
        'media_CAS_copies':0,'whole_raw_or_existing_MP3_copies':0,
        'artifact_mode':'direct actual run-relative outputs; explicit external SHA-bound inputs',
        'file_size_caps_required':True,'once_attempt_no_automatic_retry':True}


def admit_v2(repo, reservation, package_root, output, machine, peak):
    reservation=Path(reservation).resolve(); ledger=read(reservation)
    policy_path=Path(repo)/'docs/storage-retention-policy.json'; policy=read(policy_path)
    if (ledger.get('schema')!='machine-storage-coordination-episode01-v2'
        or ledger.get('machine_id')!=machine or ledger.get('state')!='ROOT_LOCK_ACTIVATED'
        or ledger.get('capacity_reservation_active') is not True
        or ledger.get('root_supersedes_previous_future_commitments') is not True
        or not ledger.get('capacity_passed') or not ledger.get('quota_passed')
        or datetime.fromisoformat(ledger['reservation_review_at_utc'])<=datetime.now(timezone.utc)):
        raise ValueError('Current same-machine root-activated v2 reservation required')
    selected=[r for r in ledger['reservations'] if r['task']=='episode01-production']
    if len(selected)!=1 or not 0<peak<=selected[0]['peak_bytes']:
        raise ValueError('Concrete future production peak exceeds active envelope')
    root=Path(package_root).resolve(); Path(output).resolve().relative_to(root)
    if any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('Production package may not cross a symlink')
    used=package_bytes(root)
    baseline=selected[0]['measured_existing_occupied_path_bytes']
    growth=max(0,used-baseline)
    if growth+peak>selected[0]['peak_bytes']:
        raise ValueError('Post-activation production growth plus this peak exceeds v2 ceiling')
    disk=shutil.disk_usage(root); cap=policy['capacity']
    safety=max(cap['safety_floor_bytes'],min(cap['safety_ceiling_bytes'],disk.total*cap['safety_volume_fraction']))
    all_peaks=sum(row['peak_bytes'] for row in ledger['reservations'])
    system=ledger['profile']['system_growth_reserve_bytes_by_volume'][root.anchor.replace('\\','/')]
    if disk.free<all_peaks+system+safety:
        raise ValueError('Fresh free space does not cover concurrent future commitments')
    if ledger['current_project_usage_upper_bound_bytes']+all_peaks>ledger['effective_project_quota_bytes']:
        raise ValueError('Shared project quota does not cover admitted future commitments')
    return {'machine_id':machine,'observed_at_utc':now(),'evidence_source':'Exact active v2 ledger, common policy, current package allocation and fresh disk readback',
        'reservation':pin(reservation),'policy':pin(policy_path),'reservation_task':'episode01-production',
        'existing_charged_baseline_bytes':baseline,'current_package_bytes':used,
        'post_activation_growth_bytes':growth,'concrete_peak_new_bytes':peak,
        'future_envelope_bytes':selected[0]['peak_bytes'],'disk':disk._asdict(),
        'capacity_passed':True,'quota_passed':True,'render_started':False}


class Inputs:
    def __init__(self, document):
        self.document=document; self.errors=[]; self.parts=[]
        self._verified={}

    def bound(self, declared):
        if not isinstance(declared,dict) or set(declared)!={'path','bytes','sha256'}:
            raise ValueError('Expected exact path/bytes/SHA binding')
        path=Path(declared['path']).resolve()
        key=(str(path),declared['bytes'],declared['sha256'].lower())
        if key not in self._verified:
            actual=pin(path)
            if (actual['bytes'],actual['sha256'].lower())!=key[1:]:
                raise ValueError('Input bytes changed: '+str(path))
            self._verified[key]=path
        return path

    def inspect(self):
        doc=self.document
        if doc.get('schema')!=SCHEMA or not doc.get('machine_id'):
            raise ValueError('Unknown explicit full-edit schema/machine')
        scope=doc.get('scope')
        if scope not in {'episode01-full-review','episode01-adoption-review-segment'}:
            raise ValueError('Declare full episode or the separate adoption review segment')
        assembly=read(self.bound(doc['assembly_plan']))
        baseline={r['entry_id']:r for r in assembly['entries'] if r['kind']=='measured-cue'}
        if len(baseline)!=158:
            raise ValueError('Expected the frozen 158-cue audio inventory')
        selected_ids={r['id'] for r in doc['cues']}
        if len(selected_ids)!=len(doc['cues']):
            raise ValueError('Duplicate measured cue ID')
        exclusions=doc.get('excluded_cues',[])
        if scope=='episode01-full-review':
            excluded_ids={row['id'] for row in exclusions if row.get('reason')}
            if (len(excluded_ids)!=len(exclusions) or selected_ids&excluded_ids
                or selected_ids|excluded_ids!=set(baseline)):
                raise ValueError('Full episode needs all frozen cues or explicit reasoned exclusions')
        elif not selected_ids.issubset(baseline):
            raise ValueError('Short review references an unknown existing cue')
        rows=[]; intervals={}; focus_checks=[]
        for row in doc['cues']:
            old=baseline[row['id']]
            if any(row[key]!=old[key] for key in ('zh','en','claim_ids','shot_ids')):
                raise ValueError('Frozen cue changed: '+row['id'])
            if row['audio']!=old['audio'] or row['speech_duration_seconds']!=old['speech_duration_seconds']:
                raise ValueError('Existing measured voice changed: '+row['id'])
            self.bound(row['audio'])
            request=read(self.bound(old['provider_request']))
            if request['request']['text']!=row['zh']:
                raise ValueError('Frozen provider request text differs')
            expected=cue_duration(row['speech_duration_seconds'])
            if abs(row['duration_seconds']-expected)>1e-6:
                raise ValueError('Measured cue clock changed')
            rows.append(row)
        slots=doc.get('result_slots',{})
        if set(slots)!={'E01-L01','E01-L02','E01-L03'}:
            raise ValueError('Keep all three explicit result slots')
        for key in ('E01-L01','E01-L03'):
            if slots[key] is None:self.errors.append(key+': independent live result and measured narration unbound')
        for key,value in slots.items():
            if value is None:continue
            if value['id']!=key or not value.get('outcome') or not value.get('cues'):
                raise ValueError('A filled result slot needs actual editorial outcome and measured sentences')
            phases=value.get('native_receipts',{})
            if set(phases)!={'before','action','after'}:
                raise ValueError('Result needs explicit independent before/action/after receipts')
            paths=[self.bound(phases[phase]) for phase in ('before','action','after')]
            if len(set(paths))!=3:
                raise ValueError('Independent after receipt cannot reuse action ACK or before file')
            checks=value.get('native_checks',[])
            if not checks:raise ValueError('Result needs concrete JSON-pointer equality checks')
            for check in checks:
                result=read(self.bound(check['file']))
                for component in check['json_pointer'].split('/')[1:]:
                    component=component.replace('~1','/').replace('~0','~')
                    result=result[int(component)] if isinstance(result,list) else result[component]
                if result!=check['equals']:raise ValueError('Actual native result assertion differs')
            for sentence in value['cues']:
                if not sentence.get('zh') or not sentence.get('en'):
                    raise ValueError('Each result sentence needs matching bilingual text')
                if sentence['id'] in baseline:
                    raise ValueError('New result narration cannot replace a frozen existing audio ID')
                self.bound(sentence['audio'])
                request=read(self.bound(sentence['provider_request']))
                if request['request']['text']!=sentence['zh']:
                    raise ValueError('New result audio request text differs')
                if abs(sentence['duration_seconds']-cue_duration(sentence['speech_duration_seconds']))>1e-6:
                    raise ValueError('Result audio must have a measured frame-aligned clock')
                rows.append(sentence)
        order=doc['sequence']
        byid={row['id']:row for row in rows}
        if len(order)!=len(set(order)) or set(order)!=set(byid):
            raise ValueError('Sequence must contain every measured cue and only filled slots exactly once')
        ordered=[byid[key] for key in order]
        for row in ordered:
            parts=row.get('visual_parts')
            if parts is None:
                self.errors.append(row['id']+': visual parts unbound');continue
            if not parts or abs(sum(p['duration_seconds'] for p in parts)-row['duration_seconds'])>1e-6:
                raise ValueError('Visual parts must exactly cover their measured cue')
            for part in parts:
                validate_burned_in_disclosure(part,self.bound)
                focus=focus_geometry(part,self.bound)
                if focus is not None:focus_checks.append({'cue_id':row['id'],**focus})
                duration=part['duration_seconds']
                if duration<=0 or abs(duration*30-round(duration*30))>1e-4:
                    raise ValueError('Each authored visual duration must align to 30fps')
                if not part.get('disclosure'):
                    raise ValueError('Each visual part needs an explicit source/experiment disclosure')
                kind=part['kind']
                if kind in {'diagram','native-readback'}:
                    if duration>6.4:raise ValueError('One source diagram focus exceeds 6.4 seconds')
                    self.bound(part['image'])
                    if kind=='diagram' and part.get('live_result_depicted') is not False:
                        raise ValueError('Source diagram cannot assert a live result')
                    if kind=='native-readback':
                        receipt=read(self.bound(part['native_card_receipt']))
                        if receipt.get('schema')!='ck3-faith-power-native-readback-card-v1' or receipt['image']!=part['image']:
                            raise ValueError('Native graphic needs its actual direct-data render receipt')
                        if receipt.get('machine_id')!=doc['machine_id']:
                            raise ValueError('Native graphic crossed machine')
                        for item in receipt['rows']:
                            actual=pointer(read(self.bound(item['file'])),item['json_pointer'])
                            if actual!=item['observed_value']:
                                raise ValueError('Native graphic value differs from actual receipt')
                elif kind=='raw':
                    raw=self.bound(part['raw']); audit=read(self.bound(part['raw_audit']))
                    if audit['machine_id']!=doc['machine_id'] or audit['raw']!=part['raw'] or audit['full_decode_exit_code']!=0:
                        raise ValueError('Raw/audit/machine binding differs')
                    start=part['raw_start_seconds']; end=start+duration
                    if start<0 or end>audit['pts']['last_pts']+1/30+1e-6:
                        raise ValueError('Raw selection exceeds actually decoded source')
                    if audit['capture_was_aborted'] and part.get('original_RED_disclosed') is not True:
                        raise ValueError('Interrupted source must retain explicit RED disclosure')
                    self.bound(part['source_index'])
                    frames=read(self.bound(part['source_frame_pts']))['frames']
                    pts=[float(f['best_effort_timestamp_time']) for f in frames]
                    chosen=[(i,t) for i,t in enumerate(pts) if start<=t<end]
                    if not chosen:raise ValueError('Raw selection contains no actually decoded source frames')
                    part['selected_source_frame_indices_exclusive']=[chosen[0][0],chosen[-1][0]+1]
                    part['actual_selected_source_first_pts']=chosen[0][1]
                    part['actual_selected_source_last_pts']=chosen[-1][1]
                    part['actual_selected_source_frame_count']=len(chosen)
                    part['source_timing']='VFR retained; explicit nearest-frame conversion to 30fps; held frames are not new game time'
                    intervals.setdefault(part['raw']['sha256'],[]).append((start,end,row['id']))
                else:raise ValueError('Only actual raw or source mechanism diagrams are supported')
        for spans in intervals.values():
            spans.sort()
            if any(b[0]<a[1]-1e-7 for a,b in zip(spans,spans[1:])):
                raise ValueError('A raw interval would repeat or loop')
        total=sum(r['duration_seconds'] for r in ordered)
        if scope=='episode01-full-review' and total<1200:
            self.errors.append('Full episode must contain at least 20 authored minutes')
        if scope=='episode01-adoption-review-segment' and not 180<=total<=300:
            self.errors.append('Adoption review segment must measure 180–300 authored seconds')
        profile=render_profile(doc,self.bound)
        music=background_music(doc,self.bound)
        if profile!=DEFAULT_PROFILE and music is None:self.errors.append('background_music: exact repository theme unbound')
        budget=peak_budget(total,len(ordered),profile=profile)
        return {'rows':ordered,'seconds':total,'gaps':self.errors,
            'ready_to_build':not self.errors,'budget':budget,'background_music':music,
            'focus_geometry_checks':focus_checks,'existing_measured_audio_inventory_count':158,'existing_audio_selected_count':len(doc['cues']),
            'scope':scope,'new_TTS_requested':False,
            'result_slots':slots,'native_business_verified':False,'human_1x_signoff':False}


def bounded(plan, seconds, *, audio):
    """Existing render-planner seam: explicit VBV and per-file output cap."""
    commands=[]
    for item in plan.commands:
        argv=list(item.spec.argv)
        argv[-1:-1]=['-maxrate',str(VIDEO_RATE),'-bufsize',str(BUFFER_BITS),
            '-threads','2','-fs',str(media_limit(seconds,audio=audio))]
        commands.append(replace(item,spec=replace(item.spec,argv=tuple(argv))))
    return replace(plan,commands=tuple(commands))


def subtitle_groups(row):
    """One timing contract for burned ASS and final-PTS companion SRT."""
    speech=float(row['speech_duration_seconds'])
    onset=float(row.get('subtitle_start_seconds',0))
    if not math.isfinite(speech) or not 0<=onset<speech:
        raise ValueError('Subtitle onset must precede the unchanged measured speech end')
    groups=row.get('subtitle_groups')
    if groups is None:
        return [{'start_seconds':onset,'end_seconds':speech,'zh':row['zh'],'en':row['en']}]
    if not isinstance(groups,list) or not groups:
        raise ValueError('Explicit subtitle groups must be nonempty')
    previous=onset
    for group in groups:
        start,end=float(group['start_seconds']),float(group['end_seconds'])
        if (not math.isfinite(start) or not math.isfinite(end)
            or not previous<=start<end<=speech):
            raise ValueError('Subtitle groups need positive ordered intervals within measured speech')
        if any(not isinstance(group.get(lang),str) or not group[lang].strip() for lang in ('zh','en')):
            raise ValueError('Every subtitle group needs both unchanged text fragments')
        previous=end
    if any(''.join(group[lang] for group in groups)!=row[lang] for lang in ('zh','en')):
        raise ValueError('Subtitle groups must exactly concatenate to the original zh/en text')
    return groups


def explicit_project_config(config, rows, *, profile=DEFAULT_PROFILE):
    """Validate real native project cues without result-independent authoring flags."""
    from xar_promo.model import ProjectConfig
    ProjectConfig.from_mapping(config)
    if profile!=DEFAULT_PROFILE:
        limit=config.get('constraints',{}).get('duration_limit_seconds')
        if (not isinstance(limit,(int,float)) or isinstance(limit,bool)
            or not sum(row['duration_seconds'] for row in rows)<=limit<=profile.max_seconds):
            raise ValueError('Explicit extended profile needs an actual native project limit covering the selected clock')
    cues=[cue for chapter in config['chapters'] for cue in chapter['cues']]
    if [cue['id'] for cue in cues]!=[row['id'] for row in rows]:
        raise ValueError('ProjectConfig must contain the exact selected cue sequence')
    for cue,row in zip(cues,rows):
        if (cue['narration'].get('zh-CN')!=row['zh']
            or cue['subtitles'].get('zh-CN')!=row['zh'] or cue['subtitles'].get('en')!=row['en']):
            raise ValueError('ProjectConfig narration/subtitles differ from measured selected voices')
    return config


def subtitle(row,font_path,font_name):
    tracks=[]; cues=[]
    groups=subtitle_groups(row)
    for language,size,margin,height,top in (('zh',49,178,60,1120),('en',31,65,38,1280)):
        face=ImageFont.truetype(str(font_path),size)
        style=AssStyleConfig(language,font_name,size,primary_colour='&H00CFE5F0',outline_colour='&H00131821',
            outline=2,shadow=1,bold=True,margin_left=145,margin_right=145,margin_vertical=margin)
        tracks.append(SubtitleTrackConfig(language,'zh-CN' if language=='zh' else 'en',2 if language=='zh' else 1,style))
        for index,group in enumerate(groups):
            layout=wrap_text(group[language],font=FontSpec(language,font_name,size),
                measure=lambda text,chosen:face.getlength(text),max_width=2270,max_lines=2,policy=WrapPolicy())
            if 1440-margin-height*len(layout.lines)<top:raise ValueError('Subtitle safety rectangle exceeded')
            identifier=row['id']+'.'+language+('.g'+str(index) if row.get('subtitle_groups') is not None else '')
            cues.append(AssCue(identifier,language,float(group['start_seconds']),float(group['end_seconds']),'\n'.join(layout.lines)))
    style=AssStyleConfig('source',font_name,28,primary_colour='&H006AA5CB',outline=2,alignment=8,
        margin_left=100,margin_right=100,margin_vertical=30)
    tracks.append(SubtitleTrackConfig('source','zh-CN',3,style)); cursor=0
    for number,part in enumerate(row['visual_parts']):
        if (part['kind']!='mechanism-motion' and not
            (part['kind'] in {'diagram','native-readback'} and part.get('burned_in_disclosure') and 'focus_rect' not in part)):
            # Explicit graphic receipt validation happens before build; raw gameplay keeps its label.
            cues.append(AssCue(row['id']+'.source'+str(number),'source',cursor,cursor+part['duration_seconds'],part['disclosure']))
        cursor+=part['duration_seconds']
    return render_ass_document(AssDocumentConfig('Faith and Power: review',2560,1440,row['duration_seconds']),
        tracks,cues,available_font_names=[font_name])


def visual_command(ffmpeg,row,target,bound):
    argv=[str(ffmpeg),'-nostdin','-n','-hide_banner','-loglevel','error','-threads','2','-filter_complex_threads','2']
    filters=[]
    for i,part in enumerate(row['visual_parts']):
        d=part['duration_seconds']
        if part['kind'] in {'diagram','native-readback'}:
            argv+=['-loop','1','-framerate','30','-t',f'{d:.9f}','-i',str(bound(part['image']))]
            scale=focus_filter(part,bound)
        elif part['kind']=='mechanism-motion':
            argv+=['-ss',f"{part['source_start_seconds']:.9f}",'-t',f'{d:.9f}','-i',str(bound(part['video']))]
            scale='scale=2560:1440:flags=lanczos'
        else:
            argv+=['-ss',f"{part['raw_start_seconds']:.9f}",'-t',f'{d:.9f}','-i',str(bound(part['raw']))]
            scale='scale=2560:1120:force_original_aspect_ratio=decrease:flags=lanczos,pad=2560:1440:(ow-iw)/2:0:color=0x211813'
        filters.append(f'[{i}:v]setpts=PTS-STARTPTS,{scale},setsar=1,fps=30:round=near,trim=duration={d:.9f},setpts=PTS-STARTPTS[v{i}]')
    filters.append(''.join(f'[v{i}]' for i in range(len(row['visual_parts'])))+f"concat=n={len(row['visual_parts'])}:v=1:a=0[out]")
    argv+=['-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-preset','veryfast','-crf','21',
        '-maxrate',str(VIDEO_RATE),'-bufsize',str(BUFFER_BITS),'-threads','2','-pix_fmt','yuv420p',
        '-t',f"{row['duration_seconds']:.9f}",'-fs',str(media_limit(row['duration_seconds'],audio=False)),str(target)]
    return argv


def pointer(value,path):
    if not isinstance(path,str) or (path and not path.startswith('/')):
        raise ValueError('Native JSON pointer required')
    for component in path.split('/')[1:]:
        component=component.replace('~1','/').replace('~0','~')
        value=value[int(component)] if isinstance(value,list) else value[component]
    return value


def direct_register(run_path,files):
    """Register actual files beneath the run, without byte copies or hardlinks."""
    loaded=load_document(run_path,check_files=True); old=loaded.run
    if old is None:raise ValueError('Native run required')
    added=[]
    for identifier,role,path,media_type in files:
        path=Path(path).resolve(); relative=path.relative_to(Path(run_path).parent.resolve())
        actual=pin(path)
        added.append(SourceRecord.from_mapping({'id':identifier,'collection':'derived','role':role,
            'path':relative.as_posix(),'label':path.name,'bytes':actual['bytes'],
            'sha256':actual['sha256'],'media_type':media_type,'source_name':path.name},'direct artifact'))
    if {r.artifact_id for r in added}&{r.artifact_id for r in old.artifacts}:raise ValueError('Direct artifact ID replay')
    updated=RunManifest(old.run_id,old.project_config,old.artifact_policy,old.phase_history,
        old.artifacts+tuple(added),old.audits,old.signoffs)
    RunManifest.from_mapping(updated.to_dict()); _replace_run(Path(run_path),old,updated)
    load_document(run_path,check_files=True)


def run_process(argv,audit,label):
    from xar_promo.process import CommandSpec, run_command
    return run_command(CommandSpec.create(argv,label=label),audit_directory=audit)


def media_duration(ffprobe,path,audit):
    result=run_process([str(ffprobe),'-v','error','-show_streams','-show_format','-of','json',str(path)],audit,'probe rendered duration')
    return json.loads(result.stdout)


def available_memory():
    if os.name=='nt':
        import ctypes
        class Status(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(key,ctypes.c_ulonglong) for key in
                ('total_physical','available_physical','total_page','available_page','total_virtual','available_virtual','extended')]
        value=Status();value.length=ctypes.sizeof(value)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):raise OSError('Fresh memory observation failed')
        return value.available_physical
    return os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')


def companion_text(rows,mapping,directory):
    """External subtitles use measured final video PTS, including mux start offset."""
    directory=Path(directory);directory.mkdir(exist_ok=False)
    def stamp(value):
        value=round(value*1000)
        return f'{value//3600000:02}:{value//60000%60:02}:{value//1000%60:02},{value%1000:03}'
    paths=[]
    for language in ('zh','en','bilingual'):
        lines=[];number=0
        for row,item in zip(rows,mapping):
            start=item['actual_final_first_pts']
            for group in subtitle_groups(row):
                number+=1
                body=group['zh']+'\n'+group['en'] if language=='bilingual' else group[language]
                lines.extend([str(number),stamp(start+float(group['start_seconds']))+' --> '+stamp(start+float(group['end_seconds'])),body,''])
        paths.append(write_text(directory/('episode01.'+language+'.srt'),'\n'.join(lines)))
    lines=['# Faith and Power: review narration','','Source and live result disclosures are preserved in the input catalog and burned-in source labels.','']
    for row,item in zip(rows,mapping):
        lines.extend([stamp(item['actual_final_first_pts'])+'  '+row['zh'],row['en'],''])
    paths.append(write_text(directory/'episode01-script.md','\n'.join(lines)))
    return paths


def theme_concat(plan, music, duration, final_cap):
    """One concat/mix: copy video, encode the final AAC once, no dry full-film copy."""
    if len(plan.commands)!=1 or len(plan.generated_files)!=1:raise ValueError('Expected the existing single concat command')
    spec=AudioMixSpec(stems=(AudioStem('narration',plan.generated_files[0].path,gain_db=0),
        AudioStem('series-theme',Path(music['file']['path']),gain_db=-17,fade_in_seconds=2,fade_out_seconds=8)),
        duration_seconds=duration,sample_rate=48000,channels=2,normalize=False,
        metadata={'ducking':False,'continuous_same_theme_loop':True,'narration_gain_db':0,'music_gain_db':-17})
    mix=plan_audio_mix(spec,output_label='faith_theme_mix')
    item=plan.commands[0]
    argv=(item.spec.argv[0],'-nostdin','-hide_banner','-loglevel','error','-n','-threads','2','-filter_complex_threads','2',
        '-f','concat','-safe','0','-i',str(plan.generated_files[0].path),'-stream_loop','-1','-i',music['file']['path'],
        '-filter_complex',mix.filtergraph,'-map','0:v:0','-map','[faith_theme_mix]',
        '-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',
        '-movflags','+faststart','-t',f'{duration:.9f}','-fs',str(final_cap),str(plan.partial_output))
    return replace(plan,commands=(replace(item,spec=replace(item.spec,argv=argv)),)),mix


def seekable_dry_manifest(content, durations):
    """Actual probed segment durations permit input seeking for short audio proof windows."""
    lines=[];index=0
    for line in content.splitlines():
        lines.append(line)
        if line.startswith('file '):
            duration=durations[index]
            if not math.isfinite(duration) or duration<=0:raise ValueError('Invalid actual segment duration')
            lines.append(f'duration {duration:.9f}');index+=1
    if index!=len(durations):raise ValueError('Dry proof manifest duration count differs')
    return '\n'.join(lines)+'\n'


def music_window_metrics(actual, dry, expected):
    import numpy as np
    residual=np.asarray(actual,dtype=np.float64)-dry
    target=np.asarray(expected,dtype=np.float64)
    music_rms=float(np.sqrt(np.mean(target*target)))
    error=float(np.sqrt(np.mean((residual-target)**2)))
    gain=float(np.dot(residual,target)/max(float(np.dot(target,target)),1e-30))
    a=residual-float(np.mean(residual));b=target-float(np.mean(target))
    correlation=float(np.dot(a,b)/max(float(np.sqrt(np.dot(a,a)*np.dot(b,b))),1e-30))
    passed=music_rms>1e-6 and correlation>.90 and .85<gain<1.15 and error/music_rms<.5
    return {'music_rms':music_rms,'residual_music_correlation':correlation,'expected_music_gain':gain,
        'residual_error_ratio':error/max(music_rms,1e-30),'passed':passed}


def fixed_music_lag(actual, expected, pad, *, max_lag=240):
    import numpy as np
    errors=[float(np.mean((actual[pad+lag:pad+lag+len(expected)]-expected)**2)) for lag in range(-max_lag,max_lag+1)]
    lag=int(np.argmin(errors))-max_lag
    if abs(lag)==max_lag:raise ValueError('Music proof calibration reaches fixed lag boundary; do not widen or refit')
    return lag


def music_presence(ffmpeg, final_ref, dry_manifest, music, source_duration, duration, directory, machine):
    """At most five 4s windows; final AAC minus independently decoded dry narration.

    Only 8k mono float PCM pipes in RAM. One calibration lag is fixed for every
    window. No whole-film extra audio decode, WAV, AAC scratch, or per-window fit.
    """
    import numpy as np
    if duration<12:raise ValueError('Music proof needs a timeline of at least12 seconds')
    audit=Path(directory)/'audit/music-windows';audit.mkdir(parents=True,exist_ok=False)
    rate=8000;length=4.;padding=.04;pad=round(padding*rate)
    points=sorted({round(min(max(.5,t),duration-length-.1),6) for t in (.5,min(30,duration/4),duration/2,duration*.75,duration-6)})
    calibration=points[1]
    def decode(label,path,start,seconds,*,concat=False,loop=False):
        argv=[str(ffmpeg),'-nostdin','-hide_banner','-v','error','-threads','2']
        if loop:argv+=['-stream_loop','-1']
        argv+=['-ss',f'{start:.9f}']
        if concat:argv+=['-f','concat','-safe','0']
        argv+=['-i',str(path),'-map','0:a:0','-vn','-t',f'{seconds:.9f}',
            '-ar',str(rate),'-ac','1','-c:a','pcm_f32le','-f','f32le','pipe:1']
        result=subprocess.run(argv,capture_output=True,timeout=30)
        cap=(math.ceil(seconds*rate)+1024)*4
        info={'machine_id':machine,'observed_at_utc':now(),'argv':argv,'returncode':result.returncode,
            'PCM_bytes_in_RAM':len(result.stdout),'PCM_sha256':hashlib.sha256(result.stdout).hexdigest(),
            'PCM_persisted':False,'stderr':result.stderr[:16384].decode('utf-8','replace')}
        write(audit/(label+'.json'),info)
        if result.returncode or len(result.stdout)>cap or len(result.stderr)>16384 or len(result.stdout)%4:
            raise ValueError('Bounded audio proof decode failed; diagnostics retained')
        return np.frombuffer(result.stdout,dtype='<f4').astype(np.float64)
    def window(index,start):
        final=decode(f'{index}-final',final_ref['path'],start-padding,length+2*padding)
        dry=decode(f'{index}-dry',dry_manifest,start,length,concat=True)
        original=decode(f'{index}-theme',music['file']['path'],start%source_duration,length,loop=True)
        n=round(length*rate)
        if len(final)<n+2*pad or len(dry)<n or len(original)<n:raise ValueError('Short decoded music-proof window')
        times=start+np.arange(n)/rate
        fade=np.minimum(np.clip(times/2,0,1),np.clip((duration-times)/8,0,1))
        expected=original[:n]*(10**(-17/20))*fade
        return final,dry[:n],expected
    calibration_index=points.index(calibration)
    calibrated=window(calibration_index,calibration)
    lag=fixed_music_lag(calibrated[0],calibrated[1]+calibrated[2],pad)
    rows=[]
    for i,start in enumerate(points):
        actual,dry,expected=calibrated if i==calibration_index else window(i,start)
        metrics=music_window_metrics(actual[pad+lag:pad+lag+len(dry)],dry,expected)
        rows.append({'start_seconds':start,'duration_seconds':length,**metrics})
    report={'machine_id':machine,'observed_at_utc':now(),'evidence_source':'Actual final AAC minus independent seeked dry segment-concat decode, compared with exact theme loop/gain/fades; bounded PCM in RAM only',
        'final':final_ref,'music':music,'dry_manifest':pin(dry_manifest),'global_lag_samples_at_8000Hz':lag,
        'lag_calibrated_once_at_seconds':calibration,'lag_search_limit_samples':240,'per_window_refitting':False,
        'thresholds':{'correlation_above':.90,'gain_open_interval':[.85,1.15],'error_RMS_over_music_RMS_below':.5,'music_RMS_above':1e-6},
        'windows':rows,'passed':all(r['passed'] for r in rows),'whole_film_extra_audio_decode':False,
        'PCM_WAV_AAC_scratch_files':0,'estimated_peak_RAM_bytes':8*1024**2,'human_listening_performed':False}
    path=write(Path(directory)/'music-presence.json',report)
    if not report['passed']:raise ValueError('Actual final AAC music presence failed; no automatic retry or relaxed thresholds')
    return path


def build(args,doc,inspection,inputs,admission):
    if not inspection['ready_to_build']:raise ValueError('Full build refused: '+ '; '.join(inspection['gaps']))
    profile=render_profile(doc,inputs.bound)
    music=background_music(doc,inputs.bound,repo=args.repo)
    if profile!=DEFAULT_PROFILE and (music is None or doc.get('project_config') is None):
        raise ValueError('Explicit extended profile requires exact music and actual selected ProjectConfig')
    out=Path(args.output).resolve(); out.mkdir(parents=True,exist_ok=False)
    write(out/'storage-admission.json',admission)
    runtime=read(args.runtime)
    fresh=fresh_runtime(args.repo,runtime,out)
    ffmpeg=inputs.bound(runtime['ffmpeg']); ffprobe=inputs.bound(runtime['ffprobe'])
    font=inputs.bound(runtime['subtitle_font']['file']); family=runtime['subtitle_font']['family']
    if ImageFont.truetype(str(font),49).getname()[0]!=family:raise ValueError('Actual subtitle font family differs')
    if doc.get('project_config') is not None:
        config=explicit_project_config(read(inputs.bound(doc['project_config'])),inspection['rows'],profile=profile)
    else:
        assembly=read(inputs.bound(doc['assembly_plan']))
        config=project(read(inputs.bound(assembly['inputs']['script'])))
    cfg=write(out/'promo-project.json',config)
    run=start_run(cfg,run_id=out.name,run_directory=out/'native-run')
    preserve_artifact(run,Path(args.input),artifact_id='full-edit-input',collection='raw',role='explicit-external-SHA-input-catalog',label=None,media_type='application/json')
    for source,identifier in ((Path(__file__),'full-review-producer'),(Path(__file__).with_name('full_diagrams.py'),'native-graphic-producer'),
            (out/'fresh-runtime.json','fresh-runtime'),(out/'storage-admission.json','storage-admission')):
        preserve_artifact(run,source,artifact_id=identifier,collection='raw',role='producer-or-runtime-input',label=None,media_type='application/json' if source.suffix=='.json' else 'text/x-python')
    media=run.parent/'derived/direct'; media.mkdir(parents=True,exist_ok=False)
    records=[]; segment_paths=[]; mapping=[]; cursor=0
    planner=font_render_planner(font.parent)
    try:
        def render_one(row):
            key=row['id']; d=row['duration_seconds']
            audio=inputs.bound(row['audio'])
            spoken=media_duration(ffprobe,audio,out/'audit/audio'/key)
            if abs(float(spoken['format']['duration'])-row['speech_duration_seconds'])>.025:
                raise ValueError('Actual existing narration duration differs')
            visual=media/(key+'.visual.mp4')
            run_process(visual_command(ffmpeg,row,visual,inputs.bound),out/'audit/visual'/key,'prepare disjoint real/diagram visual')
            probed=media_duration(ffprobe,visual,out/'audit/visual-probe'/key)
            if abs(float(probed['format']['duration'])-d)>.04:raise ValueError('Prepared visual truncated or exceeded its clock')
            ass=write_text(media/(key+'.ass'),subtitle(row,font,family))
            target=media/(key+'.mp4')
            plan=planner(ffmpeg=ffmpeg,video_input=visual,audio_input=audio,
                partial_output=media/(key+'.partial.mp4'),final_output=target,audit_directory=out/'audit/segment'/key,
                options=RenderOptions(2560,1440,30,d,preset='veryfast',crf=21),ass_path=ass)
            execute_render_plan(bounded(plan,d,audio=True))
            probe=media_duration(ffprobe,target,out/'audit/segment-probe'/key)
            if abs(float(probe['format']['duration'])-d)>.04:raise ValueError('Narrated segment truncated or exceeded its clock')
            return row,target,[(key+'.visual','prepared-visual',visual,'video/mp4'),(key+'.subtitle','subtitle',ass,'text/x-ass'),
                (key+'.segment','rendered-segment',target,'video/mp4')],float(probe['format']['duration'])
        workers=args.workers
        if workers==2 and (os.cpu_count() or 1)<4:raise ValueError('Two encoders require at least four logical CPUs')
        memory=available_memory()
        if workers==2 and memory<4*1024**3:raise ValueError('Two encoders require at least 4GiB fresh available physical RAM')
        write(out/'encode-scheduling.json',{'machine_id':doc['machine_id'],'observed_at_utc':now(),
            'evidence_source':'fresh os.cpu_count and explicit bounded encoder concurrency',
            'logical_cpu_count':os.cpu_count(),'available_physical_memory_bytes':memory,'parallel_segments':workers,'encoder_threads_per_process':2,
            'shared_total_peak_bytes':inspection['budget']['peak_new_bytes'],'automatic_retry':False})
        with ThreadPoolExecutor(max_workers=workers) as pool:
            rendered=list(pool.map(render_one,inspection['rows']))
        segment_durations=[]
        for row,target,files,actual_segment_duration in rendered:
            key=row['id'];d=row['duration_seconds'];records.extend(files)
            segment_paths.append(target)
            segment_durations.append(actual_segment_duration)
            mapping.append({'id':key,'claim_ids':row['claim_ids'],'shot_ids':row['shot_ids'],
                'audio':row['audio'],'raw_or_diagram_parts':row['visual_parts'],
                'subtitle_groups':subtitle_groups(row),'editor_annotations':row.get('editor_annotations'),
                'actual_final_frame_indices_exclusive':[round(cursor*30),round((cursor+d)*30)],
                'authored_final_interval_seconds':[cursor,cursor+d],'human_1x_review_performed':False})
            cursor+=d
        final=media/'episode01-review.mp4'
        plan=plan_concat(ffmpeg=ffmpeg,segment_paths=segment_paths,concat_path=media/'episode01.ffconcat',
            partial_output=media/'episode01-review.partial.mp4',final_output=final,audit_directory=out/'audit/concat')
        if music is not None:
            source_probe=media_duration(ffprobe,inputs.bound(music['file']),out/'audit/music-source-probe')
            source_audio=[s for s in source_probe['streams'] if s['codec_type']=='audio']
            if (len(source_audio)!=1 or source_audio[0]['sample_rate']!='48000' or source_audio[0]['channels']!=2
                or any(s['codec_type']=='video' for s in source_probe['streams'])):raise ValueError('Actual theme must be48kHz stereo audio only')
            dry_manifest=write_text(media/'music-proof-dry.ffconcat',seekable_dry_manifest(plan.generated_files[0].content,segment_durations))
            plan,mix=theme_concat(plan,music,cursor,inspection['budget']['concat_deliverable_bytes'])
            write(out/'theme-mix-plan.json',{'machine_id':doc['machine_id'],'observed_at_utc':now(),'music':music,
                'mix':mix.to_mapping(),'argv':list(plan.commands[0].spec.argv),'source_asset_copied':False,
                'video_stream_copy':True,'final_AAC_encoded_once':True,'additional_full_film_or_AAC_scratch_bytes':0})
        else:
            # Legacy concat remains a pure stream-copy with the original final-size cap.
            commands=[]
            for item in plan.commands:
                argv=list(item.spec.argv);argv[-1:-1]=['-fs',str(inspection['budget']['concat_deliverable_bytes'])]
                commands.append(replace(item,spec=replace(item.spec,argv=tuple(argv))))
            plan=replace(plan,commands=tuple(commands))
        execute_render_plan(plan)
        decoded=run_process([str(ffmpeg),'-nostdin','-v','error','-xerror','-err_detect','explode','-threads','2','-i',str(final),
            '-map','0:v:0','-map','0:a:0','-f','null','-'],out/'audit/full-decode','full review video/audio decode')
        if decoded.stderr.strip():raise ValueError('Final strict decoder emitted diagnostics')
        probe=media_duration(ffprobe,final,out/'audit/final-probe')
        if abs(float(probe['format']['duration'])-cursor)>.04:raise ValueError('Final concatenation duration differs')
        video=next(s for s in probe['streams'] if s['codec_type']=='video')
        audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        if (video['width'],video['height'],audio['sample_rate'],audio['channels'])!=(2560,1440,'48000',2):
            raise ValueError('Final actual AV geometry differs')
        if music is not None and (video['codec_name']!='h264' or audio['codec_name']!='aac'):
            raise ValueError('Mixed final must retain H264 video and actual AAC audio')
        pts_result=run_process([str(ffprobe),'-v','error','-select_streams','v:0','-show_entries',
            'frame=best_effort_timestamp_time','-of','json',str(final)],out/'audit/final-pts','all actual final frame PTS')
        pts=[float(f['best_effort_timestamp_time']) for f in json.loads(pts_result.stdout)['frames']]
        if len(pts)!=round(cursor*30) or any(abs(b-a-1/30)>.00001 for a,b in zip(pts,pts[1:])):
            raise ValueError('Final CFR frame count/cadence differs')
        for row in mapping:
            low,high=row['actual_final_frame_indices_exclusive']
            row['actual_final_first_pts']=pts[low];row['actual_final_last_pts']=pts[high-1]
            row['actual_final_end_pts_exclusive']=pts[high-1]+1/30
            part_cursor=low
            for part in row['raw_or_diagram_parts']:
                stop=part_cursor+round(part['duration_seconds']*30)
                part['actual_final_frame_indices_exclusive']=[part_cursor,stop]
                part['actual_final_first_pts']=pts[part_cursor]
                part['actual_final_last_pts']=pts[stop-1]
                part['actual_final_end_pts_exclusive']=pts[stop-1]+1/30
                part_cursor=stop
            if part_cursor!=high:raise ValueError('Part mapping does not cover actual final cue frames')
        map_path=write(out/'raw-to-final-map.json',{'machine_id':doc['machine_id'],'observed_at_utc':now(),
            'evidence_source':'actual final decode/probe/every frame PTS plus immutable input catalog',
            'final':pin(final),'entries':mapping,'human_full_1x_review_performed':False,
            'human_listening_performed':False,'clean_span_certified':False,'native_business_verified':False})
        text_paths=companion_text(inspection['rows'],mapping,media/'text')
        for path in text_paths:records.append(('text.'+path.stem,'subtitle-or-script',path,'text/plain'))
        volume=run_process([str(ffmpeg),'-nostdin','-v','info','-i',str(final),'-vn','-af','volumedetect','-f','null','-'],
            out/'audit/audio-signal','actual final audio signal check')
        mean=re.search(r'mean_volume: ([\-0-9.]+) dB',volume.stderr)
        maximum=re.search(r'max_volume: ([\-0-9.]+) dB',volume.stderr)
        if not mean or not maximum or float(maximum[1])<-60:raise ValueError('Final narration signal missing or effectively silent')
        music_proof=None
        if music is not None:
            music_proof=music_presence(ffmpeg,read(map_path)['final'],dry_manifest,music,
                float(source_probe['format']['duration']),cursor,out,doc['machine_id'])
        records.extend([('episode01.review','deliverable',final,'video/mp4')])
        direct_register(run,records)
        from xar_promo.runlog import append_phase_record
        append_phase_record(run,phase_id='full-review.direct-output',status='succeeded',
            artifact_ids=['episode01.review'],detail='Actual bounded encode and strict AV/PTS checks; human review pending; no business qualification awarded')
        write(out/'completed-review.json',{'machine_id':doc['machine_id'],'observed_at_utc':now(),
            'status':'ENCODED_REVIEW_PENDING','scope':doc['scope'],'final':pin(final),'map':pin(map_path),'native_run':pin(run),
            'actual_new_bytes':package_bytes(out),'budget':inspection['budget'],
            'text':[pin(path) for path in text_paths],
            'audio_signal':{'mean_volume_db':float(mean[1]),'max_volume_db':float(maximum[1]),'human_listening_performed':False},
            'background_music':music,'actual_music_presence':pin(music_proof) if music_proof else None,'strict_AV_full_decode_exit_code':0,
            'media_CAS_copies':0,'human_signoff_recorded':False})
        return {'final':pin(final),'map':pin(map_path),'run':pin(run),'signoff':'pending'}
    except Exception as error:
        write(out/'failure.json',{'machine_id':doc['machine_id'],'observed_at_utc':now(),
            'evidence_source':'actual failed single render attempt; outputs and partials retained',
            'error':repr(error),'automatic_retry_performed':False,'actual_new_bytes':package_bytes(out)})
        raise


def write_text(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:stream.write(value)
    return Path(path)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('plan','build'))
    parser.add_argument('--workers',type=int,choices=(1,2),default=2)
    for name in ('repo','input','runtime','reservation','package-root','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    doc=read(args.input); inputs=Inputs(doc); inspection=inputs.inspect()
    machine=subprocess.check_output([sys.executable,'-B',args.repo/'tools/ck3_live_run_id.py','machine'],text=True).strip()
    if machine!=doc['machine_id']:raise ValueError('Full edit belongs to another machine')
    admitted=admit_v2(args.repo,args.reservation,args.package_root,args.output,machine,inspection['budget']['peak_new_bytes'])
    if args.operation=='plan':
        out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
        report={k:v for k,v in inspection.items() if k!='rows'}
        report.update({'machine_id':machine,'observed_at_utc':now(),'evidence_source':'actual unchanged cue/audio SHA checks and bounded full-edit contract inspection',
            'inputs':pin(args.input),'storage_admission':admitted,'media_write_started':False})
        path=write(out/'full-build-plan.json',report)
        print(json.dumps({'plan':pin(path),'ready_to_build':inspection['ready_to_build'],'gaps':inspection['gaps'],
            'peak_new_bytes':inspection['budget']['peak_new_bytes']},ensure_ascii=False));return 0
    result=build(args,doc,inspection,inputs,admitted)
    print(json.dumps(result,ensure_ascii=False));return 0


if __name__=='__main__':raise SystemExit(main())
