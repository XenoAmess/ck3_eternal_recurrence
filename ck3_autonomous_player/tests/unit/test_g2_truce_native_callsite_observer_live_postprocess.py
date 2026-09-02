from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge/research"
FIXTURE = (
    RESEARCH
    / "fixtures/g2_truce_native_callsite_observer_live_postprocess_v1.json"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POSTPROCESSOR = _load(
    "g2_truce_native_callsite_observer_live_postprocessor",
    RESEARCH / "analyze_g2_truce_native_callsite_observer_live.py",
)


def _report_sha(report: dict[str, object]) -> str:
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest().upper()


class G2TruceNativeCallsiteObserverLivePostprocessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def _analyze(self, case: dict[str, object]) -> dict[str, object]:
        report = case["report"]
        manifest_sha = self.fixture["manifest_sha256"]
        return POSTPROCESSOR.analyze(
            report,
            self.fixture["manifest"],
            report_sha256=_report_sha(report),
            manifest_sha256=manifest_sha,
            expected_manifest_sha256=manifest_sha,
        )

    def test_fixture_covers_four_typed_terminal_classes(self) -> None:
        expected_names = {
            "installed_heartbeat_without_native_hit",
            "native_pre_call_without_return",
            "both_native_sites_return_twice_stable",
            "observer_install_or_read_failure",
        }
        self.assertEqual(
            {case["name"] for case in self.fixture["cases"]}, expected_names
        )
        for case in self.fixture["cases"]:
            with self.subTest(case=case["name"]):
                result = self._analyze(case)
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual(
                    result["classification"], case["expected_classification"]
                )
                self.assertEqual(
                    result["evaluated_days"]["observable"],
                    case["expected_evaluated_days_observable"],
                )
                self.assertFalse(result["readiness"]["promoted"])
                self.assertFalse(
                    result["readiness"]["public_readiness_changed"]
                )

    def test_only_two_stable_site_returns_publish_evaluated_days(self) -> None:
        results = {
            case["name"]: self._analyze(case)
            for case in self.fixture["cases"]
        }
        success = results["both_native_sites_return_twice_stable"]
        self.assertEqual(success["evaluated_days"]["site_0"], 1825)
        self.assertEqual(success["evaluated_days"]["site_1"], 1825)
        self.assertEqual(success["evaluated_days"]["source"], "native return EAX")
        for name, result in results.items():
            if name == "both_native_sites_return_twice_stable":
                continue
            self.assertIsNone(result["evaluated_days"]["site_0"])
            self.assertIsNone(result["evaluated_days"]["site_1"])
            self.assertIsNone(result["evaluated_days"]["source"])

    def test_success_preserves_register_thread_qpc_and_hash_bindings(self) -> None:
        case = next(
            item
            for item in self.fixture["cases"]
            if item["name"] == "both_native_sites_return_twice_stable"
        )
        result = self._analyze(case)
        self.assertEqual(
            result["observer"]["register_binding"],
            {
                "RCX": "last_script_value",
                "RDX": "last_effect_context",
                "R8": "last_evaluation_context",
                "return_EAX": "last_return_eax",
            },
        )
        rows = result["observer"]["final_callsites"]
        self.assertEqual([row["last_script_value"] for row in rows], [4352, 4608])
        self.assertEqual(
            [row["last_effect_context"] for row in rows], [8448, 8704]
        )
        self.assertEqual(
            [row["last_evaluation_context"] for row in rows], [8496, 8752]
        )
        self.assertEqual([row["last_pre_thread_id"] for row in rows], [72, 73])
        self.assertEqual([row["last_post_thread_id"] for row in rows], [72, 73])
        self.assertEqual(
            [row["last_pre_timestamp_qpc"] for row in rows], [9101, 9201]
        )
        self.assertEqual(
            [row["last_post_timestamp_qpc"] for row in rows], [9117, 9217]
        )
        self.assertEqual([row["last_return_eax"] for row in rows], [1825, 1825])
        evidence = result["input_evidence"]
        self.assertEqual(
            evidence["manifest_sha256"], self.fixture["manifest_sha256"]
        )
        self.assertEqual(
            evidence["source_commit"], POSTPROCESSOR.EXPECTED_SOURCE_COMMIT
        )
        self.assertEqual(
            evidence["source_zip_sha256"], POSTPROCESSOR.EXPECTED_SOURCE_ZIP_SHA256
        )
        self.assertTrue(result["proofs"]["session_identity"]["ok"])
        self.assertEqual(
            result["session_identity"],
            {
                "snapshot_id": "native:7",
                "snapshot_revision": 91,
                "native_revision": 7,
                "date_raw": 53_175_816,
                "connection_generation": 12,
                "episode_run_id": "native-29829-fixture",
                "episode_character_id": 29_829,
                "process_id": 1003,
            },
        )

    def test_sample_bound_is_typed_read_failure(self) -> None:
        case = copy.deepcopy(self.fixture["cases"][0])
        sample = case["report"]["observation"]["samples"][0]
        case["report"]["observation"]["samples"] = [
            copy.deepcopy(sample) for _ in range(POSTPROCESSOR.MAX_SAMPLES + 1)
        ]
        result = self._analyze(case)
        self.assertEqual(result["classification"], "read_or_install_failure")
        self.assertEqual(result["status"], "RED")
        self.assertFalse(result["proofs"]["samples_bounded"])
        self.assertFalse(result["evaluated_days"]["observable"])

    def test_manifest_hash_or_policy_mismatch_cannot_publish_a_return(self) -> None:
        case = copy.deepcopy(self.fixture["cases"][2])
        case["report"]["policy"]["evaluator_requests"] = ["forbidden"]
        result = POSTPROCESSOR.analyze(
            case["report"],
            self.fixture["manifest"],
            report_sha256=_report_sha(case["report"]),
            manifest_sha256="0" * 64,
            expected_manifest_sha256=self.fixture["manifest_sha256"],
        )
        self.assertEqual(result["classification"], "read_or_install_failure")
        self.assertFalse(result["proofs"]["manifest"]["ok"])
        self.assertFalse(result["proofs"]["runner_policy"]["ok"])
        self.assertFalse(result["evaluated_days"]["observable"])
        self.assertFalse(result["readiness"]["promoted"])

    def test_session_identity_mismatch_cannot_publish_a_return(self) -> None:
        case = copy.deepcopy(self.fixture["cases"][2])
        case["report"]["readiness"]["connection_generation"] = 0
        case["report"]["session"]["pid"] += 1
        result = self._analyze(case)

        self.assertEqual(result["classification"], "read_or_install_failure")
        self.assertEqual(result["status"], "RED")
        self.assertFalse(result["proofs"]["session_identity"]["ok"])
        self.assertIsNone(result["session_identity"])
        self.assertFalse(result["evaluated_days"]["observable"])


if __name__ == "__main__":
    unittest.main()
