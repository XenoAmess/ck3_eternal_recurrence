package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Synthetic contract vectors; they carry no live native qualification. */
final class ArmyOrdinaryActionArgumentsTest {
    private static final ExactRef REF = new ExactRef("D:/contract-vectors/army-before-read.json", 9, "a".repeat(64));
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    @Test void originalPreflightCustodyAndLargeDecimalPublicRevisionRoundTrip() {
        var args = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.MOVE_ARMY,
                raw("{\"army_id\":0,\"target_province_id\":123,\"expected_revision\":\"18446744073709551615\"}"), List.of(REF));
        var round = ArmyOrdinaryActionArguments.decode(args.raw());
        assertEquals(args, round); assertArrayEquals(args.raw().bytes(), round.raw().bytes());
        assertEquals("18446744073709551615", StrictJson.parse(round.publicArguments().bytes()).get("expected_revision").textValue());
        assertEquals(List.of(REF), round.preflightReads());
    }
    @Test void allOuterFieldsAreRequiredAndUnknownFieldsAreRejected() {
        var args = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.START_ASSAULT, raw("{\"siege_id\":7}"), List.of());
        var n = StrictJson.parse(args.raw().bytes());
        for (String key : List.of("schema", "kind", "public_arguments", "preflight_reads")) {
            var changed = n.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) changed).remove(key);
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(changed))), key);
        }
        var extra = (com.fasterxml.jackson.databind.node.ObjectNode) n.deepCopy(); extra.put("accepted", true);
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(extra))));
    }
    @Test void missingNullAndEmptyOriginalsAreDifferentDomains() {
        var args = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.DISBAND_ARMY, raw("{\"army_id\":0}"), List.of());
        var n = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(args.raw().bytes());
        n.putNull("preflight_reads"); assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(n))));
        n.putArray("preflight_reads"); assertTrue(ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(n))).preflightReads().isEmpty());
        n.putNull("public_arguments"); assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(n))));
        assertThrows(IllegalArgumentException.class, () -> new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.DISBAND_ARMY, raw("[]"), List.of()));
        assertThrows(IllegalArgumentException.class, () -> new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.DISBAND_ARMY, raw("{}"), List.of(REF, REF)));
    }
    @Test void schemaKindAndReceiptRuntimeTypesAreStrict() {
        var args = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.DECLARE_WAR, raw("{\"declaration_id\":\"8-9--1\"}"), List.of(REF));
        for (String key : List.of("schema", "kind")) {
            for (String invalid : List.of("null", "true", "7", "[]", "{}", "\"unknown\"")) {
                var n = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(args.raw().bytes()); n.set(key, StrictJson.parse(invalid.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(n))));
            }
        }
        var n = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(args.raw().bytes());
        ((com.fasterxml.jackson.databind.node.ObjectNode) n.get("preflight_reads").get(0)).put("bytes", true);
        assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(n))));
        n.put("kind", "DECLARE_WAR"); assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionArguments.decode(new RawJson(StrictJson.canonical(n))));
    }
    @Test void producerTimeoutKeepsItsNumericDecimalDomainAcrossDurableCustody() {
        var args = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1,
                raw("{\"type_index\":0,\"action_id\":\"original\",\"expected_revision\":\"10\",\"timeout_seconds\":0.125}"), List.of());
        var round = ArmyOrdinaryActionArguments.decode(args.raw()); assertEquals(args, round);
        var timeout = StrictJson.parse(round.publicArguments().bytes()).get("timeout_seconds");
        assertTrue(timeout.isNumber()); assertEquals(new java.math.BigDecimal("0.125"), timeout.decimalValue());
    }
}
