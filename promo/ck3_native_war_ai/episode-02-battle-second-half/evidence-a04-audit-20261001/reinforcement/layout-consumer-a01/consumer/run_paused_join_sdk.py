"""Root-triggered single SDK session for the minimal J-d11 paused pair.

This is an actual launch entry. It never runs during offline preparation.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import paused_join_pair as consumer


async def run(args) -> int:
    from mcp import ClientSession, StdioServerParameters, stdio_client

    generation = consumer.load(args.profile_preparation / 'sdk-generation.json')
    consumer.require(generation['schema'] == 'xar.jd11.paused-pair.sdk-generation/v1', 'wrong generation schema')
    consumer.require(consumer.check_identity(generation['root_sdk_client']).resolve() == Path(__file__).resolve(), 'SDK client changed')
    consumer.require(consumer.check_identity(generation['hot_controller']).resolve() == Path(consumer.__file__).resolve(), 'consumer changed')
    profile = Path(generation['profile_path'])
    consumer.require(consumer.identity(profile)['sha256'] == generation['profile_sha256'], 'frozen profile changed')
    args.evidence_dir.mkdir(parents=True, exist_ok=False)
    evidence, counter = args.evidence_dir, 0

    def save(name, value):
        nonlocal counter
        counter += 1
        path = evidence / f'mcp-{counter:03d}-{name}.json'
        consumer.write_new(path, value)
        return str(path)

    target, job = generation['target_id'], generation['job_name']
    command = generation['server_command_for_local_sdk_stdio']
    consumer.require(generation.get('server_environment_overrides') == consumer.LOCALE_OVERRIDES,
                     'frozen locale environment override missing')
    consumer.require(command[1:5] == ['-X', 'utf8=0', '-B', str(consumer.REPO / 'ck3_autonomous_player/operator_mcp_server.py')],
                     'server locale startup options missing')
    parameters = StdioServerParameters(command=command[0], args=command[1:], cwd=generation['server_cwd'],
                                       env=dict(os.environ, **generation['server_environment_overrides']))
    save('process-environment', {'server_command': command, 'environment_overrides': generation['server_environment_overrides'],
                                'capture_inherits_operator_environment': True, 'full_environment_logged': False})
    with (evidence / 'operator-server-stderr.log').open('x', encoding='utf-8') as err:
        async with stdio_client(parameters, errlog=err) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=120) as session:
                await session.initialize()
                save('tools', (await session.list_tools()).model_dump(mode='json'))

                async def call(name, arguments):
                    reply = await session.call_tool(name, arguments)
                    raw = reply.model_dump(mode='json')
                    receipt = save(name, {'called_at_utc': datetime.now(timezone.utc).isoformat(),
                                          'arguments': arguments, 'result': raw})
                    consumer.require(not raw.get('is_error', raw.get('isError', False)), 'MCP error: ' + receipt)
                    body = raw.get('structured_content', raw.get('structuredContent'))
                    if body is None:
                        body = json.loads(next(item['text'] for item in raw['content'] if item.get('type') == 'text'))
                    print(json.dumps({'tool': name, 'receipt': receipt, 'result': body.get('result'),
                                      'job_id': body.get('job_id'), 'jobs': body.get('jobs')}, ensure_ascii=False), flush=True)
                    return body

                capabilities = await call('operator_get_capabilities', {})
                consumer.require(capabilities.get('profile_sha256') == generation['profile_sha256'], 'capability profile SHA differs')
                status = await call('operator_get_status', {'target_id': target})
                consumer.require(status.get('identity_matches_profile') is True and not any(status.get('process_gates', {}).values()),
                                 'machine identity or exclusive process gate refused')
                preflight = await call('operator_preflight_job', {'target_id': target, 'job_name': job})
                consumer.require(preflight.get('result') == 'GREEN' and preflight.get('checks')
                                 and all(item is True for item in preflight['checks'].values()), 'operator preflight refused')
                launch = await call('operator_handoff_job', {'target_id': target, 'job_name': job, 'request_id': args.request_id})
                consumer.require(launch.get('result') == 'ACCEPTED' and launch.get('profile_sha256') == generation['profile_sha256']
                                 and (launch.get('job') or {}).get('job_name') == job, 'handoff did not bind frozen job')
                save('handoff-summary', {'run_id': 'ENTRY_ALLOCATION_PENDING', 'handoff': launch})
                controller_args = argparse.Namespace(profile_preparation=args.profile_preparation,
                    evidence_dir=evidence / 'paused-pair-controller', ready_timeout=2700, cleanup_timeout=240)
                controller = asyncio.create_task(asyncio.to_thread(consumer.run_controller, controller_args))
                deadline = time.monotonic() + args.monitor_timeout
                while time.monotonic() < deadline:
                    await asyncio.sleep(10)
                    status = await call('operator_get_status', {'target_id': target})
                    jobs = [item for item in status.get('jobs', []) if item.get('job_name') == job]
                    if jobs and all(item.get('exit_code') is not None or item.get('state') == 'exited' for item in jobs):
                        controller_exit = await controller
                        save('completion', {'status': status, 'controller_exit_code': controller_exit,
                                            'human_video_1x_review': False, 'recorder_requested': False})
                        return 0 if controller_exit == 0 and all(item.get('exit_code') == 0 for item in jobs) else 2
                save('monitor-timeout', {'status': status, 'cleanup_not_inferred': True})
                raise TimeoutError('actual job exit missing; inspect same-owner cleanup before any new attempt')


def main() -> int:
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile-preparation', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--request-id', required=True)
    parser.add_argument('--monitor-timeout', type=float, default=3900)
    args = parser.parse_args()
    consumer.require(args.request_id.strip() and 300 <= args.monitor_timeout <= 3900, 'actual unique request ID and 300..3900s bound required')
    return asyncio.run(run(args))


if __name__ == '__main__':
    raise SystemExit(main())
