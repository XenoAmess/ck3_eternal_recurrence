package org.xar.ck3.control.warpolicy;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.observation.ObservationReuse;

/** Runs unchanged against the old real adapter to reproduce its malformed-miss lease leak. */
final class ScopedMalformedLeaseRegressionTest {
    @Test void malformedObservationRevokesTheIssuedLease() {
        var owner = new ObservationReuse<ObservationContext, WarObservationFrame, WarOutcomeStakesResult>("writer", 1);
        var token = owner.bindFresh(new ObservationReuse.Scope<>(
            new ObservationContext("machine", "2026-10-22T23:00:00Z", "captured-snapshot", "a".repeat(64)),
            new WarObservationFrame("native:7", BigInteger.valueOf(42), BigInteger.valueOf(7), 10660101,
                "episode", 29829, 123, BigInteger.ONE),
            new ObservationReuse.WriterVersion("writer", BigInteger.valueOf(240))));
        var consumer = new ScopedWarOutcomeStakesProjector(
            new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled()), owner);
        assertThrows(ContractViolationException.class, () -> consumer.project(token, new byte[] {'{'}));
        assertThrows(IllegalStateException.class, () -> owner.requireCurrent(token));
        assertEquals(ObservationReuse.Invalidation.INCOMPLETE_OBSERVATION, owner.lastInvalidation());
        assertEquals(0, owner.retainedEntryCount());
    }
}
