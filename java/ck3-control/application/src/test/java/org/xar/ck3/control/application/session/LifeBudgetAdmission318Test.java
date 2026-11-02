package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import org.junit.jupiter.api.Test;

/** Scheduling arithmetic only; no Controller, canonical writer, Native or original action is issued. */
final class LifeBudgetAdmission318Test {
    private static final BatchLimits LIMITS = new BatchLimits("software-budget-0", 1,
            Duration.ofMinutes(20), Duration.ofMinutes(1), Duration.ofSeconds(1), 1);

    @Test void coldFloorAndObservedSavedTailRemainConservativeFiniteEstimates() {
        assertEquals(Duration.ofMinutes(10).toNanos(), SessionController.lifeBudgetReserveNanos(LIMITS, 0));
        assertEquals(Duration.ofMinutes(10).toNanos(), SessionController.lifeBudgetReserveNanos(LIMITS, Duration.ofMinutes(2).toNanos()));
        // An independently supplied 704-second complete envelope plus the configured 60 seconds.
        assertEquals(Duration.ofSeconds(764).toNanos(), SessionController.lifeBudgetReserveNanos(LIMITS, Duration.ofSeconds(704).toNanos()));
        assertEquals(Duration.ofMinutes(20), LIMITS.wallTime());
        assertEquals(Duration.ofMinutes(1), LIMITS.readinessTimeout());
    }

    @Test void aRequirementBeyondWholeBatchIsNotClampedOrOverflowedIntoAdmission() {
        assertEquals(Duration.ofSeconds(1260).toNanos(), SessionController.lifeBudgetReserveNanos(LIMITS, Duration.ofMinutes(20).toNanos()));
        assertEquals(Long.MAX_VALUE, SessionController.lifeBudgetReserveNanos(LIMITS, Long.MAX_VALUE - 1));
        var shortBatch = new BatchLimits("software-budget-short", 1, Duration.ofSeconds(30),
                Duration.ofMinutes(1), Duration.ofSeconds(1), 1);
        assertEquals(Duration.ofMinutes(1).toNanos(), SessionController.lifeBudgetReserveNanos(shortBatch, 0));
    }
}
