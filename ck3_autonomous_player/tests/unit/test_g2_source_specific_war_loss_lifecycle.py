from __future__ import annotations

import asyncio
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_g2_source_specific_war_loss_lifecycle.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_source_specific_war_loss_lifecycle_v1_manifest.json"
)
SPEC = importlib.util.spec_from_file_location("g2_source_loss_lifecycle", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load {SCRIPT}")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


WAR_ID = 50_331_699
ATTACKER_ID = 29_829
DEFENDER_ID = 17_116
PID = 17_292
DATE_RAW = 53_223_936


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _frozen_dependency_path(name: str, value: object) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    worktree_path = ROOT.parent / path
    if worktree_path.is_file() or name not in {
        "game_executable",
        "bookmark_events",
    }:
        return worktree_path
    installed_game_root = ROOT.parent.parent / "Crusader Kings III"
    return (
        installed_game_root / "binaries" / "ck3.exe"
        if name == "game_executable"
        else installed_game_root / "game" / "events" / "bookmark_events.txt"
    )


def _source_capture() -> dict[str, object]:
    executions: list[dict[str, object]] = []
    for index in range(6):
        current_id = 20_000 + index
        persistent_id = 30_000 + index
        army_id = 10_000 + index
        creation_soldiers = 100 + index
        executions.append(
            {
                "sequence": index + 1,
                "thread_id": 700 + index,
                "loaded_node": f"0x{0x1000 + index * 0x100:X}",
                "created_army": f"0x{0x9000 + index * 0x100:X}",
                "army_generation_id": army_id,
                "war_id": WAR_ID,
                "initial_soldiers": creation_soldiers,
                "evaluated_name": "norman_highwaymen",
                "current_regiments": [
                    {
                        "generation_id": current_id,
                        "current_soldiers": creation_soldiers,
                    }
                ],
                "persistent_regiments": [
                    {
                        "generation_id": persistent_id,
                        "war_id": WAR_ID,
                        "current_regiment_ids": [current_id],
                    }
                ],
            }
        )
    return {
        "schema": "raiktor-war-bound-private-capture-v1",
        "status": "private_test_only",
        "result": "GREEN",
        "reason": "six-action-bound-source-executions-captured",
        "read_only": True,
        "public_bridge_abi_changed": False,
        "production_detour_installed": False,
        "readiness_promotion": False,
        "pid": PID,
        "image_base": "0x140000000",
        "observation_stop_rva": "0x2E7F951",
        "observation_window_end_rva_exclusive": "0x2E7F9A6",
        "exe_sha256": RUNNER.EXPECTED_EXE_SHA256,
        "arm_proof_sha256": (
            "B7DC28B0B9EDB0F8A03E5DB2F03AD6CA1E3B649648BAE161B6A487063735B9B8"
        ),
        "event_definition_key": "bookmark.1071",
        "option_key": "bookmark.1071.a",
        "option_index": 0,
        "exact_raiktor_war_id": WAR_ID,
        "source_execution_count": 6,
        "breakpoint_installed": True,
        "original_breakpoint_byte_restored": True,
        "process_terminated": False,
        "attach_mode": True,
        "debugger_detached": True,
        "executions": executions,
    }


def _composition_row(
    ordinal: int,
    *,
    current_id: int | None = None,
    army_id: int | None = None,
    soldiers: int | None = None,
) -> dict[str, object]:
    return {
        "composition_ordinal": ordinal,
        "current_army_regiment_id": current_id,
        "raised_carmy_id": army_id,
        "current_soldiers": soldiers,
        "current_army_regiment_state": None,
        "raised_carmy_state": None,
        "frozen_carmy_roster_evidence": None,
    }


def _current_observation() -> dict[str, object]:
    capture = _source_capture()
    regiments: list[dict[str, object]] = []
    total = 0
    for index, execution in enumerate(capture["executions"]):
        current_id = execution["current_regiments"][0]["generation_id"]
        persistent_id = execution["persistent_regiments"][0]["generation_id"]
        army_id = execution["army_generation_id"]
        soldiers = 80 + index
        total += soldiers
        rows = [_composition_row(ordinal) for ordinal in range(7)]
        rows[0] = _composition_row(
            0, current_id=current_id, army_id=army_id, soldiers=soldiers
        )
        regiments.append(
            {
                "persistent_regiment_id": persistent_id,
                "bound_war_id": WAR_ID,
                "war_keep_on_attacker_victory": False,
                "current_soldiers": soldiers,
                "postwar_persistent_state": None,
                "composition_rows": rows,
            }
        )
    return {
        "schema_version": 1,
        "backend_id": "ck3-1.19.0.6-native-raiktor-war-bound-regiment-v1",
        "status": "generic_war_bound_visible_source_unattributed",
        "failure": None,
        "active_frame": {
            "snapshot_revision": 91,
            "native_revision": 7,
            "date_raw": DATE_RAW,
            "paused": True,
            "war_id": WAR_ID,
            "active_casus_belli_database_index": 411,
            "active_casus_belli_key": "raiktor_claim_cb",
            "primary_attacker_character_id": ATTACKER_ID,
            "primary_defender_character_id": DEFENDER_ID,
        },
        "postwar_frame": None,
        "owner_character_id": ATTACKER_ID,
        "war_id": WAR_ID,
        "source_attribution": {
            "mode": "authored_candidate_only",
            "authored_candidate_name": "norman_highwaymen",
            "authored_spawn_army_count": 6,
            "authored_soldiers_per_army": 500,
            "authored_total_soldiers": 3000,
        },
        "soldiers": {
            "current_soldiers_observable": True,
            "observed_current_soldiers": total,
            "pre_soldiers_observable": False,
            "observed_pre_soldiers": None,
            "proven_soldier_loss_observable": False,
            "proven_soldiers_lost": None,
        },
        "cleanup": {"observable": False, "status": None},
        "regiments": regiments,
        "readiness": {
            "exact_raiktor_war_context_ready": True,
            "generic_war_bound_identity_ready": True,
            "current_soldiers_ready": True,
            "postwar_cleanup_ready": False,
            "source_specific_attribution_ready": False,
            "pre_soldiers_ready": False,
            "proven_soldier_loss_ready": False,
            "independently_visible_value_ready": True,
            "raiktor_source_specific_domain_ready": False,
        },
    }


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:3",
        "revision": 91,
        "native_revision": 7,
        "date_raw": DATE_RAW,
        "paused": True,
        "episode_run_id": "native-29829-fixture",
        "diagnostics": {
            "connection_generation": 1,
            "bridge_pid": PID,
        },
        "played_character": {"character_id": ATTACKER_ID},
        "active_wars": [
            {
                "war_id": WAR_ID,
                "primary_opponent_character_id": DEFENDER_ID,
            }
        ],
    }


def _pre_sequence() -> dict[str, object]:
    query = {
        "query_sequence": 2,
        "queried_snapshot_id": "native:3",
        "queried_revision": 91,
        "queried_native_revision": 7,
        "queried_connection_generation": 1,
        "episode_run_id": "native-29829-fixture",
        "war_id": WAR_ID,
        "war_termination_terms": {
            "generic_war_bound_current": _current_observation(),
            "truce": {
                "evaluated_days_observable": True,
                "evaluated_days": 1825,
                "actual_expiry_observable": False,
                "expiry_date_raw": None,
            },
        },
    }
    return {
        "ok": True,
        "before_snapshot": {
            "is_error": False,
            "structured_content": _snapshot(),
        },
        "second_query": {"is_error": False, "structured_content": query},
        "public_revision": 91,
    }


class _CheckpointDriver:
    def __init__(self, save_dir: Path, *, fail: bool = False) -> None:
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.fail = fail
        self.calls: list[tuple[str, int | None]] = []

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.calls.append((step, expected_revision))
        if self.fail:
            raise RuntimeError("fixture checkpoint failure")
        checkpoint_path = self.save_dir / RUNNER.CHECKPOINT_FILENAME
        checkpoint_path.write_bytes(b"g2-source-specific-checkpoint")
        return {
            "checkpoint": {
                "status": "saved",
                "path": str(checkpoint_path.resolve()),
                "name": RUNNER.CHECKPOINT_FILENAME,
                "size": checkpoint_path.stat().st_size,
                "sha256": _sha256(checkpoint_path),
                "date_raw": DATE_RAW,
                "episode_character_id": ATTACKER_ID,
                "episode_run_id": "native-29829-fixture",
            },
            "materialization": {"available": True},
        }

    def diagnostics(self) -> dict[str, object]:
        return {"bridge_pid": PID, "connection_generation": 1}

    def take_snapshot(self) -> dict[str, object]:
        snapshot = _snapshot()
        snapshot["snapshot_id"] = "native:4"
        snapshot["revision"] = 92
        snapshot["native_revision"] = 8
        return snapshot


def _receipt(ticket: dict[str, object]) -> dict[str, object]:
    action = f"surrender-war-{WAR_ID}"
    generations = deepcopy(ticket["frozen_generations"])
    receipt = {
        "schema": RUNNER.retention.EXPECTED_RECEIPT_SCHEMA,
        "status": RUNNER.retention.EXPECTED_RECEIPT_STATUS,
        "retention_ticket_id": ticket["retention_ticket_id"],
        "exact_build": {"game_executable_sha256": RUNNER.EXPECTED_EXE_SHA256},
        "session_binding": {
            "ck3_pid": PID,
            "connection_generation": 1,
            "episode_run_id": "native-29829-fixture",
            "character_id": ATTACKER_ID,
            "war_id": WAR_ID,
        },
        "pre": {
            "source_report_sha256": ticket["source_report_sha256"],
            "snapshot_id": "native:3",
            "revision": 91,
            "native_revision": 7,
            "date_raw": DATE_RAW,
            "terms_query_sequence": 2,
            "receipt_sequence": 2,
            "ck3_pid": PID,
            "connection_generation": 1,
            "episode_run_id": "native-29829-fixture",
            "pre_termination_soldiers": ticket["pre_termination_soldiers"],
            "frozen_generation_sha256": ticket["frozen_generation_sha256"],
            "frozen_generations": generations,
        },
        "termination": {
            "submitted": True,
            "accepted": True,
            "step": action,
            "war_id": WAR_ID,
            "receipt_sequence": 3,
            "receipt_id": "fixture-receipt",
            "ck3_pid": PID,
            "connection_generation": 1,
            "episode_run_id": "native-29829-fixture",
        },
        "post": {
            "revision": 92,
            "native_revision": 8,
            "date_raw": DATE_RAW,
            "receipt_sequence": 4,
            "ck3_pid": PID,
            "connection_generation": 1,
            "episode_run_id": "native-29829-fixture",
            "paused": True,
            "war_id": WAR_ID,
            "old_full_generation_war_id_absent": True,
            "war_bound_cleanup": {
                "observable": True,
                "status": "destroyed",
                "frozen_generations": generations,
                "post_termination_soldiers": 0,
                "proven_boundary_soldiers_lost": ticket[
                    "pre_termination_soldiers"
                ],
            },
            "truce_expiry": {
                "observable": True,
                "source": RUNNER.retention.EXPECTED_EXPIRY_SOURCE,
                "formula_derived": False,
                "from_character_id": ATTACKER_ID,
                "to_character_id": DEFENDER_ID,
                "evaluated_days": 1825,
                "queried_at_date_raw": DATE_RAW,
                "expiry_date_raw": DATE_RAW + 43_800,
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
    receipt["ticket_validation"] = RUNNER.retention.validate_postwar_receipt(
        receipt, ticket
    )
    return receipt


class G2SourceSpecificWarLossLifecycleTests(unittest.TestCase):
    def _normalized(self) -> dict[str, object]:
        return RUNNER.normalize_raiktor_source_specific_capture(
            _source_capture(), capture_sha256="A" * 64
        )

    def test_builds_source_bound_dynamic_ticket_from_same_pid_generations(self) -> None:
        normalized = self._normalized()
        ticket, handoff = RUNNER.build_source_bound_ticket(
            normalized, _pre_sequence()
        )
        self.assertTrue(ticket["source_attribution_ready"])
        self.assertEqual(ticket["source_ck3_pid"], PID)
        self.assertEqual(ticket["source_set_sha256"], normalized["source_set_sha256"])
        self.assertEqual(handoff["generation_join"]["army_generation_ids"], list(range(10_000, 10_006)))
        self.assertEqual(ticket["pre_termination_soldiers"], sum(range(80, 86)))
        self.assertFalse(ticket["termination_action_bound"])

    def test_rejects_cross_pid_or_source_generation_substitution(self) -> None:
        normalized = self._normalized()
        crossed = _pre_sequence()
        crossed["before_snapshot"]["structured_content"]["diagnostics"][
            "bridge_pid"
        ] = PID + 1
        with self.assertRaisesRegex(RUNNER.LifecycleContractError, "different CK3 PIDs"):
            RUNNER.build_source_bound_ticket(normalized, crossed)

        substituted = _pre_sequence()
        generic = substituted["second_query"]["structured_content"][
            "war_termination_terms"
        ]["generic_war_bound_current"]
        generic["regiments"][5]["composition_rows"][0][
            "current_army_regiment_id"
        ] = 999_999
        with self.assertRaises(RUNNER.LifecycleContractError):
            RUNNER.build_source_bound_ticket(normalized, substituted)

    def test_full_receipt_promotes_only_private_source_loss_input(self) -> None:
        normalized = self._normalized()
        ticket, _ = RUNNER.build_source_bound_ticket(normalized, _pre_sequence())
        with tempfile.TemporaryDirectory() as temporary:
            RUNNER.create_pre_mutation_checkpoint(
                _CheckpointDriver(Path(temporary) / "save games"), ticket
            )
        receipt = _receipt(ticket)
        sequence = {
            "ok": True,
            "mutation_commands": [f"surrender-war-{WAR_ID}"],
            "postwar_receipt": receipt,
        }
        joined = RUNNER.build_source_specific_loss_join(
            normalized, ticket, sequence
        )
        self.assertTrue(joined["readiness"]["source_specific_loss_ready"])
        self.assertTrue(joined["readiness"]["comparison_input_ready"])
        self.assertFalse(joined["readiness"]["three_way_comparison_ready"])
        self.assertFalse(joined["readiness"]["decision_ready"])
        self.assertFalse(joined["readiness"]["automatic_surrender_ready"])
        self.assertEqual(
            joined["soldiers"]["proven_surrender_boundary_loss"],
            sum(range(80, 86)),
        )
        self.assertEqual(len(joined["remaining_providers"]), 3)

    def test_async_composition_reuses_one_driver_and_existing_continuation(self) -> None:
        pre = _pre_sequence()
        seen: list[tuple[str, object]] = []

        async def query(query_driver: object, **_kwargs: object) -> dict[str, object]:
            seen.append(("query", query_driver))
            return pre

        async def continue_sequence(
            continue_driver: object, **kwargs: object
        ) -> dict[str, object]:
            seen.append(("continue", continue_driver))
            ticket = kwargs["ticket"]
            return {
                "ok": True,
                "mutation_commands": [f"surrender-war-{WAR_ID}"],
                "postwar_receipt": _receipt(ticket),
            }

        with tempfile.TemporaryDirectory() as temporary:
            driver = _CheckpointDriver(Path(temporary) / "save games")
            with (
                mock.patch.object(RUNNER.terms, "_run_mcp_sequence", query),
                mock.patch.object(
                    RUNNER.postwar, "_continue_private_sequence", continue_sequence
                ),
            ):
                result = asyncio.run(
                    RUNNER.run_same_lifecycle_sequence(
                        driver,
                        source_capture=_source_capture(),
                        capture_sha256="A" * 64,
                        expected_character_id=ATTACKER_ID,
                        expected_war_id=WAR_ID,
                        expected_date_raw=DATE_RAW,
                        postwar_timeout=1.0,
                    )
                )
        self.assertTrue(result["ok"])
        self.assertEqual(seen, [("query", driver), ("continue", driver)])
        self.assertEqual(driver.calls, [("save-checkpoint", 91)])
        self.assertTrue(
            result["retention_ticket"]["termination_action_bound"]
        )
        self.assertRegex(
            result["pre_mutation_checkpoint"]["binding_sha256"],
            r"^[0-9A-F]{64}$",
        )
        post_checkpoint_frame = result["pre_mutation_checkpoint"][
            "post_checkpoint_frame"
        ]
        self.assertEqual(post_checkpoint_frame["snapshot_id"], "native:4")
        self.assertEqual(post_checkpoint_frame["revision"], 92)
        self.assertEqual(post_checkpoint_frame["native_revision"], 8)
        self.assertEqual(result["mutation_commands"], [f"surrender-war-{WAR_ID}"])

    def test_checkpoint_failure_prevents_surrender_continuation(self) -> None:
        calls: list[str] = []

        async def query(_driver: object, **_kwargs: object) -> dict[str, object]:
            calls.append("query")
            return _pre_sequence()

        async def continue_sequence(
            _driver: object, **_kwargs: object
        ) -> dict[str, object]:
            calls.append("surrender")
            raise AssertionError("surrender continuation must not run")

        with tempfile.TemporaryDirectory() as temporary:
            driver = _CheckpointDriver(
                Path(temporary) / "save games", fail=True
            )
            with (
                mock.patch.object(RUNNER.terms, "_run_mcp_sequence", query),
                mock.patch.object(
                    RUNNER.postwar, "_continue_private_sequence", continue_sequence
                ),
                self.assertRaisesRegex(RuntimeError, "checkpoint failure"),
            ):
                asyncio.run(
                    RUNNER.run_same_lifecycle_sequence(
                        driver,
                        source_capture=_source_capture(),
                        capture_sha256="A" * 64,
                        expected_character_id=ATTACKER_ID,
                        expected_war_id=WAR_ID,
                        expected_date_raw=DATE_RAW,
                        postwar_timeout=1.0,
                    )
                )
        self.assertEqual(calls, ["query"])

    def test_read_only_probe_retains_red_terms_without_checkpoint_or_action(self) -> None:
        pre = _pre_sequence()
        pre["ok"] = False
        pre["mutation_commands"] = []
        pre["checks"] = {"truce_probe": False, "mcp_results_not_errors": True}
        truce = pre["second_query"]["structured_content"][
            "war_termination_terms"
        ]["truce"]
        truce["evaluated_days_observable"] = False
        truce["evaluated_days"] = None

        async def query(query_driver: object, **_kwargs: object) -> dict[str, object]:
            self.assertIs(query_driver, driver)
            return pre

        with tempfile.TemporaryDirectory() as temporary:
            driver = _CheckpointDriver(Path(temporary) / "save games")
            with mock.patch.object(RUNNER.terms, "_run_mcp_sequence", query):
                result = asyncio.run(
                    RUNNER.run_same_lifecycle_pretermination_probe(
                        driver,
                        source_capture=_source_capture(),
                        capture_sha256="A" * 64,
                        expected_character_id=ATTACKER_ID,
                        expected_war_id=WAR_ID,
                        expected_date_raw=DATE_RAW,
                        postwar_timeout=1.0,
                    )
                )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "probe-complete")
        self.assertFalse(result["terms_ready"])
        self.assertEqual(result["failed_checks"], ["truce_probe"])
        self.assertFalse(result["truce"]["evaluated_days_observable"])
        self.assertEqual(result["mutation_commands"], [])
        self.assertFalse(result["pre_mutation_checkpoint_created"])
        self.assertFalse(result["postwar_started"])
        self.assertEqual(driver.calls, [])

    def test_wrong_explicit_war_id_fails_before_query_or_mutation(self) -> None:
        query = mock.AsyncMock()
        with mock.patch.object(RUNNER.terms, "_run_mcp_sequence", query):
            with self.assertRaisesRegex(
                RUNNER.LifecycleContractError, "explicit expected WarID"
            ):
                asyncio.run(
                    RUNNER.run_same_lifecycle_sequence(
                        object(),
                        source_capture=_source_capture(),
                        capture_sha256="A" * 64,
                        expected_character_id=ATTACKER_ID,
                        expected_war_id=WAR_ID + 1,
                        expected_date_raw=DATE_RAW,
                        postwar_timeout=1.0,
                    )
                )
        query.assert_not_awaited()

    def test_no_launch_manifest_and_preflight_are_honest(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "static-ready-no-launch")
        self.assertFalse(manifest["live_authorized"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths: dict[str, str] = {}
            hashes: dict[str, str] = {}
            required = set(manifest["paths"])
            for name in required:
                path = root / f"{name}.input"
                if name == "source_contract":
                    path.write_text(
                        json.dumps(
                            {
                                "contract": RUNNER.SOURCE_CONTRACT,
                                "default_off": True,
                                "live_authorized": False,
                            }
                        ),
                        encoding="utf-8",
                    )
                else:
                    path.write_bytes(f"fixture:{name}\n".encode("ascii"))
                paths[name] = str(path)
                hashes[name] = _sha256(path)
            fixture_manifest = {
                "schema": RUNNER.MANIFEST_SCHEMA,
                "status": "static-ready-no-launch",
                "default_off": True,
                "live_authorized": False,
                "paths": paths,
                "sha256": hashes,
                "boundaries": {
                    name: False
                    for name in (
                        "live_executed",
                        "public_readiness_promoted",
                        "action_readiness_promoted",
                        "decision_ready",
                        "automatic_surrender_ready",
                        "gen034_closed",
                    )
                },
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(fixture_manifest), encoding="utf-8")
            output = root / "preflight.json"
            with mock.patch.object(
                RUNNER,
                "EXPECTED_EXE_SHA256",
                hashes["game_executable"],
            ):
                report = RUNNER.run_no_launch_preflight(
                    manifest_path,
                    output,
                    repo_root=root,
                    process_inventory=lambda: {"counts": {"ck3.exe": 0}},
                )
        self.assertEqual(report["status"], RUNNER.EXPECTED_STATUS)
        self.assertFalse(report["boundaries"]["ck3_started_or_attached"])
        self.assertFalse(report["boundaries"]["source_specific_loss_ready"])
        self.assertFalse(report["boundaries"]["comparison_input_ready"])
        for name, value in manifest["paths"].items():
            path = _frozen_dependency_path(name, value)
            if not Path(str(value)).is_absolute():
                self.assertEqual(_sha256(path), manifest["sha256"][name])
            else:
                self.assertRegex(manifest["sha256"][name], r"^[0-9A-F]{64}$")


if __name__ == "__main__":
    unittest.main()
