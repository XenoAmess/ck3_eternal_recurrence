package org.xar.ck3.control.finance.feastbudget;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Observed;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Presence;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy.Request;

final class FeastBudgetPolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = FeastBudgetPolicyTest.class.getResourceAsStream("/feastbudget/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("committed original producer golden required"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode vector : golden().get("cases")) {
            if (name.equals(vector.get("name").textValue())) { return ((ObjectNode) vector.get("request")).deepCopy(); }
        }
        throw new IOException("missing golden vector: " + name);
    }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value); }
    private static ObjectNode nested(ObjectNode root, String... names) {
        JsonNode node = root;
        for (String name : names) { node = node.get(name); }
        return (ObjectNode) node;
    }

    @Test void allThirtyOriginalProducerResultsAndTypedProjectionRoundTrips() throws IOException {
        JsonNode vectors = golden();
        assertEquals("xar.feast-budget-original-producer-golden.v1", vectors.get("schema").textValue());
        assertEquals(6, vectors.get("source_bindings").size());
        assertEquals(30, vectors.get("cases").size());
        for (JsonNode vector : vectors.get("cases")) {
            byte[] input = bytes(vector.get("request"));
            Request parsed = FeastBudgetCodec.decode(input);
            assertEquals(parsed, FeastBudgetCodec.decode(FeastBudgetCodec.encodeRequest(parsed)), vector.get("name").textValue());
            assertArrayEquals(bytes(vector.get("expected")), FeastBudgetCodec.assess(input), vector.get("name").textValue());
        }
    }

    @Test void committedCaptureIsBoundRatherThanReplacedByPythonAtTestTime() throws IOException, NoSuchAlgorithmException {
        try (InputStream stream = FeastBudgetPolicyTest.class.getResourceAsStream("/feastbudget/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("golden absent"); }
            String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(stream.readAllBytes()));
            assertEquals("bd3aea63baf65c1fcbe36310d629cd3813343ca29e2f3de3b68603db8ec7b338", actual);
        }
    }

    @Test void unknownReserveAndObservedZeroAreDifferent() throws IOException {
        JsonNode unknown = StrictJson.parse(FeastBudgetCodec.assess(bytes(request("war_unknown_reserve"))));
        JsonNode zero = StrictJson.parse(FeastBudgetCodec.assess(bytes(request("maintenance_zero"))));
        assertTrue(unknown.get("budget").get("war_cash_reserve_raw").isNull());
        assertFalse(unknown.has("financial_reservation"));
        assertEquals(BigInteger.ZERO, zero.get("budget").get("war_cash_reserve_raw").bigIntegerValue());
        assertTrue(zero.has("financial_reservation"));
        assertFalse(zero.get("financial_reservation").get("native_future_cost_upper_bound").booleanValue());
        assertFalse(zero.get("financial_reservation").get("m5_complete_war_cash_receipt").booleanValue());
    }

    @Test void integerTokensNeverCoerceBooleanDecimalOrString() throws IOException {
        List<JsonNode> wrong = List.of(BooleanNode.TRUE, DecimalNode.valueOf(new BigDecimal("29829.0")), TextNode.valueOf("29829"));
        for (JsonNode value : wrong) {
            ObjectNode input = request("peaceful_no_reserve"); nested(input, "inputs").set("actor_character_id", value);
            assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.assess(bytesAllowFloat(input)));
            ObjectNode rate = request("war_observed_allocation");
            nested(rate, "campaign_root", "player_max_monthly_gold_maintenance_v1", "value").set("raw", value);
            assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.assess(bytesAllowFloat(rate)));
            ObjectNode scale = request("war_observed_allocation");
            nested(scale, "campaign_root", "player_max_monthly_gold_maintenance_v1", "value").set("scale", value);
            assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.assess(bytesAllowFloat(scale)));
        }
    }

    @Test void wrapperAndValidatedLedgerInputsRejectMissingUnknownAndDuplicateFields() throws IOException {
        ObjectNode missing = request("peaceful_no_reserve"); missing.remove("ledgers");
        assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.decode(bytes(missing)));
        ObjectNode unknown = request("peaceful_no_reserve"); unknown.put("fallback", true);
        assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.decode(bytes(unknown)));
        ObjectNode ledger = request("peaceful_no_reserve"); nested(ledger, "ledgers", "construction").remove("pending");
        assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.decode(bytes(ledger)));
        ObjectNode wrongLedger = request("peaceful_no_reserve");
        nested(wrongLedger, "ledgers", "construction").put("pending", false);
        assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.decode(bytes(wrongLedger)));
        String original = new String(bytes(request("peaceful_no_reserve")), StandardCharsets.UTF_8);
        String duplicate = "{\"schema\":\"xar.feast-budget-projection.v1\"," + original.substring(1);
        assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> FeastBudgetCodec.decode(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test void missingInteractionIsNotAnObservedClearInteraction() throws IOException {
        Request clear = FeastBudgetCodec.decode(bytes(request("peaceful_no_reserve")));
        Request missing = FeastBudgetCodec.decode(bytes(request("interaction_missing")));
        assertEquals(Presence.NULL, clear.snapshot().pendingInteraction());
        assertEquals(Presence.MISSING, missing.snapshot().pendingInteraction());
        assertNotEquals(clear.snapshot().pendingInteraction(), missing.snapshot().pendingInteraction());
        assertInstanceOf(Observed.class, FeastBudgetPolicy.observe(clear));
        assertEquals("interaction_pending_or_unobserved",
                StrictJson.parse(FeastBudgetCodec.encode(FeastBudgetPolicy.observe(missing))).get("reason").textValue());
    }

    @Test void maintenanceMultiplicationDoesNotOverflowSignedLongOrRoundThroughDouble() throws IOException {
        Observed observed = assertInstanceOf(Observed.class,
                FeastBudgetPolicy.observe(FeastBudgetCodec.decode(bytes(request("maintenance_uint64")))));
        assertEquals(new BigInteger("332041393326771929070"), observed.warCashReserveRaw());
        JsonNode output = StrictJson.parse(FeastBudgetCodec.encode(observed));
        assertEquals(observed.warCashReserveRaw(), output.get("budget").get("war_cash_reserve_raw").bigIntegerValue());
    }

    @Test void extensibleSdkContainersDoNotChangeProjectedAllocation() throws IOException {
        ObjectNode input = request("war_observed_allocation"); byte[] before = FeastBudgetCodec.assess(bytes(input));
        nested(input, "snapshot").put("future_native_extension", "retained by original evidence owner");
        nested(input, "snapshot").put("unrelated_float", new BigDecimal("0.5"));
        nested(input, "inputs").put("planning_stage", 5);
        nested(input, "campaign_root").put("unrelated_context", true);
        assertArrayEquals(before, FeastBudgetCodec.assess(bytesAllowFloat(input)));
    }

    private static byte[] bytesAllowFloat(JsonNode value) {
        // Negative vectors need actual float tokens; the shared canonical writer intentionally rejects them.
        return value.toString().getBytes(StandardCharsets.UTF_8);
    }
}
