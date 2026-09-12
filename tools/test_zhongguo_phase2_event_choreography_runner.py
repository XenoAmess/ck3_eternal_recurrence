#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import sys
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_zhongguo_acceptance as capture  # noqa: E402
from zhongguo_phase2_capture_choreography import (  # noqa: E402
    PHASE2_CAPTURE_SCENARIOS,
)
from zhongguo_phase2_event_choreography import (  # noqa: E402
    Phase2EventChoreographyError,
    phase2_event_sequence_plan,
)
from zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    CHECKPOINT_REQUIRED_HANDLERS,
    INCIDENT_STRICT_RECEIPT_FIELD,
    LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
    SOURCE_CHECKPOINT_REGISTRY_KIND,
    SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
)
from test_zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    _registry as _schema3_checkpoint_registry,
)
from test_zhongguo_phase2_source_checkpoint_registry import (  # noqa: E402
    strict_incident_checkpoint,
)
from test_zg361_phase2_cross_cycle_endgame_source_capture import (  # noqa: E402
    DATE_RAW as ENDGAME_DATE_RAW,
    OWNER as ENDGAME_OWNER,
    maturity_receipt_fields,
)


def _snapshot(*, event: bool = False) -> dict[str, object]:
    return {
        "snapshot_id": "runner:10",
        "revision": 10,
        "native_revision": 110,
        "date_raw": 777,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 9001, "alive": True},
        "diagnostics": {"bridge_pid": 4321, "connection_generation": 4},
        "active_event": {"instance_id": 901, "option_count": 1} if event else None,
    }


def _scoreboard(*, visible: bool) -> dict[str, object]:
    return {
        "status": "available",
        "widgets": [
            {
                "stable_identity": "zg361_scoreboard_modal",
                "exists": {"status": "available", "value": True},
                "effective_visible": {"status": "available", "value": visible},
            }
        ],
    }


class _Service:
    def __init__(self, snapshot: dict[str, object] | None = None) -> None:
        self.current = snapshot or _snapshot()

    def snapshot(self) -> dict[str, object]:
        return self.current

    def query_zhongguo_scoreboard_state_v1(
        self, _nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        self.expected_revision = expected_revision
        return _scoreboard(visible=False)


def _checkpoint_registry(root: Path) -> dict[str, object]:
    entries = []
    for index, handler in enumerate(CHECKPOINT_REQUIRED_HANDLERS, 1):
        plan = phase2_event_sequence_plan(handler)
        strict_receipt = None
        if handler == "capture_incidents_operations":
            strict_receipt, path = strict_incident_checkpoint(
                root, seed_lineage_id="seed-unit"
            )
            owner = int(strict_receipt["owner_character_id"])
            player = int(strict_receipt["player_character_id"])
            date_raw = int(strict_receipt["date_raw"])
        else:
            path = (root / f"{index}.ck3").resolve()
            path.write_bytes(f"checkpoint-{index}".encode("ascii"))
            owner = 9200 + index
            player = 9001
            date_raw = 800 + index
            if handler == "capture_cross_cycle_endgame":
                owner = ENDGAME_OWNER
                player = ENDGAME_OWNER
                date_raw = ENDGAME_DATE_RAW
        sha = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        row = {
                "span_id": plan.span_id,
                "handler": handler,
                "source_event_definition_key": plan.source_event,
                "owner_character_id": owner,
                "player_character_id": player,
                "date_raw": date_raw,
                "checkpoint": {
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha,
                    "save_lineage_id": "seed-unit",
                },
                "source_receipt": {
                    "result": "GREEN",
                    "evidence_class": "real_ck3",
                    "provider_observed": True,
                    "ui_state_verified": True,
                    "fixture_used": False,
                    "console_used": False,
                    "span_id": plan.span_id,
                    "event_definition_key": plan.source_event,
                    "owner_character_id": owner,
                    "player_character_id": player,
                    "date_raw": date_raw,
                    "checkpoint_sha256": sha,
                    "save_lineage_id": "seed-unit",
                },
            }
        if strict_receipt is not None:
            receipt_path = root / "strict-incident-input" / "receipt.json"
            row[INCIDENT_STRICT_RECEIPT_FIELD] = {
                "kind": (
                    "zg361_phase2_incidents_operations_"
                    "source_checkpoint_receipt"
                ),
                "path": str(receipt_path.resolve()),
                "bytes": receipt_path.stat().st_size,
                "sha256": hashlib.sha256(
                    receipt_path.read_bytes()
                ).hexdigest().upper(),
            }
        if handler == "capture_cross_cycle_endgame":
            row["source_receipt"].update(maturity_receipt_fields())
        entries.append(row)
    return {
        "schema_version": LEGACY_SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION,
        "registry_kind": SOURCE_CHECKPOINT_REGISTRY_KIND,
        "result": "GREEN",
        "evidence_class": "real_ck3",
        "fixture_used": False,
        "console_used": False,
        "seed_lineage_id": "seed-unit",
        "capture_lineage": {"seed_lineage_id": "seed-unit"},
        "entries": entries,
    }


class Phase2EventChoreographyRunnerTests(unittest.TestCase):
    @staticmethod
    def _incident_seed_contract(*, incident_owner: int) -> dict[str, object]:
        return {
            "domain_query_matrix": {
                "schema_version": 1,
                "b2_pip_owner_character_id": 8101,
                "incident_owner_character_id": incident_owner,
                "workforce_owner_character_id": 8103,
                "ai_owned_case_owner_character_id": 8104,
                "ai_owned_case_subject_character_id": 8105,
            }
        }

    def test_formal_preflight_binds_strict_incident_receipt_to_runner(self) -> None:
        class RestoreService(_Service):
            def restore_phase2_span_source_checkpoint_v1(self, **_kwargs):
                return {}

        with tempfile.TemporaryDirectory() as temporary:
            registry = _checkpoint_registry(Path(temporary))
            incident = next(
                row
                for row in registry["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            player = int(incident["player_character_id"])
            owner = int(incident["owner_character_id"])
            runtime_snapshot = _snapshot()
            runtime_snapshot["played_character"]["character_id"] = player
            context = SimpleNamespace(
                seed_contract=self._incident_seed_contract(
                    incident_owner=owner
                ),
                source_checkpoint_registry=registry,
                recorder=SimpleNamespace(
                    phase2_capture_lineage={"seed_lineage_id": "seed-unit"}
                ),
            )
            result = capture._Phase2RealEventChoreographyService(
                RestoreService()
            ).preflight_source_checkpoints(
                context, {"paused_snapshot": runtime_snapshot}
            )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(
            result["incident_runner_binding"]["required_postcondition"],
            "incident_xyz_terminal_kpi_plus_wrong_owner_typed_red",
        )
        self.assertFalse(
            result["incident_runner_binding"][
                "action_ack_is_result_evidence"
            ]
        )

    def test_formal_preflight_accepts_schema3_multi_branch_registry(self) -> None:
        class RestoreService(_Service):
            def restore_phase2_span_source_checkpoint_v1(self, **_kwargs):
                return {}

        with tempfile.TemporaryDirectory() as temporary:
            registry = _schema3_checkpoint_registry(
                Path(temporary), multi_branch=True
            )
            incident = next(
                row
                for row in registry["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            runtime_snapshot = _snapshot()
            runtime_snapshot["played_character"]["character_id"] = incident[
                "player_character_id"
            ]
            context = SimpleNamespace(
                seed_contract={},
                source_checkpoint_registry=registry,
                recorder=SimpleNamespace(
                    phase2_capture_lineage={
                        "seed_lineage_id": "different-runtime-seed"
                    }
                ),
            )
            result = capture._Phase2RealEventChoreographyService(
                RestoreService()
            ).preflight_source_checkpoints(
                context, {"paused_snapshot": runtime_snapshot}
            )

        self.assertEqual(
            result["schema_version"], SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["lineage_set_id"], registry["lineage_set_id"])
        self.assertEqual(
            result["handler_save_lineage_ids"][
                "capture_incidents_operations"
            ],
            incident["save_lineage_id"],
        )
        self.assertEqual(
            result["incident_runner_binding"]["owner_character_id"],
            incident["owner_character_id"],
        )

    def test_formal_preflight_rejects_missing_schema3_lineage_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = _schema3_checkpoint_registry(
                Path(temporary), multi_branch=True
            )
            registry.pop("lineage_set_id")
            context = SimpleNamespace(
                source_checkpoint_registry=registry,
                recorder=SimpleNamespace(
                    phase2_capture_lineage={"seed_lineage_id": "unused"}
                ),
            )
            with self.assertRaises(Phase2EventChoreographyError) as raised:
                capture._Phase2RealEventChoreographyService(
                    _Service()
                ).preflight_source_checkpoints(context, {})

        self.assertEqual(
            raised.exception.reason_code, "source_checkpoint_preflight_red"
        )
        self.assertEqual(
            raised.exception.evidence["upstream_reason_code"],
            "source_checkpoint_registry_header_invalid",
        )

    def test_formal_preflight_rejects_wrong_schema3_lineage_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = _schema3_checkpoint_registry(
                Path(temporary), multi_branch=True
            )
            registry["lineage_set_id"] = (
                "zg361-phase2-lineage-set-" + "0" * 64
            )
            context = SimpleNamespace(
                source_checkpoint_registry=registry,
                recorder=SimpleNamespace(
                    phase2_capture_lineage={"seed_lineage_id": "unused"}
                ),
            )
            with self.assertRaises(Phase2EventChoreographyError) as raised:
                capture._Phase2RealEventChoreographyService(
                    _Service()
                ).preflight_source_checkpoints(context, {})

        self.assertEqual(
            raised.exception.reason_code, "source_checkpoint_preflight_red"
        )
        self.assertEqual(
            raised.exception.evidence["upstream_reason_code"],
            "source_checkpoint_registry_lineage_set_invalid",
        )

    def test_registered_schema3_source_restores_its_handler_lineage(self) -> None:
        class RestoreService(_Service):
            def restore_phase2_span_source_checkpoint_v1(self, **kwargs):
                self.restore_kwargs = kwargs
                return {
                    "result": "GREEN",
                    "provider_observed": True,
                    "checkpoint_sha256": kwargs["expected_checkpoint_sha256"],
                    "save_lineage_id": kwargs["expected_save_lineage_id"],
                    "player_character_id": kwargs["expected_player_character_id"],
                    "owner_character_id": kwargs["expected_owner_character_id"],
                    "date_raw": kwargs["expected_date_raw"],
                    "event_definition_key": kwargs[
                        "expected_event_definition_key"
                    ],
                    "fixture_used": False,
                    "console_used": False,
                    "generic_character_rebind_used": False,
                }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = _schema3_checkpoint_registry(root, multi_branch=True)
            plan = phase2_event_sequence_plan(
                "capture_promotion_compensation"
            )
            entry = next(
                row for row in registry["entries"] if row["handler"] == plan.handler
            )
            service = RestoreService()
            adapter = capture._Phase2RealEventChoreographyService(service)
            context = SimpleNamespace(
                source_checkpoint_registry=registry,
                recorder=SimpleNamespace(
                    phase2_capture_lineage={
                        "seed_lineage_id": "different-runtime-seed"
                    }
                ),
                artifacts=root,
            )
            with mock.patch.object(
                adapter,
                "_wait_event",
                return_value={
                    "binding": {
                        "player_character_id": entry["player_character_id"],
                        "date_raw": entry["date_raw"],
                    }
                },
            ):
                result = adapter.stage_span_source(
                    plan, PHASE2_CAPTURE_SCENARIOS[3], context, {}
                )

        self.assertEqual(result["event_definition_key"], plan.source_event)
        self.assertEqual(
            service.restore_kwargs["expected_save_lineage_id"],
            entry["save_lineage_id"],
        )
        self.assertNotEqual(
            service.restore_kwargs["expected_save_lineage_id"],
            "different-runtime-seed",
        )

    def test_formal_preflight_uses_strict_owner_not_stale_seed_selector(
        self,
    ) -> None:
        class RestoreService(_Service):
            def restore_phase2_span_source_checkpoint_v1(self, **_kwargs):
                return {}

        with tempfile.TemporaryDirectory() as temporary:
            registry = _checkpoint_registry(Path(temporary))
            incident = next(
                row
                for row in registry["entries"]
                if row["handler"] == "capture_incidents_operations"
            )
            runtime_snapshot = _snapshot()
            runtime_snapshot["played_character"]["character_id"] = incident[
                "player_character_id"
            ]
            context = SimpleNamespace(
                seed_contract=self._incident_seed_contract(
                    incident_owner=8199
                ),
                source_checkpoint_registry=registry,
                recorder=SimpleNamespace(
                    phase2_capture_lineage={"seed_lineage_id": "seed-unit"}
                ),
            )
            result = capture._Phase2RealEventChoreographyService(
                RestoreService()
            ).preflight_source_checkpoints(
                context, {"paused_snapshot": runtime_snapshot}
            )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(
            result["incident_runner_binding"]["owner_character_id"],
            incident["owner_character_id"],
        )
        self.assertNotEqual(
            result["incident_runner_binding"]["owner_character_id"], 8199
        )
        self.assertEqual(
            result["incident_runner_binding"]["owner_source"],
            "zg361.50:zg361_notice_prompt_owner",
        )

    def test_incident_runner_rejects_ack_only_green_without_provider_proof(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            ack_only = {
                "schema_version": 1,
                "result": "GREEN",
                "selection_submissions": [
                    {"ack": {"accepted": True, "status": "submitted"}}
                ],
                "checks": {"ack_not_used_as_result": False},
            }
            with mock.patch.object(
                capture,
                "run_incident_xyz_gameplay_action_cell",
                return_value=ack_only,
            ):
                with self.assertRaises(capture.acceptance.RunnerError):
                    capture.run_phase2_incident_gameplay_action_cell(
                        _Service(),
                        artifacts,
                        owner_character_id=8052,
                    )
            self.assertEqual(
                json.loads(
                    (
                        artifacts
                        / "05_phase2_incident_xyz_gameplay_action_cell.json"
                    ).read_text(encoding="utf-8-sig")
                ),
                ack_only,
            )

    def test_required_source_without_real_registry_is_explicit_red(self) -> None:
        service = _Service()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_promotion_compensation")
        scenario = PHASE2_CAPTURE_SCENARIOS[3]
        context = SimpleNamespace(
            seed_contract={},
            source_checkpoint_registry=None,
            recorder=SimpleNamespace(
                phase2_capture_lineage={"seed_lineage_id": "seed-unit"}
            ),
            artifacts=Path("unused"),
        )
        with self.assertRaises(Phase2EventChoreographyError) as raised:
            adapter.stage_span_source(plan, scenario, context, {})
        self.assertEqual(
            raised.exception.reason_code, "source_checkpoint_provider_red"
        )
        self.assertEqual(
            raised.exception.evidence["upstream_reason_code"],
            "source_checkpoint_registry_missing",
        )

    def test_registered_source_uses_only_narrow_restore_then_exact_live_binding(self) -> None:
        class RestoreService(_Service):
            def restore_phase2_span_source_checkpoint_v1(self, **kwargs):
                self.restore_kwargs = kwargs
                return {
                    "result": "GREEN",
                    "provider_observed": True,
                    "checkpoint_sha256": kwargs["expected_checkpoint_sha256"],
                    "save_lineage_id": kwargs["expected_save_lineage_id"],
                    "player_character_id": kwargs["expected_player_character_id"],
                    "owner_character_id": kwargs["expected_owner_character_id"],
                    "date_raw": kwargs["expected_date_raw"],
                    "event_definition_key": kwargs["expected_event_definition_key"],
                    "fixture_used": False,
                    "console_used": False,
                    "generic_character_rebind_used": False,
                }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = _checkpoint_registry(root)
            plan = phase2_event_sequence_plan("capture_promotion_compensation")
            entry = next(row for row in registry["entries"] if row["handler"] == plan.handler)
            service = RestoreService()
            adapter = capture._Phase2RealEventChoreographyService(service)
            context = SimpleNamespace(
                seed_contract={},
                source_checkpoint_registry=registry,
                recorder=SimpleNamespace(
                    phase2_capture_lineage={"seed_lineage_id": "seed-unit"}
                ),
                artifacts=root,
            )
            live_snapshot = _snapshot(event=True)
            live_snapshot["date_raw"] = entry["date_raw"]
            live_snapshot["played_character"]["character_id"] = entry[
                "player_character_id"
            ]
            identity = {
                "event_instance_id": 901,
                "snapshot_revision": 10,
                "event_definition_key": plan.source_event,
            }
            with mock.patch.object(
                capture,
                "wait_for_native_event_definition",
                return_value={
                    "snapshot": live_snapshot,
                    "identity": identity,
                    "evidence": {"result": "GREEN"},
                },
            ):
                result = adapter.stage_span_source(
                    plan, PHASE2_CAPTURE_SCENARIOS[3], context, {}
                )
        self.assertEqual(result["event_definition_key"], "zg361pp.147")
        self.assertFalse(service.restore_kwargs["allow_generic_character_rebind"])
        self.assertFalse(service.restore_kwargs["allow_fixture"])
        self.assertFalse(service.restore_kwargs["allow_console"])
    def test_event_free_source_and_drain_use_paused_native_and_scoreboard_providers(self) -> None:
        service = _Service()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_fact_quota_calibration")
        scenario = PHASE2_CAPTURE_SCENARIOS[0]
        context = SimpleNamespace(artifacts=Path("unused"))
        staged = adapter.stage_span_source(plan, scenario, context, {})
        drained = adapter.drain_after_span(plan, context, {})
        self.assertTrue(staged["no_active_event"])
        self.assertFalse(staged["scoreboard_modal_visible"])
        self.assertTrue(drained["no_active_event"])
        self.assertTrue(drained["no_blocking_surface"])
        self.assertFalse(staged["console_used"])
        self.assertFalse(staged["test_fixture_used"])

    def test_event_free_source_accepts_exact_hidden_modal_diagnostic(self) -> None:
        class ProjectionUnavailableService(_Service):
            def query_zhongguo_scoreboard_state_v1(
                self, _nonce: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.expected_revision = expected_revision
                return {
                    **_scoreboard(visible=False),
                    "status": "unavailable",
                    "unavailable_reason": "state_projection_unavailable",
                }

        service = ProjectionUnavailableService()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_manager_governance")
        with mock.patch.object(
            adapter,
            "_restore_player_manager_source",
            return_value={"result": "GREEN"},
        ):
            staged = adapter.stage_span_source(
                plan,
                PHASE2_CAPTURE_SCENARIOS[2],
                SimpleNamespace(artifacts=Path("unused")),
                {},
            )
        self.assertFalse(staged["scoreboard_modal_visible"])
        self.assertEqual(service.expected_revision, 10)

    def test_manager_source_restores_player_publication_checkpoint_before_span(self) -> None:
        class RestoreService(_Service):
            @staticmethod
            def phase2_span_source_checkpoint_restore_available_v1() -> bool:
                return True

            def restore_phase2_span_source_checkpoint_v1(self, **kwargs):
                self.restore_kwargs = kwargs
                self.current["played_character"]["character_id"] = kwargs[
                    "expected_player_character_id"
                ]
                self.current["date_raw"] = kwargs["expected_date_raw"]
                return {"result": "GREEN", "provider_observed": True}

        service = RestoreService()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_manager_governance")
        manager_source = {
            "result": "GREEN",
            "checkpoint": {
                "path": "C:/manager.ck3",
                "bytes": 123,
                "sha256": "A" * 64,
                "save_lineage_id": "zg361-stage10-player-manager-unit",
            },
            "expected_event_definition_key": (
                "event_free_map:stage10_player_manager_source"
            ),
            "player_manager_character_id": 27181,
            "owner_character_id": 36354,
            "date_raw": 53155680,
        }
        result = adapter.stage_span_source(
            plan,
            PHASE2_CAPTURE_SCENARIOS[2],
            SimpleNamespace(
                artifacts=Path("unused"),
                manager_source_receipt=manager_source,
            ),
            {},
        )

        self.assertTrue(result["no_active_event"])
        self.assertEqual(
            result["binding"]["player_character_id"], 27181
        )
        self.assertEqual(
            service.restore_kwargs["expected_owner_character_id"], 36354
        )
        self.assertFalse(service.restore_kwargs["allow_fixture"])
        self.assertEqual(
            result["player_manager_source_restore"]["result"], "GREEN"
        )

    def test_product_source_wait_never_auto_clears_an_unexpected_event(self) -> None:
        service = _Service()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_receipt_appeal_pip")
        scenario = PHASE2_CAPTURE_SCENARIOS[1]
        identity = {
            "event_instance_id": 901,
            "snapshot_revision": 10,
            "event_definition_key": "zg361b2.40",
        }
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            capture,
            "wait_for_native_event_definition",
            return_value={
                "snapshot": _snapshot(event=True),
                "identity": identity,
                "evidence": {"result": "GREEN"},
            },
        ) as wait:
            result = adapter.stage_span_source(
                plan,
                scenario,
                SimpleNamespace(artifacts=Path(temporary)),
                {},
            )
        self.assertEqual(result["event_definition_key"], "zg361b2.40")
        self.assertFalse(wait.call_args.kwargs["clear_unexpected_single_option_events"])

    def test_event_close_binds_exact_identity_and_requires_instance_transition(self) -> None:
        service = _Service(_snapshot(event=True))
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_manager_governance")
        context = SimpleNamespace(artifacts=Path("unused"))
        with (
            mock.patch.object(
                capture,
                "query_event_definition_identity",
                return_value={
                    "event_instance_id": 901,
                    "event_definition_key": "zg361mg.120",
                },
            ),
            mock.patch.object(
                capture,
                "select_single_option_interruption_native",
                return_value={"result": "GREEN"},
            ) as close,
        ):
            result = adapter.close_capture_surface(
                "product_event", "zg361mg.120", plan, context, {}
            )
        self.assertTrue(result["transition_materialized"])
        self.assertEqual(close.call_args.kwargs["expected_event_instance_id"], 901)

    def test_promotion_successor_close_selects_canonical_first_option(self) -> None:
        snapshot = _snapshot(event=True)
        snapshot["active_event"]["option_count"] = 3
        service = _Service(snapshot)
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan(capture.PROMOTION_HANDLER)
        context = SimpleNamespace(artifacts=Path("unused"))
        with (
            mock.patch.object(
                capture,
                "query_event_definition_identity",
                return_value={
                    "event_instance_id": 901,
                    "event_definition_key": "zg361pp.148",
                },
            ),
            mock.patch.object(
                capture,
                "select_bound_event_option_native",
                return_value={"result": "GREEN"},
            ) as close,
            mock.patch.object(
                capture, "select_single_option_interruption_native"
            ) as single_option_close,
        ):
            result = adapter.close_capture_surface(
                "product_event", "zg361pp.148", plan, context, {}
            )
        self.assertTrue(result["transition_materialized"])
        close.assert_called_once_with(
            service,
            Path("unused"),
            "phase2_promo_phase2_promotion_compensation_zg361pp_148_close",
            expected_event_instance_id=901,
            option_number=1,
        )
        single_option_close.assert_not_called()

    def test_scoreboard_close_uses_provider_owned_close_and_later_query(self) -> None:
        service = _Service()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_fact_quota_calibration")
        close_evidence = {
            "result": "GREEN",
            "verified_pass": True,
            "production_capability_advertised": True,
            "action_request": {"action": "close"},
            "later_query": _scoreboard(visible=False),
        }
        with mock.patch.object(
            capture,
            "run_zhongguo_scoreboard_action_cell",
            return_value=close_evidence,
        ) as close:
            result = adapter.close_capture_surface(
                "named_widget",
                "zg361_scoreboard_modal",
                plan,
                SimpleNamespace(artifacts=Path("unused")),
                {},
            )
        self.assertTrue(result["transition_materialized"])
        close.assert_called_once_with(
            mock.ANY,
            nonce_prefix=(
                "zg361.phase2.promo.phase2_fact_quota_calibration.close"
            ),
            requested_action="close",
        )

    def test_scoreboard_close_accepts_verified_capture_candidate_boundary(self) -> None:
        service = _Service()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_fact_quota_calibration")
        close_evidence = {
            "result": "RED",
            "verified_pass": True,
            "production_capability_advertised": False,
            "failure_reason": "production_capability_not_advertised",
            "action_request": {"action": "close"},
            "later_query": _scoreboard(visible=False),
        }
        with mock.patch.object(
            capture,
            "run_zhongguo_scoreboard_action_cell",
            return_value=close_evidence,
        ):
            result = adapter.close_capture_surface(
                "named_widget",
                "zg361_scoreboard_modal",
                plan,
                SimpleNamespace(artifacts=Path("unused")),
                {},
            )
        self.assertTrue(result["transition_materialized"])
        self.assertEqual(result["close"], close_evidence)

    def test_drain_is_red_on_unknown_visible_event_instead_of_selecting_it(self) -> None:
        service = _Service(_snapshot(event=True))
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_fact_quota_calibration")
        with mock.patch.object(
            capture,
            "query_event_definition_identity",
            return_value={"event_definition_key": "some.other.event"},
        ):
            with self.assertRaises(Phase2EventChoreographyError) as raised:
                adapter.drain_after_span(
                    plan, SimpleNamespace(artifacts=Path("unused")), {}
                )
        self.assertEqual(raised.exception.reason_code, "span_drain_not_empty")

    def test_manager_action_waits_for_120_before_visible_surface_gate(self) -> None:
        calls: list[str] = []

        class Coordinator:
            def present_post_action_events(self, scenario, context, runtime):
                del scenario, context, runtime
                calls.append("present:zg361mg.120")
                return {
                    "result": "GREEN",
                    "capture_event_left_visible": "zg361mg.120",
                }

        service = _Service()
        driver = capture._Phase2AcceptanceActionSpanDriver(
            service, event_choreographer=Coordinator()
        )
        scenario = next(
            row
            for row in PHASE2_CAPTURE_SCENARIOS
            if row.handler == "capture_manager_governance"
        )

        def visible(_service, _scenario):
            calls.append("visible-gate")
            return {"event_definition_key": "zg361mg.120"}

        with (
            mock.patch.object(
                capture,
                "run_stage10_player_subject",
                side_effect=lambda *_args, **_kwargs: (
                    calls.append("manager-action")
                    or {"result": "GREEN"}
                ),
            ),
            mock.patch.object(
                capture,
                "_phase2_promo_visible_scenario_surface",
                side_effect=visible,
            ),
        ):
            result = driver.run_span(
                scenario,
                SimpleNamespace(
                    seed_contract={},
                    artifacts=Path("unused"),
                    manager_source_receipt={
                        "result": "GREEN",
                        "player_manager_character_id": 9001,
                        "owner_character_id": 9002,
                    },
                ),
                {},
            )
        self.assertEqual(
            calls,
            ["manager-action", "present:zg361mg.120", "visible-gate"],
        )
        self.assertEqual(
            result["post_action_event_sequence"]["capture_event_left_visible"],
            "zg361mg.120",
        )

    def test_b2_action_opens_scoreboard_as_its_postcondition_surface(self) -> None:
        service = _Service()
        coordinator = mock.Mock()
        driver = capture._Phase2AcceptanceActionSpanDriver(
            service, event_choreographer=coordinator
        )
        scenario = next(
            row
            for row in PHASE2_CAPTURE_SCENARIOS
            if row.handler == "capture_receipt_appeal_pip"
        )
        scoreboard_evidence = {
            "result": "GREEN",
            "verified_pass": True,
            "capture_only_visual_scope": True,
        }
        with (
            mock.patch.object(
                capture,
                "_phase2_domain_query_contract",
                return_value={"b2_pip_owner_character_id": 9002},
            ),
            mock.patch.object(
                capture,
                "run_phase2_b2_pip_gameplay_action_cell",
                return_value={"result": "GREEN", "postcondition_query_green": True},
            ) as b2_action,
            mock.patch.object(
                capture,
                "run_phase2_scoreboard_promo_visual_cell",
                return_value=scoreboard_evidence,
            ) as scoreboard,
            mock.patch.object(
                capture, "_phase2_promo_visible_scenario_surface"
            ) as event_surface,
        ):
            result = driver.run_span(
                scenario,
                SimpleNamespace(seed_contract={}, artifacts=Path("unused")),
                {},
            )
        b2_action.assert_called_once_with(
            service, Path("unused"), owner_character_id=9002
        )
        scoreboard.assert_called_once_with(
            service,
            Path("unused"),
            nonce_prefix="zg361.phase2.promo.b2.postcondition",
            evidence_filename=(
                "07d_phase2_b2_pip_scoreboard_visual_action_cell.json"
            ),
        )
        coordinator.present_post_action_events.assert_not_called()
        event_surface.assert_not_called()
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(
            result["visible_surface"]["surface"],
            "named_widget:zg361_scoreboard_modal",
        )
        self.assertEqual(
            result["visible_surface"]["scoreboard_action_cell"],
            scoreboard_evidence,
        )


if __name__ == "__main__":
    unittest.main()
