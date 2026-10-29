package org.xar.ck3.control.wave2.military.armyselector;

import static org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.*;

import java.util.Comparator;
import java.util.List;
import java.util.Objects;

/** Narrow migration of both actual strategy.py consumers: pursuit choice/war summaries and query gating. */
public final class QuietPursuitConsumer {
    public static final String QUERY_STEP = "query-army-strengths-v1";
    private QuietPursuitConsumer() {}
    public record WarReceipt(long warId, Selection receipt) {}
    public record Pursuit(Army selected, Selection replenishment, List<WarReceipt> warReceipts) {
        public Pursuit { warReceipts = List.copyOf(warReceipts); }
    }
    public record QueryContext(Long tacticalWarId, boolean routeThreatPresent, boolean strengthBalanceAbsent,
                               Slot<String> strengthQueryStatus, boolean paused, List<String> availableSteps,
                               List<String> controlledTacticalStates) {
        public QueryContext {
            Objects.requireNonNull(strengthQueryStatus); availableSteps = List.copyOf(availableSteps);
            controlledTacticalStates = List.copyOf(controlledTacticalStates);
        }
    }
    public record QueryScope(List<Integer> playerArmyIds, List<Integer> enemyArmyIds) {
        public QueryScope {
            playerArmyIds = List.copyOf(playerArmyIds); enemyArmyIds = List.copyOf(enemyArmyIds);
            if (playerArmyIds.stream().anyMatch(id -> id < 0) || enemyArmyIds.stream().anyMatch(id -> id < 0)) throw new IllegalArgumentException("query scope requires public CUnit IDs");
        }
    }
    public record QueryPlan(String selectedStep, long warId, QueryScope scope, List<WarReceipt> warReceipts) {
        public QueryPlan { Objects.requireNonNull(selectedStep); Objects.requireNonNull(scope); warReceipts = List.copyOf(warReceipts); }
    }
    public static Pursuit choose(Input input, List<Army> unsafeArmies, List<Army> threatenedStationaryArmies,
                                 List<Long> warSummaryIds) {
        if (!unsafeArmies.isEmpty()) return new Pursuit(strongest(unsafeArmies), null, List.of());
        if (!threatenedStationaryArmies.isEmpty()) return new Pursuit(strongest(threatenedStationaryArmies), null, List.of());
        Selection result = CurrentReplenishmentSelector.select(input);
        List<WarReceipt> receipts = result.status() == SelectionStatus.NOT_APPLICABLE ? List.of()
                : warSummaryIds.stream().filter(result.activeWarIds()::contains).map(id -> new WarReceipt(id, result)).toList();
        return new Pursuit(result.selected(), result, receipts);
    }
    public static boolean queryRequired(Pursuit pursuit, QueryContext context) {
        return context.tacticalWarId() != null
                && (context.routeThreatPresent() || pursuit.replenishment() != null && pursuit.replenishment().queryNeeded())
                && context.strengthBalanceAbsent() && context.strengthQueryStatus().presence() != Presence.VALUE
                && context.paused() && context.availableSteps().contains(QUERY_STEP)
                && context.controlledTacticalStates().stream().noneMatch(state -> List.of("combat", "retreating", "gathering").contains(state));
    }
    public static QueryPlan queryPlan(Pursuit pursuit, QueryContext context, List<Army> controlledArmies,
                                       List<Integer> routeThreatEnemyIds) {
        if (!queryRequired(pursuit, context)) return null;
        return new QueryPlan(QUERY_STEP, context.tacticalWarId(),
                new QueryScope(controlledArmies.stream().map(Army::armyId).sorted().toList(), routeThreatEnemyIds), pursuit.warReceipts());
    }
    private static Army strongest(List<Army> armies) {
        return armies.stream().min(Comparator.<Army>comparingInt(army -> army.soldiers() == null ? -1 : army.soldiers())
                .reversed().thenComparingInt(Army::armyId)).orElseThrow();
    }
}
