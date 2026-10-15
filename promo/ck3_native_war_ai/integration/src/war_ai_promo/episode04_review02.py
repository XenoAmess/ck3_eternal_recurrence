"""E04 thin wiring: preserve legacy narration/captions and xar-promo pipeline.

No provider, process, or media call occurs on import or binding. Full composition
requires measured audio plus explicitly preserved visuals and new English.
"""
from pathlib import Path
import argparse,hashlib,json,math,os
from xar_promo.pipeline import PipelineDependencies,PipelineDraft,PipelineInvocation,SegmentDraft
from xar_promo.render import RenderOptions,plan_render
from xar_promo.sources import STILL,VisualProbeResult,VisualSource
from xar_promo.media import probe_media
from xar_promo.process import run_command
from .common import load,write_new
from .composer import artifact,capture_visual,plan_capture_render
from .captions import subtitle_document

def need(ok,reason):
    if not ok:raise ValueError(reason)
def text_sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()

def bind_payloads(script,measured,english,visuals):
    """Join future actual measured inputs. Structural join is not media approval."""
    cues=script['cues'];ids=[r['id'] for r in cues]
    need(len(ids)==len(set(ids))==69,'expected exact original69')
    need(all(len(p['cues'])==len({r['id'] for r in p['cues']})==69 for p in (measured,english,visuals)),'duplicate or incomplete input rows')
    m={r['id']:r for r in measured['cues']}
    e={r['id']:r for r in english['cues']}
    v={r['id']:r for r in visuals['cues']}
    need(set(m)==set(e)==set(v)==set(ids),'measured/English/visual IDs differ')
    rows=[]
    for cue in cues:
        key=cue['id'];row=dict(m[key]);eng=e[key];vis=v[key]
        need(row['zh']==cue['zh'] and eng['chinese_utf8_sha256']==text_sha(cue['zh']),'stale measured or English text')
        need(isinstance(eng.get('en'),str) and eng['en'].strip(),'new English missing')
        speech=row.get('speech_duration_seconds');duration=row.get('duration_seconds')
        need(type(speech) in (int,float) and type(duration) in (int,float) and math.isfinite(speech) and math.isfinite(duration) and duration>=speech>0,'actual measured duration missing')
        need(('capture_clip' in vis) != ('visual_artifact_id' in vis),'one explicit visual binding required')
        need(vis.get('continuous_clean') is True if 'capture_clip' in vis else vis.get('evidence_role')=='source-explanation-card','capture clean or source-card role missing')
        row.update({k:value for k,value in vis.items() if k!='id'})
        row.update(en=eng['en'],claim_ids=[key],chinese_utf8_sha256=text_sha(cue['zh']))
        rows.append(row)
    return {'format_version':1,'media_scope':'mixed-footage' if any('capture_clip' in r for r in rows) else 'prepared-source-cards','full_film':True,'cues':rows,'human_signoff':'not-provided'}

def compose(config,run,*,config_path,run_path,workdir,adapter_factory,preset_factory,validate_only):
    del config_path,validate_only
    need(adapter_factory()['id']==config.adapter and preset_factory()['id']==config.preset,'wrong adapter/preset')
    data=load(artifact(run,run_path,'production-inputs-v1'))
    rows=data['cues'];configured=[cue for chapter in config.chapters for cue in chapter.cues]
    need([r['id'] for r in rows]==[c.cue_id for c in configured] and len(rows)==69,'cue order/coverage differs')
    ffmpeg=os.environ.get('WAR_PROMO_FFMPEG','ffmpeg');ffprobe=os.environ.get('WAR_PROMO_FFPROBE','ffprobe')
    segments=[];captures=set();by_id={r['id']:r for r in rows}
    for row,cue in zip(rows,configured):
        need(row['zh']==cue.narration['zh-CN'] and row['chinese_utf8_sha256']==text_sha(row['zh']),'spoken text differs')
        need(isinstance(row.get('en'),str) and row['en'].strip(),'new English required for bilingual render')
        need(row['en']==cue.subtitles.get('en'),'render English differs from bound ProjectConfig')
        duration=row['duration_seconds'];speech=row['speech_duration_seconds']
        need(type(duration) in (int,float) and type(speech) in (int,float) and math.isfinite(duration) and math.isfinite(speech) and duration>=speech>0,'unmeasured audio duration')
        audio_records=[record for record in run.artifacts if record.artifact_id==row['audio_artifact_id']]
        need(len(audio_records)==1 and audio_records[0].bytes==row['audio']['bytes'] and audio_records[0].sha256.lower()==row['audio']['sha256'].lower(),'preserved audio differs from measured source binding')
        if 'capture_clip' in row:
            need(row.get('continuous_clean') is True,'actual capture has not had continuous-clean review')
            visual=capture_visual(row,run,run_path);captures.add(visual.path.resolve())
        else:
            need(row.get('evidence_role')=='source-explanation-card','card cannot stand in for missing actual footage')
            visual=VisualSource(row['id'],STILL,artifact(run,run_path,row['visual_artifact_id']),'preserved-source-card',metadata={'actual_outcome_credit':False})
        segments.append(SegmentDraft(row['id'],visual,RenderOptions(2560,1440,30,duration,preset='veryfast',crf=21),{'zh-CN':row['zh'],'en':row['en']},prepared_narration=artifact(run,run_path,row['audio_artifact_id'])))
    def inspect_visual(path):
        if Path(path).suffix.lower() in {'.png','.jpg','.jpeg'}:
            from PIL import Image
            with Image.open(path) as image:return VisualProbeResult(image.get_format_mimetype(),image.width,image.height)
        probe=probe_media(ffprobe,path,audit_directory=Path(workdir)/'audit'/'probe'/Path(path).stem)
        stream=probe.video_streams[0];return VisualProbeResult('video/mp4',stream.width,stream.height)
    def subtitle_renderer(segment,narration,*,workdir):
        return subtitle_document(by_id[segment.segment_id])
    def planner(**kwargs):
        return (plan_capture_render if Path(kwargs['video_input']).resolve() in captures else plan_render)(**kwargs)
    return PipelineInvocation(PipelineDraft(config,tuple(segments),Path('episode04-review02-narrated.mp4'),'episode04-review02-narrated-v1','video/mp4'),PipelineDependencies(ffmpeg,subtitle_renderer,run_command,inspect_visual,render_planner=planner),Path(workdir))

def main():
    parser=argparse.ArgumentParser(description='Pure join before existing xar-promo plan/build; no production processes')
    for name in ('script','measured','english','visuals','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    result=bind_payloads(load(args.script),load(args.measured),load(args.english),load(args.visuals))
    write_new(args.output,result)
if __name__=='__main__':main()
