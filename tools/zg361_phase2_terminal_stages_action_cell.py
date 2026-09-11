#!/usr/bin/env python3
"""Resume the played Central owner's P1 stages 9 and 11.

The caller owns seed migration/admission, CK3 and its cleanup. This module
keeps completed stage receipts and the canonical timeline's progress across
Python retries. AF5 is assembled independently and is never required here.
The player-visible Stage 10 ``zg361mg.120`` result belongs to the opposite
role topology (the player is an AI Central owner's manager subject), so its
receipt must be collected independently and is never awaited on this route.
Stage 11 uses the owner-view Workforce provider before acting and after the
Central callback. Legitimate N/A closes need no M360 event. The module never
changes the played character to obtain an observation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "ck3_autonomous_player/src") not in sys.path:
    sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))

import zg361_phase2_promotion_source_production_entry as entry  # noqa: E402
from xar_autoplayer.bridge.driver import BridgeUnavailableError  # noqa: E402
from zhongguo_phase2_workforce_action import (  # noqa: E402
    _event_context,
    _saved_character_id,
    _scope_character_id,
    submit_m360_route_action,
)

EVENTS = {9: "zg361cl.390", 11: "zg361we.360"}
INDEPENDENT_STAGE10_EVENT = "zg361mg.120"
# R406 showed that daily paused-frame native progress reads can consume the
# whole five-minute wall-clock window while only eleven healthy product days
# elapse.  Terminal navigation samples the unchanged observer once per product
# month and retains the existing finite absolute game-date horizon.  After the
# one allowed M360 action, daily reads resume so its Central callback is caught
# at the first durable terminal frame.
ENTRY_TIMEOUT_SECONDS = 1800.0
NAVIGATION_PROGRESS_SAMPLE_DAYS = 30
POST_M360_PROGRESS_SAMPLE_DAYS = 1
STAGE10_SOURCE_KIND = "zg361_stage10_player_subject_source_v1"
MAX_CONSECUTIVE_WORKFORCE_QUERY_REBINDS = 4
_TRANSIENT_WORKFORCE_QUERY_BINDING_ERRORS = (
    "ZhongGuo Workforce owner query lacks one stable paused player binding",
    "ZhongGuo workforce owner revision is stale",
    "ZhongGuo workforce owner snapshot changed or is not ready",
    "ZhongGuo Workforce owner backend result is not bound to the requested paused frame",
    "ZhongGuo Workforce owner query crossed its paused snapshot binding",
)


class TerminalStagesError(RuntimeError):
    def __init__(self, reason: str, evidence: Mapping[str, object]):
        self.evidence = copy.deepcopy(dict(evidence))
        super().__init__(reason)


def _write(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _archive_checkpoint(
    save_result: object, destination: Path
) -> dict[str, object]:
    result = save_result if isinstance(save_result, Mapping) else {}
    checkpoint = result.get("checkpoint")
    checkpoint = checkpoint if isinstance(checkpoint, Mapping) else {}
    raw_path = checkpoint.get("path")
    expected_size = checkpoint.get("size")
    expected_sha = checkpoint.get("sha256")
    if not (
        result.get("accepted") is True
        and checkpoint.get("status") == "saved"
        and isinstance(raw_path, str)
        and Path(raw_path).is_absolute()
        and isinstance(expected_size, int)
        and not isinstance(expected_size, bool)
        and expected_size > 0
        and isinstance(expected_sha, str)
        and re.fullmatch(r"[0-9A-Fa-f]{64}", expected_sha) is not None
    ):
        raise ValueError("Stage 10 source save lacks materialized size/hash proof")
    source = Path(raw_path).resolve()
    if not source.is_file():
        raise ValueError("Stage 10 source save is not materialized")
    digest = _sha256(source)
    if source.stat().st_size != expected_size or digest != expected_sha.upper():
        raise ValueError("Stage 10 source save differs from its native receipt")
    target = destination.resolve()
    if target.exists():
        target_digest = _sha256(target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        target_digest = _sha256(target)
    if target.stat().st_size != expected_size or target_digest != digest:
        raise ValueError("Stage 10 source archive already exists with different bytes")
    return {"path": str(target), "bytes": expected_size, "sha256": digest}


def _binding(snapshot: Mapping[str, object]) -> dict[str, int]:
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("terminal stages require a paused map-ready session")
    diagnostics = snapshot["diagnostics"]
    played = snapshot["played_character"]
    result = {
        "bridge_pid": diagnostics["bridge_pid"],
        "connection_generation": diagnostics["connection_generation"],
        "player_character_id": played["character_id"],
    }
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in result.values()):
        raise ValueError("terminal stages lack a native session/player identity")
    return result


def _typed(group: object, key: str) -> object:
    value = group.get(key) if isinstance(group, Mapping) else None
    if not isinstance(value, Mapping) or value.get("status") != "available":
        raise ValueError(f"terminal field {key} is not observed")
    return value.get("value")


def _stage11_terminal(response: Mapping[str, object]) -> str | None:
    """Native Workforce closure and Central's real callback must both exist."""
    if response.get("status") != "available" or response.get("readiness", {}).get("ready") is not True:
        return None
    if response.get("terminal") is not True:
        return None
    kind = response.get("terminal_kind")
    expected_status = {"success": 2, "history_accruing": 2, "not_applicable": 3}.get(kind)
    if expected_status is None:
        raise ValueError("Workforce terminal lacks an authored terminal kind")
    central = response.get("workforce", {}).get("central")
    if _typed(central, "stage11_status") != expected_status:
        return None
    return "terminal_na" if kind == "not_applicable" else "closed"


def _ack_summary(service: object, context: Mapping[str, object]) -> dict[str, object]:
    """Acknowledge the reviewed single-option summary, then read a new snapshot."""
    options = context.get("options")
    if not isinstance(options, list) or len(options) != 1 or not (
        options[0].get("native_option_index") == 0
        and options[0].get("shown") is True and options[0].get("enabled") is True
    ):
        raise ValueError("terminal summary no longer has its sole authored acknowledgement")
    before = service.snapshot()
    event_id = context["current_event_instance_id"]
    active = before.get("active_event")
    if not isinstance(active, Mapping) or active.get("instance_id") != event_id:
        raise ValueError("terminal summary changed before acknowledgement")
    ack = service.select_event_option(
        1, event_instance_id=event_id, expected_revision=before["revision"]
    )
    after = service.snapshot()
    active = after.get("active_event")
    if ack.get("accepted") is not True or (
        isinstance(active, Mapping) and active.get("instance_id") == event_id
    ) or _binding(after) != _binding(before) or after["date_raw"] != before["date_raw"]:
        raise ValueError("native snapshot did not verify terminal summary acknowledgement")
    return {"ack": ack, "before_snapshot": before, "after_snapshot": after,
            "old_event_instance_removed": True, "action_ack_is_business_postcondition": False}


def run_terminal_stages(
    service: object, *, evidence_directory: Path, request_nonce: str,
    max_advance_days: int | None = None, start_stage: int = 9,
) -> dict[str, object]:
    """Collect stage gate rows; resume this directory on the same live binding.

    Each navigation attempt uses a bounded thirty-minute entry window. The
    persisted product-date horizon and progress survive an entry timeout.
    No method in this function launches, stops or loads CK3.
    """
    if not isinstance(request_nonce, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,55}", request_nonce) is None:
        raise ValueError("request_nonce must be a nonempty ASCII token of at most 56 characters")
    if isinstance(start_stage, bool) or start_stage not in (9, 11):
        raise ValueError("start_stage must be 9 or 11")
    configured_max_advance_days = (
        entry.MAX_ADVANCE_DAYS if max_advance_days is None else max_advance_days
    )
    if (
        isinstance(configured_max_advance_days, bool)
        or not isinstance(configured_max_advance_days, int)
        or configured_max_advance_days <= 0
    ):
        raise ValueError("max_advance_days must be a positive integer")
    directory = Path(evidence_directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "terminal-stages.json"
    initial = service.snapshot()
    binding = _binding(initial)
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["binding"] != binding or state["request_nonce"] != request_nonce:
            raise ValueError("terminal stages retry belongs to a different session or request")
        persisted_max_advance_days = state.get("configured_max_advance_days")
        if persisted_max_advance_days is None:
            persisted_max_advance_days = (
                state["progress_out"]["absolute_end_date_raw"]
                - state["progress_out"]["timeline_origin_date_raw"]
            ) // 24
        if persisted_max_advance_days != configured_max_advance_days:
            raise ValueError("terminal stages retry changed its game-day bound")
        if state.get("configured_start_stage", 9) != start_stage:
            raise ValueError("terminal stages retry changed its starting stage")
        if state["result"] == "GREEN":
            return state
    else:
        owned_stage_sequence = [9, 11] if start_stage == 9 else [11]
        state = {
            "schema_version": 1, "kind": "zg361_phase2_terminal_stages_action_cell",
            "result": "RED", "mcp_only": True, "binding": binding,
            "request_nonce": request_nonce, "attempt": 0, "current_stage": None,
            "failure_reason": None, "stage_observations": {},
            "configured_max_advance_days": configured_max_advance_days,
            "configured_start_stage": start_stage,
            "p1_acceptance_evidence": {"central_stage_terminals": {}},
            "progress_out": {
                "timeline_origin_date_raw": initial["date_raw"],
                "absolute_end_date_raw": (
                    initial["date_raw"] + configured_max_advance_days * 24
                ),
                "timeline_interrupt_drains": [],
            },
            "owned_stage_sequence": owned_stage_sequence,
            "independent_stage10_required": start_stage == 9,
            "independent_stage10_event_definition_key": INDEPENDENT_STAGE10_EVENT,
            "af5_same_slice_required": False, "action_ack_is_business_postcondition": False,
        }
    state["attempt"] += 1
    state["failure_reason"] = None
    progress = state["progress_out"]
    receipts = state["p1_acceptance_evidence"]["central_stage_terminals"]
    _write(path, state)

    def snapshot() -> dict[str, object]:
        value = service.snapshot()
        if _binding(value) != binding:
            raise ValueError("terminal continuation left its admitted session/player")
        return value

    def navigate(stage: int, *, terminal_probe=None) -> dict[str, object] | None:
        try:
            navigation = entry.enter_promotion_source_checkpoint_v1(
                service, timeout_seconds=ENTRY_TIMEOUT_SECONDS,
                progress_sample_interval_days=(
                    POST_M360_PROGRESS_SAMPLE_DAYS
                    if stage == 11 and state.get("stage11_action") is not None
                    else NAVIGATION_PROGRESS_SAMPLE_DAYS
                ),
                prefer_natural_cycle=True, pause_on_event_definition_key=EVENTS[stage],
                evidence_out=progress, terminal_observation_probe=terminal_probe,
            )
        finally:
            _write(path, state)
        current = snapshot()
        if isinstance(navigation.get("terminal_observation"), Mapping):
            state["stage_observations"][str(stage)] = {
                "snapshot": current, "provider": navigation["terminal_observation"],
                "event_required": False,
            }
            _write(path, state)
            return None
        context = _event_context(service, current, expected_definition=EVENTS[stage])
        state["stage_observations"][str(stage)] = {"snapshot": current, "event_context": context}
        _write(path, state)
        return context

    def observe_workforce(current: Mapping[str, object]) -> Mapping[str, object] | None:
        if _binding(current) != binding:
            raise ValueError("Workforce observation left the admitted played owner")
        query = getattr(service, "query_zhongguo_workforce_owner_snapshot_v1", None)
        if not callable(query):
            return None
        try:
            provider = query(
                request_nonce + ".11", expected_revision=current["revision"]
            )
        except BridgeUnavailableError as error:
            if not any(
                marker in str(error)
                for marker in _TRANSIENT_WORKFORCE_QUERY_BINDING_ERRORS
            ):
                raise
            consecutive = int(
                state.get("stage11_consecutive_query_rebinds", 0)
            ) + 1
            state["stage11_consecutive_query_rebinds"] = consecutive
            rebinds = state.setdefault("stage11_query_rebinds", [])
            if not isinstance(rebinds, list):
                raise ValueError("persisted Stage 11 query rebind audit is malformed")
            rebinds.append(
                {
                    "attempt": consecutive,
                    "stale_revision": current.get("revision"),
                    "date_raw": current.get("date_raw"),
                    "error": f"{type(error).__name__}: {error}",
                    "state_mutation_submitted": False,
                }
            )
            _write(path, state)
            if consecutive >= MAX_CONSECUTIVE_WORKFORCE_QUERY_REBINDS:
                raise
            # The production entry driver immediately takes a fresh snapshot
            # after a terminal probe returns None. This is a read-only rebind;
            # no gameplay input or CK3 restart is needed.
            return None
        state["stage11_consecutive_query_rebinds"] = 0
        state["stage11_latest_provider"] = provider
        _write(path, state)
        if provider.get("status") != "available" or provider.get("readiness", {}).get("ready") is not True:
            return None
        if provider.get("player_character_id") != binding["player_character_id"]:
            raise ValueError("Workforce query does not observe the admitted owner")
        workforce = provider["workforce"]
        subject = _typed(workforce["central"], "subject_character_id")
        if subject != provider.get("subject_character_id"):
            raise ValueError("Workforce query subject differs from the product-owned subject")
        expected_case = state.get("stage11_case_binding")
        if isinstance(expected_case, Mapping) and any(
            _typed(workforce["al_case"], key) != value
            for key, value in expected_case.items()
        ):
            raise ValueError("Workforce readback left the selected AL case")
        if _stage11_terminal(provider) is not None:
            state["stage11_terminal_provider"] = provider
            return provider
        return None

    def receipt(stage: int, provider: Mapping[str, object], terminal: str, **extra: object) -> None:
        receipts[str(stage)] = {
            "result": "GREEN", "stage": stage, "event_definition_key": EVENTS[stage],
            "provider_domain": "workforce" if stage == 11 else "central",
            "terminal_state": terminal, "provider_observed": True,
            "terminal_postcondition_verified": True,
            "action_ack_is_business_postcondition": False,
            "provider_observation": copy.deepcopy(dict(provider)), **extra,
        }
        _write(path, state)

    def capture_stage10_source(context: Mapping[str, object]) -> dict[str, object]:
        current = snapshot()
        selector_method = getattr(
            service, "query_zhongguo_manager_subordinate_selector_v1", None
        )
        capture: dict[str, object] = {
            "schema_version": 1,
            "kind": STAGE10_SOURCE_KIND,
            "result": "INELIGIBLE",
            "source_event_definition_key": EVENTS[9],
            "source_event_instance_id": context["current_event_instance_id"],
            "owner_character_id": binding["player_character_id"],
            "player_character_id": binding["player_character_id"],
            "date_raw": current["date_raw"],
            "source_event_context": copy.deepcopy(dict(context)),
            "selector": None,
            "selection_attempted": False,
        }
        if not callable(selector_method):
            capture["reason"] = "manager_subordinate_selector_unavailable"
            return capture
        try:
            root_character_id = _scope_character_id(
                context.get("root_scope"), "Stage 9 root"
            )
        except Exception as error:
            capture["reason"] = (
                f"stage9_root_unavailable: {type(error).__name__}: {error}"
            )
            return capture
        if root_character_id != binding["player_character_id"]:
            capture["reason"] = "stage9_root_is_not_played_owner"
            return capture
        selector = selector_method(
            request_nonce + ".s10",
            expected_revision=current["revision"],
        )
        capture["selector"] = copy.deepcopy(selector)
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
            and isinstance(manager, int)
            and not isinstance(manager, bool)
            and manager > 0
            and manager != binding["player_character_id"]
        ):
            capture["reason"] = "eligible_stage10_manager_unavailable"
            return capture
        after_selector = snapshot()
        active = after_selector.get("active_event")
        if not (
            _binding(after_selector) == binding
            and after_selector.get("date_raw") == current.get("date_raw")
            and isinstance(active, Mapping)
            and active.get("instance_id") == context["current_event_instance_id"]
        ):
            raise ValueError("Stage 10 source frame changed during selector qualification")
        save_result = service.save_checkpoint(
            expected_revision=after_selector["revision"]
        )
        archived = _archive_checkpoint(
            save_result, directory / "stage10-player-subject-source.ck3"
        )
        capture.update(
            result="GREEN",
            reason=None,
            selected_manager_character_id=manager,
            save_result=copy.deepcopy(save_result),
            checkpoint=archived,
            provider_observed=True,
        )
        _write(directory / "stage10-player-subject-source.json", capture)
        return capture

    try:
        if start_stage == 9 and "9" not in receipts:
            state["current_stage"] = 9
            context = navigate(9)
            if "stage10_source" not in state:
                state["stage10_source"] = capture_stage10_source(context)
                _write(path, state)
            # .390 is the product's completed career/learning portfolio digest;
            # its single option only removes zg361_cl_digest_pending.
            acknowledgement = _ack_summary(service, context)
            receipt(9, context, "complete", acknowledgement=acknowledgement)
        if "11" not in receipts:
            state["current_stage"] = 11
            context = navigate(11, terminal_probe=observe_workforce)
            if context is not None:
                if state.get("stage11_action") is not None:
                    raise ValueError("M360 was already submitted; native terminal has not been observed")
                owner = _saved_character_id(context, "zg361_we_al_owner")
                subject = _saved_character_id(context, "zg361_we_al_subject")
                if owner != binding["player_character_id"]:
                    raise ValueError("M360 owner is not the admitted played character")
                current = snapshot()
                state["stage11_park"] = {
                    "event_definition_key": EVENTS[11],
                    "event_instance_id": context["current_event_instance_id"],
                    "owner_character_id": owner, "subject_character_id": subject,
                    "snapshot": current, "selection_attempted": False,
                    "checkpoint": service.save_checkpoint(expected_revision=current["revision"]),
                }
                saved = state["stage11_park"]["checkpoint"]
                if saved.get("accepted") is not True or saved.get("checkpoint", {}).get("status") != "saved":
                    raise ValueError("Stage 11 parked checkpoint was not saved")
                observe_workforce(snapshot())
                provider = state.get("stage11_latest_provider", {})
                if provider.get("status") != "available" or provider.get("readiness", {}).get("ready") is not True:
                    state["missing_observation"] = {
                        "role": "owner_view_workforce_terminal",
                        "required_capability": "game.command.query-zhongguo-workforce-owner-snapshot-v1",
                        "existing_provider_constraint": "AL subject must be the played character",
                        "required_owner_character_id": owner, "required_subject_character_id": subject,
                        "subject_source_variable": "zg361_p2c_subject",
                        "player_switch_attempted": False,
                    }
                    raise ValueError("Stage 11 parked before M360: owner-view Workforce terminal observation is missing")
                workforce = provider["workforce"]
                al_case, source = workforce["al_case"], workforce["source"]
                if provider.get("terminal") is True or provider.get("subject_character_id") != subject or (
                    _typed(al_case, "state") != 4 or _typed(al_case, "active") is not True
                    or _typed(source, "status") != 1
                    or _typed(source, "owner_character_id") != owner
                    or _typed(source, "subject_character_id") != subject
                ):
                    raise ValueError("M360 independent prestate does not match the displayed owner/subject case")
                state["stage11_case_binding"] = {
                    key: _typed(al_case, key) for key in (
                        "owner_character_id", "subject_character_id", "cycle_serial", "case_serial",
                    )
                }
                state["stage11_pre_action_provider"] = copy.deepcopy(provider)
                state.pop("missing_observation", None)
                _write(path, state)
                # The existing canonical Workforce route is A: native option 0.
                # This helper claims submission only; owner readback below owns
                # the business terminal and the delayed Central callback.
                state["stage11_action"] = submit_m360_route_action(
                    service, route="A", evidence_path=directory / "stage11-m360-action.json",
                )
                state["stage11_park"]["selection_attempted"] = True
                _write(path, state)
                context = navigate(11, terminal_probe=observe_workforce)
                if context is not None:
                    raise ValueError("M360 was submitted but returned before its independent terminal")
            provider = state["stage11_terminal_provider"]
            terminal = _stage11_terminal(provider)
            if terminal is None:
                raise ValueError("Stage 11 has not reached its Workforce/Central terminal")
            receipt(11, provider, terminal, terminal_kind=provider["terminal_kind"],
                    m360_action=state.get("stage11_action"), player_switch_attempted=False)
        current = snapshot()
        state["terminal_snapshot"] = current
        state["save_result"] = service.save_checkpoint(expected_revision=current["revision"])
        checkpoint = state["save_result"].get("checkpoint", {})
        if state["save_result"].get("accepted") is not True or checkpoint.get("status") != "saved":
            raise ValueError("terminal checkpoint was not saved")
        state["result"] = "GREEN"
        state["current_stage"] = None
        return state
    except Exception as error:
        state["result"] = "RED"
        state["failure_reason"] = f"{type(error).__name__}: {error}"
        if isinstance(getattr(error, "evidence", None), Mapping):
            state["failure_evidence"] = copy.deepcopy(error.evidence)
        raise TerminalStagesError(str(error), state) from error
    finally:
        _write(path, state)
        _write(directory / f"attempt-{state['attempt']:03d}.json", state)
