"""One ROOT-selected official SDK request; exact stdio retained, no retry or decisions."""
from pathlib import Path
import argparse,json,subprocess,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--request-id',required=True); p.add_argument('--name',required=True)
p.add_argument('--arguments-file',type=Path,required=True); p.add_argument('--display',choices=['small','event'],default='small')
a=p.parse_args(); base=Path('C:/workspace/ck3_lyd_runtime_20261004'); run=base/'live-attempt-010'; out=run/'root-call-stdio'/a.request_id
assert a.arguments_file.is_file(); out.mkdir(parents=True,exist_ok=False)
sequence=0
def execute(argv):
    global sequence
    seq=sequence; sequence+=1
    r=subprocess.run([sys.executable,'-B','-X','utf8',*[str(x) for x in argv]],shell=False,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    for suffix,data in (('stdout',r.stdout),('stderr',r.stderr)):
        with (out/(str(seq)+'.'+suffix+'.bin')).open('xb') as f: f.write(data)
    if r.returncode:
        print(r.stdout.decode('utf-8',errors='replace')); print(r.stderr.decode('utf-8',errors='replace')); sys.exit(r.returncode)
    return r.stdout
execute([base/'root_r10_mcp_explicit_request_20261005.py','--binding',run/'mcp-binding-002/ROOT-BINDING.json','--binding-sha256','accb15735d343ab87d842cafcecb32b2944638667806da1b27ed5871fae9d501','--request-id',a.request_id,'--operation','call_tool','--name',a.name,'--arguments-file',a.arguments_file])
response=json.loads(execute([base/'root_r10_wait_read_response_20261005.py','--request-id',a.request_id])); assert response['status']=='MCP_RESULT_RECORDED'
print(json.dumps({k:response.get(k) for k in ('sequence','request_id','status','sdk_result','sdk_result_sha256','finished_at_utc')},ensure_ascii=False))
print(execute([base/('root_r10_event_display_v2_20261005.py' if a.display=='event' else 'root_r10_small_sdk_v2_20261005.py'),run/'mcp-client-evidence-002'/response['sdk_result']]).decode('utf-8',errors='replace'))
