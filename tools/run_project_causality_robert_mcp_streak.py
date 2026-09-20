#!/usr/bin/env python3
"""Record a pure-vanilla Robert 1066 campaign controlled only through MCP.

The runner starts at CK3's main menu, opens the 1066 bookmarks page, selects
Robert by his exact native character key, and then delegates every campaign
turn to the autonomous player's official MCP surface.  It records one
continuous desktop master plus append-only MCP and war ledgers.  OCR, keyboard,
mouse, fixed coordinates, and the legacy fixed-Palermo route are hard REDs.

After every victorious war the policy returns to governance and evaluates the
currently legal targets again.  Recording ends at the first attacker defeat,
player/campaign terminal, or an explicit operator bound.  A lost battle does
not end the run; only a war-level outcome does.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Iterator
import uuid


REPOSITORY = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from mcp import Client  # noqa: E402

from xar_autoplayer.bridge.mcp_server import create_server  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.succession_transition_contract import (  # noqa: E402
    ORDINARY_CAMPAIGN_SUCCESSION,
    SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
    normalize_succession_lifecycle_binding_v1,
)
from xar_autoplayer.environment import (  # noqa: E402
    agent_runtime_fingerprint,
    ck3_process_inventory,
    ensure_state_path_safe,
    make_spec,
    render_settings,
    sha256_file,
    write_json_atomic,
    write_text_atomic,
)
from xar_autoplayer.locking import (  # noqa: E402
    exclusive_launch_lock,
    exclusive_state_lock,
)
from xar_autoplayer.rules import (  # noqa: E402
    declared_vanilla_rule_defaults,
    render_presets,
)
from xar_autoplayer.runtime import (  # noqa: E402
    NativeBridgeLaunchConfig,
    launch,
    stop_tracked,
)


EXPECTED_CK3_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ROBERT_CHARACTER_KEY = "bookmark_rags_to_riches_duke_robert"
FORBIDDEN_SELECTED_STEP_FRAGMENTS = (
    "war-declare-palermo",
    "war-siege-palermo",
    "visual",
    "ocr",
    "mouse",
    "keyboard",
)
INTERACTION_FLAG_KEYS = frozenset(
    {"uses_ocr", "uses_keyboard", "uses_mouse", "visual_fallback"}
)
SAFE_OVERMATCH_NUMERATOR = 3
SAFE_OVERMATCH_DENOMINATOR = 2
CB_PRIORITY = {
    "claim_cb": 0,
    "individual_county_de_jure_cb": 1,
    "county_conquest_cb": 2,
    "duchy_conquest_cb": 3,
    "minor_religious_war": 4,
}


class CaptureError(RuntimeError):
    """The formal MCP-only capture violated its declared contract."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=Path(r"Z:\ck3_mod_rewrite\Crusader Kings III"),
    )
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--bridge-pipe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--max-hours", type=float, default=12.0)
    parser.add_argument("--max-turns", type=int, default=10000)
    parser.add_argument("--frontend-timeout", type=float, default=300.0)
    parser.add_argument("--post-terminal-hold", type=float, default=8.0)
    parser.add_argument("--max-consecutive-blocked", type=int, default=3)
    parser.add_argument(
        "--skip-recording",
        action="store_true",
        help="diagnostic-only; a run using this switch can never be GREEN",
    )
    return parser


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _append_jsonl(path: Path, value: object) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as target:
        target.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
        target.write("\n")
        target.flush()


def _walk(value: object) -> Iterator[object]:
    yield value
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def _named_dicts(value: object, name: str) -> Iterator[dict[str, object]]:
    if isinstance(value, dict):
        candidate = value.get(name)
        if isinstance(candidate, dict):
            yield candidate
        for nested in value.values():
            yield from _named_dicts(nested, name)
    elif isinstance(value, list):
        for nested in value:
            yield from _named_dicts(nested, name)


def _assert_mcp_only(value: object, *, selected_step: str | None = None) -> None:
    for node in _walk(value):
        if not isinstance(node, dict):
            continue
        for key in INTERACTION_FLAG_KEYS:
            if node.get(key) is True:
                raise CaptureError(f"MCP-only contract violated: {key}=true")
    if selected_step is not None:
        lowered = selected_step.lower()
        fragment = next(
            (
                candidate
                for candidate in FORBIDDEN_SELECTED_STEP_FRAGMENTS
                if candidate in lowered
            ),
            None,
        )
        if fragment is not None:
            raise CaptureError(
                "legacy or visual step reached the formal run: "
                f"{selected_step!r} ({fragment!r})"
            )


def _active_wars(snapshot: object) -> dict[int, dict[str, object]]:
    if not isinstance(snapshot, dict):
        return {}
    rows = snapshot.get("active_wars")
    result: dict[int, dict[str, object]] = {}
    for row in rows if isinstance(rows, list) else []:
        war_id = row.get("war_id") if isinstance(row, dict) else None
        if isinstance(war_id, int) and not isinstance(war_id, bool) and war_id > 0:
            result[war_id] = row
    return result


def _played_character(snapshot: object) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        return {}
    played = snapshot.get("played_character")
    return played if isinstance(played, dict) else {}


def _selected_step(auto_turn: object) -> str | None:
    if not isinstance(auto_turn, dict):
        return None
    direct = auto_turn.get("selected_step")
    if isinstance(direct, str):
        return direct
    plan = auto_turn.get("plan")
    selected = plan.get("selected_step") if isinstance(plan, dict) else None
    return selected if isinstance(selected, str) else None


def _plan_phase(auto_turn: object) -> str | None:
    if not isinstance(auto_turn, dict):
        return None
    direct = auto_turn.get("phase")
    if isinstance(direct, str):
        return direct
    plan = auto_turn.get("plan")
    phase = plan.get("phase") if isinstance(plan, dict) else None
    return phase if isinstance(phase, str) else None


def _rank_declaration_candidates(
    declarations: object,
    assessments_by_target: dict[int, dict[str, object]],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Rank current native declarations without trusting a zeroed adjustment.

    The native assessment exposes base, network, pre-adjustment and adjusted
    power. The show-off policy deliberately uses the maximum of the three
    target totals so an opaque negative adjustment cannot make a stronger
    opponent look harmless. A 3:2 base-power overmatch is the preferred lane;
    if no legal target meets it, the least-risk current declaration remains
    eligible because this run is explicitly meant to continue until failure.
    """
    if not isinstance(declarations, list) or not declarations:
        raise CaptureError("native MCP returned no declarable wars to rank")
    ranked: list[tuple[tuple[object, ...], dict[str, object]]] = []
    for declaration in declarations:
        if not isinstance(declaration, dict):
            raise CaptureError("native declaration row is not an object")
        target_id = declaration.get("target_character_id")
        declaration_id = declaration.get("declaration_id")
        if (
            isinstance(target_id, bool)
            or not isinstance(target_id, int)
            or target_id <= 0
            or not isinstance(declaration_id, str)
            or not declaration_id
        ):
            raise CaptureError("native declaration row lacks a stable target/id")
        assessment = assessments_by_target.get(target_id)
        if not isinstance(assessment, dict):
            raise CaptureError(
                f"target {target_id} lacks a same-frame MCP power assessment"
            )
        integer_fields = (
            "actor_power_base_raw",
            "target_power_base_raw",
            "target_pre_adjustment_total_raw",
            "target_power_total_raw",
            "target_network_contribution_raw",
            "distance_raw",
        )
        values: dict[str, int] = {}
        for name in integer_fields:
            raw = assessment.get(name)
            if isinstance(raw, bool) or not isinstance(raw, int):
                raise CaptureError(
                    f"target {target_id} assessment lacks integer {name}"
                )
            values[name] = raw
        actor_power = values["actor_power_base_raw"]
        effective_target_power = max(
            values["target_power_base_raw"],
            values["target_pre_adjustment_total_raw"],
            values["target_power_total_raw"],
        )
        if actor_power <= 0 or effective_target_power < 0:
            raise CaptureError(
                f"target {target_id} has unusable native power values"
            )
        safe_overmatch = (
            actor_power * SAFE_OVERMATCH_DENOMINATOR
            >= effective_target_power * SAFE_OVERMATCH_NUMERATOR
        )
        ratio_ppm = effective_target_power * 1_000_000 // actor_power
        casus_belli_key = declaration.get("casus_belli_key")
        cb_rank = CB_PRIORITY.get(str(casus_belli_key), 100)
        target_title_ids = declaration.get("target_title_ids")
        title_count = (
            len(target_title_ids) if isinstance(target_title_ids, list) else 0
        )
        candidate = {
            "declaration_id": declaration_id,
            "target_character_id": target_id,
            "effective_target_character_id": assessment.get(
                "effective_target_character_id"
            ),
            "casus_belli_key": casus_belli_key,
            "target_title_ids": target_title_ids,
            "actor_power_base_raw": actor_power,
            "target_power_base_raw": values["target_power_base_raw"],
            "target_network_contribution_raw": values[
                "target_network_contribution_raw"
            ],
            "target_pre_adjustment_total_raw": values[
                "target_pre_adjustment_total_raw"
            ],
            "target_power_total_raw": values["target_power_total_raw"],
            "conservative_target_power_raw": effective_target_power,
            "conservative_target_to_actor_ratio_ppm": ratio_ppm,
            "distance_raw": values["distance_raw"],
            "safe_overmatch": safe_overmatch,
            "risk_class": (
                "preferred_3_to_2_overmatch"
                if safe_overmatch
                else "least_risk_until_failure"
            ),
        }
        sort_key: tuple[object, ...] = (
            0 if safe_overmatch else 1,
            ratio_ppm,
            effective_target_power,
            values["distance_raw"],
            cb_rank,
            -title_count,
            target_id,
            declaration_id,
        )
        ranked.append((sort_key, candidate))
    ranked.sort(key=lambda item: item[0])
    rows = [row for _, row in ranked]
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows[0], rows


def _war_outcomes(auto_turn: object) -> list[dict[str, object]]:
    outcomes: list[dict[str, object]] = []
    for victory in _named_dicts(auto_turn, "war_victory"):
        if victory.get("status") == "victory_enforced":
            outcomes.append(
                {
                    "outcome": "attacker_victory",
                    "war_id": victory.get("war_id"),
                    "evidence": victory,
                }
            )
    for termination in _named_dicts(auto_turn, "war_termination_result"):
        outcome = termination.get("outcome")
        status = termination.get("status")
        if outcome in {"attacker_defeat", "white_peace"} and status in {
            "applied",
            "submitted_pending",
        }:
            outcomes.append(
                {
                    "outcome": outcome,
                    "war_id": termination.get("war_id"),
                    "evidence": termination,
                }
            )
    unique: dict[tuple[object, object], dict[str, object]] = {}
    for row in outcomes:
        unique[(row.get("outcome"), row.get("war_id"))] = row
    return list(unique.values())


def _terminal_vanished_war_outcome(
    previous_war: object,
) -> str | None:
    """Classify only a previously observed absolute player score endpoint."""
    if not isinstance(previous_war, dict):
        return None
    score = previous_war.get("player_relative_war_score")
    if isinstance(score, bool) or not isinstance(score, int):
        return None
    if score <= -100:
        return "player_defeat"
    if score >= 100:
        return "player_victory"
    return None


def _snapshot_ready_for_declaration(snapshot: object) -> bool:
    """Require a quiet paused map before issuing a fresh declaration."""
    return bool(
        isinstance(snapshot, dict)
        and snapshot.get("map_ready") is True
        and snapshot.get("paused") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
    )


def _content_blocks(result: Any) -> list[object]:
    blocks: list[object] = []
    for block in getattr(result, "content", []):
        if hasattr(block, "model_dump"):
            blocks.append(block.model_dump(mode="json"))
        else:
            blocks.append(str(block))
    return blocks


async def _call(
    client: Client,
    journal: Path,
    index: int,
    name: str,
    arguments: dict[str, object] | None = None,
) -> dict[str, object]:
    arguments = {} if arguments is None else dict(arguments)
    started_at = _utc_now()
    started = time.monotonic()
    try:
        result = await client.call_tool(name, arguments)
        row: dict[str, object] = {
            "index": index,
            "started_at": started_at,
            "finished_at": _utc_now(),
            "tool": name,
            "arguments": arguments,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": bool(result.is_error),
            "structured_content": result.structured_content,
            "content": _content_blocks(result),
        }
    except BaseException as error:
        row = {
            "index": index,
            "started_at": started_at,
            "finished_at": _utc_now(),
            "tool": name,
            "arguments": arguments,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "is_error": True,
            "exception": f"{type(error).__name__}: {error}",
        }
    _append_jsonl(journal, row)
    return row


def _structured(call: dict[str, object]) -> dict[str, object]:
    value = call.get("structured_content")
    return value if isinstance(value, dict) else {}


def _call_error_text(call: dict[str, object]) -> str:
    parts: list[str] = []
    exception = call.get("exception")
    if isinstance(exception, str):
        parts.append(exception)
    content = call.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
    return "\n".join(parts)


def _is_route_contact_timeline_unavailable(call: dict[str, object]) -> bool:
    return bool(
        call.get("is_error") is True
        and "CK3 route arrival timeline is unavailable"
        in _call_error_text(call)
    )


def _prepare_vanilla_profile(spec: Any) -> tuple[dict[str, object], dict[str, object]]:
    profile = spec.profile_dir
    for directory in (
        profile / "mod",
        profile / "logs",
        profile / "save games",
        profile / "player" / "game_rules",
        spec.state_dir / "control",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    if any((profile / "mod").iterdir()):
        raise CaptureError("pure-vanilla profile mod directory is not empty")
    dlc_load_path = profile / "dlc_load.json"
    write_json_atomic(dlc_load_path, {"enabled_mods": [], "disabled_dlcs": []})
    vanilla_defaults = declared_vanilla_rule_defaults(spec.vanilla_rules)
    vanilla_contract = {
        "profile": [
            {"rule": rule, "setting": setting}
            for rule, setting in vanilla_defaults
        ],
        "ironman": False,
    }
    presets_path = profile / "player" / "game_rules" / "presets.txt"
    write_text_atomic(presets_path, render_presets(vanilla_contract))
    settings_path = profile / "pdx_settings.txt"
    write_text_atomic(settings_path, render_settings())
    tutorial_path = profile / "tutorial.txt"
    write_text_atomic(
        tutorial_path,
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
    )
    runtime = agent_runtime_fingerprint()
    identity: dict[str, object] = {
        "format_version": 1,
        "kind": "project_causality_robert_mcp_streak_vanilla_profile",
        "state_dir": str(spec.state_dir),
        "profile_dir": str(profile),
        "display": {
            "language": "l_simp_chinese",
            "resolution": [2560, 1440],
            "mode": "fullscreen",
        },
        "load_profile": {
            "enabled_mods": [],
            "disabled_dlcs": [],
            "dlc_load_path": str(dlc_load_path),
            "dlc_load_sha256": sha256_file(dlc_load_path),
            "preset_path": str(presets_path),
            "preset_sha256": sha256_file(presets_path),
        },
        "agent_runtime": runtime,
    }
    environment_sha256 = hashlib.sha256(
        json.dumps(identity, ensure_ascii=True, sort_keys=True).encode("ascii")
    ).hexdigest()
    identity["environment_sha256"] = environment_sha256
    lifecycle = normalize_succession_lifecycle_binding_v1(
        {
            "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
            "lifecycle": ORDINARY_CAMPAIGN_SUCCESSION,
            "xar_enabled": "xar_off",
            "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
            "source": "pure-vanilla-enabled-mods-empty",
            "environment_sha256": environment_sha256,
        }
    )
    return identity, lifecycle


def _start_recorder(
    ffmpeg: str,
    output: Path,
    stderr_path: Path,
    fps: int,
) -> tuple[subprocess.Popen[bytes], Any, list[str]]:
    executable = shutil.which(ffmpeg)
    if executable is None:
        raise CaptureError(f"ffmpeg is unavailable: {ffmpeg}")
    encoders = subprocess.run(
        [executable, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    encoder_args = (
        ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", "18", "-b:v", "0"]
        if "h264_nvenc" in encoders
        else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]
    )
    command = [
        executable,
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-f",
        "gdigrab",
        "-framerate",
        str(fps),
        "-draw_mouse",
        "0",
        "-i",
        "desktop",
        "-vf",
        "scale=2560:1440:flags=lanczos,format=yuv420p",
        *encoder_args,
        "-an",
        str(output),
    ]
    error_log = stderr_path.open("wb")
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=error_log,
    )
    time.sleep(2.0)
    if process.poll() is not None:
        error_log.close()
        raise CaptureError(
            f"ffmpeg recorder exited during startup; inspect {stderr_path}"
        )
    return process, error_log, command


def _stop_recorder(process: subprocess.Popen[bytes] | None, log: Any) -> None:
    if process is not None and process.poll() is None:
        if process.stdin is not None:
            try:
                process.stdin.write(b"q\n")
                process.stdin.flush()
            except OSError:
                pass
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
    if log is not None:
        log.close()


async def _run_mcp_campaign(
    driver: NativeHeadlessGameplayDriver,
    *,
    journal: Path,
    war_journal: Path,
    target_journal: Path,
    max_turns: int,
    deadline: float,
    frontend_timeout: float,
    max_consecutive_blocked: int,
    report: dict[str, object],
) -> dict[str, object]:
    call_index = 0
    war_rows: dict[int, dict[str, object]] = {}

    async def call(
        name: str,
        arguments: dict[str, object] | None = None,
        *,
        tolerate_route_contact_timeline_unavailable: bool = False,
    ) -> dict[str, object]:
        nonlocal call_index
        call_index += 1
        row = await _call(client, journal, call_index, name, arguments)
        if row.get("is_error") is True:
            if (
                tolerate_route_contact_timeline_unavailable
                and name == "ck3_auto_turn"
                and _is_route_contact_timeline_unavailable(row)
            ):
                return {
                    "status": "read_unavailable",
                    "phase": "native_war_route_contact_horizon_unavailable",
                    "mcp_read_failure": {
                        "kind": "route_contact_timeline_unavailable",
                        "journal_record": call_index,
                        "error": _call_error_text(row),
                        "game_mutation": False,
                        "retry_same_frame": False,
                    },
                }
            raise CaptureError(
                f"MCP call {name} failed; see journal record {call_index}"
            )
        body = _structured(row)
        _assert_mcp_only(body)
        return body

    def record_war(row: dict[str, object]) -> None:
        _append_jsonl(war_journal, row)

    async def assess_and_declare_best_target(
        *, turn_index: int, snapshot: dict[str, object]
    ) -> dict[str, object]:
        discovery = await call("ck3_query_declarable_wars")
        declarations = discovery.get("declarable_wars")
        if not isinstance(declarations, list) or not declarations:
            raise CaptureError(
                "show-off policy reached war-entry NO_DECLARE with no legal targets"
            )
        target_ids = sorted(
            {
                row.get("target_character_id")
                for row in declarations
                if isinstance(row, dict)
                and isinstance(row.get("target_character_id"), int)
                and not isinstance(row.get("target_character_id"), bool)
                and int(row["target_character_id"]) > 0
            }
        )
        if not target_ids:
            raise CaptureError("legal declarations contain no assessable target")
        assessments: dict[int, dict[str, object]] = {}
        assessment_receipts: list[dict[str, object]] = []
        for target_id in target_ids:
            body = await call(
                "ck3_query_war_entry_assessments",
                {"target_character_ids": [target_id]},
            )
            envelope = body.get("war_entry_assessments")
            rows = (
                envelope.get("assessments")
                if isinstance(envelope, dict)
                else None
            )
            if not isinstance(rows, list) or len(rows) != 1:
                raise CaptureError(
                    f"MCP assessment for target {target_id} is not exactly one row"
                )
            assessment = rows[0]
            if (
                not isinstance(assessment, dict)
                or assessment.get("target_character_id") != target_id
            ):
                raise CaptureError(
                    f"MCP assessment identity mismatch for target {target_id}"
                )
            assessments[target_id] = assessment
            assessment_receipts.append(
                {
                    "target_character_id": target_id,
                    "queried_snapshot_id": body.get("queried_snapshot_id"),
                    "queried_revision": body.get("queried_revision"),
                    "queried_native_revision": body.get(
                        "queried_native_revision"
                    ),
                }
            )
        chosen, rankings = _rank_declaration_candidates(
            declarations, assessments
        )
        decision = {
            "kind": "dynamic_target_decision",
            "observed_at": _utc_now(),
            "turn_index": turn_index,
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "date_raw": snapshot.get("date_raw"),
            "policy": {
                "fixed_target": False,
                "source": "official_mcp_native_queries",
                "preferred_overmatch": (
                    "actor_base >= 1.5 * conservative_target_power"
                ),
                "conservative_target_power": (
                    "max(target_base, target_pre_adjustment_total, "
                    "target_adjusted_total)"
                ),
                "fallback": (
                    "least current target/actor ratio; continue until "
                    "war-level failure"
                ),
            },
            "assessment_receipts": assessment_receipts,
            "rankings": rankings,
            "chosen": chosen,
        }
        _append_jsonl(target_journal, decision)
        declaration = await call(
            "ck3_declare_war",
            {"declaration_id": chosen["declaration_id"]},
        )
        war_action = declaration.get("war_action")
        if not (
            isinstance(war_action, dict)
            and war_action.get("declaration_id") == chosen["declaration_id"]
            and war_action.get("status")
            in {"war_started", "declaration_submitted"}
        ):
            raise CaptureError(
                "MCP declaration did not return the chosen typed war action"
            )
        receipt = {
            **decision,
            "kind": "dynamic_target_declared",
            "declaration_result": {
                "step": declaration.get("step"),
                "accepted": declaration.get("accepted"),
                "status": declaration.get("status"),
                "war_action": war_action,
                "snapshot_id": declaration.get("snapshot_id"),
                "revision": declaration.get("revision"),
            },
        }
        _append_jsonl(target_journal, receipt)
        return receipt

    async with Client(create_server(driver)) as client:
        listed = await client.list_tools()
        tools = {tool.name for tool in listed.tools}
        required = {
            "ck3_query_frontend_gui_route_v1",
            "ck3_activate_frontend_new_game_v1",
            "ck3_activate_frontend_start_1066_bookmark_character_v1",
            "ck3_take_snapshot",
            "ck3_auto_turn",
            "ck3_query_declarable_wars",
            "ck3_query_war_entry_assessments",
            "ck3_declare_war",
        }
        missing = sorted(required - tools)
        if missing:
            raise CaptureError(f"official MCP server lacks tools: {missing}")

        frontend_deadline = time.monotonic() + frontend_timeout
        route: dict[str, object] = {}
        while time.monotonic() < frontend_deadline:
            call_index += 1
            row = await _call(
                client,
                journal,
                call_index,
                "ck3_query_frontend_gui_route_v1",
            )
            if row.get("is_error") is not True:
                route = _structured(row)
                _assert_mcp_only(route)
                if route.get("route") == "main_menu":
                    break
            await asyncio.sleep(1.0)
        if route.get("route") != "main_menu":
            raise CaptureError("native MCP did not observe the responsive main menu")
        report["main_menu"] = route

        bookmarks = await call("ck3_activate_frontend_new_game_v1")
        if not (
            bookmarks.get("postcondition_verified") is True
            and isinstance(bookmarks.get("after"), dict)
            and bookmarks["after"].get("route") == "bookmarks"
        ):
            raise CaptureError("MCP New Game did not prove the bookmarks route")
        report["bookmarks"] = bookmarks

        start = await call(
            "ck3_activate_frontend_start_1066_bookmark_character_v1",
            {"character_name_key": ROBERT_CHARACTER_KEY},
        )
        if not (
            start.get("postcondition_verified") is True
            and start.get("requested_character_name_key") == ROBERT_CHARACTER_KEY
        ):
            raise CaptureError("MCP start did not prove Robert's paused 1066 map")
        report["robert_start"] = start

        snapshot = await call("ck3_take_snapshot")
        played = _played_character(snapshot)
        if not (
            snapshot.get("map_ready") is True
            and snapshot.get("paused") is True
            and played.get("alive") is True
        ):
            raise CaptureError("Robert start lacks a live paused player snapshot")
        report["initial_snapshot"] = {
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "date_raw": snapshot.get("date_raw"),
            "episode_character_id": snapshot.get("episode_character_id"),
            "played_character": played,
        }

        previous_wars = _active_wars(snapshot)
        consecutive_blocked = 0
        terminal_reason: str | None = None
        final_outcome: str | None = None
        victories = 0
        white_peaces = 0
        defeats = 0
        declaration_pending_turn: int | None = None

        for turn_index in range(1, max_turns + 1):
            if time.monotonic() >= deadline:
                terminal_reason = "operator_max_hours"
                break
            auto_turn = await call(
                "ck3_auto_turn",
                tolerate_route_contact_timeline_unavailable=True,
            )
            selected_step = _selected_step(auto_turn)
            _assert_mcp_only(auto_turn, selected_step=selected_step)
            status = auto_turn.get("status")
            route_contact_read_unavailable = isinstance(
                auto_turn.get("mcp_read_failure"), dict
            )
            if route_contact_read_unavailable:
                consecutive_blocked = 0
            elif status == "blocked" or selected_step is None:
                consecutive_blocked += 1
            else:
                consecutive_blocked = 0
            if consecutive_blocked >= max_consecutive_blocked:
                raise CaptureError(
                    "autonomous policy remained blocked for "
                    f"{consecutive_blocked} consecutive MCP turns"
                )

            snapshot = await call("ck3_take_snapshot")
            current_wars = _active_wars(snapshot)
            plan_phase = _plan_phase(auto_turn)
            if current_wars:
                declaration_pending_turn = None
            elif (
                declaration_pending_turn is None
                and plan_phase == "native_war_entry_no_declare"
                and _snapshot_ready_for_declaration(snapshot)
            ):
                await assess_and_declare_best_target(
                    turn_index=turn_index,
                    snapshot=snapshot,
                )
                declaration_pending_turn = turn_index
                snapshot = await call("ck3_take_snapshot")
                current_wars = _active_wars(snapshot)
                if current_wars:
                    declaration_pending_turn = None
            elif (
                declaration_pending_turn is not None
                and turn_index - declaration_pending_turn >= 3
            ):
                raise CaptureError(
                    "chosen MCP declaration did not materialize as an active war"
                )
            for war_id in sorted(set(current_wars) - set(previous_wars)):
                row = {
                    "kind": "war_started",
                    "observed_at": _utc_now(),
                    "turn_index": turn_index,
                    "war_id": war_id,
                    "selected_step": selected_step,
                    "snapshot_id": snapshot.get("snapshot_id"),
                    "date_raw": snapshot.get("date_raw"),
                    "war": current_wars[war_id],
                }
                war_rows[war_id] = row
                record_war(row)

            explicit_outcomes = _war_outcomes(auto_turn)
            explicit_outcome_war_ids = {
                outcome.get("war_id")
                for outcome in explicit_outcomes
                if isinstance(outcome.get("war_id"), int)
            }
            for outcome in explicit_outcomes:
                kind = str(outcome.get("outcome"))
                war_id = outcome.get("war_id")
                record = {
                    "kind": "war_ended",
                    "observed_at": _utc_now(),
                    "turn_index": turn_index,
                    "war_id": war_id,
                    "outcome": kind,
                    "selected_step": selected_step,
                    "snapshot_id": snapshot.get("snapshot_id"),
                    "date_raw": snapshot.get("date_raw"),
                    "evidence": outcome.get("evidence"),
                    "started": war_rows.get(war_id) if isinstance(war_id, int) else None,
                }
                record_war(record)
                if kind == "attacker_victory":
                    victories += 1
                elif kind == "white_peace":
                    white_peaces += 1
                elif kind == "attacker_defeat":
                    defeats += 1
                    terminal_reason = "first_war_level_defeat"
                    final_outcome = kind

            for war_id in sorted(set(previous_wars) - set(current_wars)):
                if war_id in explicit_outcome_war_ids:
                    continue
                vanished_outcome = _terminal_vanished_war_outcome(
                    previous_wars.get(war_id)
                )
                record_war(
                    {
                        "kind": (
                            "war_ended"
                            if vanished_outcome is not None
                            else "war_disappeared_unclassified"
                        ),
                        "observed_at": _utc_now(),
                        "turn_index": turn_index,
                        "war_id": war_id,
                        "outcome": vanished_outcome,
                        "selected_step": selected_step,
                        "snapshot_id": snapshot.get("snapshot_id"),
                        "date_raw": snapshot.get("date_raw"),
                        "reason": (
                            "the immediately preceding paused native snapshot "
                            f"proved player-relative war score "
                            f"{previous_wars[war_id].get('player_relative_war_score')} "
                            "before the WarID disappeared"
                            if vanished_outcome is not None
                            else "the war left the paused native snapshot "
                            "without an explicit MCP victory, defeat, or "
                            "white-peace receipt or a terminal score; no "
                            "outcome is inferred"
                        ),
                        "started": war_rows.get(war_id),
                    }
                )
                if vanished_outcome == "player_defeat":
                    defeats += 1
                    terminal_reason = "first_war_level_defeat"
                    final_outcome = vanished_outcome
                elif (
                    vanished_outcome == "player_victory"
                    and previous_wars[war_id].get("player_side") == "attacker"
                ):
                    victories += 1

            report["progress"] = {
                "turns": turn_index,
                "mcp_calls": call_index,
                "victories": victories,
                "white_peaces": white_peaces,
                "defeats": defeats,
                "active_war_ids": sorted(current_wars),
                "last_selected_step": selected_step,
                "last_plan_phase": plan_phase,
                "last_snapshot_id": snapshot.get("snapshot_id"),
                "last_date_raw": snapshot.get("date_raw"),
            }
            previous_wars = current_wars

            played = _played_character(snapshot)
            if terminal_reason == "first_war_level_defeat":
                break
            if (
                status == "terminal"
                or snapshot.get("one_life_terminal") is True
                or played.get("alive") is False
            ):
                terminal_reason = "player_or_campaign_terminal"
                final_outcome = str(
                    snapshot.get("one_life_terminal_reason") or "terminal"
                )
                break
        else:
            terminal_reason = "operator_max_turns"

        return {
            "terminal_reason": terminal_reason,
            "final_outcome": final_outcome,
            "turns": report.get("progress", {}).get("turns", 0),
            "mcp_calls": call_index,
            "victories": victories,
            "white_peaces": white_peaces,
            "defeats": defeats,
            "interaction_policy": {
                "mcp_only": True,
                "uses_ocr": False,
                "uses_keyboard": False,
                "uses_mouse": False,
                "fixed_target": False,
                "target_policy": (
                    "query every legal target through MCP; rank conservative "
                    "native power, distance, CB and title value; reassess "
                    "after each war"
                ),
            },
        }


def main() -> int:
    args = _parser().parse_args()
    if not 1 <= args.fps <= 60:
        raise CaptureError("--fps must be between 1 and 60")
    if args.max_hours <= 0 or args.max_turns <= 0:
        raise CaptureError("operator bounds must be positive")
    if not 1 <= args.max_consecutive_blocked <= 20:
        raise CaptureError("--max-consecutive-blocked must be between 1 and 20")

    state_dir = args.state_dir.resolve()
    artifact_dir = args.artifact_dir.resolve()
    if state_dir.exists():
        raise CaptureError(f"state directory already exists: {state_dir}")
    if artifact_dir.exists():
        raise CaptureError(f"artifact directory already exists: {artifact_dir}")
    ensure_state_path_safe(state_dir)
    state_dir.mkdir(parents=True, exist_ok=False)
    artifact_dir.mkdir(parents=True, exist_ok=False)

    spec = make_spec(state_dir=state_dir, game_dir=args.game_dir.resolve())
    bridge_dll = args.bridge_dll.resolve()
    bridge_injector = args.bridge_injector.resolve()
    if not bridge_dll.is_file() or not bridge_injector.is_file():
        raise CaptureError("bridge DLL or injector is missing")
    if not spec.game_exe.is_file():
        raise CaptureError(f"CK3 executable is missing: {spec.game_exe}")
    if _sha256(spec.game_exe) != EXPECTED_CK3_SHA256:
        raise CaptureError("CK3 executable differs from the exact 1.19.0.6 pin")

    pipe_name = args.bridge_pipe or (
        rf"\\.\pipe\xar_robert_streak_{uuid.uuid4().hex[:12]}"
    )
    master = artifact_dir / "robert-1066-mcp-streak-continuous.mkv"
    recorder_log = artifact_dir / "ffmpeg-recorder.log"
    mcp_journal = artifact_dir / "mcp-calls.jsonl"
    war_journal = artifact_dir / "war-ledger.jsonl"
    target_journal = artifact_dir / "target-evaluations.jsonl"
    report_path = artifact_dir / "report.json"
    report: dict[str, object] = {
        "schema": "project-causality-robert-mcp-streak-capture/v1",
        "started_at": _utc_now(),
        "repository_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True
        ).strip(),
        "game_build": "1.19.0.6",
        "character_key": ROBERT_CHARACTER_KEY,
        "gameplay_profile": "pure-vanilla-enabled-mods-empty",
        "classification": "production-live-candidate",
        "interaction_policy": {
            "mcp_only": True,
            "uses_ocr": False,
            "uses_keyboard": False,
            "uses_mouse": False,
            "fixed_coordinates": False,
            "fixed_war_target": False,
        },
        "stop_contract": (
            "continue after every attacker victory; a battle loss is non-terminal; "
            "stop at first war-level attacker defeat, campaign terminal, or explicit operator bound"
        ),
        "paths": {
            "state_dir": str(state_dir),
            "master": str(master),
            "mcp_journal": str(mcp_journal),
            "war_journal": str(war_journal),
            "target_journal": str(target_journal),
        },
        "binary": {
            "ck3_exe": str(spec.game_exe),
            "ck3_exe_sha256": _sha256(spec.game_exe),
            "bridge_dll": str(bridge_dll),
            "bridge_dll_sha256": _sha256(bridge_dll),
            "bridge_injector": str(bridge_injector),
            "bridge_injector_sha256": _sha256(bridge_injector),
        },
        "ok": False,
        "finalized": False,
    }
    _atomic_json(report_path, report)

    handle = None
    driver: NativeHeadlessGameplayDriver | None = None
    recorder: subprocess.Popen[bytes] | None = None
    recorder_stderr = None
    primary_error: BaseException | None = None
    cleanup: dict[str, object] | None = None
    slot_stack = ExitStack()
    try:
        identity, lifecycle = _prepare_vanilla_profile(spec)
        report["profile"] = identity
        report["succession_lifecycle"] = lifecycle
        if ck3_process_inventory()["processes"]:
            raise CaptureError("CK3 is already running")
        slot_stack.enter_context(exclusive_launch_lock(spec.game_exe))
        slot_stack.enter_context(
            exclusive_state_lock(state_dir, "project-causality-robert-mcp-streak")
        )
        if args.skip_recording:
            report["recording"] = {"status": "skipped-diagnostic-red"}
        else:
            recorder, recorder_stderr, recorder_command = _start_recorder(
                args.ffmpeg, master, recorder_log, args.fps
            )
            report["recording"] = {
                "status": "running",
                "command": recorder_command,
                "started_at": _utc_now(),
            }

        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=pipe_name,
            dll_path=bridge_dll,
            injector_path=bridge_injector,
        )
        driver = NativeHeadlessGameplayDriver(
            pipe_name,
            state_dir=state_dir,
            save_dir=spec.profile_dir / "save games",
            frontend_transition_timeout_seconds=args.frontend_timeout,
            succession_lifecycle_binding=lifecycle,
            allow_private_current_timeline_blocker_query=True,
            allow_private_death_succession_modal_continue=True,
        )
        handle = launch(spec, native_bridge=config, verify_prepared_profile=False)
        report["managed_pid"] = int(handle.process.pid)
        _atomic_json(report_path, report)
        deadline = time.monotonic() + args.max_hours * 3600.0
        result = asyncio.run(
            _run_mcp_campaign(
                driver,
                journal=mcp_journal,
                war_journal=war_journal,
                target_journal=target_journal,
                max_turns=args.max_turns,
                deadline=deadline,
                frontend_timeout=args.frontend_timeout,
                max_consecutive_blocked=args.max_consecutive_blocked,
                report=report,
            )
        )
        report["result"] = result
        if args.post_terminal_hold > 0:
            time.sleep(args.post_terminal_hold)
        report["capture_contract_satisfied"] = bool(
            not args.skip_recording
            and result.get("terminal_reason")
            in {"first_war_level_defeat", "player_or_campaign_terminal"}
            and int(result.get("victories", 0)) >= 1
        )
    except BaseException as error:
        primary_error = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if handle is not None:
            try:
                cleanup = stop_tracked(handle, require_running=False)
            except BaseException as error:
                cleanup = {
                    "ok": False,
                    "error": f"{type(error).__name__}: {error}",
                }
                if primary_error is None:
                    primary_error = error
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                if primary_error is None:
                    primary_error = error
        try:
            slot_stack.close()
        except BaseException as error:
            if primary_error is None:
                primary_error = error
        _stop_recorder(recorder, recorder_stderr)
        report["cleanup"] = cleanup
        recording = report.get("recording")
        if isinstance(recording, dict) and master.is_file():
            recording.update(
                {
                    "status": "finalized",
                    "finished_at": _utc_now(),
                    "bytes": master.stat().st_size,
                    "sha256": _sha256(master),
                }
            )
        report["finished_at"] = _utc_now()
        report["finalized"] = True
        report["ok"] = bool(
            primary_error is None
            and report.get("capture_contract_satisfied") is True
            and isinstance(cleanup, dict)
            and cleanup.get("tree_gone") is True
        )
        _atomic_json(report_path, report)

    print(json.dumps({"report": str(report_path), "ok": report["ok"]}, ensure_ascii=False))
    if primary_error is not None:
        raise CaptureError(
            f"Robert MCP streak capture failed; report={report_path}: {primary_error}"
        ) from primary_error
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CaptureError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
