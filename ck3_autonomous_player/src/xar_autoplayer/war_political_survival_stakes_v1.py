"""Source-reviewed rebel-defeat exposure, separate from title targeting."""
from __future__ import annotations

from collections.abc import Mapping

from .bridge.version_identity import CK3_12004
from .m5_observed_opportunity_selector import observed_frame

PROFILE = "refused-liege-demand-primary-rebel-political-survival-v1"
CB_KEY = "refused_liege_demand_war"
SOURCE_CONTRACT = {
    "common/casus_belli_types/00_civil_war.txt":
        "a9f5d844413bd7acfd4d4b1611877ac34e78eb293f309c0e7a41f27aca3a0047",
    "common/scripted_effects/00_war_effects.txt":
        "f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b",
    "common/opinion_modifiers/00_war_opinions.txt":
        "750864482d2d6c5d268424a1e03cba24301dedf853722d7fc12cb6f9fbcc68dc",
}


def _positive(value):
    return type(value) is int and value > 0


def political_survival_stakes_qualified_v1(value):
    if not (isinstance(value, Mapping) and value.get("status") == "available"
            and value.get("profile") == PROFILE and value.get("source_contract") == SOURCE_CONTRACT
            and value.get("player_role") == "primary_rebel_attacker"
            and value.get("game_version") == CK3_12004.game_version
            and all(_positive(value.get(key)) for key in
                    ("war_id", "connection_generation", "query_sequence", "defender_character_id"))
            and value.get("observed_liege_relation") in ("immediate_liege_character_id", "top_liege_character_id")
            and value.get("actual_penalty_verified") is False
            and value.get("automatic_title_transfer_verified") is False):
        return False
    cb, frame = value.get("active_casus_belli_identity"), value.get("source_frame")
    if (not isinstance(cb, Mapping) or cb.get("canonical_key") != CB_KEY
            or not _positive(cb.get("database_index")) or not isinstance(frame, Mapping)):
        return False
    try:
        return observed_frame(frame) == frame
    except (ValueError, TypeError):
        return False


def observe_political_survival_stakes_v1(snapshot, war, campaign_root):
    """Reuse exact-frame native CB and lieges; unknown inputs preserve policy."""
    def unavailable(reason):
        return {"status": "unavailable", "profile": PROFILE, "reason": reason}

    if not isinstance(snapshot, Mapping) or not isinstance(war, Mapping):
        return unavailable("current_snapshot_or_war_unavailable")
    try:
        frame = observed_frame(snapshot)
    except (ValueError, TypeError):
        return unavailable("current_frame_identity_unavailable")
    actor = frame["played_character_id"]
    player = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    connection = diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None
    if (snapshot.get("paused") is not True or not _positive(connection)
            or not isinstance(player, Mapping) or player.get("alive") is not True
            or war.get("player_side") != "attacker" or war.get("player_is_primary_war_leader") is not True
            or not _positive(war.get("war_id")) or type(war.get("player_relative_war_score")) is not int):
        return unavailable("current_primary_rebel_attacker_identity_unavailable")
    wars = snapshot.get("active_wars")
    matches = [row for row in wars if isinstance(row, Mapping) and row.get("war_id") == war["war_id"]] if isinstance(wars, list) else []
    if len(matches) != 1 or matches[0] != war:
        return unavailable("unique_current_active_war_unavailable")
    root = campaign_root
    if (not isinstance(root, Mapping) or root.get("status") != "available"
            or not _positive(root.get("player_character_id")) or root.get("player_character_id") != actor
            or root.get("player_character_alive") is not True
            or not _positive(root.get("snapshot_revision")) or root.get("snapshot_revision") != frame["native_revision"]
            or type(root.get("date_raw")) is not int or root.get("date_raw") != frame["date_raw"]
            or root.get("independent") is not False):
        return unavailable("same_frame_living_vassal_root_unavailable")
    provenance, readiness = root.get("provenance"), root.get("readiness")
    if (not isinstance(provenance, Mapping)
            or provenance.get("game_version") != CK3_12004.game_version
            or provenance.get("executable_sha256") != CK3_12004.executable_sha256
            or provenance.get("backend_id") != CK3_12004.backend_id("campaign-root-context-v1")
            or not isinstance(readiness, Mapping) or readiness.get("lieges_ready") is not True):
        return unavailable("reviewed_exact_build_or_native_lieges_unavailable")
    opponent = war.get("primary_opponent_character_id")
    relation = next((key for key in ("immediate_liege_character_id", "top_liege_character_id")
                     if _positive(opponent) and opponent != actor and _positive(root.get(key)) and root.get(key) == opponent), None)
    if relation is None:
        return unavailable("defender_not_observed_in_current_player_liege_chain")
    rows = snapshot.get("war_termination_options")
    rows = [row for row in rows if isinstance(row, Mapping) and row.get("war_id") == war["war_id"]] if isinstance(rows, list) else []
    if len(rows) != 1:
        return unavailable("unique_same_frame_cb_query_unavailable")
    options = rows[0]
    if (options.get("source") != "native" or not _positive(options.get("query_sequence"))
            or any(not _positive(options.get(key)) for key in
                   ("queried_revision", "queried_native_revision", "queried_connection_generation"))
            or options.get("queried_snapshot_id") != frame["snapshot_id"]
            or options.get("queried_revision") != frame["revision"]
            or options.get("queried_native_revision") != frame["native_revision"]
            or options.get("episode_run_id") != frame["episode_run_id"]
            or options.get("queried_connection_generation") != connection
            or options.get("player_side") != "attacker" or options.get("player_is_primary_war_leader") is not True
            or type(options.get("player_relative_war_score")) is not int
            or options.get("player_relative_war_score") != war["player_relative_war_score"]
            or options.get("active_casus_belli_present") is not True):
        return unavailable("cb_query_not_bound_to_current_primary_attacker_frame")
    cb = options.get("active_casus_belli_identity")
    outcomes = options.get("options")
    surrender = outcomes.get("surrender") if isinstance(outcomes, Mapping) else None
    if (not isinstance(cb, Mapping) or cb.get("canonical_key") != CB_KEY
            or not _positive(cb.get("database_index")) or not isinstance(surrender, Mapping)
            or surrender.get("outcome") != "attacker_defeat"):
        return unavailable("reviewed_refused_demand_cb_or_attacker_defeat_identity_unavailable")
    return {
        "status": "available", "profile": PROFILE, "player_role": "primary_rebel_attacker",
        "war_id": war["war_id"], "source_frame": frame, "connection_generation": connection,
        "query_sequence": options["query_sequence"], "active_casus_belli_identity": dict(cb),
        "defender_character_id": opponent, "observed_liege_relation": relation,
        "game_version": CK3_12004.game_version, "source_contract": dict(SOURCE_CONTRACT),
        "exposure": ["conditional_imprisonment", "liege_revoke_imprison_banish_execute_reasons"],
        "actual_penalty_verified": False, "automatic_title_transfer_verified": False,
        "reason": "source_reviewed_rebel_defeat_political_exposure_with_current_native_cb_and_liege_roles",
    }
