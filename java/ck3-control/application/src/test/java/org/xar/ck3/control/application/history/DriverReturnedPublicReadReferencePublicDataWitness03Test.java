package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertIterableEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * NONBLIND public DATA witness: literal oracle was frozen after seeing the candidate,
 * before this test source was authored. No native/writer/source authority is issued.
 * The row142 replay gap is recorded separately; no fake issuer or mirrored callback flow is used.
 */
public final class DriverReturnedPublicReadReferencePublicDataWitness03Test {
    private static final String HASH = "0000000000000000000000000000000000000000000000000000000000000000";
    private static final ExactRef SMALL = new ExactRef("a", 1, HASH);

    @Test
    void publicInvocationKeepsLiteralReferenceOrderAndAsciiBytes() {
        OpportunityJson.Obj reference = metadataReference(new ExactRef("a", 1, HASH));
        assertIterableEquals(List.of("bytes", "path", "sha256"), reference.members().keySet());
        assertEquals(
                "{\"bytes\":1,\"path\":\"a\",\"sha256\":\"0000000000000000000000000000000000000000000000000000000000000000\"}",
                new String(DriverJson.encode(reference), StandardCharsets.UTF_8));
        assertEquals(BigInteger.ONE, OpportunityJson.integer(reference.get("bytes"), "bytes"));
    }

    @Test
    void publicInvocationRetainsUnicodeSupplementaryAndEscapedPathValues() {
        String path = "路/😀\"\\\t\n" + (char) 1;
        OpportunityJson.Obj reference = metadataReference(new ExactRef(path, 1, HASH));
        assertEquals("路/😀\"\\\t\n" + (char) 1, OpportunityJson.text(reference.get("path"), "path"));
        assertIterableEquals(List.of("bytes", "path", "sha256"), reference.members().keySet());
        assertEquals(HASH, OpportunityJson.text(reference.get("sha256"), "sha256"));
    }

    @Test
    void publicInvocationAcceptsExactly65536CanonicalReferenceBytes() {
        String path = String.valueOf((char) 1).repeat(10906) + "abc";
        OpportunityJson.Obj reference = metadataReference(new ExactRef(path, 1, HASH));
        assertEquals(65536, DriverJson.encode(reference).length);
        assertEquals(path, OpportunityJson.text(reference.get("path"), "path"));
        assertIterableEquals(List.of("bytes", "path", "sha256"), reference.members().keySet());
    }

    @Test
    void publicInvocationRejects65537CanonicalReferenceBytesAtRetainedGate() {
        String path = String.valueOf((char) 1).repeat(10906) + "abcd";
        ContractViolationException failure = assertThrows(ContractViolationException.class,
                () -> DriverReturnedPublicReadHistoryRowProducer.invocationJson(invocation(new ExactRef(path, 1, HASH))));
        assertEquals("canonical JSON exceeds shared receipt byte budget", failure.getMessage());
    }

    @Test
    void publicInvocationKeepsMaximumSafeLongAsAnIntegerToken() {
        OpportunityJson.Obj reference = metadataReference(new ExactRef("a", 9_007_199_254_740_991L, HASH));
        assertEquals(new BigInteger("9007199254740991"), OpportunityJson.integer(reference.get("bytes"), "bytes"));
        assertEquals(
                "{\"bytes\":9007199254740991,\"path\":\"a\",\"sha256\":\"0000000000000000000000000000000000000000000000000000000000000000\"}",
                new String(DriverJson.encode(reference), StandardCharsets.UTF_8));
    }

    @Test
    void zeroByteExactReferenceIsRejectedByActualMaterialConstructor() {
        ExactRef zero = new ExactRef("a", 0, HASH);
        assertEquals(0L, zero.bytes());
        ContractViolationException failure = assertThrows(ContractViolationException.class,
                () -> DriverReturnedPublicReadHistoryRowProducer.invocationJson(invocation(zero)));
        assertEquals("nonempty returned public-read original required", failure.getMessage());
    }

    @Test
    void exactReferenceConstructorRejectsNegativeAndUnsafeLongBoundaries() {
        ContractViolationException negative = assertThrows(ContractViolationException.class,
                () -> new ExactRef("a", -1, HASH));
        assertEquals("safe integer outside contract range", negative.getMessage());
        ContractViolationException unsafe = assertThrows(ContractViolationException.class,
                () -> new ExactRef("a", 9_007_199_254_740_992L, HASH));
        assertEquals("safe integer outside contract range", unsafe.getMessage());
        ContractViolationException longMaximum = assertThrows(ContractViolationException.class,
                () -> new ExactRef("a", Long.MAX_VALUE, HASH));
        assertEquals("safe integer outside contract range", longMaximum.getMessage());
    }

    @Test
    void existingPublicReferenceCodecRoundTripsUnicodeAndMaximumSafeLongData() {
        String path = "路/😀\"\\\t\n" + (char) 1;
        ExactRef original = new ExactRef(path, 9_007_199_254_740_991L, HASH);
        OpportunityJson.Obj encoded = DriverObservationEvidenceReader.reference(original);
        ExactRef replayed = DriverObservationEvidenceReader.reference(encoded);
        assertEquals(original, replayed);
        assertEquals("路/😀\"\\\t\n" + (char) 1, OpportunityJson.text(encoded.get("path"), "path"));
        assertEquals(new BigInteger("9007199254740991"), OpportunityJson.integer(encoded.get("bytes"), "bytes"));
    }

    private static OpportunityJson.Obj metadataReference(ExactRef metadata) {
        RawJson wire = DriverReturnedPublicReadHistoryRowProducer.invocationJson(invocation(metadata));
        OpportunityJson.Obj body = DriverJson.object(wire.bytes(), DriverJson.MAX_NATIVE_BYTES);
        return OpportunityJson.object(body.get("collection_metadata"), "collection_metadata");
    }

    private static DriverReturnedPublicReadHistoryMaterial.InvocationData invocation(ExactRef metadata) {
        return new DriverReturnedPublicReadHistoryMaterial.InvocationData(
                metadata,
                new OperationKey("query-army-strengths-v1"),
                new DriverReturnedPublicReadHistoryMaterial.FrameOriginals(SMALL, SMALL, SMALL, SMALL, SMALL, SMALL),
                SMALL,
                Optional.empty(),
                0,
                HASH,
                List.of(SMALL));
    }
}
