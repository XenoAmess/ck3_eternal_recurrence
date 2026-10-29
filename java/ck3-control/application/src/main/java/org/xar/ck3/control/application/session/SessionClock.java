package org.xar.ck3.control.application.session;

import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Monotonic bounds and complete wall time are independent of wall clock corrections. */
public interface SessionClock {
    record Tick(long elapsedNanos, Instant utc) {
        public Tick { StrictJson.require(elapsedNanos >= 0, "nonnegative monotonic elapsed time required"); Objects.requireNonNull(utc); }
    }
    Tick now();
    void waitFor(Duration duration) throws InterruptedException;
    final class SystemClock implements SessionClock {
        private final long origin = System.nanoTime();
        @Override public Tick now() { return new Tick(System.nanoTime() - origin, Instant.now()); }
        @Override public void waitFor(Duration duration) throws InterruptedException {
            StrictJson.require(!duration.isNegative() && duration.compareTo(Duration.ofMinutes(1)) <= 0, "finite bounded session wait required");
            java.util.concurrent.TimeUnit.NANOSECONDS.sleep(duration.toNanos());
        }
    }
}
