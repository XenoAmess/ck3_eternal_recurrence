package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual early WarCore factories. Main call order remains exclusively in WarCorePlanner. */
public final class EarlyWarCoreLeaves {
    private EarlyWarCoreLeaves() { }
    public record Sources(ExactRef early,ExactRef contact,ExactRef siegeDaily) {
        public Sources {Objects.requireNonNull(early);Objects.requireNonNull(contact);Objects.requireNonNull(siegeDaily);}
    }
    /** Seven real factories; combat/retreat and rendezvous remain their independent actual owner inputs. */
    public static List<WarCorePlanner.Leaf> factories(Sources sources,EarlyWarCoreInputs inputs) {
        Objects.requireNonNull(sources);Objects.requireNonNull(inputs);
        List<WarCorePlanner.Leaf> leaves=new ArrayList<>();
        leaves.add(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.DEFAULT_RAISE_AND_PRIMARY_IDENTITY,sources.early(),EarlyWarCoreLeaves::defaultRaise));
        leaves.addAll(inputs.contactPolicy().leaves(sources.contact()));
        leaves.add(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.STRENGTH_AND_RELIEF,sources.early(),(request,current)->strength(request,current,inputs)));
        leaves.addAll(WarSiegeDaily.factories(sources.siegeDaily(),inputs::capture));
        leaves.add(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.OBJECTIVE_SOURCE_SELECTION,sources.early(),(request,current)->objectives(request,current,inputs)));
        require(leaves.size()==7&&leaves.stream().map(WarCorePlanner.Leaf::boundary).distinct().count()==7,"seven unique actual early producers required");
        return List.copyOf(leaves);
    }
    /** One concrete installation of all nine early boundaries, including the independent actual battle producer. */
    public static List<WarCorePlanner.Leaf> completeFactories(Sources sources,ExactRef battleCoreSource,EarlyWarCoreInputs inputs) {
        List<WarCorePlanner.Leaf> complete=new ArrayList<>(factories(sources,inputs));
        complete.addAll(WarBattleControlCore.factories(Objects.requireNonNull(battleCoreSource),inputs::capture));
        var expected=java.util.EnumSet.range(WarCorePlanner.Boundary.DEFAULT_RAISE_AND_PRIMARY_IDENTITY,WarCorePlanner.Boundary.OBJECTIVE_SOURCE_SELECTION);
        require(complete.size()==9&&complete.stream().map(WarCorePlanner.Leaf::boundary).collect(java.util.stream.Collectors.toSet()).equals(expected),"every actual early boundary must be installed exactly once");
        return List.copyOf(complete);
    }
    public static MilitaryPlanningDecision defaultRaise(PlanningRequest request,OrdinaryPolicy.Draft current) {
        try {
            if(!request.observations().warInProgress())return new MilitaryPlanningDecision.Keep(empty());
            List<Obj> summaries=EarlyWarCoreInputs.summary(request,current);
            for(Obj summary:summaries)if(summary.get("player_is_primary_war_leader")!=null&&summary.get("player_is_primary_war_leader")!=Nil.INSTANCE)
                org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(summary.get("player_is_primary_war_leader"),"actual primary War leader");
            if(armies(request).stream().noneMatch(Army::controllable))return select(request,"native_war_raise","raise-troops-default",
                    "an active war has no controllable army; raise troops at the native default rally point",empty(),summaries,OrdinaryPolicy.Purpose.WORLD_ACTION);
            List<Obj> unknown=summaries.stream().filter(r->new Text("defender").equals(r.get("player_side"))
                    &&(r.get("player_is_primary_war_leader")==null||r.get("player_is_primary_war_leader")==Nil.INSTANCE)).toList();
            if(!unknown.isEmpty())return hold("defensive_war_primary_identity_required",null,
                    "the defensive war's primary-leader identity must be observable before issuing further army or time commands",
                    obj(f("required_capabilities",strings(List.of("game.state.active-wars"))),f("defensive_wars",objects(unknown))),summaries);
            return new MilitaryPlanningDecision.Keep(empty());
        }catch(IllegalArgumentException invalid){return unavailable(invalid);}
    }
    public static MilitaryPlanningDecision strength(PlanningRequest request,OrdinaryPolicy.Draft current,EarlyWarCoreInputs inputs) {
        try {
            var collected=WarContactObservation.collect(request);
            if(collected instanceof WarContactObservation.Incomplete missing)return new MilitaryPlanningDecision.Unavailable(missing.missing(),"actual strength route inputs unavailable");
            var observed=(WarContactObservation.KnownContact)collected;observed.requireSame(request);var c=observed.context();
            require(c.evidenceIssues().isEmpty()&&c.globalRouteAudits().stream().noneMatch(a->a.status()==WarContactObservation.AuditStatus.UNAVAILABLE),"route ingress must precede strength");
            List<Obj> summaries=EarlyWarCoreInputs.summary(request,current);Obj snapshot=request.observations().snapshot();
            Integer war=c.tacticalWarId().orElse(null);Optional<Balance> measured=war==null?Optional.empty():balance(request,war);
            boolean absent=snapshot.get("army_strengths_status")==null||snapshot.get("army_strengths_status")==Nil.INSTANCE;
            Obj battle=BattleControlTurnState.collect(request);
            Optional<WarStrengthRelief.ReliefContext> relief=inputs.strengthPolicy().collect(request);
            if(measured.isEmpty()&&absent&&c.controlledArmies().size()==1&&c.pursuitArmy().isPresent()
                    &&c.pursuitArmy().orElseThrow().equals(c.controlledArmies().getFirst())
                    &&"moving".equals(c.pursuitArmy().orElseThrow().tacticalState())&&c.threatenedStationaryArmyIds().isEmpty()
                    &&yes(snapshot.get("army_routes_supported"))&&yes(snapshot.get("route_contact_horizon_supported"))
                    &&request.observations().paused()&&request.observations().mapReady()&&!c.hostileArmyIds().isEmpty()&&c.hostileArmyIds().size()<=64
                    &&new Text("not_in_combat").equals(battle.get("status"))&&relief.isPresent()
                    &&new Text("not_applicable").equals(relief.orElseThrow().assessment().get("status"))
                    &&WarSiegeDaily.reviews(request,c.completeRouteThreatEnemies()).isEmpty()) {
                Optional<MilitaryPlanningDecision> first=movingContactFirst(request,c,summaries);
                if(first.isPresent())return first.orElseThrow();
            }
            boolean refill=c.replenishmentSelection().filter(r->yes(r.get("query_needed"))).isPresent();
            if(war!=null&&(!c.hostileArmyIds().isEmpty()||refill)&&measured.isEmpty()&&absent&&request.observations().paused()
                    &&has(request,"query-army-strengths")&&c.controlledArmies().stream().noneMatch(a->Set.of("combat","retreating","gathering").contains(Objects.toString(a.tacticalState(),""))))
                return select(request,"native_war_army_strength_query","query-army-strengths",
                        "read the exact current soldiers and native AI base power and current refill inputs before choosing equal-strength idle stacks or committing an offensive route",
                        obj(f("required_step",text("query-army-strengths")),f("war_id",number(war)),
                                f("army_strength_scope",obj(f("player_army_ids",numbers(c.controlledArmies().stream().map(Army::id).sorted().toList())),
                                        f("enemy_army_ids",numbers(c.hostileArmyIds()))))),summaries,OrdinaryPolicy.Purpose.READ_ONLY);
            if(relief.isEmpty())return new MilitaryPlanningDecision.Unavailable(List.of("actual-siege-relief-collector"),"same-frame relief unavailable");
            var actual=relief.orElseThrow();require(actual.before().equals(request.before()),"strength relief crossed frame");
            if(new Text("observation_unavailable").equals(actual.assessment().get("status"))) {
                Optional<MilitaryPlanningDecision> waiting=WarReliefWaiting.plan(request,c,actual.assessment(),battle,summaries);
                if(waiting.isPresent())return waiting.orElseThrow();
                return hold("native_war_defender_siege_relief_observation_blocked",null,
                        "an enemy siege is visible but same-frame army assignment, hostile position, route, or strength is incomplete; do not consume another stationary hold slice",
                        obj(f("required_observation",nullable(actual.assessment().get("required_observation"))),f("siege_relief",actual.assessment())),summaries);
            }
            war=actual.selectedWar().orElse(war);measured=war==null?Optional.empty():balance(request,war);
            if(measured.isPresent()) {
                int selected=war;Obj original=measured.orElseThrow().original();
                summaries=summaries.stream().map(r->Integer.valueOf(selected).equals(optionalInt(r.get("war_id")))?put(r,"army_strength_balance",original):r).toList();
                Optional<Obj> consolidation=consolidation(request,c.controlledArmies(),war);
                if(consolidation.isPresent()) {
                    Obj result=consolidation.orElseThrow();String step=optionalText(result.get("step"));
                    if(step!=null&&has(request,step))return select(request,"native_war_preoffensive_army_consolidation",step,
                            "the exact post-declaration strength query shows same-province idle stacks; merge the strongest stack with one sibling before an offensive route",
                            obj(f("war_id",number(war)),f("consolidation",result),f("army_strength_balance",original)),summaries,OrdinaryPolicy.Purpose.WORLD_ACTION);
                }
            }
            return new MilitaryPlanningDecision.Keep(obj(f("active_wars",objects(summaries))));
        }catch(IllegalArgumentException|java.util.NoSuchElementException invalid){return unavailable(invalid);}
    }
    private static Optional<MilitaryPlanningDecision> movingContactFirst(PlanningRequest request,WarContactObservation.Context c,List<Obj> summaries) {
        Army army=c.pursuitArmy().orElseThrow();Integer origin=army.current(),target=army.target();
        if(origin==null||origin<=0||target==null||target<=0||target.equals(origin)||army.route().isEmpty()||army.route().orElseThrow().isEmpty())return Optional.empty();
        Optional<Obj> audit=c.globalRouteAudits().stream().filter(a->a.armyId()==army.id()
                &&(a.status()==WarContactObservation.AuditStatus.SAFE||a.status()==WarContactObservation.AuditStatus.UNSAFE)
                &&Integer.valueOf(target).equals(optionalInt(a.detail().get("target_province_id")))).map(WarContactObservation.RouteAudit::detail).findFirst();
        if(audit.isEmpty())return Optional.empty();
        var query=new MilitaryTimeline.Query(army.id(),origin,target,c.hostileArmyIds(),army.route().orElseThrow());
        var proof=MilitaryTimeline.fresh(request,query);
        if(!(proof instanceof MilitaryTimeline.Found found)) {
            if(has(request,query.step())&&MilitaryTimeline.failure(request,query).isEmpty())return Optional.of(select(request,
                    "native_war_moving_contact_before_strength_query",query.step(),
                    "read the existing same-frame complete hostile one-day contact proof before the full army-strength scope; no time or route action is dispatched",
                    obj(f("route_audit",audit.orElseThrow())),summaries,OrdinaryPolicy.Purpose.READ_ONLY));
            return Optional.empty();
        }
        if(!found.horizon().oneDayFree())return Optional.empty();
        String step=WarContactWindows.advanceStep(query);if(!has(request,step))return Optional.empty();int days=1;
        for(int candidate:List.of(3,2))if(has(request,WarContactWindows.windowStep(query,candidate))){step=WarContactWindows.windowStep(query,candidate);days=candidate;break;}
        return Optional.of(select(request,"native_war_moving_contact_before_strength_progress",step,
                "same-frame complete hostile timelines admit the sole moving army's bounded watched advance; replan at the actual native stop",
                obj(f("route_contact_window_days",number(days)),f("route_audit",put(audit.orElseThrow(),"contact_horizon",found.horizon().original()))),summaries,OrdinaryPolicy.Purpose.DATE_ADVANCE));
    }
    public static Optional<Obj> consolidation(PlanningRequest request,List<Army> controlled,int war) {
        if(!request.observations().paused()||controlled.size()<2)return Optional.empty();
        Set<Integer> provinces=new java.util.HashSet<>();controlled.forEach(a->provinces.add(a.current()));
        if(provinces.size()!=1||provinces.contains(null)||controlled.stream().anyMatch(a->!"regular".equals(a.tacticalState())
                ||Boolean.TRUE.equals(a.inCombat())||Boolean.TRUE.equals(a.retreating())||a.target()!=null||a.route().isEmpty()||!a.route().orElseThrow().isEmpty()))return Optional.empty();
        Obj snapshot=request.observations().snapshot();Map<Integer,BigInteger> soldiers=new LinkedHashMap<>();
        for(Obj row:rows(snapshot.get("army_strengths")))if(new Text("available").equals(row.get("status"))&&new Text("player").equals(row.get("scope_role"))
                &&row.get("war_ids") instanceof Arr&&ids(row.get("war_ids")).contains(war)&&optionalInteger(row.get("current_soldiers"))!=null)
            soldiers.put(id(row.get("army_id")),optionalInteger(row.get("current_soldiers")));
        if(!soldiers.keySet().equals(controlled.stream().map(Army::id).collect(java.util.stream.Collectors.toSet())))return Optional.empty();
        List<Integer> ordered=soldiers.keySet().stream().sorted(Comparator.<Integer,BigInteger>comparing(soldiers::get).reversed().thenComparingInt(Integer::intValue)).toList();
        int destination=ordered.getFirst(),source=ordered.get(1);
        return Optional.of(obj(f("status",text("ready")),f("war_id",number(war)),f("province_id",number(provinces.iterator().next())),
                f("destination_army_id",number(destination)),f("destination_current_soldiers",number(soldiers.get(destination))),
                f("source_army_id",number(source)),f("source_current_soldiers",number(soldiers.get(source))),
                f("remaining_player_army_ids",numbers(ordered.subList(2,ordered.size()))),f("step",text("merge-armies-"+destination+"-with-"+source))));
    }
    private static MilitaryPlanningDecision objectives(PlanningRequest request,OrdinaryPolicy.Draft current,EarlyWarCoreInputs inputs) {
        var capture=inputs.capture(request,current);
        if(capture instanceof EarlyWarCoreInputs.Unavailable missing)return new MilitaryPlanningDecision.Unavailable(missing.missing(),"actual objective source unavailable");
        var actual=((EarlyWarCoreInputs.Available)capture).state();actual.requireSame(request);
        return new MilitaryPlanningDecision.Keep(obj(f("active_wars",objects(actual.warSummaries()))));
    }
    static boolean has(PlanningRequest request,String step){return request.observations().actionSteps().contains(new OperationKey(step));}
    static MilitaryPlanningDecision select(PlanningRequest request,String phase,String step,String reason,Obj detail,List<Obj> summaries,OrdinaryPolicy.Purpose purpose) {
        if(!has(request,step))return hold(phase+"_unsupported",step,reason,detail,summaries);
        Obj full=merge(detail,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",text(step)),f("reason",text(reason)),f("active_wars",objects(summaries))));
        return new MilitaryPlanningDecision.Select("one-life-turn-v1",phase,reason,new OperationKey(step),empty(),purpose,full);
    }
    static MilitaryPlanningDecision hold(String phase,String required,String reason,Obj detail,List<Obj> summaries) {
        Obj full=merge(detail,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",Nil.INSTANCE),f("reason",text(reason)),f("active_wars",objects(summaries))));
        if(required!=null)full=put(full,"required_step",text(required));
        return new MilitaryPlanningDecision.Hold("one-life-turn-v1",phase,reason,required==null?Optional.empty():Optional.of(new OperationKey(required)),full);
    }
    private static MilitaryPlanningDecision unavailable(Exception invalid) {
        return new MilitaryPlanningDecision.Unavailable(List.of(Objects.toString(invalid.getMessage(),"typed early input unavailable")),"actual early WarCore input is incomplete");
    }
}
