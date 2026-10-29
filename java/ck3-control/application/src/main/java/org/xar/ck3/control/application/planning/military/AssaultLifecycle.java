package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Proven exact assault lifecycles. ACK, a missing rich row and unobserved time never close a Start. */
public final class AssaultLifecycle {
    private AssaultLifecycle() { }
    public record Open(int warId,int provinceId,int siegeId,long startedIndex) {
        public Open {require(warId>0&&provinceId>0&&siegeId>0&&startedIndex>=1,"exact assault lifecycle identity required");}
        public Obj toJson() {return obj(f("war_id",number(warId)),f("province_id",number(provinceId)),f("siege_id",number(siegeId)),f("started_index",new IntegerValue(java.math.BigInteger.valueOf(startedIndex))));}
    }
    public record Pending(Open lifecycle,String reason) {
        public Pending {Objects.requireNonNull(lifecycle);require(reason!=null&&!reason.isEmpty(),"actual observation gap required");}
        public Obj toJson(){return merge(lifecycle.toJson(),obj(f("status",text("unavailable")),f("reason",text(reason))));}
    }
    private record Key(int warId,int provinceId,int siegeId) { }
    private static final Pattern START=Pattern.compile("start-assault-(0|[1-9][0-9]*)"),STOP=Pattern.compile("stop-assault-(0|[1-9][0-9]*)"),
            OCCUPATION=Pattern.compile("query-war-occupation-targets-v1-(0|[1-9][0-9]*)");

    public static WarCorePlanner.Leaf factory(ExactRef implementationSource) {
        return new WarCorePlanner.Leaf(WarCorePlanner.Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE,implementationSource,AssaultLifecycle::evaluate);
    }
    public static MilitaryPlanningDecision evaluate(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        List<Obj> summaries=NativeWarEndConditions.summaries(request);Obj annotations=obj(f("active_wars",objects(summaries)));
        if(!yes(request.observations().snapshot().get("paused")))return new MilitaryPlanningDecision.Keep(annotations);
        List<Pending> blocked=pending(request.observations().snapshot(),wars(request),request.observations().history());
        if(blocked.isEmpty())return new MilitaryPlanningDecision.Keep(annotations);
        String phase="native_war_assault_lifecycle_blocked",reason="a proven assault_started lifecycle has no exact completed, stopped, restored, or currently observable same-SiegeID state; do not advance time";
        Obj detail=merge(annotations,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",Nil.INSTANCE),
                f("required_step",text("observable-exact-assault-state")),f("reason",text(reason)),f("assault_lifecycles",objects(blocked.stream().map(Pending::toJson).toList()))));
        return new MilitaryPlanningDecision.Hold("one-life-turn-v1",phase,reason,Optional.of(new org.xar.ck3.control.application.action.OperationKey("observable-exact-assault-state")),detail);
    }
    public static List<Open> open(List<Obj> history) {
        List<DriverSurvivingHistory.Row> rows=DriverSurvivingHistory.afterLatestRestore(history.stream().map(DriverSurvivingHistory::row).toList());
        Map<Key,Open> opened=new LinkedHashMap<>();
        for(var row:rows) {
            if(!row.ok()||row.effective().result().isEmpty())continue;
            Obj result=row.effective().result().orElseThrow();Obj action=result.get("assault_action") instanceof Obj value?value:result.get("war_action") instanceof Obj value?value:null;
            if(action==null)continue;Integer siege=positive(action.get("siege_id")),war=positive(action.get("war_id")),province=positive(action.get("province_id"));
            if(siege==null||war==null||province==null)continue;Key key=new Key(war,province,siege);String command=row.effective().command().orElse("");
            if(is(action,"status","assault_started")&&Objects.equals(parse(START,command),siege))opened.put(key,new Open(war,province,siege,row.index()));
            else if(is(action,"status","assault_stopped")&&Objects.equals(parse(STOP,command),siege))opened.remove(key);
        }
        return opened.values().stream().sorted(Comparator.comparingLong(Open::startedIndex).thenComparingInt(Open::warId).thenComparingInt(Open::provinceId).thenComparingInt(Open::siegeId)).toList();
    }
    public static List<Pending> pending(Obj snapshot,List<Obj> activeWars,List<Obj> history) {
        Map<Integer,Obj> wars=new LinkedHashMap<>();for(Obj war:activeWars){Integer id=optionalInt(war.get("war_id"));if(id!=null)wars.put(id,war);}
        List<Obj> holdings=freshHoldingStates(snapshot,history);List<Pending> pending=new ArrayList<>();
        for(Open lifecycle:open(history)) {
            Obj war=wars.get(lifecycle.warId());if(war==null)continue;
            Map<Integer,Obj> states=states(war);Obj state=states.get(lifecycle.provinceId());
            if(state!=null&&occupied(snapshot,war,states,holdings).contains(lifecycle.provinceId()))continue;
            String reason;
            if(!yes(snapshot.get("war_objective_assault_supported")))reason="assault_capability_unavailable_after_start";
            else if(state==null)reason="objective_row_unavailable_after_start";
            else if(!yes(state.get("siege_observable")))reason="siege_unobservable_after_start";
            else if(state.get("active_siege")==Nil.INSTANCE)continue;
            else if(!(state.get("active_siege") instanceof Obj siege))reason="active_siege_unavailable_after_start";
            else {
                Integer observed=optionalInt(siege.get("siege_id"));
                if(!Objects.equals(observed,lifecycle.siegeId())) {
                    if(observed!=null&&observed>=0)continue;reason="siege_generation_unavailable_after_start";
                } else if(!yes(siege.get("assault_observable")))reason="assault_subdomain_unobservable_after_start";
                else if(no(siege.get("assault_in_progress")))continue;
                else if(yes(siege.get("assault_in_progress"))) {
                    if(yes(siege.get("player_army_besieging")))continue;reason="player_besieger_unavailable_after_start";
                } else reason="assault_flag_unavailable_after_start";
            }
            pending.add(new Pending(lifecycle,reason));
        }
        return List.copyOf(pending);
    }
    public static Map<Integer,Obj> states(Obj war) {
        Map<Integer,Obj> result=new LinkedHashMap<>();for(Obj row:rows(war.get("objective_province_states"))) {
            Integer province=optionalInt(row.get("province_id"));if(province!=null)result.putIfAbsent(province,row);
        }return java.util.Collections.unmodifiableMap(result);
    }
    /** Native participant-side observations override owner heuristics only for existing exact objective rows. */
    public static Set<Integer> occupied(Obj snapshot,Obj war,Map<Integer,Obj> states,List<Obj> holdingStates) {
        Set<Integer> playerSide=new HashSet<>();
        if(snapshot.get("played_character") instanceof Obj actor){Integer id=optionalInt(actor.get("character_id"));if(id!=null)playerSide.add(id);}
        for(Obj army:rows(war.get("allied_armies"))){Integer owner=optionalInt(army.get("owner_character_id"));if(owner!=null)playerSide.add(owner);}
        Set<Integer> occupied=new HashSet<>();for(var entry:states.entrySet())if(yes(entry.getValue().get("occupation_observable"))&&yes(entry.getValue().get("is_occupied"))
                &&playerSide.contains(optionalInt(entry.getValue().get("occupying_character_id"))))occupied.add(entry.getKey());
        for(Obj holding:holdingStates) {
            Integer province=optionalInt(holding.get("province_id"));
            if(!Objects.equals(holding.get("war_id"),war.get("war_id"))||province==null||!states.containsKey(province)||!yes(holding.get("occupation_observable")))continue;
            occupied.remove(province);if(yes(holding.get("is_occupied"))&&Objects.equals(holding.get("occupier_side"),war.get("player_side")))occupied.add(province);
        }
        return Set.copyOf(occupied);
    }
    /** The newest successful or failed query per War hides older answers, exactly as the original consumer. */
    public static List<Obj> freshHoldingStates(Obj snapshot,List<Obj> history) {
        if(!yes(snapshot.get("paused"))||!(snapshot.get("played_character") instanceof Obj actor)||!yes(actor.get("alive")))return List.of();
        Integer actorId=optionalInt(actor.get("character_id"));if(actorId==null||actorId<0)return List.of();
        Obj diagnostics=snapshot.get("diagnostics") instanceof Obj value?value:empty();List<Obj> result=new ArrayList<>();Set<Integer> seen=new HashSet<>();
        List<DriverSurvivingHistory.Row> branch=DriverSurvivingHistory.afterLatestRestore(history.stream().map(DriverSurvivingHistory::row).toList());
        for(int index=branch.size()-1;index>=0;index--) {
            var row=branch.get(index);Integer warId=parse(OCCUPATION,row.effective().command().orElse(""));
            if(warId==null||!seen.add(warId)||!row.ok()||row.effective().result().isEmpty())continue;
            List<Obj> wars=rows(snapshot.get("active_wars")).stream().filter(war->Objects.equals(optionalInt(war.get("war_id")),warId)).toList();
            if(wars.size()!=1||!(is(wars.getFirst(),"player_side","attacker")||is(wars.getFirst(),"player_side","defender")))continue;
            Obj response=row.effective().result().orElseThrow();if(!(response.get("war_occupation_targets_v1") instanceof Obj value))continue;
            if(!yes(value.get("available"))||!yes(value.get("collection_complete"))||!Objects.equals(optionalInt(value.get("war_id")),warId)
                    ||!Objects.equals(optionalInt(value.get("actor_character_id")),actorId)||!Objects.equals(value.get("player_side"),wars.getFirst().get("player_side"))
                    ||!equal(value,"snapshot_revision",snapshot,"native_revision")||!equal(value,"date_raw",snapshot,"date_raw")
                    ||!equal(response,"queried_snapshot_id",snapshot,"snapshot_id")||!equal(response,"queried_revision",snapshot,"revision")
                    ||!equal(response,"queried_native_revision",snapshot,"native_revision")||!equal(response,"queried_connection_generation",diagnostics,"connection_generation")
                    ||!equal(response,"queried_episode_run_id",snapshot,"episode_run_id"))continue;
            require(value.get("rows") instanceof Arr,"complete occupation rows required");
            for(Value raw:((Arr)value.get("rows")).items()) {
                require(raw instanceof Obj,"occupation holding row must be object");Obj holding=(Obj)raw;Integer province=positive(holding.get("province_id"));
                require(province!=null,"positive holding Province required");
                require(holding.get("siege_observable") instanceof Bool,"holding siege visibility must be boolean");
                require(holding.members().containsKey("active_siege")&&(holding.get("active_siege")==Nil.INSTANCE||holding.get("active_siege") instanceof Obj),"holding active siege must distinguish missing/null/object");
                result.add(obj(f("war_id",number(warId)),f("province_id",number(province)),f("siege_observable",holding.get("siege_observable")),f("active_siege",holding.get("active_siege")),
                        f("occupation_observable",nullable(holding.get("occupation_observable"))),f("is_occupied",nullable(holding.get("is_occupied"))),
                        f("occupying_character_id",nullable(holding.get("occupying_character_id"))),f("occupier_side",nullable(holding.get("occupier_side"))),f("observation_source",text("war_occupation_query"))));
            }
        }
        return List.copyOf(result);
    }
    private static boolean equal(Obj first,String a,Obj second,String b){return first.get(a)!=null&&second.get(b)!=null&&first.get(a).equals(second.get(b));}
    private static Integer positive(Value value){Integer id=optionalInt(value);return id!=null&&id>0?id:null;}
    private static Integer parse(Pattern pattern,String value){var matcher=pattern.matcher(value);if(!matcher.matches())return null;try{return Integer.valueOf(matcher.group(1));}catch(NumberFormatException invalid){return null;}}
    private static boolean is(Obj row,String key,String value){return new Text(value).equals(row.get(key));}
}
