"""Original selected-detail and selected_item reads; ordinary list guards stay intact."""
from __future__ import annotations
from collections.abc import Mapping
from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1,read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity,private_native_provenance
from .version_identity import CK3_12004,require_exact_native_backend,require_exact_native_build
from .player_holy_site_private_transport import _ref,_availability

STEP="query-player-holy-site-adoption-detail-v1"
PERMISSION="allow_private_holy_site_adoption_detail_query"


def normalize_holy_site_adoption_detail_v1(value:object,*,snapshot:Mapping[str,object],holy_site_id:int)->dict[str,object]:
    result=_availability(value,"adoption detail")
    if (result.get("schema")!="ck3_12004_holy_site_adoption_detail_v1"
            or require_exact_native_build(result.get("game_version"),result.get("executable_sha256"))!=CK3_12004
            or private_native_build_identity(snapshot)!=CK3_12004):
        raise ValueError("HolySite adoption detail requires exact 1.20.0.4")
    actor=snapshot.get("played_character")
    if (not isinstance(actor,Mapping) or result.get("played_character_id")!=actor.get("character_id")
            or result.get("date_raw")!=snapshot.get("date_raw")
            or result.get("requested_holy_site_id")!=holy_site_id
            or type(result.get("capture_epoch"))is not int or result["capture_epoch"]<=0):
        raise ValueError("HolySite adoption detail crossed its player/frame/full reference")
    if type(result.get("played_character_id"))is not int or type(result.get("date_raw"))is not int:
        raise ValueError("adoption detail player/date must retain native integer types")
    _ref(result.get("requested_holy_site_id"),"requested HolySite",nullable=False)
    for field in ("rendered_visibility_observed","native_resource_quote_available","action_ready",
                  "decision_confirm_invoked","adoption_completed_observed"):
        if result.get(field)is not False:raise ValueError("adoption detail read claimed an unimplemented action/postcondition")
    if result.get("read_only")is not True or result.get("native_resource_quote")is not None:
        raise ValueError("adoption detail query lost readonly/unknown-cost semantics")
    if not result["available"]:
        if result.get("native_can_confirm")is not None or result.get("normal_requirements_can_confirm")is not None:
            raise ValueError("unavailable adoption detail cannot invent observed false legality")
        return result
    if (result.get("decision_key")!="adopt_holy_site_decision" or result.get("decision_option_id")!=-1
            or result.get("detail_actor_id")!=actor["character_id"]
            or result.get("current_actor_id")!=actor["character_id"]
            or result.get("parameter_and_selection_match")is not True):
        raise ValueError("adoption detail definition/current actor/source parameter differs")
    _ref(result.get("detail_actor_id"),"detail actor",nullable=False)
    _ref(result.get("current_actor_id"),"current actor",nullable=False)
    for key in ("parameter_holy_site_id","selected_holy_site_id"):
        if _ref(result.get(key),key,nullable=False)!=holy_site_id:
            raise ValueError("adoption parameter and actual selected entry must both match requested full reference")
    count,index=result.get("candidate_count"),result.get("selected_index")
    if type(count)is not int or type(index)is not int or not 0<=index<count<=8192:
        raise ValueError("adoption selected candidate index is unavailable")
    token=result.get("selected_item_token")
    if type(token)is not int or not 0<=token<=0xFFFFFFFF:
        raise ValueError("actual selected_item token must preserve its native uint32 value")
    for key in ("detail_present","root_present","native_can_confirm","bypass_requirements_observed",
                "normal_requirements_legality_observed","confirm_tooltip_available"):
        if type(result.get(key))is not bool:raise ValueError("adoption detail Boolean observation is malformed: "+key)
    if not result["detail_present"]:raise ValueError("available adoption detail must exist")
    raw=result.get("bypass_requirements_raw")
    if result["bypass_requirements_observed"]:
        if type(raw)is not int or not 0<=raw<=255:raise ValueError("actual bypass_requirements byte is malformed")
    elif raw is not None:raise ValueError("unobserved bypass_requirements is unknown")
    normal=result["bypass_requirements_observed"] and raw==0
    if normal and type(result.get("normal_requirements_can_confirm"))is not bool:
        raise ValueError("regular requirements result must preserve observed Boolean")
    if (result["normal_requirements_legality_observed"]!=normal
            or result.get("normal_requirements_can_confirm")!=(result["native_can_confirm"]if normal else None)):
        raise ValueError("bypass/unknown flag cannot qualify regular native legality")
    text,reason=result.get("confirm_tooltip"),result.get("confirm_tooltip_unavailable_reason")
    if result["confirm_tooltip_available"]:
        if not isinstance(text,str)or len(text.encode("utf-8"))>65536 or reason is not None:
            raise ValueError("native confirm reason CString is malformed")
    elif text is not None or not isinstance(reason,str)or not reason:
        raise ValueError("unavailable native confirm reason must stay unknown")
    return result


def query_holy_site_adoption_detail_private_v1(driver:object,*,expected_revision:int,holy_site_id:int)->dict[str,object]:
    _ref(holy_site_id,"requested HolySite",nullable=False)
    before,envelope=read_private_g2_native_query_v1(driver,permission=PERMISSION,step=STEP,
        expected_revision=expected_revision,request_fields={"holy_site_id":holy_site_id},include_native_command_history=False)
    try:
        if (require_exact_native_backend(envelope.get("game_version"),envelope.get("executable_sha256"),
                envelope.get("backend_id"),suffix="player-holy-site-adoption-detail-v1")!=CK3_12004
                or envelope.get("domain_key")!="player_holy_site_adoption_detail_v1"
                or envelope.get("snapshot_revision")!=before.get("native_revision")
                or envelope.get("date_raw")!=before.get("date_raw")):
            raise ValueError("native adoption detail envelope differs from exact frame")
        value=normalize_holy_site_adoption_detail_v1(envelope.get("player_holy_site_adoption_detail"),snapshot=before,holy_site_id=holy_site_id)
        if envelope.get("status")!=("observed"if value["available"]else"unavailable"):
            raise ValueError("native adoption detail envelope loses source availability")
    except ValueError as error:raise BridgeUnavailableError(str(error))from error
    return {**value,**private_native_provenance(before),**private_g2_query_metadata_v1(before),
            "snapshot_revision":envelope["snapshot_revision"],"backend_id":envelope["backend_id"],
            "domain_key":envelope["domain_key"],"status":envelope["status"],"advertised":False}
