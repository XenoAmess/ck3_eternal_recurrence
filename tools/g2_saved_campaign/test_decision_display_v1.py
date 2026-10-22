"""Display producer/consumer regressions; no Game, SDK RPC, OBS or desktop."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import unittest

import decision_display_contract_v1 as contract
import decision_observation_feed as feed
from decision_text_view import AudienceState, result_text
from prepare_decision_display_runtime_v1 import transform_feed, transform_queue


STEP = "advance-route-contact-window-v1-234881394-to-2627-days-3-h-2-117440697-285212941"


def plan_row(step: str, *, callback: int | None = None, reason: str = "按当前材料选择行动。") -> contract.Record:
    request: contract.Record = {"tool": "root_before_auto_turn_submit", "parent_sequence": 143}
    if callback is not None:
        request["callback_index"] = callback
    actual: contract.Record = {"selected_step": step, "phase": "native_war_moving_contact_before_strength_progress",
                               "reason": reason}
    return {"source_namespace": "p37-responses", "request": request, "result": {"is_error": False, "structured_content": {
        "status": "planned", "selected_step": step, "plan": feed.compact_plan(actual)}}}


def result_row(step: str, status: str, *, sequence: int = 143) -> contract.Record:
    return {"source_namespace": "p37-responses", "request": {"tool": "ck3_auto_turn", "sequence": sequence},
            "result": {"is_error": False, "structured_content": {
                "selected_step": step, "result": {"status": status}}}}


class DisplayContractTests(unittest.TestCase):
    def test_actual_shape_english_route_reason_survives_both_projection_paths(self) -> None:
        english = ("same-frame complete hostile timelines admit 3 days for the sole moving army; "
                   "the watched native clock stops on actual arrival, target, combat, retreat or pause changes")
        row = plan_row(STEP, reason=english)
        first = AudienceState()
        first.consume(json.loads(json.dumps(row)))
        self.assertIn("最多推进3天", first.render())
        self.assertIn("2支敌军", first.render())
        self.assertIn("撤退或暂停变化", first.render())
        self.assertNotIn("处理当前游戏事务", first.render())
        body = contract.maybe_record(contract.maybe_record(row["result"])["structured_content"])
        projected = contract.project_result({"request": {"tool": "ck3_auto_turn", "sequence": 143}}, body)
        second = AudienceState()
        second.consume(projected)
        self.assertIn("最多推进3天", second.render())
        self.assertIn("撤退或暂停变化", second.render())

    def test_rich_war_reason_preserved_and_stale_identity_rejected(self) -> None:
        actual = {"selected_step": "move-army-1", "phase": "native_war_route",
                  "war_decision_presentation_v1": {"selected_step": "move-army-1", "phase": "native_war_route",
                      "reason": "我军2400，敌军3100。雇佣180金，预留150金；抵达未知，兵数不代表胜率。"}}
        compact = feed.compact_plan(actual)
        card = contract.parse_card(compact[contract.DETAIL], step="move-army-1", phase="native_war_route")
        self.assertIn("预留150金", " ".join(card.rationale))
        stale = copy.deepcopy(actual)
        presentation = contract.record(stale["war_decision_presentation_v1"])
        presentation["selected_step"] = "move-army-2"
        stale["war_decision_presentation_v1"] = presentation
        self.assertNotIn("预留150金", str(feed.compact_plan(stale)[contract.DETAIL]))

    def test_exact_wire_fields_null_semantics_roundtrip_and_identity(self) -> None:
        card = contract.project_card({"selected_step": "ordinary-sway-opportunity-v1", "reason": "按当前目标轮转。"})
        wire = card.wire()
        self.assertIsNone(wire["alternatives"])
        self.assertEqual(card, contract.parse_card(json.loads(json.dumps(wire)), step=card.selected_step, phase=None))
        empty = dict(wire)
        empty["alternatives"] = []
        self.assertEqual(contract.parse_card(empty, step=card.selected_step, phase=None).alternatives, ())
        invalids = [None, {key: value for key, value in wire.items() if key != "risks"},
                    {**wire, "unknown_alias": []}, {**wire, "facts": None},
                    {**wire, "facts": ("tuple-is-not-wire",)}, {**wire, "action": 0},
                    {**wire, "selected_step": "wrong"}, {**wire, "schema": "future"}]
        for invalid in invalids:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                contract.parse_card(invalid, step=card.selected_step, phase=None)
        for wrong_integer in (True, 1.0, "1", 2**53):
            with self.subTest(integer=wrong_integer), self.assertRaises(ValueError):
                contract.exact_int(wrong_integer, "sequence")

    def test_missing_detail_legacy_and_explicit_invalid_unavailable(self) -> None:
        row = plan_row("life-advance")
        body = contract.maybe_record(contract.maybe_record(row["result"])["structured_content"])
        plan = contract.record(body["plan"])
        plan.pop(contract.DETAIL)
        body["plan"] = plan
        row["result"] = {"structured_content": body}
        view = AudienceState()
        view.consume(row)
        self.assertNotIn("详情暂不可用", view.render())
        plan[contract.DETAIL] = None
        view.consume(row)
        self.assertIn("详情暂不可用", view.render())

    def test_ack_generic_return_unknown_failure_and_independent_postcondition(self) -> None:
        self.assertIn("等待独立", result_text({"status": "submitted"}))
        self.assertIn("后验仍待", result_text({"status": "executed"}))
        for status in ("failed", "rejected", "blocked"):
            self.assertIn("仍未知", result_text({"status": status}))
            self.assertNotIn("尚未执行", result_text({"status": status}))
        self.assertIn("已确认本次未提交", result_text({"status": "blocked",
            "failure_stage": "pre_submit", "business_submitted": False}))
        self.assertIn("原提交结果仍未确认", result_text({"status": "observed_after_native_error"}))
        self.assertIn("独立后验已确认", result_text({"status": "executed", "action_request_id": "fixture-action", "postcondition": {
            "status": "verified", "independent_readback": True, "source_observation": "actual-bound-receipt", "action_request_id": "fixture-action"}}))

    def test_callbacks_merge_only_same_step_query_does_not_evict_business(self) -> None:
        view = AudienceState()
        view.consume(plan_row("move-army-1", callback=1))
        view.consume(plan_row("raise-troops-default", callback=2))
        view.consume(result_row("raise-troops-default", "executed"))
        self.assertEqual(len(view.events), 2)
        self.assertIn("尚未提交", view.events[0].result)
        self.assertIn("后验仍待", view.events[1].result)
        for sequence in range(144, 150):
            view.consume(result_row("query-army-strengths-v1", "available", sequence=sequence))
        self.assertEqual(len(view.events), 2)
        self.assertIn("集结军队", view.render())
        self.assertIn("只读局势信息已读回", view.render())
        with self.assertRaises(ValueError):
            view.consume({"request": {"tool": "ck3_auto_turn", "sequence": True}})

    def test_zero_quote_is_kept_and_bool_not_displayed_as_money(self) -> None:
        actual = {"selected_step": "private-submit-player-construction-v1",
                  "construction_private_query": {"candidate": {"stock_gold_cost_raw": 0}}}
        self.assertIn("0.00000金", str(feed.compact_plan(actual)[contract.DETAIL]))
        query = contract.record(actual["construction_private_query"])
        candidate = contract.record(query["candidate"])
        candidate["stock_gold_cost_raw"] = True
        query["candidate"] = candidate
        actual["construction_private_query"] = query
        self.assertNotIn("0.00000金", str(feed.compact_plan(actual)[contract.DETAIL]))

    def test_optional_producer_failures_soften_in_both_private_paths(self) -> None:
        queue = b'''def compact_plan(plan):
    return {key: plan[key] for key in ("prewar_force_admission",) if key in plan}
def display_projection(row, body):
    # raw response retained
    return {"army_strengths": []}
'''
        private = b'''def publish_before_submit(observation):
    actual = observation.get("plan")
    if actual.get("selected_step") != observation.get("selected_step"):
        raise ValueError("actual action identity differs")
    plan = dict(actual)
    plan["event_choice_utility"] = {}
    stamp = "clock"
    row = {"plan": plan}
    return row
'''
        q: dict[str, object] = {}
        f: dict[str, object] = {"N": Path("/synthetic-runtime")}
        exec(compile(transform_queue(queue), "<private-result>", "exec"), q)
        exec(compile(transform_feed(private), "<private-callback>", "exec"), f)
        before, compact, result = f["publish_before_submit"], q["compact_plan"], q["display_projection"]
        self.assertTrue(callable(before) and callable(compact) and callable(result))
        if not callable(before) or not callable(compact) or not callable(result):
            raise AssertionError("compiled display producers missing")
        step = "private-submit-player-construction-v1"
        huge = json.loads(json.dumps({"candidate": {"stock_gold_cost_raw": 10**400}}))
        card = contract.DisplayCard(step, None, "construction", "选择本项工程", None, (),
                                    tuple("中" * 1600 for _ in range(8)), None, (), ())
        invalids: list[contract.Record] = [{"war_decision_presentation_v1": {1: "bad"}},
                    {"war_decision_presentation_v1": []},
                    {"war_decision_presentation_v1": {"renamed_reason": "bad"}},
                    {"construction_private_query": huge}, {contract.DETAIL: {"schema": "future"}},
                    {contract.DETAIL: card.wire()}]
        for extra in invalids:
            with self.subTest(optional=tuple(extra)):
                actual = {"selected_step": step, "reason": "保留实际旧理由。", **extra}
                shared = feed.compact_plan(actual)
                callback = contract.record(before({"selected_step": step, "plan": actual}))
                projected = contract.record(compact(actual))
                for value in (shared, contract.record(callback["plan"]), projected):
                    self.assertEqual(value["selected_step"], step)
                    self.assertEqual(value["reason"], "保留实际旧理由。")
                    self.assertIsNone(value[contract.DETAIL])
                    self.assertIn(contract.UNAVAILABLE, value)
                    self.assertLess(len(json.dumps(value, ensure_ascii=False).encode()), 12000)
                receipt = contract.record(result({"request": {"tool": "ck3_auto_turn", "sequence": 3}},
                    {"selected_step": step, "plan": actual, "result": {"status": "executed"}}))
                data = contract.record(contract.record(receipt["result"])["structured_content"])
                self.assertNotEqual(contract.outcome(data).stage, "verified")
        with self.assertRaises(ValueError):
            before({"selected_step": "different", "plan": {"selected_step": step}})
        wrong_steps: tuple[object, ...] = (True, 1.0, [], {})
        for invalid_step in wrong_steps:
            with self.subTest(identity=invalid_step), self.assertRaises(ValueError):
                compact({"selected_step": invalid_step, **invalids[0]})

    def test_optional_result_rows_and_budget_degrade_without_claiming_success(self) -> None:
        optional_rows: tuple[contract.Record, ...] = ({"active_wars": [{1: "bad"}]},
                         {"postcondition": {1: "bad"}},
                         {"army_strengths": [{"army_id": "x" * 20000}]})
        for optional in optional_rows:
            projected = contract.project_result({"request": {"tool": "ck3_auto_turn", "sequence": 3}},
                {"selected_step": "move-army-1", "result": {"status": "executed", **optional}})
            body = contract.record(contract.record(projected["result"])["structured_content"])
            self.assertIn(contract.UNAVAILABLE, body)
            self.assertEqual(contract.outcome(body).stage, "unknown")
            self.assertLess(len(json.dumps(projected).encode()), 16384)
        with self.assertRaises(ValueError):
            contract.project_result([], {})
        with self.assertRaises(ValueError):
            contract.project_result({}, {"selected_step": True})

    def test_gold_uses_exact_finite_native_int64_without_float_conversion(self) -> None:
        actual = {"selected_step": "private-submit-player-construction-v1",
                  "construction_private_query": {"candidate": {"stock_gold_cost_raw": 2**63 - 1}}}
        card = contract.project_card(actual)
        self.assertIn("92233720368547.75807金", " ".join(card.costs))

    def test_legacy_frontend_bookmark_display_is_preserved(self) -> None:
        view = AudienceState()
        view.consume({"request": {"tool": "ck3_select_bookmark", "sequence": 1},
                      "result": {"structured_content": {"status": "executed"}}})
        self.assertIn("选择开局角色", view.render())
        self.assertIn("1066", view.render())

    def test_long_names_drop_secondary_detail_keep_current_risks_and_outcome(self) -> None:
        card = contract.DisplayCard(
            "move-army-long", "native_war_route", "war", "调整军队前往" + "长名称" * 30,
            "目标长名称" * 30, ("本次局势" * 40,), ("当前比较理由" * 180,),
            ("其他方案" * 60,), ("工程与战争报价" * 30,),
            ("当前失地风险" * 25, "雇佣抵达未知" * 25))
        row = plan_row(card.selected_step)
        body = contract.maybe_record(contract.maybe_record(row["result"])["structured_content"])
        body["plan"] = {"selected_step": card.selected_step, "phase": card.phase,
                        contract.DETAIL: card.wire()}
        row["result"] = {"structured_content": body}
        view = AudienceState()
        view.consume(row)
        rendered = view.render()
        self.assertLessEqual(len(rendered.splitlines()), 36)
        plain = rendered.replace("\n", "")
        for risk in card.risks:
            self.assertIn(risk, plain)
        self.assertIn("计划已形成，尚未提交", plain)

    def test_future_private_runtime_transform_changes_only_display_functions(self) -> None:
        queue = b'''def compact_plan(plan):
    return {key: plan[key] for key in ("reason", "prewar_force_admission") if key in plan}
def display_projection(row, body):
    # raw response retained
    return {"army_strengths": []}
def send_native():
    return "unchanged actual command"
'''
        updated = transform_queue(queue)
        self.assertIn(b"project_plan", updated)
        self.assertIn(b"project_result", updated)
        self.assertEqual(ast.dump(ast.parse(queue).body[2]), ast.dump(ast.parse(updated).body[2]))
        private = b'''def publish_before_submit(observation):
    actual = observation.get("plan")
    plan = {"selected_step": actual["selected_step"]}
    plan["event_choice_utility"] = {}
    stamp = "clock"
    row = {"request": {}}
    return plan
def unchanged():
    return 42
'''
        changed = transform_feed(private)
        self.assertIn(b"project_plan(display_actual)", changed)
        self.assertIn(b"observation = record(observation)", changed)
        self.assertIn(b'row["source_namespace"] = (N / "p37-responses").name', changed)
        with self.assertRaises(ValueError):
            transform_feed(changed)
        self.assertEqual(ast.dump(ast.parse(private).body[1]), ast.dump(ast.parse(changed).body[1]))
        with self.assertRaises(ValueError):
            transform_queue(updated)
        with self.assertRaises(ValueError):
            transform_feed(b"def publish_before_submit(observation):\n    return None\n")




class DisplayIdentityBoundaryTests(unittest.TestCase):
    """Identity is never shortened by a presentation/prose limit."""

    @staticmethod
    def _queue_compact(actual: object) -> contract.Record:
        import os
        root = os.environ.get("XAR_IDENTITY_PRIVATE_RUNTIME_ROOT")
        source = ((Path(root) / "root_p37c23_sdk_queue.py").read_bytes() if root else b'''def compact_plan(plan):
    return {"prewar_force_admission": None}
def display_projection(row, body):
    # raw response retained
    return {"army_strengths": []}
''')
        transformed = ast.parse(transform_queue(source))
        functions: list[ast.stmt] = [node for node in transformed.body if isinstance(node, ast.FunctionDef)
                     and node.name in ("compact_plan", "display_projection")]
        namespace: dict[str, object] = {}
        exec(compile(ast.Module(functions, type_ignores=[]), "<actual-queue-formatters>", "exec"), namespace)
        compact = namespace["compact_plan"]
        if not callable(compact):
            raise AssertionError("actual compact callable required")
        return contract.record(compact(actual))

    @staticmethod
    def _row(actual: contract.Record, compact: contract.Record) -> contract.Record:
        return {"source": "actual GameplayBridgeService.before_submit callback",
                "source_namespace": "p37-responses", "game_pid": 123, "game_creation_date": "fixture",
                "request": {"tool": "root_before_auto_turn_submit", "parent_sequence": 143},
                "result": {"is_error": False, "structured_content": {"status": "planned",
                    "selected_step": actual["selected_step"], "snapshot_id": "fixture", "revision": 9,
                    "plan": compact}}}

    @staticmethod
    def _publisher(row: contract.Record, actual: contract.Record) -> contract.Record:
        import io
        from unittest.mock import patch
        import decision_text_publisher as pub
        memory: dict[str, object] = {}
        session = Path("D:/identity-boundary-fixture")
        context = {"sequence": 143, "tool": "ck3_auto_turn"}
        config = {"current_request_path": "held-context", "game": {"pid": 123, "creation_date": "fixture"}}
        started = {"configuration": {}, "session": str(session)}

        def read(path: object) -> object:
            return context if str(path) == "held-context" else memory[str(path)]

        def atomic(path: object, value: object, **kwargs: object) -> None:
            memory[str(path)] = copy.deepcopy(value)

        def pin(path: object) -> contract.Record:
            import hashlib
            raw = json.dumps(memory[str(path)], ensure_ascii=False).encode()
            return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

        observation = {"selected_step": actual["selected_step"], "plan": actual,
                       "snapshot_id": "fixture", "revision": 9}
        with patch.object(Path, "open", lambda *args, **kwargs: io.StringIO()), \
                patch.object(Path, "exists", lambda path: str(path) in memory), \
                patch.object(Path, "unlink", lambda *args, **kwargs: None), \
                patch.object(pub, "validate_started", return_value=started), \
                patch.object(pub, "checked", return_value=config), \
                patch.object(pub, "read", side_effect=read), patch.object(pub, "atomic", side_effect=atomic), \
                patch.object(pub, "pin", side_effect=pin), \
                patch.object(pub, "wait_text_published", return_value={"software_text_ack": True}):
            receipt = pub.publish_callback_observation(
                json.loads(json.dumps(row, ensure_ascii=False)), {}, actual_observation=observation)
        if receipt["callback_index"] != 1 or len(memory) != 1:
            raise AssertionError("real publisher did not emit the exact first callback")
        return contract.record(next(iter(memory.values())))

    def test_actual_queue_formatter_keeps_long_identity_through_real_publisher(self) -> None:
        for length in (1300, 1600):
            with self.subTest(length=length):
                actual: contract.Record = {"selected_step": "ordinary-" + "s" * (length - 9),
                    "phase": "p" * 1300, "reason": "r" * 1600, "policy": "q" * 1600}
                compact = self._queue_compact(actual)
                self.assertEqual(compact["selected_step"], actual["selected_step"])
                self.assertEqual(compact["phase"], actual["phase"])
                self.assertEqual((len(str(compact["reason"])), len(str(compact["policy"]))), (1200, 1200))
                published = self._publisher(self._row(actual, compact), actual)
                body = contract.record(contract.record(published["result"])["structured_content"])
                plan = contract.record(body["plan"])
                selected = actual["selected_step"]
                if not isinstance(selected, str):
                    raise AssertionError("actual selected step must remain a string")
                card = contract.parse_card(plan[contract.DETAIL], step=selected, phase=actual["phase"])
                self.assertEqual(card.selected_step, actual["selected_step"])
                self.assertEqual(card.phase, actual["phase"])
        for invalid in ("s" * 1601, True):
            with self.subTest(invalid_type=type(invalid)), self.assertRaises(ValueError):
                self._queue_compact({"selected_step": invalid})

    def test_actual_private_feed_merge_restores_complete_source_identity(self) -> None:
        import os
        import types
        from unittest.mock import patch
        root = os.environ.get("XAR_IDENTITY_PRIVATE_RUNTIME_ROOT")
        if not root:
            self.skipTest("actual read-only private runtime path not supplied")
        path = Path(root) / "root_p37c23_compact_decision_feed.py"
        namespace: dict[str, object] = {"__file__": str(Path("D:/identity-boundary-fixture") / path.name),
                                        "__name__": "identity_private_feed"}
        exec(compile(transform_feed(path.read_bytes()), "<actual-private-feed>", "exec"), namespace)
        before = namespace["publish_before_submit"]
        if not callable(before):
            raise AssertionError("actual pre-submit callback required")
        actual: contract.Record = {"selected_step": "ordinary-" + "s" * 1291,
            "phase": "p" * 1300, "reason": "r" * 1600, "policy": "q" * 1600}
        received: list[contract.Record] = []

        def publish(row: contract.Record, reference: object, *, actual_observation: object) -> contract.Record:
            self.assertEqual(contract.record(actual_observation)["plan"], actual)
            saved = self._publisher(row, actual)
            received.append(saved)
            return saved

        class FixturePublisher:
            def publish_callback_observation(self, row: contract.Record, reference: object, *,
                                            actual_observation: object) -> contract.Record:
                return publish(row, reference, actual_observation=actual_observation)
        class FixtureDecisionAPI(types.ModuleType):
            def load_api(self, *args: object) -> FixturePublisher:
                return FixturePublisher()
            def started_reference(self, *args: object) -> contract.Record:
                return {}
        api = FixtureDecisionAPI("root_decision_text_api_c23")

        def read_text(path: Path, **kwargs: object) -> str:
            if path.name == "CURRENT-REQUEST-P37.json":
                return json.dumps({"sequence": 143, "tool": "ck3_auto_turn"})
            if path.name == "ROOT-ACTUAL-GAME-LAUNCH-C23.json":
                return json.dumps({"pid": 123, "creation_date": "fixture"})
            raise AssertionError("unexpected runtime lookup: " + str(path))

        with patch.dict("sys.modules", {"root_decision_text_api_c23": api}), \
                patch.object(Path, "read_text", read_text):
            before({"selected_step": actual["selected_step"], "plan": actual,
                    "snapshot_id": "fixture", "revision": 9})
        self.assertEqual(len(received), 1)
        plan = contract.record(contract.record(contract.record(received[0]["result"])["structured_content"])["plan"])
        self.assertEqual(plan["selected_step"], actual["selected_step"])
        self.assertEqual(plan["phase"], actual["phase"])
        self.assertEqual(plan["reason"], "r" * 1200)
        self.assertEqual(plan["policy"], "q" * 1200)

    def test_fallback_identity_survives_json_roundtrip_and_result_projection(self) -> None:
        for phase_case in ("missing", None, "p" * 1300):
            with self.subTest(phase=type(phase_case).__name__):
                actual: contract.Record = {"selected_step": "ordinary-" + "s" * 1291,
                    "reason": "r" * 1600, "war_decision_presentation_v1": []}
                if phase_case != "missing":
                    actual["phase"] = phase_case
                compact = json.loads(json.dumps(feed.compact_plan(actual), ensure_ascii=False))
                self.assertEqual(compact["selected_step"], actual["selected_step"])
                self.assertEqual("phase" in compact, "phase" in actual)
                if "phase" in actual:
                    self.assertEqual(compact["phase"], actual["phase"])
                self.assertIsNone(compact[contract.DETAIL])
                self.assertIn(contract.UNAVAILABLE, compact)
                self._publisher(self._row(actual, compact), actual)
                result = contract.project_result({"request": {"tool": "ck3_auto_turn", "sequence": 143}},
                    {"selected_step": actual["selected_step"], "plan": actual, "result": {"status": "executed"}})
                roundtrip = json.loads(json.dumps(result, ensure_ascii=False))
                body = contract.record(contract.record(roundtrip["result"])["structured_content"])
                plan = contract.record(body["plan"])
                self.assertEqual(body["selected_step"], plan["selected_step"])
                self.assertEqual(plan.get("phase"), actual.get("phase"))
                self.assertNotEqual(contract.outcome(body).stage, "verified")



# Captured on xenoamess-full-tower-eb9d2c1186, 2026-10-22; software inputs only.
# N39/p37-responses/11462-0-plan.json SHA256 30da0aa90594dd21c1142875a7c2ea3a6b031b5996da20abdcec3c823c574969
N39_HORIZON_ROW = r'''{"ended_at_utc":"2026-10-22T02:58:00.569977+00:00","source":"actual GameplayBridgeService.before_submit callback","game_pid":259436,"game_creation_date":"20261022024821.378786+000","request":{"tool":"root_before_auto_turn_submit","parent_sequence":11462,"callback_protocol":"xar.ck3.decision-subdecision/v1","callback_index":1,"actual_observation_sha256":"47a9c4821c4210b5119130e1cd9928bbdeef282cae1b883ffa1db19ffcd5cdd1"},"result":{"is_error":false,"structured_content":{"status":"planned","plan":{"policy":"one-life-turn-v1","phase":"native_war_stationary_contact_horizon_progress","selected_step":"advance-route-contact-horizon-v1-234881394-to-2627-h-2-117440697-285212941","reason":"the exact stationary timeline proves the occupied objective contact-free for the next day","war_decision_presentation_v1":{"phase":"native_war_stationary_contact_horizon_progress","selected_step":"advance-route-contact-horizon-v1-234881394-to-2627-h-2-117440697-285212941","reason":"战分33；保地目标2254；我军832，优先保地战敌2091；全部主导战争敌军2091（去重）。当帧候选未同时满足原生征募、完整报价、现金预留及当前用途，继续原行动。取消工程与合法借款仍待当帧条款及独立到账核验，未计入预期资金。头数不代表胜率。"},"decision_display_v1":{"schema":"xar.decision-display/v1","selected_step":"advance-route-contact-horizon-v1-234881394-to-2627-h-2-117440697-285212941","phase":"native_war_stationary_contact_horizon_progress","domain":"war","action":"处理当前游戏事务","target":null,"facts":[],"rationale":["战分33；保地目标2254；我军832，优先保地战敌2091；全部主导战争敌军2091（去重）。当帧候选未同时满足原生征募、完整报价、现金预留及当前用途，继续原行动。取消工程与合法借款仍待当帧条款及独立到账核验，未计入预期资金。头数不代表胜率。"],"alternatives":null,"costs":[],"risks":["当前兵数不代表胜率；未来增援、抵达及战果未由本条计划确认。"]}},"selected_step":"advance-route-contact-horizon-v1-234881394-to-2627-h-2-117440697-285212941","snapshot_id":"native:16","revision":17}},"source_namespace":"p37-responses"}'''
# N39/responses/p37-responses-11469-1-result.json SHA256 97291ffc9dcece227b7e71a3b7ccd6d934dc3d68dbfd514db18717a975f0b8ec
N39_SAVE_ROW = r'''{"request":{"sequence":11469,"tool":"ck3_save_checkpoint","arguments":{"expected_revision":20}},"ended_at_utc":"2026-10-22T03:00:20.995600+00:00","source":"compact projection of this actual SDK result; raw response retained","result":{"is_error":false,"structured_content":{"status":"submitted","step":"save-checkpoint","accepted":true,"result":{"status":"submitted","step":"save-checkpoint","accepted":true,"checkpoint":{"status":"saved","path":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime\\state\\profile\\save games\\xar_checkpoint.ck3","name":"xar_checkpoint.ck3","size":117661285,"sha256":"c52326604ce1d6aefc493c1bc5d088e26600b001a59978a93ca951b383440ca9","date_raw":53279400,"overwrite_confirmed":true,"strategy":"native-autosave-command-v1","succession_lifecycle":{"schema":"xar.ck3.succession-lifecycle-binding/v1","lifecycle":"ordinary_campaign_succession","xar_enabled":null,"pact_contract":"absent_by_verified_xar_mod_not_loaded","source":"absent_by_verified_xar_mod_not_loaded","environment_sha256":"d33bf569cbd5cd08659a4cf78cabf92c60642332c598c5ae0b3e1eb823514366"},"history_index":5944,"episode_character_id":40526,"episode_run_id":"native-40526-1bec95182886"}}}},"source_ref":"D:\\codex-ck3-demos\\2026-10-14-robert-30year\\continuation42-cold-prep\\robert30-v20261019-campaign01\\runtime-a39\\p37-responses\\11469-1-result.json","source_namespace":"p37-responses"}'''

class N39ActualDisplayTests(unittest.TestCase):
    def _save(self) -> tuple[contract.Record, contract.Record]:
        row = contract.record(json.loads(N39_SAVE_ROW))
        body = contract.record(contract.record(row["result"])["structured_content"])
        return row, body

    def _published(self, row: contract.Record, body: contract.Record) -> tuple[AudienceState, contract.Outcome]:
        projected = contract.project_result(row, body)
        wire = contract.record(json.loads(json.dumps(projected)))
        rendered_body = contract.record(contract.record(wire["result"])["structured_content"])
        state = AudienceState()
        state.consume(wire)
        return state, contract.outcome(rendered_body)

    def test_real_horizon_planner_projection_reaches_formatter(self) -> None:
        row = contract.record(json.loads(N39_HORIZON_ROW))
        result = contract.record(row["result"])
        body = contract.record(result["structured_content"])
        actual = contract.record(body["plan"])
        # Remove only the old derived card to replay the captured planner input.
        del actual[contract.DETAIL]
        compact = feed.compact_plan(actual)
        body["plan"] = compact
        result["structured_content"] = body
        row["result"] = result
        state = AudienceState()
        state.consume(json.loads(json.dumps(row)))
        expected = "按接敌窗口短步推进，复查军情"
        self.assertEqual(state.decision, expected)
        self.assertIn(expected, state.render())
        self.assertIn("832", state.render())
        self.assertIn("2091", state.render())
        selected = actual["selected_step"]
        if not isinstance(selected, str):
            raise AssertionError("captured selected step must remain a string")
        card = contract.parse_card(compact[contract.DETAIL], step=selected, phase=actual["phase"])
        self.assertEqual(card.selected_step, actual["selected_step"])
        self.assertEqual(card.phase, actual["phase"])

    def test_real_submitted_saved_checkpoint_reports_receipt_not_independent_verification(self) -> None:
        row, body = self._save()
        state, report = self._published(row, body)
        self.assertEqual(report.stage, "returned")
        self.assertIn("存档回执报告已保存", state.render())
        self.assertNotIn("独立后验已确认", state.render())
        self.assertNotIn("D:\\", state.render())

    def test_saved_marker_never_overrides_error_unknown_or_rejection(self) -> None:
        cases: tuple[tuple[str, str, object], ...] = (
            ("inner", "status", "observed_after_native_error"),
            ("outer", "status", "observed_after_native_error"),
            ("inner", "native_ack_status", "unknown_after_error"),
            ("inner", "status", "failed"),
            ("outer", "status", "failed"),
            ("inner", "status", "rejected"),
            ("inner", "accepted", False),
            ("outer", "accepted", False),
        )
        for location, key, value in cases:
            with self.subTest(location=location, key=key, value=value):
                row, body = self._save()
                if location == "inner":
                    inner = contract.record(body["result"])
                    inner[key] = value
                    body["result"] = inner
                else:
                    body[key] = value
                state, report = self._published(row, body)
                self.assertEqual(report.stage, "unknown")
                self.assertNotIn("存档回执报告已保存", state.render())
                self.assertNotIn("独立后验已确认", state.render())

    def test_missing_null_empty_and_wrong_typed_saved_markers_do_not_promote(self) -> None:
        for value in (None, {}, {"status": True}, {"status": "saved "}):
            with self.subTest(value=value):
                row, body = self._save()
                inner = contract.record(body["result"])
                inner["checkpoint"] = value
                body["result"] = inner
                state, report = self._published(row, body)
                self.assertEqual(report.stage, "submitted")
                self.assertNotIn("存档回执报告已保存", state.render())
                self.assertNotIn("独立后验已确认", state.render())
        row, body = self._save()
        inner = contract.record(body["result"])
        del inner["checkpoint"]
        body["result"] = inner
        self.assertEqual(self._published(row, body)[1].stage, "submitted")


if __name__ == "__main__":
    unittest.main()
