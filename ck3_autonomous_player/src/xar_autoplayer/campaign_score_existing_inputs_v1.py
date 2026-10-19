"""Pure monthly mapping of already obtained cash/root DTOs; no query or cache.

The caller supplies the existing planning-source-frame captured with each
ordinary query. An AUTO's old input cannot become an after-MET observation.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal

from .campaign_development_score_v1 import UNITS
from .bridge.driver import BridgeUnavailableError
from .bridge.nonwar_private_build import private_native_build_identity
from .bridge.turn_bundle_contract import build_turn_bundle_v1
from .bridge.version_identity import require_exact_native_build
from .bridge.war_cash_private_transport_v1 import normalize_war_cash_current_resources_v1

_CASH_FIELDS = (
    ("gross_income", "player_monthly_gross_income", "monthly_gross_income_ready"),
    ("total_expenses", "player_monthly_total_expenses", "monthly_total_expenses_ready"),
    ("military_current", "current", "current_military_expenses_ready"),
    ("military_all_raised", "all_raised", "all_raised_military_expenses_ready"),
)


def _unknown(name, reason):
    return {"value": None, "unit": UNITS[name], "availability": "unknown",
            "source_ref": None, "reason_zh": reason}


def _frame_reason(snapshot, source):
    """Check the existing planning-source-frame/v1, without inventing an identity."""
    if not isinstance(source, Mapping):
        return "existing_planning_source_frame_missing"
    if source.get("schema") != "xar.ck3.planning-source-frame/v1" or source.get("status") != "complete":
        return "existing_planning_source_frame_incomplete"
    played, diag = snapshot.get("played_character"), snapshot.get("diagnostics")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(played, Mapping) or played.get("alive") is not True
            or not isinstance(diag, Mapping)):
        return "current_paused_player_frame_unavailable"
    for key in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"):
        if source.get(key) is None or source[key] != snapshot.get(key):
            return "existing_planning_source_frame_changed:" + key
    if source.get("actor_character_id") != played.get("character_id"):
        return "existing_planning_source_frame_changed:actor_character_id"
    for key in ("bridge_pid", "connection_generation"):
        if (type(source.get(key)) is not int or source[key] < (1 if key == "bridge_pid" else 0)
                or source[key] != diag.get(key)):
            return "existing_planning_source_frame_changed:" + key
    return None


def _cash_metrics(snapshot, packet):
    cash = normalize_war_cash_current_resources_v1(packet, snapshot=snapshot)
    if cash.get("monthly_income_semantics") is None:
        raise ValueError("cash_v2_monthly_semantics_missing")
    if cash["readiness"].get("same_frame_ready") is not True:
        raise ValueError("cash_same_frame_unavailable")
    for key, expected in (("queried_snapshot_id", "snapshot_id"),
                          ("queried_revision", "revision"),
                          ("queried_native_revision", "native_revision")):
        if cash.get(key) != snapshot.get(expected):
            raise ValueError("cash_query_binding_changed:" + key)
    wars = snapshot.get("active_wars")
    if (not isinstance(wars, list) or any(not isinstance(row, Mapping) for row in wars)
            or sorted(cash["active_war_ids"]) != sorted(row.get("war_id") for row in wars)):
        raise ValueError("cash_player_war_scope_changed")
    wallet, treasury = snapshot.get("played_character_gold"), cash.get("current_treasury")
    if (isinstance(wallet, Mapping) and isinstance(treasury, Mapping)
            and wallet != treasury):
        raise ValueError("cash_and_ordinary_wallet_disagree")
    metrics = {}
    for name, key, ready in _CASH_FIELDS:
        fixed = cash.get(key) if key not in {"current", "all_raised"} else None
        row = cash["military_expenses"].get(key) if key in {"current", "all_raised"} else None
        raw = fixed.get("raw") if isinstance(fixed, Mapping) else (
            row.get("gold_raw") if isinstance(row, Mapping) and row.get("status") == "available" else None)
        if row is not None and (row.get("resource_kind") != "actor_military_" + key + "_maintenance"
                or type(row.get("raw_scale")) is not int):
            raw = None
        if cash["readiness"].get(ready) is not True or type(raw) is not int or raw < 0:
            metrics[name] = _unknown(name, "cash_v2_component_unavailable:" + key)
        else:
            metrics[name] = {"value": format(Decimal(raw) / Decimal(100_000), "f"),
                "unit": UNITS[name], "availability": "observed", "source_ref": "existing_cash_v2",
                "locator": key if row is None else "military_expenses." + key + ".gold_raw",
                "scope": "played_character_personal_gold" if row is None else "actor_owned_military_once_across_all_wars"}
    total, military = metrics["total_expenses"], metrics["military_current"]
    if (total["availability"] == military["availability"] == "observed"
            and Decimal(military["value"]) > Decimal(total["value"])):
        metrics["military_current"] = _unknown("military_current", "cash_military_exceeds_compatible_total_expenses")
    return metrics, {"monthly_income_semantics": deepcopy(cash["monthly_income_semantics"]),
                     "game_version": cash["game_version"], "executable_sha256": cash["executable_sha256"]}


def _realm_diagnostics(snapshot, result):
    root = result.get("campaign_root_context") if isinstance(result, dict) else None
    provenance = root.get("provenance") if isinstance(root, dict) else None
    if not isinstance(provenance, Mapping) or require_exact_native_build(
            provenance.get("game_version"), provenance.get("executable_sha256")) != private_native_build_identity(snapshot):
        raise ValueError("campaign_root_exact_build_unavailable")
    bundle = build_turn_bundle_v1(snapshot, result)
    component = bundle["realm_state"]
    if component["status"] != "available":
        raise ValueError("campaign_root_unavailable:" + str(component["unavailable_reason"]))
    realm = component["value"]
    return {"status": "available", "domain": deepcopy(realm["domain"]),
            "territory": deepcopy(realm["territory"]),
            "full_realm_scoring_input_available": False}


def project_existing_month_inputs_v1(
    snapshot: Mapping, *, cash_packet=None, cash_source_frame=None,
    campaign_root_result=None, root_source_frame=None,
) -> dict:
    """Return four typed metric rows and realm diagnostics for the same MET frame.

    This consumes public cash-v2 and campaign-root result shapes already in the
    SDK. It neither searches history nor reads a Driver cache. Absent original
    planning-source-frame provenance stays unknown; no frame is manufactured.
    The runtime owner may merge raw_metrics into its existing exact-slot
    candidate and append sources only when it already holds these inputs.
    """
    result = {"schema": "xar.ck3.campaign-score-existing-inputs/v1",
        "raw_metrics": {name: _unknown(name, "existing_cash_DTO_not_obtained") for name, _, _ in _CASH_FIELDS},
        "realm_diagnostics": {"status": "unavailable", "unavailable_reason": "existing_campaign_root_DTO_not_obtained"},
        "sources": [], "input_gaps": {}, "new_RPC_calls": 0, "new_SAVE_exports": 0,
        "score_or_complete_history_claimed": False}
    for kind, payload, frame in (("cash", cash_packet, cash_source_frame),
                                  ("realm", campaign_root_result, root_source_frame)):
        if payload is None:
            result["input_gaps"][kind] = "existing_DTO_not_obtained"
            continue
        reason = _frame_reason(snapshot, frame)
        if reason is None:
            try:
                if kind == "cash":
                    result["raw_metrics"], source = _cash_metrics(snapshot, payload)
                else:
                    result["realm_diagnostics"] = _realm_diagnostics(snapshot, payload)
                    source = {"query_sequence": payload["query_sequence"]}
                result["sources"].append({"id": "existing_cash_v2" if kind == "cash" else "existing_campaign_root",
                    "kind": "already_obtained_ordinary_query", "binding": deepcopy(dict(frame)), **source})
            except (ValueError, TypeError, KeyError, BridgeUnavailableError) as error:
                reason = str(error)[:256]
        if reason is not None:
            result["input_gaps"][kind] = reason
            if kind == "cash":
                result["raw_metrics"] = {name: _unknown(name, reason) for name, _, _ in _CASH_FIELDS}
            else:
                result["realm_diagnostics"] = {"status": "unavailable", "unavailable_reason": reason}
    return result
