package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Actual ordinary WarCore10212..10448/11760..12201. Selects plans, never invokes clock/Native/writer. */
public final class WarContactPolicy {
    private final WarContactHistory history;
    private final WarContactEpochs epochs;
    private final WarStrengthRelief relief;
    public WarContactPolicy(WarContactHistory history,WarStrengthRelief actualStrengthRelief) {
        this.history=Objects.requireNonNull(history);this.epochs=new WarContactEpochs(history);this.relief=Objects.requireNonNull(actualStrengthRelief);
    }
    public static WarContactObservation.Result collect(PlanningRequest request){return WarContactObservation.collect(request);}
    public static WarCorePlanner.TacticsResult collectTactics(PlanningRequest request) {
        var result=collect(request);
        if(result instanceof WarContactObservation.Incomplete missing)return new WarCorePlanner.UnknownTactics(missing.missing());
        var known=(WarContactObservation.KnownContact)result;known.requireSame(request);var c=known.context();
        if(!c.evidenceIssues().isEmpty())return new WarCorePlanner.UnknownTactics(List.of("complete-matching-active-army-routes"));
        if(c.globalRouteAudits().stream().anyMatch(a->a.status()==WarContactObservation.AuditStatus.UNAVAILABLE))
            return new WarCorePlanner.UnknownTactics(List.of("auditable-controlled-native-routes"));
        return new WarCorePlanner.KnownTactics(request.before(),new WarCorePlanner.RouteTactics(c.unsafeArmyIds(),c.threatenedStationaryArmyIds()));
    }
    public static WarStrengthRelief.ContactObservation strengthContact(PlanningRequest request) {
        var result=collect(request);
        if(result instanceof WarContactObservation.Incomplete missing)return new WarStrengthRelief.MissingContact(missing.missing());
        var known=(WarContactObservation.KnownContact)result;known.requireSame(request);var c=known.context();
        return new WarStrengthRelief.KnownContact(new WarStrengthRelief.ContactFacts(known.before(),c.controlledArmies(),c.pursuitArmy(),c.tacticalWarId()));
    }
    public static WarStrengthRelief.MovementEvidence movementEvidence(WarContactHistory history) {
        Objects.requireNonNull(history);
        return new WarStrengthRelief.MovementEvidence() {
            @Override public WarStrengthRelief.EvidenceLookup activeIntent(PlanningRequest r,int a,int p){return evidence(r,history.activeMoveIntent(r,a,p));}
            @Override public WarStrengthRelief.EvidenceLookup acceptedArrival(PlanningRequest r,int a,int p){return evidence(r,history.acceptedArrival(r,a,p));}
            @Override public WarStrengthRelief.EvidenceLookup observedErrorArrival(PlanningRequest r,int a,int p){return evidence(r,history.observedErrorArrival(r,a,p));}
        };
    }
    private static WarStrengthRelief.EvidenceLookup evidence(PlanningRequest request,WarContactHistory.Lookup value) {
        if(value instanceof WarContactHistory.Found found){found.requireSame(request);return new WarStrengthRelief.EvidenceFound(found.before(),found.evidence());}
        if(value instanceof WarContactHistory.Incomplete gap)return new WarStrengthRelief.EvidenceUnavailable(gap.missing());
        return new WarStrengthRelief.EvidenceAbsent();
    }
    public List<WarCorePlanner.Leaf> leaves(ExactRef actualImplementationSource) {
        return List.of(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.ROUTE_INGRESS,actualImplementationSource,this::ingress),
                new WarCorePlanner.Leaf(WarCorePlanner.Boundary.ACTIVE_ROUTE_CONTACT,actualImplementationSource,this::active));
    }
    public MilitaryPlanningDecision ingress(PlanningRequest request,OrdinaryPolicy.Draft current) {
        try {
            Obj s=request.observations().snapshot();Arr summaries=summary(request,current);
            boolean routes=WarContactObservation.flag(s,"army_routes_supported");
            boolean preview=WarContactObservation.flag(s,"move_route_preview_supported");
            boolean horizon=WarContactObservation.flag(s,"route_contact_horizon_supported");
            boolean pausedObjective=WarContactObservation.flag(s,"war_objective_garrison_supported")
                    |WarContactObservation.flag(s,"war_objective_siege_progress_supported")|WarContactObservation.flag(s,"war_objective_assault_supported");
            if((routes||preview||horizon||pausedObjective)&&!yes(s.get("paused")))
                return plan(request,"native_war_route_wait_for_pause","pause-map","pause the map before reading deep native route or objective state",
                        obj(f("required_step",text("pause-map"))),summaries,OrdinaryPolicy.Purpose.WORLD_ACTION);
            if(preview&&!routes&&!WarContactObservation.objectives(wars(request)).isEmpty())
                return hold("native_war_route_monitoring_unsupported","game.state.army-routes",
                        "route preview without passive army routes cannot safely monitor a submitted march as enemy positions change",empty(),summaries);
            var result=collect(request);
            if(result instanceof WarContactObservation.Incomplete gap)return unavailable(gap.missing());
            var known=(WarContactObservation.KnownContact)result;known.requireSame(request);var c=known.context();
            summaries=annotatedSummary(request,summaries,c);
            if(!c.evidenceIssues().isEmpty())return hold("native_war_route_evidence_blocked","observable-complete-army-routes",
                    "at least one controllable or non-retreating hostile active route lacks an exact target and complete matching endpoint; keep the map paused",
                    obj(f("route_evidence_issues",objects(c.evidenceIssues()))),summaries);
            if(c.globalRouteAudits().stream().anyMatch(a->a.status()==WarContactObservation.AuditStatus.UNAVAILABLE))
                return hold("native_war_route_audit_pending","game.state.army-routes",
                        "at least one controllable active route is incomplete; do not advance or mutate any army until every route is auditable",
                        obj(f("route_audits",objects(c.globalRouteAudits().stream().map(WarContactObservation.RouteAudit::detail).toList()))),summaries);
            return new MilitaryPlanningDecision.Keep(obj(f("active_wars",summaries)));
        } catch(IllegalArgumentException|java.util.NoSuchElementException invalid){return unavailable(List.of(Objects.toString(invalid.getMessage(),"contact ingress input missing")));}
    }
    private Arr annotatedSummary(PlanningRequest request,Arr summaries,WarContactObservation.Context context) {
        List<Obj> endpoints=epochs.observe(request);List<Obj> out=new ArrayList<>();
        for(Value value:summaries.items()) {
            Obj row=OpportunityJson.object(value,"original active war summary");Integer id=optionalInt(row.get("war_id"));
            row=put(row,"enemy_endpoint_epochs",objects(endpoints.stream().filter(e->Objects.equals(optionalInt(e.get("war_id")),id)).toList()));
            if(context.replenishmentSelection().isPresent()) {
                Obj selected=context.replenishmentSelection().orElseThrow();
                if(!new Text("not_applicable").equals(selected.get("status"))&&selected.get("active_war_ids") instanceof Arr a
                        &&a.items().contains(id==null?Nil.INSTANCE:number(id)))row=put(row,"current_replenishment_selection_v1",selected);
            }
            out.add(row);
        }
        return objects(out);
    }
    public sealed interface ContinuationResult permits Continuation,ContinuationUnavailable {}
    public record Continuation(WarContactObservation.KnownContact contact,Optional<Obj> passiveRouteAudit,
            Set<Integer> blockedProvinceIds,Optional<Obj> moveIntent,Optional<Integer> selectedWar) implements ContinuationResult {
        public Continuation {
            Objects.requireNonNull(contact);Objects.requireNonNull(passiveRouteAudit);blockedProvinceIds=Set.copyOf(blockedProvinceIds);
            Objects.requireNonNull(moveIntent);Objects.requireNonNull(selectedWar);
        }
        public void requireSame(PlanningRequest request){contact.requireSame(request);}
    }
    public record ContinuationUnavailable(List<String> missing) implements ContinuationResult {
        public ContinuationUnavailable {missing=List.copyOf(missing);require(!missing.isEmpty(),"exact active-contact continuation gap");}
    }
    private record Evaluation(MilitaryPlanningDecision decision,Optional<Continuation> continuation) {}
    public MilitaryPlanningDecision active(PlanningRequest request,OrdinaryPolicy.Draft current){return evaluateActive(request,current).decision();}
    /** Late fallback consumes the actual preceding source decisions, never caller-classified route status. */
    public ContinuationResult continuation(PlanningRequest request,OrdinaryPolicy.Draft current) {
        Evaluation evaluated=evaluateActive(request,current);
        return evaluated.continuation().<ContinuationResult>map(v->v).orElseGet(()->new ContinuationUnavailable(
                evaluated.decision() instanceof MilitaryPlanningDecision.Unavailable gap?gap.missing():List.of("active-contact-earlier-guard-selected")));
    }
    private Evaluation evaluateActive(PlanningRequest request,OrdinaryPolicy.Draft current) {
        try {
            var result=collect(request);
            if(result instanceof WarContactObservation.Incomplete gap)return chosen(unavailable(gap.missing()));
            var known=(WarContactObservation.KnownContact)result;known.requireSame(request);var c=known.context();
            if(!c.evidenceIssues().isEmpty()||c.globalRouteAudits().stream().anyMatch(a->a.status()==WarContactObservation.AuditStatus.UNAVAILABLE))
                return chosen(unavailable(List.of("route-ingress-must-complete-before-active-contact")));
            var selected=relief.collect(request);
            if(selected.isEmpty())return chosen(unavailable(List.of("actual-same-frame-strength-relief-context")));
            var actual=selected.orElseThrow();require(actual.before().equals(request.before()),"relief selection crossed frame");
            Optional<Army> pursuit=actual.selectedArmy();Optional<Integer> selectedWar=actual.selectedWar();
            require(pursuit.isEmpty()||c.controlledArmies().contains(pursuit.orElseThrow()),"relief selected unobserved Army");
            Arr summaries=summary(request,current);Optional<Obj> audit=Optional.empty(),intent=Optional.empty();Set<Integer> blocked=new HashSet<>();
            if(pursuit.isEmpty()||pursuit.orElseThrow().target()==null)
                return kept(known,audit,blocked,intent,selectedWar,empty());
            Army army=pursuit.orElseThrow();int target=army.target();
            var pending=WarContactHalts.pending(request,army);
            if(pending.isPresent()&&!yes(pending.orElseThrow().get("suffix_cancellation_observed")))
                return chosen(holdObservation("native_war_unsafe_route_halt_pending","fresh-native-army-route-clear-after-halt",
                        "the native halt was submitted in this game day; wait for a fresh route and target readback before another command or time advance",
                        obj(f("halt_submission",pending.orElseThrow())),summaries));
            var movement=history.activeMoveIntent(request,army.id(),target);
            if(movement instanceof WarContactHistory.Incomplete gap)return chosen(unavailable(gap.missing()));
            if(movement instanceof WarContactHistory.Found found){found.requireSame(request);intent=Optional.of(found.evidence());}
            if(WarContactObservation.flag(request.observations().snapshot(),"army_routes_supported")) {
                var global=c.globalRouteAudits().stream().filter(a->a.armyId()==army.id()
                        &&Objects.equals(optionalInt(a.detail().get("target_province_id")),target)).findFirst();
                var passive=global.orElseGet(()->WarContactObservation.audit(army,c.completeRouteThreatEnemies()));audit=Optional.of(passive.detail());
                if(passive.status()==WarContactObservation.AuditStatus.UNAVAILABLE)
                    return chosen(hold("native_war_route_audit_pending","game.state.army-routes",
                            "the accepted move has no complete passive route yet; do not advance into an unaudited path",
                            obj(f("route_audit",passive.detail())),summaries));
                if(passive.status()==WarContactObservation.AuditStatus.SAFE||passive.status()==WarContactObservation.AuditStatus.UNSAFE) {
                    boolean scope=WarContactObservation.flag(request.observations().snapshot(),"route_contact_horizon_supported")
                            &&!c.hostileArmyIds().isEmpty()&&c.hostileArmyIds().size()<=64;
                    if(!scope) {
                        Optional<Obj> retreatWatch=retreatingOnly(request,army,passive.detail(),intent,c,summaries);
                        if(retreatWatch.isPresent())return chosen(fromPlan(request,retreatWatch.orElseThrow(),OrdinaryPolicy.Purpose.DATE_ADVANCE));
                        return chosen(holdObservation("native_war_active_route_contact_horizon_unsupported","fresh-full-hostile-route-contact-horizon",
                                "an already committed route may advance only from a fresh same-frame one-day proof over the complete hostile scope; keep time paused",
                                obj(f("route_audit",passive.detail()),f("move_intent",intent.<Value>map(v->v).orElse(Nil.INSTANCE))),summaries));
                    }
                    require(army.current()!=null&&army.current()>0&&army.route().isPresent(),"active route current Province and complete route");
                    var q=new MilitaryTimeline.Query(army.id(),army.current(),target,c.hostileArmyIds(),army.route().orElseThrow());
                    var lookup=MilitaryTimeline.fresh(request,q);
                    if(!(lookup instanceof MilitaryTimeline.Found found)) {
                        var failed=MilitaryTimeline.failure(request,q);
                        if(lookup instanceof MilitaryTimeline.Malformed malformed)
                            return chosen(hold("native_war_active_route_contact_horizon_unavailable",q.step(),
                                    "the fresh full-hostile contact query failed in this unchanged frame; keep time paused without resubmitting",
                                    obj(f("route_audit",passive.detail()),f("malformed_contact_horizon",malformed.original())),summaries));
                        if(failed.isPresent()) {
                            var watch=WarContactHalts.unavailableWatch(request,army,q,pending,failed.orElseThrow(),summaries);
                            if(watch.isPresent())return chosen(fromPlan(request,watch.orElseThrow(),watch.orElseThrow().get("selected_step").equals(text("life-advance-one-day"))
                                    ?OrdinaryPolicy.Purpose.DATE_ADVANCE:OrdinaryPolicy.Purpose.WORLD_ACTION));
                            return chosen(hold("native_war_active_route_contact_horizon_unavailable",q.step(),
                                    "the fresh full-hostile contact query failed in this unchanged frame; keep time paused without resubmitting",
                                    obj(f("route_audit",passive.detail()),f("contact_query_attempt",failed.orElseThrow()),
                                            f("move_intent",intent.<Value>map(v->v).orElse(Nil.INSTANCE))),summaries));
                        }
                        return chosen(plan(request,has(request,q.step())?"native_war_route_contact_horizon":"native_war_route_contact_horizon_unsupported",q.step(),
                                has(request,q.step())?"read the exact one-day native arrival/contact horizon over the full hostile scope before advancing the committed route":
                                "the committed route requires a fresh same-frame full-hostile one-day contact horizon",
                                obj(f("route_audit",passive.detail()),f("move_intent",intent.<Value>map(v->v).orElse(Nil.INSTANCE))),summaries,OrdinaryPolicy.Purpose.READ_ONLY));
                    }
                    MilitaryTimeline.Horizon h=found.horizon();
                    if(h.oneDayFree()) {
                        Obj safe=merge(passive.detail(),obj(f("status",text("safe_one_day_contact_horizon")),f("contact_horizon",h.original())));
                        var conjunction=WarContactWindows.conjunction(request,known,h);
                        if(!conjunction.missing().isEmpty()) {
                            Obj missing=conjunction.missing().getFirst();String step=optionalText(missing.get("query_step"));
                            if(step!=null&&has(request,step))return chosen(plan(request,"native_war_sibling_route_contact_horizon",step,
                                    "the main route proof cannot cover another moving army's closed current-Province occupancy; query that sibling's own exact one-day timeline before advancing global time",
                                    obj(f("route_audit",safe),f("moving_contact_horizons",conjunction.toJson())),summaries,OrdinaryPolicy.Purpose.READ_ONLY));
                            return chosen(hold("native_war_sibling_route_contact_horizon_unsupported",step,
                                    "another moving army requires its own exact one-day contact horizon, but the current backend does not advertise that query",
                                    obj(f("route_audit",safe),f("moving_contact_horizons",conjunction.toJson())),summaries));
                        }
                        if(!conjunction.unavailable().isEmpty())return chosen(hold("native_war_sibling_route_contact_horizon_unavailable",
                                optionalText(conjunction.unavailable().getFirst().get("query_step")),
                                "the sibling's own route-contact query was already attempted in this unchanged frame but did not yield a usable exact proof; keep time paused without resubmitting it",
                                obj(f("route_audit",safe),f("moving_contact_horizons",conjunction.toJson())),summaries));
                        if(!conjunction.conflicting().isEmpty())return chosen(hold("native_war_sibling_route_contact_horizon_conflict","safe-exact-war-route",
                                "a sibling moving army has a malformed route or a fresh timed conflict that is not the narrow unavoidable current-Province transition",
                                obj(f("route_audit",safe),f("moving_contact_horizons",conjunction.toJson())),summaries));
                        Set<Integer> covered=new HashSet<>();
                        for(Obj row:conjunction.covered())covered.add(id(row.get("army_id")));
                        for(Obj row:conjunction.unavoidable())covered.add(id(row.get("army_id")));
                        List<Army> otherUnsafe=c.controlledArmies().stream().filter(a->a.id()!=army.id()&&c.unsafeArmyIds().contains(a.id())&&!covered.contains(a.id())).toList();
                        List<Army> stationary=new ArrayList<>();List<Obj> stationaryProofs=new ArrayList<>();
                        for(Army a:c.controlledArmies().stream().filter(a->c.threatenedStationaryArmyIds().contains(a.id()))
                                .sorted(java.util.Comparator.comparingInt(Army::id)).toList()) {
                            if(a.current()==null||!WarContactWindows.stationaryFree(h,a.current())){stationary.add(a);continue;}
                            stationaryProofs.add(obj(f("army_id",number(a.id())),f("current_province_id",number(a.current())),
                                    f("proof_subject_army_id",number(army.id())),f("horizon_start_date_raw",number(h.horizonStart())),
                                    f("horizon_end_date_raw",number(h.horizonEnd())),f("one_day_contact_free",new Bool(true))));
                        }
                        boolean otherCombat=c.controlledArmies().stream().anyMatch(a->a.id()!=army.id()&&List.of("combat","retreating").contains(Objects.toString(a.tacticalState(),"")));
                        if(!otherUnsafe.isEmpty()||!stationary.isEmpty()||otherCombat)
                            return chosen(hold("native_war_route_contact_horizon_global_blocked","complete-global-route-contact-horizon",
                                    "one army's contact-free horizon cannot authorize time while another controllable army remains unsafe or threatened",
                                    obj(f("route_audit",safe),f("other_unsafe_armies",objects(otherUnsafe.stream().map(Army::raw).toList())),
                                            f("threatened_stationary_armies",objects(stationary.stream().map(Army::raw).toList())),
                                            f("stationary_contact_horizons",objects(stationaryProofs))),summaries));
                        if(!conjunction.unavoidable().isEmpty())return chosen(holdObservation("native_war_active_route_contact_blocked",
                                "qualified-combat-permission-or-safe-route",
                                "a sibling's fresh horizon predicts contact; one contact-free subject proof cannot authorize global time without a qualified combat result",
                                obj(f("route_audit",safe),f("stationary_contact_horizons",objects(stationaryProofs)),
                                        f("moving_contact_horizons",conjunction.toJson())),summaries));
                        String step=WarContactWindows.advanceStep(q);int days=1;
                        for(int candidate:List.of(3,2))if(has(request,WarContactWindows.windowStep(q,candidate))){step=WarContactWindows.windowStep(q,candidate);days=candidate;break;}
                        if(has(request,step))return chosen(plan(request,"native_war_route_contact_horizon_progress",step,
                                "same-frame complete timelines cover "+days+" day(s); the watched native clock stops on actual arrival, target, combat, retreat or pause changes",
                                obj(f("route_contact_window_days",number(days)),f("route_audit",safe),f("stationary_contact_horizons",objects(stationaryProofs)),
                                        f("moving_contact_horizons",conjunction.toJson()),f("move_intent",intent.<Value>map(v->v).orElse(Nil.INSTANCE))),summaries,OrdinaryPolicy.Purpose.DATE_ADVANCE));
                        return chosen(hold("native_war_route_contact_horizon_progress_unsupported",step,
                                "the exact route is contact-free for one day but this backend cannot advance it",obj(f("route_audit",safe)),summaries));
                    }
                    Obj unsafe=merge(passive.detail(),obj(f("contact_horizon",h.original()),f("contact_policy",text("blocked_without_qualified_combat_permission"))));
                    audit=Optional.of(unsafe);blocked.add(target);
                    if(pending.isEmpty()) {
                        var halt=WarContactHalts.unsafeHalt(request,army,unsafe,h,summaries);
                        if(halt.isPresent())return chosen(fromPlan(request,halt.orElseThrow(),OrdinaryPolicy.Purpose.WORLD_ACTION));
                    }
                }
            } else if(intent.isPresent()&&c.completeRouteThreatEnemies().stream()
                    .noneMatch(a->Objects.equals(a.current(),target)||Objects.equals(a.target(),target))) {
                String source=selectedWar.flatMap(w->wars(request).stream().filter(row->id(row.get("war_id"))==w).findFirst())
                        .filter(w->WarContactObservation.objectives(List.of(w)).contains(target)).isPresent()
                        ?"war_objective_province":"enemy_primary_default_raise_province";
                Obj pursuitDetail=obj(f("war_id",selectedWar.<Value>map(MilitaryPlanInputs::number).orElse(Nil.INSTANCE)),
                        f("army_id",number(army.id())),f("target_army_id",Nil.INSTANCE),f("target_province_id",number(target)),
                        f("target_soldiers",Nil.INSTANCE),f("target_source",text(source)),f("objective_kind",text("siege")));
                return chosen(plan(request,has(request,"life-advance")?"native_war_pursuit_progress":"native_war_pursuit_progress_unsupported","life-advance",
                        has(request,"life-advance")?"the accepted native route is still observable and safe; finish it before reconsidering siege priority":
                                "the accepted native siege route is active but this backend cannot advance it",
                        obj(f("pursuit",pursuitDetail),f("move_intent",intent.orElseThrow())),summaries,OrdinaryPolicy.Purpose.DATE_ADVANCE));
            }
            Obj annotations=empty();if(audit.isPresent())annotations=put(annotations,"route_audit",audit.orElseThrow());
            return kept(known,audit,blocked,intent,selectedWar,annotations);
        }catch(IllegalArgumentException|java.util.NoSuchElementException invalid){return chosen(unavailable(List.of(Objects.toString(invalid.getMessage(),"active contact input missing"))));}
    }
    private static Evaluation kept(WarContactObservation.KnownContact known,Optional<Obj> audit,Set<Integer> blocked,
            Optional<Obj> intent,Optional<Integer> selectedWar,Obj annotations) {
        return new Evaluation(new MilitaryPlanningDecision.Keep(annotations),Optional.of(new Continuation(known,audit,blocked,intent,selectedWar)));
    }
    private static Evaluation chosen(MilitaryPlanningDecision decision){return new Evaluation(decision,Optional.empty());}
    private static boolean has(PlanningRequest request,String step){return request.observations().actionSteps().contains(new OperationKey(step));}
    private static Arr summary(PlanningRequest request,OrdinaryPolicy.Draft current) {
        if(current.detail().get("active_wars") instanceof Arr a)return a;
        return objects(wars(request));
    }
    private static MilitaryPlanningDecision unavailable(List<String> dependencies) {
        return new MilitaryPlanningDecision.Unavailable(dependencies,"actual military contact input is incomplete");
    }
    private static MilitaryPlanningDecision hold(String phase,String required,String reason,Obj detail,Arr summaries) {
        Obj full=merge(detail,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",Nil.INSTANCE),
                f("reason",text(reason)),f("active_wars",summaries)));
        if(required!=null)full=put(full,"required_step",text(required));
        return new MilitaryPlanningDecision.Hold("one-life-turn-v1",phase,reason,required==null?Optional.empty():Optional.of(new OperationKey(required)),full);
    }
    private static MilitaryPlanningDecision holdObservation(String phase,String required,String reason,Obj detail,Arr summaries) {
        return hold(phase,null,reason,merge(detail,obj(f("required_observation",text(required)))),summaries);
    }
    private static MilitaryPlanningDecision plan(PlanningRequest request,String phase,String step,String reason,Obj detail,Arr summaries,OrdinaryPolicy.Purpose purpose) {
        if(!has(request,step))return hold(phase,step,reason,detail,summaries);
        return fromPlan(request,WarContactHalts.plan(phase,step,reason,detail,summaries),purpose);
    }
    private static MilitaryPlanningDecision fromPlan(PlanningRequest request,Obj full,OrdinaryPolicy.Purpose purpose) {
        String step=OpportunityJson.text(full.get("selected_step"),"exact contact plan selection");
        require(has(request,step),"original step is not advertised");
        return new MilitaryPlanningDecision.Select(OpportunityJson.text(full.get("policy"),"policy"),OpportunityJson.text(full.get("phase"),"phase"),
                OpportunityJson.text(full.get("reason"),"reason"),new OperationKey(step),empty(),purpose,full);
    }
    private static Optional<Obj> retreatingOnly(PlanningRequest request,Army army,Obj audit,Optional<Obj> intent,
            WarContactObservation.Context context,Arr summaries) {
        Obj s=request.observations().snapshot();Obj player=s.get("played_character") instanceof Obj p?p:null;
        if(!yes(s.get("paused"))||!yes(s.get("map_ready"))||!yes(s.get("route_contact_horizon_supported"))
                ||s.get("active_event")!=Nil.INSTANCE||s.get("pending_character_interaction")!=Nil.INSTANCE||request.observations().foregroundPresent()
                ||player==null||!yes(player.get("alive"))||!(s.get("player_armies") instanceof Arr a)||a.items().size()!=1||!a.items().getFirst().equals(army.raw())
                ||!army.controllable()||!Objects.equals(army.raw().get("owner_character_id"),player.get("character_id"))
                ||!Boolean.FALSE.equals(army.inCombat())||!Boolean.FALSE.equals(army.retreating())||!"moving".equals(army.state())
                ||!Integer.valueOf(7).equals(army.stateCode())||!yes(army.raw().get("move_target_observable"))
                ||!"complete_nonempty".equals(army.routeReadStatus())||army.route().filter(v->!v.isEmpty()&&v.getLast().equals(army.target())).isEmpty()
                ||!new Text("safe").equals(audit.get("status"))||intent.isEmpty()||!new Text("active").equals(intent.orElseThrow().get("status"))
                ||!context.hostileArmyIds().isEmpty()||!has(request,"life-advance-one-day"))return Optional.empty();
        Set<Integer> ids=new java.util.TreeSet<>();
        for(Obj war:wars(request))for(Obj enemy:MilitaryPlanInputs.rows(war.get("enemy_armies"))) {
            if(!yes(enemy.get("retreating"))||!no(enemy.get("in_combat")))return Optional.empty();ids.add(id(enemy.get("army_id")));
        }
        if(ids.isEmpty())return Optional.empty();
        return Optional.of(WarContactHalts.plan("native_war_retreating_only_committed_route_one_day_observation","life-advance-one-day",
                "all published enemies are explicitly retreating; observe one exact Native day of the already committed route, then re-read battle and hostile state without claiming contact safety",
                obj(f("route_audit",audit),f("move_intent",intent.orElseThrow()),f("retreating_enemy_army_ids",numbers(ids.stream().toList())),
                        f("contact_free_proven",new Bool(false)),f("movement_resubmitted",new Bool(false)),f("offensive_combat_permission",new Bool(false)),
                        f("war_or_material_credit",new Bool(false)),f("max_observation_days",number(1))),summaries));
    }
}

