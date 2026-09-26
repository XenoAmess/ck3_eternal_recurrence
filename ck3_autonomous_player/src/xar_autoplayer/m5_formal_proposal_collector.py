"""Default-off M5 collection of existing same-frame domain proposals.

The collector is read-only. It adapts domain-policy results observed by a
private caller and invokes the existing dispatcher once. The separate opt-in
formal planner can route its selected positive-income building through the
existing construction consumer. Public capability surfaces do not import it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path

from .construction_formal_consumer import (
    SUBMIT_STEP as CONSTRUCTION_SUBMIT_STEP,
    plan_construction_private,
    read_construction_ledger,
)
from .bridge.domain_construction_private_transport_v1 import (
    _identity as construction_process_identity,
)
from .m5_joint_dispatch import M5FrameDispatcher
from .m5_observed_opportunity_selector import (
    active_defensive_war_continuation_proposal,
    construction_proposal,
    council_steward_proposal,
    faction_gift_proposal,
    observed_frame,
    wartime_lifestyle_perk_proposal,
)


SOURCE_SCHEMA = "xar.ck3.m5-formal-proposal-sources.v1"
RESULT_SCHEMA = "xar.ck3.m5-formal-proposal-collection.v1"
_DOMAIN_ORDER = ("war", "council", "building", "diplomacy", "lifestyle")


def collect_m5_formal_proposals(
    *, snapshot: Mapping[str, object], sources: Mapping[str, object],
) -> dict[str, object]:
    """Adapt complete inputs and reserve one analytic opportunity.

    ``sources`` is private and unadvertised.  Every included domain is strict:
    omission means no complete proposal was observed, while a malformed
    included domain is a RED rather than permission to ignore its fields.
    """

    frame = observed_frame(snapshot)
    domains = sources.get("domains")
    if (
        sources.get("schema") != SOURCE_SCHEMA
        or sources.get("status") != "available"
        or sources.get("read_only") is not True
        or sources.get("advertised") is not False
        or sources.get("frame") != frame
        or not isinstance(domains, Mapping)
    ):
        raise ValueError("M5 formal proposal sources lack one private paused frame")
    unknown = set(domains) - set(_DOMAIN_ORDER)
    if unknown:
        raise ValueError(
            "M5 formal proposal sources contain unsupported domains: "
            + ", ".join(sorted(str(key) for key in unknown))
        )

    proposals: list[dict[str, object]] = []
    for domain in _DOMAIN_ORDER:
        raw = domains.get(domain)
        if raw is None:
            continue
        if not isinstance(raw, Mapping):
            raise ValueError(f"M5 {domain} proposal source is malformed")
        proposals.append(
            _adapt_domain(domain, frame=frame, snapshot=snapshot, source=raw)
        )

    commitments = sources.get("existing_commitments")
    if not isinstance(commitments, Mapping):
        raise ValueError("M5 formal proposal sources lack observed commitments")
    gold_reserve_raw = sources.get("gold_reserve_raw")
    max_active_wars = sources.get("max_active_wars")
    if type(gold_reserve_raw) is not int or gold_reserve_raw < 0:
        raise ValueError("M5 formal proposal gold reserve is unavailable")
    if type(max_active_wars) is not int or max_active_wars < 0:
        raise ValueError("M5 formal proposal war budget is unavailable")

    dispatcher = M5FrameDispatcher(
        snapshot=deepcopy(dict(snapshot)),
        existing_commitments=deepcopy(dict(commitments)),
    )
    dispatch = dispatcher.choose_observed(
        snapshot=deepcopy(dict(snapshot)),
        proposals=proposals,
        gold_reserve_raw=gold_reserve_raw,
        max_active_wars=max_active_wars,
    )
    return {
        "schema": RESULT_SCHEMA,
        "policy": "g2-m5-formal-query-only-collector-v1",
        "status": (
            "reserved_analytic"
            if dispatch.get("selected_candidate_id") is not None
            else "no_complete_feasible_proposal"
        ),
        "read_only": True,
        "advertised": False,
        "frame": frame,
        "collected_domains": [proposal["domain"] for proposal in proposals],
        "collected_candidate_ids": [
            proposal["candidate_id"] for proposal in proposals
        ],
        "dispatch": dispatch,
        "selected_step": None,
        "formal_action_ready": False,
    }


def plan_m5_formal_query_only(
    driver: object, planned: Mapping[str, object], *,
    snapshot: Mapping[str, object], history: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Read one private frame and route only a proved construction choice."""

    result = deepcopy(dict(planned))
    plan = result.get("plan")
    if not isinstance(plan, Mapping):
        raise ValueError("M5 formal collector lacks a baseline plan")
    cleaned = {
        key: value for key, value in result.items()
        if not key.startswith("_private_")
    }
    baseline = deepcopy(dict(plan))

    # The only bound source producer is the peaceful building + faction-gift
    # reader.  An existing formal war, marriage, or other domain step keeps
    # priority and must not be replaced by a private query-only RED.
    if baseline.get("selected_step") != "life-advance":
        return cleaned

    def blocked(reason: str) -> dict[str, object]:
        return {
            **cleaned,
            "plan": {
                **baseline,
                "phase": "m5_joint_query_only_red",
                "selected_step": None,
                "reason": reason,
                "m5_joint_formal_action_ready": False,
            },
        }

    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        return blocked("M5 private collector requires one paused map frame")
    revision = cleaned.get("revision")
    if type(revision) is not int or revision <= 0:
        return blocked("M5 private collector lacks the planning revision")
    reader = getattr(driver, "query_m5_joint_proposal_sources_private_v1", None)
    if not callable(reader):
        return blocked("M5 private proposal source reader is unavailable")
    # The joint source refuses unresolved actions.  Let the existing durable
    # construction consumer resolve its own receipt before another selection.
    state_dir = getattr(driver, "state_dir", None)
    if isinstance(state_dir, Path):
        try:
            ledger = read_construction_ledger(state_dir)
            pending = ledger.get("pending")
            applied = ledger.get("applied")
            if isinstance(pending, Mapping) or (
                isinstance(applied, Mapping)
                and applied.get("episode_run_id") == snapshot.get("episode_run_id")
                and (
                    construction_process_identity(driver) != (
                        applied.get("post_bridge_pid"),
                        applied.get("post_bridge_creation_date"),
                    )
                    or type(snapshot.get("native_revision")) is not int
                    or type(snapshot.get("date_raw")) is not int
                    or snapshot["native_revision"] <= applied.get("post_native_revision", 0)
                    or snapshot["date_raw"] <= applied.get("post_date_raw", 0))
            ):
                return plan_construction_private(
                    driver, cleaned, snapshot, list(history), set()
                )
            if isinstance(applied, Mapping) and (
                applied.get("episode_run_id") == snapshot.get("episode_run_id")
            ):
                baseline["construction_receipt_consumed"] = dict(applied)
        except (RuntimeError, TypeError, ValueError) as error:
            return blocked(f"M5 construction receipt RED: {error}")
    try:
        sources = reader(
            snapshot=deepcopy(dict(snapshot)),
            history=deepcopy([dict(row) for row in history]),
            baseline_plan=deepcopy(baseline),
            expected_revision=revision,
        )
        if not isinstance(sources, Mapping):
            raise ValueError("M5 private proposal source reader returned a non-object")
        collection = collect_m5_formal_proposals(
            snapshot=snapshot, sources=sources,
        )
    except (RuntimeError, TypeError, ValueError) as error:
        return blocked(f"M5 private proposal collection RED: {error}")
    dispatch = collection["dispatch"]
    reservation = dispatch.get("reservation")
    building_source = sources.get("domains", {}).get("building")
    query = (building_source.get("query")
             if isinstance(building_source, Mapping) else None)
    candidate = query.get("candidate") if isinstance(query, Mapping) else None
    income = (candidate.get("authored_monthly_income_hundredths")
              if isinstance(candidate, Mapping) else None)
    if (
        isinstance(reservation, Mapping)
        and reservation.get("domain") == "building"
        and reservation.get("candidate_id") == dispatch.get("selected_candidate_id")
        and type(income) is int and income > 0
        and isinstance(query, Mapping)
    ):
        return {
            **cleaned,
            "plan": {
                **baseline,
                "phase": "m5_joint_construction_typed_submit",
                "selected_step": CONSTRUCTION_SUBMIT_STEP,
                "construction_private_query": deepcopy(dict(query)),
                "reason": "submit one same-frame native-legal positive-income construction",
                "m5_joint_query_only": collection,
                "m5_joint_formal_action_ready": True,
            },
        }
    return {
        **cleaned,
        "plan": {
            **baseline,
            "phase": "m5_joint_query_only_observed",
            "selected_step": None,
            "reason": "compare complete same-frame proposals without submitting an action",
            "m5_joint_query_only": collection,
            "m5_joint_formal_action_ready": False,
        },
    }


def _adapt_domain(
    domain: str, *, frame: Mapping[str, object],
    snapshot: Mapping[str, object], source: Mapping[str, object],
) -> dict[str, object]:
    if domain == "war":
        return active_defensive_war_continuation_proposal(
            frame=frame,
            snapshot=snapshot,
            plan=_mapping(source.get("plan"), "war.plan"),
            observation=_mapping(source.get("observation"), "war.observation"),
        )
    if domain == "council":
        return council_steward_proposal(
            frame=frame,
            observation=_mapping(source.get("observation"), "council.observation"),
            decision=_mapping(source.get("decision"), "council.decision"),
        )
    if domain == "building":
        return construction_proposal(
            frame=frame,
            query=_mapping(source.get("query"), "building.query"),
        )
    if domain == "diplomacy":
        return faction_gift_proposal(
            frame=frame,
            candidate=_mapping(source.get("candidate"), "diplomacy.candidate"),
        )
    if domain == "lifestyle":
        return wartime_lifestyle_perk_proposal(
            frame=frame,
            query=_mapping(source.get("query"), "lifestyle.query"),
            decision=_mapping(source.get("decision"), "lifestyle.decision"),
            current_war_plan=_mapping(
                source.get("current_war_plan"), "lifestyle.current_war_plan"
            ),
        )
    raise ValueError(f"unsupported M5 proposal domain {domain!r}")


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"M5 {name} is unavailable")
    return value
