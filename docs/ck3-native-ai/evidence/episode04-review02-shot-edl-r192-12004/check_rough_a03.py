from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys
p=Path(__file__).resolve().parent;b=p.parent;r=Path('D:/workspace/ck3_eternal_recurrence');ep=r/'promo/ck3_native_war_ai/episode-04-march-logistics'
def load(q):return json.loads(Path(q).read_text(encoding='utf-8-sig'))
def pin(q,id):
 q=Path(q);x=q.read_bytes();return {'path':str(q),'bytes':len(x),'sha256':hashlib.sha256(x).hexdigest(),'artifact_id':id}
def write(name,v):
 data=(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n').encode();assert sum(f.stat().st_size for f in p.iterdir()if f.is_file())+len(data)<=131072
 with(p/name).open('xb')as f:f.write(data)
pending='C01-03 C01-04 C01-06 C01-07 C01-08 C02-01 C02-02 C02-03 C02-04 C02-06 C02-09 C02-10 C02-11 C02-12 C04-01 C04-02 C04-03 C04-04 C04-05 C04-06 C04-07 C04-08 C04-09 C04-10 C04-11 C05-01 C05-02 C05-03 C05-04 C05-05 C05-06 C05-07 C05-08 C05-09 C05-10 C05-11 C05-12 C05-13 C05-14 C05-15 C05-16 C06-03 C06-04 C06-05 C06-06 C06-07 C06-08 C06-10'.split()
media=load('D:/workspace/ck3_native_war_ai_promo_work/e04-r191-media-audit-bounded-a01/portable-media-facts.actual-a01.json')
data={'schema':'xar.e04.rough-review-inputs.v1','machine_id':'desktop-3fevhd2-1c74096080','source_head':'60de49f61d23b9c3437af4544c3f12bb28445429','review_only':True,'human_signoff':False,'render_geometry':[1920,1080],'repo_root':str(r),'metadata':{'measured':pin(b/'review02-audio-rest68-edge731-a03/production-inputs69.merged.json','source-metadata.measured'),'method':pin(b/'review02-composer-candidate-a01/input-config.methodology.json','reviewcut-input-config'),'raster':pin(b/'review02-static-raster-production-a01/raster-manifest.actual.json','source-png-manifest')},'pending_cues':pending,'visual_overrides':{'C03-01':{'role':'rough-context-only','continuous_clean':False,'event_PTS':None,'approval':'pending','source':{**media['raw'],'artifact_id':'rough-raw.R191'},'source_frames':[0,972],'source_frame_count':3359,'selection_basis':'Explicit source first972frames for context review only; not UTC-derived callback synchronization'}}}
write('ROUGH-INPUTS.source-list-a03.json',data)
env=dict(os.environ);env['PYTHONPATH']=str(p)+os.pathsep+str(r/'promo/ck3_native_war_ai/integration/src');env['PYTHONDONTWRITEBYTECODE']='1';env['XAR_E04_ROUGH_INPUT']=str(p/'ROUGH-INPUTS.source-list-a03.json')
work=p/'PROPOSED_ROUGH_PLAN_NO_CREATE';assert not work.exists()
argv=[sys.executable,'-B','-X','utf8','-m','xar_promo','plan',str(b/'review02-render-inputs-a03-materialized-a01/project/promo-project.json'),'--workdir',str(work),'--composer','review02_mixed_rough:compose','--validate-only']
result=subprocess.run(argv,cwd=r,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
write('ROUGH-PLAN.actual-a03.json',{'machine_id':data['machine_id'],'at_utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'exit_code':result.returncode,'stdout':result.stdout.decode(),'stderr':result.stderr.decode(),'workdir_created':work.exists(),'pending_key_cues':len(pending),'rough_context_cues':1,'source_card_cues':69-len(pending)-1,'event_PTS':None,'continuous_clean':False,'render_ready':False,'new_run':False,'raw_reads':0})
print(result.returncode,result.stderr.decode(),result.stdout.decode());assert result.returncode==0 and not work.exists()
