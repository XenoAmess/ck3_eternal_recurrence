from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))

from test_raiktor_war_bound_regiment_contract import _active  # noqa: E402


SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_postwar_retention_expiry_capture.py"
)
COMMITTED_MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_postwar_retention_expiry_no_launch_manifest.json"
)
SPEC = importlib.util.spec_from_file_location(
    "prepare_g2_postwar_retention_expiry_capture", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot import {SCRIPT}")
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _query(generic: dict[str, object], sequence: int) -> dict[str, object]:
    return {
        "query_sequence": sequence,
        "queried_snapshot_id": "native:3",
        "queried_revision": 91,
        "queried_native_revision": 7,
        "queried_connection_generation": 1,
        "episode_run_id": "fixture-episode",
        "war_id": 50_331_699,
        "war_termination_terms": {
            "generic_war_bound_current": copy.deepcopy(generic),
            "truce": {
                "evaluated_days_observable": True,
                "evaluated_days": 1825,
                "actual_expiry_observable": False,
                "expiry_date_raw": None,
            },
        },
    }


class G2PostwarRetentionExpiryCaptureTests(unittest.TestCase):
    def _fixture(
        self, root: Path
    ) -> tuple[Path, dict[str, object], list[dict[str, object]]]:
        repo = root / "repo"
        repo.mkdir()
        generic = _active()
        generations = PREFLIGHT._generation_vector(generic)
        expected = {
            "war_id": 50_331_699,
            "character_id": 29_829,
            "opponent_character_id": 17_116,
            "date_raw": 53_175_816,
            "snapshot_id": "native:3",
            "revision": 91,
            "native_revision": 7,
            "connection_generation": 1,
            "episode_run_id": "fixture-episode",
            "ck3_pid": 4567,
            "pre_termination_soldiers": 180,
            "evaluated_days": 1825,
            "frozen_generation_sha256": PREFLIGHT._sha256_json(generations),
        }
        pre_receipt = {
            "status": "GREEN_PRODUCTION_LIVE_EVALUATED_DAYS_PRIMITIVE",
            "exact_build": {
                "game_executable_sha256": PREFLIGHT.EXPECTED_EXE_SHA256
            },
            "paused_binding": {
                key: expected[key]
                for key in (
                    "war_id",
                    "character_id",
                    "date_raw",
                    "snapshot_id",
                    "revision",
                    "native_revision",
                    "connection_generation",
                    "episode_run_id",
                )
            },
            "war_bound_observation": {
                "observed_current_soldiers": 180,
                "source_specific_attribution_ready": False,
                "proven_soldier_loss_observable": False,
            },
            "boundaries": {
                "actual_expiry_observable": False,
                "war_bound_loss_ready": False,
                "decision_ready": False,
                "automatic_surrender_ready": False,
                "gen034_closed": False,
            },
        }
        source_report = {
            "status": "green",
            "ok": True,
            "mcp_sequence": {
                "first_query": {
                    "is_error": False,
                    "structured_content": _query(generic, 1),
                },
                "second_query": {
                    "is_error": False,
                    "structured_content": _query(generic, 2),
                },
            },
            "session": {"pid": 4567},
        }
        candidate_receipt = {
            "result": "GREEN_STATIC",
            "live": False,
            "ck3_started_or_attached": False,
            "exact_build": {
                "ck3_exe_sha256": PREFLIGHT.EXPECTED_EXE_SHA256
            },
            "proved": {"exact_generation_cleanup_pairing": True},
            "not_proved": {
                "event_source_attribution": True,
                "termination_action_binding": True,
                "surrender_causality": True,
                "public_terms_readiness": True,
                "automatic_surrender": True,
                "gen_034": True,
                "production_live": True,
            },
        }
        source_contract = {
            "ck3_exe_sha256": PREFLIGHT.EXPECTED_EXE_SHA256,
            "implementation": {"default_enabled": False},
            "hard_boundaries": {"termination_action_bound": False},
        }
        values = {
            "pre_receipt": pre_receipt,
            "source_report": source_report,
            "loss_candidate_receipt": candidate_receipt,
            "loss_candidate_source_contract": source_contract,
        }
        paths: dict[str, str] = {"runner": str(SCRIPT)}
        hashes: dict[str, str] = {"runner": _sha256(SCRIPT)}
        for name, value in values.items():
            path = repo / f"{name}.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            paths[name] = str(path)
            hashes[name] = _sha256(path)
        paths["fresh_attempt"] = str(root / "fresh-attempt")
        manifest = {
            "schema": (
                "xar.ck3.g2_postwar_retention_expiry_no_launch_manifest.v1"
            ),
            "default_off": True,
            "live_authorized": False,
            "public_readiness_promoted": False,
            "gen034_closed": False,
            "paths": paths,
            "sha256": hashes,
            "pre_binding": expected,
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, expected, generations

    @staticmethod
    def _post_receipt(
        ticket: dict[str, object], generations: list[dict[str, object]]
    ) -> dict[str, object]:
        action = f"surrender-war-{ticket['war_id']}"
        runtime_pid = 9001
        runtime_connection = 2
        runtime_episode = "future-fixture-episode"
        return {
            "schema": PREFLIGHT.EXPECTED_RECEIPT_SCHEMA,
            "status": PREFLIGHT.EXPECTED_RECEIPT_STATUS,
            "retention_ticket_id": ticket["retention_ticket_id"],
            "exact_build": {
                "game_executable_sha256": PREFLIGHT.EXPECTED_EXE_SHA256
            },
            "session_binding": {
                "ck3_pid": runtime_pid,
                "connection_generation": runtime_connection,
                "episode_run_id": runtime_episode,
                "character_id": ticket["character_id"],
                "war_id": ticket["war_id"],
            },
            "pre": {
                "source_report_sha256": ticket["source_report_sha256"],
                "snapshot_id": "native:future-3",
                "revision": 10,
                "native_revision": 9,
                "date_raw": ticket["date_raw"],
                "terms_query_sequence": 2,
                "receipt_sequence": 2,
                "ck3_pid": runtime_pid,
                "connection_generation": runtime_connection,
                "episode_run_id": runtime_episode,
                "pre_termination_soldiers": ticket[
                    "pre_termination_soldiers"
                ],
                "frozen_generation_sha256": ticket[
                    "frozen_generation_sha256"
                ],
                "frozen_generations": copy.deepcopy(generations),
            },
            "termination": {
                "submitted": True,
                "accepted": True,
                "step": action,
                "war_id": ticket["war_id"],
                "receipt_sequence": 3,
                "receipt_id": "fixture-action-receipt",
                "ck3_pid": runtime_pid,
                "connection_generation": runtime_connection,
                "episode_run_id": runtime_episode,
            },
            "post": {
                "revision": 11,
                "native_revision": 10,
                "date_raw": ticket["date_raw"],
                "receipt_sequence": 4,
                "ck3_pid": runtime_pid,
                "connection_generation": runtime_connection,
                "episode_run_id": runtime_episode,
                "paused": True,
                "war_id": ticket["war_id"],
                "old_full_generation_war_id_absent": True,
                "war_bound_cleanup": {
                    "observable": True,
                    "status": "destroyed",
                    "frozen_generations": copy.deepcopy(generations),
                    "post_termination_soldiers": 0,
                    "proven_boundary_soldiers_lost": ticket[
                        "pre_termination_soldiers"
                    ],
                },
                "truce_expiry": {
                    "observable": True,
                    "source": PREFLIGHT.EXPECTED_EXPIRY_SOURCE,
                    "formula_derived": False,
                    "from_character_id": ticket["character_id"],
                    "to_character_id": ticket["opponent_character_id"],
                    "evaluated_days": ticket["evaluated_days"],
                    "queried_at_date_raw": ticket["date_raw"],
                    "expiry_date_raw": ticket["date_raw"] + 100,
                },
            },
            "mutation_commands": [action],
            "boundaries": {
                "source_specific_attribution_ready": False,
                "public_readiness_promoted": False,
                "decision_ready": False,
                "automatic_surrender_ready": False,
                "gen034_closed": False,
            },
        }

    def test_committed_manifest_is_default_off_and_pins_the_598_vector(self) -> None:
        manifest = json.loads(COMMITTED_MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(manifest["default_off"])
        self.assertFalse(manifest["live_authorized"])
        self.assertEqual(manifest["pre_binding"]["pre_termination_soldiers"], 598)
        self.assertEqual(
            manifest["pre_binding"]["frozen_generation_sha256"],
            "6BD3E54354B267F9E785DE6FB2C2B3CB16AB72ADEF53204D2DB67299A857313F",
        )
        self.assertFalse(manifest["preflight_contract"]["live_ready"])
        for name in (
            "runner",
            "pre_receipt",
            "loss_candidate_receipt",
            "loss_candidate_source_contract",
        ):
            path = Path(manifest["paths"][name])
            if not path.is_absolute():
                path = ROOT.parent / path
            self.assertEqual(_sha256(path), manifest["sha256"][name])

    def test_no_launch_preflight_emits_deterministic_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest, expected, generations = self._fixture(root)
            first = PREFLIGHT.run_preflight(
                manifest,
                root / "first.json",
                repo_root=root / "repo",
                process_inventory=lambda: [],
            )
            second = PREFLIGHT.run_preflight(
                manifest,
                root / "second.json",
                repo_root=root / "repo",
                process_inventory=lambda: [],
            )
            ticket = first["retention_ticket"]
            self.assertEqual(ticket, second["retention_ticket"])
            self.assertEqual(ticket["pre_termination_soldiers"], expected["pre_termination_soldiers"])
            self.assertEqual(ticket["frozen_generations"], generations)
            self.assertFalse(first["boundaries"]["native_expiry_reader_available"])
            self.assertFalse(first["boundaries"]["live_authorized"])

    def test_future_receipt_accepts_only_same_session_and_generation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest, _, generations = self._fixture(root)
            ticket = PREFLIGHT.build_retention_ticket(
                json.loads(manifest.read_text(encoding="utf-8")),
                repo_root=root / "repo",
            )
            receipt = self._post_receipt(ticket, generations)
            self.assertNotEqual(
                receipt["session_binding"]["ck3_pid"],
                ticket["source_ck3_pid"],
            )
            self.assertTrue(
                PREFLIGHT.validate_postwar_receipt(receipt, ticket)["ok"]
            )

            for label, mutate in (
                (
                    "process",
                    lambda value: value["session_binding"].__setitem__(
                        "ck3_pid", 9999
                    ),
                ),
                (
                    "pre generation",
                    lambda value: value["pre"]["frozen_generations"][
                        0
                    ].__setitem__("persistent_regiment_id", 9999),
                ),
                (
                    "generation",
                    lambda value: value["post"]["war_bound_cleanup"][
                        "frozen_generations"
                    ][0].__setitem__("persistent_regiment_id", 9999),
                ),
                (
                    "formula",
                    lambda value: value["post"]["truce_expiry"].__setitem__(
                        "formula_derived", True
                    ),
                ),
                (
                    "mutation",
                    lambda value: value["mutation_commands"].append(
                        "advance-days-v1-1"
                    ),
                ),
            ):
                with self.subTest(label=label):
                    malformed = copy.deepcopy(receipt)
                    mutate(malformed)
                    self.assertFalse(
                        PREFLIGHT.validate_postwar_receipt(malformed, ticket)[
                            "ok"
                        ]
                    )

    def test_preflight_rejects_existing_attempt_or_running_ck3(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest, _, _ = self._fixture(root)
            with self.assertRaises(PREFLIGHT.PreflightError):
                PREFLIGHT.run_preflight(
                    manifest,
                    root / "blocked.json",
                    repo_root=root / "repo",
                    process_inventory=lambda: [{"pid": 9}],
                )
            value = json.loads(manifest.read_text(encoding="utf-8"))
            Path(value["paths"]["fresh_attempt"]).mkdir()
            with self.assertRaises(PREFLIGHT.PreflightError):
                PREFLIGHT.run_preflight(
                    manifest,
                    root / "blocked2.json",
                    repo_root=root / "repo",
                    process_inventory=lambda: [],
                )


if __name__ == "__main__":
    unittest.main()
