package org.xar.ck3.control.wave3.planning.participatingwar;

import org.junit.jupiter.api.Test;

final class ParticipatingWarThreatsTest {
    @Test void nativeProducerProjectionAndVersionedWireRetainUnknownsAndExactTokens() throws java.io.IOException {
        if (ParticipatingWarThreatsRegression.verify() < 80) throw new AssertionError("full default producer regressions required");
        ParticipatingWarThreatsRegression.verifyCommittedOriginalGolden();
    }
}
