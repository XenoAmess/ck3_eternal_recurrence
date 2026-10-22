package org.xar.ck3.control.finance.jointbudget;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.AssessedInput;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.MissingAssessments;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Result;

final class JointBudgetSelectorTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void matchesOriginalProductionProducerGoldenIncludingRejections() throws IOException {
        JsonNode fixture = fixture();
        assertEquals("xar.ck3.java-jointbudget.legacy-producer-golden.v1", fixture.path("schema").textValue());
        assertEquals(18, fixture.path("cases").size());
        int accepted = 0; int rejected = 0;
        for (JsonNode scenario : fixture.path("cases")) {
            byte[] input = JSON.writeValueAsBytes(scenario.get("input"));
            if (scenario.has("expected")) {
                JsonNode actual = StrictJson.parse(JointBudgetCodec.select(input));
                assertEquals(scenario.get("expected"), actual, scenario.path("name").textValue());
                accepted++;
            } else {
                assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(input), scenario.path("name").textValue());
                rejected++;
            }
        }
        assertEquals(13, accepted); assertEquals(5, rejected);
    }

    @Test void oneChoiceCannotSpendBothAlternativesAndLaterCommitmentsReduceBudget() throws IOException {
        ObjectNode input = baseline();
        ArrayNode assessments = (ArrayNode) input.get("assessments");
        for (int index = 0; index < assessments.size(); index++) {
            ObjectNode row = (ObjectNode) assessments.get(index);
            row.put("benefit_units", index < 2 ? 100 : 1);
            row.put("gold_raw", index < 2 ? 5_000_000 : 0);
        }
        Result selected = JointBudgetSelector.select(JointBudgetCodec.decode(JSON.writeValueAsBytes(input)));
        assertNotNull(selected.selectedCandidateId());
        assertEquals(2, selected.evaluated().stream().filter(row -> row.reason() == JointBudgetSelector.Reason.ELIGIBLE).count());
        assertFalse(selected.formalActionReady());
        ObjectNode published = (ObjectNode) StrictJson.parse(JointBudgetCodec.encode(selected));
        assertTrue(published.get("selected_step").isNull());
        // Reservation is still the original dispatcher's responsibility. Feed its increased commitment back explicitly.
        ((ObjectNode) input.get("commitments")).put("gold_raw", 6_000_000);
        JsonNode next = StrictJson.parse(JointBudgetCodec.select(JSON.writeValueAsBytes(input)));
        assertEquals("wait", next.get("status").textValue());
        assertTrue(next.get("selected_candidate_id").isNull());
        assertEquals("shared_gold_budget", next.get("evaluated").get(0).get("reason").textValue());
    }

    @Test void strictBoundaryRejectsWrongMissingAndUnknownFieldsWithoutCoercion() throws IOException {
        List<Consumer<ObjectNode>> mutations = List.of(
                root -> root.remove("max_active_wars"),
                root -> root.put("max_active_wars", true),
                root -> root.put("max_active_wars", 1.0),
                root -> root.put("max_active_wars", "1"),
                root -> root.putNull("gold_reserve_raw"),
                root -> root.put("unexpected", 1),
                root -> ((ObjectNode) root.get("commitments")).remove("gold_raw"),
                root -> ((ObjectNode) root.get("commitments")).putNull("pending_war_slots"),
                root -> ((ObjectNode) root.get("snapshot").get("played_character_gold")).put("scale", 100000.0),
                root -> ((ObjectNode) root.get("assessments").get(0)).remove("benefit_units"),
                root -> ((ObjectNode) root.get("assessments").get(0)).put("projected_supply_margin_units", false),
                root -> ((ObjectNode) root.get("snapshot").get("player_armies").get(0)).put("controllable", 1));
        for (Consumer<ObjectNode> mutation : mutations) {
            ObjectNode input = baseline(); mutation.accept(input);
            byte[] raw = JSON.writeValueAsBytes(input);
            assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw));
        }
    }

    @Test void duplicateKeysMalformedUtf8AndTrailingContentAreRejected() throws IOException {
        byte[] valid = JSON.writeValueAsBytes(baseline());
        String duplicate = new String(valid, StandardCharsets.UTF_8).replaceFirst("\\{", "{\"max_active_wars\":1,");
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(new byte[] {(byte) 0xc3, (byte) 0x28}));
        String trailing = new String(valid, StandardCharsets.UTF_8) + " {}";
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(trailing.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void unknownAssessmentAndDuplicateNativeIdentitiesAreRejected() throws IOException {
        ObjectNode input = baseline();
        ((ObjectNode) input.get("assessments").get(0)).put("candidate_id", "not-in-intake");
        byte[] absent = JSON.writeValueAsBytes(input);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(absent));
        input = baseline();
        ((ArrayNode) input.get("snapshot").get("active_wars")).addObject().put("war_id", 1);
        ((ArrayNode) input.get("snapshot").get("active_wars")).addObject().put("war_id", 1);
        byte[] duplicate = JSON.writeValueAsBytes(input);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(duplicate));
    }

    @Test void missingAssessmentBranchDoesNotInventTreasuryOrZeroUtility() throws IOException {
        ObjectNode input = baseline();
        ((ArrayNode) input.get("assessments")).removeAll();
        ((ObjectNode) input.get("snapshot")).remove("played_character_gold");
        input.putNull("gold_reserve_raw");
        JointBudgetSelector.Input decoded = JointBudgetCodec.decode(JSON.writeValueAsBytes(input));
        assertTrue(decoded instanceof MissingAssessments);
        Result result = JointBudgetSelector.select(decoded);
        assertEquals(JointBudgetSelector.Status.MISSING_ASSESSMENTS, result.status());
        assertNull(result.selectedCandidateId()); assertTrue(result.evaluated().isEmpty());
        assertEquals(6, result.unassessedLegalCandidateCount());
    }

    @Test void serializationRoundTripPreservesExactIntegerDomainAndNullNoAction() throws IOException {
        for (JsonNode scenario : fixture().path("cases")) {
            if (!scenario.has("expected")) { continue; }
            byte[] request = JSON.writeValueAsBytes(scenario.get("input"));
            byte[] response = JointBudgetCodec.select(request);
            assertArrayEquals(response, StrictJson.canonical(StrictJson.parse(response)));
            byte[] requestRoundTrip = JSON.writeValueAsBytes(JSON.readTree(request));
            assertArrayEquals(response, JointBudgetCodec.select(requestRoundTrip));
            assertTrue(StrictJson.parse(response).get("selected_step").isNull());
        }
    }

    @Test void immutableDomainCollectionsAndPythonUnicodeTieOrderAreExplicit() throws IOException {
        AssessedInput input = (AssessedInput) JointBudgetCodec.decode(JSON.writeValueAsBytes(baseline()));
        assertThrows(UnsupportedOperationException.class, () -> input.assessments().clear());
        assertThrows(UnsupportedOperationException.class, () -> input.commitments().claims().armyIds().add(BigInteger.ZERO));
        assertTrue(JointBudgetSelector.comparePythonText("tie:\ue000", "tie:\ud800\udc00") < 0);
        assertEquals(0, JointBudgetSelector.comparePythonText("tie:a", "tie:a"));
    }

    @Test void observedProposalCannotChangeFrameOrClaimAfterDomainApproval() throws IOException {
        JsonNode scenario = null;
        for (JsonNode row : fixture().path("cases")) {
            if (row.path("name").asText().equals("actual-normalized-domain-proposal-minimum-reserve")) { scenario = row; }
        }
        assertNotNull(scenario);
        ObjectNode input = (ObjectNode) scenario.get("input").deepCopy();
        ObjectNode proposal = (ObjectNode) input.get("intake").get("candidates").get(6).get("observed_proposal");
        ((ObjectNode) proposal.get("frame")).put("episode_run_id", "different-episode");
        byte[] drift = JSON.writeValueAsBytes(input);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(drift));
        input = (ObjectNode) scenario.get("input").deepCopy();
        ((ObjectNode) input.get("assessments").get(6)).put("gold_raw", 0);
        byte[] claimDrift = JSON.writeValueAsBytes(input);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(claimDrift));
    }

    private static ObjectNode baseline() throws IOException { return (ObjectNode) fixture().get("cases").get(0).get("input").deepCopy(); }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = JointBudgetSelectorTest.class.getResourceAsStream("/jointbudget/legacy-producer-golden.json")) {
            if (stream == null) { throw new IOException("committed original-producer golden is required"); }
            return JSON.readTree(stream);
        }
    }
}
