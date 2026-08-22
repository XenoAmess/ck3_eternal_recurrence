"""Drive Robert 1066 through the opening pact and first map decisions."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path
import re
import shutil
import time
import uuid

from .environment import (
    REPO_ROOT,
    EnvironmentSpec,
    ck3_process_inventory,
    doctor,
    ensure_state_path_safe,
    sha256_file,
    verify_profile,
    write_json_atomic,
)
from .errors import AgentError
from .locking import exclusive_launch_lock, exclusive_state_lock
from .runtime import (
    SessionHandle,
    append_event,
    launch,
    log,
    stop_tracked,
    utc_now,
    wait_for_runtime_attestation,
)


OPENING_CONTRACT = (
    REPO_ROOT
    / "ck3_autonomous_player"
    / "configs"
    / "ui"
    / "ck3-1.19.0.6.zh-hans.2560x1440.opening.json"
)
OPENING_ALLOWED_CONTROLS = frozenset(
    {
        "main_menu.new_game",
        "bookmark_lobby.select_robert",
        "bookmark_lobby.start_game",
        "pact_event.accept_contract",
        "first_life_event.begin",
        "blessing_event.option_1",
        "blessing_event.option_2",
        "blessing_event.option_3",
        "curse_event.option_1",
        "curse_event.option_2",
        "map_hud.open_player_character",
        "map_hud.open_lifestyle",
        "lifestyle_selection.open_martial",
        "lifestyle_martial.select_authority_focus",
        "lifestyle_authority_confirmation.confirm",
        "lifestyle_martial_authority.close",
        "map_hud.set_speed_five",
        "map_hud.resume",
        "map_running.pause",
    }
)

INSTANT_UI_TRANSITION_TIMEOUT_SECONDS = 20.0
INITIAL_MAIN_MENU_TIMEOUT_SECONDS = 120.0


def _remaining(deadline: float, stage: str) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise AgentError(f"opening timeout elapsed before {stage}")
    return remaining


def _bind_window(
    spec: EnvironmentSpec, handle: SessionHandle, deadline: float
):
    from .vision import BoundGameWindow

    last_error: AgentError | None = None
    while time.monotonic() < deadline:
        if handle.process.poll() is not None:
            raise AgentError("CK3 exited before its opening window could be bound")
        try:
            return BoundGameWindow.bind_session(handle, spec.game_exe)
        except AgentError as error:
            last_error = error
            time.sleep(0.25)
    raise last_error or AgentError("CK3 opening window did not appear")


def _action_summary(action: dict[str, object]) -> dict[str, object]:
    return {
        "control_id": action.get("control_id"),
        "status": action.get("status"),
        "receipt_artifact": action.get("receipt_artifact"),
        "send_input": action.get("send_input"),
        "result_observation_id": action.get("result_observation_id"),
        "expected_post_screen": action.get("expected_post_screen"),
    }


_BLESSING_RARITY_SCORE = {"普通": 1000, "稀有": 2000, "传说": 3000}
_BLESSING_CATEGORY_SCORE = {
    "秘契": 900,
    "特质": 800,
    "修正": 700,
    "属性": 650,
    "生活方式": 500,
    "宗族": 450,
    "财富": 400,
    "权谋": 380,
    "信仰": 360,
    "威望": 340,
    "压力": 320,
}
_CURSE_RARITY_LOSS = {"普通": 1000, "稀有": 2000, "传说": 3000}
_CURSE_CATEGORY_LOSS = {
    "秘契": 900,
    "修正": 800,
    "特质": 750,
    "属性": 700,
    "生活方式": 350,
    "财富": 320,
    "权谋": 300,
    "信仰": 280,
    "威望": 260,
    "压力": 240,
    "宗族": 220,
}


def _score_first_blessing(text: str) -> int:
    """Rank a visible first-life blessing without reading hidden game state."""
    rarity = next(
        (score for name, score in _BLESSING_RARITY_SCORE.items() if name in text),
        0,
    )
    category = next(
        (score for name, score in _BLESSING_CATEGORY_SCORE.items() if name in text),
        0,
    )
    magnitudes = [abs(int(value)) for value in re.findall(r"[+-]?\d+", text)]
    magnitude = min(max(magnitudes, default=0), 99)
    return rarity + category + magnitude


def _choose_first_blessing(stable: object) -> tuple[object, str, int]:
    controls = tuple(getattr(stable, "controls", ()))
    latest = getattr(stable, "latest", None)
    spans = tuple(getattr(latest, "spans", ()))
    if len(controls) != 3:
        raise AgentError("first blessing screen does not expose exactly three choices")
    ranked: list[tuple[int, str, object, str]] = []
    for control in controls:
        matches = [
            span
            for span in spans
            if span.bbox == control.bbox and span.center == control.center
        ]
        if len(matches) != 1:
            raise AgentError("first blessing control lacks one exact visible OCR span")
        visible_text = matches[0].text
        ranked.append(
            (
                _score_first_blessing(visible_text),
                str(control.control_id),
                control,
                visible_text,
            )
        )
    score, _control_id, selected, visible_text = max(
        ranked, key=lambda item: (item[0], item[1])
    )
    return selected, visible_text, score


def _score_first_curse(text: str) -> int:
    """Estimate visible curse loss; lower is preferred."""
    rarity = next(
        (loss for name, loss in _CURSE_RARITY_LOSS.items() if name in text),
        0,
    )
    category = next(
        (loss for name, loss in _CURSE_CATEGORY_LOSS.items() if name in text),
        0,
    )
    magnitudes = [abs(int(value)) for value in re.findall(r"[+-]?\d+", text)]
    magnitude = min(max(magnitudes, default=0), 99)
    return rarity + category + magnitude


def _choose_first_curse(stable: object) -> tuple[object, str, int]:
    controls = tuple(getattr(stable, "controls", ()))
    latest = getattr(stable, "latest", None)
    spans = tuple(getattr(latest, "spans", ()))
    if len(controls) != 2:
        raise AgentError("first curse screen does not expose exactly two choices")
    ranked: list[tuple[int, str, object, str]] = []
    for control in controls:
        matches = [
            span
            for span in spans
            if span.bbox == control.bbox and span.center == control.center
        ]
        if len(matches) != 1:
            raise AgentError("first curse control lacks one exact visible OCR span")
        visible_text = matches[0].text
        ranked.append(
            (
                _score_first_curse(visible_text),
                str(control.control_id),
                control,
                visible_text,
            )
        )
    loss, _control_id, selected, visible_text = min(
        ranked, key=lambda item: (item[0], item[1])
    )
    return selected, visible_text, loss


def _extract_player_character_state(observation: dict[str, object]) -> dict[str, object]:
    """Extract the first useful map-state facts from the visible player panel."""
    if observation.get("screen") != "player_character":
        raise AgentError("player character state requires the player character screen")
    ocr = observation.get("ocr")
    if not isinstance(ocr, list):
        raise AgentError("player character observation OCR is missing")
    texts = [
        item.get("text")
        for item in ocr
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    names = [
        text
        for text in texts
        if "阿普利亚公爵" in text and "罗贝尔" in text
    ]
    if len(names) != 1:
        raise AgentError("player character identity is not uniquely visible")

    def visible_count(prefix: str) -> int | None:
        matches: list[int] = []
        for text in texts:
            normalized = re.sub(r"\s+", "", text)
            match = re.fullmatch(re.escape(prefix) + r"[（(]?([0-9]+)[）)]?", normalized)
            if match:
                matches.append(int(match.group(1)))
        return matches[0] if len(matches) == 1 else None

    return {
        "character": names[0],
        "is_player": True,
        "spouse_visible": texts.count("配偶") == 1,
        "player_heir_visible": texts.count("玩家继承人") == 1,
        "kin_count": visible_count("亲族"),
        "courtier_count": visible_count("廷臣"),
        "vassal_count": visible_count("臣属"),
        "source_observation_id": observation.get("observation_id"),
        "policy_boundary": "player-visible OCR only",
    }


def _extract_lifestyle_state(observation: dict[str, object]) -> dict[str, object]:
    """Record the visible lifestyle decision that the opening selected."""
    if observation.get("screen") != "lifestyle_martial_authority":
        raise AgentError("lifestyle state requires the selected authority screen")
    ocr = observation.get("ocr")
    if not isinstance(ocr, list):
        raise AgentError("lifestyle observation OCR is missing")
    texts = [
        re.sub(r"\s+", "", item.get("text", ""))
        for item in ocr
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    if texts.count("军事生活方式") != 1 or texts.count("当前：权威重心") != 1:
        raise AgentError("selected military authority focus is not uniquely visible")
    return {
        "lifestyle": "军事",
        "focus": "权威",
        "visible_current_focus": "当前：权威重心",
        "source_observation_id": observation.get("observation_id"),
        "strategy": "growth100.stabilize-domain-control-v1",
        "policy_boundary": "player-visible OCR only",
    }


def _extract_map_date(observation: dict[str, object]) -> dict[str, object]:
    """Read the rendered CK3 calendar from a visible map observation."""
    if observation.get("screen") not in {"map_hud", "map_running"}:
        raise AgentError("map date requires a paused or running map screen")
    ocr = observation.get("ocr")
    if not isinstance(ocr, list):
        raise AgentError("map observation OCR is missing")
    matches: list[tuple[str, int, int, int]] = []
    for item in ocr:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            continue
        text = re.sub(r"\s+", "", item["text"])
        match = re.search(
            r"(?:公元)?(\d{3,4})年(\d{1,2})月(\d{1,2})日",
            text,
        )
        if match:
            matches.append((text, *(int(value) for value in match.groups())))
    if len(matches) != 1:
        raise AgentError("map date is not uniquely visible")
    visible_text, year, month, day = matches[0]
    try:
        ordinal = datetime(year, month, day, tzinfo=timezone.utc).toordinal()
    except ValueError as error:
        raise AgentError("map date is invalid") from error
    return {
        "year": year,
        "month": month,
        "day": day,
        "ordinal": ordinal,
        "visible_text": visible_text,
        "source_observation_id": observation.get("observation_id"),
        "policy_boundary": "player-visible OCR only",
    }


def _drive_opening(
    spec: EnvironmentSpec,
    handle: SessionHandle,
    manifest: dict[str, object],
    artifacts: Path,
    events: Path,
    contract_path: Path,
    contract_sha256: str,
    deadline: float,
) -> dict[str, object]:
    from .control import VisibleUiDriver
    from .control.executor import _prepare_key_press_batch
    from .vision import load_ui_contract

    display = manifest.get("display")
    if not isinstance(display, dict):
        raise AgentError("prepared display contract is missing")
    language = str(display.get("language", ""))
    contract = load_ui_contract(contract_path, expected_sha256=contract_sha256)
    window = _bind_window(spec, handle, deadline)
    append_event(
        events,
        {
            "kind": "foreground_activation_planned",
            "pid": window.pid,
            "hwnd": window.hwnd,
        },
    )
    foreground = window.request_foreground_without_input(
        responsive_gate_timeout_seconds=min(
            30.0, _remaining(deadline, "foreground activation")
        ),
        responsive_gate_deadline=deadline,
    )
    append_event(
        events,
        {
            "kind": "foreground_activation_finished",
            "pid": window.pid,
            "hwnd": window.hwnd,
            "status": "confirmed",
            "attestation": foreground,
        },
    )

    def new_driver() -> VisibleUiDriver:
        return VisibleUiDriver(
            window,
            contract,
            artifacts,
            expected_game_version=spec.expected_game_version,
            expected_language=language,
            expected_contract_sha256=contract_sha256,
            durable_event_callback=lambda event: append_event(events, event),
            allowed_controls=OPENING_ALLOWED_CONTROLS,
        )

    actions: list[dict[str, object]] = []

    def click(
        screen: str,
        control_id: str,
        next_stage: str,
        *,
        observe_timeout_seconds: float | None = None,
        post_timeout_seconds: float | None = None,
    ) -> dict[str, object]:
        driver = new_driver()
        observation_timeout = _remaining(deadline, f"stable {screen}")
        if observe_timeout_seconds is not None:
            observation_timeout = min(
                observation_timeout, observe_timeout_seconds
            )
        stable = driver.observe_stable(
            screen,
            observation_timeout,
            stable_frames=2,
        )
        matches = [
            control for control in stable.controls if control.control_id == control_id
        ]
        if len(matches) != 1:
            visible = sorted(control.control_id for control in stable.controls)
            raise AgentError(
                f"{screen} lacks one {control_id} control; visible={visible!r}"
            )
        transition_timeout = _remaining(deadline, next_stage)
        if post_timeout_seconds is not None:
            transition_timeout = min(transition_timeout, post_timeout_seconds)
        transition = driver.click_visible_control(
            matches[0].token,
            timeout_seconds=transition_timeout,
        )
        action = transition.get("action")
        observation = transition.get("observation")
        if not isinstance(action, dict) or not isinstance(observation, dict):
            raise AgentError(f"{control_id} transition result is malformed")
        if action.get("status") != "confirmed":
            raise AgentError(f"{control_id} was not confirmed")
        actions.append(_action_summary(action))
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": control_id,
                "result_screen": observation.get("screen"),
                "result_observation_id": observation.get("observation_id"),
            },
        )
        return observation

    def toggle_player_character(
        screen: str, next_screen: str, next_stage: str
    ) -> None:
        driver = new_driver()
        driver.observe_stable(
            screen,
            _remaining(deadline, f"stable {screen} before F1"),
            stable_frames=2,
        )
        window.require_foreground()
        append_event(
            events,
            {
                "kind": "opening_key_input_planned",
                "control_id": "player_character.close",
                "key": "f1",
                "scan_code": 0x3B,
                "expected_post_screen": next_screen,
            },
        )
        accepted, last_error = _prepare_key_press_batch(0x3B)()
        if accepted != 2:
            raise AgentError(
                "F1 character-window toggle SendInput was partial: "
                f"accepted={accepted}, last_error={last_error}"
            )
        stable = driver.observe_stable(
            next_screen,
            _remaining(deadline, next_stage),
            stable_frames=2,
        )
        actions.append(
            {
                "control_id": "player_character.close",
                "status": "confirmed",
                "input_kind": "keyboard",
                "key": "f1",
                "scan_code": 0x3B,
                "send_input": {
                    "requested": 2,
                    "accepted": accepted,
                    "last_error": last_error,
                },
                "result_observation_id": stable.observation_id,
                "expected_post_screen": next_screen,
            }
        )
        append_event(
            events,
            {
                "kind": "opening_step_completed",
                "control_id": "player_character.close",
                "result_screen": stable.screen,
                "result_observation_id": stable.observation_id,
            },
        )

    click(
        "main_menu",
        "main_menu.new_game",
        "bookmark lobby",
        observe_timeout_seconds=INITIAL_MAIN_MENU_TIMEOUT_SECONDS,
    )
    click(
        "bookmark_lobby",
        "bookmark_lobby.select_robert",
        "Robert selection",
    )
    click(
        "bookmark_lobby_selected",
        "bookmark_lobby.start_game",
        "first pact event",
    )
    click(
        "pact_event",
        "pact_event.accept_contract",
        "first-life explanation",
    )
    click(
        "first_life_event",
        "first_life_event.begin",
        "first blessing choice",
    )
    blessing_driver = new_driver()
    blessing_stable = blessing_driver.observe_stable(
        "blessing_event",
        _remaining(deadline, "stable first blessing choice"),
        stable_frames=2,
    )
    selected, visible_text, strategy_score = _choose_first_blessing(blessing_stable)
    blessing_transition = blessing_driver.click_visible_control(
        selected.token,
        timeout_seconds=min(
            _remaining(deadline, "first curse choice"),
            INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
        ),
    )
    blessing_action = blessing_transition.get("action")
    final_observation = blessing_transition.get("observation")
    if not isinstance(blessing_action, dict) or not isinstance(
        final_observation, dict
    ):
        raise AgentError("first blessing transition result is malformed")
    if blessing_action.get("status") != "confirmed":
        raise AgentError("first blessing choice was not confirmed")
    action_summary = _action_summary(blessing_action)
    action_summary["visible_choice"] = visible_text
    action_summary["strategy_score"] = strategy_score
    actions.append(action_summary)
    append_event(
        events,
        {
            "kind": "opening_step_completed",
            "control_id": selected.control_id,
            "result_screen": final_observation.get("screen"),
            "result_observation_id": final_observation.get("observation_id"),
        },
    )
    if final_observation.get("screen") != "curse_event":
        raise AgentError("opening did not reach the first curse choice")
    curse_driver = new_driver()
    curse_stable = curse_driver.observe_stable(
        "curse_event",
        _remaining(deadline, "stable first curse choice"),
        stable_frames=2,
    )
    curse_selected, curse_text, curse_loss = _choose_first_curse(curse_stable)
    curse_transition = curse_driver.click_visible_control(
        curse_selected.token,
        timeout_seconds=min(
            _remaining(deadline, "playable map"),
            INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
        ),
    )
    curse_action = curse_transition.get("action")
    final_observation = curse_transition.get("observation")
    if not isinstance(curse_action, dict) or not isinstance(final_observation, dict):
        raise AgentError("first curse transition result is malformed")
    if curse_action.get("status") != "confirmed":
        raise AgentError("first curse choice was not confirmed")
    curse_summary = _action_summary(curse_action)
    curse_summary["visible_choice"] = curse_text
    curse_summary["strategy_loss"] = curse_loss
    actions.append(curse_summary)
    append_event(
        events,
        {
            "kind": "opening_step_completed",
            "control_id": curse_selected.control_id,
            "result_screen": final_observation.get("screen"),
            "result_observation_id": final_observation.get("observation_id"),
        },
    )
    if final_observation.get("screen") != "map_hud":
        raise AgentError("opening did not reach the playable map after its first pair")
    final_observation = click(
        "map_hud",
        "map_hud.open_player_character",
        "player character state",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    player_state = _extract_player_character_state(final_observation)
    toggle_player_character(
        "player_character",
        "map_hud",
        "playable map after player inspection",
    )
    click(
        "map_hud",
        "map_hud.open_lifestyle",
        "lifestyle selection",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    click(
        "lifestyle_selection",
        "lifestyle_selection.open_martial",
        "martial lifestyle",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    click(
        "lifestyle_martial_unfocused",
        "lifestyle_martial.select_authority_focus",
        "authority focus confirmation",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    final_observation = click(
        "lifestyle_authority_confirmation",
        "lifestyle_authority_confirmation.confirm",
        "selected authority focus",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    lifestyle_state = _extract_lifestyle_state(final_observation)
    final_observation = click(
        "lifestyle_martial_authority",
        "lifestyle_martial_authority.close",
        "paused map after lifestyle selection",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    starting_date = _extract_map_date(final_observation)
    final_observation = click(
        "map_hud",
        "map_hud.set_speed_five",
        "speed five selected",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    final_observation = click(
        "map_hud",
        "map_hud.resume",
        "running timeline",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    running_date = _extract_map_date(final_observation)
    if int(running_date["ordinal"]) <= int(starting_date["ordinal"]):
        raise AgentError("CK3 timeline did not advance after resume")
    final_observation = click(
        "map_running",
        "map_running.pause",
        "paused advanced timeline",
        post_timeout_seconds=INSTANT_UI_TRANSITION_TIMEOUT_SECONDS,
    )
    paused_date = _extract_map_date(final_observation)
    if int(paused_date["ordinal"]) < int(running_date["ordinal"]):
        raise AgentError("paused map date moved backwards")
    return {
        "character": "Robert the Fox, Duke of Apulia",
        "bookmark": "1066",
        "actions": actions,
        "first_blessing_choice": {
            "control_id": selected.control_id,
            "visible_text": visible_text,
            "strategy_score": strategy_score,
            "strategy": "growth100.first-blessing-visible-v1",
        },
        "first_curse_choice": {
            "control_id": curse_selected.control_id,
            "visible_text": curse_text,
            "strategy_loss": curse_loss,
            "strategy": "growth100.first-curse-visible-v1",
        },
        "player_character_state": player_state,
        "lifestyle_state": lifestyle_state,
        "time_progression": {
            "strategy": "speed-five-visible-date-v1",
            "starting_date": starting_date,
            "running_date": running_date,
            "paused_date": paused_date,
            "elapsed_days": int(paused_date["ordinal"])
            - int(starting_date["ordinal"]),
            "policy_boundary": "player-visible OCR and rendered timeline controls only",
        },
        "final_screen": final_observation.get("screen"),
        "final_observation_id": final_observation.get("observation_id"),
        "window_binding": window.audit_binding(),
        "foreground_activation": foreground,
    }


def opening_smoke(
    spec: EnvironmentSpec, timeout_seconds: float = 300
) -> dict[str, object]:
    """Complete Robert's first bargain pair and choose his opening focus."""
    ensure_state_path_safe(spec.state_dir)
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise AgentError("opening timeout must be finite and positive")
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "opening-smoke"):
            manifest = verify_profile(spec)
            doctor(spec, require_prepared=True)
            if ck3_process_inventory()["processes"]:
                raise AgentError("refusing opening smoke while CK3 is already running")
            return _opening_smoke_locked(spec, manifest, float(timeout_seconds))


def _opening_smoke_locked(
    spec: EnvironmentSpec,
    manifest: dict[str, object],
    timeout_seconds: float,
) -> dict[str, object]:
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-opening-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    events = run_dir / "events.jsonl"
    artifacts.mkdir(parents=True, exist_ok=False)
    contract_archive = run_dir / "opening-ui-contract.json"
    shutil.copy2(OPENING_CONTRACT, contract_archive)
    contract_sha256 = sha256_file(contract_archive)
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run_id,
        "kind": "ck3_opening_smoke",
        "started_at": utc_now(),
        "environment_sha256": manifest.get("environment_sha256"),
        "contract": {
            "path": contract_archive.name,
            "sha256": contract_sha256,
        },
        "finalized": False,
        "ok": False,
    }
    report_path = run_dir / "report.json"
    write_json_atomic(report_path, report)
    append_event(
        events,
        {
            "kind": "opening_started",
            "environment_sha256": manifest.get("environment_sha256"),
            "contract_sha256": contract_sha256,
        },
    )
    deadline = time.monotonic() + timeout_seconds
    handle: SessionHandle | None = None
    primary_error: BaseException | None = None
    try:
        log("launching CK3 for Robert 1066 opening")
        handle = launch(spec)
        report["process"] = {
            "pid": int(handle.process.pid),
            "creation_date": handle.ck3_creation_date,
        }
        append_event(events, {"kind": "ck3_launched", "pid": handle.process.pid})
        report["load_attestation"] = wait_for_runtime_attestation(
            spec,
            handle,
            _remaining(deadline, "runtime load attestation"),
        )
        append_event(events, {"kind": "single_mod_runtime_attested"})
        report["opening"] = _drive_opening(
            spec,
            handle,
            manifest,
            artifacts,
            events,
            contract_archive,
            contract_sha256,
            deadline,
        )
    except BaseException as error:
        primary_error = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if handle is not None:
            try:
                shutdown = stop_tracked(
                    handle, require_running=primary_error is None
                )
                report["shutdown_attestation"] = shutdown
                if shutdown.get("ok") is not True and primary_error is None:
                    primary_error = AgentError(
                        "opening shutdown contract failed: "
                        + "; ".join(
                            str(item)
                            for item in shutdown.get("contract_errors", [])
                        )
                    )
                    report["error"] = str(primary_error)
            except BaseException as error:
                report["shutdown_error"] = f"{type(error).__name__}: {error}"
                if primary_error is None:
                    primary_error = error
        report["finished_at"] = utc_now()
        report["ok"] = primary_error is None
        report["finalized"] = True
        append_event(
            events,
            {
                "kind": "opening_finished",
                "ok": report["ok"],
                "final_screen": (
                    report.get("opening", {}).get("final_screen")
                    if isinstance(report.get("opening"), dict)
                    else None
                ),
            },
        )
        write_json_atomic(report_path, report)
    if primary_error is not None:
        if not isinstance(primary_error, Exception):
            raise primary_error
        raise AgentError(
            f"opening smoke failed; report={report_path}: {primary_error}"
        ) from primary_error
    return report
