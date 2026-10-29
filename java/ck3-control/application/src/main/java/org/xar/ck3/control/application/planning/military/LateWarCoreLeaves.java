package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.LateWarCoreInputs.is;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.capabilities.DefenderRefugeScopes;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.LateWarCoreInputs.Context;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner;

/** Actual ranked route producer strategy12202..12933, followed by the original late fallback/pursuit producer. */
public final class LateWarCoreLeaves {
    private LateWarCoreLeaves() {}
    public static List<WarCorePlanner.Leaf> factories(ExactRef rankedSource,ExactRef fallbackSource,LateWarCoreInputs.Provider inputs) {
        Objects.requireNonNull(inputs);
        return List.of(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.ORDINARY_RANKED_ROUTE,rankedSource,
                (request,previous)->capture(inputs,request,previous,true)),
                new WarCorePlanner.Leaf(WarCorePlanner.Boundary.DEFENSIVE_ROUTE_FALLBACK_AND_PURSUIT,fallbackSource,
                (request,previous)->capture(inputs,request,previous,false)));
    }
    private static MilitaryPlanningDecision capture(LateWarCoreInputs.Provider provider,PlanningRequest request,OrdinaryPolicy.Draft previous,boolean ranked) {
        LateWarCoreInputs.Capture capture=provider.collect(request,previous);
        if(capture instanceof LateWarCoreInputs.Unavailable missing)return new MilitaryPlanningDecision.Unavailable(missing.missing(),
                "the actual earlier WarCore producer has not published its same-frame late inputs");
        if(capture instanceof LateWarCoreInputs.NoPursuit residual) {
            LateWarCoreInputs.validateNoPursuit(request,residual);
            return ranked?new MilitaryPlanningDecision.Keep(empty()):residual(request,residual);
        }
        Context c=((LateWarCoreInputs.Available)capture).context();
        require(c.request().equals(request),"late input provider changed the planning request");
        if(ranked)return rank(c);
        LateRouteSelection selection=LateRouteSelection.decode(request,previous.detail().get(LateRouteSelection.FIELD));
        var clean=new java.util.LinkedHashMap<String,Value>(previous.detail().members());clean.remove(LateRouteSelection.FIELD);
        OrdinaryPolicy.Draft original=new OrdinaryPolicy.Draft(previous.policy(),previous.phase(),previous.reason(),previous.kind(),previous.command(),previous.purpose(),previous.domain(),new Obj(clean));
        return LateWarCoreFallback.plan(c,original,selection);
    }
    private static MilitaryPlanningDecision residual(PlanningRequest request,LateWarCoreInputs.NoPursuit p) {
        String phase,required=null,reason,step=null;List<Field> extra=new ArrayList<>();
        if(!p.stationaryThreats().isEmpty()) {
            phase="native_war_stationary_threat_blocked";required="replace-threatened-stationary-position";
            reason="enemy convergence threatens the stationary army and no immediate reroute is available";extra.add(f("route_rejections",objects(p.stationaryThreats())));
        } else if(p.exactSiegeRejection().isPresent()) {
            phase="native_war_siege_exit_blocked";required="replace-rejected-siege-position";
            reason="the exact siege was rejected and no safe replacement route is active; do not advance time";extra.add(f("siege_state",p.exactSiegeRejection().orElseThrow()));
        } else if(advertised(request,"life-advance")) {
            phase="native_war_reconnaissance";step="life-advance";reason="no enemy province is currently published; advance one bounded native interval and inspect again";
        } else {
            phase="native_war_reconnaissance_unsupported";required="life-advance";reason="the active war has no published enemy province and time cannot advance";
        }
        Obj detail=merge(obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",step==null?Nil.INSTANCE:text(step)),
                f("reason",text(reason)),f("active_wars",objects(p.warSummaries()))),obj(extra.toArray(Field[]::new)));
        if(required!=null)detail=put(detail,"required_step",text(required));
        return step==null?new MilitaryPlanningDecision.Hold("one-life-turn-v1",phase,reason,Optional.ofNullable(required).map(OperationKey::new),detail):
                new MilitaryPlanningDecision.Select("one-life-turn-v1",phase,reason,new OperationKey(step),empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,detail);
    }
    public static MilitaryPlanningDecision rank(Context c) {
        var p=c.published();
        if(p.stationaryThreats().isEmpty()&&p.unsafeArmyIds().isEmpty()) {
            Optional<Obj> intent=WarHistorySteps.capitalRegroupIntent(c.history(),c.snapshot(),c.subject().id(),p.tacticalWarId());
            if(intent.isPresent())return available(c,"native_war_capital_regroup_progress","native_war_capital_regroup_progress_unsupported",
                    "life-advance","the army independently arrived at the same-campaign capital regroup target; hold one bounded observation day before reconsidering the exhausted siege",
                    "the bounded capital regroup intent is active but the backend cannot advance its observation day",f("regroup_intent",intent.orElseThrow()));
        }
        List<Integer> candidates=p.rankedExactObjectives().stream().filter(p.siegeObjectives()::contains).toList();
        String source="war_objective_province";
        if(is(p.siegeRelief(),"status","ready")&&optionalInt(p.siegeRelief().get("target_province_id"))!=null) {
            candidates=List.of(province(p.siegeRelief().get("target_province_id")));source="enemy_siege_relief";
        }
        Optional<Obj> defensiveHold=!p.stationaryThreats().isEmpty()&&candidates.isEmpty()?WarCapitalContext.primaryDefenderHold(c,true,true):Optional.empty();
        Optional<Obj> refugeHold=Optional.empty(),root=Optional.empty(),refugeScope=Optional.empty();
        if(candidates.isEmpty()) {
            refugeHold=defensiveHold.isPresent()?defensiveHold:WarCapitalContext.primaryDefenderHold(c,true,true);
            if(refugeHold.isPresent()) {
                root=WarCapitalContext.sameFrameRoot(c.request());
                if(root.isEmpty()&&advertised(c.request(),"query-campaign-root-context-v1"))return action(c,"native_war_refuge_lifecycle_context",
                        "query-campaign-root-context-v1","read the current complete realm and direct-vassal capitals before a stationary defender chooses another native route or day",
                        f("defensive_hold",refugeHold.orElseThrow()));
                if(root.isPresent())refugeScope=DefenderRefugeScopes.directVassalRefugeLifecycleScope(c.snapshot(),root.orElseThrow());
            }
        }
        Optional<Obj> rally=defensiveHold.isPresent()?WarHistorySteps.nativeRallyHoldBinding(c.history(),c.snapshot(),p.tacticalWarId(),c.subject().id(),c.current()):Optional.empty();
        boolean refuge=false;Map<Integer,String> sources=new HashMap<>();
        if(defensiveHold.isPresent()&&rally.isPresent()) {
            root=WarCapitalContext.sameFrameRoot(c.request());
            Optional<List<Integer>> counties=root.flatMap(WarCapitalContext::directlyHeldCountyCapitals);
            if(counties.isEmpty())return required(c,"native_war_safe_objective_context","query-campaign-root-context-v1",
                    "the threatened primary defender requires a complete same-frame directly-held county-capital set before claiming that no alternate objective exists",
                    f("defensive_hold",defensiveHold.orElseThrow()),f("native_rally_hold_binding",rally.orElseThrow()),f("route_rejections",objects(p.stationaryThreats())));
            List<Integer> alternates=new ArrayList<>(counties.orElseThrow().stream().filter(v->v!=c.current()).toList());
            alternates.forEach(v->sources.put(v,"player_held_county_capital"));
            List<Integer> vassals=DefenderRefugeScopes.directVassalCapitalProvinceIds(root.orElseThrow()).orElse(List.of());
            for(int v:vassals)if(v!=c.current()&&!alternates.contains(v)&&advertised(c.request(),previewStep(c,v))) {
                alternates.add(v);sources.put(v,"same_realm_vassal_capital");
            }
            alternates.add(c.current());sources.put(c.current(),"stationary_player_held_capital");candidates=List.copyOf(alternates);source="player_held_county_capital";
            if(!p.routePreviewSupported())return hold(c,"native_war_safe_objective_route_preview_unsupported",null,
                    "directly-held county fallback candidates are observed, but none may be selected without the native route preview",
                    f("required_observation",text("fresh-native-route-preview")),f("candidate_province_ids",numbers(candidates)),
                    f("defensive_hold",defensiveHold.orElseThrow()),f("native_rally_hold_binding",rally.orElseThrow()),f("route_rejections",objects(p.stationaryThreats())));
        } else if(refugeScope.isPresent()&&refugeHold.isPresent()) {
            Obj scope=refugeScope.orElseThrow();String kind=optionalText(scope.get("current_kind"));
            if("direct_vassal_capital".equals(kind)||"directly_held_capital".equals(kind)) {
                refuge=true;List<Integer> values=new ArrayList<>();values.add(c.current());values.addAll(route(scope.get("candidate_province_ids")).orElseThrow());
                for(int v:values)sources.put(v,"same_realm_vassal_capital");sources.put(c.current(),"stationary_same_realm_vassal_capital");
                candidates=List.copyOf(values);source="same_realm_vassal_capital";
            }
        }
        List<Obj> rejected=new ArrayList<>();Set<Integer> blocked=new HashSet<>(p.blockedProvinces());
        Optional<Integer> target=Optional.empty();Optional<Obj> selectedAudit=Optional.empty(),transition=Optional.empty();
        boolean swept=p.routePreviewSupported()&&!candidates.isEmpty();
        if(swept)for(int rank=0;rank<candidates.size();rank++) {
            int candidate=candidates.get(rank);String candidateSource=sources.getOrDefault(candidate,source);
            if(candidate==c.current()) {
                if(p.exactSiegeRejection().isPresent()) {rejected.add(obj(f("target_province_id",number(candidate)),f("status",text("current_exact_siege_rejected")),
                        f("siege_status",nullable(p.exactSiegeRejection().orElseThrow().get("status")))));continue;}
                if(c.routeUnsafe()) {rejected.add(rejection(candidate,"cannot_replace_unsafe_active_route"));continue;}
                if(!p.stationaryThreats().isEmpty()||refuge) {
                    Optional<MilitaryTimeline.Horizon> horizon=Optional.empty();
                    if(c.contactSupported()) {
                        horizon=horizon(c,candidate,List.of());String query=query(c,candidate);
                        if(horizon.isEmpty()) {
                            Optional<Obj> failed=failure(c,candidate,List.of());
                            if(failed.isPresent()) {rejected.add(merge(rejection(candidate,"contact_timeline_unavailable"),obj(f("conflicts",objects(p.stationaryThreats())),f("contact_query_attempt",failed.orElseThrow()))));blocked.add(candidate);continue;}
                            return available(c,"native_war_stationary_contact_horizon","native_war_stationary_contact_horizon_unsupported",query,
                                    "resolve geometric convergence on the occupied exact objective with the stationary subject and hostile native arrival timelines",
                                    "the occupied exact objective requires a fresh stationary one-day contact horizon",
                                    f("route_audit",obj(f("status",text("stationary_geometric_threat")),f("target_province_id",number(candidate)),f("conflicts",objects(p.stationaryThreats())))),
                                    f("route_rejections",objects(rejected)));
                        }
                        MilitaryTimeline.Horizon h=horizon.orElseThrow();String advance=advance(c,candidate);
                        if(h.oneDayFree())return available(c,"native_war_stationary_contact_horizon_progress","native_war_stationary_contact_horizon_progress_unsupported",advance,
                                "the exact stationary timeline proves the occupied objective contact-free for the next day",
                                "the fresh stationary horizon is actionable, but the proof-bound one-day advance is unavailable",
                                f("route_audit",obj(f("status",text("safe_one_day_stationary_contact_horizon")),f("target_province_id",number(candidate)),f("contact_horizon",h.original()))),f("route_rejections",objects(rejected)));
                        if(unavoidable(h))transition=Optional.of(obj(f("advance_step",text(advance)),f("target_province_id",number(candidate)),f("contact_horizon",h.original())));
                    }
                    Obj rejection=merge(rejection(candidate,"unsafe"),obj(f("conflicts",objects(p.stationaryThreats()))));
                    if(horizon.isPresent())rejection=put(rejection,"contact_horizon",horizon.orElseThrow().original());
                    rejected.add(rejection);continue;
                }
                target=Optional.of(candidate);selectedAudit=Optional.of(obj(f("status",text("arrived")),f("target_province_id",number(candidate))));break;
            }
            if(blocked.contains(candidate)) {rejected.add(rejection(candidate,"blocked"));continue;}
            Optional<Obj> preview=preview(c,candidate);
            if(preview.isPresent()&&is(preview.orElseThrow(),"status","deferred")) {
                Obj observed=preview.orElseThrow();
                if(is(observed,"native_rejection_stage","move_mode_unavailable")) {rejected.add(put(rejection(candidate,"move_mode_unavailable"),"native_rejection_stage",text("move_mode_unavailable")));continue;}
                if(!p.stationaryThreats().isEmpty()||refuge) {
                    rejected.add(rejection(candidate,"deferred_while_stationary_province_threatened"));
                    if(refugeSource(candidateSource))continue;
                    return hold(c,"native_war_move_readiness_observation_required","query-native-army-move-readiness",
                            "the same-frame native preview rejected this canonical threatened CUnit before route construction; target enumeration cannot change the subject's move readiness",
                            f("route_preview",observed),f("route_rejections",objects(rejected)));
                }
                if(c.routeUnsafe()||p.exactSiegeRejection().isPresent()) {rejected.add(rejection(candidate,c.routeUnsafe()?"deferred_while_active_route_unsafe":"deferred_while_exact_siege_rejected"));continue;}
                String step=advertised(c.request(),"life-advance-one-day")?"life-advance-one-day":advertised(c.request(),"life-advance")?"life-advance":null;
                if(step!=null)return action(c,"native_war_route_preview_deferred",step,
                        "the same-frame army state rejected a read-only route preview; advance only the existing bounded date step before replanning",f("route_preview",observed),f("route_rejections",objects(rejected)));
                return hold(c,"native_war_route_preview_deferred_unsupported","life-advance","the deferred route preview requires time to advance",f("route_preview",observed),f("route_rejections",objects(rejected)));
            }
            if(preview.isEmpty())return available(c,"native_war_route_preview","native_war_route_preview_unsupported",previewStep(c,candidate),
                    "preview the exact objective route at the current date and origin before moving","the exact objective requires a fresh route preview before movement",
                    f("route_preview",obj(f("status",text("required")),f("army_id",number(c.subject().id())),f("origin_province_id",number(c.current())),f("target_province_id",number(candidate)))),f("route_rejections",objects(rejected)));
            Obj observed=preview.orElseThrow();List<Integer> route=route(observed.get("route_province_ids")).orElseThrow();Obj audit=audit(c,candidate,route);
            if((is(audit,"status","unsafe")||is(audit,"status","safe"))&&c.contactSupported()) {
                Optional<MilitaryTimeline.Horizon> h=horizon(c,candidate,route);
                if(h.isEmpty()) {
                    Optional<Obj> failed=failure(c,candidate,route);
                    if(failed.isPresent()) {rejected.add(merge(audit,obj(f("status",text("contact_timeline_unavailable")),f("contact_query_attempt",failed.orElseThrow()))));blocked.add(candidate);continue;}
                    return available(c,"native_war_candidate_contact_horizon","native_war_candidate_contact_horizon_unsupported",query(c,candidate),
                            "check the previewed objective route against the complete native one-day hostile contact timeline before movement",
                            "the intersecting candidate route requires a fresh exact one-day contact horizon",f("route_preview",observed),f("route_audit",audit),f("route_rejections",objects(rejected)));
                }
                var nativeH=h.orElseThrow();audit=put(audit,"contact_horizon",nativeH.original());
                if(!nativeH.oneDayFree())audit=merge(audit,obj(f("status",text("unsafe")),f("native_contact_veto",text("one_day_contact_not_free"))));
                else {
                    boolean enemyCurrent=rows(audit.get("conflicts")).stream().anyMatch(r->is(r,"kind","enemy_current_on_route"));
                    if(c.balance().filter(Balance::hostileOvermatch).isPresent()&&(refugeSource(candidateSource)||enemyCurrent))
                        audit=put(audit,"one_day_contact_horizon_rejected",text(refugeSource(candidateSource)?"hostile_operational_overmatch_player_held_county_fallback":"hostile_operational_overmatch_enemy_current_on_exact_route"));
                    else audit=put(audit,"status",text("safe_one_day_contact_horizon"));
                }
            }
            if(!safe(audit)) {rejected.add(audit);blocked.add(candidate);continue;}
            Optional<Obj> rollback=rollback(c,candidate,route(audit.get("route_province_ids")).orElseThrow());
            if(rollback.isPresent()) {rejected.add(obj(f("status",text("rolled_back_route_failure")),f("target_province_id",number(candidate)),f("route_province_ids",audit.get("route_province_ids")),f("failure",rollback.orElseThrow())));blocked.add(candidate);continue;}
            target=Optional.of(candidate);source=candidateSource;
            selectedAudit=Optional.of(put(audit,"selection",obj(f("policy",text("player_held_county_capital".equals(source)?"first_safe_player_held_county_capital":"same_realm_vassal_capital".equals(source)?"first_safe_same_realm_vassal_capital":"first_safe_ranked_exact_objective")),
                    f("route_hops",number(route(audit.get("route_province_ids")).orElseThrow().size())),f("objective_rank",number(rank)),f("evaluated_candidate_count",number(rank+1)),f("unevaluated_candidate_count",number(Math.max(0,candidates.size()-rank-1))))));break;
        }
        var selection=new LateRouteSelection(target,source,selectedAudit,rejected,transition,candidates,swept,defensiveHold,rally,refuge,root);
        return new MilitaryPlanningDecision.Keep(obj(f(LateRouteSelection.FIELD,selection.encode(c.request()))));
    }
    static Optional<Obj> preview(Context c,int target) {return freshPreview(c.request(),c.subject(),target).map(MilitaryPlanInputs::previewDocument);}
    static Obj audit(Context c,int target,List<Integer> route) {return auditDocument(MilitaryRouteGeometry.geometry(route,c.current(),target,c.enemies().stream().map(Army::geometry).toList()));}
    static String previewStep(Context c,int target) {return RouteReevaluationPlanner.previewStep(c.subject().id(),target);}
    static String query(Context c,int target) {return new MilitaryTimeline.Query(c.subject().id(),c.current(),target,c.hostileIds(),List.of()).step();}
    static String advance(Context c,int target) {return query(c,target).replaceFirst("^query-","advance-");}
    static Optional<MilitaryTimeline.Horizon> horizon(Context c,int target,List<Integer> route) {
        var lookup=MilitaryTimeline.fresh(c.request(),new MilitaryTimeline.Query(c.subject().id(),c.current(),target,c.hostileIds(),route));
        return lookup instanceof MilitaryTimeline.Found found?Optional.of(found.horizon()):Optional.empty();
    }
    static Optional<Obj> failure(Context c,int target,List<Integer> route) {return MilitaryTimeline.failure(c.request(),new MilitaryTimeline.Query(c.subject().id(),c.current(),target,c.hostileIds(),route));}
    static boolean unavoidable(MilitaryTimeline.Horizon h) {
        var subject=h.subject();boolean moving=!subject.provinceIds().isEmpty()&&subject.arrivalDates().getFirst()>h.horizonEnd();
        boolean stationary=subject.provinceIds().isEmpty()&&subject.arrivalDates().isEmpty()&&h.targetProvinceId()==subject.currentProvinceId()&&subject.effectiveOriginProvinceId()==subject.currentProvinceId();
        return !h.oneDayFree()&&!h.nativeConflicts().isEmpty()&&(moving||stationary)&&h.nativeConflicts().stream().allMatch(
                conflict->conflict instanceof MilitaryTimeline.SameProvince p&&p.provinceId()==subject.currentProvinceId()&&p.start()<=h.horizonEnd());
    }
    static Optional<Obj> rollback(Context c,int target,List<Integer> route) {
        Value plural=c.snapshot().get("native_rollback_war_failures");List<Obj> failures=plural instanceof Arr?rows(plural):
                c.snapshot().get("native_rollback_war_failure") instanceof Obj one?List.of(one):List.of();
        for(Obj f:failures) {
            if(!is(f,"status","rolled_back_active_route")||!Objects.equals(optionalInt(f.get("war_id")),c.published().tacticalWarId())
                    ||!Objects.equals(optionalInt(f.get("army_id")),c.subject().id())||!Objects.equals(optionalInt(f.get("restored_origin_province_id")),c.current())
                    ||!Objects.equals(optionalInt(f.get("route_origin_province_id")),c.current())||!Objects.equals(optionalInt(f.get("target_province_id")),target)
                    ||!(f.get("route_province_ids") instanceof Arr))continue;
            if(!MilitaryRouteGeometry.remaining(route(f.get("route_province_ids")).orElseThrow(),c.current()).equals(route))continue;
            String episode=optionalText(c.snapshot().get("episode_run_id")),old=optionalText(f.get("episode_run_id"));
            if(episode!=null&&old!=null&&!episode.equals(old))continue;return Optional.of(f);
        }
        return Optional.empty();
    }
    static boolean safe(Obj audit) {return is(audit,"status","safe")||is(audit,"status","safe_one_day_contact_horizon");}
    static boolean refugeSource(String source) {return "player_held_county_capital".equals(source)||"same_realm_vassal_capital".equals(source);}
    static Obj rejection(int target,String status) {return obj(f("target_province_id",number(target)),f("status",text(status)));}
    static MilitaryPlanningDecision available(Context c,String phase,String unsupported,String step,String reason,String missingReason,Field... extra) {
        return advertised(c.request(),step)?action(c,phase,step,reason,extra):hold(c,unsupported,step,missingReason,extra);
    }
    static MilitaryPlanningDecision required(Context c,String phase,String step,String reason,Field... extra) {
        return advertised(c.request(),step)?actionRequired(c,phase,step,reason,extra):hold(c,phase,step,reason,extra);
    }
    private static MilitaryPlanningDecision actionRequired(Context c,String phase,String step,String reason,Field... extra) {
        Field[] full=java.util.Arrays.copyOf(extra,extra.length+1);full[extra.length]=f("required_step",text(step));return action(c,phase,step,reason,full);
    }
    static MilitaryPlanningDecision action(Context c,String phase,String step,String reason,Field... extra) {
        require(advertised(c.request(),step),"actual advertised original military operation required");
        Obj detail=plan(c,phase,reason,step,extra);OrdinaryPolicy.Purpose purpose=step.startsWith("query-")||step.startsWith("preview-")?
                OrdinaryPolicy.Purpose.READ_ONLY:step.startsWith("advance-")||step.startsWith("life-advance")?OrdinaryPolicy.Purpose.DATE_ADVANCE:OrdinaryPolicy.Purpose.WORLD_ACTION;
        return new MilitaryPlanningDecision.Select("one-life-turn-v1",phase,reason,new OperationKey(step),empty(),purpose,detail);
    }
    static MilitaryPlanningDecision hold(Context c,String phase,String required,String reason,Field... extra) {
        Obj detail=plan(c,phase,reason,null,extra);if(required!=null)detail=put(detail,"required_step",text(required));
        return new MilitaryPlanningDecision.Hold("one-life-turn-v1",phase,reason,Optional.ofNullable(required).map(OperationKey::new),detail);
    }
    private static Obj plan(Context c,String phase,String reason,String step,Field... extra) {
        return merge(obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",step==null?Nil.INSTANCE:text(step)),
                f("reason",text(reason)),f("active_wars",objects(c.published().warSummaries()))),obj(extra));
    }
}
