package org.xar.ck3.control.application.session;

import java.time.Duration;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** One finite batch on the already owned, persistent ordinary session. */
public record BatchLimits(String batchId, int maximumTurns, Duration wallTime,
        Duration readinessTimeout, Duration pollInterval, int checkpointEveryEligibleAdvances) {
    public BatchLimits {
        StrictJson.require(batchId != null && batchId.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"), "bounded unique batch ID required");
        StrictJson.require(maximumTurns >= 1 && maximumTurns <= 100_000, "finite positive ordinary turn bound required");
        positiveMillis(wallTime, 86_400_000, "wall time");
        positiveMillis(readinessTimeout, 3_600_000, "readiness timeout");
        positiveMillis(pollInterval, 60_000, "poll interval");
        StrictJson.require(pollInterval.compareTo(readinessTimeout) <= 0, "poll interval exceeds readiness timeout");
        StrictJson.require(checkpointEveryEligibleAdvances >= 1 && checkpointEveryEligibleAdvances <= 100_000,
                "finite positive checkpoint cadence required");
    }
    private static void positiveMillis(Duration value, long maximum, String label) {
        Objects.requireNonNull(value, label);
        StrictJson.require(!value.isNegative() && !value.isZero() && value.getNano() % 1_000_000 == 0
                && value.compareTo(Duration.ofMillis(maximum)) <= 0, "bounded whole-millisecond " + label + " required");
    }
}
