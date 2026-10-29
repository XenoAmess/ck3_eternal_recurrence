package org.xar.ck3.control.wave3.military.landcontext;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterProjection;

public record FullLandStockProjection(Status status, boolean ready, List<String> missingInputs,
                                       FullLandStockInput input, UpdaterProjection updater,
                                       RateStage rate, StockStage stock, BudgetStage budget) {
    public FullLandStockProjection {
        Objects.requireNonNull(status); Objects.requireNonNull(input); Objects.requireNonNull(updater);
        Objects.requireNonNull(rate); Objects.requireNonNull(stock); Objects.requireNonNull(budget);
        missingInputs = List.copyOf(missingInputs);
        if (ready != (status == Status.AVAILABLE)) throw new IllegalArgumentException("full LAND status differs from readiness");
    }
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum RateBasis { NOT_CALLED_REJECTED_UPDATER, SAME_QUERY_LAND_NUMERIC_KERNEL_AT_CAPTURED_NATIVE_USAGE }
    public enum ClampBranch { NEGATIVE_WRAPPED_ADD_TO_ZERO, MIN_CHANGED_CAPTURED_CAPACITY, CAPTURED_STOCK_RETAINED_REJECTED_UPDATER }
    public enum BudgetBasis { CONDITIONAL_POST_UPDATER_STOCK, GETTER_NOT_CALLED_REJECTED_UPDATER }
    public record RateStage(Boolean wouldEvaluate, boolean ready, Long raw, RateBasis basis,
                             Integer nativeUsageSoldiers, Integer nativeLimitSoldiers,
                             FullLandRateProjection fullLandRateProjection, List<String> missingInputs) {
        public RateStage { missingInputs = List.copyOf(missingInputs); }
    }
    public record StockStage(boolean ready, Long raw, Long signed64Add, ClampBranch clampBranch, List<String> missingInputs) {
        public StockStage { missingInputs = List.copyOf(missingInputs); }
    }
    public record BudgetStage(Boolean wouldCall, boolean callPredicateReady, Integer globalDateRawI32,
                               boolean fleetDatePredicateReady, Boolean suppression, BudgetBasis stockBasis,
                               Long stockRaw, Integer stateIndex, Long baseFractionRaw, Long effectiveFractionRaw,
                               boolean ready, Integer soldiers, List<String> missingInputs) {
        public BudgetStage { Objects.requireNonNull(stockBasis); missingInputs = List.copyOf(missingInputs); }
    }
}
