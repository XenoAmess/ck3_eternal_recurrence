from pathlib import Path
import os,sys,json,hashlib
p=Path(__file__).parent;r=Path('D:/workspace/ck3_eternal_recurrence');sys.path.insert(0,str(r/'promo/ck3_native_war_ai/integration/src'))
import review02_mixed_rough as m
from xar_promo.model import ProjectConfig
os.environ['XAR_E04_ROUGH_INPUT']=str(p/'ROUGH-INPUTS.source-list-a03.json')
c=ProjectConfig.from_mapping(m.load(p.parent/'review02-render-inputs-a03-materialized-a01/project/promo-project.json'));kw=dict(config_path=None,run_path=None,workdir=p/'NO_CREATE',adapter_factory=lambda:{'id':c.adapter},preset_factory=lambda:{'id':c.preset})
i=m.compose(c,None,validate_only=True,**kw);s=i.draft.segments[20]
q=i.dependencies.render_planner(ffmpeg='ffmpeg',video_input=s.visual_source.path,audio_input=s.prepared_narration,partial_output=Path('a.partial.mp4'),final_output=Path('a.mp4'),audit_directory=Path('audit'),options=s.render_options)
g=q.commands[0].spec.argv;f=g[g.index('-filter_complex')+1];assert 'scale=1536:864' in f and 'pad=1920:1080:192:0' in f and 'tpad='not in f and ',fps='not in f
try:m.compose(c,None,validate_only=False,**kw)
except ValueError:pass
else:raise AssertionError('unguarded build')
v={'machine_id':'desktop-3fevhd2-1c74096080','checks':'native plan69 + real graph seam + unpreserved build refusal PASS','composer_sha256':hashlib.sha256((p/'review02_mixed_rough.py').read_bytes()).hexdigest(),'render_ready':False,'media_processes':0}
b=json.dumps(v,separators=(',',':')).encode();assert sum(f.stat().st_size for f in p.iterdir()if f.is_file())+len(b)<=131072
with(p/'GRAPH-CHECK.actual-a03.json').open('xb')as h:h.write(b)
print(v)
