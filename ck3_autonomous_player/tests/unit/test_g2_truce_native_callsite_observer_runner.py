from __future__ import annotations

import importlib.util
from pathlib import Path
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

    def test_verifier_freezes_exact_source_and_two_anchors(self) -> None:
        self.assertEqual(
            VERIFIER.EXPECTED_SOURCE_COMMIT,
            "36fafd811b29bba11758d1ebc3929be8cbd4c9d4",
        )
        self.assertEqual(
            [rva for rva, _ in VERIFIER.ANCHORS],
            [0x2EDAF01, 0x2EDB58F],
        )
        verifier_source = (
            RESEARCH / "verify_g2_truce_native_callsite_observer_candidate.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"all_frozen_files_read_only"', verifier_source)


if __name__ == "__main__":
    unittest.main()
