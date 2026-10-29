package org.xar.ck3.control.g2.m4;

import java.net.URL;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

final class M4ResearchTest {
    @Test void realM4EntryRetainsOriginalWartimePolicyAndRejectsMalformedInputs() throws Exception {
        URL corpus = M4ResearchTest.class.getResource("/m4producer/wartime-original02.json.gz");
        assertNotNull(corpus, "complete actual original producer golden is mandatory");
        M4ResearchVerification.Result result = M4ResearchVerification.verify(Path.of(corpus.toURI()));
        assertEquals(31, result.originalProducerVectors());
        assertEquals(10, result.rejectedBoundaryInputs());
        assertEquals(3, result.freshConsumerReads());
    }
}
