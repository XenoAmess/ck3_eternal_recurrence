package org.xar.ck3.control.wave2.military.stocksupply;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyModel;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyProjection;
import org.xar.ck3.control.wave2.military.landstock.LandStockModel;
import org.xar.ck3.control.wave2.military.landstock.LandStockPolicy;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterInput;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterProjection;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteProjection;

/** Source-ordered updater writes, Fleet rate, stock clamp, and explicit-stock getter. */
public final class StockSupplyProjection {
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum RateBasis {
        NOT_CALLED_REJECTED_UPDATER, LAND_RATE_SOURCE_ROLE_NOT_CLOSED,
        EXISTING_SAME_QUERY_FLEET_RATE_RECOMPUTED_AT_SOURCE_NEXT_GLOBAL_DATE
    }
    public enum StockBranch {
        CAPTURED_STOCK_RETAINED_REJECTED_UPDATER, NEGATIVE_WRAPPED_ADD_TO_ZERO,
        MIN_CHANGED_CAPTURED_CAPACITY
    }
    public record Input(FleetSupplyModel.ArmyRow row, UpdaterInput updater,
                        Long observedRate, Long capturedCapacity) {
        public Input { Objects.requireNonNull(row); Objects.requireNonNull(updater); }
    }
    public record RateStage(Boolean wouldEvaluate, boolean ready, BigInteger raw, RateBasis basis,
                            Boolean sourcePairMatches, NextFleetRate.Result existingRate,
                            List<String> missingInputs) {
        public RateStage { missingInputs = List.copyOf(missingInputs); }
    }
    public record StockStage(boolean ready, Long raw, Long signed64Add, StockBranch clampBranch,
                             List<String> missingInputs) {
        public StockStage { missingInputs = List.copyOf(missingInputs); }
    }
    public record BudgetStage(Boolean wouldCall, boolean callPredicateReady, Integer globalDate,
                              boolean fleetDatePredicateReady, Boolean suppression,
                              boolean getterRejected, Long stockRaw, Integer stateIndex,
                              Long baseFraction, Long effectiveFraction, boolean ready,
                              Integer soldiers, List<String> missingInputs) {
        public BudgetStage { missingInputs = List.copyOf(missingInputs); }
    }
    public record Result(Input input, UpdaterProjection updater, Status status, boolean ready,
                         RateStage rate, StockStage stock, BudgetStage budget,
                         List<String> missingInputs) {
        public Result {
            Objects.requireNonNull(input); Objects.requireNonNull(updater); Objects.requireNonNull(status);
            Objects.requireNonNull(rate); Objects.requireNonNull(stock); Objects.requireNonNull(budget);
            missingInputs = List.copyOf(missingInputs);
        }
    }
    private StockSupplyProjection() {}

    public static Result project(Input input) {
        Objects.requireNonNull(input);
        var row = input.row();
        UpdaterProjection writes = UpdaterWriteProjection.project(input.updater());
        var future = writes.sourceNextDate();
        Integer next = future == null ? null : future.nextDateRawI32();
        var admission = writes.nextAdmission();
        Boolean admitted = admission.admitted();
        RateStage rate = new RateStage(admitted, false, null, null, null, null, List.of());
        StockStage stock = new StockStage(false, null, null, null, List.of());
        BudgetStage budget = new BudgetStage(admitted, admission.ready(), next, false, null,
                false, null, null, null, null, false, null, List.of());
        if (Boolean.FALSE.equals(admitted)) {
            rate = new RateStage(false, false, null, RateBasis.NOT_CALLED_REJECTED_UPDATER,
                    null, null, List.of());
            stock = row.currentSupplyRaw() == null
                    ? new StockStage(false, null, null, null, List.of("current_supply_raw"))
                    : new StockStage(true, row.currentSupplyRaw(), null,
                            StockBranch.CAPTURED_STOCK_RETAINED_REJECTED_UPDATER, List.of());
            budget = new BudgetStage(false, admission.ready(), next, false, null,
                    true, null, null, null, null, true, 0, List.of());
        } else if (Boolean.TRUE.equals(admitted)) {
            var tick = row.fleetTick();
            if (tick == null) {
                rate = absentRate(List.of("current_fleet_supply_tick_inputs_v1"), null);
            } else if (Boolean.FALSE.equals(tick.nativeFleetBranchApplicable())) {
                rate = absentRate(List.of("source_reached_land_rate_24E5FE0_24E6450_after_updater_writes"),
                        RateBasis.LAND_RATE_SOURCE_ROLE_NOT_CLOSED);
            } else if (tick.nativeFleetBranchApplicable() == null) {
                rate = absentRate(List.of("current_fleet_supply_tick_inputs_v1.native_fleet_branch_applicable"), null);
            } else {
                if (future != null && future.currentDateRawI32() != null && tick.currentNativeDateLow32() != null
                        && !future.currentDateRawI32().equals(tick.currentNativeDateLow32())) {
                    throw new ProjectionDomainRejection("source-next stock program current Fleet clock differs from native source seed");
                }
                NextFleetRate.Result scalar = NextFleetRate.project(rateInput(input));
                boolean matches = next != null && scalar.nextDateLow32() != null && next.equals(scalar.nextDateLow32());
                if (next != null && scalar.nextDateLow32() != null && !matches) {
                    throw new ProjectionDomainRejection("source-next stock program native next date differs from Fleet helper date");
                }
                List<String> missing = new ArrayList<>();
                if (!matches) missing.add("source_next_date_pair_matches_existing_fleet_rate_helper");
                missing.addAll(scalar.missingInputs());
                boolean ready = scalar.ready() && matches;
                rate = new RateStage(true, ready, ready ? scalar.raw() : null,
                        ready ? RateBasis.EXISTING_SAME_QUERY_FLEET_RATE_RECOMPUTED_AT_SOURCE_NEXT_GLOBAL_DATE : null,
                        matches, scalar, missing);
            }
            if (rate.ready()) stock = stockStage(LandStockPolicy.projectStockAfterRate(
                    rate.raw(), row.currentSupplyRaw(), input.capturedCapacity()));
            var getter = FleetSupplyProjection.projectAtStock(row, stock.raw(),
                    FleetSupplyModel.StockBasis.CONDITIONAL_POST_UPDATER_STOCK);
            budget = new BudgetStage(true, admission.ready(), next, getter.fleetDatePredicateReady(),
                    getter.conditionalNativeFleetSupplyLossSuppressed(), false, stock.raw(),
                    getter.heldStockStateIndex(), getter.supplyBaseFractionRaw(), getter.supplyEffectiveFractionRaw(),
                    getter.ready(), getter.conditionalSupplyBudgetSoldiers(), getter.missingInputs());
        }
        List<String> missing = new ArrayList<>(writes.missingInputs());
        missing.addAll(rate.missingInputs()); missing.addAll(stock.missingInputs()); missing.addAll(budget.missingInputs());
        boolean ready = writes.ready() && admission.ready() && stock.ready() && budget.ready()
                && (Boolean.FALSE.equals(admitted) || rate.ready());
        Status status = ready ? Status.AVAILABLE : "available".equals(row.status()) ? Status.PARTIAL : Status.UNAVAILABLE;
        return new Result(input, writes, status, ready, rate, stock, budget,
                List.copyOf(new LinkedHashSet<>(missing)));
    }

    public static NextFleetRate.Input rateInput(Input input) {
        var row = input.row();
        return new NextFleetRate.Input("available".equals(row.status()), row.armyId(),
                row.nativeCarmyId(), input.observedRate(), row.fleetTick());
    }
    private static RateStage absentRate(List<String> missing, RateBasis basis) {
        return new RateStage(true, false, null, basis, null, null, missing);
    }
    private static StockStage stockStage(LandStockModel.StockResult result) {
        return switch (result) {
            case LandStockModel.StockNotReached ignored -> new StockStage(false, null, null, null, List.of());
            case LandStockModel.MissingStock absent -> new StockStage(false, null, absent.signed64Add(), null, absent.missingInputs());
            case LandStockModel.AvailableStock available -> new StockStage(true, available.raw(), available.signed64Add(),
                    StockBranch.valueOf(available.clampBranch().name()), List.of());
        };
    }
}
