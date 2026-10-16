"""Root-only single-owner readonly capture after native source/build admission.

Uses the existing registered ck3_inspect_gui_window_tree_v1(military) tool.
It creates one native endpoint: do not run alongside Root's existing endpoint.
No open/click/evaluate/resume action or retry is implemented.
"""
from __future__ import annotations
import argparse,asyncio,datetime as dt,hashlib,json,os,sys
from pathlib import Path

def _json_value(value):
    """Retain MCP error content even when structured_content is absent."""
    if hasattr(value, 'model_dump'):
        return value.model_dump(mode='json')
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if all(hasattr(value, key) for key in ('is_error', 'structured_content', 'content')):
        return {'is_error': _json_value(value.is_error),
                'structured_content': _json_value(value.structured_content),
                'content': _json_value(value.content)}
    return repr(value)

async def capture(args):
    repo=args.repo_root.resolve();sys.path.insert(0,str(repo/'ck3_autonomous_player/src'));sys.path.insert(0,str(repo))
    from tools.ck3_live_run_id import current_machine_id
    machine=current_machine_id()
    if machine!=args.expected_machine_id:raise ValueError('capture machine changed')
    from mcp import Client
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.mcp_server import create_server
    driver=NativeHeadlessGameplayDriver(pipe_name=args.pipe_name,state_dir=args.state_dir)
    try:
        async with Client(create_server(driver)) as client:
            response=await client.call_tool('ck3_inspect_gui_window_tree_v1',{'window_kind':'military'})
        value=response.structured_content
        failed=response.is_error or type(value) is not dict
        record={'machine_id':machine,'observed_at':dt.datetime.now(dt.UTC).isoformat(),
            'source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'tool':'ck3_inspect_gui_window_tree_v1','arguments':{'window_kind':'military'},
            'tool_calls':1,'response_is_error':response.is_error,'body':value,
            'error_envelope':_json_value(response) if failed else None,
            'actual_clicks':0,'native_expression_evaluations':0}
        b=(json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode()
        if len(b)>2*1024*1024:raise ValueError('capture exceeds declared 2MiB output budget')
        with args.output.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        if response.is_error or type(value) is not dict:raise ValueError('actual military tree failed; original response retained')
        frame=value.get('refill_receiver_frame_12004') or {}
        expected={'game_pid':args.expected_game_pid,'connection_generation':args.expected_connection_generation,
            'native_revision':args.expected_native_revision,'played_character_full_id':args.expected_played_full_id,'date_raw':args.expected_date_raw}
        if any(frame.get(k)!=v for k,v in expected.items()) or not value.get('refill_receiver_public_binding_12004'):
            raise ValueError('capture lacks expected actual frame; response retained')
        found=[]
        for w in value.get('widgets',[]):
            for cb in w.get('standard_click_binding_12004',{}).get('callbacks',[]):
                e=cb.get('indirect_target_3aa30e0',{}).get('expression_3a9f960',{})
                if 'receiver_entry_candidates_12004' in e:found.append((w['child_path'],cb['index']))
        if not found:raise ValueError('no source-bound candidate leaf observed; response retained')
        print(json.dumps({'output':str(args.output),'sha256':hashlib.sha256(b).hexdigest(),'candidate_widgets':found,'actual_clicks':0}))
    finally:driver.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--enable-root-capture',action='store_true')
    p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--state-dir',type=Path,required=True)
    p.add_argument('--pipe-name',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expected-machine-id',required=True)
    for key in ('game-pid','connection-generation','native-revision','played-full-id','date-raw'):
        p.add_argument('--expected-'+key,type=int,required=True)
    args=p.parse_args()
    if not args.enable_root_capture:p.error('Root must admit the frozen build and sole live endpoint before enabling capture')
    asyncio.run(capture(args))

if __name__=='__main__':main()
