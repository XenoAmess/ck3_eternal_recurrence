"""Focused tests for the bounded private-probe readiness-call contract."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "validate_private_probe_readiness_contract.py"
SPEC = importlib.util.spec_from_file_location("private_probe_readiness_contract", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load private-probe readiness validator")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


READINESS_SOURCE = """
def _wait_for_readiness(
    driver,
    *,
    session_done,
    session_state,
    timeout_seconds,
    stable_seconds,
    poll_interval_seconds,
    cold_start_checkpoint,
    allow_terminal,
):
    return {}
"""

GOOD_RUNNER = """
EXPECTED_OWNER = 29829

def run(driver):
    binding = _wait_for_readiness(
        driver,
        session_done=object(),
        session_state={},
        timeout_seconds=300.0,
        stable_seconds=1.0,
        poll_interval_seconds=0.1,
        cold_start_checkpoint=False,
        allow_terminal=False,
    )
    snapshot = driver.take_internal_semantic_snapshot()
    if snapshot.get("episode_character_id") != EXPECTED_OWNER:
        raise RuntimeError("wrong player")
    return binding
"""

LEGACY_RUNNER = GOOD_RUNNER.replace(
    "        allow_terminal=False,\n",
    "        allow_terminal=False,\n        expected_character_id=EXPECTED_OWNER,\n",
)


class PrivateProbeReadinessContractTest(unittest.TestCase):
    def test_r689_unsupported_character_keyword_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            MODULE.ContractError,
            "unsupported .*expected_character_id",
        ):
            MODULE.validate_runner_contract(
                readiness_source=READINESS_SOURCE,
                runner_source=LEGACY_RUNNER,
                expected_character_id=29829,
            )

    def test_supported_call_and_independent_character_check_are_accepted(self) -> None:
        result = MODULE.validate_runner_contract(
            readiness_source=READINESS_SOURCE,
            runner_source=GOOD_RUNNER,
            expected_character_id=29829,
        )
        self.assertEqual(result["status"], "green")
        self.assertNotIn("expected_character_id", result["keyword_arguments"])
        self.assertEqual(result["expected_character_id"], 29829)
        self.assertEqual(
            result["character_binding_source"],
            "post-readiness internal semantic snapshot",
        )


if __name__ == "__main__":
    unittest.main()
