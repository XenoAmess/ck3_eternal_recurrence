"""Focused real SDK-to-queue contract seam; no driver or native execution.

The fixture supplies an import-only bridge package path to load the real pure
SDK contract and its original dependencies without running bridge.__init__.
No validator, SDK function, queue function or native callee is substituted.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "ck3_autonomous_player/src"
FALLBACK = Path(os.environ.get("XAR_HOF_TEST_DEPENDENCY_SOURCE", str(SDK)))
sys.path[:0] = [str(SDK), str(ROOT / "tools")]
import xar_autoplayer


class _BridgePackage(ModuleType):
    __path__: list[str]


_bridge = _BridgePackage("xar_autoplayer.bridge")
_bridge.__path__ = [str(SDK / "xar_autoplayer/bridge"), str(FALLBACK / "xar_autoplayer/bridge")]
sys.modules["xar_autoplayer.bridge"] = _bridge
from xar_autoplayer.bridge import ingame_decision_item_contract as contract
from xar_autoplayer.selected_decision_terms_v1 import json_object, selected_parameter_context_verified_v1
import faith_e02_hof_queue as Q

KEY = "create_hof_decision"
ACTOR = 50331652
DATE = 53175816
EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
BINDING: dict[str, object] = {"native_revision": 4, "connection_generation": 2,
    "game_pid": 1234, "played_character_id": ACTOR, "date_raw": DATE}


def clone(value: object) -> dict[str, object]:
    decoded: object = json.loads(json.dumps(value))
    return json_object(decoded, "authored JSON fixture must stay an object")


def stock() -> dict[str, object]:
    return {"schema": "ck3-selected-decision-terms-v1", "read_only": True,
        "available": True, "unavailable_reason": None, "game_version": "1.20.0.4",
        "executable_sha256": EXE, "decision_key": KEY, "capture_epoch": 17,
        "date_raw": DATE, "played_character_id": ACTOR, "context_verified": True,
        "named_parameter_count": 1, "context_adapter": "actual_create_hof_stock_default_parameter_only",
        "stock_default_parameter": {"token_source": "stock_detail_default_token_slot_0x5D4C0D8",
            "canonical_token": 71, "key": 71, "scope_kind": 4, "scope_flags": 0,
            "scope_payload": 0xFFFFFFFF, "no_custom_controller": True},
        "can_confirm": True, "requirements_bypass_observed": True, "requirements_bypass_raw": 0,
        "ordinary_legality_observed": True, "ordinary_can_confirm": True,
        "confirm_tooltip_available": True, "confirm_tooltip": "authored tooltip",
        "requirements_description_available": True, "requirements_description": "authored requirements\ncomplete",
        "cost_description_available": True, "cost_description": "authored full quote",
        "resource_quote_available": True, "resource_quote": {"raw_scale": 100000,
            "resource_vector_raw": [0, 0, 100000000, 0, 0, 0, 0, 0, 0, 0], "native_affordable": True},
        "cooldown_observed": True, "cooldown": {"present": False, "current_counter_raw": 100,
            "expiry_raw": None, "active": False, "counter_unit": "native_decision_clock_counter"},
        "action_ready": False, "decision_confirm_invoked": False}


def outer(terms: object) -> dict[str, object]:
    return {"schema": "ck3-ingame-decision-item-v1", "step": contract.STEP, "read_only": True,
        "game_version": "1.20.0.4", "executable_sha256": EXE, "available": True, **BINDING,
        "owner_thread_verified": True, "frame_verified": True, "source_abi_pins_verified": True,
        "gui_owner_binding_verified": True, "decisions_tree_complete": True, "decisions_root_visible": True,
        "row_owner_verified": True, "row_scope_reference_available": True, "group_count": 7,
        "row_count": 21, "matching_row_count": 1, "row_context_reference_key": 0xFF00731,
        "decision_key": KEY, "detail_tree_complete": True, "detail_root_visible": True,
        "detail_definition_available": True, "detail_definition_matches_target": True,
        "detail_decision_key": KEY, "detail_actor_binding_verified": True, "detail_actor_reference_key": ACTOR,
        "row_widget_datacontext_verified": False, "action_qualified": False,
        "unavailable_reason": "", "selected_terms": terms}


def sdk_to_queue(terms: object) -> object:
    raw = outer(terms)
    normalized = contract.normalize_decision_item(raw, dict(BINDING), KEY)
    return Q.quote_terms({"ok": True, "result": normalized}, ACTOR, DATE)


class SharedTermsTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = Path(os.environ.get("XAR_HOF_TEST_SCRATCH_ROOT", str(ROOT)))
        self.tmp = tempfile.TemporaryDirectory(prefix="hof-typed-", dir=scratch)
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_actual_cpp_stock_and_unavailable_wire_through_both_consumers(self) -> None:
        positive = os.environ.get("XAR_HOF_TEST_NATIVE_STOCK")
        negative = os.environ.get("XAR_HOF_TEST_NATIVE_REJECTED")
        if positive is None or negative is None:
            self.skipTest("Actual retained native component wires require explicit input paths")
        assert positive is not None and negative is not None
        for path, expected_sha, available in (
            (Path(positive), "9a1b96bfce89797e0224f69969ecc485d97a9bf9ff2fc3a57654a43c3c0c2066", True),
            (Path(negative), "6837f869ee3a1deebee57ae21032024b8fefaa00cd527f109d16822aa8f8e708", False),
        ):
            with self.subTest(path=path.name):
                body = path.read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(), expected_sha)
                decoded: object = json.loads(body)
                terms = json_object(decoded, "native body must be an object")
                normalized = contract.normalize_decision_item(outer(terms), dict(BINDING), KEY)
                self.assertEqual(normalized["selected_terms"], terms)
                self.assertIs(terms["available"], available)
                if available:
                    self.assertEqual(Q.quote_terms({"ok": True, "result": normalized}, ACTOR, DATE), terms)
                else:
                    # This is unavailable/count1, not an available empty row.
                    self.assertEqual(terms["named_parameter_count"], 1)
                    with self.assertRaises(ValueError):
                        Q.quote_terms({"ok": True, "result": normalized}, ACTOR, DATE)
                self.assertEqual(path.read_bytes(), body)

    def test_one_shared_helper_and_empty_missing_null_roundtrip(self) -> None:
        self.assertIs(Q.selected_parameter_context_verified_v1, selected_parameter_context_verified_v1)
        self.assertIs(contract.selected_parameter_context_verified_v1, selected_parameter_context_verified_v1)
        for present in (False, True):
            terms = stock()
            terms.update(context_adapter="actual_empty_named_parameters_only", named_parameter_count=0)
            del terms["stock_default_parameter"]
            if present:
                terms["stock_default_parameter"] = None
            observed = json_object(sdk_to_queue(clone(terms)), "typed terms remain JSON")
            self.assertEqual(observed, terms)
            self.assertEqual("stock_default_parameter" in observed, present)
            self.assertIs(observed["action_ready"], False)

    def test_parameter_missing_extra_wrong_types_and_boolean_numbers_refused(self) -> None:
        mutations: list[tuple[str, object]] = [("canonical_token", True), ("key", True),
            ("scope_kind", True), ("scope_flags", False), ("scope_payload", -1),
            ("scope_payload", float(0xFFFFFFFF)), ("no_custom_controller", 1),
            ("token_source", "another_source"), ("key", 72), ("scope_kind", 3)]
        for key, bad in mutations:
            with self.subTest(key=key, bad=bad):
                terms = stock(); parameter = json_object(terms["stock_default_parameter"], "stock object")
                parameter[key] = bad
                with self.assertRaises(ValueError): sdk_to_queue(terms)
        for extra in (False, True):
            terms = stock(); parameter = json_object(terms["stock_default_parameter"], "stock object")
            if extra: parameter["extra"] = 0
            else: del parameter["scope_payload"]
            with self.assertRaises(ValueError): sdk_to_queue(terms)
        for count in (True, 1.0, 0, 2):
            terms = stock(); terms["named_parameter_count"] = count
            with self.assertRaises(ValueError): sdk_to_queue(terms)
        self.assertFalse(selected_parameter_context_verified_v1(stock(), "another_decision"))

    def test_sdk_observations_do_not_grant_hof_permission(self) -> None:
        for refusal in ("native_false", "unaffordable", "bypass"):
            terms = stock()
            if refusal == "native_false": terms.update(can_confirm=False, ordinary_can_confirm=False)
            if refusal == "unaffordable": json_object(terms["resource_quote"], "quote")["native_affordable"] = False
            if refusal == "bypass": terms.update(requirements_bypass_raw=1, ordinary_legality_observed=False, ordinary_can_confirm=None)
            normalized = contract.normalize_decision_item(outer(terms), dict(BINDING), KEY)
            with self.assertRaises(ValueError): Q.quote_terms({"ok": True, "result": normalized}, ACTOR, DATE)
        for bad in (True, 1.0):
            packet = outer(stock()); packet["matching_row_count"] = bad
            with self.assertRaises(ValueError): Q.quote_terms({"ok": True, "result": packet}, ACTOR, DATE)
        with self.assertRaises(ValueError): Q.quote_terms({"ok": True, "result": outer(stock())}, True, DATE)
        with self.assertRaises(ValueError): Q.quote_terms({"ok": True, "result": outer(stock())}, ACTOR, True)
        for bad in (True, 1.5, 1 << 63):
            terms = stock(); quote = json_object(terms["resource_quote"], "quote")
            quote["resource_vector_raw"] = [bad, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            with self.assertRaises(ValueError): sdk_to_queue(terms)

    def test_real_receipt_pair_json_fields_and_tamper_boundary(self) -> None:
        terms = stock(); terms["opaque_future_field"] = {"still": [None, False, 1, "1"]}
        values: list[dict[str, object]] = []
        refs: list[object] = []
        for i in range(2):
            row: dict[str, object] = {"ok": True, "result": contract.normalize_decision_item(outer(clone(terms)), dict(BINDING), KEY)}
            path = self.root / (str(i) + ".json")
            path.write_text(json.dumps({"rows": [row]}), encoding="utf-8")
            values.append(row); refs.append(Q.pin(path))
        claim: dict[str, object] = {"schema": "faith-e02-R19-hof-once-claim-v1", "decision_key": KEY,
            "actor": ACTOR, "date_raw": DATE, "quote_receipts": refs}
        pair = Q.verify_quote_pair(clone(claim))
        self.assertIsInstance(pair, list); self.assertEqual(pair, [terms, terms])
        bad = clone(claim); bad["actor"] = True
        with self.assertRaises(ValueError): Q.verify_quote_pair(bad)
        first = json_object(refs[0], "pin"); first["bytes"] = True
        with self.assertRaises(ValueError): Q.verify_quote_pair(claim)
        refs[0] = Q.pin(self.root / "0.json")
        changed = stock(); changed["cost_description"] = "changed original quote text"
        (self.root / "1.json").write_text(json.dumps({"rows": [{"ok": True, "result": outer(changed)}]}), encoding="utf-8")
        refs[1] = Q.pin(self.root / "1.json")
        with self.assertRaises(ValueError): Q.verify_quote_pair(claim)

    def test_cli_from_unrelated_cwd_requires_no_bridge_package(self) -> None:
        plan = self.root / "plan.json"
        plan.write_text(json.dumps({"steps": [{"id": "read", "kind": "tool", "tool": Q.QUERY,
            "args": {"decision_key": KEY}, "fresh_revision": True, "continue_on_error": True}]}), encoding="utf-8")
        probe = self.root / "probe.py"
        probe.write_text("import runpy,sys\nsys.modules['xar_autoplayer.bridge']=None\nq,p=sys.argv[1:]\nsys.argv=[q,'--plan',p]\nrunpy.run_path(q,run_name='__main__')\n", encoding="utf-8")
        env = dict(os.environ); env.pop("PYTHONPATH", None); env.pop("MYPYPATH", None)
        result = subprocess.run([sys.executable, "-I", "-B", str(probe), str(ROOT / "tools/faith_e02_hof_queue.py"), str(plan)],
            cwd=self.root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(json.loads(result.stdout), {"policy_validated": True, "submitted": False})


if __name__ == "__main__":
    unittest.main(verbosity=2)
