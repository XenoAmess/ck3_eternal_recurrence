#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import hashlib
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
    SOURCE_CHECKPOINT_REGISTRY_KIND,
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
        path = (root / f"{index}.ck3").resolve()
        path.write_bytes(f"checkpoint-{index}".encode("ascii"))
        sha = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        owner = 9200 + index
        player = 9001
        entries.append(
            {
                "span_id": plan.span_id,
                "handler": handler,
                "source_event_definition_key": plan.source_event,
                "owner_character_id": owner,
                "player_character_id": player,
                "date_raw": 800 + index,
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
                    "date_raw": 800 + index,
                    "checkpoint_sha256": sha,
                    "save_lineage_id": "seed-unit",
                },
            }
        )
    return {
        "schema_version": 1,
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

    def test_scoreboard_close_uses_provider_owned_close_and_later_query(self) -> None:
        service = _Service()
        adapter = capture._Phase2RealEventChoreographyService(service)
        plan = phase2_event_sequence_plan("capture_fact_quota_calibration")
        close_evidence = {
            "result": "GREEN",
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
                "_phase2_domain_query_contract",
                return_value={
                    "ai_owned_case_owner_character_id": 9002,
                    "ai_owned_case_subject_character_id": 9001,
                },
            ),
            mock.patch.object(
                capture,
                "run_phase2_ai_owned_case_gameplay_action_cell",
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
                SimpleNamespace(seed_contract={}, artifacts=Path("unused")),
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


if __name__ == "__main__":
    unittest.main()
