package org.xar.ck3.control.wave3.governance.heirranking;

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

final class HeirCandidateRankingConsumerPortTest {
    @Test
    void actualRankingAndDiagnosticProducersMatchSevenCommittedVectors() throws IOException {
        JsonNode vectors = golden();
        assertEquals(7, vectors.path("cases").size());
        assertEquals("c6d55a12b4450909641dbffe5b12e900878f29cde406aadd4a6d185bd78039b0",
                vectors.path("sources").get(0).path("sha256").textValue());
        for (JsonNode vector : vectors.path("cases")) {
            byte[] input = StrictJson.canonical(vector.path("input"));
            byte[] before = input.clone();
            var actual = HeirCandidateRankingConsumerPort.evaluate(input);
            assertArrayEquals(StrictJson.canonical(vector.path("expected_choices")), actual.choices(), vector.path("name").textValue());
            assertArrayEquals(StrictJson.canonical(vector.path("expected_rejections")), actual.rejectionReasons(), vector.path("name").textValue());
            assertArrayEquals(actual.choices(), HeirCandidateRankingConsumerPort.rank(input));
            assertArrayEquals(actual.rejectionReasons(), HeirCandidateRankingConsumerPort.diagnose(input));
            assertArrayEquals(actual.choices(), StrictJson.canonical(StrictJson.parse(actual.choices())));
            assertArrayEquals(before, input);
        }
    }

    @Test
    void adultOrderUsesAgeGapBeforeAcceptanceThenExactCandidateIdentity() throws IOException {
        JsonNode result = StrictJson.parse(HeirCandidateRankingConsumerPort.rank(StrictJson.canonical(input(1))));
        List<BigInteger> ids = new ArrayList<>();
        result.forEach(choice -> ids.add(choice.path("candidate_character_id").bigIntegerValue()));
        assertEquals(List.of(301, 304, 302, 300, 303).stream().map(BigInteger::valueOf).toList(), ids);
        result.forEach(choice -> assertEquals("unpartnered_first_heir_adult_marriage_opportunity", choice.path("value").textValue()));
    }

    @Test
    void rawIntegerAndBooleanTokensAreNotCoercedOrNormalizedBeforeValidation() throws IOException {
        String original = new String(StrictJson.canonical(input(0)), StandardCharsets.UTF_8);
        for (String raw : List.of("true", "300.0", "3e2", "\"300\"")) {
            String changed = original.replace("\"candidate_character_id\":300", "\"candidate_character_id\":" + raw);
            rejected(changed);
        }
        for (String raw : List.of("0", "1", "1.0", "\"true\"")) {
            String changed = original.replace("\"complete_can_send\":true", "\"complete_can_send\":" + raw);
            rejected(changed);
        }
        rejected(original.replace("\"recipient_answer_status_raw\":0", "\"recipient_answer_status_raw\":false"));
        rejected(original.replace("\"recipient_ai_accept_raw\":500", "\"recipient_ai_accept_raw\":500.0"));
        rejected(original.replace("\"heir_sex_selector_raw\":0", "\"heir_sex_selector_raw\":false"));
    }

    @Test
    void unavailableOrMismatchedNativeSourcesDoNotProduceOpportunities() throws IOException {
        for (String field : List.of("unavailable", "revision", "sequence")) {
            ObjectNode input = input(0);
            ObjectNode projection = (ObjectNode) input.get("projection");
            switch (field) {
                case "unavailable" -> projection.put("status", "unavailable");
                case "revision" -> projection.put("native_revision", 8);
                case "sequence" -> projection.put("legality_query_sequence", 3);
                default -> throw new IllegalStateException("unexpected test branch");
            }
            var result = HeirCandidateRankingConsumerPort.evaluate(StrictJson.canonical(input));
            assertEquals(0, StrictJson.parse(result.choices()).size());
            assertEquals(0, StrictJson.parse(result.rejectionReasons()).size());
        }
    }

    @Test
    void observedEmptyCollectionsDifferFromMissingOrNullCollections() throws IOException {
        ObjectNode empty = input(2);
        ObjectNode row = (ObjectNode) empty.path("projection").path("rows").get(0);
        row.putArray("possible_alliance_pairs");
        JsonNode known = StrictJson.parse(HeirCandidateRankingConsumerPort.diagnose(StrictJson.canonical(empty)));
        assertFalse(known.get(0).path("rejection_reasons").toString().contains("betrothal_alliance_projection_unavailable"));
        row.putNull("possible_alliance_pairs");
        JsonNode unknown = StrictJson.parse(HeirCandidateRankingConsumerPort.diagnose(StrictJson.canonical(empty)));
        assertTrue(unknown.get(0).path("rejection_reasons").toString().contains("betrothal_alliance_projection_unavailable"));
        ObjectNode adult = input(0);
        ((ObjectNode) adult.path("projection").path("rows").get(0)).remove("heir_spouse_character_ids");
        assertTrue(new String(HeirCandidateRankingConsumerPort.diagnose(StrictJson.canonical(adult)), StandardCharsets.UTF_8)
                .contains("heir_spouse_list_not_empty"));
    }

    @Test
    void compactMinusOneMeansKnownAbsentAndUnknownRankedDynastyDoesNotInventAChange() throws IOException {
        ObjectNode input = input(4);
        ObjectNode row = (ObjectNode) input.path("projection").path("rows").get(0);
        row.put("candidate_dynasty_id", 999);
        JsonNode absent = StrictJson.parse(HeirCandidateRankingConsumerPort.diagnose(StrictJson.canonical(input)));
        assertTrue(absent.get(0).path("rejection_reasons").toString().contains("candidate_dynasty_changed_since_ranking"));
        ((ObjectNode) input.path("legality").path("native_legal_candidates").get(0)).putNull("candidate_dynasty_id");
        JsonNode unknown = StrictJson.parse(HeirCandidateRankingConsumerPort.diagnose(StrictJson.canonical(input)));
        assertFalse(unknown.get(0).path("rejection_reasons").toString().contains("candidate_dynasty_changed_since_ranking"));
    }

    @Test
    void minorAgeGapTwoRemainsAllowedAndThreeRemainsRejected() throws IOException {
        ObjectNode input = input(2);
        ObjectNode source = (ObjectNode) input.path("legality").path("native_legal_candidates").get(3);
        ObjectNode row = (ObjectNode) input.path("projection").path("rows").get(3);
        source.put("heir_dynasty_id", 20);
        JsonNode allowed = StrictJson.parse(HeirCandidateRankingConsumerPort.diagnose(StrictJson.canonical(input)));
        assertEquals(0, allowed.get(3).path("rejection_reasons").size());
        source.put("candidate_adult_measure_raw", 16);
        row.put("candidate_adult_measure_raw", 16);
        row.put("candidate_is_adult", true);
        JsonNode rejected = StrictJson.parse(HeirCandidateRankingConsumerPort.diagnose(StrictJson.canonical(input)));
        assertTrue(rejected.get(3).path("rejection_reasons").toString().contains("betrothal_age_gap_out_of_bounds"));
    }

    @Test
    void largePositiveIdentityAndUnpricedFutureResultsRemainExact() throws IOException {
        JsonNode result = StrictJson.parse(HeirCandidateRankingConsumerPort.rank(StrictJson.canonical(input(4))));
        BigInteger exact = new BigInteger("9007199254740993");
        boolean found = false;
        for (JsonNode choice : result) {
            if (choice.path("candidate_character_id").bigIntegerValue().equals(exact)) { found = true; }
            assertTrue(choice.path("unpriced").toString().contains("child_dynasty_result"));
            assertFalse(choice.has("material_result"));
            assertFalse(choice.has("native_rank"));
        }
        assertTrue(found);
    }

    @Test
    void defensiveOutputAndTypedResultInvariantsRejectInvalidPublicConstruction() throws IOException {
        var result = HeirCandidateRankingConsumerPort.evaluate(StrictJson.canonical(input(0)));
        byte[] expected = result.choices();
        byte[] changed = result.choices();
        changed[0] = 0;
        assertArrayEquals(expected, result.choices());
        assertThrows(IllegalArgumentException.class, () -> new HeirCandidateRanking.RankedChoice(BigInteger.ONE, 0,
                HeirCandidateRanking.Outcome.BETROTHAL, BigInteger.ONE, BigInteger.ZERO, false,
                HeirCandidateRanking.Value.ADULT_MARRIAGE));
    }

    @Test
    void exactWrapperIdentitySetAndBoundedJsonRejectMalformedInputs() throws IOException {
        ObjectNode extra = input(0);
        extra.put("qualified", true);
        assertThrows(ContractViolationException.class, () -> HeirCandidateRankingConsumerPort.rank(StrictJson.canonical(extra)));
        ObjectNode missing = input(0);
        missing.remove("projection");
        assertThrows(ContractViolationException.class, () -> HeirCandidateRankingConsumerPort.rank(StrictJson.canonical(missing)));
        ObjectNode missingIdentity = input(0);
        ((ObjectNode) missingIdentity.path("legality").path("native_legal_candidates").get(0)).remove("subject_character_id");
        assertThrows(ContractViolationException.class, () -> HeirCandidateRankingConsumerPort.rank(StrictJson.canonical(missingIdentity)));
        ObjectNode duplicates = input(0);
        ArrayNode refused = duplicates.putArray("rejected_candidate_ids");
        refused.add(300).add(300);
        assertThrows(ContractViolationException.class, () -> HeirCandidateRankingConsumerPort.rank(StrictJson.canonical(duplicates)));
        rejected("{\"legality\":{},\"legality\":{},\"projection\":{},\"rejected_candidate_ids\":[]}");
        assertThrows(ContractViolationException.class, () -> HeirCandidateRankingConsumerPort.rank(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(ContractViolationException.class, () -> HeirCandidateRankingConsumerPort.rank(new byte[65537]));
    }

    private static ObjectNode input(int index) throws IOException { return (ObjectNode) golden().path("cases").get(index).path("input").deepCopy(); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = HeirCandidateRankingConsumerPortTest.class.getResourceAsStream("/heirranking/producer-golden.json")) {
            if (input == null) { throw new IOException("committed actual producer golden required; no skip or Python fallback"); }
            return StrictJson.parse(input.readNBytes(98_305), 98_304);
        }
    }
    private static void rejected(String input) {
        assertThrows(ContractViolationException.class, () -> HeirCandidateRankingConsumerPort.rank(input.getBytes(StandardCharsets.UTF_8)));
    }
}
