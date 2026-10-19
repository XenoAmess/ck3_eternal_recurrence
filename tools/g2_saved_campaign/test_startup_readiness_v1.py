"""One real readiness-function fixture with explicit local MCP and relay doubles."""
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from startup_readiness_v1 import LOADING_ERROR, startup_readiness_call


class StartupReadinessOrderTests(unittest.IsolatedAsyncioTestCase):
    async def test_loading_then_semantic_completion_uses_only_injected_relay(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary);queue_root=root/'queue';outbox=root/'responses'
            queue_root.mkdir();outbox.mkdir();events=[]
            semantic='ck3_take_semantic_snapshot_private_v1'
            request={'sequence':198,'tool':semantic,'arguments':{}}
            request_path=queue_root/'0198-request.json'
            request_path.write_text(json.dumps(request))

            def atomic(path,value,*,replace=False,limit=None):
                with Path(path).open('w' if replace else 'x',encoding='utf-8') as stream:
                    json.dump(value,stream)

            class Queue:
                cold_readiness_verified=False
                checkpoint_bootstrap_verified=False
                initial_camera=None
                next_sequence=198
                def check_before(self,tool,arguments):events.append('check_before')
                def guard(self):events.append('guard')
                def call_budget(self,tool):return 10
                def check_after(self,tool,arguments,body):
                    events.append('check_after')
                    self.cold_readiness_verified=True
                def consume_sequence(self,original):
                    events.append('consume_sequence')
                    assert original is request and self.next_sequence==198
                    self.next_sequence+=1

            class Result:
                def __init__(self,value):self.value=value
                def model_dump(self,*,mode):return self.value

            class LocalSession:
                calls=0
                async def call_tool(self,tool,arguments,*,read_timeout_seconds):
                    self.calls+=1;events.append('local_mcp_'+str(self.calls))
                    assert tool==semantic and arguments=={} and read_timeout_seconds==10
                    if self.calls==1:
                        return Result({'is_error':True,'result_type':'complete','structured_content':None,
                            'content':[{'type':'text','text':LOADING_ERROR}]})
                    return Result({'is_error':False,'result_type':'complete',
                        'structured_content':{'status':'fixture_semantic_complete'}})

            queue=Queue();session=LocalSession();publications=[]
            def decoded(row):
                events.append('decoded')
                assert row['result']['is_error'] is False
                return row['result']['structured_content']
            def relay(response,projection):
                events.append('injected_current_provider_relay')
                assert queue.cold_readiness_verified and queue.next_sequence==199
                assert response.exists() and not (queue_root/'0198-after-result.json').exists()
                assert projection['result']['structured_content']['status']=='fixture_semantic_complete'
                publications.append(response)
            async def sleep(seconds):
                events.append('loading_sleep')
                assert seconds==5
            env={'SEMANTIC':semantic,'Q':queue_root,'OUTBOX':outbox,'N':root,'atomic':atomic,
                'now':lambda:datetime.now(timezone.utc),'decoded':decoded,
                'display_projection':lambda row,body:row}
            body,response=await startup_readiness_call(queue,session,request,request_path,env,
                relay_compact=relay,sleep=sleep)
            self.assertEqual(events,['check_before','guard','local_mcp_1','loading_sleep',
                'guard','local_mcp_2','decoded','check_after','consume_sequence','injected_current_provider_relay'])
            self.assertEqual(session.calls,2)
            self.assertEqual(publications,[response])
            self.assertEqual(queue.next_sequence,199)
            self.assertEqual(body,{'status':'fixture_semantic_complete'})
            self.assertEqual(json.loads((queue_root/'0198-after-result.json').read_text())['loading_attempts'],1)
            self.assertEqual(len(list(outbox.glob('*-1-result.json'))),1)


if __name__=='__main__':unittest.main()
