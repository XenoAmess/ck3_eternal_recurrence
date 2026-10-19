"""Current relay injection over the actual C7 resident-call I/O shape."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace, ModuleType
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
from g2_saved_campaign.p51_resident_successor_adoption_v1 import (
    bind_handoff_relay_v1, bind_queue_relay_v1,
)

# Verbatim resident factory from frozen C7 handoff af114b3088ca847fdd14affe40f1c942f191fc0c2cac81e45d431eda64e070e1.
# This fixture performs only local fake-session I/O; it does not load a runtime.
RESIDENT_IO = '''def _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth):
    from root_p37_overlay_relay import relay_compact, error_projection
    def verify():
        queue.guard()
        require(birth_reader(pid) == birth, "original Game kernel birth changed")

    async def call(tool, arguments):
        verify()
        require(tool in {env["SEMANTIC"], AUTO, CAPS, SAVE,
                         "ck3_query_current_timeline_blocker_context_v1", "ck3_resume_successor_ui_v1",
                         "ck3_continue_death_succession_modal_v1"},
                "non-handoff tool forbidden")
        require(not env["pending_request_paths"](
            env["INBOX"], env["OUTBOX"], queue.next_sequence,
            held_control=queue.held_control), "another pending request owns the queue")
        request = {"sequence": queue.next_sequence, "tool": tool, "arguments": arguments,
                   "source": SCHEMA + "; unique request; no original action replay"}
        path = env["INBOX"] / f"{request['sequence']:04d}-1-result.json"
        response = env["OUTBOX"] / path.name
        require(not path.exists() and not response.exists()
                and not (env["Q"] / f"INFLIGHT-{request['sequence']:04d}.json").exists(),
                "handoff request number already attempted")
        env["atomic"](path, request, limit=16384)
        sequence = queue.consume_sequence(request)
        context = {**request, "request_file": str(path), "at_utc": env["now"]().isoformat(),
                   "replay_allowed": False, "automatic_succession": True}
        env["atomic"](env["N"] / "CURRENT-REQUEST-P37.json", context, replace=True, limit=16384)
        env["atomic"](env["Q"] / f"INFLIGHT-{sequence:04d}.json", context, limit=16384)
        env["atomic"](env["Q"] / f"{sequence:04d}-before-action.json", context, limit=16384)
        audit["calls"].append({"sequence": sequence, "tool": tool, "response": str(response),
                               "status": "attempted"})
        env["atomic"](audit_path, audit, replace=True, limit=65536)
        started, mono = env["now"]().isoformat(), time.monotonic()
        try:
            reply = await session.call_tool(tool, arguments,
                                           read_timeout_seconds=queue.call_budget(tool))
            row = {"request": request, "started_at_utc": started,
                   "ended_at_utc": env["now"]().isoformat(),
                   "elapsed_seconds": time.monotonic() - mono,
                   "result": reply.model_dump(mode="json")}
        except Exception as error:
            row = {"request": request, "started_at_utc": started,
                   "ended_at_utc": env["now"]().isoformat(),
                   "elapsed_seconds": time.monotonic() - mono,
                   "client_error": repr(error), "replay_allowed": False}
        env["atomic"](response, row, limit=env["REPLY_RESERVE"])
        queue.current_attempt = {"request": request, "row": row, "response": str(response)}
        audit["calls"][-1].update(status="received")
        env["atomic"](audit_path, audit, replace=True, limit=65536)
        try:
            body = env["decoded"](row)
        except Exception:
            relay_compact(response, error_projection(row))
            raise
        projected = env["display_projection"](row, body)
        relay_compact(response, projected)
        env["atomic"](env["N"] / "p37-display-responses" / response.name, projected, limit=16384)
        env["atomic"](env["Q"] / f"{sequence:04d}-after-result.json", {
            "at_utc": row["ended_at_utc"], "request": str(path), "response": str(response),
            "tool": tool, "actual_status": body.get("status"),
            "automatic_succession": True}, limit=16384)
        verify()
        return body, response

    return call
'''

HANDOFF_HEAD = '''async def automatic_handoff(queue, session, state, *, original_before, event, env,
                            birth_reader=None):
    from root_p37_overlay_relay import relay_compact, error_projection
    call = _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth)
    return call

'''


def require(ok, message):
    if not ok:
        raise ValueError(message)


class RelayBindingTests(unittest.IsolatedAsyncioTestCase):
    async def run_resident(self, fail_relay=False):
        source = bind_handoff_relay_v1(HANDOFF_HEAD + RESIDENT_IO)
        self.assertNotIn('from root_p37_overlay_relay import', source)
        namespace = dict(Path=Path, time=time, require=require, SCHEMA='fixture',
                         AUTO='AUTO', CAPS='CAPS', SAVE='SAVE')
        exec(compile(source, '<bound-actual-resident-io>', 'exec'), namespace)
        events, audit = [], {'calls': []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('inbox', 'outbox', 'queue'):
                (root / name).mkdir()
            audit_path = root / 'queue/AUDIT.json'
            queue = SimpleNamespace(next_sequence=3851, held_control=None, current_attempt=None,
                                    guard=lambda: events.append('guard'), call_budget=lambda tool: 5)
            def consume(request):
                sequence = queue.next_sequence
                queue.next_sequence += 1
                return sequence
            queue.consume_sequence = consume
            def atomic(path, value, **options):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding='utf-8')
                events.append('write:' + path.name + (':' + audit['calls'][-1]['status']
                              if path == audit_path else ''))
            body = {'status': 'observed', 'date_raw': 53186856}
            async def call_tool(tool, arguments, **options):
                events.append('session_call')
                return SimpleNamespace(model_dump=lambda **kwargs: {'isError': False, 'body': body})
            def current_relay(path, projection):
                events.append('current_relay')
                self.assertEqual(json.loads(path.read_text())['result']['body'], body)
                self.assertEqual(queue.current_attempt['response'], str(path))
                self.assertEqual(audit['calls'][-1]['status'], 'received')
                self.assertFalse((root / 'queue/3851-after-result.json').exists())
                if fail_relay:
                    raise ValueError('real display failure retained')
            old = ModuleType('root_p37_overlay_relay')
            def poison(*args):
                raise AssertionError('implicit old relay invoked')
            old.relay_compact = old.error_projection = poison
            from datetime import datetime, timezone
            env = dict(SEMANTIC='SEM', INBOX=root/'inbox', OUTBOX=root/'outbox', Q=root/'queue', N=root,
                       atomic=atomic, now=lambda: datetime.now(timezone.utc), pending_request_paths=lambda *a, **k: [],
                       decoded=lambda row: row['result']['body'], display_projection=lambda row, body: body,
                       REPLY_RESERVE=65536)
            with patch.dict(sys.modules, {'root_p37_overlay_relay': old}):
                factory = namespace['_resident_make_call']
                with self.assertRaises(TypeError):
                    factory(queue, None, env, audit, audit_path, lambda pid: 123, 42, 123)
                call = factory(queue, SimpleNamespace(call_tool=call_tool), env, audit, audit_path,
                               lambda pid: 123, 42, 123,
                               relay_compact=current_relay, error_projection=lambda row: row)
                if fail_relay:
                    with self.assertRaisesRegex(ValueError, 'display failure'):
                        await call('SEM', {})
                    self.assertFalse((root/'queue/3851-after-result.json').exists())
                else:
                    observed, _ = await call('SEM', {})
                    self.assertEqual(observed, body)
                    self.assertGreater(events.index('write:3851-after-result.json'), events.index('current_relay'))
            self.assertEqual(events.count('session_call'), 1)
            self.assertEqual(queue.next_sequence, 3852)
            self.assertLess(events.index('write:3851-1-result.json'), events.index('write:AUDIT.json:received'))
            self.assertLess(events.index('write:AUDIT.json:received'), events.index('current_relay'))

    async def test_current_relay_after_durable_result_before_after_result(self):
        await self.run_resident()

    async def test_display_failure_preserves_original_without_replay_or_after_result(self):
        await self.run_resident(fail_relay=True)

    def test_both_queue_paths_require_explicit_generation_relay(self):
        source = '''class Queue:
    async def full_loop(self, session, state):
        if True:
            if True:
                from root_p37_automatic_natural_succession_handoff import automatic_handoff
                state = await automatic_handoff(self, session, state,
                    original_before=before, event=event, env=globals())
        if state.get("resident_successor_ui_pending") is not None:
            from p51_resident_successor_adoption_v1 import finish_deferred_ui_v1
            state = await finish_deferred_ui_v1(self, session, state, globals())
'''
        with self.assertRaises(TypeError):
            bind_queue_relay_v1(source)
        with self.assertRaisesRegex(ValueError, 'explicit current relay'):
            bind_queue_relay_v1(source, relay_module='not-a-module;bad')
        bound = bind_queue_relay_v1(source, relay_module='root_p37c99_overlay_relay')
        nodes = list(ast.walk(ast.parse(bound)))
        imports = [node for node in nodes if isinstance(node, ast.ImportFrom)
                   and node.module == 'root_p37c99_overlay_relay']
        self.assertEqual(len(imports), 2)
        calls = [node for node in nodes if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id in {'automatic_handoff', 'finish_deferred_ui_v1'}]
        self.assertEqual(len(calls), 2)
        for call in calls:
            self.assertTrue({'relay_compact', 'error_projection'} <= {item.arg for item in call.keywords})


if __name__ == '__main__':
    unittest.main()
