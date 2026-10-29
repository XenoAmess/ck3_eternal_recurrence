package org.xar.ck3.control.g2.m0;

import java.io.IOException;
import org.junit.jupiter.api.Test;

final class M0ProducerDifferentialTest {
    @Test void unchangedOriginalProducersMatchJavaAndRejectCrossBoundInputs() throws IOException {
        M0ProducerDifferential.verify(getClass().getResourceAsStream("/g2/m0/original-producer01.json.gz"));
    }
    @Test void sharedNativePacketExtractionPreservesAllOriginalCacheConsumers() throws IOException {
        NativeTerminationPacketVerification.verify(getClass().getResourceAsStream(
                "/org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl"));
    }
}
