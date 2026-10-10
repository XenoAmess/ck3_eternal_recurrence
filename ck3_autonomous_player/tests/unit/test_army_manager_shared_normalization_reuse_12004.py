"""One new consumer FIRST: retained Native63 packet, one registered auto-turn.

Root runs this explicit CLI once; the historical seven-scene method is not run.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import unittest
from unittest.mock import patch


_OPTIONS = None
_NORMALIZERS = (
    "normalize_current_daily_assault_roster_admission_v1",
    "normalize_current_pre_date_pending_update_inputs_v1",
    "normalize_current_post_admission_refresh_inputs_v1",
    "normalize_current_selected_title_holder_owner_relation_v1",
    "normalize_current_army_combat_roles_phase_inputs_v1",
    "normalize_current_army_flag31_inputs_v1",
)


class ArmyManagerSharedNormalizationReuse12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_shared_object_validation_reuse_and_one_registered_normal_route(self):
        from xar_autoplayer.bridge import war_contract
        from xar_autoplayer.bridge.army_strengths_manager_shared_wire import (
            FIELD_NAMES, expand_army_strengths_manager_inputs,
        )

        output = _OPTIONS.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=False)
        report_path = output / "FIRST-CONSUMER-RECEIPT.json"
        report = {"status": "RUNNING", "source_root": str(_OPTIONS.source_root.resolve()),
            "retained_native_packet": str(_OPTIONS.native_packet.resolve()),
            "native_producer_replays": 0, "old_seven_scene_test_runs": 0,
            "registered_tool": "ck3_auto_turn", "registered_calls": 0}

        def persist():
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        persist()
        try:
            self.assertEqual(Path(war_contract.__file__).resolve(),
                _OPTIONS.source_root.resolve() / "ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py")
            whole = json.loads(_OPTIONS.native_packet.read_text(encoding="utf-8"))
            original = deepcopy(whole)
            expanded = expand_army_strengths_manager_inputs(whole["result"], detached=False)
            raw_rows = expanded["army_strengths"]
            self.assertEqual(len(raw_rows), 2)
            for field in FIELD_NAMES:
                self.assertIsInstance(raw_rows[0][field], dict)
                self.assertIs(raw_rows[0][field], raw_rows[1][field])
            # The private row normalizer's default retains the original uncached path.
            expected = [war_contract._normalize_army_strength_row(row,
                name=f"army_strengths[{index}]") for index, row in enumerate(raw_rows)]

            def traced_batch(rows):
                with ExitStack() as stack:
                    spies = [stack.enter_context(patch.object(war_contract, name,
                        wraps=getattr(war_contract, name))) for name in _NORMALIZERS]
                    copies = stack.enter_context(patch.object(war_contract, "deepcopy", wraps=deepcopy))
                    normalized = war_contract.normalize_army_strengths(rows)
                    return normalized, [spy.call_count for spy in spies], copies.call_count

            normalized, calls, copies = traced_batch(raw_rows)
            self.assertEqual(normalized, expected)
            self.assertEqual(calls, [1] * 6)
            self.assertEqual(copies, 6)
            for field in FIELD_NAMES:
                self.assertIsNot(normalized[0][field], normalized[1][field])
                self.assertIsNot(normalized[0][field], raw_rows[0][field])
            field = FIELD_NAMES[1]
            normalized[1][field]["_independence_probe"] = {"value": 1}
            self.assertNotIn("_independence_probe", normalized[0][field])
            self.assertNotIn("_independence_probe", raw_rows[0][field])
            # Equal independent legacy objects must each be validated, not memoized by equality.
            legacy_rows = [deepcopy(row) for row in raw_rows]
            legacy, legacy_calls, legacy_copies = traced_batch(legacy_rows)
            self.assertEqual(legacy, expected)
            self.assertEqual(legacy_calls, [2] * 6)
            self.assertEqual(legacy_copies, 0)
            malformed = [deepcopy(row) for row in raw_rows]
            malformed[1][field] = {"malformed": True}
            with self.assertRaises(ValueError):
                war_contract.normalize_army_strengths(malformed)
            # Cache lifetime ends with the batch; the same raw inputs validate again.
            again, again_calls, _ = traced_batch(raw_rows)
            self.assertEqual(again, expected)
            self.assertEqual(again_calls, [1] * 6)
            report.update(shared_family_validator_calls=calls,
                uncached_per_row_equivalent_validator_calls=12,
                optimized_validator_calls=sum(calls), replacement_row_copies=copies,
                independent_legacy_validator_calls=legacy_calls,
                mutable_rows_independent=True, invalid_distinct_input_rejected=True,
                cache_lifetime="one normalize_army_strengths call")
            persist()
            # Reuse the already qualified real Driver/Service/registered-route harness,
            # calling only its route helper, never its seven-scene test method.
            harness_path = Path(__file__).with_name("test_army_manager_shared_registered_mcp_12004.py")
            spec = importlib.util.spec_from_file_location("_held_army_shared_route", harness_path)
            held = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(held)
            harness = held.ArmyManagerSharedRegisteredMcp12004Tests()
            with ExitStack() as stack:
                spies = [stack.enter_context(patch.object(war_contract, name,
                    wraps=getattr(war_contract, name))) for name in _NORMALIZERS]
                observed, route = await harness._run_route(
                    whole, "ck3_auto_turn", expected, output / "registered-normal",
                )
                self.assertEqual([spy.call_count for spy in spies], [1] * 6)
            rows = observed["result"]["army_strengths"]
            for actual, baseline in zip(rows, expected):
                self.assertEqual({key: actual[key] for key in baseline}, baseline)
            self.assertEqual(whole, original)
            report.update(status="GREEN", registered_calls=1, registered_route=route,
                internal_values_and_readiness_preserved=True, retained_packet_unchanged=True,
                wire_schema_changes=0, live_latency_measured=False, G2_credit_delta=0)
        except BaseException:
            report.update(status="RED", error=traceback.format_exc())
            raise
        finally:
            persist()


def main():
    global _OPTIONS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-packet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    _OPTIONS = parser.parse_args()
    project = _OPTIONS.source_root.resolve()
    sys.path[:0] = [str(project / "ck3_autonomous_player/src"),
        str(project / "ck3_workshop_mcp/src"), str(project / "tools")]
    suite = unittest.TestSuite([ArmyManagerSharedNormalizationReuse12004Tests(
        "test_shared_object_validation_reuse_and_one_registered_normal_route")])
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
