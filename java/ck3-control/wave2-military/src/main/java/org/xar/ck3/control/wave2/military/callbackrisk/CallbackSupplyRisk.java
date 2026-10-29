package org.xar.ck3.control.wave2.military.callbackrisk;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossPolicy;

/** One captured-current callback entry; no earlier stage or callback occurrence is replayed. */
public final class CallbackSupplyRisk {
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public record Input(Integer armyId, Integer nativeCarmyId, MonthlyLossModel.Input supply,
                        Long observedAttritionFractionRaw, Long lastSupplyUpdateDateStorageRaw64,
                        CurrentSupplyDispatch dispatch) {
        public Input { Objects.requireNonNull(supply); }
    }
    public record Result(Input input, MonthlyLossModel.StockState currentStockState,
                         MonthlyLossModel.SupplyEntry supplyEntry, MonthlyLossModel.StockState postStockState,
                         Boolean positiveBudget, Boolean entersPositiveBaseState, Status status, boolean ready,
                         List<String> missingInputs) {
        public Result {
            Objects.requireNonNull(input); Objects.requireNonNull(currentStockState);
            Objects.requireNonNull(supplyEntry); Objects.requireNonNull(status);
            missingInputs = List.copyOf(missingInputs);
        }
    }
    public record ArmyRisk(Integer armyId, Result projection) {
        public ArmyRisk { Objects.requireNonNull(projection); }
    }
    private CallbackSupplyRisk() {}

    public static Result project(Input input) {
        Objects.requireNonNull(input);
        var values = input.supply();
        var current = MonthlyLossPolicy.projectStockState(values.currentSupplyRaw(), values.supply());
        var entry = MonthlyLossPolicy.projectSupplyEntry(values);
        if (!values.available()) return new Result(input, current, entry, null, null, null,
                Status.UNAVAILABLE, false, List.of("available_same_query_army_strength"));
        List<String> missing = new ArrayList<>(entry.missingInputs());
        if (Boolean.FALSE.equals(entry.admitted()) && values.currentSupplyRaw() == null) missing.add("current_supply_raw");
        MonthlyLossModel.StockState post = entry.postStockReady()
                ? MonthlyLossPolicy.projectStockState(entry.postStockRaw(), values.supply()) : null;
        Boolean enters = current.ready() && post != null && post.ready()
                ? current.baseFractionRaw() <= 0 && post.baseFractionRaw() > 0 : null;
        Boolean positive = entry.component().ready() ? entry.component().soldiers() > 0 : null;
        boolean ready = entry.ready();
        Status status = ready ? Status.AVAILABLE : entry.admitted() != null || current.ready()
                || values.currentSupplyRaw() != null ? Status.PARTIAL : Status.UNAVAILABLE;
        return new Result(input, current, entry, post, positive, enters, status, ready,
                List.copyOf(new LinkedHashSet<>(missing)));
    }
    public static List<ArmyRisk> projectServiceRows(List<Input> rows) {
        return rows.stream().map(row -> new ArmyRisk(row.armyId(), project(row))).toList();
    }
}
