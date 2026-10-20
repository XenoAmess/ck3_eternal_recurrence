from __future__ import annotations
import datetime as dt
import hashlib
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = Path('D:/workspace/ck3_eternal_recurrence')
MACHINE = 'desktop-3fevhd2-1c74096080'
SOURCES = [
 ('r194-r196','C:/ck3-e04-resume-20261015-a01/r194-r196-chapter-assemble-a01/work-a02/R194-R196-SPLIT-MERGE-BOARDING-55s-REVIEW-DRAFT-a02.mp4',7168415,'9323a8ace8adf7ea104d5f2fa29b9908baf7bdaa536b3621097273a37714e136',1649),
 ('r211','D:/workspace/ck3_native_war_ai_promo_work/e04-r211-actual-insert-render-a01/work-build-a02/R211-R05-ACTUAL-INSERT-27s-REVIEW-NO-SIGNOFF.mp4',1954195,'3d8da9b2e87e65101a3ecf8d44dae5ce4f1953f1d404e100b3b8ddeac7847e3a',810),
 ('r215','D:/workspace/ck3_native_war_ai_promo_work/e04-r215-month-refill-insert-a01/work-build-a01/R215-R06-MONTH-INSERT-21s-REVIEW-NO-SIGNOFF.mp4',1404907,'fb6701ca2dd932fef9496432e441b9dbac735d287388b96992a257158a44ea9c',630),
 ('r217','D:/workspace/ck3_native_war_ai_promo_work/e04-r217-county-insert-a01/work-build-a01/R217-R04-COUNTY-INSERT-27s-REVIEW-NO-SIGNOFF.mp4',1698188,'4b7f762d37c2c6e961e7284a7db26d24634dfcbe1970eb8043e2428611619e33',810),
]

def run(argv):
 p = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=ROOT)
 if p.returncode: raise RuntimeError(json.dumps({'argv':argv,'returncode':p.returncode,'stderr':p.stderr}))
 return p.stdout

def pin(path):
 p=Path(path)
 with p.open('rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha}

def write(name,data):
 (ROOT/name).parent.mkdir(parents=True,exist_ok=True)
 with (ROOT/name).open('x',encoding='utf-8',newline='\n') as stream: json.dump(data,stream,ensure_ascii=False,indent=2); stream.write('\n')

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 now=dt.datetime.now(dt.timezone.utc).isoformat()
 release=json.loads(run(['gh','api','repos/XenoAmess/xar_promo_toolchain/releases/latest']))
 asset=next(a for a in release['assets'] if a['name'].endswith('.whl'))
 dist=metadata.distribution('xar-promo-toolchain')
 direct=json.loads((Path(dist._path)/'direct_url.json').read_text(encoding='utf-8'))
 assert not release['draft'] and not release['prerelease']
 assert dist.version==release['tag_name'].removeprefix('v')=='0.3.0'
 assert direct['url']==asset['browser_download_url']
 assert direct['archive_info']['hash']==asset['digest'].replace(':','=')
 assert asset['browser_download_url'] in (REPO/'tools/requirements-promo-toolchain.txt').read_text(encoding='utf-8-sig')
 probes=[]
 for ident,path,size,sha,frames in SOURCES:
  actual=pin(path); assert actual['bytes']==size and actual['sha256']==sha,(ident,actual)
  probe=json.loads(run([shutil.which('ffprobe'),'-v','error','-show_streams','-show_format','-show_data_hash','sha256','-of','json',path]))
  probes.append({'id':ident,'file':actual,'expected_frames_from_passed_QA':frames,'probe':probe})
 from xar_promo.pipeline import PipelineDependencies,PipelineDraft,PipelineInvocation,SegmentDraft
 from xar_promo.render import plan_concat
 apis={c.__name__:str(inspect.signature(c)) for c in [PipelineDependencies,PipelineDraft,PipelineInvocation,SegmentDraft,plan_concat]}
 help_records={name:run([sys.executable,'-m','xar_promo',*args]) for name,args in [('version',['--version']),('help',['--help']),('plan',['plan','--help']),('build',['build','--help']),('init',['init','--help']),('preserve',['preserve','--help']),('review',['review','--help'])]}
 result={'schema':'xar.e04.resume-media-intake.v1','machine_id':MACHINE,'observed_at_utc':now,
  'source_commit':run(['git','-C',str(REPO),'rev-parse','HEAD']).strip(),
  'interpreter':{'path':sys.executable,'version':sys.version,'xar_promo_version':dist.version,'direct_url':direct},
  'official_release':{'query_argv':['gh','api','repos/XenoAmess/xar_promo_toolchain/releases/latest'],'tag':release['tag_name'],'release_id':release['id'],'url':release['html_url'],'wheel_url':asset['browser_download_url'],'wheel_digest':asset['digest']},
  'skill':pin('D:/workspace/xar_promo_toolchain/codex-skill/promo-video-pipeline/SKILL.md'),
  'inputs':probes,'help':help_records,'apis':apis,'old_inputs_redecoded':False,'raw_inputs_copied':False,
  'C_volume':dict(zip(('total','used','free'),shutil.disk_usage('C:/'))),'new_heavy_write_admitted':False,
  'requested_peak_bytes':268435456,'estimated_streamcopy_output_bytes':sum(x[2] for x in SOURCES),
  'expected_video_frames':sum(x[4] for x in SOURCES),'expected_video_seconds':sum(x[4] for x in SOURCES)/30,
  'remaining_limits':['editorial sequence across separate runs','continuous-clean pending','human 1x and signoff pending','formal dynamic credit unchanged 0/11','ABC unchanged 0/3']}
 write('INTAKE.actual.json',result)
 print(json.dumps({'intake':pin(ROOT/'INTAKE.actual.json'),'apis':apis,'streams':[{'id':p['id'],'streams':[dict((k,s.get(k)) for k in ('codec_name','codec_type','profile','width','height','pix_fmt','level','sample_rate','channels','time_base','r_frame_rate','start_time','duration','nb_frames','extradata_hash')) for s in p['probe']['streams']]} for p in probes]},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
