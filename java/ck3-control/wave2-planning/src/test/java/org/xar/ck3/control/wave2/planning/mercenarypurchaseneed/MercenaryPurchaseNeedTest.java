package org.xar.ck3.control.wave2.planning.mercenarypurchaseneed;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.planning.mercenarypurchaseneed.MercenaryPurchaseNeed.*;

final class MercenaryPurchaseNeedTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void everyActualProducerCaseMatchesUsingOriginalRequestBytes() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.mercenary-purchase-model-need.golden.v1", golden.path("schema").textValue());
        assertEquals(0, golden.path("producer_exit_code").intValue());
        assertFalse(golden.path("machine_id").textValue().isBlank());
        assertEquals("d9f32c208fa47a0b2007f4a5194462a9929fac2f636c8e58ba25a8cffb1a089c",
                golden.path("producer_ref").path("sha256").textValue());
        int cases = 0;
        for (JsonNode sample : golden.get("cases")) {
            byte[] wire = bytes(sample.get("request_json").textValue());
            Need need = observe(MercenaryPurchaseNeedCodec.decode(wire));
            byte[] result = MercenaryPurchaseNeedCodec.encode(need);
            assertEquals(sample.get("expected_result"), JSON.readTree(result), sample.get("name").textValue());
            assertEquals(need, MercenaryPurchaseNeedCodec.decodeResult(result));
            cases++;
        }
        assertEquals(22, cases);
    }

    @Test
    void unknownCurrentCountsKeepTheExistingQueryAndDoNotClaimWarSafety() throws IOException {
        Need need = observe(new Input(List.of(war(Optional.empty(), Optional.of(BigInteger.TEN), Truth.FALSE)),
                new HostileUnion(List.of(BigInteger.ONE), Truth.FALSE)));
        assertTrue(need.queryCanChangeCurrentHeadcountFlipModel());
        JsonNode result = JSON.readTree(MercenaryPurchaseNeedCodec.encode(need));
        assertTrue(result.get("overall_war_safe").isNull());
        assertFalse(result.get("future_enemy_reinforcements_bounded").booleanValue());
        assertTrue(result.get("pending_hire_observations_must_bypass").booleanValue());
    }

    @Test
    void sharedForcesRemainUnknownUntilExplicitlyFalseAndNeverCreateNeedWithoutRecoverableWars() {
        War advantage = war(Optional.of(BigInteger.TEN), Optional.of(BigInteger.ONE), Truth.FALSE);
        for (Truth shared : new Truth[]{Truth.TRUE, Truth.UNKNOWN}) {
            assertTrue(observe(new Input(List.of(advantage), new HostileUnion(List.of(BigInteger.ONE, BigInteger.TWO), shared)))
                    .queryCanChangeCurrentHeadcountFlipModel());
        }
        assertFalse(observe(new Input(List.of(advantage), new HostileUnion(List.of(BigInteger.ONE, BigInteger.TWO), Truth.FALSE)))
                .queryCanChangeCurrentHeadcountFlipModel());
        assertFalse(observe(new Input(List.of(), new HostileUnion(List.of(BigInteger.ONE, BigInteger.TWO), Truth.UNKNOWN)))
                .queryCanChangeCurrentHeadcountFlipModel());
    }

    @Test
    void pendingAndUnknownHireReceiptsBypassThePruningModel() {
        Input noNeed = new Input(List.of(), new HostileUnion(List.of(), Truth.FALSE));
        assertFalse(((ModelRoute) route(noNeed, PendingHire.ABSENT)).need().queryCanChangeCurrentHeadcountFlipModel());
        assertEquals(new ExistingReceiptRoute(PendingHire.PENDING), route(noNeed, PendingHire.PENDING));
        assertEquals(new ExistingReceiptRoute(PendingHire.UNKNOWN), route(noNeed, PendingHire.UNKNOWN));
    }

    @Test
    void scoreThresholdAndUnprotectedWarsUseTheExistingCurrentModel() {
        for (int score : new int[]{-101, -100}) {
            War terminal = new War(List.of("pressure"), Optional.of(BigInteger.valueOf(score)), Optional.empty(), Optional.empty(), Truth.TRUE);
            assertFalse(observe(new Input(List.of(terminal), new HostileUnion(List.of(), Truth.UNKNOWN)))
                    .queryCanChangeCurrentHeadcountFlipModel());
        }
        War recoverable = new War(List.of("pressure"), Optional.of(BigInteger.valueOf(-99)), Optional.empty(), Optional.empty(), Truth.TRUE);
        assertTrue(observe(new Input(List.of(recoverable), new HostileUnion(List.of(), Truth.FALSE)))
                .queryCanChangeCurrentHeadcountFlipModel());
        War noPressure = new War(List.of(), Optional.of(BigInteger.ZERO), Optional.empty(), Optional.empty(), Truth.TRUE);
        assertFalse(observe(new Input(List.of(noPressure), new HostileUnion(List.of(), Truth.FALSE)))
                .queryCanChangeCurrentHeadcountFlipModel());
    }

    @Test
    void malformedObservedCountTypesAreRejectedAndCannotPruneAQuery() throws IOException {
        String baseline = golden().get("cases").get(0).get("request_json").textValue();
        for (String token : new String[]{"true", "1000.0", "\"1000\"", "-1"}) {
            byte[] wire = bytes(baseline.replace("\"observed_player_raised_soldiers\":1000",
                    "\"observed_player_raised_soldiers\":" + token));
            assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decode(wire));
        }
        ObjectNode request = request();
        ((ObjectNode) request.path("priority").path("primary_war_hostile_union_v1")).put("shared_force_deficit", 0);
        byte[] wire = JSON.writeValueAsBytes(request);
        assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decode(wire));
    }

    @Test
    void extensiblePriorityIsProjectedAndEnvelopeFieldErrorsAreRejected() throws IOException {
        ObjectNode request = request();
        ((ObjectNode) request.get("priority")).putObject("future_input").put("available", true);
        Need original = observe(MercenaryPurchaseNeedCodec.decode(JSON.writeValueAsBytes(request)));
        assertTrue(original.queryCanChangeCurrentHeadcountFlipModel());
        for (String field : new String[]{"schema", "priority"}) {
            ObjectNode missing = request.deepCopy(); missing.remove(field);
            byte[] raw = JSON.writeValueAsBytes(missing);
            assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decode(raw));
        }
        request.put("same_frame_green", true);
        byte[] extra = JSON.writeValueAsBytes(request);
        assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decode(extra));
        assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decode(bytes("{\"schema\":1,\"schema\":2}")));
        assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decode(new byte[65_537]));
    }

    @Test
    void receiptRoundtripRejectsSafetyClaimsOrChangedBranchFields() throws IOException {
        Need need = new Need(false, Reason.NO_RECOVERABLE_CURRENT_DEFICIT);
        byte[] encoded = MercenaryPurchaseNeedCodec.encode(need);
        assertEquals(need, MercenaryPurchaseNeedCodec.decodeResult(encoded));
        for (String field : new String[]{"overall_war_safe", "future_enemy_reinforcements_bounded"}) {
            ObjectNode altered = (ObjectNode) JSON.readTree(encoded); altered.put(field, true);
            byte[] changed = JSON.writeValueAsBytes(altered);
            assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decodeResult(changed));
        }
        ObjectNode missing = (ObjectNode) JSON.readTree(encoded); missing.remove("pending_hire_observations_must_bypass");
        byte[] changed = JSON.writeValueAsBytes(missing);
        assertThrows(IllegalArgumentException.class, () -> MercenaryPurchaseNeedCodec.decodeResult(changed));
    }

    @Test
    void exactLargeCountsAndDefensiveCopiesPreserveTheValueContract() {
        BigInteger huge = BigInteger.ONE.shiftLeft(90);
        Input input = new Input(List.of(war(Optional.of(huge), Optional.of(huge.add(BigInteger.ONE)), Truth.TRUE)),
                new HostileUnion(List.of(BigInteger.ONE), Truth.FALSE));
        assertTrue(observe(input).queryCanChangeCurrentHeadcountFlipModel());
        assertEquals(huge, input.wars().get(0).observedPlayerRaisedSoldiers().orElseThrow());
        assertThrows(UnsupportedOperationException.class, () -> input.wars().clear());
        assertThrows(UnsupportedOperationException.class, () -> input.hostileUnion().warIds().clear());
    }

    private static War war(Optional<BigInteger> own, Optional<BigInteger> enemy, Truth deficit) {
        return new War(List.of("observed-pressure"), Optional.of(BigInteger.valueOf(-20)), own, enemy, deficit);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = MercenaryPurchaseNeedTest.class.getResourceAsStream("/mercenarypurchaseneed/golden.json")) {
            if (stream == null) { throw new IllegalStateException("actual producer golden missing; capture not executed"); }
            return JSON.readTree(stream);
        }
    }
    private static ObjectNode request() throws IOException {
        return (ObjectNode) JSON.readTree(golden().get("cases").get(0).get("request_json").textValue());
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
