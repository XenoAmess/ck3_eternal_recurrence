package org.xar.ck3.control.governance.crownauthority;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Candidate;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Readback;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Status;

final class CrownAuthorityPolicyTest {
    @TestFactory
    Stream<DynamicTest> unchangedProducerAndSelectorGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals(20, golden.get("cases").size());
        assertEquals(1, golden.get("native_request_count").intValue());
        assertFalse(golden.get("native_game_action").booleanValue());
        return StreamSupport.stream(golden.get("cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () ->
                        assertEquals(row.get("expected"), StrictJson.parse(
                                CrownAuthorityCodec.choose(StrictJson.canonical(row.get("input")))))));
    }

    @Test
    void completeReadbackSerializationRoundTripsEveryProducerCase() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            JsonNode original = row.get("input").get("readback");
            Readback parsed = CrownAuthorityCodec.decodeReadback(StrictJson.canonical(original));
            byte[] encoded = CrownAuthorityCodec.encodeReadback(parsed);
            assertEquals(original, StrictJson.parse(encoded), row.get("name").textValue());
            assertEquals(parsed, CrownAuthorityCodec.decodeReadback(encoded));
        }
    }

    @Test
    void rejectsMissingUnknownNullAndWrongNestedTypes() throws IOException {
        for (String field : List.of("date_raw", "proof_epoch", "resources", "candidates", "title_successors", "schema")) {
            ObjectNode request = input();
            readback(request).remove(field);
            assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(request)), field);
        }
        ObjectNode unknown = input();
        readback(unknown).put("renamed_active_law", "crown_authority_0");
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(unknown)));
        for (String field : List.of("resources", "candidates", "title_successors", "active_law_key", "queried_revision")) {
            ObjectNode request = input(); readback(request).putNull(field);
            assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(request)), field);
        }
        ObjectNode wrongCost = input();
        candidate(wrongCost).putObject("costs");
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(wrongCost)));
    }

    @Test
    void everyIntegerEntryRejectsBooleanFloatAndStringTokens() throws IOException {
        for (String invalid : List.of("true", "40.0", "\"40\"")) {
            JsonNode value = StrictJson.parse(invalid.getBytes(StandardCharsets.UTF_8));
            for (String field : List.of("snapshot_revision", "native_snapshot_revision", "proof_epoch", "date_raw",
                    "player_character_id", "queried_revision", "queried_native_revision")) {
                ObjectNode request = input(); readback(request).set(field, value);
                assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(request)), field);
            }
            ObjectNode wrongCost = input();
            ((ObjectNode) candidate(wrongCost).get("costs").get(0)).set("cost_raw", value);
            assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(wrongCost)));
            ObjectNode wrongBalance = input();
            ((ObjectNode) readback(wrongBalance).get("resources").get(0)).set("amount_raw", value);
            assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(wrongBalance)));
            ObjectNode wrongReserve = input();
            ((ObjectNode) wrongReserve.get("reserves_raw")).set("prestige", value);
            assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(wrongReserve)));
        }
    }

    @Test
    void nativeQ64RangeAndReserveDomainAreCheckedBeforeDecision() throws IOException {
        for (BigInteger amount : List.of(BigInteger.valueOf(-1), BigInteger.ONE.shiftLeft(63))) {
            ObjectNode request = input();
            ((ObjectNode) candidate(request).get("costs").get(0)).put("cost_raw", amount);
            assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(request)));
        }
        ObjectNode balance = input();
        ((ObjectNode) readback(balance).get("resources").get(0)).put("amount_raw", BigInteger.ONE.shiftLeft(63));
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(balance)));
        ObjectNode reserve = input(); ((ObjectNode) reserve.get("reserves_raw")).put("prestige", -1);
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(reserve)));
        ObjectNode currency = input(); ((ObjectNode) currency.get("reserves_raw")).put("invented_currency", 0);
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(currency)));
    }

    @Test
    void noComponentVetoOverridesFinalNativeCanEnact() throws IOException {
        ObjectNode request = input(); candidate(request).put("engine_final_only", false);
        assertEquals("ready", StrictJson.parse(CrownAuthorityCodec.choose(bytes(request))).get("status").textValue());
        candidate(request).put("can_enact", false).put("blocked_reason", "合法性：原生拒绝 🏰");
        JsonNode blocked = StrictJson.parse(CrownAuthorityCodec.choose(bytes(request)));
        assertEquals("native_blocked", blocked.get("status").textValue());
        assertEquals("合法性：原生拒绝 🏰", blocked.get("reason").textValue());
        assertEquals(0, blocked.get("budgets_raw").size());
    }

    @Test
    void sourceFrameMismatchIsRejectedAndNullableSnapshotIdIsRetained() throws IOException {
        ObjectNode mismatch = input(); readback(mismatch).put("queried_native_revision", 41);
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(mismatch)));
        ObjectNode nullable = input(); readback(nullable).putNull("queried_snapshot_id");
        Readback parsed = CrownAuthorityCodec.decodeReadback(bytes(readback(nullable)));
        assertTrue(StrictJson.parse(CrownAuthorityCodec.encodeReadback(parsed)).get("queried_snapshot_id").isNull());
        ObjectNode missing = input(); readback(missing).remove("queried_snapshot_id");
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(bytes(missing)));
    }

    @Test
    void malformedUtf8DuplicateFieldsTrailingTokensAndSizeAreRejected() throws IOException {
        byte[] valid = bytes(input());
        String text = new String(valid, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(
                text.replace("\"reserves_raw\":{}", "\"reserves_raw\":{},\"reserves_raw\":{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose((text + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> CrownAuthorityCodec.choose(new byte[65537]));
    }

    @Test
    void modelDefensivelyCopiesListsAndReserves() throws IOException {
        CrownAuthorityCodec.Request request = CrownAuthorityCodec.decodeRequest(bytes(input()));
        Readback readback = request.readback();
        assertThrows(UnsupportedOperationException.class, () -> readback.candidates().clear());
        assertThrows(UnsupportedOperationException.class, () -> readback.resources().clear());
        assertThrows(UnsupportedOperationException.class, () -> readback.candidates().get(1).costs().clear());
        List<CrownAuthorityPolicy.Cost> costs = new ArrayList<>(readback.candidates().get(1).costs());
        Candidate detached = new Candidate("crown_authority_1", false, true, true, "", costs);
        costs.clear(); assertEquals(1, detached.costs().size());
        EnumMap<Currency, BigInteger> reserves = new EnumMap<>(Currency.class);
        reserves.put(Currency.PRESTIGE, BigInteger.ONE);
        CrownAuthorityCodec.Request detachedRequest = new CrownAuthorityCodec.Request(readback, reserves);
        reserves.clear(); assertEquals(1, detachedRequest.reservesRaw().size());
        assertEquals(Status.READY, CrownAuthorityPolicy.choose(detachedRequest.readback(), detachedRequest.reservesRaw()).status());
    }

    @Test
    void duplicateTargetRowsKeepOriginalFirstMatchSemantics() throws IOException {
        ObjectNode request = input();
        ObjectNode first = candidate(request); first.put("can_enact", false).put("blocked_reason", "first_target_blocked");
        ObjectNode second = first.deepCopy(); second.put("can_enact", true);
        ((ArrayNode) readback(request).get("candidates")).add(second);
        JsonNode decision = StrictJson.parse(CrownAuthorityCodec.choose(bytes(request)));
        assertEquals("native_blocked", decision.get("status").textValue());
        assertEquals("first_target_blocked", decision.get("reason").textValue());
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = CrownAuthorityPolicyTest.class.getResourceAsStream("/crownauthority/original-producer-golden.json")) {
            assertNotNull(stream, "checked-in golden is mandatory; no Python runtime fallback");
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode input() throws IOException { return (ObjectNode) golden().get("cases").get(0).get("input").deepCopy(); }
    private static ObjectNode readback(ObjectNode request) { return (ObjectNode) request.get("readback"); }
    private static ObjectNode candidate(ObjectNode request) { return (ObjectNode) readback(request).get("candidates").get(1); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value); }
}
