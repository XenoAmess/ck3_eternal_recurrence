package org.xar.ck3.control.military.defenderrisk;

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
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class DefenderContinueRiskTest {
    private static final String GOLDEN_SHA = "3efece10495c0cd208d27f251056593aabf047f259844e265cbed8efc3323656";

    @TestFactory
    Stream<DynamicTest> originalProducerVectors() throws IOException, NoSuchAlgorithmException {
        byte[] raw = resource();
        assertEquals(GOLDEN_SHA, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        JsonNode fixture = StrictJson.parse(raw);
        assertEquals("xar.ck3.java.defenderrisk.golden.v1", fixture.get("schema").textValue());
        assertEquals(14, fixture.get("cases").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                // Requests may carry opaque floating-point conflict evidence; the policy never computes with it.
                byte[] input = vector.get("request").toString().getBytes(StandardCharsets.UTF_8);
                JsonNode actual = StrictJson.parse(DefenderContinueRiskCodec.evaluate(input));
                assertEquals(vector.get("expected"), actual);
                assertReadOnly(actual);
            }));
        }
        return tests.stream();
    }

    @Test
    void allProducerInputsRoundTripWithoutPythonProcess() throws IOException {
        for (JsonNode vector : StrictJson.parse(resource()).get("cases")) {
            DefenderContinueRisk.Request request = DefenderContinueRiskCodec.decode(bytes(vector.get("request")));
            byte[] encoded = DefenderContinueRiskCodec.encodeRequest(request);
            assertEquals(request, DefenderContinueRiskCodec.decode(encoded));
            assertEquals(vector.get("expected"), StrictJson.parse(DefenderContinueRiskCodec.evaluate(encoded)));
        }
    }

    @Test
    void requiredFieldsNullAndUnknownKeysRemainDistinct() throws IOException {
        for (String key : List.of("frame", "contact", "siege")) {
            ObjectNode input = input(0);
            input.remove(key);
            rejected(input);
        }
        ObjectNode extra = input(0);
        extra.put("action", "surrender");
        rejected(extra);
        ObjectNode emptyContact = input(0);
        emptyContact.set("contact", StrictJson.object());
        rejected(emptyContact);
        ObjectNode missingArrival = input(0);
        ((ObjectNode) missingArrival.get("contact")).remove("subject_target_arrival_date_raw");
        rejected(missingArrival);
        ObjectNode nullable = input(2);
        JsonNode absent = StrictJson.parse(DefenderContinueRiskCodec.evaluate(bytes(nullable)));
        assertFalse(absent.get("contact").has("source_sha256"));
        assertTrue(absent.get("contact").get("target_arrival_date_raw").isNull());
    }

    @Test
    void frameIntegersRejectBooleanFloatStringAndNullIncludingNestedSourceFrame() throws IOException {
        for (String field : List.of("revision", "native_revision", "date_raw", "connection_generation",
                "played_character_id", "war_id", "player_relative_war_score")) {
            for (String rawToken : List.of("true", "1.0", "\"1\"", "null")) {
                ObjectNode input = input(0);
                rejectedRawField(input, (ObjectNode) input.get("frame"), field, rawToken);
                ObjectNode nested = input(0);
                rejectedRawField(nested, (ObjectNode) nested.get("contact").get("source_frame"), field, rawToken);
            }
        }
    }

    @Test
    void positiveIdentitiesAndExactSourceFrameAreRequired() throws IOException {
        for (String field : List.of("revision", "native_revision", "connection_generation", "played_character_id", "war_id")) {
            ObjectNode input = input(0);
            ((ObjectNode) input.get("frame")).put(field, 0);
            rejected(input);
        }
        ObjectNode crossed = input(0);
        ObjectNode source = (ObjectNode) crossed.get("contact").get("source_frame");
        source.put("native_revision", source.get("native_revision").bigIntegerValue().subtract(BigInteger.ONE));
        rejected(crossed);
        ObjectNode sourceShape = input(0);
        ((ObjectNode) sourceShape.get("contact").get("source_frame")).put("unexpected", 1);
        rejected(sourceShape);
        ObjectNode lowercase = input(0);
        ((ObjectNode) lowercase.get("contact")).put("source_sha256",
                lowercase.get("contact").get("source_sha256").textValue().toLowerCase(java.util.Locale.ROOT));
        rejected(lowercase);
    }

    @Test
    void contactIntegerAndBooleanTokensAreStrict() throws IOException {
        for (String field : List.of("subject_army_id", "target_province_id", "horizon_start_date_raw",
                "horizon_end_date_raw", "first_waypoint_arrival_date_raw", "subject_target_arrival_date_raw")) {
            for (String rawToken : List.of("true", "1.0", "\"1\"")) {
                ObjectNode input = input(0);
                rejectedRawField(input, (ObjectNode) input.get("contact"), field, rawToken);
            }
        }
        ObjectNode nonBoolean = input(0);
        ((ObjectNode) nonBoolean.get("contact")).put("one_day_contact_free", 1);
        rejected(nonBoolean);
        ObjectNode conflicts = input(0);
        ((ObjectNode) conflicts.get("contact")).putNull("conflicts");
        rejected(conflicts);
    }

    @Test
    void contactHorizonAndArrivalOrderingRejectUnsupportedBounds() throws IOException {
        BigInteger start = input(0).get("frame").get("date_raw").bigIntegerValue();
        for (BigInteger end : List.of(start, start.subtract(BigInteger.ONE), start.add(BigInteger.valueOf(25)))) {
            ObjectNode input = input(0);
            ((ObjectNode) input.get("contact")).put("horizon_end_date_raw", end);
            rejected(input);
        }
        ObjectNode before = input(0);
        ((ObjectNode) before.get("contact")).put("first_waypoint_arrival_date_raw", start);
        rejected(before);
        ObjectNode afterTarget = input(0);
        ObjectNode contact = (ObjectNode) afterTarget.get("contact");
        contact.put("first_waypoint_arrival_date_raw", contact.get("subject_target_arrival_date_raw").bigIntegerValue().add(BigInteger.ONE));
        rejected(afterTarget);
    }

    @Test
    void offsiteRosterCannotDuplicateOrIncludeSubjectArmy() throws IOException {
        ObjectNode duplicated = input(0);
        ArrayNode arrivals = (ArrayNode) duplicated.get("contact").get("offsite_target_arrivals");
        arrivals.add(arrivals.get(0).deepCopy());
        rejected(duplicated);
        ObjectNode ownArmy = input(0);
        ObjectNode contact = (ObjectNode) ownArmy.get("contact");
        ((ObjectNode) contact.get("offsite_target_arrivals").get(0)).set("army_id", contact.get("subject_army_id"));
        rejected(ownArmy);
        ObjectNode wrongType = input(0);
        ((ObjectNode) wrongType.get("contact").get("offsite_target_arrivals").get(0)).put("army_id", true);
        rejected(wrongType);
    }

    @Test
    void siegeTimerBoundsDoNotOverflowAndZeroStillDoesNotAuthorizeAnExit() throws IOException {
        for (BigInteger days : List.of(BigInteger.valueOf(-1), DefenderContinueRisk.MAX_SIEGE_DAYS.add(BigInteger.ONE))) {
            ObjectNode input = input(1);
            ((ObjectNode) input.get("siege")).put("remaining_days_estimate", days);
            rejected(input);
        }
        for (String rawToken : List.of("false", "0.0", "\"0\"")) {
            ObjectNode input = input(1);
            rejectedRawField(input, (ObjectNode) input.get("siege"), "remaining_days_estimate", rawToken);
        }
        ObjectNode empty = input(1);
        ((ObjectNode) empty.get("siege")).putArray("besieging_army_ids");
        rejected(empty);
        ObjectNode duplicate = input(1);
        ArrayNode armies = (ArrayNode) duplicate.get("siege").get("besieging_army_ids");
        armies.add(armies.get(0).deepCopy());
        rejected(duplicate);
    }

    @Test
    void routeAndSiegeCannotJoinAcrossProvinces() throws IOException {
        ObjectNode input = input(3);
        ObjectNode siege = (ObjectNode) input.get("siege");
        siege.put("province_id", siege.get("province_id").bigIntegerValue().add(BigInteger.ONE));
        rejected(input);
    }

    @Test
    void duplicateKeysTrailingTokensAndInvalidUtf8RejectBeforeDomainConstruction() {
        assertThrows(ContractViolationException.class, () -> DefenderContinueRiskCodec.decode(
                "{\"frame\":null,\"frame\":null,\"contact\":null,\"siege\":null}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> DefenderContinueRiskCodec.decode("{} {}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> DefenderContinueRiskCodec.decode(new byte[]{(byte) 0xc3, (byte) 0x28}));
    }

    @Test
    void sourceAndCollectionsRemainImmutable() throws IOException {
        DefenderContinueRisk.Request request = DefenderContinueRiskCodec.decode(bytes(input(0)));
        assertNotNull(request.contact());
        assertThrows(UnsupportedOperationException.class, () -> request.contact().offsiteTargetArrivals().clear());
        DefenderContinueRisk.Envelope envelope = DefenderContinueRisk.observe(request);
        assertThrows(UnsupportedOperationException.class, () -> envelope.blockers().clear());
    }

    private static void assertReadOnly(JsonNode result) {
        assertTrue(result.get("read_only").booleanValue());
        assertFalse(result.get("material_comparison_ready").booleanValue());
        for (String field : List.of("continuation_loss_upper_raw", "continuation_win_probability",
                "surrender_vs_continue_utility_interval", "recommended_outcome", "action_literal")) {
            assertTrue(result.get(field).isNull(), field);
        }
        assertFalse(result.get("siege").get("completion_upper_bound_proven").booleanValue());
        assertFalse(result.get("contact").get("offsite_roster_complete_proven").booleanValue());
    }
    private static void rejected(ObjectNode node) {
        assertThrows(ContractViolationException.class, () -> DefenderContinueRiskCodec.decode(bytes(node)));
    }
    private static void rejectedRawField(ObjectNode request, ObjectNode owner, String field, String rawToken) {
        // Construct the actual wire token: serializing DecimalNode(BigDecimal.ONE) would test integer 1.
        String marker = "\"$defenderrisk-exact-raw-token$\"";
        owner.put(field, "$defenderrisk-exact-raw-token$");
        String encoded = request.toString();
        assertTrue(encoded.contains(marker));
        byte[] raw = encoded.replace(marker, rawToken).getBytes(StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> DefenderContinueRiskCodec.decode(raw), rawToken);
    }
    private static byte[] bytes(JsonNode node) { return node.toString().getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode input(int index) throws IOException {
        return (ObjectNode) StrictJson.parse(resource()).get("cases").get(index).get("request").deepCopy();
    }
    private static byte[] resource() throws IOException {
        try (InputStream stream = DefenderContinueRiskTest.class.getResourceAsStream("/defenderrisk/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed producer golden missing"); }
            return stream.readAllBytes();
        }
    }
}
