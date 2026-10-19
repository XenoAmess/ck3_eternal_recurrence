"""Two new composition checks; no historical M7 matrix or runtime tests."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import time
import unittest

import prepare_source22_m7_candidate_sdk_v1 as source


class Source22M7CrossPackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changed, cls.rows, cls.report = source.compose(verify_all_base=True)

    def test_custody_and_source22_wal_ctor_commute_with_complete_inverse(self):
        report = self.report
        self.assertTrue(report["M7_then_WAL_equals_WAL_then_M7_entire_Driver"])
        self.assertTrue(report["entire_each_existing_leaf_inverse"])
        self.assertTrue(report["non_owned_Driver_function_ASTs_unchanged"])
        self.assertEqual(set(report["Driver_changed_functions"]), source.ALLOWED_DRIVER)
        imports = report["static_internal_dependency_closure"][source.DRIVER]
        self.assertIn("xar_autoplayer/bridge/succession_binding_refresh_wal_v1.py", imports)
        self.assertIn("xar_autoplayer/bridge/exact_clock_failure_diagnostic_v1.py", imports)
        self.assertIn("xar_autoplayer/bridge/player_heir_candidate_component_v1.py", imports)
        self.assertIn("xar_autoplayer/bridge/native_loaded_provider_custody_v1.py", imports)
        self.assertEqual(report["Runtime_changed_functions"], ["_apply_pre_native_resume_v1", "launch"])
        # Reapplying the source M7 route must fail before any changed byte is
        # returned.  This guards the old empty-wait-options source context.
        _, _, operations = source.frozen_inputs()
        operation = next(o for o in operations if o["kind"] == "exact_reversible_committed_hunks"
                         and o["relative"] == source.DRIVER)
        with self.assertRaisesRegex(ValueError, "exact hunk context"):
            source.exact.transfer_exact_hunks(self.changed[source.DRIVER], source.read_patch(operation))

    def test_complete_inventory_preserves_recovery_family_performance_and_current_epoch_inputs(self):
        _, base = source.read_manifest()
        rows = {r["relative"]: r for r in self.rows}
        self.assertEqual((len(base), len(rows)), (1449, 1456))
        self.assertEqual(sum(d["before"] is None for d in self.report["delta"]), 7)
        self.assertEqual(sum(d["before"] is not None for d in self.report["delta"]), 5)
        modified = {d["relative"] for d in self.report["delta"]}
        for name in base.keys() - modified:
            self.assertEqual(rows[name], base[name], name)
        self.assertNotIn(source.MCP, modified)
        self.assertNotIn("xar_autoplayer/bridge/service.py", modified)
        self.assertNotIn("xar_autoplayer/bridge/readonly_planning_retry_v1.py", modified)
        self.assertNotIn("xar_autoplayer/bridge/campaign_root_terminal_retry_v1.py", modified)
        self.assertNotIn("xar_autoplayer/bridge/campaign_root_retry_diagnostic_v1.py", modified)
        self.assertNotIn("xar_autoplayer/bridge/exact_day_speed_configuration_v1.py", modified)
        self.assertNotIn("xar_autoplayer/family_marriage_formal_consumer.py", modified)
        self.assertNotIn("xar_autoplayer/m5_formal_proposal_collector.py", modified)
        self.assertNotIn("xar_autoplayer/bridge/turn_bundle_contract.py", modified)
        self.assertNotIn("xar_autoplayer/sway_formal_consumer.py", modified)
        self.assertNotIn("xar_autoplayer/bridge/active_scheme_sway_formal_private_transport.py", modified)
        self.assertNotIn("xar_autoplayer/war_reinforcement_tradeoff_v1.py", modified)
        self.assertNotIn("xar_autoplayer/vanilla_events/c19_finite_source_rebind_v1.py", rows)
        self.assertNotIn("xar_autoplayer/bridge/bounded_multiday_wal_v1.py", rows)
        epoch = self.report["epoch_inputs_after_final_Driver"]
        self.assertEqual(epoch["bridge/native_driver.py"], rows[source.DRIVER]["sha256"])
        self.assertEqual(epoch["bridge/mcp_server.py"], base[source.MCP]["sha256"])
        self.assertEqual(epoch["bridge/service.py"], base["xar_autoplayer/bridge/service.py"]["sha256"])
        self.assertNotEqual(self.report["source_epoch_detached_model"],
                            "3642dbf251640efc845ab0c633d8f5f832e49682e482cd1df9b676324fb6ddc3")
        self.assertFalse(self.report["source_epoch_actual_filesystem_authority"])
        self.assertEqual(self.report["actual_H"], "unknown")


def qualify():
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Source22M7CrossPackage))
    source.exact.require(result.wasSuccessful(), "new M7 composition qualification failed: " + stream.getvalue())
    report = dict(Source22M7CrossPackage.report)
    report["qualification"] = {
        "kind": "Two new RAM composition cross-package checks; no Game/OS/Native function execution",
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "seconds": round(time.perf_counter() - started, 6), "runner": stream.getvalue(),
        "historical_M7_57_or_other_matrices_repeated": False,
        "new_SDK_global_imports": 0, "new_children": 0, "scratch_files": 0,
        "source_compile": "All twelve changed modules compiled in RAM; internal imports inventoried without importing SDK",
        "source_provenance_inheritance": {
            "original_M7_source_proof": {"path": str(source.OLD_PROOF), "bytes": source.OLD_PROOF_PIN[0], "sha256": source.OLD_PROOF_PIN[1]},
            "M7_scope": "Exact seven leaves plus original70137/6db hunks. Old57 software cases retained at their old source pins, not rerun or promoted to current runtime.",
            "creator_S_guard": {"path": str(source.EVIDENCE / "g2-m7-c17-no-site-direct-script-guard-2026-10-19.json"),
                                "bytes": 3096, "sha256": "a2d5e78ef791d4fd6b43dd285682f12193680abded9adeb518caf2db2b864517"},
            "owned_kernel_boundary": "Old four harmless Python-child run predates final creator guard; Native absence/module/hello were synthetic. No new loaded-provider credit.",
            "Source22": "Actual0722 full1449 inventory plus exact source bodies verified. All current recovery/performance rows retained.",
        },
    }
    report["source_package"] = {
        "source_card": {"path": "D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/SOURCE22-M7-COMPOSER96KiB-CONSUMER64KiB-SOURCE-COMMITMENTS01.json",
                        "bytes": 2106, "sha256": "41e54516937b8f0f7438439b844f6bfb886eaa1efc6709b405f645b1d1e3b79d"},
        "hard_bytes": 98304, "new_files": [], "new_file_count": 3, "scratch_bytes": 0,
        "new_production_tree_or_copy_bytes": 0,
        "full_participating_output_payload_in_existing_refs": report["output"]["changed_source_logical_bytes_each"],
        "logical_complete_gross_bytes_including_new_three": 0,
        "unmeasured_physical_RAM_peak": True,
    }
    for path in source.OWNED_FILES[:2]:
        report["source_package"]["new_files"].append({"path": str(path), **source.exact.pin(path.read_bytes())})
    report["plan_path"] = str(source.OWNED_FILES[2])
    report["plan_bytes"] = 0
    report["new_three_gross_bytes"] = 0
    for _ in range(12):
        raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
        other = sum(r["bytes"] for r in report["source_package"]["new_files"])
        total = other + len(raw)
        full = report["output"]["changed_source_logical_bytes_each"] + total
        if (report["plan_bytes"], report["new_three_gross_bytes"],
            report["source_package"]["logical_complete_gross_bytes_including_new_three"]) == (len(raw), total, full):
            break
        report["plan_bytes"] = len(raw)
        report["new_three_gross_bytes"] = total
        report["source_package"]["logical_complete_gross_bytes_including_new_three"] = full
    else:
        raise ValueError("self-size accounting failed to converge")
    source.exact.require(total <= 98304 and full <= 2621440, "complete source package exceeds admitted caps")
    return report, raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-plan", action="store_true", help="create only the named small source-plan; no SDK or Git writes")
    args = parser.parse_args()
    report, raw = qualify()
    if args.write_plan:
        target = source.OWNED_FILES[2]
        source.exact.require(target.resolve().is_relative_to(source.REPO.resolve()), "source report outside workspace")
        with target.open("xb") as stream:
            stream.write(raw)
    print(json.dumps({"status": report["status"], "plan_written": args.write_plan,
                      "plan": {"path": str(source.OWNED_FILES[2]), **source.exact.pin(raw)},
                      "output": report["output"], "new_three_gross_bytes": report["new_three_gross_bytes"],
                      "complete_gross": report["source_package"]["logical_complete_gross_bytes_including_new_three"],
                      "qualification": report["qualification"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
