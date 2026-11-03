package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalOnly;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalReason;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Evidence;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.EvidenceKind;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Source;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * NONBLIND public DATA witness. No main method, reflection,
 * native/archive/writer access, fabricated ActionReceipt instance or qualified issuer.
 * Source/Evidence/ExactRef below are manual public DATA. Their enum labels do not
 * claim an actual action, canonical membership, source custody or effect permission.
 * Only public encode/decode and DATA constructors are exercised; expected JSON is
 * literal fixture material, not an implementation of the private reference helper.
 */
final class DriverActionHistoryCodecPublicRefWitnessTest {
    private static final String SHA = "0".repeat(64);

    @Test void publicEncodeKeepsThreeReferenceFieldsInOrderAndEscapesThePath() {
        String path = "D:\\quoted\"line\n\t\b\f\r" + (char) 0 + "/tail";
        Source source = softwareSource(new ExactRef(path, 7, SHA));
        RawJson encoded = DriverActionHistoryCodec.encode(source);
        var row = DriverJson.object(encoded.bytes(), DriverActionHistoryCodec.MAX_SOURCE_BYTES);
        var receipt = OpportunityJson.object(row.get("receipt"), "receipt");
        assertEquals(List.of("bytes", "path", "sha256"), new ArrayList<>(receipt.members().keySet()));
        assertEquals("{\"bytes\":7,\"path\":\"D:\\\\quoted\\\"line\\n\\t\\b\\f\\r\\u0000/tail\",\"sha256\":\""
                + SHA + "\"}", new String(DriverJson.encode(receipt), StandardCharsets.UTF_8));
        assertEquals(source, DriverActionHistoryCodec.decode(encoded));
    }

    @Test void publicEncodeAcceptsAnExactly65536ByteCanonicalReference() {
        // Literal fixture: 10906 NULs encode as 65436 ASCII bytes; "abc" adds 3.
        // The fixed bytes=1 / empty-path / 64-zero-SHA JSON frame contributes 97.
        String path = String.valueOf((char) 0).repeat(10906) + "abc";
        RawJson encoded = DriverActionHistoryCodec.encode(softwareSource(new ExactRef(path, 1, SHA)));
        var row = DriverJson.object(encoded.bytes(), DriverActionHistoryCodec.MAX_SOURCE_BYTES);
        byte[] receipt = DriverJson.encode(row.get("receipt"));
        assertEquals(65536, receipt.length);
        assertEquals("{\"bytes\":1,\"path\":\"" + "\\u0000".repeat(10906) + "abc\",\"sha256\":\"" + SHA + "\"}",
                new String(receipt, StandardCharsets.UTF_8));
    }

    @Test void publicEncodeRejectsOneByteOverTheCanonicalReferenceBudget() {
        String path = String.valueOf((char) 0).repeat(10906) + "abcd";
        Source source = softwareSource(new ExactRef(path, 1, SHA));
        var failure = assertThrows(ContractViolationException.class, () -> DriverActionHistoryCodec.encode(source));
        assertEquals("canonical JSON exceeds shared receipt byte budget", failure.getMessage());
    }

    @Test void exactReferenceConstructorGatesRunBeforePublicEncoding() {
        var empty = assertThrows(ContractViolationException.class, () -> new ExactRef("", 1, SHA));
        assertEquals("nonempty bounded text required", empty.getMessage());
        var negative = assertThrows(ContractViolationException.class, () -> new ExactRef("software", -1, SHA));
        assertEquals("safe integer outside contract range", negative.getMessage());
        var digest = assertThrows(ContractViolationException.class, () -> new ExactRef("software", 1, "F".repeat(64)));
        assertEquals("lowercase SHA-256 required", digest.getMessage());
        var unicode = assertThrows(ContractViolationException.class,
                () -> new ExactRef(String.valueOf((char) 0xd800), 1, SHA));
        assertEquals("unpaired Unicode surrogate", unicode.getMessage());
        var longText = assertThrows(ContractViolationException.class,
                () -> new ExactRef("x".repeat(32769), 1, SHA));
        assertEquals("nonempty bounded text required", longText.getMessage());
    }

    @Test void publicSourceAndMaterialConstructorsKeepTheirDataGates() {
        var zero = assertThrows(ContractViolationException.class,
                () -> softwareSource(new ExactRef("software-zero", 0, SHA)));
        assertEquals("nonempty original reference required", zero.getMessage());
        ExactRef support = new ExactRef("software-support", 1, SHA);
        var material = softwareMaterial(support);
        var unresolved = assertThrows(ContractViolationException.class,
                () -> new Source("software-data", SHA, 1, support, support, ActionReceipt.Outcome.UNRESOLVED, material));
        assertEquals("UNKNOWN or ACK has no completed history coverage", unresolved.getMessage());
        var noEvidence = assertThrows(ContractViolationException.class,
                () -> new CanonicalOnly(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER, List.of(), List.of(support)));
        assertEquals("independent original material is mandatory; a receipt/record alone is not Driver history material",
                noEvidence.getMessage());
    }

    private static Source softwareSource(ExactRef receipt) {
        ExactRef support = new ExactRef("software-support", 1, SHA);
        return new Source("software-data", SHA, 1, receipt, support, ActionReceipt.Outcome.APPLIED_CONFIRMED,
                softwareMaterial(support));
    }

    private static CanonicalOnly softwareMaterial(ExactRef support) {
        return new CanonicalOnly(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                List.of(new Evidence(EvidenceKind.MATERIAL, support)), List.of(support));
    }
}
