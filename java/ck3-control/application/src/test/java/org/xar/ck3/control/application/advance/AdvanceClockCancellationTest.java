package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Exercises the production cancel validator, including the no-tick modal boundary. */
final class AdvanceClockCancellationTest {
    private static final AdvancePlan PLAN = new AdvancePlan(BigInteger.valueOf(100), BigInteger.valueOf(124), 1, 1,
            "exact_one_day_unavoidable_contact", true, AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty());
    private static Status status(State state, String generation, long ticks, int date) {
        return new Status(state, new CrossJsDecimalUInt64(generation), 100, 124, date, 0, 1, Mode.TERMINAL_OR_SENTINEL,
                0, 0, ticks, 0, 0, List.of(), 0, -1, false, false, false, false);
    }
    @Test void zeroDayIdleOfOriginalGenerationIsAControlBoundaryWithoutDayCredit() {
        AdvanceClock.validateCancellation(status(State.ARMED, "37", 0, 100), status(State.IDLE, "37", 0, 100), PLAN, BigInteger.valueOf(100));
    }
    @Test void cancelAckCannotSubstituteForIdleOrAuthorizeAnotherGeneration() {
        Status arm = status(State.ARMED, "37", 0, 100);
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateCancellation(arm, arm, PLAN, BigInteger.valueOf(100)));
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateCancellation(arm, status(State.IDLE, "38", 0, 100), PLAN, BigInteger.valueOf(100)));
    }
    @Test void impossibleTicksChangedCallbackDateAndDeadlineCancellationAreRefused() {
        Status arm = status(State.ARMED, "37", 0, 100);
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateCancellation(arm, status(State.IDLE, "37", 1, 124), PLAN, BigInteger.valueOf(100)));
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateCancellation(arm, status(State.IDLE, "37", 0, 101), PLAN, BigInteger.valueOf(100)));
        assertThrows(IllegalArgumentException.class, () -> AdvanceClock.validateCancellation(arm, status(State.IDLE, "37", 1, 124), PLAN, BigInteger.valueOf(124)));
    }
}
