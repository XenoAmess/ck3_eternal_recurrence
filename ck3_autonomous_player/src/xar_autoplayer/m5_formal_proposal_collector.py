"""Default-off M5 collection of existing same-frame domain proposals.

The collector is read-only.  It adapts domain-policy results that a private
caller has already observed, invokes the existing dispatcher once, and never
returns a CK3 step.  Public strategy and capability surfaces do not import it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

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
    """Run one private source read at the formal paused decision boundary."""

    result = deepcopy(dict(planned))
    plan = result.get("plan")
    if not isinstance(plan, Mapping):
        raise ValueError("M5 formal collector lacks a baseline plan")
    cleaned = {
        key: value for key, value in result.items()
        if not key.startswith("_private_")
    }
    baseline = deepcopy(dict(plan))

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
