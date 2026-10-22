package org.xar.ck3.control.finance.factiongift;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class FactionGiftPolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @TestFactory
    List<DynamicTest> originalProducerGoldenAndPersistenceRoundTrip() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java.faction-gift-policy-golden/v1", golden.path("schema").textValue());
        assertEquals(5, golden.path("original_tests_executed").size());
        assertEquals(0, golden.path("capture").path("game_rpc_count").intValue());
        assertEquals(63, golden.path("cases").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.path("cases")) {
            String name = vector.path("name").textValue();
            tests.add(DynamicTest.dynamicTest(name, () -> {
                byte[] input = JSON.writeValueAsBytes(vector.path("input"));
                FactionGiftChoice actual = FactionGiftPolicy.choose(input);
                byte[] encoded = FactionGiftPolicy.encode(actual);
                assertEquals(vector.path("expected"), JSON.readTree(encoded), name);
                FactionGiftChoice restored = FactionGiftPolicy.decodeChoice(encoded);
                assertEquals(actual, restored, name + " persisted model");
                assertTrue(Arrays.equals(encoded, FactionGiftPolicy.encode(restored)), name + " stable encoding");
                byte[] reserializedInput = JSON.writeValueAsBytes(JSON.readTree(input));
                assertEquals(actual, FactionGiftPolicy.choose(reserializedInput), name + " input JSON-domain round trip");
            }));
        }
        return List.copyOf(tests);
    }

    @Test
    void rejectsUnknownDuplicateMissingAndTrailingEnvelopeFields() throws IOException {
        ObjectNode request = input();
        request.put("minimumGoldReserveRaw", 0);
        assertThrows(IllegalArgumentException.class, () -> choose(request));
        request.remove("minimumGoldReserveRaw");
        request.remove("minimum_gold_reserve_raw");
        assertThrows(IllegalArgumentException.class, () -> choose(request));
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(utf8(
                "{\"observations\":[],\"complete_native_enumeration\":true,"
                        + "\"minimum_gold_reserve_raw\":0,\"minimum_gold_reserve_raw\":1}")));
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(utf8("{} {}")));
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(utf8("[]")));
    }

    @Test
    void rejectsUnknownObservationAndPreviewFieldsWithoutAliases() throws IOException {
        ObjectNode request = input();
        ObjectNode observation = (ObjectNode) request.path("observations").get(0);
        observation.put("recipientCharacterId", 33011);
        assertThrows(IllegalArgumentException.class, () -> choose(request));
        observation.remove("recipientCharacterId");
        ObjectNode preview = (ObjectNode) observation.get("gift_preview");
        preview.put("gold_cost", 75);
        assertThrows(IllegalArgumentException.class, () -> choose(request));
    }

    @Test
    void metadataDateIsNotAliasForRequiredObservedDate() throws IOException {
        ObjectNode request = input();
        ObjectNode observation = (ObjectNode) request.path("observations").get(0);
        observation.set("date_raw", observation.remove("observed_date_raw"));
        FactionGiftChoice.Declined outcome = assertInstanceOf(FactionGiftChoice.Declined.class, choose(request));
        assertEquals(FactionGiftChoice.Reason.NATIVE_IDENTITY_OR_METRIC_UNAVAILABLE, outcome.reason());
    }

    @Test
    void metadataHasDeclaredTypesWithoutChangingDecisionInputs() throws IOException {
        ObjectNode request = input();
        ObjectNode observation = (ObjectNode) request.path("observations").get(0);
        FactionGiftChoice baseline = choose(request);
        observation.put("date_raw", -1);
        observation.putNull("gift_opinion_modifier_value");
        assertEquals(baseline, choose(request));
        observation.put("gift_opinion_modifier_value", false);
        assertThrows(IllegalArgumentException.class, () -> choose(request));
        observation.putNull("gift_opinion_modifier_value");
        observation.put("date_raw", 1.0);
        assertThrows(IllegalArgumentException.class, () -> choose(request));
    }

    @Test
    void rejectsMalformedUtf8AndBoundedInputOrObservationCount() throws IOException {
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(new byte[0]));
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(
                new byte[FactionGiftPolicy.MAX_INPUT_BYTES + 1]));
        byte[] malformed = {'{', '"', (byte) 0xC3, '"', ':', '0', '}'};
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(malformed));
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(
                "{}".getBytes(StandardCharsets.UTF_16LE)));
        ObjectNode request = input();
        ArrayNode observations = JSON.createArrayNode();
        for (int index = 0; index <= FactionGiftPolicy.MAX_OBSERVATIONS; index++) observations.addNull();
        request.set("observations", observations);
        assertThrows(IllegalArgumentException.class, () -> choose(request));
    }

    @Test
    void strictPersistedChoiceRejectsFloatIdsMissingNullsAndStatusConflict() throws IOException {
        byte[] encoded = FactionGiftPolicy.encode(choose(input()));
        ObjectNode choice = (ObjectNode) JSON.readTree(encoded);
        choice.put("source_faction_id", 771.0);
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.decodeChoice(JSON.writeValueAsBytes(choice)));
        choice.put("source_faction_id", 771);
        choice.remove("gold_cost_raw");
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.decodeChoice(JSON.writeValueAsBytes(choice)));
        choice.put("gold_cost_raw", 7_500_000);
        choice.put("status", "budget_reject");
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.decodeChoice(JSON.writeValueAsBytes(choice)));

        FactionGiftChoice declined = new FactionGiftChoice.Declined(FactionGiftChoice.Reason.COMPLETE_NATIVE_EMPTY);
        ObjectNode decline = (ObjectNode) JSON.readTree(FactionGiftPolicy.encode(declined));
        decline.put("recipient_character_id", 33011);
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.decodeChoice(JSON.writeValueAsBytes(decline)));
        decline.putNull("recipient_character_id");
        decline.remove("membership_role");
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.decodeChoice(JSON.writeValueAsBytes(decline)));
    }

    @Test
    void typedModelCannotConstructPartialOrInvalidSelectedOutcome() {
        assertThrows(IllegalArgumentException.class, () -> new FactionGiftChoice.Declined(FactionGiftChoice.Reason.SELECTED));
        assertThrows(IllegalArgumentException.class, () -> new FactionGiftChoice.Selected(
                BigInteger.ZERO, BigInteger.ONE, FactionGiftChoice.MembershipRole.LEADER,
                BigInteger.ONE, BigInteger.ONE, BigInteger.ZERO, BigInteger.ONE,
                BigInteger.ONE, BigInteger.ONE, BigInteger.ONE));
    }

    private static JsonNode golden() throws IOException {
        try (InputStream source = FactionGiftPolicyTest.class.getResourceAsStream("/factiongift/python-golden-v1.json")) {
            assertNotNull(source, "committed original-producer golden is mandatory");
            byte[] bytes = source.readNBytes(145_001);
            assertTrue(bytes.length <= 145_000, "bounded golden");
            return JSON.readTree(bytes);
        }
    }

    private static ObjectNode input() throws IOException {
        return (ObjectNode) golden().path("cases").get(0).path("input").deepCopy();
    }

    private static FactionGiftChoice choose(JsonNode request) throws IOException {
        return FactionGiftPolicy.choose(JSON.writeValueAsBytes(request));
    }

    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}
