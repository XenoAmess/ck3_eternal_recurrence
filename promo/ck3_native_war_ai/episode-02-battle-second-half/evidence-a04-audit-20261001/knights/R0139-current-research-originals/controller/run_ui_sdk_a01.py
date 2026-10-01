import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from mcp import ClientSession, StdioServerParameters, stdio_client
ROOT=Path(__file__).resolve().parent
PROFILE=ROOT/'operator-profile-a01.json'
def write(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2)
async def main():
    evidence=ROOT/'ui-sdk-a01'
    evidence.mkdir(exist_ok=False)
    params=StdioServerParameters(command=sys.executable,args=['-X','utf8','C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-12-R0129-native-center-diagnostic/source/ck3_autonomous_player/operator_mcp_server.py','--profile',str(PROFILE)],
             cwd='C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-12-R0129-native-center-diagnostic/source',env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='utf-8'))
    target='ck3-six-gap-ui-20261001-a02'
    job='six-gap-ui-capture'
    number=0
    with (evidence/'server-stderr.log').open('x',encoding='utf-8') as err:
        async with stdio_client(params,errlog=err) as (reader,writer):
            async with ClientSession(reader,writer,read_timeout_seconds=120) as session:
                await session.initialize()
                write(evidence/'tools.json',(await session.list_tools()).model_dump(mode='json'))
                async def call(name,args):
                    nonlocal number
                    reply=(await session.call_tool(name,args)).model_dump(mode='json')
                    number+=1
                    write(evidence/f'{number:03d}-{name}.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'arguments':args,'reply':reply})
                    if reply.get('is_error',reply.get('isError',False)):
                        raise RuntimeError('MCP error '+name)
                    body=reply.get('structured_content',reply.get('structuredContent'))
                    if body is None:
                        body=json.loads(next(v['text'] for v in reply['content'] if v.get('type')=='text'))
                    return body
                caps=await call('operator_get_capabilities',{})
                status=await call('operator_get_status',{'target_id':target})
                if not status.get('identity_matches_profile') or any(status.get('process_gates',{}).values()):
                    raise RuntimeError('Identity or process gate refused')
                preflight=await call('operator_preflight_job',{'target_id':target,'job_name':job})
                if preflight.get('result')!='GREEN' or not all(v is True for v in preflight['checks'].values()):
                    raise RuntimeError('Operator preflight refused')
                launched=await call('operator_handoff_job',{'target_id':target,'job_name':job,'request_id':'six-gap-ui-20261001-a02-root'})
                if launched.get('result')!='ACCEPTED':
                    raise RuntimeError('Handoff refused')
                print(json.dumps({'handoff':launched},ensure_ascii=False),flush=True)
                deadline=time.monotonic()+3900
                while time.monotonic()<deadline:
                    await asyncio.sleep(15)
                    status=await call('operator_get_status',{'target_id':target})
                    jobs=[r for r in status.get('jobs',[]) if r.get('job_name')==job]
                    if jobs and all(r.get('exit_code') is not None for r in jobs):
                        write(evidence/'completion.json',status)
                        print(json.dumps({'completed_jobs':jobs},ensure_ascii=False),flush=True)
                        return 0 if all(r.get('exit_code')==0 for r in jobs) else 2
                raise TimeoutError('Same-owner job still active; inspect retained state')
if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
