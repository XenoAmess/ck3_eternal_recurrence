"""Construction-only Clan scene; existing feudal LIFE and war scope unchanged."""
from __future__ import annotations

from collections.abc import Mapping

from .lifestyle_formal_consumer import ROOT_QUERY_STEP, _same_frame_feudal_scope


def same_frame_construction_scope_v1(
    snapshot: Mapping[str, object], history: list[dict[str, object]],
) -> dict[str, object]:
    """Delegate every existing feudal result and admit only an observed Clan.

    This identifies a scene, not action permission. The caller still needs
    exact .4 native final legality, gold-only quote and jointly observed cash-v2.
    No Government composite query, guessed feature or persisted profile is used.
    """
    original = _same_frame_feudal_scope(snapshot, history, require_peace=False)
    if original.get("status") != "outside_scene":
        return original
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, Mapping) else None
    for row in reversed(history):
        result = row.get("result")
        root = result.get("campaign_root_context") if isinstance(result, Mapping) else None
        if not (row.get("command") == ROOT_QUERY_STEP and row.get("ok") is True
                and isinstance(root, Mapping) and root.get("status") == "available"
                and root.get("snapshot_revision") == snapshot.get("native_revision")
                and root.get("date_raw") == snapshot.get("date_raw")
                and root.get("player_character_id") == actor):
            continue
        government = root.get("government")
        flags = government.get("flags") if isinstance(government, Mapping) else None
        if (isinstance(government, Mapping)
                and government.get("key") == "clan_government"
                and isinstance(flags, list) and "government_is_clan" in flags):
            return {
                "status": "admitted", "at_peace": not snapshot["active_wars"],
                "government_key": "clan_government",
                "snapshot_revision": snapshot["native_revision"],
                "player_character_id": actor,
            }
        return original
    return original


def clan_construction_cash_frame_reason_v1(
    snapshot: Mapping[str, object], observation: object,
) -> str | None:
    """Require observed current actor NET; quote projection checks arithmetic.

    NET means personal gold gross minus complete monthly expenses, including
    native tax obligations. It is not an attributed new-building return.
    """
    budget = (observation.get("current_cash_scenarios")
              if isinstance(observation, Mapping) else None)
    packet = budget.get("source_cash_resources") if isinstance(budget, Mapping) else None
    if not isinstance(packet, Mapping):
        return "current native cash-v2 is unavailable for this Clan spend"
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, Mapping) else None
    if not (packet.get("played_character_id") == actor
            and packet.get("snapshot_revision") == snapshot.get("native_revision")
            and packet.get("date_raw") == snapshot.get("date_raw")
            and packet.get("game_version") == "1.20.0.4"
            and packet.get("read_only") is True):
        return "Clan cash and construction scene belong to different actor frames"
    readiness = packet.get("readiness")
    if not (isinstance(readiness, Mapping)
            and all(readiness.get(flag) is True for flag in (
                "same_frame_ready", "current_treasury_ready",
                "monthly_gross_income_ready", "monthly_total_expenses_ready",
                "monthly_net_income_ready"))
            and isinstance(packet.get("monthly_income_semantics"), Mapping)):
        return "current native Clan NET or treasury is not observed"
    return None
