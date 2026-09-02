from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from test_war_termination_terms_contract import (
    WAR_ID,
    _available_raiktor_observed_terms,
)
from xar_autoplayer.bridge.raiktor_surrender_public_aggregate import (
    project_raiktor_surrender_six_domain,
)
from xar_autoplayer.bridge.war_contract import normalize_war_termination_terms


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "native_bridge/research"
FIXTURE = (
    RESEARCH
    / "fixtures/g2_truce_native_callsite_observer_live_postprocess_v1.json"
)
SPEC = importlib.util.spec_from_file_location(
    "g2_truce_passive_postprocessor",
    RESEARCH / "analyze_g2_truce_native_callsite_observer_live.py",
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError("cannot load G2 passive observer postprocessor")
POSTPROCESSOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POSTPROCESSOR)


def _report_sha(report: dict[str, object]) -> str:
    encoded = json.dumps(
        report, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:7",
        "revision": 91,
        "native_revision": 7,
        "date_raw": 53_175_816,
        "paused": True,
        "episode_run_id": "native-29829-fixture",
        "episode_character_id": 29_829,
        "played_character": {"character_id": 29_829, "alive": True},
        "diagnostics": {
            "connection_generation": 12,
            "bridge_pid": 1003,
        },
        "active_wars": [
            {
                "war_id": WAR_ID,
                "player_side": "attacker",
                "player_is_primary_war_leader": True,
                "primary_opponent_character_id": 41_002,
            }
        ],
    }


class RaiktorPassiveTruceAggregationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def _postprocess(self, name: str) -> dict[str, object]:
        case = next(
            item for item in self.fixture["cases"] if item["name"] == name
        )
        report = case["report"]
        manifest_sha = self.fixture["manifest_sha256"]
        return POSTPROCESSOR.analyze(
            report,
            self.fixture["manifest"],
            report_sha256=_report_sha(report),
            manifest_sha256=manifest_sha,
            expected_manifest_sha256=manifest_sha,
        )

    def _project(self, postprocess: object) -> dict[str, object]:
        terms = normalize_war_termination_terms(
            _available_raiktor_observed_terms(), expected_war_id=WAR_ID
        )
        aggregate = project_raiktor_surrender_six_domain(
            _snapshot(),
            terms,
            passive_truce_postprocess_value=postprocess,
        )
        self.assertIsInstance(aggregate, dict)
        assert isinstance(aggregate, dict)
        return aggregate

    def test_green_two_return_session_promotes_only_truce_readiness(self) -> None:
        postprocess = self._postprocess(
            "both_native_sites_return_twice_stable"
        )

        aggregate = self._project(postprocess)

        self.assertEqual(postprocess["status"], "GREEN")
        self.assertEqual(aggregate["status"], "incomplete")
        self.assertEqual(
            aggregate["missing_domains"], ["generic_war_bound_current"]
        )
        truce = aggregate["domains"]["truce"]
        self.assertTrue(truce["available"])
        self.assertEqual(truce["payload"]["evaluated_days"], 1_825)
        self.assertTrue(aggregate["readiness"]["truce_ready"])
        self.assertFalse(
            aggregate["readiness"]["generic_war_bound_current_ready"]
        )
        self.assertFalse(aggregate["readiness"]["six_dynamic_domains_ready"])
        self.assertFalse(aggregate["readiness"]["action_terms_ready"])
        self.assertFalse(
            aggregate["readiness"]["automatic_surrender_ready"]
        )

    def test_non_green_terminals_remain_typed_unavailable(self) -> None:
        for name in (
            "installed_heartbeat_without_native_hit",
            "native_pre_call_without_return",
            "observer_install_or_read_failure",
        ):
            with self.subTest(name=name):
                aggregate = self._project(self._postprocess(name))
                self.assertEqual(
                    aggregate["domains"]["truce"], {"available": False}
                )
                self.assertIn("truce", aggregate["missing_domains"])
                self.assertFalse(aggregate["readiness"]["truce_ready"])
                self.assertFalse(
                    aggregate["readiness"]["action_terms_ready"]
                )
                self.assertFalse(
                    aggregate["readiness"]["automatic_surrender_ready"]
                )

    def test_green_does_not_mutate_termination_decision_readiness(self) -> None:
        terms = normalize_war_termination_terms(
            _available_raiktor_observed_terms(), expected_war_id=WAR_ID
        )
        readiness_before = copy.deepcopy(terms["readiness"])

        aggregate = project_raiktor_surrender_six_domain(
            _snapshot(),
            terms,
            passive_truce_postprocess_value=self._postprocess(
                "both_native_sites_return_twice_stable"
            ),
        )

        self.assertIsInstance(aggregate, dict)
        self.assertEqual(terms["readiness"], readiness_before)
        self.assertFalse(terms["readiness"]["decision_ready"])
        self.assertFalse(terms["readiness"]["automatic_surrender_ready"])
        self.assertFalse(terms["readiness"]["ready"])

    def test_partial_return_remains_typed_unavailable(self) -> None:
        case = copy.deepcopy(
            next(
                item
                for item in self.fixture["cases"]
                if item["name"] == "both_native_sites_return_twice_stable"
            )
        )
        for sample in case["report"]["observation"]["samples"]:
            sample["callsites"][1]["post_call_count"] = 0
            sample["callsites"][1]["last_post_thread_id"] = 0
            sample["callsites"][1]["last_post_timestamp_qpc"] = 0
        case["report"]["status"] = "red"
        case["report"]["ok"] = False
        case["report"]["error"] = (
            "RuntimeError: observation_timeout_without_stable_native_return"
        )
        case["report"]["observation"]["result"] = (
            "observation_timeout_without_stable_native_return"
        )
        manifest_sha = self.fixture["manifest_sha256"]
        postprocess = POSTPROCESSOR.analyze(
            case["report"],
            self.fixture["manifest"],
            report_sha256=_report_sha(case["report"]),
            manifest_sha256=manifest_sha,
            expected_manifest_sha256=manifest_sha,
        )

        aggregate = self._project(postprocess)

        self.assertEqual(
            postprocess["classification"], "incomplete_two_site_return"
        )
        self.assertEqual(aggregate["domains"]["truce"], {"available": False})
        self.assertFalse(aggregate["readiness"]["action_terms_ready"])
        self.assertFalse(aggregate["readiness"]["automatic_surrender_ready"])

    def test_manifest_source_or_session_drift_remains_unavailable(self) -> None:
        original = self._postprocess(
            "both_native_sites_return_twice_stable"
        )
        mutations = (
            lambda value: value["input_evidence"].__setitem__(
                "manifest_sha256", "0" * 64
            ),
            lambda value: value["input_evidence"].__setitem__(
                "source_commit", "0" * 40
            ),
            lambda value: value["session_identity"].__setitem__(
                "episode_run_id", "stale-episode"
            ),
            lambda value: value["session_identity"].__setitem__(
                "process_id", 1004
            ),
            lambda value: value["session_identity"].__setitem__(
                "snapshot_revision", 92
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = copy.deepcopy(original)
                mutate(value)
                aggregate = self._project(value)
                self.assertEqual(
                    aggregate["domains"]["truce"], {"available": False}
                )
                self.assertFalse(aggregate["readiness"]["truce_ready"])
                self.assertFalse(
                    aggregate["readiness"]["action_terms_ready"]
                )
                self.assertFalse(
                    aggregate["readiness"]["automatic_surrender_ready"]
                )

    def test_two_callsites_must_return_the_same_stable_days(self) -> None:
        value = self._postprocess("both_native_sites_return_twice_stable")
        value["evaluated_days"]["site_1"] = 1_826
        value["observer"]["final_callsites"][1]["last_return_eax"] = 1_826

        aggregate = self._project(value)

        self.assertEqual(aggregate["domains"]["truce"], {"available": False})
        self.assertFalse(aggregate["readiness"]["truce_ready"])
        self.assertFalse(aggregate["readiness"]["action_terms_ready"])
        self.assertFalse(aggregate["readiness"]["automatic_surrender_ready"])


if __name__ == "__main__":
    unittest.main()
