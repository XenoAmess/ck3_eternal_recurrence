"""Same-owner operator SDK session for the explicitly prepared research profile."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from mcp import ClientSession, StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parent

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def write(path, body):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

async def main():
    profile_path = ROOT / 'operator-profile-a01.json'
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    require(len(profile['jobs']) == 1, 'Exactly one declared capture job required')
    job = next(iter(profile['jobs']))
    target = profile['target']['id']
    source = Path(profile['jobs'][job]['working_directory'])
    evidence = ROOT / 'native-sdk-attempt-01'
    evidence.mkdir(exist_ok=False)
    parameters = StdioServerParameters(command=sys.executable,
        args=['-X', 'utf8', str(source / 'ck3_autonomous_player/operator_mcp_server.py'), '--profile', str(profile_path)],
        cwd=str(source), env=dict(os.environ, PYTHONUTF8='0', PYTHONIOENCODING='utf-8'))
    number = 0
    with (evidence / 'server-stderr.log').open('x', encoding='utf-8') as err:
        async with stdio_client(parameters, errlog=err) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=120) as session:
                await session.initialize()
                write(evidence / 'tools.json', (await session.list_tools()).model_dump(mode='json'))
                async def call(name, arguments):
                    nonlocal number
                    reply = (await session.call_tool(name, arguments)).model_dump(mode='json')
                    number += 1
                    write(evidence / f'{number:03d}-{name}.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
                          'arguments': arguments, 'reply': reply})
                    require(not reply.get('is_error', reply.get('isError', False)), 'Operator MCP error: ' + name)
                    body = reply.get('structured_content', reply.get('structuredContent'))
                    if body is None:
                        body = json.loads(next(block['text'] for block in reply['content'] if block.get('type') == 'text'))
                    return body
                await call('operator_get_capabilities', {})
                status = await call('operator_get_status', {'target_id': target})
                require(status.get('identity_matches_profile') is True and not any(status.get('process_gates', {}).values()),
                        'Current identity or exclusive process gate refused')
                preflight = await call('operator_preflight_job', {'target_id': target, 'job_name': job})
                require(preflight.get('result') == 'GREEN' and all(v is True for v in preflight['checks'].values()), 'Operator preflight refused')
                handoff = await call('operator_handoff_job', {'target_id': target, 'job_name': job, 'request_id': 'e2-scoped-ui-20261001-a03-root'})
                require(handoff.get('result') == 'ACCEPTED', 'Operator handoff refused')
                print(json.dumps({'handoff': handoff}, ensure_ascii=False), flush=True)
                deadline = time.monotonic() + 3900
                while time.monotonic() < deadline:
                    await asyncio.sleep(15)
                    status = await call('operator_get_status', {'target_id': target})
                    jobs = [row for row in status.get('jobs', []) if row.get('job_name') == job]
                    if jobs and all(row.get('exit_code') is not None for row in jobs):
                        write(evidence / 'completion.json', status)
                        print(json.dumps({'completed_jobs': jobs}, ensure_ascii=False), flush=True)
                        return 0 if all(row.get('exit_code') == 0 for row in jobs) else 2
                raise TimeoutError('Same-owner job still active; inspect retained state before any stop')

if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
