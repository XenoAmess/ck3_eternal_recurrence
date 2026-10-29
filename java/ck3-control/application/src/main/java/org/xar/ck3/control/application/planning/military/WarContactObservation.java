package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorCodec;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Original strategy10246..10448 collection. No input is a preclassified safety conclusion. */
public final class WarContactObservation {
    private WarContactObservation() {}
    public sealed interface Result permits KnownContact,Incomplete {}
    public record Incomplete(List<String> missing) implements Result {
        public Incomplete { missing=List.copyOf(missing);require(!missing.isEmpty(),"exact contact dependencies required"); }
    }
    public record KnownContact(ObservationIdentity before,G2Source source,Context context) implements Result {
        public KnownContact { Objects.requireNonNull(before);Objects.requireNonNull(source);Objects.requireNonNull(context); }
        public void requireSame(PlanningRequest request) {
            require(before.equals(request.before())&&source.equals(request.source()),"contact observation crossed frame or source");
        }
    }
    public enum AuditStatus { SAFE,UNSAFE,UNAVAILABLE,ROUTE_DOES_NOT_REACH_TARGET }
    public record RouteAudit(int armyId,AuditStatus status,Obj detail) {
        public RouteAudit { require(armyId>=0,"route audit ArmyID");Objects.requireNonNull(status);Objects.requireNonNull(detail); }
    }
    public record Context(List<Army> controlledArmies,List<Army> completeRouteThreatEnemies,
            List<Integer> hostileArmyIds,List<RouteAudit> globalRouteAudits,List<Obj> evidenceIssues,
            Set<Integer> unsafeArmyIds,Set<Integer> threatenedStationaryArmyIds,
            Set<Integer> startBlockingRouteArmyIds,Optional<Army> pursuitArmy,
            Optional<Integer> tacticalWarId,Optional<Obj> replenishmentSelection) {
        public Context {
            controlledArmies=List.copyOf(controlledArmies);completeRouteThreatEnemies=List.copyOf(completeRouteThreatEnemies);
            hostileArmyIds=List.copyOf(hostileArmyIds);globalRouteAudits=List.copyOf(globalRouteAudits);evidenceIssues=List.copyOf(evidenceIssues);
            unsafeArmyIds=Set.copyOf(unsafeArmyIds);threatenedStationaryArmyIds=Set.copyOf(threatenedStationaryArmyIds);
            startBlockingRouteArmyIds=Set.copyOf(startBlockingRouteArmyIds);Objects.requireNonNull(pursuitArmy);
            Objects.requireNonNull(tacticalWarId);Objects.requireNonNull(replenishmentSelection);
            if(pursuitArmy.isPresent())require(controlledArmies.contains(pursuitArmy.orElseThrow()),"selected Army not in actual roster");
        }
    }
    public static Result collect(PlanningRequest request) {
        Objects.requireNonNull(request);
        try { return new KnownContact(request.before(),request.source(),collectRequired(request)); }
        catch(IllegalArgumentException|java.util.NoSuchElementException invalid) {
            return new Incomplete(List.of("current-war-contact:"+Objects.toString(invalid.getMessage(),"typed input missing")));
        }
    }
    static Context collectRequired(PlanningRequest request) {
        Obj snapshot=request.observations().snapshot();
        require(snapshot.get("player_armies") instanceof Arr,"snapshot.player_armies");
        require(snapshot.get("active_wars") instanceof Arr,"snapshot.active_wars");
        List<Obj> wars=MilitaryPlanInputs.rows(snapshot.get("active_wars"));
        Map<Integer,Army> merged=new LinkedHashMap<>();
        for(Obj raw:MilitaryPlanInputs.rows(snapshot.get("player_armies")))admit(merged,raw);
        Map<Integer,Army> enemies=new LinkedHashMap<>();
        for(Obj war:wars) {
            id(war.get("war_id"));
            require(war.get("allied_armies") instanceof Arr,"active_wars.allied_armies");
            require(war.get("enemy_armies") instanceof Arr,"active_wars.enemy_armies");
            for(Obj ally:MilitaryPlanInputs.rows(war.get("allied_armies")))if(yes(ally.get("controllable")))admit(merged,ally);
            for(Obj enemy:MilitaryPlanInputs.rows(war.get("enemy_armies")))admit(enemies,enemy);
        }
        List<Army> controlled=merged.values().stream().filter(Army::controllable).toList();
        List<Army> threats=enemies.values().stream().filter(a->!"retreating".equals(a.tacticalState())).toList();
        List<Integer> hostiles=threats.stream().map(Army::id).sorted().toList();
        List<Obj> issues=new ArrayList<>();
        for(Army a:controlled)evidenceIssue(a,"player",null).ifPresent(issues::add);
        for(Obj war:wars)for(Obj raw:MilitaryPlanInputs.rows(war.get("enemy_armies"))) {
            Army a=army(raw);
            if(!"retreating".equals(a.tacticalState()))evidenceIssue(a,"enemy",id(war.get("war_id"))).ifPresent(issues::add);
        }
        Set<Integer> threatened=new LinkedHashSet<>(),blocking=new LinkedHashSet<>(),unsafe=new LinkedHashSet<>();
        List<RouteAudit> audits=new ArrayList<>();
        boolean routeSupported=flag(snapshot,"army_routes_supported");
        for(Army a:controlled) {
            String state=a.tacticalState();
            if(a.target()==null&&("regular".equals(state)||"sieging".equals(state))
                    &&!stationaryThreats(a.current(),threats).isEmpty())threatened.add(a.id());
            if(a.target()!=null&&a.target()>0||a.route().filter(r->!r.isEmpty()).isPresent()
                    ||"moving".equals(state)||Integer.valueOf(7).equals(a.stateCode()))blocking.add(a.id());
            if(!routeSupported||Set.of("combat","retreating","gathering").contains(Objects.toString(state,"")))continue;
            if(a.target()==null) {
                if("moving".equals(state)||Integer.valueOf(7).equals(a.stateCode())||a.route().filter(r->!r.isEmpty()).isPresent())
                    audits.add(new RouteAudit(a.id(),AuditStatus.UNAVAILABLE,obj(f("army_id",number(a.id())),
                            f("army_state",nullable(a.state()==null?null:text(state))),f("status",text("unavailable")),
                            f("reason",text("active controlled movement lacks an observable exact move target")),f("conflicts",new Arr(List.of())))));
                continue;
            }
            RouteAudit audit=audit(a,threats);audits.add(audit);
            if(audit.status()==AuditStatus.UNSAFE)unsafe.add(a.id());
        }
        Optional<Obj> selection=Optional.empty();Optional<Army> pursuit;
        if(!unsafe.isEmpty())pursuit=strongest(controlled.stream().filter(a->unsafe.contains(a.id())).toList());
        else if(!threatened.isEmpty())pursuit=strongest(controlled.stream().filter(a->threatened.contains(a.id())).toList());
        else {
            List<Value> warIds=wars.stream().<Value>map(w->number(id(w.get("war_id")))).toList();
            Obj selector=obj(f("schema",text(ArmySelectorCodec.SCHEMA)),f("armies",objects(controlled.stream().map(Army::raw).toList())),
                    f("snapshot",snapshot),f("active_war_ids",new Arr(warIds)));
            var selected=org.xar.ck3.control.wave2.military.armyselector.CurrentReplenishmentSelector.select(
                    ArmySelectorCodec.decode(OpportunityJson.encode(selector)));
            Obj receipt=OpportunityJson.object(OpportunityJson.parse(ArmySelectorCodec.encode(selected)),"current refill selection");
            selection=Optional.of(receipt);
            pursuit=selected.selected()==null?Optional.empty():controlled.stream().filter(a->a.id()==selected.selected().armyId()).findFirst();
        }
        return new Context(controlled,threats,hostiles,audits,issues,unsafe,threatened,blocking,pursuit,tacticalWar(wars),selection);
    }
    private static void admit(Map<Integer,Army> byId,Obj raw) {
        Army a=army(raw);byId.putIfAbsent(a.id(),a);
    }
    public static boolean flag(Obj source,String key) {
        Value value=source.get(key);require(value instanceof Bool,"snapshot."+key+" requires explicit Boolean");return ((Bool)value).value();
    }
    public static Optional<Army> strongest(List<Army> rows) {
        return rows.stream().max(Comparator.comparing((Army a)->Optional.ofNullable(optionalInteger(a.raw().get("soldiers"))).orElse(BigInteger.valueOf(-1)))
                .thenComparing(Comparator.comparingInt(Army::id).reversed()));
    }
    public static Optional<Integer> tacticalWar(List<Obj> wars) {
        return wars.stream().min(Comparator.comparingInt(WarContactObservation::warRank).thenComparingInt(w->id(w.get("war_id"))))
                .map(w->id(w.get("war_id")));
    }
    private static int warRank(Obj war) {
        if(yes(war.get("player_is_primary_war_leader")))
            return new Text("attacker").equals(war.get("player_side"))&&!objectives(List.of(war)).isEmpty()?0:1;
        return 2;
    }
    public static List<Integer> objectives(List<Obj> wars) {
        Set<Integer> out=new LinkedHashSet<>();
        for(Obj war:wars)if(war.get("war_objective_province_ids") instanceof Arr a)
            for(Value v:a.items())out.add(province(v));
        return List.copyOf(out);
    }
    public static List<Obj> stationaryThreats(Integer current,List<Army> enemies) {
        if(current==null)return List.of();List<Obj> out=new ArrayList<>();
        for(Army enemy:enemies) {
            if("retreating".equals(enemy.tacticalState()))continue;
            String kind=Objects.equals(enemy.current(),current)?"enemy_at_stationary_province":
                    Objects.equals(enemy.target(),current)?"enemy_targeting_stationary_province":
                    enemy.route().filter(r->r.contains(current)).isPresent()?"enemy_route_to_stationary_province":null;
            if(kind!=null)out.add(obj(f("kind",text(kind)),f("enemy_army_id",number(enemy.id())),f("province_id",number(current))));
        }
        return List.copyOf(out);
    }
    static Optional<Obj> evidenceIssue(Army a,String role,Integer war) {
        boolean active="moving".equals(a.tacticalState())||Integer.valueOf(7).equals(a.stateCode())
                ||a.route().filter(r->!r.isEmpty()).isPresent()||role.equals("player")&&a.target()!=null;
        if(!active)return Optional.empty();
        List<Integer> route=a.route().map(r->MilitaryRouteGeometry.remaining(r,a.current()==null?0:a.current())).orElse(null);
        String reason=a.target()==null||a.target()<=0?"active_route_target_unavailable":route==null?"active_route_unavailable":
                route.isEmpty()?"active_route_empty":!route.getLast().equals(a.target())?"active_route_endpoint_mismatch":null;
        if(reason==null)return Optional.empty();
        return Optional.of(obj(f("role",text(role)),f("war_id",war==null?Nil.INSTANCE:number(war)),f("army_id",number(a.id())),
                f("army_state",a.tacticalState()==null?Nil.INSTANCE:text(a.tacticalState())),
                f("current_province_id",a.current()==null?Nil.INSTANCE:number(a.current())),
                f("move_target_province_id",a.target()==null?Nil.INSTANCE:number(a.target())),
                f("route_province_ids",a.route().<Value>map(MilitaryPlanInputs::numbers).orElse(Nil.INSTANCE)),f("reason",text(reason))));
    }
    public static RouteAudit audit(Army army,List<Army> enemies) {
        if(army.target()==null||army.target()<=0||army.route().isEmpty())
            return new RouteAudit(army.id(),AuditStatus.UNAVAILABLE,obj(f("army_id",number(army.id())),f("status",text("unavailable")),
                    f("reason",text("route_not_observable")),f("target_province_id",army.target()==null?Nil.INSTANCE:number(army.target()))));
        var result=MilitaryRouteGeometry.geometry(army.route().orElseThrow(),army.current()==null?0:army.current(),army.target(),
                enemies.stream().map(Army::geometry).toList());
        if(result.status()==MilitaryRouteGeometry.Status.ROUTE_DOES_NOT_REACH_TARGET)
            return new RouteAudit(army.id(),AuditStatus.UNAVAILABLE,obj(f("army_id",number(army.id())),
                    f("army_state",army.tacticalState()==null?Nil.INSTANCE:text(army.tacticalState())),
                    f("status",text("unavailable")),f("target_province_id",number(result.targetProvinceId())),
                    f("route_province_ids",numbers(result.routeProvinceIds())),f("reason",text("route_does_not_reach_target"))));
        AuditStatus status=switch(result.status()) {case SAFE,SAFE_ONE_DAY_CONTACT_HORIZON->AuditStatus.SAFE;case UNSAFE->AuditStatus.UNSAFE;case ROUTE_DOES_NOT_REACH_TARGET->AuditStatus.ROUTE_DOES_NOT_REACH_TARGET;};
        List<Obj> conflicts=new ArrayList<>();
        for(var c:result.conflicts()) {
            Obj out=obj(f("kind",text(c.kind().name().toLowerCase(java.util.Locale.ROOT))),
                    f("enemy_army_id",c.enemyArmyId()==null?Nil.INSTANCE:number(c.enemyArmyId())),f("province_id",number(c.provinceId())));
            if(c.toProvinceId().isPresent())out=put(out,"to_province_id",number(c.toProvinceId().orElseThrow()));
            if(c.playerHop().isPresent())out=put(out,"player_hop",number(c.playerHop().orElseThrow()));
            if(c.enemyHop().isPresent())out=put(out,"enemy_hop",number(c.enemyHop().orElseThrow()));
            conflicts.add(out);
        }
        return new RouteAudit(army.id(),status,obj(f("army_id",number(army.id())),
                f("army_state",army.tacticalState()==null?Nil.INSTANCE:text(army.tacticalState())),
                f("status",text(status.name().toLowerCase(java.util.Locale.ROOT))),f("target_province_id",number(result.targetProvinceId())),
                f("route_province_ids",numbers(result.routeProvinceIds())),f("conflicts",objects(conflicts))));
    }
}

