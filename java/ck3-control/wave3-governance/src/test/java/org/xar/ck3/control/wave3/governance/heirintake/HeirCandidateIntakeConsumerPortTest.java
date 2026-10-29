package org.xar.ck3.control.wave3.governance.heirintake;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
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
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class HeirCandidateIntakeConsumerPortTest {
    @Test
    void actualProducerGoldenAndFiveOriginalPlanningConsumersMatchNextRichRequests() throws IOException {
        JsonNode golden = golden();
        assertEquals(7, golden.path("cases").size());
        assertEquals("c6d55a12b4450909641dbffe5b12e900878f29cde406aadd4a6d185bd78039b0",
                golden.path("sources").get(0).path("sha256").textValue());
        int actualConsumers = 0;
        for (JsonNode vector : golden.path("cases")) {
            byte[] input = StrictJson.canonical(vector.path("input"));
            byte[] before = input.clone();
            var actual = HeirCandidateIntakeConsumerPort.evaluate(input);
            assertArrayEquals(StrictJson.canonical(vector.path("expected")), actual.result(), vector.path("name").textValue());
            assertArrayEquals(actual.result(), StrictJson.canonical(StrictJson.parse(actual.result())));
            assertArrayEquals(actual.result(), HeirCandidateIntakeConsumerPort.consume(input));
            if (vector.path("consumer_executed").booleanValue()) {
                actualConsumers++;
                JsonNode consumer = vector.path("consumer");
                JsonNode richRequests = consumer.path("rich_requests");
                if (richRequests.isEmpty()) {
                    assertTrue(actual.nextRichCandidateIds().isEmpty());
                    assertEquals("fewer_than_five_projectable_legal_candidates", consumer.path("family_marriage_status").textValue());
                } else {
                    assertEquals(1, richRequests.size());
                    assertEquals(integers(richRequests.get(0).path("candidate_character_ids")),
                            actual.nextRichCandidateIds().orElseThrow());
                    assertArrayEquals(StrictJson.canonical(consumer.path("ranking")),
                            StrictJson.canonical(StrictJson.parse(actual.result()).path("ranking")));
                }
                assertFalse(consumer.path("calls").toString().contains("submit"));
                assertFalse(consumer.path("game_action").booleanValue());
            }
            assertArrayEquals(before, input);
        }
        assertEquals(5, actualConsumers, "two refusal-only cases are not claimed as ledger consumer qualification");
    }

    @Test
    void c9LowerAcceptanceExternalPeersReallyPrecedeTheOldAcceptanceTopFive() throws IOException {
        var actual = HeirCandidateIntakeConsumerPort.evaluate(StrictJson.canonical(input(0)));
        assertEquals(List.of(BigInteger.valueOf(306), BigInteger.valueOf(305)),
                actual.nextRichCandidateIds().orElseThrow().subList(0, 2));
        JsonNode ranking = StrictJson.parse(actual.result()).path("ranking");
        assertEquals(2, ranking.path("prefilter_eligible_count").intValue());
        assertEquals(0, ranking.path("value_input_unavailable_count").intValue());
    }

    @Test
    void compactMinusOneAndNullStayKnownAbsentAndUnknownSeparately() throws IOException {
        JsonNode ranking = StrictJson.parse(HeirCandidateIntakeConsumerPort.consume(StrictJson.canonical(input(1)))).path("ranking");
        assertEquals(1, ranking.path("candidate_dynasty_absent_count").intValue());
        assertEquals(1, ranking.path("value_input_unavailable_count").intValue());
        assertEquals(2, ranking.path("prefilter_eligible_count").intValue());
    }

    @Test
    void noPeerAndAllUnknownRetainFreshFallbackWithDifferentConclusions() throws IOException {
        var noPeer = HeirCandidateIntakeConsumerPort.evaluate(StrictJson.canonical(input(2)));
        var unknown = HeirCandidateIntakeConsumerPort.evaluate(StrictJson.canonical(input(3)));
        assertEquals(noPeer.nextRichCandidateIds(), unknown.nextRichCandidateIds());
        assertEquals("no_age_matched_external_realm_candidate", StrictJson.parse(noPeer.result()).path("ranking").path("conclusion").textValue());
        assertEquals("unobserved_value_inputs_remain", StrictJson.parse(unknown.result()).path("ranking").path("conclusion").textValue());
        assertEquals(7, StrictJson.parse(unknown.result()).path("ranking").path("value_input_unavailable_count").intValue());
    }

    @Test
    void refusalFallbackIsRetainedForFiveRowDiagnosticsWithoutBecomingASelectedAction() throws IOException {
        var actual = HeirCandidateIntakeConsumerPort.evaluate(StrictJson.canonical(input(4)));
        assertEquals(List.of(306, 305, 300, 301, 302).stream().map(BigInteger::valueOf).toList(),
                actual.nextRichCandidateIds().orElseThrow());
        JsonNode result = StrictJson.parse(actual.result());
        assertEquals(2, result.path("ranking").path("prefilter_eligible_count").intValue());
        assertFalse(result.has("choice"));
        assertFalse(result.has("material_result"));
        assertFalse(result.has("qualified"));
    }

    @Test
    void fewerThanFiveAndKnownEmptyInputsDoNotProposeANativeRead() throws IOException {
        assertTrue(HeirCandidateIntakeConsumerPort.evaluate(StrictJson.canonical(input(5))).nextRichCandidateIds().isEmpty());
        var empty = HeirCandidateIntakeConsumerPort.evaluate("{\"legal_rows\":[],\"rejected_candidate_ids\":[]}".getBytes(StandardCharsets.UTF_8));
        assertTrue(empty.nextRichCandidateIds().isEmpty());
        assertEquals(0, StrictJson.parse(empty.result()).path("ranking").path("projected_count").intValue());
    }

    @Test
    void exactRawNativeIntegerAndBooleanFieldsRejectCoercion() throws IOException {
        String original = new String(StrictJson.canonical(input(0)), StandardCharsets.UTF_8);
        for (String wrong : List.of("true", "300.0", "3e2", "\"300\"", "null")) {
            rejected(original.replace("\"candidate_character_id\":300", "\"candidate_character_id\":" + wrong));
        }
        rejected(original.replace("\"recipient_ai_accept_raw\":500", "\"recipient_ai_accept_raw\":500.0"));
        rejected(original.replace("\"heir_adult_measure_raw\":6", "\"heir_adult_measure_raw\":true"));
        rejected(original.replace("\"realm_backed_actor_recipient\":true", "\"realm_backed_actor_recipient\":1"));
    }

    @Test
    void exactWrapperRefusalIdentitySetAndRequiredAcceptanceRejectMalformedInputs() throws IOException {
        ObjectNode wrong = input(0);
        wrong.put("qualified", true);
        assertThrows(ContractViolationException.class, () -> HeirCandidateIntakeConsumerPort.consume(StrictJson.canonical(wrong)));
        ObjectNode missing = input(0);
        ((ObjectNode) missing.path("legal_rows").get(0)).remove("recipient_ai_accept_raw");
        assertThrows(IllegalArgumentException.class, () -> HeirCandidateIntakeConsumerPort.consume(StrictJson.canonical(missing)));
        ObjectNode duplicate = input(0);
        ArrayNode refused = duplicate.putArray("rejected_candidate_ids");
        refused.add(300).add(300);
        assertThrows(ContractViolationException.class, () -> HeirCandidateIntakeConsumerPort.consume(StrictJson.canonical(duplicate)));
        rejected("{\"legal_rows\":[],\"legal_rows\":[],\"rejected_candidate_ids\":[]}");
        assertThrows(ContractViolationException.class, () -> HeirCandidateIntakeConsumerPort.consume(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(ContractViolationException.class, () -> HeirCandidateIntakeConsumerPort.consume(new byte[65537]));
    }

    @Test
    void resultAndProposedReadListAreDefensiveAndImmutable() throws IOException {
        var result = HeirCandidateIntakeConsumerPort.evaluate(StrictJson.canonical(input(0)));
        byte[] before = result.result();
        byte[] changed = result.result();
        changed[0] = 0;
        assertArrayEquals(before, result.result());
        assertThrows(UnsupportedOperationException.class, result.nextRichCandidateIds().orElseThrow()::clear);
    }

    @Test
    void typedStatisticsCannotClaimMoreThanFiveProjectedCandidates() {
        assertThrows(IllegalArgumentException.class, () -> new HeirCandidateIntake.Statistics(0, 0, 0, 6,
                HeirCandidateIntake.Conclusion.BOUNDED_FIVE_ROW_PROJECTION));
        assertThrows(IllegalArgumentException.class, () -> new HeirCandidateIntake.Intake(List.of(),
                new HeirCandidateIntake.Statistics(0, 0, 0, 1, HeirCandidateIntake.Conclusion.UNOBSERVED_VALUE_INPUTS_REMAIN)));
    }

    private static List<BigInteger> integers(JsonNode values) {
        List<BigInteger> result = new ArrayList<>();
        values.forEach(value -> result.add(value.bigIntegerValue()));
        return List.copyOf(result);
    }
    private static ObjectNode input(int index) throws IOException { return (ObjectNode) golden().path("cases").get(index).path("input").deepCopy(); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = HeirCandidateIntakeConsumerPortTest.class.getResourceAsStream("/heirintake/producer-golden.json")) {
            if (input == null) { throw new IOException("committed actual producer/consumer golden required; no skip or Python fallback"); }
            return StrictJson.parse(input.readAllBytes());
        }
    }
    private static void rejected(String input) {
        assertThrows(ContractViolationException.class, () -> HeirCandidateIntakeConsumerPort.consume(input.getBytes(StandardCharsets.UTF_8)));
    }
}
