"""Private same-frame M5 sources for peaceful construction and faction gifts.

This module only composes existing read-only domain queries.  It does not
advertise a capability, submit an action, or turn partial data into a no-op.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping, Sequence

from .bridge.domain_construction_private_transport_v1 import (
    RESERVE_RAW as CONSTRUCTION_RESERVE_RAW,
    query_construction_private,
)
from .bridge.driver import BridgeUnavailableError
from .bridge.faction_gift_formal_route_v1 import (
    MINIMUM_GOLD_RESERVE_RAW as FACTION_GIFT_RESERVE_RAW,
)
from .construction_formal_consumer import read_construction_ledger
from .faction_gift_formal_candidate_v1 import (
    latest_same_frame_faction_root_v1,
)
from .faction_gift_pending_v1 import read_faction_gift_ledger_v1
from .m5_formal_proposal_collector import SOURCE_SCHEMA
from .m5_observed_opportunity_selector import observed_frame


PRODUCER_POLICY = "g2-m5-peacetime-building-faction-source-v1"


def query_m5_peacetime_proposal_sources_v1(
    driver: object,
    *,
    snapshot: Mapping[str, object],
    history: Sequence[Mapping[str, object]],
    baseline_plan: Mapping[str, object],
    expected_revision: int,
) -> dict[str, object]:
    """Read at most one building and one faction-gift proposal on one frame."""

    frame = _require_peaceful_frame(snapshot, expected_revision=expected_revision)
    observed_gold_raw = _snapshot_gold(snapshot)
    if (
        baseline_plan.get("policy") != "one-life-turn-v1"
        or baseline_plan.get("selected_step") != "life-advance"
    ):
        raise BridgeUnavailableError(
            "M5 peacetime source requires the ordinary life-advance baseline"
        )
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise BridgeUnavailableError(
            "M5 peacetime source lacks its managed durable state_dir"
        )

    construction_ledger = read_construction_ledger(state_dir)
    faction_ledger = read_faction_gift_ledger_v1(state_dir)
    if construction_ledger.get("pending") is not None:
        raise BridgeUnavailableError(
            "M5 peacetime source has an unresolved construction action"
        )
    if faction_ledger.get("pending") is not None:
        raise BridgeUnavailableError(
            "M5 peacetime source has an unresolved faction gift action"
        )
    applied = construction_ledger.get("applied")
    construction_consumed = (
        isinstance(applied, Mapping)
        and applied.get("episode_run_id") == frame["episode_run_id"]
    )

    _require_driver_frame(driver, frame, expected_gold_raw=observed_gold_raw)
    root_view = latest_same_frame_faction_root_v1(snapshot, history)
    root_status = root_view.get("status")
    if root_status not in {"known_empty", "targeting_present"}:
        raise BridgeUnavailableError(
            "M5 peacetime source lacks a complete same-frame feudal faction root: "
            f"{root_status or 'unknown'}"
        )

    if construction_consumed:
        # The current formal construction route admits one applied action per
        # episode.  Omit only that domain; an independent faction proposal is
        # still useful and must not be turned into a permanent joint no-op.
        construction = {"status": "already_consumed_in_episode"}
    else:
        construction = query_construction_private(
            driver, expected_revision=expected_revision
        )
        _require_driver_frame(
            driver, frame, expected_gold_raw=observed_gold_raw
        )
        construction_status = construction.get("status")
        if construction_status not in {
            "selected", "no_legal_budgeted_building",
        }:
            raise BridgeUnavailableError(
                "M5 peacetime construction source is incomplete: "
                f"{construction_status or 'unknown'}"
            )
        construction_world = construction.get("world")
        if (
            not isinstance(construction_world, Mapping)
            or construction_world.get("player_gold_raw") != observed_gold_raw
        ):
            raise BridgeUnavailableError(
                "M5 peacetime construction gold crossed the planning frame"
            )
    construction_status = construction["status"]

    faction: dict[str, object]
    if root_status == "known_empty":
        faction = {
            "status": "known_empty",
            "reason": "same_frame_public_targeting_count_zero",
            "public_capability_advertised": False,
            "gift_submission_enabled": False,
        }
    else:
        root = root_view.get("root")
        reader = getattr(driver, "query_faction_gift_private_candidate_v1", None)
        if not isinstance(root, Mapping) or not callable(reader):
            raise BridgeUnavailableError(
                "M5 peacetime faction source reader is unavailable"
            )
        raw_faction = reader(
            snapshot=deepcopy(dict(snapshot)),
            same_frame_root=deepcopy(dict(root)),
            minimum_gold_reserve_raw=FACTION_GIFT_RESERVE_RAW,
        )
        if not isinstance(raw_faction, Mapping):
            raise BridgeUnavailableError(
                "M5 peacetime faction source returned a non-object"
            )
        faction = deepcopy(dict(raw_faction))
        faction_status = faction.get("status")
        if faction_status not in {"selected", "no_legal_candidate"}:
            raise BridgeUnavailableError(
                "M5 peacetime faction source is incomplete: "
                f"{faction_status or 'unknown'}"
            )
        observation = faction.get("observation")
        if (
            not isinstance(observation, Mapping)
            or observation.get("player_gold_raw") != observed_gold_raw
        ):
            raise BridgeUnavailableError(
                "M5 peacetime faction gold crossed the planning frame"
            )

    _require_driver_frame(driver, frame, expected_gold_raw=observed_gold_raw)
    # The two existing query transports do not mutate either formal ledger.
    # Re-read them before publishing explicit empty commitments.
    if read_construction_ledger(state_dir) != construction_ledger:
        raise BridgeUnavailableError(
            "M5 peacetime construction ledger changed during readback"
        )
    if read_faction_gift_ledger_v1(state_dir) != faction_ledger:
        raise BridgeUnavailableError(
            "M5 peacetime faction ledger changed during readback"
        )

    domains: dict[str, object] = {}
    if construction_status == "selected":
        domains["building"] = {"query": deepcopy(dict(construction))}
    if faction.get("status") == "selected":
        domains["diplomacy"] = {"candidate": deepcopy(faction)}

    return {
        "schema": SOURCE_SCHEMA,
        "status": "available",
        "read_only": True,
        "advertised": False,
        "frame": deepcopy(frame),
        "existing_commitments": {
            "frame": deepcopy(frame),
            "gold_raw": 0,
            "pending_war_slots": 0,
            "army_ids": [],
            "ally_character_ids": [],
            "character_ids": [],
            "commitment_keys": [],
        },
        # Each admitted proposal retains its existing domain reserve.  Zero is
        # the observed absence of an additional cross-domain cash commitment.
        "gold_reserve_raw": 0,
        # This producer proves an empty active-war vector and admits no war
        # proposal, so its observed joint war-slot budget is exactly zero.
        "max_active_wars": 0,
        "domains": domains,
        "producer": {
            "policy": PRODUCER_POLICY,
            "scope": "peacetime_building_and_faction_gift_only",
            "observed_player_gold_raw": observed_gold_raw,
            "domain_minimum_gold_reserves_raw": {
                "building": CONSTRUCTION_RESERVE_RAW,
                "diplomacy": FACTION_GIFT_RESERVE_RAW,
            },
            "observed_active_war_count": 0,
            "observed_player_army_count": 0,
            "construction_status": construction_status,
            "faction_status": faction.get("status"),
            "pending_formal_ledgers_empty": True,
            "formal_action_ready": False,
        },
    }


def _require_peaceful_frame(
    snapshot: Mapping[str, object], *, expected_revision: int
) -> dict[str, object]:
    if type(expected_revision) is not int or expected_revision <= 0:
        raise BridgeUnavailableError(
            "M5 peacetime source lacks the planning revision"
        )
    frame = observed_frame(snapshot)
    played = snapshot.get("played_character")
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or not isinstance(played, Mapping)
        or played.get("alive") is not True
        or played.get("character_id") != frame["played_character_id"]
        or snapshot.get("active_event") is not None
        or snapshot.get("pending_character_interaction") is not None
        or snapshot.get("one_life_terminal_reason") is not None
        or snapshot.get("active_wars") != []
        or snapshot.get("player_armies") != []
        or frame["revision"] != expected_revision
        or frame["snapshot_id"] != f"native:{frame['native_revision']}"
    ):
        raise BridgeUnavailableError(
            "M5 peacetime source requires one stable peaceful paused actor frame"
        )
    _snapshot_gold(snapshot)
    return frame


def _snapshot_gold(snapshot: Mapping[str, object]) -> int:
    gold = snapshot.get("played_character_gold")
    raw = gold.get("raw") if isinstance(gold, Mapping) else None
    if (
        type(raw) is not int
        or raw < 0
        or gold.get("scale") != 100_000
    ):
        raise BridgeUnavailableError(
            "M5 peacetime source lacks observed player gold"
        )
    return raw


def _require_driver_frame(
    driver: object, expected_frame: Mapping[str, object], *,
    expected_gold_raw: int,
) -> None:
    reader = getattr(driver, "take_internal_semantic_snapshot", None)
    if not callable(reader):
        raise BridgeUnavailableError(
            "M5 peacetime source lacks an internal semantic snapshot reader"
        )
    current = reader()
    if not isinstance(current, Mapping):
        raise BridgeUnavailableError(
            "M5 peacetime source internal snapshot is malformed"
        )
    current_frame = _require_peaceful_frame(
        current, expected_revision=int(expected_frame["revision"])
    )
    if current_frame != dict(expected_frame):
        raise BridgeUnavailableError(
            "M5 peacetime source crossed its paused frame"
        )
    if _snapshot_gold(current) != expected_gold_raw:
        raise BridgeUnavailableError(
            "M5 peacetime source player gold changed during readback"
        )
