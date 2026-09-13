#!/usr/bin/env python3
"""Run the bounded G2-M1 two-character campaign-root live gate in one CK3 process."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import threading
import time
from typing import Any
import uuid


SCRIPT_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SCRIPT_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_campaign_root_context_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.campaign_root_context_contract import (  # noqa: E402
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.set_played_character_contract import (  # noqa: E402
    SET_PLAYED_CHARACTER_V1_CAPABILITY,
    set_played_character_v1_step,
)
from xar_autoplayer.environment import is_relative_to  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


TURN_BUNDLE_STEP = "query-turn-bundle-v1"
COUNCIL_COVERAGE_KEY = "standard_landed_non_nomadic_core_v1"
CORE_COUNCIL_POSITIONS = {
    "councillor_chancellor",
    "councillor_steward",
    "councillor_marshal",
    "councillor_spymaster",
    "councillor_court_chaplain",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-profile", type=Path, required=True)
    parser.add_argument("--source-save", type=Path, required=True)
    parser.add_argument("--expected-source-save-sha256", required=True)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--first-character-id", type=int, required=True)
    parser.add_argument("--first-primary-title-id", type=int, required=True)
    parser.add_argument("--first-capital-province-id", type=int, required=True)
    parser.add_argument("--second-character-id", type=int, required=True)
    parser.add_argument("--second-primary-title-id", type=int, required=True)
    parser.add_argument("--second-capital-province-id", type=int, required=True)
    parser.add_argument("--second-immediate-liege-id", type=int, required=True)
    parser.add_argument("--second-top-liege-id", type=int, required=True)
    parser.add_argument("--expected-date-raw", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _fixed_q100000(value: object) -> bool:
    return bool(
        isinstance(value, dict)
        and isinstance(value.get("raw"), int)
        and not isinstance(value.get("raw"), bool)
        and value.get("scale") == 100_000
    )


def _scene_proof(
    sequence: object,
    bundle: object,
    *,
    expected_character_id: int,
    expected_primary_title_id: int,
    expected_capital_province_id: int,
    expected_immediate_liege_id: int | None,
    expected_top_liege_id: int,
    expected_independent: bool,
    require_relationship_vectors: bool,
) -> dict[str, object]:
    sequence = sequence if isinstance(sequence, dict) else {}
    first = sequence.get("first_query")
    first = first if isinstance(first, dict) else {}
    root = first.get("campaign_root_context")
    root = root if isinstance(root, dict) else {}
    readiness = root.get("readiness")
    readiness = readiness if isinstance(readiness, dict) else {}
    title = root.get("primary_title")
    title = title if isinstance(title, dict) else {}
    partition = root.get("held_title_partition")
    partition = partition if isinstance(partition, list) else []
    direct = root.get("direct_landed_vassal_character_ids")
    direct = direct if isinstance(direct, list) else []
    adjacent = root.get("adjacent_external_province_holder_character_ids")
    adjacent = adjacent if isinstance(adjacent, list) else []
    related = root.get("related_character_contexts")
    related = related if isinstance(related, list) else []
    council = root.get("council")
    council = council if isinstance(council, dict) else {}
    positions = council.get("positions")
    positions = positions if isinstance(positions, list) else []
    position_keys = {
        row.get("position_key") for row in positions if isinstance(row, dict)
    }
    occupied = [
        row
        for row in positions
        if isinstance(row, dict)
        and isinstance(row.get("incumbent_character_id"), int)
    ]
    bundle = bundle if isinstance(bundle, dict) else {}
    bundle_readiness = bundle.get("readiness")
    bundle_readiness = (
        bundle_readiness if isinstance(bundle_readiness, dict) else {}
    )
    realm = bundle.get("realm_state")
    realm = realm if isinstance(realm, dict) else {}
    realm_value = realm.get("value")
    realm_value = realm_value if isinstance(realm_value, dict) else {}
    bundle_council = realm_value.get("council")
    bundle_council = (
        bundle_council if isinstance(bundle_council, dict) else {}
    )
    relationship_checks = {
        "direct_vassal_present": bool(direct),
        "adjacent_external_holder_present": bool(adjacent),
        "related_contexts_cover_vectors": len(related)
        == len(set(direct) | set(adjacent)),
    }
    checks = {
        "same_frame_double_query": sequence.get("ok") is True,
        "root_available_and_ready": root.get("status") == "available"
        and readiness.get("ready") is True
        and all(value is True for value in readiness.values()),
        "character_identity": root.get("player_character_id")
        == expected_character_id,
        "primary_title_identity": title.get("title_id")
        == expected_primary_title_id,
        "capital_identity": root.get("capital_province_id")
        == expected_capital_province_id,
        "liege_identity": root.get("immediate_liege_character_id")
        == expected_immediate_liege_id
        and root.get("top_liege_character_id") == expected_top_liege_id
        and root.get("independent") is expected_independent,
        "fixed_point_observations": _fixed_q100000(
            root.get("player_monthly_gold_income")
        )
        and _fixed_q100000(root.get("player_health")),
        "domain_observed": isinstance(root.get("player_domain_size"), int)
        and not isinstance(root.get("player_domain_size"), bool)
        and int(root["player_domain_size"]) >= 0
        and isinstance(root.get("player_domain_limit"), int)
        and not isinstance(root.get("player_domain_limit"), bool)
        and int(root["player_domain_limit"]) > 0,
        "factions_observed": isinstance(
            root.get("player_targeting_faction_count"), int
        )
        and not isinstance(root.get("player_targeting_faction_count"), bool)
        and int(root["player_targeting_faction_count"]) >= 0,
        "partition_observed": bool(partition)
        and sum(
            row.get("primary") is True
            for row in partition
            if isinstance(row, dict)
        )
        == 1
        and any(
            isinstance(row, dict)
            and row.get("primary") is True
            and isinstance(row.get("title"), dict)
            and row["title"].get("title_id") == expected_primary_title_id
            for row in partition
        ),
        "council_observed": council.get("status") == "available"
        and council.get("coverage_key") == COUNCIL_COVERAGE_KEY
        and council.get("owner_character_id") == expected_character_id
        and council.get("auxiliary_vacancies_complete") is False
        and CORE_COUNCIL_POSITIONS.issubset(position_keys),
        "turn_bundle_projects_council": bundle.get("schema")
        == "xar.ck3.turn-bundle/v1"
        and bundle.get("status") in {"available", "partial"}
        and bundle_readiness.get("realm_council_ready") is True
        and bundle_council.get("status") == "available"
        and bundle_council.get("value") == council,
        "relationship_vectors": (
            all(relationship_checks.values())
            if require_relationship_vectors
            else True
        ),
    }
    return {
        "expected": {
            "character_id": expected_character_id,
            "primary_title_id": expected_primary_title_id,
            "capital_province_id": expected_capital_province_id,
            "immediate_liege_character_id": expected_immediate_liege_id,
            "top_liege_character_id": expected_top_liege_id,
            "independent": expected_independent,
        },
        "checks": checks,
        "relationship_checks": relationship_checks,
        "occupied_council_task_count": len(occupied),
        "root": root,
        "turn_bundle": bundle,
        "ok": all(checks.values()),
    }


def _switch_proof(
    before: object,
    result: object,
    after: object,
    *,
    from_character_id: int,
    to_character_id: int,
) -> dict[str, object]:
    before = before if isinstance(before, dict) else {}
    result = result if isinstance(result, dict) else {}
    after = after if isinstance(after, dict) else {}
    played = after.get("played_character")
    played = played if isinstance(played, dict) else {}
    checks = {
        "typed_success": result.get("step")
        == set_played_character_v1_step(to_character_id)
        and result.get("accepted") is True
        and result.get("status") == "switched"
        and result.get("postcondition_verified") is True,
        "identity_changed": result.get("from_character_id")
        == from_character_id
        and result.get("to_character_id") == to_character_id
        and played.get("character_id") == to_character_id,
        "revision_advanced": isinstance(before.get("revision"), int)
        and isinstance(after.get("revision"), int)
        and int(after["revision"]) > int(before["revision"])
        and result.get("before_revision") == before.get("revision")
        and result.get("after_revision") == after.get("revision"),
        "same_paused_date": before.get("paused") is True
        and after.get("paused") is True
        and before.get("date_raw") == after.get("date_raw"),
        "same_process_episode": before.get("episode_run_id")
        == after.get("episode_run_id")
        == result.get("episode_run_id"),
        "map_ready": before.get("map_ready") is True
        and after.get("map_ready") is True,
    }
    return {"before": before, "result": result, "after": after, "checks": checks,
            "ok": all(checks.values())}


def _capability_proof(capabilities: object) -> dict[str, object]:
    value = capabilities if isinstance(capabilities, dict) else {}
    advertised = value.get("bridge_capabilities")
    advertised = advertised if isinstance(advertised, list) else []
    hello = base._diagnostics(value).get("hello")
    hello = hello if isinstance(hello, dict) else {}
    hello_caps = hello.get("capabilities")
    hello_caps = hello_caps if isinstance(hello_caps, list) else []
    required = {
        QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
        SET_PLAYED_CHARACTER_V1_CAPABILITY,
    }
    checks = {
        "bridge_capabilities": required.issubset(advertised),
        "hello_capabilities": required.issubset(hello_caps),
        "campaign_query_step": QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
        in value.get("action_steps", []),
        "campaign_driver_surface": value.get(
            "campaign_root_context_v1_query_supported"
        )
        is True,
    }
    return {"required": sorted(required), "checks": checks, "ok": all(checks.values())}


def _run_scene(service: GameplayBridgeService, **expected: object) -> dict[str, object]:
    sequence = base._run_double_query_sequence(service, save_checkpoint=False)
    revision = sequence.get("expected_revision")
    bundle = service.query_turn_bundle_v1(expected_revision=int(revision))
    after = service.snapshot()
    binding_ok = base._same_paused_binding(sequence["before_snapshot"], after)
    proof = _scene_proof(sequence, bundle, **expected)
    proof["turn_bundle_same_paused_binding"] = binding_ok
    proof["ok"] = proof["ok"] is True and binding_ok
    return proof


def _run_live(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    args: argparse.Namespace,
) -> dict[str, object]:
    stop_event = threading.Event()
    done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    driver_closed = False
    error_text: str | None = None
    values: dict[str, object] = {}

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=float(args.timeout) + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                stop_event=stop_event,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(target=supervise, name="xar-g2-m1-two-scene")
        thread.start()
        values["readiness"] = _wait_for_readiness(
            driver,
            session_done=done,
            session_state=session_state,
            timeout_seconds=float(args.readiness_timeout),
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        before_caps = driver.capabilities()
        values["capabilities_before"] = before_caps
        values["exact_build_proof"] = base._exact_build_proof(
            before_caps, base._sha256_file(spec.game_exe)
        )
        values["capability_proof"] = _capability_proof(before_caps)
        starting = service.snapshot()
        if starting.get("played_character", {}).get("character_id") != args.first_character_id:
            raise RuntimeError("source save opened on the wrong first character")
        if starting.get("date_raw") != args.expected_date_raw:
            raise RuntimeError("source save opened on the wrong date")
        first = _run_scene(
            service,
            expected_character_id=args.first_character_id,
            expected_primary_title_id=args.first_primary_title_id,
            expected_capital_province_id=args.first_capital_province_id,
            expected_immediate_liege_id=None,
            expected_top_liege_id=args.first_character_id,
            expected_independent=True,
            require_relationship_vectors=True,
        )
        values["first_scene"] = first
        before_switch = service.snapshot()
        switch_result = service.set_player_character_v1(
            args.second_character_id,
            expected_revision=base._snapshot_revision(before_switch),
        )
        after_switch = service.snapshot()
        switch = _switch_proof(
            before_switch,
            switch_result,
            after_switch,
            from_character_id=args.first_character_id,
            to_character_id=args.second_character_id,
        )
        values["switch"] = switch
        second = _run_scene(
            service,
            expected_character_id=args.second_character_id,
            expected_primary_title_id=args.second_primary_title_id,
            expected_capital_province_id=args.second_capital_province_id,
            expected_immediate_liege_id=args.second_immediate_liege_id,
            expected_top_liege_id=args.second_top_liege_id,
            expected_independent=False,
            require_relationship_vectors=False,
        )
        values["second_scene"] = second
        after_caps = driver.capabilities()
        values["capabilities_after"] = after_caps
        values["same_process_proof"] = base._same_process_proof(
            before_caps, after_caps
        )
        values["cross_scene"] = {
            "same_date": first["root"].get("date_raw")
            == second["root"].get("date_raw")
            == args.expected_date_raw,
            "at_least_one_occupied_council_task": (
                int(first["occupied_council_task_count"])
                + int(second["occupied_council_task_count"])
                > 0
            ),
        }
        required = (
            values["exact_build_proof"],
            values["capability_proof"],
            first,
            switch,
            second,
            values["same_process_proof"],
        )
        if not all(item.get("ok") is True for item in required) or not all(
            values["cross_scene"].values()
        ):
            raise RuntimeError("G2-M1 two-scene readiness proof failed")
    except BaseException as error:
        error_text = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if thread is not None:
            thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                error_text = detail if error_text is None else f"{error_text}; {detail}"
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True and error_text is None:
        error_text = str(cleanup.get("reason") or "managed process cleanup unproven")
    return {
        "stage": "same-process-two-scene",
        "session_started": thread is not None,
        "ok": error_text is None and cleanup.get("ok") is True,
        **values,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": error_text,
    }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    started_wall = utc_now()
    output = args.output.expanduser().resolve()
    source_profile = args.source_profile.expanduser().resolve()
    target = base._target_state_dir(args.state_dir)
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    if is_relative_to(output, source_profile) or is_relative_to(output, target):
        raise AgentError("artifact output must be outside source and disposable state")
    expected_sha = base._expected_sha256(args.expected_source_save_sha256)
    clone_nonce = uuid.uuid4().hex
    source_save: Path | None = None
    source_identity: dict[str, object] | None = None
    source_before: str | None = None
    disposable: dict[str, object] | None = None
    clone: dict[str, object] | None = None
    live: dict[str, object] | None = None
    primary_error: str | None = None
    try:
        source_save, source_identity = base._resolve_source_save(
            source_profile, args.source_save, expected_sha
        )
        source_before = base._sha256_file(source_save)
        disposable = base._prepare_disposable_root(
            target, source_profile=source_profile, clone_nonce=clone_nonce
        )
        spec, clone = base._prepare_stage_clone(
            source_profile=source_profile,
            target_state_dir=target / "same-process",
            game_dir=args.game_dir.expanduser().resolve(),
            source_save=source_save,
            stage="same-process-two-scene",
        )
        config = NativeBridgeLaunchConfig(
            mode=base.PURE_NATIVE_MODE,
            pipe_name=args.bridge_pipe,
            dll_path=args.bridge_dll.expanduser().resolve(),
            injector_path=args.bridge_injector.expanduser().resolve(),
        )
        live = _run_live(spec=spec, config=config, args=args)
        if live.get("ok") is not True:
            raise RuntimeError(str(live.get("error") or "live gate failed"))
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    source_after = (
        base._sha256_file(source_save)
        if source_save is not None and source_save.is_file()
        else None
    )
    source_unchanged = source_before is not None and source_before == source_after
    cleanup = (
        base._cleanup_disposable_root(
            target,
            clone_nonce=clone_nonce,
            retain_state=bool(args.retain_state),
            stages=[live],
        )
        if target.exists()
        else {"attempted": False, "removed": True, "ok": True, "path": str(target)}
    )
    if not source_unchanged and primary_error is None:
        primary_error = "immutable source save changed"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(cleanup.get("reason") or "disposable cleanup failed")
    ok = bool(
        primary_error is None
        and live
        and live.get("ok") is True
        and source_unchanged
        and cleanup.get("ok") is True
    )
    payload = {
        "format_version": 1,
        "kind": "ck3_g2_m1_campaign_root_two_scene_live_acceptance",
        "started_at": started_wall,
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "bounds": {
            "managed_ck3_processes": 1,
            "date_advance_allowed": False,
            "save_allowed": False,
            "direct_root_queries_per_scene": 2,
            "turn_bundle_queries_per_scene": 1,
            "played_character_switches": 1,
        },
        "allowed_commands": [
            QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            TURN_BUNDLE_STEP,
            set_played_character_v1_step(args.second_character_id),
        ],
        "source_save": source_identity,
        "source_save_invariant": {
            "before_sha256": source_before,
            "after_sha256": source_after,
            "unchanged": source_unchanged,
        },
        "disposable": disposable,
        "clone": clone,
        "live": live,
        "disposable_cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "output": str(output),
                "artifact_sha256": base._sha256_file(output),
                "cleanup": payload.get("disposable_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
