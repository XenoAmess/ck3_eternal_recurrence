"""Append exact certificate producer and closure stdio refs to the bounded request."""
from pathlib import Path
import hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');R=B/'live-attempt-029';O=B/'r29-business-permanent-archive-sourceonly-20261008-001'
BAD={'.ck3','.exe','.dll','.lib','.dmp','.png','.tar','.bin','.zip'}
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve()
 if p.suffix.lower()in BAD:raise ValueError('external body/binary excluded')
 data=p.read_bytes();return {'path':p.as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
q=read(O/'REQUEST.actual.json');seen={Path(r['path']).resolve().as_posix().casefold()for r in q['files']};extra=[]
def add(p,role):
 p=Path(p)
 if p.suffix.lower()in BAD:return
 k=p.resolve().as_posix().casefold()
 if k not in seen:seen.add(k);r=pin(p)|{'role':role};q['files'].append(r);extra.append(r)
def refs(v,role):
 if isinstance(v,dict):
  if all(k in v for k in ['path','bytes','sha256'])and isinstance(v['path'],str)and Path(v['path']).suffix.lower()not in BAD:
   r=pin(v['path'])
   if r['bytes']!=v['bytes']or r['sha256']!=v['sha256'].lower():raise ValueError('certificate original source bytes differ')
   add(v['path'],role)
  else:
   for x in v.values():refs(x,role)
 elif isinstance(v,list):
  for x in v:refs(x,role)
cert=read(R/'B3-r3-signed-author-001/FORMAL-NATIVE-QUALIFICATION.actual-or-pending.json')
refs(cert['source_artifacts'],'exact independent formal leaf/source producer artifacts from actual B3 certificate')
refs(cert.get('retained_source_artifacts',{}),'exact retained initial/joined/provenance artifacts bound by formal certificate')
q['facts']['B3_actual_source_artifacts']=cert['source_artifacts']
# Nonexistent optional locator paths are preserved in source001 history; the actual certificate supplies the correct source refs.
q['facts']['missing_optional_source_refs']=[r for r in q['facts']['missing_optional_source_refs']if not r['path'].endswith('/reader/formal_native_qualification.py')]
for row in read(B/'r29-root-typed-close-actual-source-20261008-001/DEPENDENCIES.json').values():
 if isinstance(row,dict)and isinstance(row.get('path'),str)and Path(row['path']).suffix.lower()not in BAD:
  p=Path(row['path'])
  if p.suffix=='.json':
   doc=read(p)
   for name in ['stdout','stderr','argv_input']:
    if isinstance(doc.get(name),dict):refs(doc[name],'exact original typed closure execution stdio/argv')
refs(read(B/'r29-root-actual-typed-closed-boundary-20261008-001/HELPERS-CLOSED.actual.json'),'exact original helper closed refs from ROOT verified boundary')
put(O/'FACTS.final.original-derived.json',q['facts']);add(O/'FACTS.final.original-derived.json','final bounded R29 facts including exact actual formal source artifacts')
put(O/'CURATION-ADDENDUM.actual.json',{'prior_request':pin(O/'REQUEST.actual.json'),'added_files':extra,'correct_source_locator':'certificate.source_artifacts original refs; old guessed optional locations remain historical source001 only','body_binary_SDK_MAIN_calls':0})
add(O/'CURATION-ADDENDUM.actual.json','exact added certificate/closure refs curation audit')
q['files']=[r for r in q['files']if Path(r['path']).name not in ['inspect_existing_json.py','inspect_facts.py','inspect_tail.py','inspect_closed_facts.py','inspect_zero_and_roots.py']]
put(O/'REQUEST.final.actual.json',q)
a=read(O/'CREATE-ARGV.actual.json');argv=a['argv'];argv[argv.index('--request')+1]=(O/'REQUEST.final.actual.json').as_posix();argv[argv.index('--sha256')+1]=pin(O/'REQUEST.final.actual.json')['sha256'];a['request']=pin(O/'REQUEST.final.actual.json')
put(O/'CREATE-ARGV.final.actual.json',a)
print(json.dumps({'request':pin(O/'REQUEST.final.actual.json'),'argv':pin(O/'CREATE-ARGV.final.actual.json'),'files':len(q['files']),'extra':len(extra),'actual_formal_sources':cert['source_artifacts']}))
