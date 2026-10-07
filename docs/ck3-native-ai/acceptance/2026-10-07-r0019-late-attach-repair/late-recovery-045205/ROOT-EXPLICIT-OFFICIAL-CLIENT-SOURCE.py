"""One explicit official SDK call in the retained Client, after its queue refusal.

Executed by standard debugger evaluation. No transport, client, server or game
is restarted. The original queue attach_requested flag is never changed.
"""
from pathlib import Path
from datetime import datetime,timezone
import asyncio,gc,hashlib,json,os,sys
import psutil

def require(ok,message):
    if not ok:
        raise RuntimeError(message)

def ref(path):
    raw=path.read_bytes()
    return {'path':path.resolve().as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

b=Path('C:/workspace/ck3_lyd_runtime_20261004')
recovery=b/'r19-debugpy-recovery-20261007-001'
run=b/'live-attempt-019'
identity=json.loads((recovery/'PROCESS-IDENTITIES.actual.json').read_bytes())
expected=identity['client']
proc=psutil.Process(os.getpid())
require(os.getpid()==expected['pid'] and proc.create_time()==expected['create_time'] and proc.cmdline()==expected['cmdline'],'Different original SDK Client process')
module=sys.modules['__main__']
require(ref(Path(module.__file__))['sha256']=='56e53b3b3be226b5f22538d0bebc19ff5b7b3a7427fbc263d383cbbee8e4b25d','Frozen Client queue source differs')
overlay=recovery/'PYTHON-SOURCE-OVERLAY.actual.json'
require(ref(overlay)['sha256']=='fa1ddcbfc97ce969ee27aeaaee6f53d2ddf52de2763c6d5cfa3a138a76582732','Actual loaded service repair differs')
loops=[obj for obj in gc.get_objects() if isinstance(obj,asyncio.AbstractEventLoop) and obj.is_running() and not obj.is_closed()]
require(len(loops)==1,'One original running Client event loop required')
loop=loops[0]
tasks=[task for task in asyncio.all_tasks(loop) if getattr(task.get_coro(),'cr_code',None) is module.serve.__code__]
require(len(tasks)==1,'One original SDK serve coroutine required')
frame=tasks[0].get_coro().cr_frame
local=frame.f_locals
client=local['client']
require(local['attach_requested'] is True and local['inventory_verified'] is True and local['terminal_exit_requested'] is False,'Original one-shot/inventory/terminal facts differ')
require(local['session']['client_session_id']=='5b11bc8186974854aa695cf2704e8866','Different retained SDK session')
require(local['output'].resolve()==(run/'mcp-client-001').resolve(),'Different Client evidence directory')
prefix='direct-r19-root-late-verify-001'
out=local['output']
require(not (out/(prefix+'.started.json')).exists(),'Explicit late verification was already scheduled')
started={'schema':'lyd.root.explicit-sdk-late-verification.v1','request_id':prefix,'name':'ck3_attach_profile_bridge_v1','arguments':{},'started_at_utc':datetime.now(timezone.utc).isoformat(),'client_session_id':local['session']['client_session_id'],'native_session_id':'172caf27cc8b44549ea94ed2f306cfe0','client_process':expected,'client_object_id':id(client),'loop_object_id':id(loop),'service_source_overlay':ref(overlay),'source':ref(Path(__file__)),'route':'ORIGINAL_CLIENT_OFFICIAL_SDK_EXPLICIT_CALL_AFTER_QUEUE_HARNESS_REFUSAL','queue_attach_requested_before':True,'queue_attach_requested_reset':False,'new_transport':False,'new_client':False,'new_server':False,'reconnected':False,'reinjected':False}
module.write_fresh(out/(prefix+'.started.json'),started)

async def explicit_late_call():
    result_path=out/(prefix+'.sdk-result.json')
    record=dict(started)
    try:
        typed=await client.call_tool('ck3_attach_profile_bridge_v1',{},read_timeout_seconds=60)
        payload=typed.model_dump(mode='json',by_alias=True,exclude_none=False)
        module.write_fresh(result_path,payload)
        record.update(status='OFFICIAL_SDK_RESULT_RECORDED',is_error=getattr(typed,'isError',None),sdk_result=ref(result_path),native_receipts=module.preserve_native_receipts(payload,out,local['native_evidence'],prefix),queue_attach_requested_after=frame.f_locals['attach_requested'])
    except Exception as error:
        record.update(status='ERROR_NO_RETRY',reason=type(error).__name__+': '+str(error))
    record['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    module.write_fresh(out/(prefix+'.response.json'),record)

# The future cannot execute until the debugger continues the original event loop.
# It sends exactly one ordinary official SDK call; no queue flag is reset.
future=asyncio.run_coroutine_threadsafe(explicit_late_call(),loop)
