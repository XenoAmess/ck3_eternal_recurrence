"""Review02 method-preview followup: reuse 66 exact encodes and render 3 corrections.

This project composer is deliberately machine-bound to the sealed a02 source run.
The public xar-promo plan/build CLI remains the orchestration and media engine.
"""
from dataclasses import replace
from pathlib import Path
import hashlib
import json
import os
import sys

from PIL import Image
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import CommandSpec, run_command
from xar_promo.render import PlannedCommand, RenderOptions, RenderPlan, plan_render
from xar_promo.sources import STILL, VIDEO, VisualProbeResult, VisualSource
from tools.ck3_live_run_id import current_machine_id
from war_ai_promo.composer import artifact

INDEX_ID = 'source-typography-reuse-index'
FIX = {'C05-09', 'C05-10', 'C05-14'}
LINES = {
 'C05-09': 'Dialogue: 10,0:00:04.80,0:00:10.60,Chinese,explicit-correction,0,0,0,,{\\an7\\pos(64,1160)\\fs40\\b1\\bord2}纠错：1/1 只是记录界面显示值，不代表实体兵槽人数。',
 'C05-10': 'Dialogue: 10,0:00:00.00,9:59:59.99,Chinese,visual-scope,0,0,0,,{\\an7\\pos(64,1160)\\fs40\\b1\\bord2}方法示意：途中会合及合并按钮瞬间未拍到；R194 同地拆合后读回见 C05-06。',
 'C05-14': 'Dialogue: 10,0:00:09.00,0:00:14.50,Chinese,explicit-correction,0,0,0,,{\\an7\\pos(64,1160)\\fs40\\b1\\bord2}纠错：新增一人仅指新增 1/1 角色记录；本场实体兵员未增加。',
}
OLD_C0510_REVIEW = r'{\an7\pos(48,48)\fs36}PARTIAL METHOD REVIEW'
NEW_C0510_REVIEW = r'{\an7\pos(48,94)\fs26}PARTIAL METHOD REVIEW'

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    digest=hashlib.sha256();total=0
    with Path(path).open('rb') as src:
        for block in iter(lambda:src.read(1024*1024),b''):
            digest.update(block);total+=len(block)
    return total,digest.hexdigest()

def resolve_ref(source_run, ref):
    run_dir=source_run.parent.resolve()
    path=(run_dir/ref['path_relative_to_source_run']).resolve()
    need(path.is_relative_to(run_dir), 'source CAS path escaped sealed a02 run')
    need(path.is_file() and path.stat().st_size==ref['bytes'], 'source CAS length differs: '+ref['artifact_id'])
    need(sha(path)==(ref['bytes'],ref['sha256'].lower()), 'source CAS hash differs: '+ref['artifact_id'])
    return path

def replace_correction(cue, old):
    if cue not in FIX:
        return old
    role='explicit-correction' if cue!='C05-10' else 'visual-scope'
    lines=old.splitlines(keepends=True)
    selected=[i for i,line in enumerate(lines) if line.startswith('Dialogue: 10,') and ',Chinese,'+role+',' in line]
    need(len(selected)==1, 'expected one old correction line in '+cue)
    previous=lines[selected[0]]
    need('\\pos(48,110)\\fs34' in previous, 'old typography no longer matches sealed a02 source')
    lines[selected[0]]=LINES[cue]+('\n' if previous.endswith('\n') else '')
    result=''.join(lines)
    if cue=='C05-10':
        need(result.count(OLD_C0510_REVIEW)==1, 'C05-10 generic review label changed')
        result=result.replace(OLD_C0510_REVIEW,NEW_C0510_REVIEW)
    return result

def compose(config, run, *, config_path, run_path, workdir, adapter_factory, preset_factory, validate_only):
    del config_path
    need(adapter_factory()['id']==config.adapter and preset_factory()['id']==config.preset, 'wrong project components')
    if run is None:
        need(validate_only, 'build requires native run with preserved source index')
        named=os.environ.get('XAR_E04_REUSE_INDEX')
        need(named, 'read-only config plan requires explicit source index')
        index_path=Path(named)
    else:
        index_path=artifact(run,run_path,INDEX_ID)
    index=json.loads(index_path.read_text(encoding='utf-8-sig'))
    need(index.get('schema')=='xar.e04.review02-full69-focused-typography-source-index.v1', 'wrong reuse index schema')
    need(isinstance(index.get('machine_id'),str) and bool(index['machine_id']), 'reuse index lacks machine identity')
    need(current_machine_id()==index['machine_id'], 'current machine differs from sealed source machine')
    need(index.get('unchanged_segment_reuse_count')==66 and index.get('new_render_count')==3 and index.get('total_frames')==58406, 'reuse scope changed')
    need(set(index.get('candidate_corrections',[]))==FIX, 'correction cue set differs')
    source=index['source_run_manifest']
    source_run=Path(source['path']).resolve()
    need(source_run.is_file() and sha(source_run)==(source['bytes'],source['sha256']), 'sealed a02 manifest changed')
    source_manifest=json.loads(source_run.read_text(encoding='utf-8'))
    need(len(source_manifest.get('artifacts',[]))==463, 'sealed a02 artifact count changed')
    by_artifact={r['id']:r for r in source_manifest['artifacts']}
    need(len(by_artifact)==463, 'duplicate sealed a02 artifact ID')
    cues=[cue for chapter in config.chapters for cue in chapter.cues]
    rows=index['cues']
    need(len(cues)==len(rows)==69 and [c.cue_id for c in cues]==[r['cue_id'] for r in rows], 'frozen 69 cue order changed')
    need(sum(r['duration_frames'] for r in rows)==58406, 'frozen 69 clock changed')
    by_id={row['cue_id']:row for row in rows}
    refs={}
    for row in rows:
        key=row['cue_id'];refs[key]={}
        need(row['reuse_exact_encoded_segment'] is (key not in FIX), 'reuse flag differs: '+key)
        for role,ref in row['refs'].items():
            original=by_artifact[ref['artifact_id']]
            need(original['path']==ref['path_relative_to_source_run'] and original['bytes']==ref['bytes'] and original['sha256'].lower()==ref['sha256'].lower(), 'index/source manifest binding differs: '+key+'/'+role)
            if role in ('segment','narration','subtitle') or (key in FIX and role=='visual'):
                refs[key][role]=resolve_ref(source_run,ref)
    segments=[];reuse_paths={}
    for cue,row in zip(cues,rows):
        key=cue.cue_id;duration=row['duration_frames']/30
        visual=refs[key]['visual'] if key in FIX else refs[key]['segment']
        if key not in FIX:
            reuse_paths[str(visual.resolve())]=(key,row['refs']['segment'])
        kind=STILL if key in FIX else VIDEO
        source_object=VisualSource(key,kind,visual,'method-review-typography-card' if key in FIX else 'reused-exact-encoded-method-review-segment',metadata={'source_run_sha256':source['sha256'],'new_encoding':key in FIX,'formal_dynamic_credit':False})
        segments.append(SegmentDraft(key,source_object,RenderOptions(1920,1080,30,duration,preset='veryfast',crf=21),{'zh-CN':cue.narration['zh-CN'],'en':cue.subtitles['en']},prepared_narration=refs[key]['narration']))
    def subtitles(segment,narration,*,workdir):
        del narration,workdir
        path=refs[segment.segment_id]['subtitle']
        return replace_correction(segment.segment_id,path.read_text(encoding='utf-8-sig'))
    def inspect(path):
        p=Path(path).resolve()
        if str(p) in reuse_paths:
            return VisualProbeResult('video/mp4',1920,1080)
        with Image.open(p) as img:
            need((img.width,img.height)==(1920,1080), 'static card geometry changed')
            return VisualProbeResult('image/png',img.width,img.height)
    helper=Path(__file__).with_name('reuse_exact_segment.py').resolve()
    need(helper.is_file(), 'exact reuse helper absent')
    def planner(**kwargs):
        key=str(Path(kwargs['video_input']).resolve())
        if key not in reuse_paths:
            normal=plan_render(**kwargs)
            changed=[]
            for command in normal.commands:
                argv=list(command.spec.argv)
                need('-threads' not in argv and '-filter_complex_threads' not in argv, 'standard render thread seam changed')
                argv[-1:-1]=['-threads','1','-filter_complex_threads','1']
                changed.append(replace(command,spec=replace(command.spec,argv=tuple(argv))))
            return replace(normal,commands=tuple(changed))
        cue,ref=reuse_paths[key]
        partial=Path(kwargs['partial_output']).resolve()
        final=Path(kwargs['final_output']).resolve()
        audit_dir=Path(kwargs['audit_directory']).resolve()
        cwd=Path(kwargs['working_directory']).resolve()
        spec=CommandSpec.create((sys.executable,'-B','-X','utf8',str(helper),'--source',key,'--partial-output',str(partial),'--expected-bytes',str(ref['bytes']),'--expected-sha256',ref['sha256']),label='reuse exact a02 encoded segment '+cue,cwd=cwd,partial_artifacts=(partial,))
        return RenderPlan((PlannedCommand(spec,audit_dir/'reuse'),),(),partial,final)
    output=Path('episode04-review02-FULL69-METHOD-TYPOGRAPHY-PARTIAL-NO-SIGNOFF.mp4')
    draft=PipelineDraft(config,tuple(segments),output,'episode04-review02-full69-method-typography-partial-no-signoff','video/mp4')
    return PipelineInvocation(draft,PipelineDependencies(os.environ.get('WAR_PROMO_FFMPEG','ffmpeg'),subtitles,run_command,inspect,render_planner=planner),Path(workdir))
