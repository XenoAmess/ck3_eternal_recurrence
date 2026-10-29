package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Narrow runtime boundary for the actual ordinary semantic snapshot and history. */
public final class MilitaryPlanInputs {
    private MilitaryPlanInputs() {}
    public record Field(String key, Value value) {
        public Field { StrictJson.text(key); Objects.requireNonNull(value); }
    }
    public static Field f(String key,Value value) { return new Field(key,value); }
    public static Obj obj(Field... fields) {
        Map<String,Value> values=new LinkedHashMap<>();
        for(Field field:fields) require(values.put(field.key(),field.value())==null,"duplicate emitted military field");
        return new Obj(values);
    }
    public static Obj put(Obj source,String field,Value value) {
        Map<String,Value> copy=new LinkedHashMap<>(source.members());copy.put(field,Objects.requireNonNull(value));return new Obj(copy);
    }
    public static Obj merge(Obj source,Obj added) {
        Map<String,Value> copy=new LinkedHashMap<>(source.members());copy.putAll(added.members());return new Obj(copy);
    }
    public static Obj empty() { return new Obj(Map.of()); }
    public static Text text(String value) { return new Text(StrictJson.text(value)); }
    public static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    public static IntegerValue number(BigInteger value) { return new IntegerValue(value); }
    public static Arr numbers(List<Integer> values) { return new Arr(values.stream().<Value>map(MilitaryPlanInputs::number).toList()); }
    public static Arr objects(List<Obj> values) { return new Arr(values.stream().<Value>map(v->v).toList()); }
    public static Arr strings(List<String> values) { return new Arr(values.stream().<Value>map(Text::new).toList()); }
    public static Value nullable(Value value) { return value==null?Nil.INSTANCE:value; }
    public static boolean yes(Value value) { return new Bool(true).equals(value); }
    public static boolean no(Value value) { return new Bool(false).equals(value); }
    public static String optionalText(Value value) {
        if(value==null||value==Nil.INSTANCE)return null;
        return OpportunityJson.text(value,"military text");
    }
    public static Integer optionalInt(Value value) {
        if(value==null||value==Nil.INSTANCE)return null;
        BigInteger n=OpportunityJson.integer(value,"military signed32");
        require(n.compareTo(BigInteger.valueOf(Integer.MIN_VALUE))>=0&&n.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"military signed32 width");
        return n.intValueExact();
    }
    public static BigInteger optionalInteger(Value value) {
        return value==null||value==Nil.INSTANCE?null:OpportunityJson.integer(value,"military exact integer");
    }
    public static int id(Value value) {
        Integer n=optionalInt(value);require(n!=null&&n>=0,"public military ID required");return n;
    }
    public static int int32(Value value) {
        Integer n=optionalInt(value);require(n!=null,"required exact signed32 integer");return n;
    }
    public static int province(Value value) {
        Integer n=optionalInt(value);require(n!=null&&n>0,"positive Province ID required");return n;
    }
    public static List<Obj> rows(Value value) {
        List<Obj> out=new ArrayList<>();
        for(Value row:OpportunityJson.array(value,"military row array"))out.add(OpportunityJson.object(row,"military row"));
        return List.copyOf(out);
    }
    public static Optional<List<Integer>> route(Value value) {
        if(value==null||value==Nil.INSTANCE)return Optional.empty();
        List<Integer> out=new ArrayList<>();
        for(Value item:OpportunityJson.array(value,"original route"))out.add(province(item));
        return Optional.of(List.copyOf(out));
    }
    public static List<Integer> ids(Value value) {
        List<Integer> out=new ArrayList<>();
        for(Value item:OpportunityJson.array(value,"original IDs"))out.add(id(item));
        return List.copyOf(out);
    }
    public static Obj frame(PlanningRequest request) {
        var before=request.before().frame();var identity=before.identity();
        return obj(f("played_character_id",number(identity.player())),f("native_revision",number(identity.nativeRevision())),
                f("date_raw",number(identity.dateRaw())),f("snapshot_id",text(before.snapshotId())),
                f("revision",number(before.revision())),f("episode_run_id",text(before.episodeRunId())));
    }
    public static String command(Obj row) {
        String command=optionalText(row.get("command"));
        if(!"auto-turn".equals(command))return command;
        Value result=row.get("result");
        if(!(result instanceof Obj r)||!(r.get("auto_turn") instanceof Obj auto))return null;
        return optionalText(auto.get("selected_step"));
    }
    public static Obj result(Obj row) {
        if(!(row.get("result") instanceof Obj result))return null;
        if(!new Text("auto-turn").equals(row.get("command")))return result;
        for(String field:List.of("assault_action","route_preview","war_action","war_progress_before","war_progress_after"))
            if(result.get(field) instanceof Obj)return result;
        return result.get("auto_turn") instanceof Obj auto&&auto.get("result") instanceof Obj nested?nested:result;
    }
    public static List<Obj> afterRestore(List<Obj> history) {
        int first=0;
        for(int i=0;i<history.size();i++)
            if("restore-checkpoint".equals(command(history.get(i)))&&yes(history.get(i).get("ok")))first=i+1;
        return List.copyOf(history.subList(first,history.size()));
    }
    public static boolean sameLease(PlanningRequest request,Obj result) {
        Obj snapshot=request.observations().snapshot();Value diagnostics=snapshot.get("diagnostics");
        return snapshot.get("snapshot_id") instanceof Text snapshotId&&!snapshotId.value().isBlank()
                &&snapshot.get("episode_run_id") instanceof Text episode&&!episode.value().isBlank()
                &&exactUint64(snapshot.get("revision"),false)&&exactUint64(snapshot.get("native_revision"),true)
                &&diagnostics instanceof Obj d&&exactUint64(d.get("connection_generation"),true)
                &&result.get("queried_snapshot_id") instanceof Text&&result.get("queried_episode_run_id") instanceof Text
                &&exactUint64(result.get("queried_revision"),false)&&exactUint64(result.get("queried_native_revision"),true)
                &&exactUint64(result.get("queried_connection_generation"),true)
                &&Objects.equals(result.get("queried_snapshot_id"),snapshot.get("snapshot_id"))
                &&Objects.equals(result.get("queried_revision"),snapshot.get("revision"))
                &&Objects.equals(result.get("queried_native_revision"),snapshot.get("native_revision"))
                &&Objects.equals(result.get("queried_episode_run_id"),snapshot.get("episode_run_id"))
                &&Objects.equals(result.get("queried_connection_generation"),d.get("connection_generation"));
    }
    private static boolean exactUint64(Value value,boolean positive) {
        return value instanceof IntegerValue integer&&integer.value().signum()>=(positive?1:0)
                &&integer.value().compareTo(StrictJson.UINT64_MAX)<=0;
    }
    public static boolean mergeBarrier(Obj row,int army) {
        if(!yes(row.get("ok")))return false;
        String command=command(row);
        if(command==null||!command.startsWith("merge-armies-"))return false;
        String[] pair=command.substring("merge-armies-".length()).split("-with-",-1);
        if(pair.length!=2)return false;
        try { return Integer.parseInt(pair[0])==army||Integer.parseInt(pair[1])==army; }
        catch(NumberFormatException invalid) { return false; }
    }
    public record Army(int id,Integer owner,Integer current,String state,Boolean inCombat,Boolean retreating,
                       Integer stateCode,boolean controllable,Optional<List<Integer>> route,
                       boolean moveTargetPresent,Integer target,String routeReadStatus,Obj raw) {
        public Army { route=route.map(List::copyOf);Objects.requireNonNull(raw); }
        public boolean explicitIdle() {
            return "regular".equals(state)&&Boolean.FALSE.equals(inCombat)&&Boolean.FALSE.equals(retreating)
                    &&"complete_empty".equals(routeReadStatus)&&route.isPresent()&&route.orElseThrow().isEmpty()
                    &&moveTargetPresent&&target==null;
        }
        public String tacticalState() {
            if(Boolean.TRUE.equals(retreating))return "retreating";
            if(Boolean.TRUE.equals(inCombat))return "combat";
            if(state!=null)return state.toLowerCase(java.util.Locale.ROOT);
            if(stateCode==null)return null;
            return switch(stateCode){case 2->"combat";case 3->"sieging";case 6->"retreating";case 7->"moving";default->null;};
        }
        public MilitaryRouteGeometry.Enemy geometry() {
            return new MilitaryRouteGeometry.Enemy(id,Optional.ofNullable(current).filter(value->value>0),Optional.ofNullable(target).filter(value->value>0),
                    route.orElse(List.of()),"retreating".equals(tacticalState())
                    ?MilitaryRouteGeometry.TacticalState.RETREATING:MilitaryRouteGeometry.TacticalState.OTHER);
        }
    }
    public static Army army(Obj row) {
        var observed=org.xar.ck3.control.nativebridge.capabilities.army.NativeArmiesCodec.normalizeArmy(
                OpportunityJson.toNode(row),"planner army");
        // The complete native contract retains wide observations. These strategy APIs
        // still require signed32 addresses; exact conversion rejects unsupported width.
        Obj canonical=org.xar.ck3.control.application.driver.DriverJson.object(
                org.xar.ck3.control.nativebridge.capabilities.army.NativeArmiesCodec.encodeArmy(observed)
                        .toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),
                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        java.util.function.Function<BigInteger,Integer> address=value->optionalInt(number(value));
        return new Army(observed.armyId().value(),address.apply(observed.ownerCharacterId()),
                observed.currentProvinceId().map(address).orElse(null),observed.armyState().orElse(null),
                observed.inCombat().orElse(null),observed.retreating().orElse(null),
                observed.armyStateCode().map(address).orElse(null),observed.controllable(),
                observed.routeProvinceIds(),row.members().containsKey("move_target_province_id"),
                observed.moveTargetProvinceId().map(address).orElse(null),
                observed.routeEvidence().map(evidence->evidence.status().wire()).orElse(null),canonical);
    }
    public static List<Army> armies(PlanningRequest request) {
        // war_contract.player_armies_from_state1568..1587: first public-ID
        // occurrence wins, including controllable allied-army rows.
        Map<Integer,Army> first=new LinkedHashMap<>();
        for(Obj row:rows(request.observations().snapshot().get("player_armies"))) {
            Army army=army(row);first.putIfAbsent(army.id(),army);
        }
        for(Obj war:wars(request))for(Obj row:rows(war.get("allied_armies"))) {
            Army army=army(row);if(army.controllable())first.putIfAbsent(army.id(),army);
        }
        return List.copyOf(first.values());
    }
    public static List<Obj> wars(PlanningRequest request) { return rows(request.observations().snapshot().get("active_wars")); }
    /** Actual history producer into the already qualified preview lease/restore/merge reducer. */
    public static Optional<org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.Preview> freshPreview(
            PlanningRequest request,Army subject,int target) {
        require(subject.current()!=null&&subject.current()>0,"preview requires current Province");
        Obj lookup=obj(f("commands",objects(request.observations().history())),f("snapshot",request.observations().snapshot()),
                f("army_id",number(subject.id())),f("origin_province_id",number(subject.current())),f("target_province_id",number(target)),
                f("date_raw",number(request.before().frame().identity().dateRaw())));
        return org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.freshPreview(
                org.xar.ck3.control.wave3.military.routereroute.RoutePreviewConsumerCodec.decode(OpportunityJson.encode(lookup)));
    }
    public static Obj previewDocument(org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.Preview preview) {
        return OpportunityJson.object(OpportunityJson.parse(
                org.xar.ck3.control.wave3.military.routereroute.RoutePreviewConsumerCodec.encode(Optional.of(preview))),"native route preview");
    }
    public static boolean advertised(PlanningRequest request,String step) {
        return request.observations().actionSteps().contains(new org.xar.ck3.control.application.action.OperationKey(step));
    }
    public static Obj auditDocument(MilitaryRouteGeometry.Audit audit) {
        if(audit.status()==MilitaryRouteGeometry.Status.ROUTE_DOES_NOT_REACH_TARGET)return obj(f("status",text("unavailable")),
                f("target_province_id",number(audit.targetProvinceId())),f("route_province_ids",numbers(audit.routeProvinceIds())),f("reason",text("route_does_not_reach_target")));
        List<Obj> conflicts=new ArrayList<>();
        for(var conflict:audit.conflicts()) {
            String kind=conflict.kind().name().toLowerCase(java.util.Locale.ROOT);
            Obj row=obj(f("kind",text(kind)),f("enemy_army_id",conflict.enemyArmyId()==null?Nil.INSTANCE:number(conflict.enemyArmyId())),
                    f(conflict.kind()==MilitaryRouteGeometry.ConflictKind.OPPOSITE_EDGE_INTERSECTION?"from_province_id":"province_id",number(conflict.provinceId())));
            if(conflict.toProvinceId().isPresent())row=put(row,"to_province_id",number(conflict.toProvinceId().orElseThrow()));
            if(conflict.playerHop().isPresent())row=put(row,"player_hop",number(conflict.playerHop().orElseThrow()));
            if(conflict.enemyHop().isPresent())row=put(row,"enemy_hop",number(conflict.enemyHop().orElseThrow()));
            conflicts.add(row);
        }
        return obj(f("status",text(audit.status()==MilitaryRouteGeometry.Status.SAFE?"safe":audit.status()==MilitaryRouteGeometry.Status.SAFE_ONE_DAY_CONTACT_HORIZON?"safe_one_day_contact_horizon":"unsafe")),
                f("target_province_id",number(audit.targetProvinceId())),f("route_province_ids",numbers(audit.routeProvinceIds())),f("conflicts",objects(conflicts)));
    }
    public static List<Army> enemies(PlanningRequest request) {
        Map<Integer,Army> first=new LinkedHashMap<>();
        for(Obj war:wars(request)) {
            Value enemies=war.get("enemy_armies");
            if(enemies==null||enemies==Nil.INSTANCE)continue;
            for(Obj row:rows(enemies)) {
                Integer id=optionalInt(row.get("army_id"));
                if(id!=null&&id>=0)first.putIfAbsent(id,army(row));
            }
        }
        return List.copyOf(first.values());
    }
    /** Original native_driver33786 excludes only explicitly observed retreat states. */
    public static List<Integer> hostiles(PlanningRequest request) {
        return enemies(request).stream().filter(a->!Boolean.TRUE.equals(a.retreating())
                &&!"retreating".equals(a.state())&&!Integer.valueOf(6).equals(a.stateCode()))
                .map(Army::id).distinct().sorted().toList();
    }
    public record Balance(BigInteger friendlyCurrent,BigInteger enemyCurrent,BigInteger friendlyPower,
                          BigInteger enemyPower,Obj original) {
        public boolean hostileOvermatch() {
            return enemyCurrent.multiply(BigInteger.valueOf(4)).compareTo(friendlyCurrent.multiply(BigInteger.valueOf(5)))>0
                    ||enemyPower.multiply(BigInteger.valueOf(4)).compareTo(friendlyPower.multiply(BigInteger.valueOf(5)))>0;
        }
    }
    public static Optional<Balance> balance(PlanningRequest request,int war) {
        Obj snapshot=request.observations().snapshot();
        if(!request.observations().paused()||!(new Text("available").equals(snapshot.get("army_strengths_status"))||new Text("partial").equals(snapshot.get("army_strengths_status")))
                ||!(snapshot.get("army_strengths") instanceof Arr))return Optional.empty();
        var friendly=new ArrayList<Obj>();var enemy=new ArrayList<Obj>();var all=new ArrayList<Obj>();
        for(Obj row:rows(snapshot.get("army_strengths"))) {
            if(!(row.get("war_ids") instanceof Arr)||!ids(row.get("war_ids")).contains(war))continue;
            if(!new Text("available").equals(row.get("status")))return Optional.empty();
            id(row.get("army_id"));all.add(row);
            String role=optionalText(row.get("scope_role"));
            if("player".equals(role)||"active_war_ally".equals(role))friendly.add(row);
            else if("active_war_enemy".equals(role))enemy.add(row);
        }
        if(friendly.isEmpty()||enemy.isEmpty())return Optional.empty();
        var measured=new ArrayList<Obj>(friendly);measured.addAll(enemy);
        for(Obj row:measured)for(String field:List.of("current_soldiers","maximum_soldiers","ai_base_power_raw"))
            if(optionalInteger(row.get(field))==null)return Optional.empty();
        BigInteger fc=sum(friendly,"current_soldiers"),ec=sum(enemy,"current_soldiers");
        BigInteger fp=sum(friendly,"ai_base_power_raw"),ep=sum(enemy,"ai_base_power_raw");
        Obj original=obj(f("status",text("available")),f("war_id",number(war)),
                f("friendly_army_ids",numbers(friendly.stream().map(row->id(row.get("army_id"))).sorted().toList())),
                f("enemy_army_ids",numbers(enemy.stream().map(row->id(row.get("army_id"))).sorted().toList())),
                f("friendly_current_soldiers",number(fc)),f("enemy_current_soldiers",number(ec)),
                f("friendly_maximum_soldiers",number(sum(friendly,"maximum_soldiers"))),
                f("enemy_maximum_soldiers",number(sum(enemy,"maximum_soldiers"))),
                f("friendly_ai_base_power_raw",number(fp)),f("enemy_ai_base_power_raw",number(ep)),
                f("hostile_operational_overmatch",new Bool(ec.multiply(BigInteger.valueOf(4)).compareTo(fc.multiply(BigInteger.valueOf(5)))>0
                    ||ep.multiply(BigInteger.valueOf(4)).compareTo(fp.multiply(BigInteger.valueOf(5)))>0)),
                f("interpretation",text("operational_routing_risk_not_battle_win_odds")));
        return Optional.of(new Balance(fc,ec,fp,ep,original));
    }
    private static BigInteger sum(List<Obj> rows,String field) {
        return rows.stream().map(row->OpportunityJson.integer(row.get(field),field)).reduce(BigInteger.ZERO,BigInteger::add);
    }
    public static void require(boolean condition,String message) { StrictJson.require(condition,message); }
}


