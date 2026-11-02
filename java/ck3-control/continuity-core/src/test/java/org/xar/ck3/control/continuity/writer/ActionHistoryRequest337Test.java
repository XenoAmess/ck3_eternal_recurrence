package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

final class ActionHistoryRequest337Test {
    private static final String ACTION = WriterContracts.DRIVER_ACTION_HISTORY_KIND;
    // A public metadata value, never opened or treated as a physical original.
    private static final ExactRef REF = new ExactRef("D:/pure-data337/reference", 1, "a".repeat(64));

    @Test
    void canonicalValuesAndDefensiveOwnershipMatchOriginalConstructor() {
        for (String source : List.of("true", "\" \"", "{\"x\":null}", "[null]", "1", "-1", "2.0", "2e0", "5e-324")) {
            byte[] raw = bytes(" {\"v\":[2.0,2e0,-0.0,1.2300,1e6,1e-400],\"source\":"
                    + source + ",\"evidence_id\":\"e\"} ");
            assertAccepted(ACTION, raw, List.of(REF), true);
            assertAccepted("another_metadata_kind", raw, List.of(REF), true);
        }
        byte[] unicode = bytes("{\"\\ud800\\udc00\":1,\"source\":{\"\\ue000\":2},\"evidence_id\":\"e\"}");
        assertAccepted(ACTION, unicode, List.of(), true);

        var evidence = new ArrayList<>(List.of(REF));
        byte[] input = bytes("{\"source\":true,\"evidence_id\":\"original\",\"v\":-0.0}");
        Original expected = original(ACTION, input, evidence);
        var actual = new WriterContracts.Request(ACTION, input, evidence);
        Arrays.fill(input, (byte) ' ');
        evidence.clear();
        byte[] exported = actual.details();
        exported[0] = '?';
        actual.detailsObject().put("evidence_id", "mutated export");
        assertArrayEquals(expected.details(), actual.details());
        assertEquals(List.of(REF), actual.evidence());
        assertThrows(UnsupportedOperationException.class, () -> actual.evidence().clear());
        assertEquals(identity(expected), actual.identity());
        assertEquals(sourceKey(expected), actual.sourceKey());
        assertEquals(0x8000000000000000L,
                Double.doubleToRawLongBits(actual.detailsObject().get("v").doubleValue()));

        String prefix = "{\"evidence_id\":\"e\",\"pad\":\"";
        String suffix = "\",\"source\":true}";
        byte[] inclusive = bytes(prefix + "a".repeat(65_536 - bytes(prefix + suffix).length) + suffix);
        assertEquals(65_536, inclusive.length);
        assertAccepted(ACTION, inclusive, List.of(), false);
        Original largeOld = original(ACTION, inclusive, List.of());
        var largeNew = new WriterContracts.Request(ACTION, inclusive, List.of());
        RuntimeException firstIdentity = assertThrows(RuntimeException.class, () -> identity(largeOld));
        RuntimeException newIdentity = assertThrows(RuntimeException.class, largeNew::identity);
        assertFailure(firstIdentity, newIdentity);
        assertEquals(sourceKey(largeOld), largeNew.sourceKey());
    }

    @Test
    void rejectionOrderAndOtherKindsKeepOriginalFailures() {
        assertRejected(null, new byte[] {(byte) 0xff}, null);
        assertRejected("", null, null);
        assertRejected(ACTION, null, null);
        assertRejected(ACTION, bytes("{}"), null);
        assertRejected(ACTION, new byte[] {(byte) 0xc3, 0x28}, null);
        assertRejected(ACTION, bytes("{\"evidence_id\":\"e\",\"source\":true,\"v\":1e400}"), null);
        assertRejected(ACTION, bytes("{\"evidence_id\":false,\"source\":false}"), List.of());
        assertRejected(ACTION, bytes("{\"source\":false}"), List.of());
        for (String source : List.of("null", "false", "0", "-0.0", "1e-400", "\"\"", "{}", "[]")) {
            byte[] raw = bytes("{\"evidence_id\":\"e\",\"source\":" + source + "}");
            assertRejected(ACTION, raw, List.of());
            assertRejected("another_metadata_kind", raw, List.of());
        }
        for (String raw : List.of(
                "{\"evidence_id\":\"e\"}", "[]", "null", "{} {}",
                "{\"evidence_id\":\"e\",\"source\":true,\"source\":true}",
                "{\"evidence_id\":\"e\",\"source\":true,\"v\":9007199254740992}",
                "{\"evidence_id\":\"e\",\"source\":true,\"v\":1e-2147483648}",
                "{\"evidence_id\":\"e\",\"source\":true,\"v\":\"\\ud800\"}",
                "{\"evidence_id\":\"e\",\"source\":true,\"\\udc00\":0}")) {
            assertRejected(ACTION, bytes(raw), List.of());
        }
        var nullElement = new ArrayList<ExactRef>();
        nullElement.add(null);
        assertRejected(ACTION, bytes("{\"evidence_id\":false,\"source\":false}"), nullElement);
        byte[] expanded = bytes("{\"evidence_id\":false,\"source\":false,\"v\":["
                + "1e6,".repeat(7_000) + "1e6]}");
        assertTrue(expanded.length < 65_536);
        assertRejected(ACTION, expanded, null);
        assertRejected("another_metadata_kind", expanded, null);
        byte[] oversized = bytes("{\"evidence_id\":\"e\",\"source\":true,\"pad\":\""
                + "a".repeat(65_536) + "\"}");
        assertRejected(ACTION, oversized, null);
    }

    private record Original(String kind, byte[] details, List<ExactRef> evidence) { }

    // Original compact-constructor pipeline, using unchanged public helpers.
    // This is DATA comparison; it creates no writer, session or private issuer.
    private static Original original(String kind, byte[] details, List<ExactRef> evidence) {
        StrictJson.text(kind);
        details = WriterContracts.canonical(details);
        evidence = List.copyOf(evidence);
        ObjectNode row = WriterContracts.object(details);
        StrictJson.text(row.get("evidence_id"));
        var source = row.get("source");
        StrictJson.require(source != null && !source.isNull() && !source.isMissingNode()
                && (!source.isContainerNode() || !source.isEmpty())
                && (!source.isTextual() || !source.textValue().isEmpty())
                && (!source.isBoolean() || source.booleanValue())
                && (!source.isNumber() || source.doubleValue() != 0), "exact event source");
        return new Original(kind, details, evidence);
    }

    private static void assertAccepted(String kind, byte[] raw, List<ExactRef> evidence, boolean checkIdentity) {
        Original expected = original(kind, raw, evidence);
        var actual = new WriterContracts.Request(kind, raw, evidence);
        assertEquals(expected.kind(), actual.kind());
        assertArrayEquals(expected.details(), actual.details());
        assertEquals(expected.evidence(), actual.evidence());
        assertEquals(WriterContracts.object(expected.details()), actual.detailsObject());
        if (checkIdentity) { assertEquals(identity(expected), actual.identity()); }
        assertEquals(sourceKey(expected), actual.sourceKey());
    }

    private static String identity(Original value) {
        ObjectNode row = StrictJson.object();
        row.put("kind", value.kind());
        row.set("details", WriterContracts.object(value.details()));
        return ContinuityJson.digest(row);
    }

    private static String sourceKey(Original value) {
        ObjectNode row = StrictJson.object();
        row.put("kind", value.kind());
        row.set("evidence_id", WriterContracts.object(value.details()).get("evidence_id"));
        return ContinuityJson.digest(row);
    }

    private static void assertRejected(String kind, byte[] raw, List<ExactRef> evidence) {
        RuntimeException expected = assertThrows(RuntimeException.class, () -> original(kind, raw, evidence));
        RuntimeException actual = assertThrows(RuntimeException.class,
                () -> new WriterContracts.Request(kind, raw, evidence));
        assertFailure(expected, actual);
    }

    private static void assertFailure(Throwable expected, Throwable actual) {
        assertEquals(expected.getClass(), actual.getClass());
        assertEquals(expected.getMessage(), actual.getMessage());
        if (expected.getCause() == null) { assertNull(actual.getCause()); }
        else { assertNotNull(actual.getCause()); assertFailure(expected.getCause(), actual.getCause()); }
    }

    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
