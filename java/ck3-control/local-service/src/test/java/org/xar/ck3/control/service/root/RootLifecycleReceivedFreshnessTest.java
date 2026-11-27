package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.time.Instant;
import org.junit.jupiter.api.Test;

class RootLifecycleReceivedFreshnessTest {
    private static final Duration FRESHNESS = Duration.ofMinutes(1);

    @Test void recoveredLifeCannotReuseTheEarlierOpeningFrameAfterThePublicationWork() {
        Instant afterOriginalTerminal = Instant.parse("2026-11-27T13:07:24.746997700Z");
        Instant earlierOpening = Instant.parse("2026-11-27T13:34:44.459095600Z");
        Instant closingCycle = Instant.parse("2026-11-27T13:38:58.410488Z");

        assertTrue(earlierOpening.isAfter(afterOriginalTerminal));
        assertFalse(RootLifecycleAuthority.freshAt(earlierOpening, closingCycle, FRESHNESS));
        assertTrue(RootLifecycleAuthority.freshAt(closingCycle.minusSeconds(1), closingCycle, FRESHNESS));
    }

    @Test void receivedTimestampRequiresAnActualUnexpiredObservation() {
        Instant now = Instant.parse("2026-11-27T13:38:58Z");

        assertTrue(RootLifecycleAuthority.freshAt(now, now, FRESHNESS));
        assertTrue(RootLifecycleAuthority.freshAt(now.minus(FRESHNESS).plusNanos(1), now, FRESHNESS));
        assertFalse(RootLifecycleAuthority.freshAt(now.minus(FRESHNESS), now, FRESHNESS));
        assertFalse(RootLifecycleAuthority.freshAt(now.plusNanos(1), now, FRESHNESS));
    }
}
