#!/usr/bin/env python3
"""Collect the player-subject Stage 10 terminal from an exact Stage 9 boundary.

The cell starts only while the played Central owner is paused on ``zg361cl.390``.
It selects one provider-observed direct AI manager, saves that exact source,
acknowledges Stage 9, and observes the two-day Stage 10 pump opening this
manager's F case.  It then rebinds the player before the first delayed F ticket.
The existing manager-governance provider owns the terminal proof when the real
``zg361mg.120`` event appears.

No process lifecycle is owned here.  A failed attempt is not retried in place;
the caller may restore the source checkpoint and start a new bounded attempt.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import sys
from typing import Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "ck3_autonomous_player/src") not in sys.path:
    sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))

from xar_autoplayer.bridge.set_played_character_contract import (  # noqa: E402
    SET_PLAYED_CHARACTER_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_manager_subordinate_selector_contract import (  # noqa: E402
    QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY,
)

import zg361_phase2_promotion_source_production_entry as entry  # noqa: E402
from zg361_phase2_terminal_stages_action_cell import (  # noqa: E402
    _ack_summary,
    _typed,
)
from zhongguo_phase2_workforce_action import (  # noqa: E402
    _event_context,
    _saved_character_id,
    _scope_character_id,
)


STAGE9_EVENT = "zg361cl.390"
STAGE10_EVENT = "zg361mg.120"
MAX_ADVANCE_DAYS = 30
ENTRY_TIMEOUT_SECONDS = 600.0
PROGRESS_SAMPLE_DAYS = 1

Navigator = Callable[..., dict[str, object]]


class Stage10PlayerSubjectError(RuntimeError):
    def __init__(self, reason_code: str, evidence: Mapping[str, object]):
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"Stage 10 player-subject cell RED [{reason_code}]")


def _write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _positive(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 2**31 - 1:
        raise ValueError(f"{label} must be a positive signed CharacterID")
    return value


def _binding(snapshot: object) -> dict[str, int]:
    if not isinstance(snapshot, Mapping):
        raise ValueError("snapshot is not an object")
    diagnostics = snapshot.get("diagnostics")
    played = snapshot.get("played_character")
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(diagnostics, Mapping)
        or not isinstance(played, Mapping)
    ):
        raise ValueError("Stage 10 requires a paused map-ready native frame")
    return {
        "bridge_pid": _positive(diagnostics.get("bridge_pid"), "bridge PID"),
        "connection_generation": _positive(
            diagnostics.get("connection_generation"), "connection generation"
        ),
        "player_character_id": _positive(
            played.get("character_id"), "played character"
        ),
        "date_raw": int(snapshot["date_raw"]),
    }


def _save(service: object, snapshot: Mapping[str, object], label: str) -> dict[str, object]:
    result = service.save_checkpoint(expected_revision=int(snapshot["revision"]))
    checkpoint = result.get("checkpoint") if isinstance(result, Mapping) else None
    if not (
        isinstance(result, Mapping)
        and result.get("accepted") is True
        and isinstance(checkpoint, Mapping)
        and checkpoint.get("status") == "saved"
    ):
        raise ValueError(f"{label} checkpoint was not saved")
    return copy.deepcopy(dict(result))


def _terminal_provider(
    provider: object, *, owner: int, subject: int
) -> dict[str, object]:
    if not isinstance(provider, Mapping):
        raise ValueError("Stage 10 provider is not an object")
    readiness = provider.get("readiness")
    binding = provider.get("binding")
    case = provider.get("f_case")
    if not (
        provider.get("status") == "available"
        and provider.get("unavailable_reason") is None
        and isinstance(readiness, Mapping)
        and readiness.get("ready") is True
        and provider.get("player_character_id") == subject
        and isinstance(binding, Mapping)
        and binding.get("subject_character_id") == subject
        and binding.get("owner_character_id") == owner
        and binding.get("subject_binding_kind") == "played_character"
        and _typed(case, "owner_character_id") == owner
        and _typed(case, "subject_character_id") == subject
        and _typed(case, "state") == 5
        and _typed(case, "active") is False
    ):
        raise ValueError("Stage 10 player-subject F case is not terminal")
    return copy.deepcopy(dict(provider))


def _active_provider(
    provider: object, *, owner: int, subject: int
) -> dict[str, object] | None:
    if not isinstance(provider, Mapping) or provider.get("status") != "available":
        return None
    binding = provider.get("binding")
    case = provider.get("f_case")
    try:
        state = _typed(case, "state")
        active = _typed(case, "active")
        exact = (
            provider.get("player_character_id") == owner
            and isinstance(binding, Mapping)
            and binding.get("subject_character_id") == subject
            and binding.get("owner_character_id") == owner
            and binding.get("subject_binding_kind")
            == "bounded_ai_direct_manager"
            and _typed(case, "owner_character_id") == owner
            and _typed(case, "subject_character_id") == subject
            and isinstance(state, int)
            and not isinstance(state, bool)
            and 1 <= state <= 4
            and active is True
        )
    except ValueError:
        return None
    return copy.deepcopy(dict(provider)) if exact else None


def run_stage10_player_subject(
    service: object,
    *,
    evidence_directory: Path,
    request_nonce: str,
    navigator: Navigator = entry.enter_promotion_source_checkpoint_v1,
) -> dict[str, object]:
    """Run one 30-day maximum Stage 10 player-subject acceptance slice."""

    if not isinstance(request_nonce, str) or re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{0,47}", request_nonce
    ) is None:
        raise ValueError("request_nonce must be a nonempty ASCII token of at most 48 characters")
    directory = Path(evidence_directory)
    path = directory / "stage10-player-subject.json"
    state: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_stage10_player_subject_action_cell",
        "result": "RED",
        "request_nonce": request_nonce,
        "mcp_only": True,
        "max_advance_days": MAX_ADVANCE_DAYS,
        "source_event_definition_key": STAGE9_EVENT,
        "target_event_definition_key": STAGE10_EVENT,
        "action_ack_is_business_postcondition": False,
        "failure_reason": None,
    }
    try:
        capabilities = service.capabilities()
        available = capabilities.get("bridge_capabilities") if isinstance(capabilities, Mapping) else None
        required = {
            QUERY_ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_CAPABILITY,
            QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
            SET_PLAYED_CHARACTER_V1_CAPABILITY,
        }
        if not isinstance(available, list) or not required.issubset(set(available)):
            raise Stage10PlayerSubjectError(
                "required_capability_unavailable",
                {**state, "required_capabilities": sorted(required), "bridge_capabilities": available},
            )

        initial = service.snapshot()
        owner_binding = _binding(initial)
        owner = owner_binding["player_character_id"]
        source_context = _event_context(
            service, initial, expected_definition=STAGE9_EVENT
        )
        if _scope_character_id(source_context.get("root_scope"), "Stage 9 root") != owner:
            raise ValueError("Stage 9 event root is not the played Central owner")
        state["owner_binding"] = owner_binding
        state["source_event_context"] = source_context

        current = service.snapshot()
        if _binding(current) != owner_binding:
            raise ValueError("Stage 9 source changed during qualification")
        selector = service.query_zhongguo_manager_subordinate_selector_v1(
            request_nonce + ".select", expected_revision=int(current["revision"])
        )
        readiness = selector.get("readiness") if isinstance(selector, Mapping) else None
        selection = selector.get("selection") if isinstance(selector, Mapping) else None
        manager = (
            selection.get("manager_character_id")
            if isinstance(selection, Mapping)
            else None
        )
        if not (
            isinstance(selector, Mapping)
            and selector.get("status") == "available"
            and selector.get("provider_observed") is True
            and isinstance(readiness, Mapping)
            and readiness.get("ready") is True
            and isinstance(selection, Mapping)
        ):
            raise Stage10PlayerSubjectError(
                "eligible_manager_unavailable", {**state, "selector": selector}
            )
        manager = _positive(manager, "selected manager")
        if manager == owner:
            raise ValueError("selector returned the played Central owner")
        state["selector"] = copy.deepcopy(dict(selector))
        state["selected_manager_character_id"] = manager

        current = service.snapshot()
        if _binding(current) != owner_binding:
            raise ValueError("Stage 9 source changed before checkpoint save")
        state["source_checkpoint"] = _save(service, current, "Stage 9 source")
        state["stage9_acknowledgement"] = _ack_summary(service, source_context)

        progress: dict[str, object] = {
            "timeline_origin_date_raw": owner_binding["date_raw"],
            "absolute_end_date_raw": owner_binding["date_raw"]
            + MAX_ADVANCE_DAYS * 24,
            "timeline_interrupt_drains": [],
        }
        state["progress"] = progress

        def observe_open_case(
            observed_snapshot: Mapping[str, object],
        ) -> Mapping[str, object] | None:
            if _binding(observed_snapshot)["player_character_id"] != owner:
                raise ValueError("Stage 10 opening probe left the Central owner")
            response = service.query_zhongguo_manager_governance_snapshot_v1(
                request_nonce + ".open",
                expected_revision=int(observed_snapshot["revision"]),
                subject_character_id=manager,
                owner_character_id=owner,
            )
            state["opening_latest_provider"] = copy.deepcopy(response)
            _write(path, state)
            opened = _active_provider(response, owner=owner, subject=manager)
            if opened is not None:
                state["opening_provider"] = opened
            return opened

        _write(path, state)
        opening_navigation = navigator(
            service,
            timeout_seconds=ENTRY_TIMEOUT_SECONDS,
            progress_sample_interval_days=PROGRESS_SAMPLE_DAYS,
            prefer_natural_cycle=True,
            pause_on_event_definition_key=STAGE10_EVENT,
            evidence_out=progress,
            terminal_observation_probe=observe_open_case,
        )
        opened = opening_navigation.get("terminal_observation")
        if _active_provider(opened, owner=owner, subject=manager) is None:
            raise ValueError("selected manager did not enter the current Stage 10 F case")
        state["opening_navigation"] = copy.deepcopy(dict(opening_navigation))

        current = service.snapshot()
        current_binding = _binding(current)
        if (
            current_binding["bridge_pid"] != owner_binding["bridge_pid"]
            or current_binding["connection_generation"]
            != owner_binding["connection_generation"]
            or current_binding["player_character_id"] != owner
            or current_binding["date_raw"] > progress["absolute_end_date_raw"]
        ):
            raise ValueError("Stage 10 opening probe changed the owner lineage")
        switch = service.set_player_character_v1(
            manager, expected_revision=int(current["revision"])
        )
        manager_snapshot = service.snapshot()
        manager_binding = _binding(manager_snapshot)
        if not (
            isinstance(switch, Mapping)
            and switch.get("accepted") is True
            and switch.get("status") in {"switched", "already_played"}
            and switch.get("to_character_id") == manager
            and switch.get("postcondition_verified") is True
            and manager_binding["bridge_pid"] == owner_binding["bridge_pid"]
            and manager_binding["connection_generation"]
            == owner_binding["connection_generation"]
            and manager_binding["date_raw"] == current_binding["date_raw"]
            and manager_binding["player_character_id"] == manager
        ):
            raise ValueError("played-character switch lost its same-session postcondition")
        state["player_switch"] = copy.deepcopy(dict(switch))
        state["manager_binding"] = manager_binding

        _write(path, state)
        navigation = navigator(
            service,
            timeout_seconds=ENTRY_TIMEOUT_SECONDS,
            progress_sample_interval_days=PROGRESS_SAMPLE_DAYS,
            prefer_natural_cycle=True,
            pause_on_event_definition_key=STAGE10_EVENT,
            evidence_out=progress,
        )
        state["navigation"] = copy.deepcopy(dict(navigation))
        terminal_snapshot = service.snapshot()
        terminal_binding = _binding(terminal_snapshot)
        if (
            terminal_binding["bridge_pid"] != manager_binding["bridge_pid"]
            or terminal_binding["connection_generation"]
            != manager_binding["connection_generation"]
            or terminal_binding["player_character_id"] != manager
            or terminal_binding["date_raw"] > progress["absolute_end_date_raw"]
        ):
            raise ValueError("Stage 10 navigation left its bounded player-subject lineage")
        context = _event_context(
            service, terminal_snapshot, expected_definition=STAGE10_EVENT
        )
        if _scope_character_id(context.get("root_scope"), "Stage 10 root") != manager:
            raise ValueError("Stage 10 event root is not the played manager")
        event_owner = _saved_character_id(context, "zg361_mg_f_ticket_owner")
        event_subject = _saved_character_id(context, "zg361_mg_f_ticket_subject")
        if event_owner != owner or event_subject != manager:
            raise ValueError("Stage 10 event left the selected owner/manager case")

        current = service.snapshot()
        provider = service.query_zhongguo_manager_governance_snapshot_v1(
            request_nonce + ".terminal",
            expected_revision=int(current["revision"]),
            subject_character_id=manager,
            owner_character_id=owner,
        )
        provider = _terminal_provider(provider, owner=owner, subject=manager)
        state["terminal_event_context"] = context
        state["terminal_provider"] = provider
        current = service.snapshot()
        state["terminal_checkpoint"] = _save(
            service, current, "Stage 10 terminal"
        )
        state["terminal_acknowledgement"] = _ack_summary(service, context)
        final = service.snapshot()
        if _binding(final)["player_character_id"] != manager:
            raise ValueError("Stage 10 acknowledgement changed the played manager")

        gate = {
            "result": "GREEN",
            "event_definition_key": STAGE10_EVENT,
            "provider_domain": "manager_governance",
            "terminal_state": "complete",
            "provider_observed": True,
            "terminal_postcondition_verified": True,
            "owner_character_id": owner,
            "subject_character_id": manager,
            "role_topology": "ai_central_owner_to_player_manager_subject",
            "provider_observation": provider,
            "action_ack_is_business_postcondition": False,
        }
        state["p1_acceptance_evidence"] = {
            "central_stage_10_terminal": gate
        }
        state["terminal_binding"] = terminal_binding
        state["final_snapshot"] = final
        state["result"] = "GREEN"
        state["failure_reason"] = None
        return state
    except Stage10PlayerSubjectError as error:
        state = copy.deepcopy(error.evidence)
        raise
    except Exception as error:
        state["failure_reason"] = f"{type(error).__name__}: {error}"
        raise Stage10PlayerSubjectError("stage10_slice_failed", state) from error
    finally:
        _write(path, state)


__all__ = [
    "ENTRY_TIMEOUT_SECONDS",
    "MAX_ADVANCE_DAYS",
    "PROGRESS_SAMPLE_DAYS",
    "STAGE9_EVENT",
    "STAGE10_EVENT",
    "Stage10PlayerSubjectError",
    "run_stage10_player_subject",
]
