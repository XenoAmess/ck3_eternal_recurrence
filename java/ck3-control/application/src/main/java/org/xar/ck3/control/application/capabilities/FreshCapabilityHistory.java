package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.application.capabilities.CapabilityJson.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Native Driver-owned history consumers, preserving latest failures as scope tombstones. */
public final class FreshCapabilityHistory {
    private static final Pattern OCCUPATION_QUERY = Pattern.compile("query-war-occupation-targets-v1-([1-9][0-9]*)");
    private static final Pattern PREVIEW = Pattern.compile("preview-move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)");
    private static final Pattern RETREAT_ORDER = Pattern.compile("order-active-combat-retreat-v1-(0|[1-9][0-9]*)-revision-(0|[1-9][0-9]*)-combat-(-?(?:0|[1-9][0-9]*))-side-([01])-scope-(full_side|owner_subset)-to-([1-9][0-9]*)-token-([A-Za-z0-9_-]{32,128})");
    private static final Set<String> TOKEN_KEYS = Set.of("candidate_token","order_step","source_binding","battle_control_snapshot","battle_binding","target_province_id","route_preview");
    private FreshCapabilityHistory() { }
    public record Occupation(Set<Integer> opposingOccupiedTargets,List<Obj> holdingSiegeStates) {
        public Occupation { opposingOccupiedTargets = Set.copyOf(opposingOccupiedTargets); holdingSiegeStates = List.copyOf(holdingSiegeStates); }
    }
    public static List<Obj> afterLatestRestore(List<Obj> history) {
        List<Obj> owned = List.copyOf(history);
        for (int i = owned.size() - 1; i >= 0; i--) if (named(owned.get(i),"command","restore-checkpoint") && yes(owned.get(i),"ok")) return List.copyOf(owned.subList(i + 1,owned.size()));
        return owned;
    }
    public static List<Obj> last128(List<Obj> history) { return List.copyOf(history.subList(Math.max(0,history.size() - 128),history.size())); }
    public static Occupation occupation(Obj snapshot,List<Obj> ownedTail) {
        Set<Integer> targets = new TreeSet<>(), seenWars = new HashSet<>(); List<Obj> states = new ArrayList<>();
        Obj player = obj(snapshot.get("played_character")).orElse(null);
        if (!yes(snapshot,"paused") || !yes(player,"alive") || !int32Id(player.get("character_id"))) return new Occupation(targets,states);
        List<Obj> fresh = afterLatestRestore(ownedTail);
        for (int i = fresh.size() - 1; i >= 0; i--) {
            Obj row = fresh.get(i); Matcher match = OCCUPATION_QUERY.matcher(Optional.ofNullable(textOrNull(row,"command")).orElse(""));
            if (!match.matches()) continue;
            Optional<Integer> parsed = int32(match.group(1),false); if (parsed.isEmpty() || !seenWars.add(parsed.orElseThrow())) continue;
            int warId = parsed.orElseThrow();
            List<Obj> wars = rows(snapshot.get("active_wars")).stream().filter(w -> eq(w,"war_id",iv(warId))).toList();
            if (wars.size() != 1 || !Set.of("attacker","defender").contains(Optional.ofNullable(textOrNull(wars.getFirst(),"player_side")).orElse(""))) continue;
            String side = textOrNull(wars.getFirst(),"player_side");
            Obj result = obj(row.get("result")).orElse(null), value = result == null ? null : obj(result.get("war_occupation_targets_v1")).orElse(null);
            if (!yes(row,"ok") || value == null || !yes(value,"available") || !yes(value,"collection_complete") || !eq(value,"war_id",iv(warId))
                    || !eq(value,"actor_character_id",player.get("character_id")) || !named(value,"player_side",side)
                    || !equalField(value,"snapshot_revision",snapshot,"native_revision") || !equalField(value,"date_raw",snapshot,"date_raw") || !sameQuery(snapshot,result)) continue;
            String opposite = "defender".equals(side) ? "attacker" : "defender";
            for (Obj holding : requiredRows(value,"rows")) {
                if (int32Id(holding.get("province_id")) && named(holding,"territory_side",side) && yes(holding,"occupation_observable")
                        && yes(holding,"is_occupied") && named(holding,"occupier_side",opposite) && yes(holding,"counted_occupied_by_opposing_side")) targets.add(idAt(holding,"province_id"));
                Map<String,Value> material = new LinkedHashMap<>(); material.put("war_id",iv(warId));
                for (String field : List.of("province_id","siege_observable","active_siege","occupation_observable","is_occupied","occupying_character_id","occupier_side"))
                    material.put(field,holding.members().containsKey(field) ? holding.get(field) : Nil.INSTANCE);
                material.put("observation_source",new Text("war_occupation_query")); states.add(new Obj(material));
            }
        }
        return new Occupation(targets,states);
    }
    public static Set<String> firstHopSteps(Obj snapshot,List<Obj> ownedTail,Set<String> advertised,Set<String> caps) {
        Set<String> steps = new TreeSet<>();
        if (!yes(snapshot,"paused") || !yes(snapshot,"map_ready") || !nil(snapshot,"active_event") || !nil(snapshot,"pending_character_interaction")
                || !caps.containsAll(Set.of(NativeActionSteps.PREVIEW,NativeActionSteps.MOVE,NativeActionSteps.HORIZON))) return steps;
        List<Integer> hostiles = hostileIds(snapshot);
        if (hostiles.isEmpty() || hostiles.size() > 64 || textOrNull(snapshot,"episode_run_id") == null) return steps;
        Set<String> seen = new HashSet<>(); List<Obj> fresh = afterLatestRestore(ownedTail);
        for (int i = fresh.size() - 1; i >= 0; i--) {
            Obj row = fresh.get(i); String command = textOrNull(row,"command"); Matcher match = PREVIEW.matcher(command == null ? "" : command);
            if (!match.matches() || !seen.add(command) || !advertised.contains(command)) continue;
            Optional<Integer> armyId = int32(match.group(1),true), targetId = int32(match.group(2),false);
            if (armyId.isEmpty() || targetId.isEmpty()) continue;
            Obj army = army(snapshot,armyId.orElseThrow()).orElse(null), result = obj(row.get("result")).orElse(null);
            Obj preview = result == null ? null : obj(result.get("route_preview")).orElse(null);
            if (!yes(row,"ok") || !sameQuery(snapshot,result) || !yes(army,"controllable") || !int32Id(army.get("current_province_id"))
                    || preview == null || !named(preview,"status","available") || !eq(preview,"army_id",iv(armyId.orElseThrow()))
                    || !eq(preview,"origin_province_id",army.get("current_province_id")) || !eq(preview,"target_province_id",iv(targetId.orElseThrow()))
                    || !equalField(preview,"previewed_date_raw",snapshot,"date_raw") || !(preview.get("route_province_ids") instanceof Arr route)) continue;
            List<Value> remaining = route.items();
            if (!remaining.isEmpty() && remaining.getFirst().equals(army.get("current_province_id"))) remaining = remaining.subList(1,remaining.size());
            if (remaining.size() <= 1 || !remaining.getLast().equals(iv(targetId.orElseThrow())) || remaining.stream().anyMatch(v -> !int32Id(v))) continue;
            int hop = integer(remaining.getFirst(),"first hop").intValueExact();
            steps.add(NativeActionSteps.preview(armyId.orElseThrow(),hop)); steps.add(NativeActionSteps.horizon(armyId.orElseThrow(),hop,hostiles));
            if (!NativeActionSteps.combat(army)) steps.add(NativeActionSteps.move(armyId.orElseThrow(),hop));
        }
        return steps;
    }
    public static Set<String> retreatPreviewSteps(Obj snapshot,Set<String> advertised) {
        Set<String> result = new TreeSet<>(); if (!yes(snapshot,"paused")) return result;
        for (String step : advertised) {
            Matcher match = PREVIEW.matcher(step); if (!match.matches()) continue;
            Optional<Integer> selected = int32(match.group(1),true), target = int32(match.group(2),false);
            if (selected.isEmpty() || target.isEmpty()) continue;
            Obj army = army(snapshot,selected.orElseThrow()).orElse(null);
            if (yes(army,"controllable") && NativeActionSteps.combat(army) && !eq(army,"current_province_id",iv(target.orElseThrow())))
                result.add("preview-active-combat-retreat-v1-" + selected.orElseThrow() + "-to-" + target.orElseThrow());
        }
        return result;
    }
    public static Optional<String> retreatOrder(Obj snapshot,Obj token) {
        if (token == null || !token.members().keySet().equals(TOKEN_KEYS) || !yes(snapshot,"paused")) return Optional.empty();
        Obj source = obj(token.get("source_binding")).orElse(null), battle = obj(token.get("battle_binding")).orElse(null), diagnostics = obj(snapshot.get("diagnostics")).orElse(null);
        if (source == null || battle == null || diagnostics == null) return Optional.empty();
        for (String key : List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id")) if (!equalField(source,key,snapshot,key)) return Optional.empty();
        if (!equalField(source,"connection_generation",diagnostics,"connection_generation")) return Optional.empty();
        String order = textOrNull(token,"order_step"); Matcher match = RETREAT_ORDER.matcher(order == null ? "" : order);
        if (!match.matches() || !eq(token,"candidate_token",new Text(match.group(7))) || !eq(source,"revision",iv(match.group(2)))
                || !eq(battle,"combat_id",iv(match.group(3))) || !eq(battle,"selected_public_cunit_id",iv(match.group(1)))
                || !eq(battle,"side_index",iv(match.group(4))) || !named(battle,"side_scope",match.group(5)) || !eq(token,"target_province_id",iv(match.group(6)))) return Optional.empty();
        BigInteger revision = new BigInteger(match.group(2)), combat = new BigInteger(match.group(3));
        Optional<Integer> selected = int32(match.group(1),true), target = int32(match.group(6),false);
        if (selected.isEmpty() || target.isEmpty() || revision.bitLength() > 64 || combat.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) < 0
                || combat.compareTo(INT32_MAX) > 0 || combat.equals(BigInteger.valueOf(-1))) return Optional.empty();
        Obj army = army(snapshot,selected.orElseThrow()).orElse(null);
        return yes(army,"controllable") && NativeActionSteps.combat(army) && equalField(army,"current_province_id",battle,"combat_province_id") ? Optional.of(order) : Optional.empty();
    }
    public static Optional<List<Integer>> sentinelWatch(Obj snapshot) {
        if (snapshot == null || !(snapshot.get("player_armies") instanceof Arr armies)) return Optional.empty();
        Set<Integer> ids = new TreeSet<>();
        for (Value value : armies.items()) {
            if (!(value instanceof Obj army)) return Optional.empty();
            if (!yes(army,"controllable")) continue;
            if (!unitId(army.get("army_id")) || !ids.add(integerAt(army,"army_id").intValueExact())) return Optional.empty();
        }
        return ids.isEmpty() || ids.size() > 64 ? Optional.empty() : Optional.of(List.copyOf(ids));
    }
    public static Optional<Obj> completedTerminal(List<Obj> fullOwnedHistory,String episodeRunId) {
        for (int i = fullOwnedHistory.size() - 1; i >= 0; i--) {
            Obj row = fullOwnedHistory.get(i); if (!named(row,"command","death-terminal")) continue;
            Obj result = obj(row.get("result")).orElse(null), score = result == null ? null : result;
            if (!yes(row,"ok") || result == null || !yes(result,"terminal") || !named(result,"settlement_status","complete")) return Optional.empty();
            Obj settlement = obj(result.get("one_life_settlement")).orElse(null), strategy = obj(result.get("cross_run_strategy")).orElse(null);
            Obj recorded = strategy == null ? null : obj(strategy.get("recorded_episode")).orElse(null);
            if (settlement == null || nil(settlement,"final_score") || recorded == null || !named(recorded,"run_id",episodeRunId)
                    || !numeric(result.get("score")) || !numericEqual(recorded.get("score"),result.get("score"))) return Optional.empty();
            return Optional.of(result);
        }
        return Optional.empty();
    }
    public static List<Integer> hostileIds(Obj snapshot) {
        return NativeActionSteps.enemies(rows(snapshot.get("active_wars"))).stream().filter(e -> unitId(e.get("army_id")) && !NativeActionSteps.retreating(e))
                .map(e -> integerAt(e,"army_id").intValueExact()).distinct().sorted().toList();
    }
    public static boolean sameQuery(Obj snapshot,Obj result) {
        if (snapshot == null || result == null) return false;
        Obj diagnostics = obj(snapshot.get("diagnostics")).orElse(null);
        if (diagnostics == null) return false;
        for (String field : List.of("snapshot_id","revision","native_revision","episode_run_id")) if (!equalField(result,"queried_" + field,snapshot,field)) return false;
        return equalField(result,"queried_connection_generation",diagnostics,"connection_generation");
    }
    private static Optional<Obj> army(Obj snapshot,int armyId) { return rows(snapshot.get("player_armies")).stream().filter(a -> eq(a,"army_id",iv(armyId))).findFirst(); }
    private static Optional<Integer> int32(String text,boolean allowZero) {
        BigInteger n = new BigInteger(text); return n.signum() >= (allowZero ? 0 : 1) && n.compareTo(INT32_MAX) <= 0 ? Optional.of(n.intValueExact()) : Optional.empty();
    }
    private static IntegerValue iv(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static IntegerValue iv(String value) { return new IntegerValue(new BigInteger(value)); }
    private static boolean numeric(Value value) { return value instanceof IntegerValue || value instanceof DecimalValue; }
    private static boolean numericEqual(Value a,Value b) {
        if (!numeric(a) || !numeric(b)) return false;
        return decimal(a).compareTo(decimal(b)) == 0;
    }
    private static BigDecimal decimal(Value value) { return value instanceof IntegerValue i ? new BigDecimal(i.value()) : new BigDecimal(((DecimalValue)value).token()); }
}
