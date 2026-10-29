package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;

/** Original recent-war history reducer. Tactical hints grant no native outcome, action or replay authority. */
public final class WarRecentTactics {
    private static final BigInteger HOURS = BigInteger.valueOf(24);
    private static final BigInteger COOLDOWN_HOURS = BigInteger.valueOf(90 * 24);
    private static final BigInteger STALE_DAYS = BigInteger.valueOf(14);
    private static final BigInteger DEFEAT_DROP = BigInteger.valueOf(20);
    private WarRecentTactics() { }

    public record Tactics(List<Integer> blockedEnemyIds, List<Integer> blockedProvinceIds,
            Optional<Boolean> contactStale, BigInteger retreatDays, List<Integer> completedObjectiveProvinceIds) {
        public Tactics {
            blockedEnemyIds = ids(blockedEnemyIds, true); blockedProvinceIds = ids(blockedProvinceIds, false);
            completedObjectiveProvinceIds = ids(completedObjectiveProvinceIds, false);
            Objects.requireNonNull(contactStale); Objects.requireNonNull(retreatDays);
            StrictJson.require(retreatDays.signum() >= 0, "nonnegative exact observed retreat duration required");
            boolean blocked = !blockedEnemyIds.isEmpty() || !blockedProvinceIds.isEmpty();
            if (contactStale.isPresent()) StrictJson.require(contactStale.orElseThrow() == blocked, "contact state differs from active collision blocks");
            else StrictJson.require(!blocked && retreatDays.signum() == 0 && completedObjectiveProvinceIds.isEmpty(), "absent tactical IDs retain the original empty result only");
        }
        public Obj toJson() {
            Map<String, Value> fields = new LinkedHashMap<>();
            fields.put("blocked_enemy_ids", numbers(blockedEnemyIds)); fields.put("blocked_province_ids", numbers(blockedProvinceIds));
            contactStale.ifPresent(value -> fields.put("contact_stale", new Bool(value)));
            fields.put("retreat_days", number(retreatDays)); fields.put("completed_objective_province_ids", numbers(completedObjectiveProvinceIds));
            return new Obj(fields);
        }
    }

    /** The real early-war planner consumer uses the same frozen snapshot and full surviving Driver rows. */
    public static Obj collect(PlanningRequest request, int armyId, int warId) {
        Objects.requireNonNull(request);
        return evaluate(request.observations().history(), request.observations().snapshot(), OptionalInt.of(armyId), OptionalInt.of(warId)).toJson();
    }

    public static Tactics evaluate(List<Obj> originalHistory, Obj currentSnapshot, OptionalInt armyId, OptionalInt warId) {
        Objects.requireNonNull(originalHistory); Objects.requireNonNull(currentSnapshot);
        Objects.requireNonNull(armyId); Objects.requireNonNull(warId);
        List<Obj> history = List.copyOf(originalHistory);
        if (armyId.isEmpty() || warId.isEmpty()) return new Tactics(List.of(), List.of(), Optional.empty(), BigInteger.ZERO, List.of());
        StrictJson.require(armyId.getAsInt() >= 0 && warId.getAsInt() > 0, "actual public CUnit including zero and positive WarID required");
        Optional<BigInteger> currentDate = exact(currentSnapshot.get("date_raw"));
        Map<Integer, BigInteger> blockedEnemies = new HashMap<>();
        Map<Integer, BigInteger> blockedProvinces = new HashMap<>();
        Set<Integer> completed = new TreeSet<>();
        BigInteger contactDays = BigInteger.ZERO, retreatDays = BigInteger.ZERO;
        int contactProbes = 0;
        for (Obj row : afterRestore(history)) {
            if (!WarHistorySteps.isLifeAdvance(command(row)) || !yes(row.get("ok"))) continue;
            // The original helper reads factual root progress, never the nested selected plan.
            Optional<Obj> result = object(row.get("result"));
            var before = WarHistorySteps.progressSlice(result, WarHistorySteps.ProgressPhase.BEFORE, warId.getAsInt());
            var after = WarHistorySteps.progressSlice(result, WarHistorySteps.ProgressPhase.AFTER, warId.getAsInt());
            if (before.war().isEmpty()) continue;
            Obj beforeWar = before.war().orElseThrow();
            Optional<Obj> beforePlayer = WarHistorySteps.progressArmy(before.war(), WarHistorySteps.ArmyRole.PLAYER, armyId.getAsInt());
            Optional<Obj> afterPlayer = WarHistorySteps.progressArmy(after.war(), WarHistorySteps.ArmyRole.PLAYER, armyId.getAsInt());
            BigInteger elapsed = before.dateRaw().isPresent() && after.dateRaw().isPresent()
                    ? after.dateRaw().orElseThrow().subtract(before.dateRaw().orElseThrow()).divide(HOURS).max(BigInteger.ZERO) : BigInteger.ZERO;
            retreatDays = WarHistorySteps.armyTacticalState(afterPlayer).filter("retreating"::equals).isPresent()
                    ? retreatDays.add(elapsed) : BigInteger.ZERO;
            OptionalInt province = beforePlayer.map(value -> province(value.get("current_province_id"))).orElseGet(OptionalInt::empty);
            Set<Integer> local = new HashSet<>();
            if (province.isPresent()) for (Obj enemy : objects(beforeWar.get("enemy_armies"))) {
                OptionalInt id = unit(enemy.get("army_id"));
                OptionalInt location = province(enemy.get("current_province_id"));
                if (id.isPresent() && location.isPresent() && location.getAsInt() == province.getAsInt()
                        && WarHistorySteps.armyTacticalState(Optional.of(enemy)).filter("retreating"::equals).isEmpty()) local.add(id.getAsInt());
            }
            Set<Integer> afterEnemies = new HashSet<>();
            after.war().ifPresent(war -> {
                for (Obj enemy : objects(war.get("enemy_armies"))) unit(enemy.get("army_id")).ifPresent(afterEnemies::add);
            });
            Optional<BigInteger> beforeScore = exact(beforeWar.get("player_relative_war_score"));
            Optional<BigInteger> afterScore = after.war().flatMap(war -> exact(war.get("player_relative_war_score")));
            boolean improved = beforeScore.isPresent() && afterScore.isPresent()
                    && afterScore.orElseThrow().compareTo(beforeScore.orElseThrow()) > 0;
            if (province.isPresent() && WarHistorySteps.armyTacticalState(beforePlayer).filter("sieging"::equals).isPresent()
                    && WarHistorySteps.progressSiegeObjectives(beforeWar).contains(BigInteger.valueOf(province.getAsInt()))
                    && WarHistorySteps.armyTacticalState(afterPlayer).filter("sieging"::equals).isEmpty()
                    && (after.war().isEmpty() || improved)) completed.add(province.getAsInt());
            boolean vanished = local.stream().anyMatch(id -> !afterEnemies.contains(id));
            if (improved || vanished) {
                contactDays = BigInteger.ZERO; contactProbes = 0;
                local.forEach(blockedEnemies::remove); province.ifPresent(blockedProvinces::remove);
            } else if (!local.isEmpty()) {
                contactDays = contactDays.add(elapsed); contactProbes++;
                if (contactDays.compareTo(STALE_DAYS) >= 0 || contactProbes >= 2)
                    block(local, province, after.dateRaw(), blockedEnemies, blockedProvinces);
            }
            if (beforeScore.isPresent() && afterScore.isPresent()
                    && beforeScore.orElseThrow().subtract(afterScore.orElseThrow()).compareTo(DEFEAT_DROP) >= 0 && !local.isEmpty())
                block(local, province, after.dateRaw(), blockedEnemies, blockedProvinces);
        }
        List<Integer> activeEnemies = active(blockedEnemies, currentDate), activeProvinces = active(blockedProvinces, currentDate);
        return new Tactics(activeEnemies, activeProvinces, Optional.of(!activeEnemies.isEmpty() || !activeProvinces.isEmpty()), retreatDays, new ArrayList<>(completed));
    }

    private static void block(Set<Integer> enemies, OptionalInt province, Optional<BigInteger> date,
            Map<Integer, BigInteger> blockedEnemies, Map<Integer, BigInteger> blockedProvinces) {
        if (date.isEmpty()) return;
        BigInteger until = date.orElseThrow().add(COOLDOWN_HOURS);
        for (int enemy : enemies) blockedEnemies.put(enemy, until);
        province.ifPresent(value -> blockedProvinces.put(value, until));
    }
    private static List<Integer> active(Map<Integer, BigInteger> blocked, Optional<BigInteger> current) {
        return blocked.entrySet().stream().filter(entry -> current.isEmpty() || current.orElseThrow().compareTo(entry.getValue()) < 0)
                .map(Map.Entry::getKey).sorted().toList();
    }
    private static List<Integer> ids(List<Integer> values, boolean zero) {
        List<Integer> result = List.copyOf(values); int previous = -1;
        for (int value : result) { StrictJson.require(value >= (zero ? 0 : 1) && value > previous, "unique ordered tactical IDs required"); previous = value; }
        return result;
    }
    private static Optional<BigInteger> exact(Value value) { return value instanceof IntegerValue number ? Optional.of(number.value()) : Optional.empty(); }
    private static OptionalInt unit(Value value) { return id(value, true); }
    private static OptionalInt province(Value value) { return id(value, false); }
    private static OptionalInt id(Value value, boolean zero) {
        if (!(value instanceof IntegerValue number) || number.value().compareTo(BigInteger.valueOf(zero ? 0 : 1)) < 0
                || number.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0) return OptionalInt.empty();
        return OptionalInt.of(number.value().intValueExact());
    }
    private static Optional<Obj> object(Value value) { return value instanceof Obj object ? Optional.of(object) : Optional.empty(); }
    private static List<Obj> objects(Value value) {
        if (!(value instanceof Arr array)) return List.of();
        List<Obj> objects = new ArrayList<>(); for (Value item : array.items()) if (item instanceof Obj object) objects.add(object); return List.copyOf(objects);
    }
}
