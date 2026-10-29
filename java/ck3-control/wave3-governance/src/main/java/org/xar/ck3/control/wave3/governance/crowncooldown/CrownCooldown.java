package org.xar.ck3.control.wave3.governance.crowncooldown;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Exact actual4 scalar-clock meaning; not a script-keyword or game-time estimator. */
public final class CrownCooldown {
    public static final String EXPIRY_TYPE = "signed32_scalar_clock_counter";
    public static final String RAW_UNIT = "scalar_clock_step_calendar_unqualified";
    public static final String PROJECTED_UNIT = "scalar_clock_step_calendar_projected";
    public static final String TICK_SOURCE = "native_variable_manager_turn_tick_context";
    private static final BigInteger UINT32_MASK = new BigInteger("ffffffff", 16);
    private static final BigInteger UINT64_BOUND = BigInteger.ONE.shiftLeft(64);
    public static final List<DurationFactor> FACTORS = List.of(new DurationFactor(1300, 1),
            new DurationFactor(1301, 30), new DurationFactor(1302, 365), new DurationFactor(1327, 7));
    private CrownCooldown() { }

    public enum State {
        UNAVAILABLE("unavailable"), ABSENT("absent"), UNTIMED("untimed"), TIMED("timed");
        private final String wire;
        State(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public record DurationFactor(int tokenId, int multiplierI32) { }
    public record DurationLiteral(BigInteger tokenId, int literalI32, boolean accepted,
            int multiplierI32, Integer clockStepsI32) { }
    public record RawObservation(boolean readAvailable, Boolean present, Boolean timed,
            Integer expiryRaw, Integer currentClockRaw, Integer remainingRaw,
            BigInteger retryDateRaw, String expiryType, String remainingUnit) { }
    public record TurnTick(boolean readAvailable, BigInteger managerMatchCount,
            Boolean managerContainsContext, Boolean scalarTailAllowsTick,
            Boolean contextTickEligible, String unavailableReason, String source) { }
    public record Clock(State state, Integer currentClockRaw, Integer nativeClockDeadlineRaw,
            Integer remainingNativeClockSteps, BigInteger queryRetryDateRaw,
            List<DurationFactor> durationTokenFactors, boolean keywordNamesQualified,
            boolean calendarDeadlineReady) {
        public Clock { Objects.requireNonNull(state); durationTokenFactors = List.copyOf(durationTokenFactors); }
    }

    public static DurationLiteral scale(BigInteger tokenId, int literalI32) {
        Objects.requireNonNull(tokenId);
        for (DurationFactor factor : FACTORS) {
            if (tokenId.equals(BigInteger.valueOf(factor.tokenId()))) {
                // Java int multiplication deliberately retains IMUL's low32 bits
                // and signed32 interpretation. Widening/saturating would change it.
                int product = literalI32 * factor.multiplierI32();
                return new DurationLiteral(tokenId, literalI32, true, factor.multiplierI32(), product);
            }
        }
        return new DurationLiteral(tokenId, literalI32, false, 0, null);
    }

    public static Clock interpret(RawObservation value, BigInteger dateRaw, TurnTick turnTick) {
        validateRaw(value, dateRaw);
        if (turnTick != null) { validateTurnTick(turnTick); }
        if (PROJECTED_UNIT.equals(value.remainingUnit())) { validateProjection(value, dateRaw, turnTick); }
        return interpretNormalized(value, dateRaw);
    }

    /**
     * Interprets the already normalized raw value as the legacy pure helper does.
     * This supplies no native qualification; full-query callers must use interpret
     * with the actual same-query turn-tick proof.
     */
    public static Clock interpretNormalized(RawObservation value, BigInteger dateRaw) {
        validateRaw(value, dateRaw);
        if (!value.readAvailable()) { return clock(State.UNAVAILABLE, null, null, null, null, false); }
        if (Boolean.FALSE.equals(value.present())) {
            return clock(State.ABSENT, value.currentClockRaw(), null, value.remainingRaw(), value.retryDateRaw(), false);
        }
        if (Boolean.FALSE.equals(value.timed())) {
            return clock(State.UNTIMED, value.currentClockRaw(), null, value.remainingRaw(), null, false);
        }
        return clock(State.TIMED, value.currentClockRaw(), value.expiryRaw(), value.remainingRaw(),
                value.retryDateRaw(), PROJECTED_UNIT.equals(value.remainingUnit()));
    }

    public static void validateRaw(RawObservation value, BigInteger dateRaw) {
        Objects.requireNonNull(value); Objects.requireNonNull(dateRaw);
        require(EXPIRY_TYPE.equals(value.expiryType()) && (RAW_UNIT.equals(value.remainingUnit()) || PROJECTED_UNIT.equals(value.remainingUnit())),
                "crown cooldown raw type or unit differs");
        boolean projected = PROJECTED_UNIT.equals(value.remainingUnit());
        if (projected) {
            require(value.readAvailable() && Boolean.TRUE.equals(value.present()) && Boolean.TRUE.equals(value.timed())
                    && value.remainingRaw() != null && value.remainingRaw() > 0 && signed(value.retryDateRaw(), 32),
                    "projected crown cooldown requires a positive timed native result");
        }
        if (!value.readAvailable()) {
            require(value.present() == null && value.timed() == null && value.expiryRaw() == null && value.currentClockRaw() == null
                    && value.remainingRaw() == null && value.retryDateRaw() == null, "unavailable crown cooldown must retain null inputs");
            return;
        }
        require(value.present() != null && value.timed() != null && value.currentClockRaw() != null && value.remainingRaw() != null,
                "available crown cooldown requires native bool/int32 inputs");
        if (!value.present()) {
            require(!value.timed() && value.expiryRaw() == null && value.remainingRaw() == -1
                    && signed(value.retryDateRaw(), 64) && value.retryDateRaw().equals(dateRaw),
                    "absent crown cooldown native result differs");
            return;
        }
        require(value.expiryRaw() != null && value.timed() == (value.expiryRaw() >= 0),
                "present crown cooldown native expiry classification differs");
        require(projected || value.retryDateRaw() == null, "present raw cooldown has no qualified calendar retry date");
        if (!value.timed()) { require(value.remainingRaw() == -1, "untimed crown cooldown native sentinel differs"); }
        else {
            // Signed int subtraction intentionally has the native low32 wrap.
            int remaining = value.expiryRaw() - value.currentClockRaw();
            require(value.remainingRaw() == remaining, "timed crown cooldown native signed32 remaining differs");
        }
    }

    public static void validateTurnTick(TurnTick tick) {
        Objects.requireNonNull(tick);
        require(TICK_SOURCE.equals(tick.source()), "crown cooldown turn-tick source or availability differs");
        if (!tick.readAvailable()) {
            require(tick.managerMatchCount() == null && tick.managerContainsContext() == null && tick.scalarTailAllowsTick() == null
                    && tick.contextTickEligible() == null && tick.unavailableReason() != null && !tick.unavailableReason().isEmpty(),
                    "unavailable crown turn-tick requires null inputs and a reason");
            return;
        }
        BigInteger count = tick.managerMatchCount();
        require(count != null && count.signum() >= 0 && count.compareTo(UINT64_BOUND) < 0
                && tick.managerContainsContext() != null && tick.scalarTailAllowsTick() != null && tick.contextTickEligible() != null
                && tick.unavailableReason() == null, "available crown turn-tick requires uint64 count and bool inputs");
        require(tick.managerContainsContext() == (count.signum() > 0)
                && tick.contextTickEligible() == (tick.managerContainsContext() && tick.scalarTailAllowsTick()),
                "crown turn-tick native input relationship differs");
    }

    private static void validateProjection(RawObservation raw, BigInteger dateRaw, TurnTick tick) {
        require(tick != null, "projected crown cooldown requires its same-query turn-tick observation");
        require(tick.readAvailable() && Boolean.TRUE.equals(tick.managerContainsContext()) && Boolean.TRUE.equals(tick.scalarTailAllowsTick())
                && Boolean.TRUE.equals(tick.contextTickEligible()), "projected crown cooldown requires its eligible same-query native context");
        BigInteger[] parts = BigInteger.valueOf(raw.remainingRaw()).divideAndRemainder(tick.managerMatchCount());
        BigInteger days = parts[0].add(parts[1].signum() == 0 ? BigInteger.ZERO : BigInteger.ONE);
        int retry = dateRaw.add(days.multiply(BigInteger.valueOf(24))).and(UINT32_MASK).intValue();
        require(raw.retryDateRaw().equals(BigInteger.valueOf(retry)), "projected crown cooldown same-query calendar retry differs");
    }

    private static Clock clock(State state, Integer current, Integer expiry, Integer remaining, BigInteger retry, boolean projected) {
        return new Clock(state, current, expiry, remaining, retry, FACTORS, false, projected);
    }
    private static boolean signed(BigInteger value, int bits) {
        return value != null && value.compareTo(BigInteger.ONE.shiftLeft(bits - 1).negate()) >= 0
                && value.compareTo(BigInteger.ONE.shiftLeft(bits - 1)) < 0;
    }
    static void require(boolean condition, String reason) { if (!condition) { throw new ProjectionDomainRejection(reason); } }
}
