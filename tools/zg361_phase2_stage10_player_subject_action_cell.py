#!/usr/bin/env python3
"""Collect the player-manager Stage 10 terminal after one real B1 publication.

The cell starts from a paused, product-only player manager whose active B1 is
already at its frozen near-publication boundary.  An exact-build campaign-root
query must prove that the player is a celestial duke-or-higher with one
immediate superior.  The shared production navigator drains the remaining B1
publication tail and pauses on the new ``zg361mg.120`` player-subject terminal.
No player switch, fixture, console input, or fresh B1 opening belongs to this
route.

No process lifecycle is owned here. A contract-only repair may resume through
the operator on the retained paused CK3 process. The original absolute game-day
deadline and prior interrupt history remain authoritative across that resume.
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

from xar_autoplayer.bridge.campaign_root_context_contract import (  # noqa: E402
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (  # noqa: E402
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_promotion_source_progress_contract import (  # noqa: E402
    ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY,
    QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY,
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


STAGE10_EVENT = "zg361mg.120"
MAX_ADVANCE_DAYS = 120
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
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
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


def _campaign_source(
    response: object,
    *,
    expected_player: int,
    expected_owner: int,
) -> dict[str, object]:
    if not isinstance(response, Mapping):
        raise ValueError("campaign-root source is not an object")
    readiness = response.get("readiness")
    title = response.get("primary_title")
    government = response.get("government")
    flags = government.get("flags") if isinstance(government, Mapping) else None
    game_rules = response.get("selected_game_rule_tokens")
    if not (
        response.get("status") == "available"
        and response.get("unavailable_reason") is None
        and response.get("campaign_root_context_ready") is True
        and isinstance(readiness, Mapping)
        and readiness.get("ready") is True
        and response.get("player_character_id") == expected_player
        and response.get("player_character_alive") is True
        and response.get("independent") is False
        and response.get("immediate_liege_character_id") == expected_owner
        and expected_player != expected_owner
        and isinstance(title, Mapping)
        and isinstance(title.get("tier_raw"), int)
        and title.get("tier_raw") >= 3
        and isinstance(flags, list)
        and "government_is_celestial" in flags
        and isinstance(game_rules, list)
        and "zg361_on" in game_rules
    ):
        raise ValueError("source is not the contracted celestial player-manager")
    return copy.deepcopy(dict(response))


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
        and readiness.get("subject_binding_ready") is True
        and readiness.get("case_identity_ready") is True
        and readiness.get("same_frame_ready") is True
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


def run_stage10_player_subject(
    service: object,
    *,
    evidence_directory: Path,
    request_nonce: str,
    expected_player_manager_character_id: int,
    expected_owner_character_id: int,
    resume_progress: Mapping[str, object] | None = None,
    navigator: Navigator = entry.enter_promotion_source_checkpoint_v1,
) -> dict[str, object]:
    """Run one 120-day maximum near-publication B1 to Stage 10 slice."""

    if not isinstance(request_nonce, str) or re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._:-]{0,47}", request_nonce
    ) is None:
        raise ValueError(
            "request_nonce must be a nonempty ASCII token of at most 48 characters"
        )
    manager = _positive(
        expected_player_manager_character_id, "expected player manager"
    )
    owner = _positive(expected_owner_character_id, "expected owner")
    if manager == owner:
        raise ValueError("Stage 10 player manager and owner must differ")
    directory = Path(evidence_directory)
    path = directory / "stage10-player-subject.json"
    state: dict[str, object] = {
        "schema_version": 2,
        "kind": "zg361_phase2_stage10_player_subject_action_cell",
        "result": "RED",
        "request_nonce": request_nonce,
        "mcp_only": True,
        "max_advance_days": MAX_ADVANCE_DAYS,
        "source_route": "player_manager_real_b1_publication",
        "target_event_definition_key": STAGE10_EVENT,
        "expected_player_manager_character_id": manager,
        "expected_owner_character_id": owner,
        "action_ack_is_business_postcondition": False,
        "failure_reason": None,
    }
    try:
        capabilities = service.capabilities()
        available = (
            capabilities.get("bridge_capabilities")
            if isinstance(capabilities, Mapping)
            else None
        )
        required = {
            QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
            QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
            QUERY_PROMOTION_SOURCE_PROGRESS_V1_TRANSPORT_CAPABILITY,
            ACTIVATE_REVIEW_NOW_V1_TRANSPORT_CAPABILITY,
        }
        if not isinstance(available, list) or not required.issubset(set(available)):
            raise Stage10PlayerSubjectError(
                "required_capability_unavailable",
                {
                    **state,
                    "required_capabilities": sorted(required),
                    "bridge_capabilities": available,
                },
            )

        initial = service.snapshot()
        initial_binding = _binding(initial)
        if initial_binding["player_character_id"] != manager:
            raise ValueError("loaded player differs from the contracted manager")
        campaign = service.query_campaign_root_context_v1(
            expected_revision=int(initial["revision"])
        )
        campaign = _campaign_source(
            campaign, expected_player=manager, expected_owner=owner
        )
        state["source_binding"] = initial_binding
        state["source_campaign_root"] = campaign

        current = service.snapshot()
        if _binding(current) != initial_binding:
            raise ValueError("player-manager source changed during qualification")
        state["source_checkpoint"] = _save(
            service, current, "player-manager source"
        )

        if resume_progress is None:
            progress: dict[str, object] = {
                "timeline_origin_date_raw": initial_binding["date_raw"],
                "absolute_end_date_raw": initial_binding["date_raw"]
                + MAX_ADVANCE_DAYS * 24,
                "timeline_interrupt_drains": [],
            }
        else:
            progress = copy.deepcopy(dict(resume_progress))
            origin = progress.get("timeline_origin_date_raw")
            deadline = progress.get("absolute_end_date_raw")
            drains = progress.get("timeline_interrupt_drains")
            unexpected = progress.get("unexpected_event")
            target = progress.get("target_binding")
            unexpected_key = (
                unexpected.get("event_definition_key")
                if isinstance(unexpected, Mapping)
                else None
            )
            retained_target = (
                progress.get("readiness") == "paused-real-zg361mg.120"
                and isinstance(target, Mapping)
                and isinstance(target.get("event_instance_id"), int)
                and not isinstance(target.get("event_instance_id"), bool)
                and target.get("event_instance_id") > 0
            )
            if not (
                isinstance(origin, int)
                and not isinstance(origin, bool)
                and isinstance(deadline, int)
                and not isinstance(deadline, bool)
                and origin <= initial_binding["date_raw"] <= deadline
                and deadline == origin + MAX_ADVANCE_DAYS * 24
                and isinstance(drains, list)
                and (isinstance(unexpected_key, str) or retained_target)
            ):
                raise ValueError("Stage 10 resume progress is not a retained bounded RED")
            progress["contract_resume"] = {
                "same_process_required": True,
                "resume_boundary": (
                    "unexpected_event"
                    if isinstance(unexpected_key, str)
                    else "target_event"
                ),
                "resume_date_raw": initial_binding["date_raw"],
                "retained_timeline_origin_date_raw": origin,
                "retained_absolute_end_date_raw": deadline,
                "retained_interrupt_drain_count": len(drains),
                "retained_event_definition_key": (
                    unexpected_key if isinstance(unexpected_key, str) else STAGE10_EVENT
                ),
            }
        state["progress"] = progress
        _write(path, state)
        navigation = navigator(
            service,
            timeout_seconds=ENTRY_TIMEOUT_SECONDS,
            progress_sample_interval_days=PROGRESS_SAMPLE_DAYS,
            prefer_natural_cycle=False,
            pause_on_event_definition_key=STAGE10_EVENT,
            evidence_out=progress,
        )
        state["navigation"] = copy.deepcopy(dict(navigation))
        terminal_snapshot = service.snapshot()
        terminal_binding = _binding(terminal_snapshot)
        if (
            terminal_binding["bridge_pid"] != initial_binding["bridge_pid"]
            or terminal_binding["connection_generation"]
            != initial_binding["connection_generation"]
            or terminal_binding["player_character_id"] != manager
            or terminal_binding["date_raw"] > progress["absolute_end_date_raw"]
        ):
            raise ValueError("Stage 10 navigation left its bounded player-manager lineage")
        context = _event_context(
            service, terminal_snapshot, expected_definition=STAGE10_EVENT
        )
        if _scope_character_id(context.get("root_scope"), "Stage 10 root") != manager:
            raise ValueError("Stage 10 event root is not the played manager")
        event_owner = _saved_character_id(context, "zg361_mg_f_ticket_owner")
        event_subject = _saved_character_id(context, "zg361_mg_f_ticket_subject")
        if event_owner != owner or event_subject != manager:
            raise ValueError("Stage 10 event left the contracted owner/manager case")

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
            "role_topology": "superior_owner_to_player_manager_subject",
            "source_trigger": "real_player_b1_publication",
            "provider_observation": provider,
            "action_ack_is_business_postcondition": False,
        }
        state["p1_acceptance_evidence"] = {"central_stage_10_terminal": gate}
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
    "STAGE10_EVENT",
    "Stage10PlayerSubjectError",
    "run_stage10_player_subject",
]
