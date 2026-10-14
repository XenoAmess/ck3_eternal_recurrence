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
        value = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
        value.pop("verification_scope", None)  # Retain the original core26 regression below.
        return value

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
        with tempfile.TemporaryDirectory(prefix="rmtm-keypaths-tiny-") as directory, patch.object(adapter, "migration_delta", return_value=False):
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
        with tempfile.TemporaryDirectory(prefix="rmtm-keypaths-route-") as directory, patch.object(adapter, "migration_delta", return_value=False):
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


class MigrationDelta(unittest.TestCase):
    def config(self):
        return json.loads(CONFIG.read_text(encoding="utf-8-sig"))

    def context(self):
        return {"case": "core", "repo_root": str(ROOT), "run_id": "new-run", "case_inputs": {},
                "case_spec": {"adapter": {"config": str(CONFIG)}}}

    def test_only_seven_positive_families_but_all_d8_law_and_fail_gates_remain(self):
        config = self.config()
        required = config["required_release_families"]
        self.assertEqual(len(required), 7)
        self.assertTrue({"phase3_succession_title", "phase3_succession_personal_county", "phase3_succession_loyal_realm",
                         "phase3_succession_ministry_entitlement", "phase3_succession_exact_ministers",
                         "phase3_later_dynasty_realm_and_ministry_inherited"}.issubset(required))
        families = [row for row in config["families"] if row["name"] in required]
        markers = [f"RQA: {row['kind']} {row['representation']} {row['name']}" for row in families]
        raw = ("\n".join(markers + [config["begin"], config["done"]]) + "\n").encode()
        bundle = {"schema": "rmtm-effective-single-heir-actual-rows-v1",
                  "phases": [phase("d3", 11, 1000), phase("predeath", 11, 1001), phase("postdeath", 22, 1002)]}
        verdict = adapter.focused_marker_verdict(config, raw, bundle, law)
        self.assertEqual(verdict["verification_scope"], "migration_delta_v1")
        self.assertFalse(verdict["legacy_core26_credit"])
        self.assertFalse(verdict["business_pass"])
        for marker in markers:
            with self.assertRaises(ValueError): adapter.focused_marker_verdict(config, raw.replace(marker.encode(), b"missing"), bundle, law)
        with self.assertRaises(ValueError): adapter.focused_marker_verdict(config, raw + b"RQA: TEST FAIL original_movement_identity_frozen\n", bundle, law)
        broken = copy.deepcopy(bundle); broken["phases"][2]["physical_record"]["result"]["title_id"] = 99
        with self.assertRaises(ValueError): adapter.focused_marker_verdict(config, raw, broken, law)

    def test_historical_setup_requires_original_pins_runtime_production_and_facts(self):
        with tempfile.TemporaryDirectory(prefix="rmtm-delta-reuse-") as directory:
            base = Path(directory); image = base / "original.png"; image.write_bytes(b"synthetic GUI fixture")
            manifest = base / "manifest.json"; manifest.write_text("{}", encoding="utf-8")
            runtime = pin(manifest)
            provenance = {"formal_product_manifest": pin(manifest),
                          "formal_product_expected_files": {"effect.txt": {"bytes": 1, "sha256": "frozen"}}}
            prepared = base / "prepared.json"
            prepared.write_text(json.dumps({"product": "reclaim-motherland", "case": "core", "runtime_manifest": runtime,
                "case_inputs": {"input_provenance": provenance}, "business_acceptance": "NOT_ASSESSED"}), encoding="utf-8")
            review = base / "review.json"
            record = {"status": "complete", "reviewer": "old-operator", "run_id": "old-failed-run",
                      "facts": {name: True for name in self.config()["reused_setup_requirements"]}, "evidence": [pin(image)]}
            review.write_text(json.dumps(record), encoding="utf-8")
            context = self.context(); context["runtime_manifest"] = runtime
            context["case_inputs"] = {"input_provenance": copy.deepcopy(provenance),
                                     "reused_setup_evidence": {"prepared_case": pin(prepared), "review": pin(review)}}
            result = adapter.reused_setup_evidence(context)
            self.assertTrue(result["not_current_run_gui"])
            self.assertFalse(result["historical_case_pass_reclassified"])
            self.assertFalse(result["business_pass"])
            context["runtime_manifest"] = {**runtime, "sha256": "different"}
            with self.assertRaises(ValueError): adapter.reused_setup_evidence(context)
            context["runtime_manifest"] = runtime
            context["case_inputs"]["input_provenance"]["formal_product_expected_files"]["effect.txt"]["bytes"] = 2
            with self.assertRaises(ValueError): adapter.reused_setup_evidence(context)
            context["case_inputs"]["input_provenance"] = copy.deepcopy(provenance)
            context["run_id"] = record["run_id"]
            with self.assertRaises(ValueError): adapter.reused_setup_evidence(context)
            context["run_id"] = "new-run"
            record["facts"][self.config()["reused_setup_requirements"][0]] = False
            review.write_text(json.dumps(record), encoding="utf-8")
            context["case_inputs"]["reused_setup_evidence"]["review"] = pin(review)
            with self.assertRaises(ValueError): adapter.reused_setup_evidence(context)
            self.assertLess(sum(p.stat().st_size for p in base.iterdir()), 4096)

    def test_date_join_setup_reuse_allows_only_the_exact_host_overlay(self):
        with tempfile.TemporaryDirectory(prefix="rmtm-date-join-reuse-") as directory:
            base = Path(directory)
            host = base / "host.py"
            host.write_bytes(b"x" * 251389)
            host_ref = pin(host)
            old = {"schema": "ck3-mod-acceptance-shared-runtime-v1", "runtime_id": "old",
                   "host": {"path_key": "host", "bytes": 234852, "sha256": "old-host"},
                   "game": {"version": "1.20.0.4"}, "native": {"dll": "same"},
                   "source_index": {"sha256": "same"}, "imports": [{"sha256": "same"}]}
            overlay = {"source19_host_sha256": "old-host", "tested_main_host_sha256": "tested-main",
                       "selected_top_level_functions": ["campaign_pause_frame_binding",
                           "require_campaign_pause_successor", "_campaign_pause_frame_rejection_detail",
                           "_campaign_pending_running_date"],
                       "selected_method": "wait_campaign_running_successor", "running_loop_replacements": 1,
                       "legacy_source_root_and_index_unchanged": True,
                       "native_dll_and_index_unchanged": True, "previous_failed_scene_not_recredited": True}
            new = {**copy.deepcopy(old), "runtime_id": "date-join",
                   "host": {"path_key": "host", "bytes": 251389, "sha256": host_ref["sha256"]},
                   "host_overlay": overlay}
            old_path, new_path = base / "old.json", base / "new.json"
            old_path.write_text(json.dumps(old), encoding="utf-8")
            new_path.write_text(json.dumps(new), encoding="utf-8")
            context = {"runtime_manifest": pin(new_path),
                       "case_inputs": {"runtime_host_overlay": host_ref}}
            with patch.multiple(adapter,
                _DATE_JOIN_PARENT_MANIFEST_SHA=pin(old_path)["sha256"],
                _DATE_JOIN_MANIFEST_SHA=pin(new_path)["sha256"],
                _DATE_JOIN_PARENT_HOST_SHA="old-host",
                _DATE_JOIN_TESTED_MAIN_HOST_SHA="tested-main",
                _DATE_JOIN_FROZEN_HOST_SHA=host_ref["sha256"]):
                result = adapter.date_join_runtime_setup_equivalence(context, pin(old_path))
                self.assertTrue(result["same_game_native_package_imports_and_shared_contract"])
                self.assertFalse(result["historical_business_pass_reclassified"])
                context["case_inputs"]["runtime_host_overlay"] = {**host_ref, "sha256": "wrong"}
                with self.assertRaises(ValueError):
                    adapter.date_join_runtime_setup_equivalence(context, pin(old_path))
                context["case_inputs"]["runtime_host_overlay"] = host_ref
                new["native"] = {"dll": "changed"}
                new_path.write_text(json.dumps(new), encoding="utf-8")
                context["runtime_manifest"] = pin(new_path)
                with patch.object(adapter, "_DATE_JOIN_MANIFEST_SHA", context["runtime_manifest"]["sha256"]):
                    with self.assertRaises(ValueError):
                        adapter.date_join_runtime_setup_equivalence(context, pin(old_path))

    def test_current_route_keeps_days_law_and_succession_without_repeated_setup_gui(self):
        with tempfile.TemporaryDirectory(prefix="rmtm-delta-route-") as directory:
            days, phases, reviews, checkpoints = [], [], [], {}
            reuse = {"historical_case_pass_reclassified": False, "not_current_run_gui": True, "business_pass": False}
            def checkpoint(name, value): checkpoints[name] = value; return value
            client = SimpleNamespace(output=directory, checkpoint=checkpoint,
                log_bytes=lambda: (emitter.FOCUSED_DONE + "\n").encode() if "rmtm-D8" in days else b"")
            with patch.object(adapter, "validate_contract"), patch.object(adapter, "reused_setup_evidence", return_value=reuse), \
                 patch.object(adapter, "observe", return_value=({"date_raw": 1000}, None)), \
                 patch.object(adapter, "original_day", side_effect=lambda c, name, *a, **k: days.append(name)), \
                 patch.object(adapter, "_law_phase", side_effect=lambda c, name: (phases.append(name) or Path("test-" + name), {"date_raw": 1007})), \
                 patch.object(adapter, "literals"), patch.object(adapter, "review", side_effect=lambda c, name, *a: reviews.append(name)):
                self.assertFalse(adapter.run_case(self.context(), client)["business_pass"])
            self.assertEqual(days, ["rmtm-D" + str(day) for day in range(1, 9)])
            self.assertEqual(phases, ["d3", "predeath", "postdeath"])
            self.assertEqual(reviews, ["rmtm-Continue-once", "rmtm-real-succession"])
            self.assertEqual(checkpoints["rmtm-verdict-input"]["verification_scope"], "migration_delta_v1")
            self.assertEqual(checkpoints["rmtm-verdict-input"]["reused_setup_evidence"], reuse)


if __name__ == "__main__":
    unittest.main()
