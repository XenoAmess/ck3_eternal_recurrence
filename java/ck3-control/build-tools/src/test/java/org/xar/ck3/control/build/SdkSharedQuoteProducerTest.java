package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.Digest;
import org.xar.ck3.control.build.SdkSourceAssembly.SourceCost;
import org.xar.ck3.control.build.SdkSourceAssembly.SourceViewCosts;

final class SdkSharedQuoteProducerTest {
    private static final String GROUP = "D:/sdk-quote-contract-only/views";
    private static SourceCost cost(String path, long bytes, char sha) { return new SourceCost(path, new Digest(bytes, String.valueOf(sha).repeat(64))); }
    @Test void sameAssemblyAlgorithmCountsLogicalPathsButCopiesOnlyChangedLeavesAndChargesEveryLink() throws Exception {
        var base = new SourceViewCosts(List.of(cost("src/a.py", 1, 'a'), cost("src/b.py", 4097, 'b')), 3);
        var legacy = new SourceViewCosts(List.of(cost("src/a.py", 1, 'a'), cost("src/b.py", 4098, 'c')), 3);
        var consumer = new SourceViewCosts(List.of(cost("src/a.py", 1, 'a'), cost("src/b.py", 4097, 'b'), cost("test/c.py", 3, 'd')), 4);
        var quote = SdkSourceAssembly.sourceQuote("contract-machine", GROUP, base, legacy, consumer, 0, 0, 1L << 27);
        assertEquals(12298, quote.allViewLogicalBytes()); assertEquals(4101, quote.privateChangedLogicalBytes());
        assertEquals(4098, quote.baselineCopyLogicalBytes()); assertEquals(7, quote.sourcePathCount());
        assertEquals(11, quote.directories()); assertEquals(15728640, quote.metadataHardBytes());
        long actualNoReuseUpper = SdkSourceAssembly.sourceAllocationUpper(quote, base, legacy, consumer, Set.of(), 4096, 4096, 0);
        assertEquals(15843328, actualNoReuseUpper);
        assertEquals(actualNoReuseUpper + 8192, SdkSourceAssembly.sourceAllocationUpper(quote, base, legacy, consumer, Set.of(), 4096, 4096, 2));
        var mapper = ControlBuild.strictMapper();
        assertEquals(quote, mapper.readValue(mapper.writeValueAsBytes(quote), SdkSourceAssembly.SharedQuote.class));
        assertThrows(IllegalArgumentException.class, () -> SdkSourceAssembly.sourceAllocationUpper(quote, base, legacy, consumer, Set.of("src/a.py"), 4096, 4096, 0));
        var crossed = SdkSourceAssembly.sourceQuote("contract-machine", GROUP, base, legacy, consumer, 0, 0, 1L << 28);
        assertNotEquals(quote, crossed);
        assertThrows(IllegalArgumentException.class, () -> new SourceViewCosts(List.of(cost("src/a.py", 1, 'a'), cost("SRC/A.py", 2, 'b')), 3));
    }
    @Test void zeroByteReuseStillRequiresAReservedLinkAndCannotCreateCopyCredit() {
        var base = new SourceViewCosts(List.of(cost("empty.py", 0, 'a')), 2);
        var quote = SdkSourceAssembly.sourceQuote("contract-machine", GROUP, base, base, base, 0, 0, 1L << 27);
        long ordinary = SdkSourceAssembly.sourceAllocationUpper(quote, base, base, base, Set.of(), 4096, 4096, 0);
        assertEquals(ordinary + 4096, SdkSourceAssembly.sourceAllocationUpper(quote, base, base, base, Set.of(), 4096, 4096, 1));
        var reused = SdkSourceAssembly.sourceQuote("contract-machine", GROUP, base, base, base, 1, 0, 1L << 27);
        assertEquals(ordinary + 4096, SdkSourceAssembly.sourceAllocationUpper(reused, base, base, base, Set.of("empty.py"), 4096, 4096, 0));
        assertThrows(IllegalArgumentException.class, () -> SdkSourceAssembly.sourceAllocationUpper(reused, base, base, base, Set.of(), 4096, 4096, 0));
    }
    @Test void finiteForecastRequestRoundtripRejectsWrongPrimitiveTypesAndDoesNotClaimLiveDeployment() throws Exception {
        var ref = new FileRef("D:/pinned-contract-metadata.json", 1, "a".repeat(64));
        var request = new SdkSharedQuoteProducer.Request(SdkSharedQuoteProducer.REQUEST_SCHEMA, "contract-machine", "2030-01-01T00:00:00Z",
                ref, ref, ref, GROUP, 4096, 4096, 1L << 27,
                new SdkSharedQuoteProducer.ServiceBound(512L << 20, 640L << 20, 10000),
                SdkSharedQuoteProducer.ReusePolicy.EXISTING_ORIGINALS_READ_ONLY);
        var mapper = ControlBuild.strictMapper(); byte[] bytes = mapper.writeValueAsBytes(request);
        assertEquals(request, mapper.readValue(bytes, SdkSharedQuoteProducer.Request.class));
        var root = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(bytes);
        for (String field : List.of("allocation_unit_bytes", "shared_view_physical_hard_bytes")) {
            var wrong = root.deepCopy(); wrong.put(field, true);
            assertThrows(java.io.IOException.class, () -> mapper.treeToValue(wrong, SdkSharedQuoteProducer.Request.class));
            wrong.put(field, 4096.0);
            assertThrows(java.io.IOException.class, () -> mapper.treeToValue(wrong, SdkSharedQuoteProducer.Request.class));
        }
        assertThrows(IllegalArgumentException.class, () -> new SdkSharedQuoteProducer.ServiceBound(513L << 20, 640L << 20, 10000));
        var missing = root.deepCopy(); missing.remove("future_service_bound");
        assertThrows(java.io.IOException.class, () -> mapper.treeToValue(missing, SdkSharedQuoteProducer.Request.class));
    }
}

