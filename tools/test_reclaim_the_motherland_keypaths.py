"""One bounded, game-free focused-release class; no Git or full fixture copy."""
from __future__ import annotations

import codecs
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "tools"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import prepare_reclaim_the_motherland_1_20_fixture as emitter
import reclaim_the_motherland_scope_witness as witness
import reclaim_the_motherland_effective_law_contract as law
from tools.ck3_mod_acceptance_cases import rmtm_adapter as adapter
from tools.ck3_mod_acceptance_cases._business import pin
from test_reclaim_the_motherland_contract import parse_clausewitz

CONFIG = ROOT / "tools/ck3_mod_acceptance_cases/rmtm_keypaths.json"
SOURCE = ROOT / "tools/fixtures/reclaim_the_motherland_acceptance"


def phase(phase_name, actor, date, heir=22):
    snapshot = {"backend_id": "native-headless", "source": "injected-dll-named-pipe",
        "episode_projection": "native_campaign", "paused": True, "map_ready": True, "active_event": None,
        "played_character": {"character_id": actor, "alive": True, "source": "native"},
        "diagnostics": {"connected": True, "bridge_pid": 123, "connection_generation": 1,
            "hello": {"expected_ck3_version": law.VERSION, "expected_ck3_sha256": law.EXE_SHA}},
        "native_revision": date, "revision": date, "snapshot_id": f"native:{date}", "date_raw": date}
    binding = {"queried_snapshot_id": f"native:{date}", "queried_native_revision": date,
               "queried_revision": date, "snapshot_revision": date, "date_raw": date}
    root = {**binding, "accepted": True, "status": "available", "campaign_root_context_ready": True,
        "build": {"version": law.VERSION, "exe_sha256": law.EXE_SHA},
        "campaign_root_context": {"status": "available", "snapshot_revision": date, "date_raw": date,
            "player_character_id": actor, "player_character_alive": True, "independent": True,
            "primary_title": {"title_id": 44, "tier_key": "hegemony"},
            "held_title_partition": [{"primary": True, "title": {"title_id": 44}, "first_heir_character_id": heir}]}}
    physical = {**binding, "accepted": True, "read_only": True, "status": "available", "title_id": 44,
        "title_own_laws": {"schema": "xar.ck3.title-own-laws.v1", "schema_version": 1,
            "available": True, "status": "available", "unavailable_reason": None,
            "game_version": law.VERSION, "executable_sha256": law.EXE_SHA,
            "actor_character_id": actor, "title_id": 44, "snapshot_revision": date, "date_raw": date,
            "native_law_count": 1, "single_heir_member": True,
            "laws": [{"native_definition_id": 7, "key": law.LAW}]}}
    matches = []
    for literal in law.phase_literals(phase_name)["literals"]:
        count = int(literal.endswith("=TRUE") or " PENDING_PHYSICAL " in literal)
        matches.append({"literal": literal, "line_count": count,
                        "samples": [{"line_number": 1, "text": literal}] if count else []})
    script = {"schema": "xar.ck3.engine-log-literals/v1", "read_only": True,
              "exists": True, "case_sensitive": True, "log_name": "debug.log", "matches": matches}
    value = {"phase": phase_name}
    for key, tool, result in (("root", "ck3_query_campaign_root_context_v1", root),
                             ("physical", "ck3_query_title_own_laws_v1", physical),
                             ("script", "ck3_query_engine_log_literals_v1", script)):
        value[key + "_record"] = {"ok": True, "plan": {"tool": tool}, "result": result,
                                  "after_snapshot": copy.deepcopy(snapshot)}
    return value


class OwnedKeypaths(unittest.TestCase):
    def config(self):
        return json.loads(CONFIG.read_text(encoding="utf-8-sig"))

    def context(self):
        return {"case": "core", "repo_root": str(ROOT), "case_inputs": {},
                "case_spec": {"adapter": {"config": str(CONFIG)}}}

    def test_scope_removes_offer_and_duplicate_tail_but_retains_law_failure_boundary(self):
        old = json.loads(CONFIG.with_name("rmtm_core.json").read_text(encoding="utf-8-sig"))
        removed = {"phase4_offer_vassalization_paths_valid",
                   "phase4_two_released_rulers_refused_immediate_vassalization",
                   "phase4_recent_independence_expired", "china_control_reset",
                   "fifty_percent_below_claim_threshold", "original_fifty_one_percent_threshold_reached",
                   "restoration_decision_ready", "original_mandate_effect_plus_later_title_destroyed"}
        current = self.config()
        self.assertEqual(current["families"], [row for row in old["families"] if row["name"] not in removed])
        self.assertEqual(len(current["families"]), 26)
        self.assertEqual(current["done"], emitter.FOCUSED_DONE)
        for key in ("natural_game_day_limit", "fixture_recent_independence_override_days", "forbidden_markers", "post_start"):
            self.assertEqual(current[key], old[key])
        self.assertEqual(witness.byte_pin((SOURCE / witness.FIXTURE_RELATIVE).read_bytes())["sha256"],
                         "b25240d58d3d160ed12e2a1cd876d63633ebc695776891de91c72fd62ba3f355")
        self.assertFalse(adapter.validate_contract(self.context())["business_pass"])
        bad = self.context(); bad["case_inputs"][emitter.PHASE4_OPTION] = True
        with self.assertRaises(ValueError): adapter.validate_contract(bad)
        threshold = json.loads(CONFIG.with_name("rmtm_threshold_ui.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(threshold["release_scope"], "owned_keypaths")
        self.assertIn("RQAUI: TEST PASS actual_production_restoration_effect_observed", threshold["required_markers"])

    def test_five_driver_changes_exact_inverse_bom_and_original_succession_timing(self):
        original = emitter.events(True).encode("utf-8-sig")
        for raw in (original, original.replace(b"\n", b"\r\n")):
            focused = emitter.focused_project(raw)
            self.assertTrue(focused.startswith(codecs.BOM_UTF8))
            self.assertEqual(emitter.focused_project(focused, inverse=True), raw)
            self.assertNotIn(emitter.PHASE4_SEND.rstrip(), focused)
            self.assertNotIn(b"rqa_verify_vassalization_probe_effect = yes", focused)
            for token in (b"rqa_verify_chaos_effect = yes", b"rqa_execute_succession_effect = yes",
                          b"rqa120_production_restoration_effect = yes",
                          b"rqa120_stage value = 90", b"rqa120.2 days = 3"):
                self.assertEqual(focused.count(token), raw.count(token))
            self.assertEqual(focused.count(b"rqa_prepare_threshold_effect = yes"),
                             raw.count(b"rqa_prepare_threshold_effect = yes") - 1)
            self.assertEqual(focused.count(emitter.FOCUSED_DONE.encode("ascii")), 1)
            self.assertNotIn(b"rqa_verify_recent_independence_expiry_effect = yes", focused)
            parse_clausewitz(focused.decode("utf-8-sig"))
            proof = emitter.focused_projection_receipt(raw, focused)
            self.assertEqual(proof["original_driver"], proof["inverse_driver"])
            self.assertFalse(proof["business_pass"])
        with self.assertRaises(ValueError): emitter.focused_project(emitter.focused_project(original))

    def test_actual_three_phase_law_and_all_actual_fail_lines_still_reject(self):
        config = self.config()
        bundle = {"schema": "rmtm-effective-single-heir-actual-rows-v1",
                  "phases": [phase("d3", 11, 1000), phase("predeath", 11, 1001), phase("postdeath", 22, 1002)]}
        expected = [f"RQA: {row['kind']} {row['representation']} {row['name']}" for row in config["families"]]
        raw = ("\n".join(expected + [config["begin"], config["done"]]) + "\n").encode()
        self.assertFalse(adapter.focused_marker_verdict(config, raw, bundle, law)["business_pass"])
        for badraw in (raw + b"RQA: TEST FAIL phase4_two_released_rulers_refused_immediate_vassalization\n",
                       raw + expected[0].encode() + b"\n", raw.replace(expected[0].encode(), b"missing"),
                       raw + b"RQA: TEST PASS later_dynasty_single_heir_law_and_heir_ready\n"):
            with self.assertRaises(ValueError): adapter.focused_marker_verdict(config, badraw, bundle, law)
        for mutation in ("title", "law", "successor"):
            broken = copy.deepcopy(bundle)
            if mutation == "title": broken["phases"][0]["physical_record"]["result"]["title_id"] = 99
            elif mutation == "law": broken["phases"][0]["physical_record"]["result"]["title_own_laws"]["laws"][0]["key"] = "wrong"
            else: broken["phases"][1]["root_record"]["result"]["campaign_root_context"]["held_title_partition"][0]["first_heir_character_id"] = 99
            with self.assertRaises(ValueError): adapter.focused_marker_verdict(config, raw, broken, law)

    def test_materialized_projection_inventory_inverse_and_load_order_are_still_required(self):
        with tempfile.TemporaryDirectory(prefix="rmtm-keypaths-tiny-") as directory:
            base = Path(directory); fixture, state = base / "fixture", base / "state"
            original = emitter.events(True).encode("utf-8-sig")
            driver = emitter.focused_project(original)
            files = {"events/rqa120_events.txt": driver}; projections = []
            for relative, kind, source in ((witness.FIXTURE_RELATIVE, "execute", SOURCE / witness.FIXTURE_RELATIVE),
                    (witness.CALLBACK_RELATIVE, "callback", ROOT / "mod_reclaim_the_motherland" / witness.CALLBACK_RELATIVE)):
                files[relative], proof = witness.project(source.read_bytes(), kind)
                projections.append({"relative": relative, **proof})
            for relative, raw in files.items():
                for root in (fixture, state / "profile/mod-content/fixture"):
                    path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            receipt = {"ui_checkpoints": True, "threshold_ui": False,
                emitter.FOCUSED_OPTION: emitter.focused_projection_receipt(original, driver),
                "scope_witness_projection": {"scope_dump_count": 3, "projections": projections},
                "prepared_file_sha256": {name: witness.byte_pin(raw)["sha256"] for name, raw in files.items()}}
            receipt_path = fixture.with_suffix(".prepare.json"); receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            profile = base / "profile-preparation.json"
            profile.write_text(json.dumps({"provenance": {"kind": "case-emitter-and-exact-formal-staging",
                "fixture": str(fixture), "product": str(ROOT / "mod_reclaim_the_motherland")}}), encoding="utf-8")
            (state / "preparation.json").write_text(json.dumps({"preparation": pin(profile)}), encoding="utf-8")
            load = state / "profile/dlc_load.json"; load.write_text(json.dumps({"enabled_mods": ["mod/product.mod", "mod/fixture.mod"]}), encoding="utf-8")
            context = self.context(); context.update(state_dir=str(state))
            context["case_inputs"] = {"product_dir": str(ROOT / "mod_reclaim_the_motherland")}
            self.assertFalse(adapter.validate_contract(context)["business_pass"])
            receipt[emitter.FOCUSED_OPTION]["business_pass"] = True
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(ValueError): adapter.validate_contract(context)
            receipt[emitter.FOCUSED_OPTION]["business_pass"] = False
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            load.write_text(json.dumps({"enabled_mods": ["mod/fixture.mod", "mod/product.mod"]}), encoding="utf-8")
            with self.assertRaises(ValueError): adapter.validate_contract(context)
            self.assertLess(sum(path.stat().st_size for path in base.rglob("*") if path.is_file()), 1024 * 1024)
        self.assertFalse(base.exists())

    def test_run_keeps_d3_d4_and_succession_but_never_requests_offer_reviews(self):
        with tempfile.TemporaryDirectory(prefix="rmtm-keypaths-route-") as directory:
            seen_days, seen_phases, seen_reviews = [], [], []
            client = SimpleNamespace(output=directory,
                                     log_bytes=lambda: (emitter.FOCUSED_DONE + "\n").encode("ascii")
                                     if "rmtm-D8" in seen_days else b"",
                                     checkpoint=lambda name, value: value)
            context = self.context()
            with patch.object(adapter, "validate_contract"), patch.object(adapter, "observe", return_value=({"date_raw": 1000}, None)), \
                 patch.object(adapter, "original_day", side_effect=lambda c, name, *a, **k: seen_days.append(name)), \
                 patch.object(adapter, "_law_phase", side_effect=lambda c, name: (seen_phases.append(name) or Path("test-" + name), {"date_raw": 1007})), \
                 patch.object(adapter, "literals"), patch.object(adapter, "review", side_effect=lambda c, name, *a: seen_reviews.append(name)):
                self.assertFalse(adapter.run_case(context, client)["business_pass"])
            self.assertEqual(seen_days, ["rmtm-D" + str(day) for day in range(1, 9)])
            self.assertEqual(seen_phases, ["d3", "predeath", "postdeath"])
            self.assertEqual(seen_reviews, ["rmtm-owned-keypaths-GUI", "rmtm-Continue-once", "rmtm-real-succession", "rmtm-owned-keypaths-final"])
            self.assertLess(sum(path.stat().st_size for path in Path(directory).rglob("*") if path.is_file()), 1024)
        self.assertFalse(Path(directory).exists())


if __name__ == "__main__":
    unittest.main()
