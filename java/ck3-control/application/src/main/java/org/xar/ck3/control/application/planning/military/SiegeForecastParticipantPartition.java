package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.OptionalInt;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original strategy18025..18127: a current siege roster is never a complete future battle roster by itself. */
public final class SiegeForecastParticipantPartition {
    private SiegeForecastParticipantPartition() { }
    public enum Reason {
        WAR_ENEMY_OR_STRENGTH_ROSTER_MISSING, WAR_ENEMY_ROSTER_INVALID, STRENGTH_OR_CONTACT_ROSTER_MISMATCH,
        HOSTILE_ARRIVAL_TIMELINE_UNAVAILABLE, HOSTILE_ROUTE_ROSTER_INVALID, HOSTILE_TIMELINE_UNAVAILABLE,
        WAR_CONTACT_POSITION_MISMATCH, TARGET_DEFENDERS_NOT_EXACT_SIEGE_ROSTER, SUBJECT_TARGET_ARRIVAL_UNAVAILABLE,
        OFFSITE_HOSTILE_ROUTE_INVALID, OFFSITE_HOSTILE_MAY_JOIN_BY_TARGET_ENTRY;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface Result permits Available, Unavailable { Obj toJson(); }
    public record Unavailable(Reason reason) implements Result {
        public Unavailable { Objects.requireNonNull(reason); }
        @Override public Obj toJson() { return obj(f("status",text("unavailable")),f("reason",text(reason.wire()))); }
    }
    public record OffsiteArrival(int armyId, OptionalInt targetArrivalDateRaw) {
        public OffsiteArrival { require(armyId>=0,"public Army ID required"); Objects.requireNonNull(targetArrivalDateRaw); }
        public Obj toJson() { return obj(f("army_id",number(armyId)),f("target_arrival_date_raw",targetArrivalDateRaw.isPresent()?number(targetArrivalDateRaw.getAsInt()):Nil.INSTANCE)); }
    }
    public record Available(List<Integer> defenderArmyIds,List<Integer> offsiteHostileArmyIds,
            OptionalInt subjectTargetArrivalDateRaw,List<OffsiteArrival> offsiteTargetArrivals) implements Result {
        public Available { defenderArmyIds=List.copyOf(defenderArmyIds);offsiteHostileArmyIds=List.copyOf(offsiteHostileArmyIds);
            Objects.requireNonNull(subjectTargetArrivalDateRaw);offsiteTargetArrivals=List.copyOf(offsiteTargetArrivals);require(!defenderArmyIds.isEmpty(),"observed siege defenders required");
            for(List<Integer> side:List.of(defenderArmyIds,offsiteHostileArmyIds))require(side.equals(side.stream().distinct().sorted().toList())&&side.stream().allMatch(id->id>=0),"canonical public participant IDs required");
            require(defenderArmyIds.stream().noneMatch(offsiteHostileArmyIds::contains),"defender and offsite rosters overlap");
            require(offsiteHostileArmyIds.isEmpty()?subjectTargetArrivalDateRaw.isEmpty()&&offsiteTargetArrivals.isEmpty():subjectTargetArrivalDateRaw.isPresent()&&offsiteTargetArrivals.stream().map(OffsiteArrival::armyId).toList().equals(offsiteHostileArmyIds),"offsite arrival scope differs"); }
        @Override public Obj toJson() {
            Obj value=obj(f("status",text("available")),f("defender_army_ids",numbers(defenderArmyIds)),f("offsite_hostile_army_ids",numbers(offsiteHostileArmyIds)),
                    f("offsite_arrival_risk",text(offsiteHostileArmyIds.isEmpty()?"none_observed":"unmodeled_after_target_entry")));
            if(!offsiteHostileArmyIds.isEmpty())value=merge(value,obj(f("subject_target_arrival_date_raw",number(subjectTargetArrivalDateRaw.orElseThrow())),
                    f("offsite_target_arrivals",objects(offsiteTargetArrivals.stream().map(OffsiteArrival::toJson).toList()))));
            return value;
        }
    }
    public static Result partition(Obj war,Obj balance,MilitaryTimeline.Horizon contact,int armyId,int target) {
        require(armyId>=0&&target>0,"public Army and positive Province required");Objects.requireNonNull(contact);
        if(war==null||!(war.get("enemy_armies") instanceof Arr enemies)||enemies.items().isEmpty()||balance==null)
            return unavailable(Reason.WAR_ENEMY_OR_STRENGTH_ROSTER_MISSING);
        Map<Integer,Army> byId=new LinkedHashMap<>();
        for(Value raw:enemies.items()) {
            if(!(raw instanceof Obj row))return unavailable(Reason.WAR_ENEMY_ROSTER_INVALID);
            Army enemy;
            try {enemy=army(row);}catch(IllegalArgumentException invalid){return unavailable(Reason.WAR_ENEMY_ROSTER_INVALID);}
            if(byId.putIfAbsent(enemy.id(),enemy)!=null)return unavailable(Reason.WAR_ENEMY_ROSTER_INVALID);
        }
        List<Integer> enemyIds=byId.keySet().stream().sorted().toList();
        try {if(!ids(balance.get("friendly_army_ids")).equals(List.of(armyId))||!ids(balance.get("enemy_army_ids")).equals(enemyIds)
                ||!contact.hostileIds().containsAll(enemyIds))return unavailable(Reason.STRENGTH_OR_CONTACT_ROSTER_MISMATCH);}
        catch(IllegalArgumentException invalid){return unavailable(Reason.STRENGTH_OR_CONTACT_ROSTER_MISMATCH);}
        Map<Integer,MilitaryTimeline.TimedRoute> routes=new LinkedHashMap<>();
        for(var route:contact.hostiles())if(routes.putIfAbsent(route.armyId(),route)!=null)return unavailable(Reason.HOSTILE_ROUTE_ROSTER_INVALID);
        for(int id:enemyIds) {
            var route=routes.get(id);if(route==null||!yes(route.original().get("timeline_observable")))return unavailable(Reason.HOSTILE_TIMELINE_UNAVAILABLE);
            if(!Objects.equals(byId.get(id).current(),route.currentProvinceId()))return unavailable(Reason.WAR_CONTACT_POSITION_MISMATCH);
        }
        List<Integer> defenders=enemyIds.stream().filter(id->Integer.valueOf(target).equals(byId.get(id).current())).toList();
        if(defenders.isEmpty()||defenders.stream().anyMatch(id->!"sieging".equals(byId.get(id).tacticalState())))return unavailable(Reason.TARGET_DEFENDERS_NOT_EXACT_SIEGE_ROSTER);
        List<Integer> offsite=enemyIds.stream().filter(id->!defenders.contains(id)).toList();
        if(offsite.isEmpty())return new Available(defenders,List.of(),OptionalInt.empty(),List.of());
        var subject=contact.subject();
        if(subject.provinceIds().isEmpty()||subject.provinceIds().getLast()!=target||subject.arrivalDates().size()!=subject.provinceIds().size())
            return unavailable(Reason.SUBJECT_TARGET_ARRIVAL_UNAVAILABLE);
        int arrival=subject.arrivalDates().getLast();List<OffsiteArrival> arrivals=new ArrayList<>();
        for(int id:offsite) {
            var route=routes.get(id);
            if(route.provinceIds().size()!=route.arrivalDates().size())return unavailable(Reason.OFFSITE_HOSTILE_ROUTE_INVALID);
            int index=route.provinceIds().indexOf(target);OptionalInt observed=OptionalInt.empty();
            if(index>=0) {int date=route.arrivalDates().get(index);if(date<=arrival)return unavailable(Reason.OFFSITE_HOSTILE_MAY_JOIN_BY_TARGET_ENTRY);observed=OptionalInt.of(date);}
            arrivals.add(new OffsiteArrival(id,observed));
        }
        return new Available(defenders,offsite,OptionalInt.of(arrival),arrivals);
    }
    private static Unavailable unavailable(Reason reason) {return new Unavailable(reason);}
}
