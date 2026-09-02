from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge/research"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load(
    "g2_truce_native_callsite_observer_runner",
    RESEARCH / "run_g2_truce_native_callsite_observer_live.py",
)
VERIFIER = _load(
    "g2_truce_native_callsite_observer_verifier",
    RESEARCH / "verify_g2_truce_native_callsite_observer_candidate.py",
)


def _capabilities(*, pre0: int, post0: int, result0: int = 1825):
    rows = []
    for index, rva in enumerate(RUNNER.EXPECTED_CALL_RVAS):
        pre = pre0 if index == 0 else 0
        post = post0 if index == 0 else 0
        rows.append(
            {
                "call_instruction_rva": rva,
                "pre_call_count": pre,
                "post_call_count": post,
                "last_script_value": 0x1000 + index,
                "last_effect_context": 0x2000 + index,
                "last_evaluation_context": 0x2030 + index,
                "last_pre_thread_id": 71,
                "last_pre_timestamp_qpc": 9001,
                "last_return_eax": result0 if index == 0 else 0,
                "last_post_thread_id": 71,
                "last_post_timestamp_qpc": 9017,
            }
        )
    return {
        "diagnostics": {
            "last_heartbeat": {
                "type": "heartbeat",
                "sequence": 17,
                "pid": 1234,
                RUNNER.OBSERVER_KEY: {
                    "private_build": True,
                    "installed_mask": 3,
                    "failure": 0,
                    "callsites": rows,
                },
            }
        }
    }


class G2TruceNativeCallsiteObserverRunnerTests(unittest.TestCase):
    def test_valid_complete_native_row_has_stable_signature(self) -> None:
        sample = RUNNER._observer_sample(_capabilities(pre0=1, post0=1))
        self.assertIsNotNone(sample)
        self.assertTrue(sample["schema_ok"])
        first = RUNNER._completed_signature(sample)
        second = RUNNER._completed_signature(sample)
        self.assertIsNotNone(first)
        self.assertEqual(first, second)

    def test_pre_without_native_return_is_not_complete(self) -> None:
        sample = RUNNER._observer_sample(_capabilities(pre0=1, post0=0))
        self.assertIsNotNone(sample)
        self.assertTrue(sample["schema_ok"])
        self.assertIsNone(RUNNER._completed_signature(sample))

    def test_schema_rejects_wrong_callsite_rva(self) -> None:
        value = _capabilities(pre0=1, post0=1)
        heartbeat = value["diagnostics"]["last_heartbeat"]
        heartbeat[RUNNER.OBSERVER_KEY]["callsites"][0][
            "call_instruction_rva"
        ] = 0x3373000
        sample = RUNNER._observer_sample(value)
        self.assertIsNotNone(sample)
        self.assertFalse(sample["schema_ok"])

    def test_runner_is_heartbeat_only(self) -> None:
        source = (
            RESEARCH / "run_g2_truce_native_callsite_observer_live.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"heartbeat_only": True', source)
        self.assertIn('"mcp_queries": []', source)
        self.assertIn('"evaluator_requests": []', source)
        self.assertNotIn("query_war_termination_terms", source)
        self.assertNotIn("surrender_war", source)

    def test_runner_materializes_bound_typed_acceptance_after_cleanup(self) -> None:
        fixture = json.loads(
            (
                RESEARCH
                / "fixtures/"
                "g2_truce_native_callsite_observer_live_postprocess_v1.json"
            ).read_text(encoding="utf-8")
        )
        cases = {
            case["name"]: case for case in fixture["cases"]
        }
        for name, expected_ok in (
            ("both_native_sites_return_twice_stable", True),
            ("installed_heartbeat_without_native_hit", False),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                report_path = root / "report.json"
                manifest_path = root / "ready-to-run.json"
                RUNNER._write_json_atomic(report_path, cases[name]["report"])
                RUNNER._write_json_atomic(manifest_path, fixture["manifest"])
                manifest_sha256 = hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest().upper()

                result = RUNNER._materialize_acceptance_evidence(
                    report_path=report_path,
                    manifest_path=manifest_path,
                    expected_manifest_sha256=manifest_sha256,
                    expected_source_commit=(
                        RUNNER.postprocessor.EXPECTED_SOURCE_COMMIT
                    ),
                    expected_source_zip_sha256=(
                        RUNNER.postprocessor.EXPECTED_SOURCE_ZIP_SHA256
                    ),
                )

                acceptance = result["acceptance"]
                self.assertEqual(acceptance["ok"], expected_ok)
                self.assertEqual(
                    acceptance["input_evidence"]["runner_report_sha256"],
                    hashlib.sha256(report_path.read_bytes()).hexdigest().upper(),
                )
                self.assertEqual(
                    acceptance["input_evidence"]["ready_manifest_sha256"],
                    manifest_sha256,
                )
                self.assertEqual(
                    Path(result["typed_path"]).name, "typed-postprocess.json"
                )
                self.assertEqual(
                    Path(result["acceptance_path"]).name,
                    "acceptance-report.json",
                )
                self.assertFalse(
                    acceptance["readiness"]["action_terms_ready"]
                )
                self.assertFalse(
                    acceptance["readiness"]["decision_ready"]
                )
                self.assertFalse(
                    acceptance["readiness"]["automatic_surrender_ready"]
                )
                self.assertFalse(
                    acceptance["projection"]["expiry_observable"]
                )
                self.assertFalse(
                    acceptance["projection"]["war_bound_observable"]
                )

    def test_runner_requires_manifest_binding_for_future_candidate(self) -> None:
        source = (
            RESEARCH / "run_g2_truce_native_callsite_observer_live.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"--ready-manifest"', source)
        self.assertIn('"acceptance-report.json"', source)

    def test_verifier_freezes_exact_source_and_two_anchors(self) -> None:
        self.assertEqual(
            VERIFIER.EXPECTED_SOURCE_COMMIT,
            "0d83cc3d0affaa29878ae2311d0bd23cd2780059",
        )
        self.assertEqual(
            [rva for rva, _ in VERIFIER.ANCHORS],
            [0x2EDAF01, 0x2EDB58F],
        )
        verifier_source = (
            RESEARCH / "verify_g2_truce_native_callsite_observer_candidate.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"all_frozen_files_read_only"', verifier_source)
        self.assertIn('"postprocessor_frozen_with_candidate"', verifier_source)
        self.assertIn('"unique_command_binds_ready_manifest"', verifier_source)


if __name__ == "__main__":
    unittest.main()
