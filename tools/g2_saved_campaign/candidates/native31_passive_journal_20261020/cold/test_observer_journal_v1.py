"""Pure fake transport tests; these observations are not real Game evidence."""
from __future__ import annotations
from dataclasses import replace
import copy
import json
import unittest
from typing import Callable
import observer_journal_v1 as r
import native31_mcp_extension_v1 as ext

EXPECTED = r.ExpectedGameV1("fixture-machine", 123, 456, 1, "fixture-pipe", r.NATIVE31_SHA256)
REQUEST = "fixture.query"
WANTED = "failed-command"

def event(seq: int, kind: int) -> dict[str, object]:
    return {"seq": seq, "qpc": seq*100, "thread": 7, "kind": kind, "role": 1,
        "invocation": 3, "identity_epoch": 12, "connection": 1, "attributed": 1,
        "request_id": WANTED, "desired_paused": 0,
        "token": {"pointer": (1<<60)+23, "incarnation": 19},
        "parent": {"pointer": 0, "incarnation": 0}, "caller_rva": 0x123,
        "aux": 0, "qualified": 1, "queue_accepted": 0, "payload_valid": 1,
        "player_bits": 0, "command_paused": 0, "native_sequence": 44,
        "scalar_valid": 1, "game": 0x1000, "jomini": 0x2000,
        "date_bits": 53274624, "paused": 1 if kind == 7 else 0}

def frame(events: list[dict[str, object]] | None = None) -> dict[str, object]:
    items = [event(1,7), event(2,8)] if events is None else events
    return {"type": "command_result", "protocol_version": 1, "request_id": REQUEST,
        "ok": True, "result": {"step": r.STEP, "accepted": True,
        "status": "passive_observation_only", "drain_fence": False,
        "observer_schema": r.SCHEMA,
        "lifetime_coverage": "observed_clone_and_primary_delete_slots_only",
        "scalar_samples_are_snapshots": False, "query_is_tail": True,
        "qpc_frequency": 1000, "snapshot_qpc": 301, "process_id": 123,
        "process_birth": "456", "image_base": 0x140000000, "attached": 1,
        "readable": 1, "newest": len(items), "oldest_retained": 1,
        "returned_count": len(items), "first_returned": 1,
        "coverage_gaps": 0, "lost": 0, "live_registry": 0, "events": items}}

def result_object(value: dict[str, object]) -> dict[str, object]:
    candidate = value["result"]
    assert isinstance(candidate, dict)
    return candidate

class FakeState:
    def __init__(self, reply: dict[str, object] | None, *, pre: int = 1, post: int = 1) -> None:
        self.reply = reply
        self.pre, self.post = pre, post
        self.reads = 0
        self.waits = 0
    def diagnostics(self) -> dict[str, object]:
        self.reads += 1
        generation = self.pre if self.reads == 1 else self.post
        return {"connected": True, "connection_generation": generation,
            "hello": {"pid": 123, "connection_generation": generation}}
    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object] | None:
        self.waits += 1
        return self.reply

class FakeEndpoint:
    pipe_name = "fixture-pipe"
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []
    def send(self, value: dict[str, object]) -> None:
        self.sent.append(copy.deepcopy(value))

class FakeDriver:
    pipe_name = "fixture-pipe"
    def __init__(self) -> None:
        self.endpoint = FakeEndpoint()
        self.state = FakeState(frame())
        self._player_heir_candidate_owner_v1: object = object()

def query(reply: dict[str, object] | None, *, pre: int = 1, post: int = 1,
          expected: r.ExpectedGameV1 = EXPECTED) -> tuple[r.ReadResultV1, FakeEndpoint, FakeState]:
    endpoint = FakeEndpoint()
    state = FakeState(reply, pre=pre, post=post)
    result = r._query_once_v1(endpoint, state, expected=expected, request_id=REQUEST,
        wanted=(WANTED,), timeout_seconds=0.1)
    return result, endpoint, state

class ReaderTests(unittest.TestCase):
    def test_exact_fixed_step_and_positive_pair(self) -> None:
        value, endpoint, state = query(frame())
        self.assertEqual(value.status, "positive_observations_only")
        self.assertEqual(len(value.execute_pairs), 1)
        self.assertEqual(value.execute_pairs[0].elapsed_seconds, 0.1)
        self.assertEqual(value.execute_pairs[0].enter.player_bits, 0)
        self.assertEqual(endpoint.sent, [{"type":"execute_step","protocol_version":1,
            "request_id":REQUEST,"step":r.STEP,"expected_revision":0}])
        self.assertEqual(state.waits,1)
        self.assertEqual(value.credit_days,0)
        self.assertFalse(value.drain_fence)
        self.assertFalse(value.automatic_recovery_allowed)
        self.assertFalse(value.loaded_provider_issued)
        self.assertFalse(value.absence_is_nonexecution_proof)
    def test_retains_original_without_mutation(self) -> None:
        original=frame()
        before=copy.deepcopy(original)
        value, _, _=query(original)
        self.assertEqual(original,before)
        self.assertEqual(value.original_parsed_frame,before)
        original["request_id"]="changed"
        self.assertEqual(value.original_parsed_frame,before)
    def test_timeout_once_no_retry(self) -> None:
        value, endpoint, state=query(None)
        self.assertEqual(value.status,"unavailable")
        self.assertEqual(value.actual_native_requests,1)
        self.assertEqual((len(endpoint.sent),state.waits),(1,1))
    def test_pre_generation_drift_zero_send(self) -> None:
        value, endpoint, state=query(frame(),pre=2)
        self.assertEqual(value.actual_native_requests,0)
        self.assertEqual((len(endpoint.sent),state.waits),(0,0))
    def test_post_generation_drift_one_send(self) -> None:
        value, endpoint, _=query(frame(),post=2)
        self.assertEqual(value.status,"unavailable")
        self.assertEqual(len(endpoint.sent),1)
        self.assertIsNotNone(value.original_parsed_frame)
    def test_wrong_native_sha_zero_send(self) -> None:
        with self.assertRaises(ValueError):
            query(frame(),expected=replace(EXPECTED,native_dll_sha256="0"*64))
    def test_pid_birth_mismatch_unavailable(self) -> None:
        for key, bad in [("process_id",124),("process_birth","457"),
                         ("process_birth","2026-10-20T00:00:00")]:
            with self.subTest(key=key,bad=bad):
                item=frame();result_object(item)[key]=bad
                value, endpoint,_=query(item)
                self.assertEqual(value.status,"unavailable")
                self.assertEqual(len(endpoint.sent),1)
    def test_envelope_and_contract_mutants(self) -> None:
        for target,key,bad in [
            ("frame","protocol_version",True),("frame","request_id","other"),
            ("frame","ok",1),("result","accepted",1),("result","attached",True),
            ("result","readable",0),("result","drain_fence",True),
            ("result","scalar_samples_are_snapshots",True),
            ("result","query_is_tail",False),("result","qpc_frequency",0),
            ("result","image_base",0),("result","returned_count",3),
            ("result","first_returned",2),("result","oldest_retained",2),
            ("result","observer_schema","wrong")]:
            with self.subTest(key=key,bad=bad):
                item=frame()
                (item if target=="frame" else result_object(item))[key]=bad
                self.assertEqual(query(item)[0].status,"unavailable")
    def test_event_strict_mutants(self) -> None:
        for key,bad in [("seq",2),("kind",11),("qpc",-1),("thread",True),
            ("attributed",True),("qualified",2),("request_id",""),
            ("player_bits",1<<32),("game",0)]:
            with self.subTest(key=key):
                first=event(1,7); first[key]=bad
                self.assertEqual(query(frame([first,event(2,8)]))[0].status,"unavailable")
    def test_oversize_ring_rejected(self) -> None:
        self.assertEqual(query(frame([event(n+1,7) for n in range(65)]))[0].status,"unavailable")
    def test_pair_requires_all_identity_and_payload_fields(self) -> None:
        for key,bad in [("connection",2),("identity_epoch",13),("invocation",4),
            ("role",2),("native_sequence",45),("player_bits",1),
            ("command_paused",1),("desired_paused",1),("payload_valid",0),
            ("qualified",0),("attributed",0)]:
            with self.subTest(key=key):
                last=event(2,8);last[key]=bad
                value=query(frame([event(1,7),last]))[0]
                self.assertEqual(value.status,"positive_observations_only")
                self.assertEqual(value.execute_pairs,())
    def test_pair_requires_incarnation(self) -> None:
        last=event(2,8)
        last["token"]={"pointer":(1<<60)+23,"incarnation":20}
        self.assertEqual(query(frame([event(1,7),last]))[0].execute_pairs,())
    def test_old_connection_not_attributed_to_current(self) -> None:
        items=[event(1,7),event(2,8)]
        for item in items:item["connection"]=2
        value=query(frame(items))[0]
        self.assertEqual(len(value.execute_pairs),1)
        self.assertFalse(value.protocol_connection_binding_verified)
        self.assertFalse(value.current_failed_request_completion_proven)
        payload=r.result_payload_v1(value)
        self.assertFalse(payload["protocol_connection_binding_verified"])
        self.assertFalse(payload["current_failed_request_completion_proven"])
        raw=payload["original_parsed_frame_json"]
        assert isinstance(raw,str)
        self.assertIn('"connection":2',raw)
    def test_orphan_tail_and_gaps_never_prove_absence(self) -> None:
        for items in [[],[event(1,8)],[event(1,7)]]:
            item=frame(items)
            result_object(item)["coverage_gaps"]=5
            result_object(item)["lost"]=7
            value=query(item)[0]
            self.assertEqual(value.execute_pairs,())
            self.assertFalse(value.drain_fence)
            self.assertFalse(value.absence_is_nonexecution_proof)
    def test_nonmonotonic_qpc_no_duration_claim(self) -> None:
        last=event(2,8);last["qpc"]=99
        value=query(frame([event(1,7),last]))[0]
        self.assertIsNone(value.execute_pairs[0].elapsed_seconds)
    def test_output_u64_text_and_original_json(self) -> None:
        value=query(frame())[0]
        payload=r.result_payload_v1(value)
        self.assertEqual(payload["game_creation_filetime"],"456")
        raw=payload["original_parsed_frame_json"]
        assert isinstance(raw,str)
        self.assertEqual(json.loads(raw),frame())
        self.assertFalse(payload["absence_is_nonexecution_proof"])
    def test_bad_request_context_rejected(self) -> None:
        for expected in [replace(EXPECTED,pid=True),replace(EXPECTED,creation_filetime=0),
            replace(EXPECTED,connection_generation=0),replace(EXPECTED,pipe_name="other")]:
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError):query(frame(),expected=expected)
    def test_registration_is_zero_native_and_fixed_zero_arg_tool(self) -> None:
        driver=FakeDriver()
        callbacks: list[Callable[[],dict[str,object]]]=[]
        def register(callback: Callable[[],dict[str,object]]) -> object:
            callbacks.append(callback)
            return callback
        callback=ext.register_native31_journal_v1(register,
            owner=driver._player_heir_candidate_owner_v1,driver=driver,machine_id="fixture")
        self.assertEqual(callbacks,[callback])
        self.assertEqual(callback.__name__,"ck3_observe_native31_time_command_journal_v1")
        self.assertEqual(driver.endpoint.sent,[])
        self.assertEqual(driver.state.reads,0)
    def test_wrong_registration_owner_rejected_zero_native(self) -> None:
        driver=FakeDriver()
        def register(callback: Callable[[],dict[str,object]]) -> object:return callback
        with self.assertRaises(ValueError):
            ext.register_native31_journal_v1(register,owner=object(),driver=driver,machine_id="fixture")
        self.assertEqual(driver.endpoint.sent,[])
    def test_wrapper_requires_actual_issued_dto_before_native(self) -> None:
        driver=FakeDriver()
        with self.assertRaises(ValueError):
            r.read_from_source28_owner_once_v1(object(),driver,machine_id="fixture",request_id=REQUEST)
        self.assertEqual(driver.endpoint.sent,[])

if __name__=="__main__":unittest.main()
