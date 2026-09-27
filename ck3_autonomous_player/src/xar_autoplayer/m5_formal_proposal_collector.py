"""Default-off M5 collection of existing same-frame domain proposals.

The collector is read-only. It adapts domain-policy results observed by a
private caller and invokes the existing dispatcher once. The separate opt-in
formal planner routes its selected building, marriage or faction gift through
the owning formal consumer. Public capability surfaces do not import it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path

from .construction_formal_consumer import (
    SUBMIT_STEP as CONSTRUCTION_SUBMIT_STEP,
    plan_construction_private,
    priority_construction_receipt,
    read_construction_ledger,
)
from .bridge.observed_heir_marriage_private_action_v1 import (
    SUBMIT_STEP as FAMILY_SUBMIT_STEP,
)
from .bridge.faction_gift_formal_route_v1 import (
    SUBMIT_STEP as FACTION_GIFT_SUBMIT_STEP,
    plan_faction_gift_private_v1,
)
from .bridge.driver import PreSubmissionRevisionMismatchError
from .bridge.domain_construction_private_transport_v1 import (
    _identity as construction_process_identity,
)
from .m5_joint_dispatch import M5FrameDispatcher
from .faction_gift_formal_candidate_v1 import latest_same_frame_faction_root_v1
from .faction_gift_pending_v1 import read_faction_gift_ledger_v1
from .lifestyle_formal_consumer import ROOT_QUERY_STEP
from .family_marriage_formal_consumer import (
    plan_family_marriage_private, read_family_marriage_ledger,
)
from .m5_observed_opportunity_selector import (
    active_defensive_war_continuation_proposal,
    construction_proposal,
    council_steward_proposal,
    faction_gift_proposal,
    first_heir_marriage_proposal,
    observed_frame,
    wartime_lifestyle_perk_proposal,
)


SOURCE_SCHEMA = "xar.ck3.m5-formal-proposal-sources.v1"
RESULT_SCHEMA = "xar.ck3.m5-formal-proposal-collection.v1"
_DOMAIN_ORDER = ("war", "council", "building", "marriage", "diplomacy", "lifestyle")


def _same_frame_root_returned_unavailable(
    snapshot: Mapping[str, object], history: Sequence[Mapping[str, object]],
) -> bool:
    """Recognize a completed native read with no usable root on this frame."""
    for row in reversed(history):
        if row.get("command") != ROOT_QUERY_STEP or row.get("ok") is not True:
            continue
        result = row.get("result")
        context = (result.get("campaign_root_context")
                   if isinstance(result, Mapping) else None)
        if (isinstance(context, Mapping)
                and result.get("step") == ROOT_QUERY_STEP
                and result.get("accepted") is True
                and result.get("status") == "unavailable"
                and result.get("snapshot_revision") == snapshot.get("native_revision")
                and context.get("status") == "unavailable"
                and context.get("snapshot_revision") == snapshot.get("native_revision")
                and context.get("date_raw") == snapshot.get("date_raw")):
            return True
    return False


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
    active_wars = snapshot.get("active_wars")
    if not isinstance(active_wars, list):
        raise ValueError("M5 active wars are unavailable")
    if active_wars:
        from .m5_war_cash_resource_v1 import require_complete_war_cash_resource_v1

        if len(active_wars) != 1 or not isinstance(active_wars[0], Mapping):
            raise ValueError("M5 active-war cash scope needs one observed war")
        war_id = active_wars[0].get("war_id")
        cash = require_complete_war_cash_resource_v1(
            sources.get("war_cash_resource"), frame=frame, war_id=war_id,
        )
        treasury = snapshot.get("played_character_gold")
        if (not isinstance(treasury, Mapping)
                or treasury.get("scale") != 100_000
                or cash["observed_treasury_raw"] != treasury.get("raw")):
            raise ValueError("M5 war cash treasury differs from snapshot")
        if (type(commitments.get("gold_raw")) is not int
                or commitments["gold_raw"]
                < cash["existing_shared_gold_commitment_raw"]
                or gold_reserve_raw < cash["joint_gold_reserve_raw"]):
            raise ValueError("M5 shared budget omits active-war cash")
        war_source = domains.get("war")
        if war_source is not None:
            observation = war_source.get("observation")
            if (not isinstance(observation, Mapping)
                    or observation.get("war_cash_resource") != cash):
                raise ValueError("M5 war proposal cash differs from shared budget")

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
    result = {
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
    producer = sources.get("producer")
    if isinstance(producer, Mapping) and isinstance(
        producer.get("family_status"), str
    ):
        result["producer_family_status"] = producer["family_status"]
    return result


def plan_m5_formal_query_only(
    driver: object, planned: Mapping[str, object], *,
    snapshot: Mapping[str, object], history: Sequence[Mapping[str, object]],
    available_steps: set[str],
) -> dict[str, object]:
    """Read one private frame and route its proved formal domain choice."""

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

    def root_unavailable(reason: str) -> dict[str, object]:
        # The joint comparison cannot run without the faction root.  Keep it
        # visibly unresolved and hold date advance; the service may still
        # invoke the independent, native-gated family consumer on this frame.
        return {
            **cleaned,
            "plan": {
                **baseline,
                "phase": "m5_joint_root_unavailable_independent_family",
                "selected_step": None,
                "reason": reason,
                "m5_joint_status": "same_frame_faction_root_unavailable",
                "m5_joint_red_reason": reason,
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
    gift_enabled = getattr(
        driver, "allow_private_faction_gift_formal_trial", False
    ) is True
    family_enabled = getattr(
        driver, "allow_private_family_marriage_formal_trial", False
    ) is True
    if isinstance(state_dir, Path):
        try:
            ledger = read_construction_ledger(state_dir)
            pending = ledger.get("pending")
            applied = ledger.get("applied")
            priority_receipt = (
                None if isinstance(pending, Mapping) else
                priority_construction_receipt(
                    driver, ledger, snapshot,
                    process_identity=(
                        construction_process_identity(driver)
                        if isinstance(applied, Mapping) or ledger.get("applied_prior")
                        else None
                    ),
                )
            )
            if isinstance(pending, Mapping) or priority_receipt is not None:
                return plan_construction_private(
                    driver, cleaned, snapshot, list(history),
                    available_steps,
                )
            if isinstance(applied, Mapping) and (
                applied.get("episode_run_id") == snapshot.get("episode_run_id")
            ):
                baseline["construction_receipt_consumed"] = dict(applied)
            # A submitted gift must resolve its material receipt before the
            # source producer considers another gift on this frame.
            if gift_enabled and isinstance(
                read_faction_gift_ledger_v1(state_dir).get("pending"), Mapping
            ):
                return plan_faction_gift_private_v1(
                    driver, {**cleaned, "plan": baseline}, snapshot,
                    history, available_steps,
                )
            if family_enabled:
                family_ledger = read_family_marriage_ledger(state_dir)
                family_pending = family_ledger.get("pending")
                family_resolved = family_ledger.get("resolved")
                if isinstance(family_pending, Mapping) or (
                    isinstance(family_resolved, Mapping)
                    and family_resolved.get("episode_run_id")
                    == snapshot.get("episode_run_id")
                ):
                    family = plan_family_marriage_private(
                        driver, {**cleaned, "plan": baseline}, snapshot,
                    )
                    family_plan = family.get("plan")
                    if not isinstance(family_plan, Mapping):
                        raise ValueError("M5 pending family plan is unavailable")
                    # A changed heir can make an old resolved pair stale.
                    # Its fresh proposal must compete with the other same-frame
                    # sources; only in-flight/result work has priority here.
                    if family_plan.get("selected_step") == "life-advance":
                        baseline = deepcopy(dict(family_plan))
                    elif family_plan.get("selected_step") != FAMILY_SUBMIT_STEP:
                        return family
        except PreSubmissionRevisionMismatchError:
            # The native runner owns one bounded readiness replan after the
            # existing gift consumer observed a newer same-date paused frame.
            raise
        except (RuntimeError, TypeError, ValueError) as error:
            return blocked(f"M5 prior action receipt RED: {error}")
    # The source needs a public faction root before it can compare a gift to
    # an otherwise ready building. Read the missing same-frame root first;
    # never interpret an absent root as an empty faction opportunity.
    root_status = latest_same_frame_faction_root_v1(snapshot, history)["status"]
    if root_status == "same_frame_root_not_observed":
        if _same_frame_root_returned_unavailable(snapshot, history):
            return root_unavailable(
                "M5 same-frame root returned unavailable; joint inputs remain RED"
            )
        if ROOT_QUERY_STEP not in available_steps:
            return root_unavailable(
                "M5 same-frame faction root is absent and its query is unavailable"
            )
        return {
            **cleaned,
            "plan": {
                **baseline,
                "phase": "m5_joint_root_query",
                "selected_step": ROOT_QUERY_STEP,
                "reason": "observe same-frame feudal faction facts before joint spending",
                "m5_joint_formal_action_ready": False,
            },
        }
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
    except PreSubmissionRevisionMismatchError:
        raise
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
    family_source = sources.get("domains", {}).get("marriage")
    family_plan = (family_source.get("plan")
                   if isinstance(family_source, Mapping) else None)
    if (
        isinstance(reservation, Mapping)
        and reservation.get("domain") == "marriage"
        and reservation.get("candidate_id") == dispatch.get("selected_candidate_id")
        and isinstance(family_plan, Mapping)
        and family_plan.get("selected_step") == FAMILY_SUBMIT_STEP
    ):
        return {
            **cleaned,
            "plan": {
                **baseline,
                **deepcopy(dict(family_plan)),
                "phase": "m5_joint_family_typed_submit",
                "selected_step": FAMILY_SUBMIT_STEP,
                "reason": "submit one same-frame native-legal valued first-heir marriage",
                "m5_joint_query_only": collection,
                "m5_joint_formal_action_ready": True,
            },
        }
    gift_source = sources.get("domains", {}).get("diplomacy")
    gift_candidate = (gift_source.get("candidate")
                      if isinstance(gift_source, Mapping) else None)
    if (
        gift_enabled
        and isinstance(reservation, Mapping)
        and reservation.get("domain") == "diplomacy"
        and reservation.get("candidate_id") == dispatch.get("selected_candidate_id")
        and isinstance(gift_candidate, Mapping)
    ):
        gift = plan_faction_gift_private_v1(
            driver, {**cleaned, "plan": {**baseline, "selected_step": "life-advance"}},
            snapshot, history, available_steps,
        )
        gift_plan = gift.get("plan")
        selected_candidate = (gift_plan.get("faction_gift_private_candidate_v1")
                              if isinstance(gift_plan, Mapping) else None)
        if not (
            isinstance(selected_candidate, Mapping)
            and selected_candidate.get("status") == "selected"
            and selected_candidate.get("choice") == gift_candidate.get("choice")
            and selected_candidate.get("observation")
            == gift_candidate.get("observation")
        ):
            return blocked("M5 selected faction gift changed before formal routing")
        step = gift_plan.get("selected_step")
        if step not in {FACTION_GIFT_SUBMIT_STEP, "save-checkpoint"}:
            return blocked("M5 selected faction gift has no formal submit path")
        return {
            **gift,
            "plan": {
                **gift_plan,
                "m5_joint_query_only": collection,
                "m5_joint_formal_action_ready": step == FACTION_GIFT_SUBMIT_STEP,
            },
        }
    if (
        not gift_enabled
        and isinstance(reservation, Mapping)
        and reservation.get("domain") == "diplomacy"
    ):
        return {
            **cleaned,
            "plan": {
                **baseline,
                "selected_step": "life-advance",
                "m5_joint_status": "selected_gift_formal_consumer_disabled",
                "m5_joint_query_only": collection,
                "m5_joint_formal_action_ready": False,
            },
        }
    if collection["status"] == "no_complete_feasible_proposal":
        return {
            **cleaned,
            "plan": {
                **baseline,
                "phase": "m5_joint_empty_proposals",
                "selected_step": "life-advance",
                "reason": "no complete same-frame proposal; continue normal life advance",
                "m5_joint_query_only": collection,
                "m5_joint_formal_action_ready": False,
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
    if domain == "marriage":
        return first_heir_marriage_proposal(
            frame=frame,
            plan=_mapping(source.get("plan"), "marriage.plan"),
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
