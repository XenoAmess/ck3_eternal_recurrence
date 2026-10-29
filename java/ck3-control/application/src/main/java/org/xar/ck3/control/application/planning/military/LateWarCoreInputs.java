package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Immutable publication from the real earlier WarCore producers. Missing is never an empty army/objective set. */
public final class LateWarCoreInputs {
    private LateWarCoreInputs() {}
    public record Sentinel(boolean enabled,int speed,boolean highSpeedAb) {
        public Sentinel { require(speed>=1&&speed<=5,"stationary sentinel speed 1..5"); }
    }
    public record Published(ObservationIdentity before,int tacticalWarId,int subjectArmyId,
            List<Integer> rankedExactObjectives,List<Integer> siegeObjectives,Set<Integer> blockedProvinces,
            List<Obj> stationaryThreats,Set<Integer> unsafeArmyIds,List<Obj> activeAssaults,
            Optional<Obj> passiveRouteAudit,Obj siegeRelief,Optional<Obj> exactSiegeRejection,
            List<Obj> terminationRows,List<Obj> warSummaries,Obj tacticalState,
            boolean routePreviewSupported,boolean contactHorizonSupported,
            boolean exactOccupationFullyObservable,boolean allSiegeObjectivesCompleted,Sentinel sentinel) {
        public Published {
            Objects.requireNonNull(before);require(tacticalWarId>0&&subjectArmyId>=0,"actual War/public Unit identity");
            rankedExactObjectives=provinces(rankedExactObjectives);siegeObjectives=provinces(siegeObjectives);
            blockedProvinces=Set.copyOf(blockedProvinces);blockedProvinces.forEach(p->require(p>0,"blocked Province"));
            stationaryThreats=List.copyOf(stationaryThreats);unsafeArmyIds=Set.copyOf(unsafeArmyIds);
            unsafeArmyIds.forEach(p->require(p>=0,"unsafe public Unit"));activeAssaults=List.copyOf(activeAssaults);
            Objects.requireNonNull(passiveRouteAudit);Objects.requireNonNull(siegeRelief);Objects.requireNonNull(exactSiegeRejection);
            terminationRows=List.copyOf(terminationRows);warSummaries=List.copyOf(warSummaries);
            Objects.requireNonNull(tacticalState);Objects.requireNonNull(sentinel);
            for(Obj row:terminationRows)id(row.get("war_id"));
        }
    }
    public record Context(PlanningRequest request,Published published,Obj snapshot,Obj war,Army subject,
            List<Army> controlled,List<Army> enemies,List<Integer> hostileIds,Optional<Balance> balance) {
        public Context {
            Objects.requireNonNull(request);Objects.requireNonNull(published);Objects.requireNonNull(snapshot);
            Objects.requireNonNull(war);Objects.requireNonNull(subject);controlled=List.copyOf(controlled);
            enemies=List.copyOf(enemies);hostileIds=List.copyOf(hostileIds);Objects.requireNonNull(balance);
            require(published.before().equals(request.before()),"late WarCore publication crossed frame");
        }
        public boolean routeUnsafe() { return published.passiveRouteAudit().filter(a->is(a,"status","unsafe")).isPresent(); }
        public boolean contactSupported() { return published.contactHorizonSupported()&&!hostileIds.isEmpty()&&hostileIds.size()<=64; }
        public int current() { require(subject.current()!=null&&subject.current()>0,"late subject needs actual Province");return subject.current(); }
        public Obj termination() {
            return published.terminationRows().stream().filter(r->Objects.equals(optionalInt(r.get("war_id")),published.tacticalWarId()))
                    .findFirst().orElse(empty());
        }
        public List<Army> unsafeArmies() { return controlled.stream().filter(a->published.unsafeArmyIds().contains(a.id())).toList(); }
        public List<Obj> history() { return request.observations().history(); }
    }
    public sealed interface Capture permits Available,Unavailable,NoPursuit {}
    /** Real residual strategy14727..14762 publication; this is distinct from a missing earlier producer. */
    public record NoPursuit(ObservationIdentity before,List<Obj> stationaryThreats,
            Optional<Obj> exactSiegeRejection,List<Obj> warSummaries) implements Capture {
        public NoPursuit {
            Objects.requireNonNull(before);stationaryThreats=List.copyOf(stationaryThreats);
            Objects.requireNonNull(exactSiegeRejection);warSummaries=List.copyOf(warSummaries);
        }
    }
    public record Available(Context context) implements Capture { public Available {Objects.requireNonNull(context);} }
    public record Unavailable(List<String> missing) implements Capture {
        public Unavailable {missing=List.copyOf(missing);require(!missing.isEmpty(),"exact missing upstream producers required");}
    }
    @FunctionalInterface public interface Provider { Capture collect(PlanningRequest request,OrdinaryPolicy.Draft previous); }

    public static void validateNoPursuit(PlanningRequest request,NoPursuit publication) {
        require(publication.before().equals(request.before()),"residual publication crossed current frame");
        boolean canonical=rows(request.observations().snapshot().get("player_armies")).stream().anyMatch(raw->{
            Integer id=optionalInt(raw.get("army_id")),province=optionalInt(raw.get("current_province_id"));
            return yes(raw.get("controllable"))&&id!=null&&id>=0&&province!=null&&province>0;
        });
        require(!canonical,"canonical current controllable subject cannot bypass the actual late route producers");
    }

    /** This verifies raw identities against the same semantic request; it cannot synthesize earlier tactical conclusions. */
    public static Context collect(PlanningRequest request,Published publication) {
        require(publication.before().equals(request.before()),"source publication must bind current public/native observation");
        List<Army> controlled=armies(request).stream().filter(Army::controllable).toList();
        Army subject=controlled.stream().filter(a->a.id()==publication.subjectArmyId()).findFirst().orElseThrow(
                ()->new IllegalArgumentException("late public Unit is absent from the actual controllable army set"));
        Obj war=wars(request).stream().filter(r->Objects.equals(optionalInt(r.get("war_id")),publication.tacticalWarId()))
                .findFirst().orElseThrow(()->new IllegalArgumentException("late tactical War absent from actual active wars"));
        require(publication.unsafeArmyIds().stream().allMatch(i->controlled.stream().anyMatch(a->a.id()==i)),
                "published unsafe Unit absent from actual controllable set");
        List<Army> enemies=enemies(request).stream().filter(a->!"retreating".equals(a.tacticalState())).toList();
        List<Integer> ids=enemies.stream().map(Army::id).distinct().sorted().toList();
        require(ids.size()==enemies.size(),"complete hostile identity set required");
        return new Context(request,publication,request.observations().snapshot(),war,subject,controlled,enemies,ids,
                balance(request,publication.tacticalWarId()));
    }
    private static List<Integer> provinces(List<Integer> values) {
        List<Integer> result=List.copyOf(values);result.forEach(p->require(p>0,"positive objective Province required"));
        require(new HashSet<>(result).size()==result.size(),"duplicate ranked objective");return result;
    }
    public static boolean is(Obj row,String field,String value) { return new Text(value).equals(row.get(field)); }
    /** One exact schema, preserving required null versus missing for optional conclusions. */
    public static Published decode(ObservationIdentity before,Obj row) {
        require(row.members().keySet().equals(FIELDS),"whole late WarCore publication required; unknown/missing field");
        Obj sentinel=OpportunityJson.object(row.get("sentinel"),"sentinel publication");
        require(sentinel.members().keySet().equals(Set.of("enabled","speed","high_speed_ab")),"exact sentinel fields");
        return new Published(before,id(row.get("tactical_war_id")),id(row.get("subject_army_id")),
                requiredProvinces(row,"ranked_exact_objectives"),requiredProvinces(row,"siege_objectives"),
                Set.copyOf(requiredProvinces(row,"blocked_provinces")),rows(row.get("stationary_threats")),
                Set.copyOf(ids(row.get("unsafe_army_ids"))),rows(row.get("active_assaults")),
                optionalObject(row.get("passive_route_audit")),OpportunityJson.object(row.get("siege_relief"),"siege relief"),
                optionalObject(row.get("exact_siege_rejection")),rows(row.get("termination_rows")),rows(row.get("war_summaries")),
                OpportunityJson.object(row.get("tactical_state"),"tactical state"),
                flag(row,"route_preview_supported"),flag(row,"contact_horizon_supported"),
                flag(row,"exact_occupation_fully_observable"),flag(row,"all_siege_objectives_completed"),
                new Sentinel(flag(sentinel,"enabled"),int32(sentinel.get("speed")),flag(sentinel,"high_speed_ab")));
    }
    public static Obj encode(Published p) {
        return obj(f("tactical_war_id",number(p.tacticalWarId())),f("subject_army_id",number(p.subjectArmyId())),
                f("ranked_exact_objectives",numbers(p.rankedExactObjectives())),f("siege_objectives",numbers(p.siegeObjectives())),
                f("blocked_provinces",numbers(p.blockedProvinces().stream().sorted().toList())),
                f("stationary_threats",objects(p.stationaryThreats())),f("unsafe_army_ids",numbers(p.unsafeArmyIds().stream().sorted().toList())),
                f("active_assaults",objects(p.activeAssaults())),f("passive_route_audit",p.passiveRouteAudit().<Value>map(v->v).orElse(Nil.INSTANCE)),
                f("siege_relief",p.siegeRelief()),f("exact_siege_rejection",p.exactSiegeRejection().<Value>map(v->v).orElse(Nil.INSTANCE)),
                f("termination_rows",objects(p.terminationRows())),f("war_summaries",objects(p.warSummaries())),f("tactical_state",p.tacticalState()),
                f("route_preview_supported",new Bool(p.routePreviewSupported())),f("contact_horizon_supported",new Bool(p.contactHorizonSupported())),
                f("exact_occupation_fully_observable",new Bool(p.exactOccupationFullyObservable())),
                f("all_siege_objectives_completed",new Bool(p.allSiegeObjectivesCompleted())),
                f("sentinel",obj(f("enabled",new Bool(p.sentinel().enabled())),f("speed",number(p.sentinel().speed())),
                    f("high_speed_ab",new Bool(p.sentinel().highSpeedAb())))));
    }
    private static Optional<Obj> optionalObject(Value value) {
        require(value!=null,"required nullable late input missing");
        return value==Nil.INSTANCE?Optional.empty():Optional.of(OpportunityJson.object(value,"late optional object"));
    }
    private static boolean flag(Obj row,String field) { return OpportunityJson.bool(row.get(field),field); }
    private static List<Integer> requiredProvinces(Obj row,String field) {
        return route(row.get(field)).orElseThrow(()->new IllegalArgumentException("required objective array missing/null"));
    }
    private static final Set<String> FIELDS=Set.of("tactical_war_id","subject_army_id","ranked_exact_objectives",
            "siege_objectives","blocked_provinces","stationary_threats","unsafe_army_ids","active_assaults",
            "passive_route_audit","siege_relief","exact_siege_rejection","termination_rows","war_summaries","tactical_state",
            "route_preview_supported","contact_horizon_supported","exact_occupation_fully_observable","all_siege_objectives_completed","sentinel");
}
