from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_same_frame_white_peace_comparator import (
    COMPARISON_CONTRACT,
    PROVIDER_SCHEMA,
    SOURCE_SCHEMA,
    SameFrameWhitePeaceComparisonError,
    provide_raiktor_same_frame_white_peace_comparison,
)
from test_raiktor_white_peace_comparison_provider import _provider_inputs


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_same_frame_white_peace_comparison.py"
)
CONTRACT = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "raiktor_same_frame_white_peace_comparison_v1_contract.json"
)


def _load_script() -> object:
    spec = importlib.util.spec_from_file_location("g2_same_frame_comparator", SCRIPT)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ARTIFACT = _load_script()


def _canonical(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest().upper()


def _source(frame: dict[str, object]) -> dict[str, object]:
    body = {
        "schema": SOURCE_SCHEMA,
        "retention_ticket_id": "1" * 64,
        "source_set_sha256": "2" * 64,
        "checkpoint": {
            "path": "synthetic/do-not-ship/g2-source-before-surrender.ck3",
            "name": "g2-source-before-surrender.ck3",
            "size": 123456,
            "sha256": "3" * 64,
            "date_raw": frame["date_raw"],
        },
        "frame": {
            "ck3_pid": frame["ck3_pid"],
            "connection_generation": 1,
            "episode_run_id": frame["episode_id"],
            "character_id": frame["primary_attacker_character_id"],
            "war_id": frame["war_id"],
            "snapshot_id": frame["snapshot_id"],
            "revision": frame["snapshot_revision"],
            "native_revision": frame["native_revision"],
            "date_raw": frame["date_raw"],
            "paused": True,
        },
        "frame_checks": {
            "same_pid": True,
            "same_connection": True,
            "same_snapshot": True,
            "same_revision": True,
            "same_native_revision": True,
            "same_date": True,
            "same_episode": True,
            "same_character": True,
            "paused": True,
            "war_still_active": True,
        },
    }
    return {**body, "binding_sha256": _canonical(body)}


def _inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    candidate, terms, _campaign, _owner, observation, _utility = (
        _provider_inputs()
    )
    return _source(candidate["frame"]), observation, terms


def _write_json(path: Path, value: object) -> str:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class RaiktorSameFrameWhitePeaceComparatorTests(unittest.TestCase):
    def test_complete_inputs_publish_static_terms_comparison_only(self) -> None:
        source, white, surrender = _inputs()

        result = provide_raiktor_same_frame_white_peace_comparison(
            source_checkpoint_value=source,
            white_peace_observation_value=white,
            surrender_terms_value=surrender,
        )

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["status"], "static-ready")
        self.assertTrue(result["same_frame_comparison_ready"])
        self.assertEqual(result["blockers"], [])
        self.assertFalse(result["production_live"])
        self.assertFalse(result["production_recommendation_ready"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["action_literal"])
        self.assertFalse(result["automatic_surrender_ready"])
        self.assertFalse(result["gen034_closed"])
        certificate = result["comparison_certificate"]
        self.assertEqual(certificate["contract"], COMPARISON_CONTRACT)
        self.assertEqual(
            certificate["frame_binding"],
            {
                "snapshot_id": "fixture-native:91",
                "revision": 91,
                "native_revision": 7,
                "war_id": 50331699,
            },
        )
        comparison = certificate["terms_comparison"]
        self.assertEqual(
            comparison["primary_gold_transfer_raw"],
            {"white_peace": 0, "surrender": 15_000_000},
        )
        self.assertEqual(
            comparison["claim_disposition"],
            {
                "white_peace": "retain_declared_target_claims",
                "surrender": "remove_declared_target_claims",
            },
        )
        self.assertFalse(certificate["utility_compared"])
        self.assertIsNone(certificate["preferred_outcome"])

    def test_all_four_required_identity_drifts_fail_closed(self) -> None:
        for name, mutate in (
            (
                "snapshot_id",
                lambda source: source["frame"].__setitem__(
                    "snapshot_id", "fixture-native:92"
                ),
            ),
            (
                "revision",
                lambda source: source["frame"].__setitem__("revision", 92),
            ),
            (
                "native_revision",
                lambda source: source["frame"].__setitem__(
                    "native_revision", 8
                ),
            ),
            (
                "war_id",
                lambda source: source["frame"].__setitem__(
                    "war_id", 50331700
                ),
            ),
        ):
            with self.subTest(name=name):
                source, white, surrender = _inputs()
                mutate(source)
                source["binding_sha256"] = _canonical(
                    {key: value for key, value in source.items() if key != "binding_sha256"}
                )
                result = provide_raiktor_same_frame_white_peace_comparison(
                    source_checkpoint_value=source,
                    white_peace_observation_value=white,
                    surrender_terms_value=surrender,
                )
                self.assertEqual(result["status"], "evidence_required")
                self.assertFalse(result["same_frame_comparison_ready"])
                self.assertIsNone(result["comparison_certificate"])
                self.assertFalse(result["action_ready"])

    def test_stale_surrender_hash_and_incomplete_white_are_typed_red(self) -> None:
        source, white, surrender = _inputs()
        white["evaluated_surrender_terms_sha256"] = "F" * 64
        white["status"] = "incomplete"
        white["completeness"]["favor_hook_ready"] = False

        result = provide_raiktor_same_frame_white_peace_comparison(
            source_checkpoint_value=source,
            white_peace_observation_value=white,
            surrender_terms_value=surrender,
        )

        self.assertIn("white_peace_complete", result["blockers"])
        self.assertIn(
            "white_observation_binds_surrender_sha256", result["blockers"]
        )
        self.assertIn("surrender_snapshot_transitively_bound", result["blockers"])
        self.assertFalse(result["same_frame_comparison_ready"])

    def test_missing_inputs_do_not_default(self) -> None:
        result = provide_raiktor_same_frame_white_peace_comparison(
            source_checkpoint_value=None,
            white_peace_observation_value=None,
            surrender_terms_value=None,
        )
        self.assertEqual(result["status"], "evidence_required")
        self.assertEqual(
            result["blockers"],
            [
                "source_checkpoint_unavailable",
                "white_peace_terms_observation_unavailable",
                "surrender_terms_unavailable",
            ],
        )
        self.assertFalse(result["production_live"])
        self.assertFalse(result["gen034_closed"])

    def test_source_binding_hash_drift_is_rejected(self) -> None:
        source, white, surrender = _inputs()
        source["binding_sha256"] = "E" * 64
        with self.assertRaises(SameFrameWhitePeaceComparisonError):
            provide_raiktor_same_frame_white_peace_comparison(
                source_checkpoint_value=source,
                white_peace_observation_value=white,
                surrender_terms_value=surrender,
            )

    def test_file_comparator_hash_binds_inputs_and_refuses_overwrite(self) -> None:
        source, white, surrender = _inputs()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "source.json"
            white_path = root / "white.json"
            surrender_path = root / "surrender.json"
            output_path = root / "comparison.json"
            source_sha = _write_json(source_path, source)
            white_sha = _write_json(white_path, white)
            surrender_sha = _write_json(surrender_path, surrender)

            artifact = ARTIFACT.prepare_comparison_artifact(
                source_checkpoint_path=source_path,
                source_checkpoint_sha256=source_sha,
                white_peace_observation_path=white_path,
                white_peace_observation_sha256=white_sha,
                surrender_terms_path=surrender_path,
                surrender_terms_sha256=surrender_sha,
                output_path=output_path,
            )

            self.assertEqual(artifact["status"], "static-ready")
            self.assertTrue(output_path.is_file())
            self.assertEqual(artifact["boundaries"]["mutation_commands"], [])
            self.assertFalse(artifact["boundaries"]["ck3_started_or_attached"])
            with self.assertRaises(ARTIFACT.ComparisonArtifactError):
                ARTIFACT.prepare_comparison_artifact(
                    source_checkpoint_path=source_path,
                    source_checkpoint_sha256=source_sha,
                    white_peace_observation_path=white_path,
                    white_peace_observation_sha256=white_sha,
                    surrender_terms_path=surrender_path,
                    surrender_terms_sha256=surrender_sha,
                    output_path=output_path,
                )

    def test_contract_fixture_preserves_static_boundary(self) -> None:
        fixture = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertTrue(fixture["synthetic_fixture_only"])
        self.assertEqual(fixture["comparison_contract"], COMPARISON_CONTRACT)
        self.assertEqual(
            fixture["exact_frame_binding"]["required_equal_fields"],
            ["snapshot_id", "revision", "native_revision", "WarID"],
        )
        self.assertFalse(fixture["hard_boundaries"]["production_live"])
        self.assertFalse(fixture["hard_boundaries"]["action_ready"])
        self.assertFalse(fixture["hard_boundaries"]["gen034_closed"])


if __name__ == "__main__":
    unittest.main()
