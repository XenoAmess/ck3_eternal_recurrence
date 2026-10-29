package org.xar.ck3.control.wave2.planning.warcashprovenance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapModels.*;

final class WarFinancingCapabilityGapTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void actualOldProducerCasesMatchWithoutNormalizingRawFloatTokens() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.war-financing-capability-gap.golden.v1", golden.path("schema").textValue());
        assertEquals(0, golden.path("producer_exit_code").intValue());
        assertFalse(golden.path("machine_id").textValue().isBlank());
        assertEquals("9eb2f93a573e2c6f467e6ff478c50d9856350cb4c436b5403fd0dd70351b772e",
                golden.path("producer_refs").get(0).path("sha256").textValue());
        int cases = 0;
        for (JsonNode example : golden.get("cases")) {
            byte[] wire = bytes(example.get("request_json").textValue());
            if (example.has("expected_exception")) {
                assertEquals("ValueError", example.get("expected_exception").textValue());
                assertThrows(IllegalArgumentException.class,
                        () -> WarFinancingCapabilityGap.observe(FinancingGapCodec.decode(wire)), example.get("name").textValue());
            } else {
                Optional<Gap> actual = WarFinancingCapabilityGap.observe(FinancingGapCodec.decode(wire));
                byte[] encoded = FinancingGapCodec.encode(actual);
                assertEquals(example.get("expected_result"), JSON.readTree(encoded), example.get("name").textValue());
                assertEquals(actual, FinancingGapCodec.decodeResult(encoded));
            }
            cases++;
        }
        assertEquals(31, cases);
    }

    @Test
    void advertisedConfirmNeverProvesLoanTermsFundsOrSubmitEligibility() throws IOException {
        ObjectNode request = request();
        request.putArray("bridge_capabilities").add(FinancingGapCodec.CAPABILITY);
        JsonNode receipt = result(request);
        JsonNode debt = receipt.get("legal_debt");
        assertTrue(debt.path("source_reviewed_confirm_route").path("advertised_in_supplied_bridge_capabilities").booleanValue());
        assertFalse(debt.path("current_build_full_terms_verified").booleanValue());
        assertFalse(debt.path("typed_debt_readback_verified").booleanValue());
        assertFalse(debt.path("independently_attributed_received_funds_verified").booleanValue());
        assertFalse(debt.path("submit_planned").booleanValue());
        assertTrue(debt.path("principal_quote_raw").isNull());
        assertTrue(receipt.path("cancel_construction").path("refund_quote_raw").isNull());
        assertFalse(receipt.path("cancel_construction").path("submit_planned").booleanValue());
        assertEquals(0, receipt.path("unreceived_funding_credited_raw").intValue());
        assertTrue(receipt.path("selected_action").isNull());
        assertTrue(receipt.path("unknown_submission_must_not_be_replayed").booleanValue());
        assertTrue(receipt.path("continue_existing_war_action").booleanValue());
    }

    @Test
    void sourceContainersAreExtensibleButRootIdentityDriftInvalidatesOnlyMaintenance() throws IOException {
        ObjectNode request = request();
        ((ObjectNode) request.get("snapshot")).putObject("additional_native_sibling").put("future", true);
        ((ObjectNode) request.get("root")).putArray("future_root_sibling").add(1);
        assertEquals(BigInteger.valueOf(36_000_000),
                WarFinancingCapabilityGap.observe(decode(request)).orElseThrow().ordinaryMilitaryBufferRaw().orElseThrow());
        for (String field : new String[]{"player_character_id", "snapshot_revision", "date_raw"}) {
            ObjectNode changed = request.deepCopy();
            ((ObjectNode) changed.get("root")).put(field, 1);
            Gap gap = WarFinancingCapabilityGap.observe(decode(changed)).orElseThrow();
            assertTrue(gap.ordinaryMilitaryBufferRaw().isEmpty());
            assertEquals(MaintenanceStatus.UNOBSERVED, gap.maximumMilitaryMaintenanceStatus());
        }
    }

    @Test
    void historicalPriorityCannotTriggerACurrentFinancingGap() throws IOException {
        for (String active : new String[]{"[]", "null", "[{\"war_id\":100}]", "[{\"war_id\":true}]"}) {
            ObjectNode request = request();
            ((ObjectNode) request.get("snapshot")).set("active_wars", JSON.readTree(active));
            assertTrue(WarFinancingCapabilityGap.observe(decode(request)).isEmpty());
        }
    }

    @Test
    void currentCashAndCrisisScoreBoundariesAreExact() throws IOException {
        ObjectNode request = request();
        ObjectNode war = (ObjectNode) request.path("priority").path("wars").get(0);
        war.put("player_relative_war_score", 40);
        ((ObjectNode) request.path("snapshot").path("played_character_gold")).put("raw", 36_000_000);
        assertTrue(WarFinancingCapabilityGap.observe(decode(request)).isEmpty());
        ((ObjectNode) request.path("snapshot").path("played_character_gold")).put("raw", 35_999_999);
        assertTrue(WarFinancingCapabilityGap.observe(decode(request)).isPresent());
        ((ObjectNode) request.path("snapshot").path("played_character_gold")).put("raw", 100_000_000);
        war.put("player_relative_war_score", -25);
        assertEquals(1, WarFinancingCapabilityGap.observe(decode(request)).orElseThrow().crisisWarIds().size());
        war.put("player_relative_war_score", -24);
        assertTrue(WarFinancingCapabilityGap.observe(decode(request)).isEmpty());
    }

    @Test
    void invalidOptionalCashNeverBecomesZeroAndUnknownAdvertisementRemainsNull() throws IOException {
        ObjectNode request = request();
        ((ObjectNode) request.path("snapshot").path("played_character_gold")).put("raw", false);
        Gap gap = WarFinancingCapabilityGap.observe(decode(request)).orElseThrow();
        assertTrue(gap.observedTreasuryRaw().isEmpty());
        JsonNode receipt = JSON.readTree(FinancingGapCodec.encode(Optional.of(gap)));
        assertTrue(receipt.get("observed_treasury_raw").isNull());
        assertTrue(receipt.path("legal_debt").path("source_reviewed_confirm_route")
                .get("advertised_in_supplied_bridge_capabilities").isNull());
        assertEquals(0, receipt.get("unreceived_funding_credited_raw").intValue());
    }

    @Test
    void pendingConstructionIsIntentAndDoesNotBecomeObservedProjectOrCash() throws IOException {
        ObjectNode request = request();
        ((ObjectNode) request.get("construction_ledger")).putObject("pending").put("status", "submission_unresolved");
        JsonNode receipt = result(request);
        assertTrue(receipt.get("construction_intent_present").booleanValue());
        assertFalse(receipt.get("current_active_project_independently_observed").booleanValue());
        assertTrue(receipt.get("selected_action").isNull());
        assertEquals(0, receipt.get("unreceived_funding_credited_raw").intValue());
    }

    @Test
    void malformedIdentityTokensAreRejectedWithoutBooleanOrFloatCoercion() throws IOException {
        String baseline = golden().get("cases").get(0).get("request_json").textValue();
        for (String token : new String[]{"true", "12.0", "\"12\"", "null", "0", "-1"}) {
            byte[] raw = bytes(baseline.replace("\"native_revision\":12", "\"native_revision\":" + token));
            assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(raw));
        }
        ObjectNode request = request();
        ((ObjectNode) request.get("snapshot")).remove("episode_run_id");
        byte[] missing = JSON.writeValueAsBytes(request);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(missing));
    }

    @Test
    void exactRequestEnvelopeRejectsMissingUnknownDuplicateKeysAndBadCapabilityCollections() throws IOException {
        ObjectNode base = request();
        for (String field : new String[]{"schema", "snapshot", "priority", "root", "construction_ledger", "bridge_capabilities"}) {
            ObjectNode missing = base.deepCopy(); missing.remove(field);
            byte[] raw = JSON.writeValueAsBytes(missing);
            assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(raw));
        }
        ObjectNode unknown = base.deepCopy(); unknown.put("same_frame_verified", true);
        byte[] extra = JSON.writeValueAsBytes(unknown);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(extra));
        ObjectNode duplicateCaps = base.deepCopy(); duplicateCaps.putArray("bridge_capabilities").add("c").add("c");
        byte[] duplicate = JSON.writeValueAsBytes(duplicateCaps);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(duplicate));
        ObjectNode wrongCaps = base.deepCopy(); wrongCaps.put("bridge_capabilities", true);
        byte[] wrong = JSON.writeValueAsBytes(wrongCaps);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(wrong));
        assertThrows(IllegalArgumentException.class,
                () -> FinancingGapCodec.decode(bytes("{\"schema\":\"a\",\"schema\":\"b\"}")));
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decode(new byte[65_537]));
    }

    @Test
    void receiptRoundtripRejectsAlteredEligibilityFlagsMissingAndWrongTypes() throws IOException {
        Optional<Gap> gap = WarFinancingCapabilityGap.observe(decode(request()));
        byte[] valid = FinancingGapCodec.encode(gap);
        assertEquals(gap, FinancingGapCodec.decodeResult(valid));
        ObjectNode altered = (ObjectNode) JSON.readTree(valid);
        ((ObjectNode) altered.get("legal_debt")).put("submit_planned", true);
        byte[] raw = JSON.writeValueAsBytes(altered);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decodeResult(raw));
        altered = (ObjectNode) JSON.readTree(valid);
        altered.remove("observed_treasury_raw");
        byte[] missing = JSON.writeValueAsBytes(altered);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decodeResult(missing));
        altered = (ObjectNode) JSON.readTree(valid);
        altered.put("ordinary_military_buffer_raw", true);
        byte[] wrong = JSON.writeValueAsBytes(altered);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decodeResult(wrong));
        assertEquals(Optional.empty(), FinancingGapCodec.decodeResult(bytes("null")));
    }

    @Test
    void exactLargeIntegersSurviveTheJsonBoundaryAndModelsRemainImmutable() throws IOException {
        ObjectNode request = request();
        BigInteger huge = BigInteger.ONE.shiftLeft(90);
        ((ObjectNode) request.path("snapshot").path("played_character_gold")).put("raw", huge.negate());
        Input input = decode(request);
        Gap gap = WarFinancingCapabilityGap.observe(input).orElseThrow();
        assertEquals(huge.negate(), gap.observedTreasuryRaw().orElseThrow());
        assertEquals(Optional.of(gap), FinancingGapCodec.decodeResult(FinancingGapCodec.encode(Optional.of(gap))));
        assertThrows(UnsupportedOperationException.class, () -> input.activeWarIds().add(BigInteger.ONE));
        assertThrows(UnsupportedOperationException.class, () -> input.priorityWars().clear());
        assertThrows(UnsupportedOperationException.class, () -> gap.crisisWarIds().clear());
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = WarFinancingCapabilityGapTest.class.getResourceAsStream("/warcashprovenance/golden.json")) {
            if (stream == null) { throw new IllegalStateException("actual producer golden missing; capture has not executed"); }
            return JSON.readTree(stream);
        }
    }
    private static ObjectNode request() throws IOException {
        return (ObjectNode) JSON.readTree(golden().get("cases").get(0).get("request_json").textValue());
    }
    private static Input decode(ObjectNode request) throws IOException { return FinancingGapCodec.decode(JSON.writeValueAsBytes(request)); }
    private static JsonNode result(ObjectNode request) throws IOException {
        return JSON.readTree(FinancingGapCodec.encode(WarFinancingCapabilityGap.observe(decode(request))));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
