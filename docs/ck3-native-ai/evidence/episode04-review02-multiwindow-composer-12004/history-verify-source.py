"""One behavior check: a shared immutable raw gets two independent cue seeks."""
from pathlib import Path
import datetime, hashlib, importlib.util, importlib.metadata, json, os, sys
from unittest.mock import patch
sys.dont_write_bytecode=True
P=Path(__file__).parent
R=Path('D:/workspace/ck3_eternal_recurrence')
sys.path.insert(0,str(R/'promo/ck3_native_war_ai/integration/src'))
from xar_promo.model import ProjectConfig

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

base=R/'promo/ck3_native_war_ai/integration/src/war_ai_promo/episode04_review02_mixed_rough.py'
before=hashlib.sha256(base.read_bytes()).hexdigest()
old=module('baseline_rough',base)
new=module('candidate_rough',P/'episode04_review02_multiwindow_rough.py')
config_path=Path('C:/ck3-e04-resume-20261015-a01/review02-render-inputs-a03-materialized-a01/project/promo-project.json')
config=ProjectConfig.from_mapping(new.load(config_path))
os.environ['XAR_E04_ROUGH_INPUT']=str(P/'ROUGH-INPUTS.candidate-a01.json')
kw=dict(config_path=config_path,run_path=None,workdir=P/'NO_CREATE',adapter_factory=lambda:{'id':config.adapter},preset_factory=lambda:{'id':config.preset},validate_only=True)
opened=Path.open
def guarded_open(self,mode='r',*args,**kwargs):
    if self.suffix.lower() in {'.mkv','.mp3','.png'} and 'r' in mode:
        raise AssertionError('media body read forbidden')
    return opened(self,mode,*args,**kwargs)
def forbidden(*args,**kwargs):raise AssertionError('media execution forbidden')

with patch.object(Path,'open',guarded_open):
    old.probe_media=old.run_command=forbidden
    new.probe_media=new.run_command=forbidden
    try:old.compose(config,None,**kw)
    except ValueError as error:
        assert str(error)=='one raw window per source; preserve separate prepared clips for reuse'
        control=str(error)
    else:raise AssertionError('baseline unexpectedly accepted the shared raw')
    invocation=new.compose(config,None,**kw)
    segments={s.segment_id:s for s in invocation.draft.segments}
    records=[]
    for cue,first,stop in [('C05-06',0,857),('C05-10',1055,1887)]:
        s=segments[cue]
        assert s.start_seconds==first/30
        plan=invocation.dependencies.render_planner(ffmpeg='ffmpeg',video_input=s.visual_source.path.resolve(),audio_input=s.prepared_narration.resolve(),partial_output=P/'NO_CREATE'/cue/'partial.mp4',final_output=P/'NO_CREATE'/cue/'final.mp4',audit_directory=P/'NO_CREATE'/'audit'/'segments'/cue,options=s.render_options,ass_path=P/'NO_CREATE'/cue/'subtitles.ass',start_seconds=float(s.start_seconds),working_directory=P/'NO_CREATE')
        argv=list(plan.commands[0].spec.argv)
        seeks=[float(argv[i+1]) for i,x in enumerate(argv) if x=='-ss']
        assert (not seeks and first==0) or (len(seeks)==1 and abs(seeks[0]-first/30)<0.000001),(cue,seeks)
        graph=argv[argv.index('-filter_complex')+1]
        assert 'scale=1536:864' in graph and 'pad=1920:1080:192:0' in graph
        assert 'tpad=' not in graph and ',fps=' not in graph
        records.append({'cue':cue,'source_frames':[first,stop],'start_seconds':s.start_seconds,'encoded_duration_seconds':(stop-first)/30,'planned_input_seeks':seeks,'graph_sha256':hashlib.sha256(graph.encode()).hexdigest(),'raw_path':str(s.visual_source.path)})
assert records[0]['raw_path']==records[1]['raw_path']
assert hashlib.sha256(base.read_bytes()).hexdigest()==before
assert not (P/'NO_CREATE').exists()
result={'schema':'episode04.multiwindow.behavior-check.actual.v1','machine_id':'desktop-3fevhd2-1c74096080','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','behavior_checks':1,'toolchain_version':importlib.metadata.version('xar-promo-toolchain'),'baseline_rejection':control,'candidate_draft_cues':len(invocation.draft.segments),'windows':records,'main_composer_unchanged_sha256':before,'raw_body_reads':0,'audio_payload_reads':0,'new_frames':0,'media_processes':0,'SDK_calls':0,'new_runs':0,'render_ready':False,'candidate_counts':[4,20,45],'new_research_business_dynamic_credit':0}
b=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
(P/'BEHAVIOR-CHECK.actual-a01.json').write_bytes(b)
print(json.dumps({'status':'PASS','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'raw_body_reads':0}))
