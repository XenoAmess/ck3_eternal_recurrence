package org.xar.ck3.control.wave2.military.landstock;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Pure numeric models; none of their states grant observation or callback qualification. */
public final class LandStockModel {
    private LandStockModel() {}

    public record RateInput(Long usage, Long limit, Long provinceComponent, Boolean resupply,
                            Long loadedGain, Long loadedExcessSlope, Long loadedMinLoss,
                            Long loadedMaxLoss, Long loadedDivisorFloor, Long commanderModifier) {}
    public enum DivisionPath { FAST, WIDE_DIVISOR, DECOMPOSED, ZERO_DIVISOR_POSITIVE_U32_MAX, NOT_NEGATIVE }
    public record DivisionResult(BigInteger value, DivisionPath path) {
        public DivisionResult { Objects.requireNonNull(value); Objects.requireNonNull(path); }
    }
    public record Components(long provinceComponent, long excessLoss, long gainComponent,
                             long localBeforeAdjustment) {}
    public sealed interface RateResult permits UnavailableRate, ComponentsUnavailableRate, AvailableRate {
        Long limit();
        List<String> missingInputs();
    }
    public record UnavailableRate(Long limit, List<String> missingInputs) implements RateResult {
        public UnavailableRate { missingInputs = List.copyOf(missingInputs); }
    }
    public record ComponentsUnavailableRate(Long limit, Components components,
                                            List<String> missingInputs) implements RateResult {
        public ComponentsUnavailableRate { Objects.requireNonNull(components); missingInputs = List.copyOf(missingInputs); }
    }
    public record AvailableRate(Long limit, Components components, long conditionalRate,
                                BigInteger localAfterAdjustment, Long commanderDivisor,
                                DivisionPath divisionPath) implements RateResult {
        public AvailableRate {
            Objects.requireNonNull(limit); Objects.requireNonNull(components);
            Objects.requireNonNull(localAfterAdjustment); Objects.requireNonNull(divisionPath);
        }
        @Override public List<String> missingInputs() { return List.of(); }
    }
    public enum ClampBranch { NEGATIVE_WRAPPED_ADD_TO_ZERO, MIN_CHANGED_CAPTURED_CAPACITY }
    public sealed interface StockResult permits StockNotReached, MissingStock, AvailableStock {}
    public record StockNotReached() implements StockResult {}
    public record MissingStock(Long signed64Add, List<String> missingInputs) implements StockResult {
        public MissingStock { missingInputs = List.copyOf(missingInputs); }
    }
    public record AvailableStock(long raw, long signed64Add, ClampBranch clampBranch) implements StockResult {
        public AvailableStock { Objects.requireNonNull(clampBranch); }
    }
    public record RateAndStock(RateResult rate, StockResult stock) {
        public RateAndStock { Objects.requireNonNull(rate); Objects.requireNonNull(stock); }
    }
}
