package org.xar.ck3.control.wave2.military.landstock;

import static org.xar.ck3.control.wave2.military.landstock.LandStockModel.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;

/** Complete 24E5BB4..5E4D numeric kernel and the source LAND stock-add/clamp branch. */
public final class LandStockPolicy {
    public static final long SCALE = 100_000;
    private static final long MULTIPLY_BOUND = 3_037_000_499L;
    private static final long DIVIDE_FAST_BOUND = 0x53E2D6238DA3L;
    private static final BigInteger Q = BigInteger.valueOf(SCALE);

    private LandStockPolicy() {}

    /** The supply helper decomposes the HIGH operand; the battle helper is a different ABI. */
    public static long nativeFixedMultiply(long base, long multiplier) {
        if (base >= -MULTIPLY_BOUND && base <= MULTIPLY_BOUND
                && multiplier >= -MULTIPLY_BOUND && multiplier <= MULTIPLY_BOUND) {
            return (base * multiplier) / SCALE;
        }
        long low = Math.min(base, multiplier);
        long high = Math.max(base, multiplier);
        long quotient = high / SCALE;
        long remainder = high - quotient * SCALE;
        return quotient * low + (remainder * low) / SCALE;
    }

    /** Keep division unwrapped until the exact source wrap points; Java MIN/-1 is not substituted. */
    public static DivisionResult nativeFixedDivide(long value, long divisor) {
        if (divisor == 0) return new DivisionResult(BigInteger.valueOf(4_294_967_295L),
                DivisionPath.ZERO_DIVISOR_POSITIVE_U32_MAX);
        BigInteger divisorValue = BigInteger.valueOf(divisor);
        if (value >= -DIVIDE_FAST_BOUND && value <= DIVIDE_FAST_BOUND) {
            return new DivisionResult(BigInteger.valueOf(value * SCALE).divide(divisorValue), DivisionPath.FAST);
        }
        // abs(Long.MIN_VALUE) wraps back to Long.MIN_VALUE in the source before this comparison.
        if (Math.abs(divisor) >= SCALE * SCALE) {
            return new DivisionResult(BigInteger.valueOf(value).divide(BigInteger.valueOf(divisor / SCALE)),
                    DivisionPath.WIDE_DIVISOR);
        }
        long quotient = value / SCALE;
        long remainder = value - quotient * SCALE;
        long whole = quotient * SCALE;
        BigInteger qa = BigInteger.valueOf(whole).divide(divisorValue);
        long ra = BigInteger.valueOf(whole).subtract(qa.multiply(divisorValue)).longValue();
        long sum = qa.multiply(Q).longValue()
                + BigInteger.valueOf(ra * SCALE).divide(divisorValue).longValue()
                + BigInteger.valueOf(remainder * SCALE).divide(divisorValue).longValue();
        return new DivisionResult(BigInteger.valueOf(sum), DivisionPath.DECOMPOSED);
    }

    public static RateResult projectRate(RateInput input) {
        List<String> missing = new ArrayList<>();
        if (input.usage() == null) missing.add("usage");
        if (input.limit() == null) missing.add("limit");
        if (input.provinceComponent() == null) missing.add("province_component_raw");
        if (missing.isEmpty() && input.usage() <= input.limit() && input.resupply() == null) {
            missing.add("native_resupply_eligible");
        }
        if (!missing.isEmpty()) return new UnavailableRate(input.limit(), missing);
        long usage = input.usage();
        long limit = input.limit();
        long province = input.provinceComponent();
        long loss = 0;
        long gain = 0;
        if (usage > limit) {
            require(input.loadedExcessSlope(), "loaded_excess_slope_raw", missing);
            require(input.loadedMinLoss(), "loaded_min_loss_raw", missing);
            require(input.loadedMaxLoss(), "loaded_max_loss_raw", missing);
            if (!missing.isEmpty()) return new UnavailableRate(limit, missing);
            long candidate = nativeFixedMultiply((usage - limit) * SCALE, input.loadedExcessSlope());
            loss = candidate < input.loadedMinLoss() ? input.loadedMinLoss() : Math.min(candidate, input.loadedMaxLoss());
        } else if (Boolean.TRUE.equals(input.resupply())) {
            if (input.loadedGain() == null) return new UnavailableRate(limit, List.of("loaded_gain_raw"));
            gain = input.loadedGain();
        }
        long local = province - loss;
        Components components = new Components(province, loss, gain, local);
        BigInteger adjusted = BigInteger.valueOf(local);
        Long divisor = null;
        DivisionPath path = DivisionPath.NOT_NEGATIVE;
        if (local < 0) {
            require(input.loadedDivisorFloor(), "loaded_divisor_floor_raw", missing);
            require(input.commanderModifier(), "commander_modifier_1a9_raw", missing);
            require(input.loadedMaxLoss(), "loaded_max_loss_raw", missing);
            if (!missing.isEmpty()) return new ComponentsUnavailableRate(limit, components, missing);
            divisor = Math.max(input.loadedDivisorFloor(), SCALE + input.commanderModifier());
            DivisionResult divided = nativeFixedDivide(local, divisor);
            adjusted = divided.value().max(BigInteger.valueOf(-input.loadedMaxLoss()));
            path = divided.path();
        }
        long finalRate = BigInteger.valueOf(gain).add(adjusted).longValue();
        return new AvailableRate(limit, components, finalRate, adjusted, divisor, path);
    }

    public static RateAndStock projectRateAndStock(RateInput input, Long capturedStock, Long capturedCapacity) {
        RateResult rate = projectRate(input);
        if (!(rate instanceof AvailableRate available)) return new RateAndStock(rate, new StockNotReached());
        return new RateAndStock(rate, projectStockAfterRate(available, capturedStock, capturedCapacity));
    }

    public static StockResult projectStockAfterRate(AvailableRate rate, Long capturedStock, Long capturedCapacity) {
        return projectStockAfterRate(BigInteger.valueOf(rate.conditionalRate()), capturedStock, capturedCapacity);
    }

    /** Shared updater branch; wrapping a source fixed-point rate occurs at the source stock ADD. */
    public static StockResult projectStockAfterRate(BigInteger rate, Long capturedStock, Long capturedCapacity) {
        if (rate == null) throw new IllegalArgumentException("explicit source-derived rate is required");
        if (capturedStock == null) return new MissingStock(null, List.of("current_supply_raw"));
        long changed = BigInteger.valueOf(capturedStock).add(rate).longValue();
        if (changed < 0) return new AvailableStock(0, changed, ClampBranch.NEGATIVE_WRAPPED_ADD_TO_ZERO);
        if (capturedCapacity == null) return new MissingStock(changed, List.of("current_supply_capacity_raw"));
        return new AvailableStock(Math.min(changed, capturedCapacity), changed, ClampBranch.MIN_CHANGED_CAPTURED_CAPACITY);
    }

    private static void require(Long value, String name, List<String> missing) {
        if (value == null) missing.add(name);
    }
}
