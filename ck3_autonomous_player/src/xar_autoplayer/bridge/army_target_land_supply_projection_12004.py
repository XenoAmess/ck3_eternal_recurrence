"""Conditional target rate; never an observed post-arrival monthly change.

Source: actual .4 24E5180..24E5FDA, foreign own addition 24E5B04..5BAA,
shared 24E5FE0 adjustment. The caller must establish one paused frame lease.
"""
from __future__ import annotations
from collections.abc import Mapping
from .army_captured_target_land_supply_inputs_contract import (
    normalize_target_land_supply_in_route_preview,
)
from .army_current_province_supply_contributors_contract import (
    normalize_current_province_supply_contributors_v1,
)
from .army_current_land_supply_rate_contract import normalize_current_land_supply_rate_inputs_v1
from .army_full_land_supply_rate_projection import _project_land_rate_operands_v1

_OPERANDS=("loaded_excess_slope_raw","loaded_min_loss_raw","loaded_max_loss_raw",
           "loaded_divisor_floor_raw","commander_modifier_1a9_raw")


def _own_selected_contribution(row):
    if row.get("status")!="available" or any(type(row.get(k)) is not int for k in ("army_id","native_carmy_id")):
        return None
    family=normalize_current_province_supply_contributors_v1(
        row.get("current_province_supply_contributors_v1"))
    if family is None:return None
    public,native=row.get("army_id"),row.get("native_carmy_id")
    if family["subject_army_id"]!=public or family["subject_carmy_id"]!=native:
        raise ValueError("selected supply Army FullIDs disagree")
    occurrences=[o for o in family["occurrences"] if o["army_id"]==public
                 and o["native_carmy_id"]==native and o["included"] is True
                 and o["status"]=="available"]
    if not occurrences or type(family["province_id"]) is not int:return None
    observed=[]
    for o in occurrences:
        if o["owner_character_id"]!=family["owner_character_id"]:
            raise ValueError("selected own owner context disagrees")
        ids=[]; total=0
        for r in o["regiments"]:
            if r["status"]!="available":return None
            if r["native_supply_loss_eligible"]:
                # Native flags2 accumulates ordered ArRg+38 using signed32 ADD.
                total=(total+r["current_soldiers"]+(1<<31))%(1<<32)-(1<<31)
                ids.append(r["army_regiment_id"])
        if total!=o["native_eligible_current_soldiers"]:
            raise ValueError("selected flags2 count disagrees with complete eligible roster")
        observed.append((total,tuple(ids)))
    if any(value!=observed[0] for value in observed):
        raise ValueError("duplicate own occurrences have conflicting complete rosters")
    total,ids=observed[0]
    if total<0 or len(ids)!=len(set(ids)):
        raise ValueError("ordinary arrival requires nonnegative nonaliased eligible roster")
    return dict(army_id=public,native_carmy_id=native,
                owner_character_id=family["owner_character_id"],
                current_province_id=family["province_id"],
                eligible_current_soldiers=total,eligible_army_regiment_ids=list(ids))


def project_conditional_target_land_rate_12004(
    row: Mapping[str,object], preview: Mapping[str,object], *,
    same_frame_inputs: bool=False, selected_rows=(),
):
    """Project explicit selected union into target's captured current mode0 U.

    Each selected Army away from target is added once. Armies already there
    are represented by captured U and are not re-added. No subtraction from
    the origin, path terrain guess, or observed target monthly rate is used.
    """
    result=dict(source="conditional_target_land_supply_rate_12004",
        source_body_rva="24E5180",source_body_bytes=3674,
        source_body_sha256="36ffa60acf90c96a61299625427706a7891c83c8d337d38bb4b5b62c24e72fb3",
        status="unavailable",full_land_rate_ready=False,
        conditional_full_land_rate_raw=None,scale=100000,missing_inputs=[],
        captured_target_current_usage_soldiers=None,
        conditional_arrival_usage_soldiers=None,selected_supply_eligible_union=[],
        actual_target_monthly_observed=False,actual_arrival_observed=False,
        actual_arrival_readback_required=True,
        assumption="normal arrival inserts each selected Army once; all other captured target/owner/commander/roster/loaded inputs remain unchanged",
        monthly_dispatch_observed=False,physical_loss_predicted=False)
    missing=result["missing_inputs"]
    if same_frame_inputs is not True:missing.append("same_paused_frame_query_and_preview_lease")
    if row.get("status")!="available":missing.append("available_selected_ArmyStrength")
    normalized=normalize_target_land_supply_in_route_preview(dict(preview))
    supply=normalized.get("province_supply")
    target=supply.get("target") if isinstance(supply,dict) else None
    if not isinstance(target,dict) or target.get("status")!="available":
        missing.append("available_captured_target_supply");return result
    if (normalized.get("army_id")!=row.get("army_id")
            or supply.get("native_carmy_id")!=row.get("native_carmy_id")):
        raise ValueError("target preview belongs to another selected Army FullID")
    family=target.get("captured_target_land_supply_inputs_v1")
    if not isinstance(family,dict) or not family["province_component_observation_ready"]:
        missing.append("captured_target_land_supply_inputs_v1");return result
    if target.get("scale")!=1 or type(target.get("scale")) is not int:
        raise ValueError("captured target soldier scale is malformed")
    u,limit=target.get("native_supply_usage_soldiers"),target.get("native_supply_limit_soldiers")
    for key,value in (("target_current_usage",u),("target_limit",limit)):
        if type(value) is not int or not 0<=value<(1<<31):missing.append(key)
    if missing:return result
    selected=tuple(selected_rows) if selected_rows else (row,)
    subjects={(x.get("army_id"),x.get("native_carmy_id")) for x in selected}
    if (len(subjects)!=len(selected) or len({x.get("army_id") for x in selected})!=len(selected)
            or len({x.get("native_carmy_id") for x in selected})!=len(selected)
            or (row.get("army_id"),row.get("native_carmy_id")) not in subjects):
        raise ValueError("selected union must contain subject exactly once")
    seen_regiments=set(); added=0
    for item in selected:
        own=_own_selected_contribution(item)
        if own is None:
            missing.append("selected_complete_own_supply_eligible_roster");continue
        if own["owner_character_id"]!=supply.get("owner_character_id"):
            raise ValueError("conditional selected union requires same actual owner")
        ids=set(own["eligible_army_regiment_ids"])
        if ids & seen_regiments:raise ValueError("selected union shares eligible ArRg FullID")
        seen_regiments|=ids
        away=own["current_province_id"]!=target.get("province_id")
        own["added_to_target_current_usage"]=away
        if away:added+=own["eligible_current_soldiers"]
        result["selected_supply_eligible_union"].append(own)
    result["captured_target_current_usage_soldiers"]=u
    result["conditional_arrival_usage_soldiers"]=u+added
    # Foreign getter uses QWORD scaled addition, but a later ordinary current
    # Province getter has a signed32 accumulation. Do not claim overflow arrival.
    if u+added>=(1<<31):missing.append("ordinary_arrival_usage_within_signed32")
    operands={key:None for key in _OPERANDS}
    current=normalize_current_land_supply_rate_inputs_v1(row.get("current_land_supply_rate_inputs_v1"))
    if current:
        if (current["subject_army_id"]!=row.get("army_id") or
                current["subject_carmy_id"]!=row.get("native_carmy_id")):
            raise ValueError("current loaded supply operands belong to another Army")
        for key in _OPERANDS[:-1]:operands[key]=current[key]
        # M is reusable only for the exact preview-resolved commander. A sea
        # early-return's missing M never becomes native0.
        if current["commander_resolved_full_id"]==supply.get("commander_character_id"):
            operands["commander_modifier_1a9_raw"]=current["commander_modifier_1a9_raw"]
    child=family.get("loss_adjustment_operands_v1")
    if isinstance(child,dict):
        if child["commander_resolved_full_id"] is not None and child["commander_resolved_full_id"]!=supply.get("commander_character_id"):
            raise ValueError("target loss modifier resolved commander differs from preview")
        for key in _OPERANDS:
            if child[key] is not None:
                if operands[key] is not None and operands[key]!=child[key]:
                    raise ValueError("same-frame captured target/current loss operands disagree")
                operands[key]=child[key]
    result["captured_loss_operands"]=operands
    if missing:return result
    result.update(_project_land_rate_operands_v1(usage=u+added,limit=limit,
        p=family["province_component_raw"],resupply=family["native_resupply_eligible"],
        gain=family["loaded_gain_raw"],operands=operands))
    return result
