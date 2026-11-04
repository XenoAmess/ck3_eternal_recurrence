package org.xar.ck3.control.application.readiness;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.time.Instant;
import org.junit.jupiter.api.Test;

public final class NativeReadinessObservationTimingTest {

    @Test
    void checkedAfterIoDeadlineButBeforeScopeDeadlineAccepts() {
        Instant ioDeadline = Instant.ofEpochSecond(100);
        Instant scopeDeadline = Instant.ofEpochSecond(200);
        Instant observedAt = Instant.ofEpochSecond(50);
        Instant checkedAt = Instant.ofEpochSecond(150);
        assertDoesNotThrow(() -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAt, ioDeadline, scopeDeadline));
    }

    @Test
    void observedAtEqualIoDeadlineAccepts() {
        Instant ioDeadline = Instant.ofEpochSecond(100);
        Instant scopeDeadline = Instant.ofEpochSecond(200);
        Instant observedAt = ioDeadline;
        Instant checkedAtEqual = observedAt;
        assertDoesNotThrow(() -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAtEqual, ioDeadline, scopeDeadline));
        Instant checkedAtLater = Instant.ofEpochSecond(150);
        assertDoesNotThrow(() -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAtLater, ioDeadline, scopeDeadline));
    }

    @Test
    void lateOrFutureObservationRejects() {
        {
            Instant ioDeadline = Instant.ofEpochSecond(100);
            Instant scopeDeadline = Instant.ofEpochSecond(200);
            Instant observedAt = Instant.ofEpochSecond(101);
            Instant checkedAt = Instant.ofEpochSecond(150);
            assertThrows(IllegalArgumentException.class, () -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAt, ioDeadline, scopeDeadline));
        }
        {
            Instant ioDeadline = Instant.ofEpochSecond(200);
            Instant scopeDeadline = Instant.ofEpochSecond(300);
            Instant checkedAt = Instant.ofEpochSecond(100);
            Instant observedAt = Instant.ofEpochSecond(101);
            assertThrows(IllegalArgumentException.class, () -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAt, ioDeadline, scopeDeadline));
        }
    }

    @Test
    void checkedAtAtOrAfterScopeDeadlineRejects() {
        Instant ioDeadline = Instant.ofEpochSecond(100);
        Instant scopeDeadline = Instant.ofEpochSecond(200);
        Instant observedAt = Instant.ofEpochSecond(50);
        Instant checkedAtEqual = scopeDeadline;
        assertThrows(IllegalArgumentException.class, () -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAtEqual, ioDeadline, scopeDeadline));
        Instant checkedAtAfter = Instant.ofEpochSecond(201);
        assertThrows(IllegalArgumentException.class, () -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAtAfter, ioDeadline, scopeDeadline));
    }

    @Test
    void ioDeadlineEqualScopeDeadlinePreservesBudget() {
        Instant deadline = Instant.ofEpochSecond(100);
        Instant observedAt = Instant.ofEpochSecond(50);
        Instant checkedAtBefore = Instant.ofEpochSecond(99);
        assertDoesNotThrow(() -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAtBefore, deadline, deadline));
        Instant checkedAtEqual = deadline;
        assertThrows(IllegalArgumentException.class, () -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAtEqual, deadline, deadline));
        Instant checkedAtAfter = Instant.ofEpochSecond(101);
        assertThrows(IllegalArgumentException.class, () -> NativeReadinessCollector.requireObservationTiming(observedAt, checkedAtAfter, deadline, deadline));
    }
}