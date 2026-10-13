"""Bounded current4 war-exit observations, without a settlement prediction.

This pure consumer performs no queries or actions. Requested outcome, observed
WarID absence and an independently observed result identity are separate facts.
The current native interfaces supply no independent result identity here.
"""
from __future__ import annotations

from copy import deepcopy

from .bridge.player_claims_contract import (
    PLAYER_CLAIMS_V1_EXE_SHA256,
    normalize_player_claims_v1,
    player_claims_title_ids,
    query_player_claims_v1_step,
)
from .bridge.player_truce_expiry_contract import normalize_player_truce_expiry_v1
from .bridge.title_holder_contract import (
    normalize_title_holder_v1,
    query_title_holder_v1_step,
)

SCHEMA = "xar.ck3.ordinary-war-exit-observation.v1"
RESULT_KEY = "ordinary_war_exit_observation_v1"
# This is only a receipt-size bound; it changes no game or query selection.
MAXIMUM_OBSERVED_TITLES = 32
_PREFIXES = {
    "enforce-demands-": "player_victory",
    "offer-white-peace-": "white_peace",
    "surrender-war-": "player_defeat",
}


def _integer(value: object, *, minimum: int = 0, maximum: int = 2**31 - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("full integer identity unavailable")
    return value


def _frame(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("snapshot unavailable")
    diagnostics = value.get("diagnostics")
    played = value.get("played_character")
    if (value.get("paused") is not True or value.get("map_ready") is not True
            or not isinstance(played, dict) or played.get("alive") is not True
            or not isinstance(diagnostics, dict)):
        raise ValueError("living paused map frame unavailable")
    hello = diagnostics.get("hello")
    if not isinstance(hello, dict):
        raise ValueError("native build provenance unavailable")
    version = hello.get("expected_ck3_version", hello.get("game_version"))
    sha = hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
    if (version != "1.20.0.4" or not isinstance(sha, str)
            or sha.upper() != PLAYER_CLAIMS_V1_EXE_SHA256):
        raise ValueError("current4 build provenance unavailable")
    for field in ("snapshot_id", "episode_run_id"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise ValueError("snapshot/episode identity unavailable")
    return {
        "snapshot_id": value["snapshot_id"],
        "revision": _integer(value.get("revision"), minimum=1, maximum=2**64 - 1),
        "native_revision": _integer(value.get("native_revision"), minimum=1, maximum=2**64 - 1),
        "date_raw": _integer(value.get("date_raw"), minimum=-(2**31)),
        "episode_run_id": value["episode_run_id"],
        "actor_character_id": _integer(played.get("character_id")),
        "bridge_pid": _integer(diagnostics.get("bridge_pid"), minimum=1),
        "connection_generation": _integer(diagnostics.get("connection_generation"), minimum=1),
    }


def _wars(snapshot: dict[str, object]) -> list[dict[str, object]]:
    rows = snapshot.get("active_wars")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("active-war observation unavailable")
    ids = [_integer(row.get("war_id"), minimum=1) for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("active-war observation duplicated")
    return rows


def _fixed(value: object) -> dict[str, int] | None:
    if (not isinstance(value, dict) or type(value.get("raw")) is not int
            or not -(2**63) <= value["raw"] < 2**63 or value.get("scale") != 100_000
            or type(value.get("scale")) is not int):
        return None
    return {"raw": value["raw"], "scale": 100_000}


def _query_envelope(result: object, frame: dict[str, object], step: str) -> dict[str, object]:
    if (not isinstance(result, dict) or result.get("step") != step
            or result.get("accepted") is not True or result.get("read_only") is not True
            or result.get("backend_id") != "native-headless"):
        raise ValueError("typed read-only envelope unavailable")
    _integer(result.get("query_sequence"), minimum=1, maximum=2**64 - 1)
    # Consume the Service/Driver query binding, rather than a caller's label.
    for key, field in (("queried_snapshot_id", "snapshot_id"),
                       ("queried_revision", "revision"),
                       ("queried_native_revision", "native_revision")):
        if type(result.get(key)) is not type(frame[field]) or result[key] != frame[field]:
            raise ValueError("typed query differs from post frame")
    return result


def compose_ordinary_war_exit_observation_v1(
    *, before_snapshot: object, post_snapshot: object, action_result: object,
    claims_result: object = None, title_holder_results: object = None,
    truce_result: object = None,
) -> dict[str, object] | None:
    """Compose observations; unavailable evidence never blocks an action.

Optional queries must be existing Service/Driver results from the supplied
post frame. At most32 frozen targets are rendered, with omitted count explicit.
No requested outcome, ACK or material observation supplies result identity.
"""
    step = action_result.get("step") if isinstance(action_result, dict) else None
    requested = None
    war_id = None
    for prefix, outcome in _PREFIXES.items():
        if isinstance(step, str) and step.startswith(prefix):
            suffix = step[len(prefix):]
            if (suffix.isascii() and suffix.isdecimal() and len(suffix) <= 10
                    and not suffix.startswith("0") and 0 < int(suffix) <= 2**31 - 1):
                requested, war_id = outcome, int(suffix)
            break
    if requested is None:
        return None
    receipt: dict[str, object] = {
        "schema": SCHEMA, "status": "unbound", "war_id": war_id,
        "requested_outcome": requested, "requested_native_outcome": None,
        "command_acknowledged": action_result.get("accepted") is True,
        "war_absence_observed": None, "observed_result_identity": None,
        "result_identity_reason": "no_independent_result_observer",
        "before_frame": None, "post_frame": None,
        "resources": {}, "claims": {"status": "not_observed", "rows": None},
        "titles": {"status": "not_observed", "rows": []},
        "truce": {"status": "not_observed", "expiry_date_raw": None},
        "issues": [],
    }
    issues = receipt["issues"]
    try:
        before, post = _frame(before_snapshot), _frame(post_snapshot)
        if (any(before[key] != post[key] for key in (
                "episode_run_id", "actor_character_id", "bridge_pid", "connection_generation"))
                or any(post[key] < before[key] for key in ("date_raw", "revision", "native_revision"))):
            raise ValueError("post frame crossed action identity")
        wars = _wars(before_snapshot)
        matches = [row for row in wars if row["war_id"] == war_id]
        if len(matches) != 1 or matches[0].get("player_side") not in {"attacker", "defender"}:
            raise ValueError("pre-action full WarID/side unavailable")
        war = matches[0]
        side = war["player_side"]
        opponent = _integer(war.get("primary_opponent_character_id"))
        raw_targets = war.get("targeted_title_ids")
        target_ids = [] if raw_targets == [] else player_claims_title_ids(raw_targets)
        rendered_ids = target_ids[:MAXIMUM_OBSERVED_TITLES]
        absent = all(row["war_id"] != war_id for row in _wars(post_snapshot))
    except ValueError as error:
        issues.append(str(error))
        return receipt
    physical_victory = (requested == "player_victory") == (side == "attacker")
    receipt.update({
        "status": "war_absent" if absent else "war_present",
        "requested_native_outcome": (
            "white_peace" if requested == "white_peace"
            else "attacker_victory" if physical_victory else "attacker_defeat"
        ),
        "war_absence_observed": absent, "before_frame": before, "post_frame": post,
        "player_side": side, "opponent_character_id": opponent,
        "target_title_ids": rendered_ids, "target_title_count": len(target_ids),
        "target_titles_omitted": len(target_ids) - len(rendered_ids),
    })
    if not absent:
        # A still-active war supplies no postwar material observation.
        return receipt
    for name in ("gold", "prestige", "piety"):
        pre = _fixed(before_snapshot.get("played_character_" + name))
        after = _fixed(post_snapshot.get("played_character_" + name))
        receipt["resources"][name] = {
            "status": "observed" if pre is not None and after is not None else "unavailable",
            "before": pre, "after": after,
            "delta_raw": after["raw"] - pre["raw"] if pre is not None and after is not None else None,
            "same_date": before["date_raw"] == post["date_raw"],
            "action_attribution": "unproven",
        }
    if claims_result is not None:
        try:
            result = _query_envelope(claims_result, post, query_player_claims_v1_step(rendered_ids))
            value = normalize_player_claims_v1(
                result.get("player_claims"), expected_title_ids=rendered_ids,
                expected_actor_character_id=post["actor_character_id"],
                expected_snapshot_revision=post["native_revision"], expected_date_raw=post["date_raw"],
            )
            receipt["claims"] = {"status": value["status"], "rows": deepcopy(value["claims"]),
                                  "query_sequence": result["query_sequence"],
                                  "unavailable_reason": value.get("unavailable_reason")}
        except ValueError as error:
            receipt["claims"] = {"status": "unavailable", "rows": None}
            issues.append("claims: " + str(error))
    if title_holder_results is not None:
        rows, seen = [], set()
        try:
            if not isinstance(title_holder_results, list) or len(title_holder_results) > len(rendered_ids):
                raise ValueError("bounded title result list unavailable")
            for result in title_holder_results:
                value = result.get("title_holder") if isinstance(result, dict) else None
                title_id = value.get("title_id") if isinstance(value, dict) else None
                if type(title_id) is not int or title_id not in rendered_ids or title_id in seen:
                    raise ValueError("title result is not a unique frozen target")
                _query_envelope(result, post, query_title_holder_v1_step(title_id))
                value = normalize_title_holder_v1(
                    value, expected_title_id=title_id,
                    expected_actor_character_id=post["actor_character_id"],
                    expected_snapshot_revision=post["native_revision"], expected_date_raw=post["date_raw"],
                )
                if (value["game_version"] != "1.20.0.4"
                        or value["executable_sha256"].upper() != PLAYER_CLAIMS_V1_EXE_SHA256):
                    raise ValueError("title result lacks current4 provenance")
                rows.append({key: deepcopy(value.get(key)) for key in (
                    "title_id", "status", "holder_character_id", "holder_immediate_liege_character_id",
                    "holder_top_liege_character_id", "holder_in_player_realm", "unavailable_reason",
                )})
                seen.add(title_id)
            receipt["titles"] = {"status": "observed" if rows else "not_observed", "rows": rows,
                                 "observed_target_count": len(seen),
                                 "all_frozen_targets_observed": len(seen) == len(target_ids)
                                 and all(row["status"] == "available" for row in rows)}
        except ValueError as error:
            receipt["titles"] = {"status": "unavailable", "rows": []}
            issues.append("titles: " + str(error))
    if truce_result is not None:
        try:
            step = "query-raiktor-actual-truce-expiry-v1-" + str(opponent)
            result = _query_envelope(truce_result, post, step)
            # The shared normalizer intentionally takes only the native envelope.
            wire = {key: result.get(key) for key in (
                "step", "accepted", "query_sequence", "snapshot_revision",
                "raiktor_actual_truce_expiry", "backend_id", "read_only", "date_raw",
            )}
            value = normalize_player_truce_expiry_v1(
                wire, expected_toward_character_id=opponent,
                expected_owner_character_id=post["actor_character_id"],
                expected_snapshot_revision=post["native_revision"], expected_date_raw=post["date_raw"],
            )
            receipt["truce"] = {key: deepcopy(value[key]) for key in (
                "status", "owner_character_id", "toward_character_id", "native_has_truce",
                "expiry_date_raw", "temporal_semantics", "unavailable_reason",
            )}
            receipt["truce"]["direction"] = "player_toward_opponent"
            receipt["truce"]["query_sequence"] = result["query_sequence"]
        except ValueError as error:
            receipt["truce"] = {"status": "unavailable", "expiry_date_raw": None}
            issues.append("truce: " + str(error))
    return receipt
