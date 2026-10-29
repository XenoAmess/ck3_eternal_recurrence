package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.PreviewStatus;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** The actual selected-move origin review and bounded alternate search, without movement authority. */
public final class RouteOriginExposurePolicy implements OrdinaryPolicy {
    public record HeldCapitals(ObservationIdentity before,List<Integer> provinceIds) {
        public HeldCapitals {Objects.requireNonNull(before);provinceIds=List.copyOf(provinceIds);provinceIds.forEach(p->require(p>0,"held capital Province"));}
    }
    @FunctionalInterface public interface HeldCapitalPort {Optional<HeldCapitals> collect(PlanningRequest request);}
    public interface GeneralForecastPort {
        Obj review(PlanningRequest request,Obj originalCandidate);
        Obj contactAdmission(Obj exactForecast);
    }
    private final ExactRef source;
    private final HeldCapitalPort held;
    private final GeneralForecastPort general;
    private final SafeWarRendezvousPolicy.MovementState movement;
    private final MilitaryPlanningDecision.ApplicationAdapter adapter;
    public RouteOriginExposurePolicy(ExactRef source,HeldCapitalPort held,GeneralForecastPort general,
            SafeWarRendezvousPolicy.MovementState movement,MilitaryPlanningDecision.ApplicationAdapter adapter) {
        this.source=Objects.requireNonNull(source);this.held=Objects.requireNonNull(held);this.general=Objects.requireNonNull(general);
        this.movement=Objects.requireNonNull(movement);this.adapter=Objects.requireNonNull(adapter);
    }
    @Override public PlanningStage stage(){return PlanningStage.ROUTE_ORIGIN_EXPOSURE;}
    @Override public ExactRef implementationSource(){return source;}
    @Override public Decision evaluate(PlanningRequest request,Draft previous) {
        return adapter.adapt(request,previous,review(request,previous));
    }
    public MilitaryPlanningDecision review(PlanningRequest request,Draft previous) {
        Obj baseline=previous.detail(),observed=baseline,snapshot=request.observations().snapshot();
        Optional<Move> parsed=parseMove(optionalText(observed.get("selected_step")));
        if(parsed.isPresent()&&snapshot.get("player_armies") instanceof Arr) {
            Move move=parsed.orElseThrow();Army subject=null;
            for(Obj row:rows(snapshot.get("player_armies")))if(Integer.valueOf(move.army()).equals(optionalInt(row.get("army_id")))){subject=army(row);break;}
            if(subject!=null&&subject.route().isPresent()&&subject.route().orElseThrow().isEmpty()&&subject.moveTargetPresent()&&subject.target()==null
                    &&subject.current()!=null&&subject.current()>0) {
                var preview=freshPreview(request,subject,move.target());
                if(preview.isPresent()&&!hostiles(request).isEmpty()) {
                    var query=new MilitaryTimeline.Query(subject.id(),subject.current(),move.target(),hostiles(request),preview.orElseThrow().routeProvinceIds());
                    var lookup=MilitaryTimeline.fresh(request,query);
                    if(lookup instanceof MilitaryTimeline.Found found) {
                        var exposure=MilitaryTimeline.origin(found.horizon(),subject.current());
                        if(exposure.veto()&&qualifiedOrigin(request,observed,exposure.detail()))return new MilitaryPlanningDecision.Keep(empty());
                        if(exposure.veto())observed=merge(observed,obj(f("phase",text("native_war_pre_move_origin_exposure_rejected")),f("selected_step",Nil.INSTANCE),
                                f("active_attack_allowed",new Bool(false)),f("reason",text("the fresh native timeline puts a hostile at the origin before this army reaches its first waypoint; one contact-free day cannot justify the longer committed leg")),
                                f("pre_move_origin_exposure_v1",exposure.detail()),f("contact_admission",obj(f("admitted",new Bool(false)),f("reason",text("native_origin_entry_before_subject_first_arrival")))),
                                f("original_move_plan_v1",observed)));
                    }
                }
            }
        }
        return alternate(request,previous,observed);
    }
    private boolean qualifiedOrigin(PlanningRequest request,Obj plan,Obj exposure) {
        if(!yes(plan.get("general_battle_forecast_used_for_decision"))||!(plan.get("encounter") instanceof Obj encounter)
                ||!(plan.get("general_battle_forecast") instanceof Obj forecast)||!(plan.get("general_battle_contact_admission") instanceof Obj admission)
                ||!yes(admission.get("admitted"))||!Objects.equals(encounter.get("target_province_id"),exposure.get("origin_province_id")))return false;
        Obj snapshot=request.observations().snapshot(),capture=obj(f("snapshot_id",nullable(snapshot.get("snapshot_id"))),f("revision",nullable(snapshot.get("revision"))),
                f("native_revision",nullable(snapshot.get("native_revision"))),f("date_raw",nullable(snapshot.get("date_raw"))));
        if(!capture.equals(forecast.get("capture"))||!yes(general.contactAdmission(forecast).get("admitted"))
                ||!(encounter.get("attacker_army_ids") instanceof Arr)||!(encounter.get("defender_army_ids") instanceof Arr))return false;
        List<Integer> attackers=ids(encounter.get("attacker_army_ids")),defenders=ids(encounter.get("defender_army_ids"));int subject=id(exposure.get("subject_army_id"));
        if(attackers.contains(subject)==defenders.contains(subject))return false;
        Set<Integer> incoming=new HashSet<>();for(Obj row:rows(exposure.get("native_timeline_exposures")))incoming.add(id(row.get("hostile_army_id")));
        return !incoming.isEmpty()&&new HashSet<>(attackers.contains(subject)?defenders:attackers).containsAll(incoming);
    }
    private MilitaryPlanningDecision alternate(PlanningRequest request,Draft previous,Obj observed) {
        Obj snapshot=request.observations().snapshot();
        boolean origin=new Text("native_war_pre_move_origin_exposure_rejected").equals(observed.get("phase"))
                &&observed.get("pre_move_origin_exposure_v1") instanceof Obj exposure&&yes(exposure.get("veto"));
        boolean rejected=new Text("native_war_general_battle_model_rejected").equals(observed.get("phase"))
                ||observed.get("stationary_model_rejection_continuation_v1") instanceof Obj;
        if(!(origin||rejected)||!(observed.get("contact_admission") instanceof Obj admission)||!no(admission.get("admitted"))
                ||!new Text(origin?"native_origin_entry_before_subject_first_arrival":"bounded_model_risk_budget_exceeded").equals(admission.get("reason")))return retained(observed,previous);
        if(!quiet(snapshot)||!(snapshot.get("played_character") instanceof Obj actor)||!yes(actor.get("alive"))
                ||!(snapshot.get("player_armies") instanceof Arr))return retained(observed,previous);
        List<Army> own=rows(snapshot.get("player_armies")).stream().map(MilitaryPlanInputs::army).filter(Army::controllable).toList();
        if(own.size()!=1)return retained(observed,previous);Army army=own.getFirst();
        boolean stationary=army.state()!=null?Set.of("regular","sieging").contains(army.state().toLowerCase(java.util.Locale.ROOT)):
                Integer.valueOf(1).equals(army.stateCode())||Integer.valueOf(3).equals(army.stateCode());
        if(army.current()==null||army.current()<=0||!Objects.equals(army.raw().get("owner_character_id"),actor.get("character_id"))
                ||army.route().isEmpty()||!army.route().orElseThrow().isEmpty()||!army.moveTargetPresent()||army.target()!=null
                ||!Boolean.FALSE.equals(army.inCombat())||!Boolean.FALSE.equals(army.retreating())||!stationary)return retained(observed,previous);
        List<Obj> wars=wars(request);List<Integer> hostiles=hostiles(request);if(hostiles.isEmpty()||hostiles.size()>64)return retained(observed,previous);
        List<Army> enemies=enemies(request).stream().filter(e->hostiles.contains(e.id())).toList();
        List<Army> incoming=enemies.stream().filter(e->!Objects.equals(e.current(),army.current())
                &&(Objects.equals(e.target(),army.current())||e.route().isPresent()&&e.route().orElseThrow().contains(army.current()))).toList();
        if(incoming.isEmpty())return retained(observed,previous);
        Optional<HeldCapitals> completeHeld=held.collect(request);if(completeHeld.isPresent())require(completeHeld.orElseThrow().before().equals(request.before()),"held capitals crossed frame");
        Map<Integer,Obj> seeds=new java.util.TreeMap<>();
        for(Obj war:wars)if(new Text("defender").equals(war.get("player_side"))&&war.get("war_objective_province_ids") instanceof Arr
                &&war.get("objective_province_states") instanceof Arr) {
            Map<Integer,Obj> states=new HashMap<>();for(Obj row:rows(war.get("objective_province_states")))states.put(int32(row.get("province_id")),row);
            for(int province:ids(war.get("war_objective_province_ids")))if(province>0&&states.containsKey(province)&&yes(states.get(province).get("occupation_observable"))&&no(states.get(province).get("is_occupied")))
                seeds.putIfAbsent(province,obj(f("source",text("observed_unoccupied_defensive_objective")),f("war_id",nullable(war.get("war_id")))));
        }
        if(completeHeld.isPresent())for(int province:completeHeld.orElseThrow().provinceIds())seeds.putIfAbsent(province,
                obj(f("source",text("complete_same_frame_directly_held_county_capital")),f("war_id",Nil.INSTANCE)));
        Set<Integer> danger=new HashSet<>();for(Army enemy:enemies){if(enemy.current()!=null&&enemy.current()>0)danger.add(enemy.current());if(enemy.target()!=null&&enemy.target()>0)danger.add(enemy.target());enemy.route().ifPresent(danger::addAll);}
        List<Obj> refusals=new ArrayList<>();
        for(var seed:seeds.entrySet()) {
            int target=seed.getKey();Obj targetSource=seed.getValue();
            if(target==army.current()||danger.contains(target)){refusals.add(refusal(target,"current_or_observed_hostile_path"));continue;}
            String previewStep="preview-move-army-"+army.id()+"-to-"+target,moveStep="move-army-"+army.id()+"-to-"+target;
            if(!advertised(request,previewStep)){refusals.add(refusal(target,"preview_not_advertised"));continue;}
            var preview=freshPreview(request,army,target);
            if(preview.isEmpty())return selected(decorate(plan(previewStep,"native_war_route_preview",
                    "the proposed attack was rejected and a hostile is approaching; preview a real alternate defensive objective or held capital before choosing an escape"),
                    observed,wars,army,incoming,hostiles,target,targetSource,"preview",refusals),Purpose.READ_ONLY);
            var p=preview.orElseThrow();if(p.status()!=PreviewStatus.AVAILABLE){refusals.add(put(refusal(target,"native_preview_unavailable"),"native_preview",previewDocument(p)));continue;}
            var audit=MilitaryRouteGeometry.geometry(p.routeProvinceIds(),army.current(),target,enemies.stream().map(Army::geometry).toList());
            if(audit.status()!=MilitaryRouteGeometry.Status.SAFE){refusals.add(put(refusal(target,"route_geometry_rejected"),"route_audit",auditDocument(audit)));continue;}
            var query=new MilitaryTimeline.Query(army.id(),army.current(),target,hostiles,p.routeProvinceIds());var horizon=MilitaryTimeline.fresh(request,query);
            if(!(horizon instanceof MilitaryTimeline.Found found)) {
                if(horizon instanceof MilitaryTimeline.Missing&&MilitaryTimeline.failure(request,query).isEmpty()&&advertised(request,query.step())) {
                    Obj candidate=merge(plan(query.step(),"native_war_candidate_contact_horizon","test the alternate escape route against every observed hostile native timeline; no movement is authorized by this query"),
                            obj(f("route_preview",previewDocument(p)),f("route_audit",auditDocument(audit))));
                    return selected(decorate(candidate,observed,wars,army,incoming,hostiles,target,targetSource,"contact_query",refusals),Purpose.READ_ONLY);
                }
                refusals.add(refusal(target,"fresh_full_hostile_horizon_unavailable"));continue;
            }
            var contact=found.horizon();if(!contact.oneDayFree()){refusals.add(put(refusal(target,"contact_not_free"),"contact_horizon",contact.original()));continue;}
            var originExposure=MilitaryTimeline.origin(contact,army.current());
            if(originExposure.veto()){refusals.add(put(refusal(target,"origin_exposed_before_first_arrival"),"origin_exposure",originExposure.detail()));continue;}
            if(!advertised(request,moveStep)){refusals.add(refusal(target,"native_move_not_advertised"));continue;}
            var intent=movement.activeIntent(request,army.id(),target);
            if(!(intent instanceof WarStrengthRelief.EvidenceAbsent)){refusals.add(refusal(target,intent instanceof WarStrengthRelief.EvidenceUnavailable?"move_intent_evidence_unavailable":"existing_move_intent_no_resubmit"));continue;}
            var backoff=movement.deferredBackoff(request,army.id(),target);
            if(backoff instanceof WarStrengthRelief.EvidenceUnavailable){refusals.add(refusal(target,"move_backoff_evidence_unavailable"));continue;}
            if(backoff instanceof WarStrengthRelief.EvidenceFound evidence){require(evidence.before().equals(request.before()),"origin backoff crossed frame");if(!yes(evidence.evidence().get("retry_due"))){refusals.add(refusal(target,"native_move_backoff_no_resubmit"));continue;}}
            Obj replacement=merge(plan(moveStep,"native_war_pursuit","avoid the rejected battle by a separately previewed, full-hostile checked route to an observed alternate; actual arrival remains unverified"),
                    obj(f("active_wars",objects(wars)),f("route_preview",previewDocument(p)),f("route_audit",put(auditDocument(audit),"contact_horizon",contact.original())),
                            f("pursuit",obj(f("army_id",number(army.id())),f("target_province_id",number(target)),f("target_source",targetSource.get("source"))))));
            Obj guarded=Objects.requireNonNull(general.review(request,replacement));
            if(yes(guarded.get("active_attack_allowed"))){refusals.add(refusal(target,"alternate_would_authorize_attack"));continue;}
            Obj decorated=decorate(guarded,observed,wars,army,incoming,hostiles,target,targetSource,"original_general_review",refusals);
            String step=optionalText(guarded.get("selected_step"));
            if(step==null)return held(decorated);
            return selected(decorated,moveStep.equals(step)?Purpose.WORLD_ACTION:Purpose.READ_ONLY);
        }
        if(completeHeld.isEmpty()&&advertised(request,"query-campaign-root-context-v1"))return selected(decorate(plan("query-campaign-root-context-v1","native_war_safe_objective_context",
                "the known defensive objectives did not yield a safe escape; read current complete directly held county capitals before declaring alternatives exhausted"),observed,wars,army,incoming,hostiles,null,
                obj(f("source",text("same_frame_root_required"))),"root_query",refusals),Purpose.READ_ONLY);
        Obj retained=decorate(observed,observed,wars,army,incoming,hostiles,null,obj(f("source",text("no_qualified_alternate"))),"not_selected",refusals);
        return retained(retained,previous);
    }
    private record Move(int army,int target) {}
    private static Optional<Move> parseMove(String step) {
        if(step==null||!step.matches("move-army-(0|[1-9][0-9]*)-to-[1-9][0-9]*"))return Optional.empty();
        String[] values=step.substring(10).split("-to-",-1);try{return Optional.of(new Move(Integer.parseInt(values[0]),Integer.parseInt(values[1])));}catch(NumberFormatException invalid){return Optional.empty();}
    }
    private static boolean quiet(Obj s){return yes(s.get("paused"))&&yes(s.get("map_ready"))&&s.get("active_event")==Nil.INSTANCE&&s.get("pending_character_interaction")==Nil.INSTANCE
            &&s.members().containsKey("top_exclusive_modal_choice_hint")&&!(s.get("top_exclusive_modal_choice_hint") instanceof Obj hint&&new Text("present").equals(hint.get("status")));}
    private static Obj plan(String step,String phase,String reason){return obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",text(step)),f("active_attack_allowed",new Bool(false)),f("reason",text(reason)));}
    private static Obj refusal(int target,String status){return obj(f("province_id",number(target)),f("status",text(status)));}
    private static Obj decorate(Obj plan,Obj original,List<Obj> wars,Army army,List<Army> incoming,List<Integer> hostiles,Integer target,Obj source,String stage,List<Obj> refusals) {
        Obj details=obj(f("schema",text("xar.ck3.safe-reposition-after-model-rejection/v1")),f("stage",text(stage)),f("subject_army_id",number(army.id())),f("origin_province_id",number(army.current())),
                f("candidate_province_id",target==null?Nil.INSTANCE:number(target)),f("candidate_source",source),f("incoming_hostile_army_ids",numbers(incoming.stream().map(Army::id).distinct().sorted().toList())),
                f("all_hostile_army_ids",numbers(hostiles)),f("candidate_rejections",objects(refusals)),f("original_model_rejection",nullable(original.get("contact_admission"))),f("original_phase",nullable(original.get("phase"))),
                f("original_selected_step",nullable(original.get("selected_step"))),f("rejected_battle_forecast",nullable(original.get("battle_forecast"))),f("origin_exposure",nullable(original.get("pre_move_origin_exposure_v1"))),
                f("arrival_guaranteed",new Bool(false)),f("safe_retreat_achieved",new Bool(false)),f("new_attack_authorization",new Bool(false)),f("unknown_modal_is_absence_proof",new Bool(false)));
        return merge(plan,obj(f("active_wars",objects(wars)),f("safe_reposition_after_model_rejection_v1",details)));
    }
    private static MilitaryPlanningDecision retained(Obj observed,Draft previous) {
        if(observed.get("selected_step")==Nil.INSTANCE&&previous.command().isPresent())return held(observed);
        return new MilitaryPlanningDecision.Keep(observed);
    }
    private static MilitaryPlanningDecision.Hold held(Obj detail) {
        return new MilitaryPlanningDecision.Hold(optionalText(detail.get("policy")),optionalText(detail.get("phase")),optionalText(detail.get("reason")),Optional.empty(),detail);
    }
    private static MilitaryPlanningDecision.Select selected(Obj detail,Purpose purpose) {
        return new MilitaryPlanningDecision.Select(optionalText(detail.get("policy")),optionalText(detail.get("phase")),optionalText(detail.get("reason")),new OperationKey(optionalText(detail.get("selected_step"))),empty(),purpose,detail);
    }
}
