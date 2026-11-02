"""Runtime-owned invocation: adopt one approved Java leaf, then trigger one local dev scan.

Source adoption, HTTP response and actual lifecycle acceptance remain separate evidence.
This helper does not start/stop a JVM, touch a ledger or retry a Game action.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,time,urllib.error,urllib.parse,urllib.request,uuid,xml.etree.ElementTree as ET

p=argparse.ArgumentParser()
p.add_argument('--source-root',required=True);p.add_argument('--relative-path',required=True)
p.add_argument('--candidate',required=True);p.add_argument('--expected-before-sha256',required=True)
p.add_argument('--expected-new-sha256',required=True);p.add_argument('--evidence-root',required=True)
p.add_argument('--base-url',default='http://127.0.0.1:8089');p.add_argument('--timeout-seconds',type=float,default=60)
a=p.parse_args();source=Path(a.source_root).resolve();candidate=Path(a.candidate).resolve()
relative=Path(a.relative_path);assert not relative.is_absolute() and '..' not in relative.parts
target=(source/relative).resolve();assert target.is_relative_to(source)
assert relative.suffix=='.java' and '/src/main/java/' in relative.as_posix()
modules={m.text for m in ET.parse(source/'pom.xml').findall('{http://maven.apache.org/POM/4.0.0}modules/{http://maven.apache.org/POM/4.0.0}module')}
assert relative.parts[0] in modules,'declared module required'
url=urllib.parse.urlsplit(a.base_url);assert url.scheme=='http' and url.hostname=='127.0.0.1' and url.port and url.path in ('','/')
assert not url.username and not url.password and not url.query and not url.fragment
assert 0<a.timeout_seconds<=1800
raw=candidate.read_bytes();assert 0<len(raw)<=8*1024*1024
newsha=hashlib.sha256(raw).hexdigest();assert newsha==a.expected_new_sha256
before=target.read_bytes() if target.exists() else None
oldsha=hashlib.sha256(before).hexdigest() if before is not None else 'ABSENT'
assert oldsha==a.expected_before_sha256,'source changed outside the approved adoption'
evidence=Path(a.evidence_root).resolve();assert not evidence.is_relative_to(source)
evidence.mkdir(parents=True,exist_ok=False)
def now():return datetime.now(timezone.utc).isoformat()
def save(name,value):(evidence/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
prepared={'at_utc':now(),'source_root':str(source),'relative_path':relative.as_posix(),'candidate':str(candidate),'before_sha256':oldsha,'new_sha256':newsha,'candidate_bytes':len(raw),'trigger_url':a.base_url.rstrip('/')+'/q/dev-ui/','method':'GET','automatic_after_source_adoption':True,'actual_reload_proved':False}
save('PREPARED.json',prepared)
target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_name(target.name+'.pending-'+uuid.uuid4().hex)
with temporary.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
os.replace(temporary,target);assert hashlib.sha256(target.read_bytes()).hexdigest()==newsha
save('SOURCE-ADOPTED.json',{**prepared,'adopted_at_utc':now(),'source_changed':oldsha!=newsha,'actual_reload_proved':False})
started=time.perf_counter();began=now();status=None;failure=None;body=b'';content_type=None
try:
    request=urllib.request.Request(prepared['trigger_url'],method='GET',headers={'User-Agent':'CK3-Dev-Adoption307/1'})
    with urllib.request.urlopen(request,timeout=a.timeout_seconds) as response:
        status=response.status;content_type=response.headers.get('Content-Type');body=response.read(65537)
except urllib.error.HTTPError as error:
    status=error.code;content_type=error.headers.get('Content-Type');body=error.read(65537);failure=str(error)
except Exception as error:failure=type(error).__name__+': '+str(error)
(evidence/'HTTP-BODY-PREFIX.bin').write_bytes(body[:65536])
result={'began_at_utc':began,'ended_at_utc':now(),'elapsed_seconds':time.perf_counter()-started,'url':prepared['trigger_url'],'http_status':status,'content_type':content_type,'failure':failure,'body_prefix_bytes':min(len(body),65536),'body_truncated':len(body)>65536,'source_adopted':True,'automatic_scan_request_sent':True,'actual_reload_proved':False,'acceptance':'Runtime must separately observe actual compilation/restart, old delegate completion, successor loader and sameGame resume. HTTP200 alone is not reload success. No automatic retry, rollback or process operation.'}
save('TRIGGER-ACTUAL.json',result);print(json.dumps(result),flush=True)
raise SystemExit(0 if status is not None and status<500 else 2)
