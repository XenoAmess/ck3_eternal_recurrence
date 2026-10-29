package org.xar.ck3.control.wave3.governance.heirdiagnostic;

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
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.heirintake.HeirCandidateIntakeConsumerPort;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRankingConsumerPort;

final class HeirCandidateDiagnosticConsumerPortTest {
    private static final int PRODUCER_COLLECTION_MAX_BYTES = 98_304;
    private static final int DOWNSTREAM_COLLECTION_MAX_BYTES = 65_536;

    @Test
    void actualHelperThreePlanConsumersAndOriginalPrewriteConsumerAreClosed() throws IOException {
        JsonNode golden = golden();
        assertEquals(3, golden.path("cases").size());
        assertEquals("c6d55a12b4450909641dbffe5b12e900878f29cde406aadd4a6d185bd78039b0",
                golden.path("sources").get(0).path("sha256").textValue());
        int boundaries = 0;
        for (JsonNode vector : golden.path("cases")) {
            byte[] request = StrictJson.canonical(vector.path("input"));
            byte[] before = request.clone();
            var actual = HeirCandidateDiagnosticConsumerPort.evaluate(request);
            assertArrayEquals(StrictJson.canonical(vector.path("expected")), actual.diagnostic(), vector.path("name").textValue());
            assertArrayEquals(actual.diagnostic(), HeirCandidateDiagnosticConsumerPort.project(request));
            assertArrayEquals(actual.diagnostic(), StrictJson.canonical(StrictJson.parse(actual.diagnostic())));
            assertArrayEquals(before, request);
            assertTrue(vector.path("plan_consumer").path("diagnostic_matches").booleanValue());
            JsonNode consumer = vector.path("submit_consumer");
            assertEquals(0, consumer.path("native_submit_count").intValue());
            assertFalse(consumer.path("pending_written").booleanValue());
            if (consumer.path("stage").textValue().equals("stopped_before_first_write")) {
                boundaries++;
                assertEquals(1, consumer.path("write_callback_count").intValue());
                JsonNode projection = consumer.path("selected_value_projection");
                var selected = actual.observation().selectedProjection().orElseThrow();
                assertEquals(selected.projected().roles().candidate().orElseThrow(), projection.path("candidate_character_id").bigIntegerValue());
                assertEquals(actual.observation().header().nativeRevision(), projection.path("source_native_revision").bigIntegerValue());
                assertEquals(actual.observation().header().legalityQuerySequence(), projection.path("source_legality_query_sequence").bigIntegerValue());
                assertEquals(actual.observation().header().episode().orElseThrow(), projection.path("source_episode_run_id").textValue());
                assertEquals(actual.observation().header().date().orElseThrow(), projection.path("source_date_raw").bigIntegerValue());
                JsonNode diagnostic = StrictJson.parse(actual.diagnostic());
                JsonNode selectedJson = diagnostic.path("rows").get(selected.ordinal());
                for (String field : List.of("heir_dynasty_id", "candidate_dynasty_id", "candidate_native_fertility",
                        "candidate_native_scorer_age_branch_v1", "candidate_spouse_character_ids")) {
                    assertEquals(selectedJson.path(field), projection.path(field), field);
                }
                assertEquals("basis_only_unpriced", projection.path("child_dynasty_prediction_status").textValue());
                assertTrue(projection.path("predicted_child_dynasty_id").isNull());
            } else {
                assertEquals("unselected-no-submit", consumer.path("stage").textValue());
                assertTrue(actual.observation().selectedProjection().isEmpty());
            }
        }
        assertEquals(2, boundaries, "pre-write boundaries are not actual submissions or ledger completion");
        JsonNode refusals = golden.path("cases").get(0).path("submit_drift_rejections");
        assertEquals(9, refusals.size());
        for (JsonNode refusal : refusals) {
            assertEquals("rejected_before_write", refusal.path("stage").textValue());
            assertEquals(0, refusal.path("write_callback_count").intValue());
            assertEquals(0, refusal.path("native_submit_count").intValue());
        }
        assertFalse(golden.path("native_source_qualification").booleanValue());
    }

    @Test
    void actualProposalTurnCompactorAndNoopConsumersRetainTheirOwnFrameGuards() throws IOException {
        byte[] producerBytes = requiredResource("/heirdiagnostic/producer-golden.json", PRODUCER_COLLECTION_MAX_BYTES);
        JsonNode producer = StrictJson.parse(producerBytes, PRODUCER_COLLECTION_MAX_BYTES);
        JsonNode receipt = StrictJson.parse(requiredResource("/heirdiagnostic/consumer-golden.json", 65_536), 65_536);
        assertEquals("xar.ck3.heir-diagnostic.actual-java-downstream-consumers.v3", receipt.path("schema").textValue());
        assertEquals(sha256(producerBytes), StrictJson.text(receipt.get("input_sha256")), "exact original bytes, including newline");
        for (String field : List.of("same_root_bootstrap_session", "actual_shared_http")) {
            assertTrue(receipt.path(field).isBoolean()); assertTrue(receipt.path(field).booleanValue());
        }
        assertEquals(3, receipt.path("producer_input_refs").size());
        assertEquals(2, receipt.path("java_consumer_regressions").size());
        assertEquals(List.of("test_family_marriage_formal_consumer", "test_m5_peacetime_proposal_sources_v1"),
                java.util.stream.StreamSupport.stream(receipt.path("java_consumer_regressions").spliterator(), false)
                        .map(value -> StrictJson.text(value.get("module"))).toList());
        for (JsonNode regression : receipt.path("java_consumer_regressions")) {
            long discovered = StrictJson.integer(regression.get("discovered"), 1, Integer.MAX_VALUE);
            assertEquals(discovered, StrictJson.integer(regression.get("run"), 1, Integer.MAX_VALUE));
            for (String field : List.of("failures", "errors", "skipped")) {
                assertEquals(0, StrictJson.integer(regression.get(field), 0, Integer.MAX_VALUE));
            }
        }
        long exchanges = 0;
        for (String operation : List.of("governance-heir-rank", "governance-heir-intake", "governance-heir-diagnostic")) {
            exchanges += StrictJson.integer(receipt.path("java_operation_counts").get(operation), 1, Integer.MAX_VALUE);
        }
        assertEquals(3, receipt.path("java_operation_counts").size());
        assertEquals(exchanges, StrictJson.integer(receipt.get("java_exchange_count"), 1, Integer.MAX_VALUE));
        assertTrue(StrictJson.text(receipt.get("java_transport_sha256")).matches("[0-9a-f]{64}"));
        assertEquals(3, receipt.path("cases").size());
        boolean[] seen = new boolean[3]; int selected = 0;
        for (JsonNode consumer : receipt.path("cases")) {
            int index = Math.toIntExact(StrictJson.integer(consumer.get("producer_case"), 0, 2));
            assertFalse(seen[index]); seen[index] = true;
            JsonNode source = producer.path("cases").get(index);
            assertEquals(source.path("name"), consumer.path("name"));
            assertEquals(sha256(StrictJson.canonical(source.path("input"))), consumer.path("input_sha256").textValue());
            byte[] actual = HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(source.path("input")));
            assertEquals(sha256(actual), consumer.path("java_diagnostic_sha256").textValue());
            for (String field : List.of("turn_compactor_preserved_all_fields", "turn_record_preserved_all_fields", "original_plan_consumers_exact")) {
                assertTrue(consumer.path(field).isBoolean()); assertTrue(consumer.path(field).booleanValue());
            }
            if (!source.path("input").path("choice").isNull()) {
                selected++;
                assertTrue(consumer.path("proposal").isObject());
                assertEquals("stopped_before_first_write", consumer.path("submit_prewrite_consumer").path("stage").textValue());
                assertEquals(1, consumer.path("submit_prewrite_consumer").path("write_callbacks").intValue());
                assertEquals(4, consumer.path("proposal_drift_rejections").size());
            } else {
                assertEquals("unselected-no-submit", consumer.path("submit_prewrite_consumer").path("stage").textValue());
                assertTrue(consumer.path("complete_noop").path("empty_reason_row_rejected").booleanValue());
            }
        }
        assertEquals(2, selected);
        for (boolean present : seen) { assertTrue(present); }
        byte[] rankingBytes = requiredResource("/heirranking/producer-golden.json", PRODUCER_COLLECTION_MAX_BYTES);
        byte[] intakeBytes = requiredResource("/heirintake/producer-golden.json", PRODUCER_COLLECTION_MAX_BYTES);
        assertEquals(sha256(rankingBytes), receipt.path("ranking_input_sha256").textValue());
        assertEquals(sha256(intakeBytes), receipt.path("intake_input_sha256").textValue());
        JsonNode ranking = StrictJson.parse(rankingBytes, PRODUCER_COLLECTION_MAX_BYTES);
        JsonNode intake = StrictJson.parse(intakeBytes, PRODUCER_COLLECTION_MAX_BYTES);
        assertEquals(7, receipt.path("ranking_cases").size());
        assertEquals(7, receipt.path("intake_cases").size());
        for (int index = 0; index < 7; index++) {
            JsonNode rank = ranking.path("cases").get(index);
            JsonNode ranked = receipt.path("ranking_cases").get(index);
            assertEquals(rank.path("name"), ranked.path("name"));
            assertEquals(sha256(StrictJson.canonical(rank.path("input"))), ranked.path("input_sha256").textValue());
            assertEquals(sha256(StrictJson.canonical(rank.path("expected_choices"))), ranked.path("java_choices_sha256").textValue());
            assertTrue(ranked.path("choice_consumer_equal").booleanValue());
            JsonNode pool = intake.path("cases").get(index);
            JsonNode consumed = receipt.path("intake_cases").get(index);
            assertEquals(pool.path("name"), consumed.path("name"));
            assertEquals(sha256(StrictJson.canonical(pool.path("input"))), consumed.path("input_sha256").textValue());
            assertEquals(sha256(StrictJson.canonical(pool.path("expected"))), consumed.path("java_result_sha256").textValue());
            assertEquals(pool.path("consumer_executed"), consumed.path("source_plan_consumer_executed"));
            if (pool.path("consumer_executed").booleanValue()) {
                assertEquals(pool.path("consumer").path("rich_requests"), consumed.path("plan_consumer").path("rich_requests"));
            } else {
                assertEquals("pure_producer_only_refusal_history_not_ledger_adoption", consumed.path("plan_consumer").path("scope").textValue());
            }
        }
        assertTrue(receipt.path("production_ledger_written").isBoolean());
        assertFalse(receipt.path("production_ledger_written").booleanValue());
        assertTrue(receipt.path("game_or_rpc").isBoolean()); assertFalse(receipt.path("game_or_rpc").booleanValue());
    }

    @Test
    void sharedProjectionTransportRejectsLegacyCaptureAndWrongVersionOrUnknownOperationBeforeDispatch() {
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("heir-consumer-transport",
                ProjectionOperation.GOVERNANCE_HEIR_DIAGNOSTIC),
                ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), ProjectionJson.MAX_BYTES));
        byte[] valid = ProjectionWire.encodeCall(call);
        assertEquals(call.identity(), ProjectionWire.decodeCall(valid).identity());
        String envelope = new String(valid, StandardCharsets.UTF_8);
        for (String version : List.of("true", "1.0", "\"1\"", "0", "2")) {
            byte[] malformed = envelope.replace("\"schema_version\":1", "\"schema_version\":" + version)
                    .getBytes(StandardCharsets.UTF_8);
            assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeCall(malformed), version);
        }
        byte[] unknown = envelope.replace(ProjectionOperation.GOVERNANCE_HEIR_DIAGNOSTIC.wire(), "python-fallback")
                .getBytes(StandardCharsets.UTF_8);
        assertThrows(ProjectionProtocolException.class, () -> ProjectionWire.decodeCall(unknown));
        for (String sequence : List.of("true", "1.0", "\"1\"", "0", "1", "2")) {
            String retired = "{\"schema\":\"xar.ck3.heir-java-consumer-capture-request.v1\",\"sequence\":"
                    + sequence + ",\"operation\":\"RANK\",\"input\":{}}\n";
            assertThrows(ProjectionProtocolException.class,
                    () -> ProjectionWire.decodeCall(retired.getBytes(StandardCharsets.UTF_8)), sequence);
        }
    }

    @Test
    void optionalMissingNativeFactsStayNullAndNoFertilityIsInferred() throws IOException {
        JsonNode result = StrictJson.parse(HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(input(0))));
        assertTrue(result.path("rows").get(0).path("candidate_native_fertility").isNull());
        assertTrue(result.path("rows").get(0).path("candidate_spouse_character_ids").isNull());
        assertEquals(0, result.path("rows").get(0).path("heir_spouse_count").intValue());
        assertTrue(result.path("read_only").booleanValue());
        assertFalse(result.path("advertised").booleanValue());
        assertFalse(result.has("qualified"));
        assertFalse(result.has("material_result"));
        assertFalse(result.has("native_source_proof"));
    }

    @Test
    void nativeSignedUnknownFactsAndPairSubsetArePreservedWithoutChangingPolicy() throws IOException {
        JsonNode result = StrictJson.parse(HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(input(1))));
        JsonNode row = result.path("rows").get(1);
        assertEquals(-1, row.path("candidate_native_fertility").path("effective_raw").intValue());
        assertTrue(row.path("candidate_native_fertility_floor_comparison_v1").path("passes").isNull());
        assertEquals(-1, row.path("candidate_native_scorer_age_override_raw").intValue());
        assertFalse(row.path("possible_alliance_pairs").get(0).has("sdk_extension_omitted_by_diagnostic"));
        assertEquals(5, row.path("possible_alliance_pairs").get(0).size());
        assertTrue(row.path("candidate_spouse_character_ids").isEmpty());
    }

    @Test
    void unknownSpouseCollectionAndKnownEmptyAreDifferentAndUnselectedRemainsNull() throws IOException {
        JsonNode unknown = StrictJson.parse(HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(input(2))));
        assertTrue(unknown.path("rows").get(0).path("heir_spouse_count").isNull());
        assertTrue(unknown.path("selected_candidate_character_id").isNull());
        assertFalse(unknown.path("rows").get(0).path("rejection_reasons").isEmpty());
        ObjectNode explicit = input(0);
        row(explicit, 0).putNull("heir_spouse_character_ids");
        JsonNode nullResult = StrictJson.parse(HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(explicit)));
        assertTrue(nullResult.path("rows").get(0).path("heir_spouse_count").isNull());
    }

    @Test
    void exactMetadataAndLargeIdentitiesAreRetainedRatherThanRoundedOrRequalified() throws IOException {
        ObjectNode request = input(0);
        BigInteger exact = new BigInteger("9007199254740993");
        ((ObjectNode) request.path("choice")).put("candidate_character_id", exact);
        row(request, 0).put("candidate_character_id", exact);
        ((ObjectNode) request.path("legality").path("native_legal_candidates").get(0)).put("candidate_character_id", exact);
        ((ObjectNode) request.path("snapshot")).put("episode_run_id", "exact-other-episode");
        var result = HeirCandidateDiagnosticConsumerPort.evaluate(StrictJson.canonical(request));
        assertEquals(exact, result.observation().header().selectedCandidate().orElseThrow());
        assertEquals(exact, StrictJson.parse(result.diagnostic()).path("rows").get(0).path("candidate_character_id").bigIntegerValue());
        assertEquals("exact-other-episode", result.observation().header().episode().orElseThrow());
        assertFalse(StrictJson.parse(result.diagnostic()).has("qualified"));
    }

    @Test
    void requiredNativeFieldsAndOptionalObservationsRejectWrongTokenTypes() throws IOException {
        String request = new String(StrictJson.canonical(input(1)), StandardCharsets.UTF_8);
        for (String wrong : List.of("true", "300.0", "3e2", "\"300\"", "null")) {
            reject(request.replace("\"candidate_character_id\":300", "\"candidate_character_id\":" + wrong));
        }
        reject(request.replace("\"native_revision\":7", "\"native_revision\":7.0"));
        reject(request.replace("\"candidate_is_adult\":true", "\"candidate_is_adult\":1"));
        reject(request.replace("\"effective_raw\":15000", "\"effective_raw\":true"));
        reject(request.replace("\"ready\":true", "\"ready\":1"));
        reject(request.replace("\"date_raw\":53215920", "\"date_raw\":\"53215920\""));
        reject(request.replace("\"candidate_spouse_character_ids\":[]", "\"candidate_spouse_character_ids\":[true]"));
    }

    @Test
    void exactRequestShapeMissingFieldsPairsAndFiveRowBoundaryRejectMalformedInputs() throws IOException {
        ObjectNode extra = input(0); extra.put("qualified", true);
        rejectNode(extra);
        ObjectNode missing = input(0); missing.remove("choice"); rejectNode(missing);
        ObjectNode shortRows = input(0); ((ArrayNode) shortRows.path("projection").path("rows")).remove(4); rejectNode(shortRows);
        ObjectNode absentId = input(0); row(absentId, 0).remove("candidate_character_id"); rejectNode(absentId);
        ObjectNode badPair = input(1);
        ((ObjectNode) row(badPair, 0).path("possible_alliance_pairs").get(0)).remove("would_attempt_if_accepted");
        rejectNode(badPair);
        ObjectNode duplicateRefusals = input(0); duplicateRefusals.putArray("rejected_candidate_ids").add(300).add(300);
        rejectNode(duplicateRefusals);
        reject("{\"legality\":{},\"legality\":{}}");
        assertThrows(ContractViolationException.class, () -> HeirCandidateDiagnosticConsumerPort.project(new byte[65537]));
        assertThrows(ContractViolationException.class, () -> HeirCandidateDiagnosticConsumerPort.project(new byte[] {(byte) 0xc3, 0x28}));
    }

    @Test
    void finalDuplicateLegalRowAndMissingLegalMatchUseTheSingleRankingRejectionPolicy() throws IOException {
        ObjectNode duplicate = input(0);
        ArrayNode legal = (ArrayNode) duplicate.path("legality").path("native_legal_candidates");
        ObjectNode last = ((ObjectNode) legal.get(0)).deepCopy(); last.put("recipient_ai_accept_raw", -1); legal.add(last);
        JsonNode result = StrictJson.parse(HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(duplicate)));
        assertEquals(6, result.path("final_legal_candidate_count").intValue());
        assertEquals(-1, result.path("rows").get(0).path("recipient_ai_accept_raw").intValue());
        assertTrue(result.path("rows").get(0).path("rejection_reasons").toString().contains("recipient_accept_not_positive"));
        ObjectNode absent = input(0);
        ((ArrayNode) absent.path("legality").path("native_legal_candidates")).remove(0);
        JsonNode missing = StrictJson.parse(HeirCandidateDiagnosticConsumerPort.project(StrictJson.canonical(absent)));
        assertTrue(missing.path("rows").get(0).path("recipient_ai_accept_raw").isNull());
        assertFalse(missing.path("rows").get(0).path("rejection_reasons").isEmpty());
    }

    @Test
    void typedObservationAndSerializedResultAreImmutable() throws IOException {
        var actual = HeirCandidateDiagnosticConsumerPort.evaluate(StrictJson.canonical(input(0)));
        byte[] original = actual.diagnostic(); byte[] changed = actual.diagnostic(); changed[0] = 0;
        assertArrayEquals(original, actual.diagnostic());
        assertThrows(UnsupportedOperationException.class, actual.observation().rows()::clear);
        assertThrows(UnsupportedOperationException.class, actual.observation().rows().get(0).rejectionReasons()::clear);
        assertThrows(IllegalArgumentException.class, () -> new HeirCandidateDiagnostic.Observation(actual.observation().header(), List.of()));
    }

    private static ObjectNode row(ObjectNode request, int index) { return (ObjectNode) request.path("projection").path("rows").get(index); }
    private static ObjectNode input(int index) throws IOException { return (ObjectNode) golden().path("cases").get(index).path("input").deepCopy(); }
    private static JsonNode golden() throws IOException {
        return StrictJson.parse(requiredResource("/heirdiagnostic/producer-golden.json", PRODUCER_COLLECTION_MAX_BYTES),
                PRODUCER_COLLECTION_MAX_BYTES);
    }
    private static byte[] requiredResource(String path, int maximumBytes) throws IOException {
        try (InputStream input = HeirCandidateDiagnosticConsumerPortTest.class.getResourceAsStream(path)) {
            if (input == null) { throw new IOException("committed actual golden required; no skip or Python fallback: " + path); }
            byte[] raw = input.readNBytes(maximumBytes + 1);
            if (raw.length > maximumBytes) { throw new IOException("actual golden exceeds its collection budget: " + path); }
            return raw;
        }
    }
    private static String sha256(byte[] raw) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("required SHA-256 algorithm unavailable", impossible);
        }
    }
    private static void rejectNode(ObjectNode input) { reject(new String(StrictJson.canonical(input), StandardCharsets.UTF_8)); }
    private static void reject(String input) {
        assertThrows(ContractViolationException.class, () -> HeirCandidateDiagnosticConsumerPort.project(input.getBytes(StandardCharsets.UTF_8)));
    }
}
