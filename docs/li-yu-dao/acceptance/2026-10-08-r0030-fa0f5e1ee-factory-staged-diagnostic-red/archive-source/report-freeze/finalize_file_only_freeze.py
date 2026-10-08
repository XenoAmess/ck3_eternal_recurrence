"""Append actual postclose CI/BOM import refs and run only the file request freezer."""
from pathlib import Path
import hashlib,json,subprocess
B=Path('C:/workspace/ck3_lyd_runtime_20261004');O=B/'r30-final-report-sourceonly-20261008-001';S=B/'r30-permanent-archive-plan-sourceonly-20261008-002'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve()
 if p.suffix.lower()in ['.ck3','.exe','.dll','.lib','.obj','.pdb','.tar','.bin','.zip','.png']:raise ValueError('no binary/body/archive reread')
 v=p.read_bytes();return {'path':p.as_posix(),'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
f=read(O/'FACTS.actual.json');receipt=B/'r30-root-ci-bom-import-20261008-002/RESULT.actual.json'
f['postclose_CI_BOM_ROOT_actual_import']=pin(receipt)
f['postclose_CI_BOM_limits']='ROOT imported13files after genuine close; first wrong-preimage attempt failed before writes and second used actual MAIN001 preimage. Loaded FA0 CI/native/runtime facts remain unchanged; no future newHEAD/newbuild credit.'
# The original comparison rows do not have a universal title_id key. The exact named political field projection is the authoritative ID list.
for row in f['stages']:row.pop('political_delta_ids',None)
put(O/'FACTS.final.actual.json',f)
report=(O/'REPORT.actual.md').read_text(encoding='utf-8')
report+='\nROOT在真实typedclose后已实际导入CI/BOM修补13files（actual import002原回执另存）。import001因错误preimage在写入前拒绝；002按当前MAIN原001builder精确preimage导入。该后续源码变化不改加载FA0的旧官方CI失败或R30诊断RED，也不补新HEAD/新编译/新实机信用。\n'
with (O/'REPORT.final.actual.md').open('x',encoding='utf-8',newline='\n')as out:out.write(report)
q=read(O/'PACKROOTS.closed.actual.json');exclude={B/'r30-permanent-archive-frozen-source-20261008-001',B/'r30-permanent-archive-candidate-20261008-001'}
q['packroots']=[p.as_posix()for p in sorted(B.iterdir())if p.name.startswith(('r30-','root-r30-','r30_'))and p not in exclude]
put(O/'PACKROOTS.final.closed.actual.json',q)
a=read(O/'FREEZE-ARGV.actual.json');argv=a['argv']
for n,p in [('facts',O/'FACTS.final.actual.json'),('report',O/'REPORT.final.actual.md'),('packroots',O/'PACKROOTS.final.closed.actual.json')]:argv[argv.index('--'+n)+1]=p.as_posix();argv[argv.index('--'+n+'-sha256')+1]=pin(p)['sha256'];a[n]=pin(p)
put(O/'FREEZE-ARGV.final.actual.json',a)
result=subprocess.run(argv,capture_output=True,check=False)
with (O/'freeze.stdout').open('xb')as out:out.write(result.stdout)
with (O/'freeze.stderr').open('xb')as out:out.write(result.stderr)
put(O/'FREEZE-ORIGINAL-EXEC.actual.json',{'argv_input':pin(O/'FREEZE-ARGV.final.actual.json'),'argv':argv,'exit_code':result.returncode,'stdout':pin(O/'freeze.stdout'),'stderr':pin(O/'freeze.stderr'),'collector_executed':False,'body_binary_SDK_process_game_MAIN_calls':0})
print(result.stdout.decode('utf-8'));print('freeze_exit',result.returncode)
if result.returncode:print(result.stderr.decode('utf-8',errors='replace'))
raise SystemExit(result.returncode)
