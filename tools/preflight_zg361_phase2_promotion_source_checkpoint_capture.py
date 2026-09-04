#!/usr/bin/env python3
"""No-launch preflight for the real Promotion source checkpoint entry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from zg361_phase2_promotion_source_checkpoint_capture import (  # noqa: E402
    HANDLER,
    build_no_launch_preflight,
)
from zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    CHECKPOINT_REQUIRED_HANDLERS,
)


RUNNER = ROOT / "tools/run_zhongguo_acceptance.py"
CAPTURE = ROOT / "tools/zg361_phase2_promotion_source_checkpoint_capture.py"
PRODUCTION_ENTRY = (
    ROOT / "tools/zg361_phase2_promotion_source_production_entry.py"
)
ASSEMBLER = ROOT / "tools/zhongguo_phase2_source_checkpoint_registry.py"
ADAPTER = (
    ROOT
    / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
)
PROVIDER_CAPABILITY = (
    "game.command.query-zhongguo-promotion-compensation-postcondition-v1"
)


def _tuple_labels(source: str, symbol: str) -> tuple[str, ...]:
    match = re.search(
        rf"{re.escape(symbol)}\s*=\s*\((?P<body>.*?)\)\s*",
        source,
        re.DOTALL,
    )
    return () if match is None else tuple(re.findall(r'"([^"]+)"', match["body"]))


def run_preflight() -> dict[str, object]:
    """Inspect repository wiring only; never instantiate a service or CK3."""

    callable_report = build_no_launch_preflight()
    runner_source = RUNNER.read_text(encoding="utf-8-sig")
    capture_source = CAPTURE.read_text(encoding="utf-8-sig")
    production_entry_source = PRODUCTION_ENTRY.read_text(encoding="utf-8-sig")
    assembler_source = ASSEMBLER.read_text(encoding="utf-8-sig")
    adapter_source = ADAPTER.read_text(encoding="utf-8-sig")
    focused_bridge_labels = _tuple_labels(
        runner_source,
        "PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_BRIDGE_CAPABILITY_LABELS",
    )
    focused_query_labels = _tuple_labels(
        runner_source,
        "PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_QUERY_FLAG_LABELS",
    )
    focused_action_labels = _tuple_labels(
        runner_source,
        "PHASE2_PROMOTION_SOURCE_CAPTURE_REQUIRED_ACTION_STEP_LABELS",
    )
    checks = {
        "capture_callable_contract_green": callable_report.get("result")
        == "GREEN",
        "formal_explicit_live_mode_registered": all(
            token in runner_source
            for token in (
                '"--phase2-promotion-source-checkpoint-live"',
                "capture_promotion_source_checkpoint_v2(",
                "phase2_promotion_source_capture_live: bool = False",
                '"product_only_runtime": True',
                '"acceptance_fixture_loaded": False',
            )
        ),
        "focused_profile_has_exact_entry_query_action_and_save": focused_bridge_labels
        == (
            "paused_snapshot",
            "map_ready_state",
            "played_character_state",
            "active_event_state",
            "save_checkpoint",
            "current_event_context",
            "pause_timeline",
            "resume_timeline",
            "bounded_timeline_speed",
            "event_option_action_ack",
            "promotion_source_progress_transport",
            "review_now_action_transport",
        )
        and focused_query_labels == ("current_event_context",)
        and focused_action_labels
        == (
            "save_checkpoint",
            "pause_timeline",
            "resume_timeline",
            "bounded_timeline_speed",
        ),
        "runner_executes_exact_product_prefix": all(
            token in runner_source
            for token in (
                "enter_promotion_source_checkpoint_v1(",
                '"03_promotion_source_production_entry.json"',
                "capture_promotion_source_checkpoint_v2(",
            )
        )
        and all(
            token in production_entry_source
            for token in (
                "query_zhongguo_promotion_source_progress_v1(",
                "activate_zhongguo_review_now_v1(",
                "verify_review_now_independent_postcondition_v1(",
                "select_event_option(",
                "if key != M146",
                "if key == M147",
                '"action_ack_used_as_state_evidence": False',
            )
        ),
        "exact_source_option_and_scopes_bound": all(
            token in capture_source
            for token in (
                'SOURCE_EVENT_DEFINITION_KEY',
                'SOURCE_OPTION_NUMBER',
                '"zg361_pp_prompt_owner"',
                '"zg361_pp_prompt_subject"',
                '"zg361_pp_prompt_case"',
                '"zg361_pp_prompt_cycle"',
                '"zg361_pp_prompt_mechanism"',
                '"zg361_pp_prompt_state"',
                '"option_shown": True',
                '"option_enabled": True',
            )
        ),
        "single_entry_boundary_is_explicit": (
            callable_report.get("incomplete_for_canonical_4_entry_registry")
            is True
            and callable_report.get("required_handler_order")
            == list(CHECKPOINT_REQUIRED_HANDLERS)
            and CHECKPOINT_REQUIRED_HANDLERS[0] == HANDLER
            and '"canonical_registry_ready": False' in capture_source
            and '"append_exact_entries_without_rewrite"' in capture_source
        ),
        "canonical_schema2_assembler_remains_authoritative": all(
            token in assembler_source
            for token in (
                'SOURCE_CHECKPOINT_CAPTURE_MANIFEST_KIND',
                'SOURCE_CHECKPOINT_REGISTRY_SCHEMA_VERSION',
                'CHECKPOINT_REQUIRED_HANDLERS',
            )
        ),
        "fixture_console_and_ack_cannot_supply_checkpoint_state": all(
            token in capture_source
            for token in (
                'lineage.get("fixture_used") is False',
                'lineage.get("console_used") is False',
                '"action_ack_used_as_state_evidence": False',
                '"event_option_action_executed": False',
            )
        )
        and "select_event_option(" not in capture_source
        and '"fixture_used": False' in production_entry_source
        and '"console_used": False' in production_entry_source,
        "result_provider_remains_default_off": PROVIDER_CAPABILITY
        not in adapter_source
        and "promotion_compensation_postcondition" not in focused_bridge_labels,
        "no_launch_path": all(
            token not in capture_source + production_entry_source
            for token in (
                "launch_native_ck3(",
                "start_phase2_native_session_supervisor(",
                "subprocess.",
            )
        ),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_capture_no_launch_preflight",
        "result": "GREEN" if not failed else "RED",
        "readiness": "static-ready-live-pending",
        "ck3_started": False,
        "ck3_launch_attempted": False,
        "service_instantiated": False,
        "checkpoint_written": False,
        "capture_artifact_written": False,
        "provider_default_off": True,
        "incomplete_for_canonical_4_entry_registry": True,
        "canonical_registry_ready": False,
        "deterministic_merge_input": {
            "schema_version": 2,
            "handler": HANDLER,
            "entry_index": 0,
            "required_handler_order": list(CHECKPOINT_REQUIRED_HANDLERS),
            "merge_operation": "append_exact_entries_without_rewrite",
        },
        "checks": checks,
        "failed_checks": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = run_preflight()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if arguments.output is not None:
        output = arguments.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["run_preflight"]
