#!/usr/bin/env python3
"""Product-only CK3 Switch Character transition for the Phase 2 endgame.

The transition is intentionally narrower than a character-rebind API.  Its
target CharacterID comes from the live ``zg361we.361`` saved subject scope;
the caller supplies only that subject's landed-title key so the existing
exact-build title-map capability can put the native map selection target at
the current CK3 client centre.  The ordinary single-player UI then performs
the switch.  GREEN is never inferred from keyboard/mouse submission: the
native bridge must subsequently observe the exact subject, unchanged date,
paused state, PID and connection generation before a child checkpoint is
saved and handed to the strict production binder.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import time
from typing import Final, Mapping, Protocol

from zg361_phase2_cross_cycle_endgame_action_cell import (
    EndgameResultBinding,
    EndgameSubjectProofSession,
    PRODUCTION_SUBJECT_TRANSITION_MODE,
    RESULT_EVENT,
)
from zg361_phase2_cross_cycle_endgame_production_subject import (
    EXACT_EXE_SHA256,
    EXACT_GAME_VERSION,
    PRODUCTION_SUBJECT_CHECKPOINT_KIND,
    bind_product_subject_checkpoint_session,
)


TITLE_NAVIGATION_CAPABILITY: Final = (
    "game.command.center-map-on-landed-title-v1"
)
RESULT_OPTION_NUMBER: Final = 1
DEFAULT_TIMEOUT_SECONDS: Final = 60.0
DEFAULT_POLL_INTERVAL_SECONDS: Final = 0.10
UI_SOURCE_CONTRACT_KIND: Final = (
    "ck3_1_19_0_6_single_player_switch_character_ui_v1"
)

_REQUIRED_UI_SOURCES: Final = {
    "game/gui/frontend_ingame_menu.gui": (
        'name = "switch_character_button"',
        'text = "FRONTEND_SWITCH_CHARACTER"',
        'shortcut = "menu_switch"',
        'onclick = "[PauseMenu.SwitchCharacter]"',
        "GameHasMultiplePlayers",
        "IsIronmanEnabled",
    ),
    "game/gui/frontend_bookmarks.gui": (
        'name = "pick_any_character_button"',
        "shortcut = any_ruler",
        'name = "start_button"',
        'onclick = "[GameSetup.StartGame]"',
        'shortcut = "confirm"',
    ),
    "game/gui/shortcuts.shortcuts": (
        'confirm = "RETURN"',
        'any_ruler = "tab"',
        'menu_switch = "3"',
    ),
}


class ProductSwitchCharacterError(RuntimeError):
    """Typed RED emitted before a product subject session can be bound."""

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **dict(evidence),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"product Switch Character RED [{reason_code}]")


def _fail(reason_code: str, **evidence: object) -> None:
    raise ProductSwitchCharacterError(reason_code, evidence)


class ProductSwitchService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]: ...

    def center_map_on_landed_title_v1(
        self, title_key: str, *, expected_revision: int
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...

    def query_zhongguo_ai_owned_case_snapshot_v1(
        self,
        owner_character_id: int,
        subject_character_id: int,
        request_nonce: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]: ...


class SwitchCharacterUiPort(Protocol):
    def switch_to_centered_title(
        self,
        *,
        expected_ck3_pid: int,
        evidence_directory: Path,
    ) -> Mapping[str, object]: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _positive_int(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        _fail("integer_binding_invalid", label=label, observed=value)
    return value


def _paused_binding(
    snapshot: object,
    *,
    expected_player: int,
    require_event: bool,
) -> dict[str, object]:
    if not isinstance(snapshot, Mapping):
        _fail("snapshot_not_an_object", snapshot=snapshot)
    played = snapshot.get("played_character")
    active = snapshot.get("active_event")
    diagnostics = snapshot.get("diagnostics")
    player = played.get("character_id") if isinstance(played, Mapping) else None
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "player_character_id": player,
        "bridge_pid": (
            diagnostics.get("bridge_pid")
            if isinstance(diagnostics, Mapping)
            else None
        ),
        "connection_generation": (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, Mapping)
            else None
        ),
        "event_instance_id": (
            active.get("instance_id") if isinstance(active, Mapping) else None
        ),
    }
    valid = (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and isinstance(binding["revision"], int)
        and not isinstance(binding["revision"], bool)
        and int(binding["revision"]) >= 0
        and isinstance(binding["native_revision"], int)
        and not isinstance(binding["native_revision"], bool)
        and int(binding["native_revision"]) > 0
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and isinstance(binding["episode_run_id"], str)
        and bool(binding["episode_run_id"])
        and player == expected_player
        and isinstance(binding["bridge_pid"], int)
        and not isinstance(binding["bridge_pid"], bool)
        and int(binding["bridge_pid"]) > 0
        and isinstance(binding["connection_generation"], int)
        and not isinstance(binding["connection_generation"], bool)
        and int(binding["connection_generation"]) > 0
        and (
            not require_event
            or (
                isinstance(binding["event_instance_id"], int)
                and not isinstance(binding["event_instance_id"], bool)
                and int(binding["event_instance_id"]) > 0
            )
        )
    )
    if not valid:
        _fail(
            "paused_managed_binding_unavailable",
            expected_player_character_id=expected_player,
            require_event=require_event,
            binding=binding,
        )
    return binding


def _require_result_surface(
    service: ProductSwitchService,
    snapshot: Mapping[str, object],
    binding: Mapping[str, object],
    result: EndgameResultBinding,
) -> dict[str, object]:
    response = service.query_current_event_window_context_v1(
        int(binding["event_instance_id"]),
        expected_revision=int(binding["revision"]),
    )
    context = (
        response.get("current_event_window_context")
        if isinstance(response, Mapping)
        else None
    )
    options = context.get("options") if isinstance(context, Mapping) else None
    enabled = (
        [
            row.get("native_option_index")
            for row in options
            if isinstance(row, Mapping)
            and row.get("shown") is True
            and row.get("enabled") is True
        ]
        if isinstance(options, list)
        else []
    )
    if not (
        isinstance(response, Mapping)
        and response.get("status") == "available"
        and isinstance(context, Mapping)
        and context.get("status") == "available"
        and context.get("event_definition_key") == RESULT_EVENT
        and context.get("current_event_instance_id")
        == binding["event_instance_id"]
        and context.get("snapshot_revision") == binding["native_revision"]
        and context.get("date_raw") == result.result_date_raw
        and enabled == [0, 1, 2]
    ):
        _fail(
            "owner_result_surface_not_actionable",
            result_binding=asdict(result),
            paused_binding=dict(binding),
            event_response=response,
        )
    return dict(context)


def _require_title_navigation(
    service: ProductSwitchService,
    *,
    title_key: str,
    binding: Mapping[str, object],
) -> dict[str, object]:
    capabilities = service.capabilities()
    available = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, Mapping)
        else None
    )
    if not isinstance(available, list) or TITLE_NAVIGATION_CAPABILITY not in available:
        _fail(
            "title_navigation_capability_unavailable",
            required_capability=TITLE_NAVIGATION_CAPABILITY,
            capabilities=capabilities,
        )
    try:
        navigation = service.center_map_on_landed_title_v1(
            title_key, expected_revision=int(binding["revision"])
        )
    except (TypeError, ValueError, RuntimeError) as error:
        _fail(
            "subject_title_navigation_red",
            subject_title_key=title_key,
            error=f"{type(error).__name__}: {error}",
        )
    title = navigation.get("title") if isinstance(navigation, Mapping) else None
    nav_binding = (
        navigation.get("binding") if isinstance(navigation, Mapping) else None
    )
    camera = (
        navigation.get("camera_center")
        if isinstance(navigation, Mapping)
        else None
    )
    if not (
        isinstance(navigation, Mapping)
        and navigation.get("accepted") is True
        and navigation.get("status") in {"centered", "already_centered"}
        and isinstance(title, Mapping)
        and title.get("key") == title_key
        and title.get("anchor_kind") == "title_bounds_center"
        and isinstance(nav_binding, Mapping)
        and nav_binding.get("date_raw") == binding["date_raw"]
        and nav_binding.get("episode_run_id") == binding["episode_run_id"]
        and nav_binding.get("connection_generation")
        == binding["connection_generation"]
        and isinstance(camera, Mapping)
        and camera.get("postcondition_verified") is True
        and camera.get("settled") is True
    ):
        _fail(
            "subject_title_navigation_not_settled",
            subject_title_key=title_key,
            owner_binding=dict(binding),
            navigation=navigation,
        )
    return dict(navigation)


def _archive_exact_checkpoint(
    checkpoint: Mapping[str, object],
    *,
    destination: Path,
    expected_sha256: str,
) -> dict[str, object]:
    raw_path = checkpoint.get("path")
    expected_bytes = checkpoint.get("bytes", checkpoint.get("size"))
    observed_sha = str(checkpoint.get("sha256", "")).upper()
    source = Path(raw_path).resolve() if isinstance(raw_path, str) else Path()
    expected_sha = str(expected_sha256).upper()
    if not (
        isinstance(raw_path, str)
        and source.is_absolute()
        and source.is_file()
        and isinstance(expected_bytes, int)
        and not isinstance(expected_bytes, bool)
        and expected_bytes > 0
        and source.stat().st_size == expected_bytes
        and observed_sha == expected_sha
        and len(expected_sha) == 64
        and _sha256(source) == expected_sha
    ):
        _fail(
            "checkpoint_source_bytes_invalid",
            checkpoint=dict(checkpoint),
            expected_sha256=expected_sha,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        _fail("checkpoint_archive_already_exists", path=str(destination))
    shutil.copyfile(source, destination)
    if destination.stat().st_size != expected_bytes or _sha256(destination) != expected_sha:
        _fail(
            "checkpoint_archive_copy_invalid",
            source=str(source),
            destination=str(destination),
        )
    return {
        "path": str(destination.resolve()),
        "bytes": expected_bytes,
        "sha256": expected_sha,
        "source_path": str(source),
    }


def _wait_for_binding(
    service: ProductSwitchService,
    *,
    expected_player: int,
    expected_date_raw: int,
    expected_pid: int,
    expected_generation: int,
    require_no_event: bool,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    deadline = time.monotonic() + timeout_seconds
    observations: list[dict[str, object]] = []
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            snapshot = service.snapshot()
            binding = _paused_binding(
                snapshot, expected_player=expected_player, require_event=False
            )
            active = snapshot.get("active_event")
            observations.append(
                {
                    **binding,
                    "active_event_present": active is not None,
                }
            )
            if (
                binding["date_raw"] == expected_date_raw
                and binding["bridge_pid"] == expected_pid
                and binding["connection_generation"] == expected_generation
                and (not require_no_event or active is None)
            ):
                return binding, observations
            last_error = "binding_mismatch"
        except ProductSwitchCharacterError as error:
            last_error = error.reason_code
        if poll_interval_seconds:
            time.sleep(poll_interval_seconds)
    _fail(
        "played_character_transition_not_observed",
        expected_player_character_id=expected_player,
        expected_date_raw=expected_date_raw,
        expected_bridge_pid=expected_pid,
        expected_connection_generation=expected_generation,
        require_no_event=require_no_event,
        last_error=last_error,
        observations=observations,
    )


def _save_child_checkpoint(
    service: ProductSwitchService,
    *,
    binding: Mapping[str, object],
    destination: Path,
) -> dict[str, object]:
    response = service.save_checkpoint(expected_revision=int(binding["revision"]))
    checkpoint = response.get("checkpoint") if isinstance(response, Mapping) else None
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    sha = str(checkpoint.get("sha256", "")).upper()
    if not (
        isinstance(response, Mapping)
        and response.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and len(sha) == 64
    ):
        _fail("subject_checkpoint_save_not_accepted", response=response)
    archived = _archive_exact_checkpoint(
        checkpoint, destination=destination, expected_sha256=sha
    )
    return {**archived, "save_response": dict(response)}


def produce_product_subject_checkpoint_session(
    service: ProductSwitchService,
    *,
    result: EndgameResultBinding,
    owner_result_checkpoint: Mapping[str, object],
    subject_title_key: str,
    ui: SwitchCharacterUiPort,
    evidence_directory: Path,
    expected_ck3_pid: int,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> EndgameSubjectProofSession:
    """Switch through CK3 UI, materialize child bytes, then invoke the binder."""

    if not isinstance(subject_title_key, str) or not subject_title_key:
        raise ValueError("subject_title_key must be a non-empty stable title key")
    if not callable(getattr(ui, "switch_to_centered_title", None)):
        raise TypeError("ui must implement switch_to_centered_title")
    if timeout_seconds <= 0 or poll_interval_seconds < 0:
        raise ValueError("switch wait bounds are invalid")
    expected_ck3_pid = _positive_int(expected_ck3_pid, "expected_ck3_pid")
    evidence_directory.mkdir(parents=True, exist_ok=True)

    owner_snapshot = service.snapshot()
    owner_binding = _paused_binding(
        owner_snapshot,
        expected_player=result.owner_character_id,
        require_event=True,
    )
    if not (
        owner_binding["date_raw"] == result.result_date_raw
        and owner_binding["bridge_pid"] == expected_ck3_pid
    ):
        _fail(
            "owner_result_binding_drifted",
            expected_result=asdict(result),
            owner_binding=owner_binding,
            expected_ck3_pid=expected_ck3_pid,
        )
    result_surface = _require_result_surface(
        service, owner_snapshot, owner_binding, result
    )
    owner_archive = _archive_exact_checkpoint(
        owner_result_checkpoint,
        destination=evidence_directory / "owner-result-zg361we-361.ck3",
        expected_sha256=result.result_checkpoint_sha256,
    )
    navigation = _require_title_navigation(
        service,
        title_key=subject_title_key,
        binding=owner_binding,
    )

    action_ack = service.select_event_option(
        RESULT_OPTION_NUMBER,
        event_instance_id=int(owner_binding["event_instance_id"]),
        expected_revision=int(owner_binding["revision"]),
    )
    if not (
        isinstance(action_ack, Mapping)
        and action_ack.get("accepted") is True
        and action_ack.get("status") == "submitted"
    ):
        _fail("result_event_dismiss_not_submitted", action_ack=action_ack)
    owner_after_event, owner_settle = _wait_for_binding(
        service,
        expected_player=result.owner_character_id,
        expected_date_raw=result.result_date_raw,
        expected_pid=int(owner_binding["bridge_pid"]),
        expected_generation=int(owner_binding["connection_generation"]),
        require_no_event=True,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )

    ui_receipt = ui.switch_to_centered_title(
        expected_ck3_pid=expected_ck3_pid,
        evidence_directory=evidence_directory,
    )
    if not (
        isinstance(ui_receipt, Mapping)
        and ui_receipt.get("result") == "GREEN"
        and ui_receipt.get("transition_mode")
        == PRODUCTION_SUBJECT_TRANSITION_MODE
        and ui_receipt.get("expected_ck3_pid") == expected_ck3_pid
        and ui_receipt.get("official_ui_switch_submitted") is True
        and ui_receipt.get("native_title_center_click") is True
        and ui_receipt.get("caller_coordinate_used") is False
        and ui_receipt.get("fixture_used") is False
        and ui_receipt.get("console_used") is False
        and ui_receipt.get("generic_character_rebind_used") is False
        and ui_receipt.get("business_postcondition_observed") is False
    ):
        _fail("official_switch_ui_receipt_invalid", ui_receipt=ui_receipt)

    subject_binding, subject_observations = _wait_for_binding(
        service,
        expected_player=result.subject_character_id,
        expected_date_raw=result.result_date_raw,
        expected_pid=int(owner_binding["bridge_pid"]),
        expected_generation=int(owner_binding["connection_generation"]),
        require_no_event=True,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    child_checkpoint = _save_child_checkpoint(
        service,
        binding=subject_binding,
        destination=evidence_directory / "played-subject-child.ck3",
    )
    post_save_snapshot = service.snapshot()
    post_save_binding = _paused_binding(
        post_save_snapshot,
        expected_player=result.subject_character_id,
        require_event=False,
    )
    if not (
        post_save_binding["date_raw"] == result.result_date_raw
        and post_save_binding["bridge_pid"] == owner_binding["bridge_pid"]
        and post_save_binding["connection_generation"]
        == owner_binding["connection_generation"]
        and post_save_snapshot.get("active_event") is None
    ):
        _fail(
            "subject_checkpoint_post_save_binding_drifted",
            owner_binding=owner_binding,
            subject_binding=subject_binding,
            post_save_binding=post_save_binding,
        )

    receipt = {
        "schema_version": 1,
        "kind": PRODUCTION_SUBJECT_CHECKPOINT_KIND,
        "result": "GREEN",
        "transition_mode": PRODUCTION_SUBJECT_TRANSITION_MODE,
        "game_version": EXACT_GAME_VERSION,
        "game_exe_sha256": EXACT_EXE_SHA256,
        "parent_result_checkpoint_sha256": result.result_checkpoint_sha256,
        "save_lineage_id": result.save_lineage_id,
        "source_event_definition_key": RESULT_EVENT,
        "owner_character_id": result.owner_character_id,
        "subject_character_id": result.subject_character_id,
        "player_character_id": result.subject_character_id,
        "date_raw": result.result_date_raw,
        "path": child_checkpoint["path"],
        "bytes": child_checkpoint["bytes"],
        "sha256": child_checkpoint["sha256"],
        "product_only": True,
        "official_ui_switch_observed": True,
        "fixture_used": False,
        "typed_event_fixture_used": False,
        "business_state_fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "owner_result_checkpoint": owner_archive,
        "owner_before": owner_binding,
        "owner_after_result_option": owner_after_event,
        "subject_after_switch": subject_binding,
        "subject_after_save": post_save_binding,
        "subject_title_key": subject_title_key,
        "title_navigation": navigation,
        "result_event_surface": result_surface,
        "result_event_action_ack": dict(action_ack),
        "owner_settle_observations": owner_settle,
        "ui_submission": dict(ui_receipt),
        "subject_observations": subject_observations,
    }
    receipt_path = evidence_directory / "product-subject-checkpoint-receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return bind_product_subject_checkpoint_session(service, result, receipt)


def preflight_switch_character_ui_source(game_root: Path) -> dict[str, object]:
    """Read exact vanilla UI sources only; never starts or attaches to CK3."""

    root = Path(game_root).resolve()
    files: dict[str, object] = {}
    missing: list[str] = []
    for relative, snippets in _REQUIRED_UI_SOURCES.items():
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            files[relative] = {
                "readable": False,
                "error": f"{type(error).__name__}: {error}",
            }
            missing.append(relative)
            continue
        absent = [snippet for snippet in snippets if snippet not in text]
        files[relative] = {
            "readable": True,
            "sha256": _sha256(path),
            "required_snippets": list(snippets),
            "missing_snippets": absent,
        }
        if absent:
            missing.append(relative)
    if missing:
        _fail(
            "exact_build_switch_ui_source_contract_red",
            game_root=str(root),
            failed_files=missing,
            files=files,
            ck3_launched=False,
        )
    return {
        "schema_version": 1,
        "kind": UI_SOURCE_CONTRACT_KIND,
        "result": "GREEN",
        "readiness": "static-ready-live-pending",
        "game_version": EXACT_GAME_VERSION,
        "game_exe_sha256": EXACT_EXE_SHA256,
        "game_root": str(root),
        "files": files,
        "semantic_shortcuts": {
            "pause_menu": "ESCAPE",
            "switch_character": "3",
            "any_ruler": "TAB",
            "start_selected_character": "RETURN",
        },
        "map_target_source": "exact_build_native_title_bounds_center",
        "caller_coordinates_allowed": False,
        "ck3_launched": False,
        "live_executed": False,
    }


__all__ = [
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "DEFAULT_TIMEOUT_SECONDS",
    "ProductSwitchCharacterError",
    "ProductSwitchService",
    "SwitchCharacterUiPort",
    "TITLE_NAVIGATION_CAPABILITY",
    "UI_SOURCE_CONTRACT_KIND",
    "preflight_switch_character_ui_source",
    "produce_product_subject_checkpoint_session",
]
