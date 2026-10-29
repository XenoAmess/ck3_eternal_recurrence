package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** strategy10751/11389..11485/15964/16063: original objective ordering and actual occupation override. */
public final class WarObjectiveSources {
    private WarObjectiveSources() { }
    public record State(ObservationIdentity before,int warId,int subjectArmyId,
            List<Integer> rankedExactObjectives,List<Integer> siegeObjectives,
            Set<Integer> completedObjectives,Set<Integer> blockedProvinces,
            Map<Integer,Obj> exactStates,boolean exactOccupationFullyObservable,
            boolean allSiegeObjectivesCompleted) {
        public State {
            Objects.requireNonNull(before);require(warId>0&&subjectArmyId>=0,"actual War/public Unit identity");
            rankedExactObjectives=List.copyOf(rankedExactObjectives);siegeObjectives=List.copyOf(siegeObjectives);
            completedObjectives=Set.copyOf(completedObjectives);blockedProvinces=Set.copyOf(blockedProvinces);
            exactStates=java.util.Collections.unmodifiableMap(new java.util.LinkedHashMap<>(exactStates));
        }
        public void requireSame(PlanningRequest request,int war,int army) {
            require(before.equals(request.before())&&warId==war&&subjectArmyId==army,"objective source crossed actual frame/War/Unit");
        }
    }
    public static State collect(PlanningRequest request,Obj war,Army subject,Obj relief,Obj tactical) {
        Objects.requireNonNull(request);Objects.requireNonNull(war);Objects.requireNonNull(subject);
        int warId=province(war.get("war_id"));Obj snapshot=request.observations().snapshot();
        require(wars(request).contains(war)&&armies(request).contains(subject),"objective inputs must be actual snapshot members");
        List<Integer> exact=WarContactObservation.objectives(List.of(war));
        Map<Integer,Obj> states=war.get("objective_province_states") instanceof Arr?AssaultLifecycle.states(war):Map.of();
        List<Integer> initialSiege=attackerSiegeObjectives(war,exact);
        Set<Integer> completed=new LinkedHashSet<>(ids(tactical.get("completed_objective_province_ids")));
        Set<Integer> blocked=new LinkedHashSet<>(ids(tactical.get("blocked_province_ids")));
        boolean complete=!exact.isEmpty()&&yes(snapshot.get("war_objective_occupation_supported"))
                &&new ArrayList<>(states.keySet()).equals(exact);
        boolean observable=complete&&exact.stream().allMatch(p->yes(states.get(p).get("occupation_observable")));
        if(complete) {
            Set<Integer> occupied=AssaultLifecycle.occupied(snapshot,war,states,
                    AssaultLifecycle.freshHoldingStates(snapshot,request.observations().history()));
            for(int p:exact)if(yes(states.get(p).get("occupation_observable"))) {
                completed.remove(p);if(occupied.contains(p))completed.add(p);
            }
        }
        exact=rank(exact,states,yes(snapshot.get("war_objective_fort_level_supported")),yes(snapshot.get("war_objective_garrison_supported")));
        List<Integer> siege=new ArrayList<>(observable?exact:initialSiege);
        Integer arrived=new Text("arrived_sieging").equals(relief.get("status"))?optionalInt(relief.get("target_province_id")):null;
        if(arrived!=null) {
            require(arrived>0,"actual arrived relief Province");completed.remove(arrived);siege.remove(arrived);siege.addFirst(arrived);
        }
        boolean allCompleted=!siege.isEmpty();
        siege=siege.stream().filter(p->!completed.contains(p)).toList();
        exact=exact.stream().filter(p->!completed.contains(p)).toList();
        allCompleted&=siege.isEmpty();
        return new State(request.before(),warId,subject.id(),exact,siege,completed,blocked,states,observable,allCompleted);
    }
    public static List<Integer> attackerSiegeObjectives(Obj war,List<Integer> exact) {
        Integer score=optionalInt(war.get("player_relative_war_score"));
        if(!new Text("attacker").equals(war.get("player_side"))||!yes(war.get("player_is_primary_war_leader"))||score==null)return List.of();
        List<Integer> result=new ArrayList<>(exact);
        Integer fallback=optionalInt(war.get("enemy_primary_default_raise_province_id"));
        if(score>0&&fallback!=null&&fallback>0&&!result.contains(fallback))result.add(fallback);
        return List.copyOf(result);
    }
    public static List<Integer> rank(List<Integer> provinces,Map<Integer,Obj> states,boolean fortSupported,boolean garrisonSupported) {
        List<Integer> original=List.copyOf(provinces);
        if(!fortSupported&&!garrisonSupported)return original;
        Map<Integer,Integer> ordinal=new java.util.LinkedHashMap<>();
        for(int i=0;i<original.size();i++)require(ordinal.put(original.get(i),i)==null,"exact objectives must be unique");
        return original.stream().sorted(Comparator.comparingInt((Integer p)->rankValue(states.get(p),"fort_level",fortSupported))
                .thenComparingInt(p->rankValue(states.get(p),"garrison_size",garrisonSupported)).thenComparingInt(ordinal::get)).toList();
    }
    private static int rankValue(Obj row,String field,boolean supported) {
        Integer actual=supported&&row!=null?optionalInt(row.get(field)):null;
        return actual==null?Integer.MAX_VALUE:actual;
    }
}
