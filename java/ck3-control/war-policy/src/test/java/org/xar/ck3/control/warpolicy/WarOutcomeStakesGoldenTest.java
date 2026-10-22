package org.xar.ck3.control.warpolicy;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.DoubleNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicContainer;
import org.junit.jupiter.api.DynamicNode;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Default CI uses committed frozen vectors, never untracked Python or live game IO. */
final class WarOutcomeStakesGoldenTest {
    private static final String RESOURCE = "/org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl";
    private static final int CORPUS_MAX_BYTES = 2 * 1024 * 1024;
    private static final Set<String> ORIGINAL_METHODS = Set.of(
        "test_actual_normalizer_cache_and_json_roundtrip_claim_defender",
        "test_political_profile_requires_observed_liege_and_retains_separate_exposure",
        "test_unknown_cb_and_unreviewed_side_do_not_gain_stakes",
        "test_stale_or_ambiguous_native_input_never_classifies",
        "test_native_legal_accepted_exit_is_not_complete_terms_or_actual_defeat",
        "test_sources_and_exact_build_are_required",
        "test_ids_sequences_and_revisions_reject_bool_float_and_strings",
        "test_wrong_missing_fields_and_source_pin_are_rejected",
        "test_missing_null_empty_and_detached_targets_are_preserved",
        "test_large_python_only_revision_survives_json_without_rounding",
        "test_current_observation_machine_is_separate_from_source_review_machine");
    private final WarOutcomeStakesProjector projector = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled());

    @TestFactory
    Stream<DynamicNode> originalElevenMethodLineagesAgainstFrozenOracleVectors() throws IOException {
        Corpus corpus = corpus();
        return ORIGINAL_METHODS.stream().sorted().map(method -> DynamicContainer.dynamicContainer(method,
            corpus.vectors().stream().filter(row -> method.equals(row.path("test_method").textValue()))
                .map(row -> DynamicTest.dynamicTest("captured call " + row.path("ordinal"), () -> {
                    byte[] input = StrictJson.text(row.get("input_json")).getBytes(StandardCharsets.UTF_8);
                    if ("invalid_contract".equals(row.path("expected_kind").textValue())) {
                        assertThrows(ContractViolationException.class, () -> projector.project(input));
                    } else {
                        byte[] actual = projector.project(input);
                        assertArrayEquals(StrictJson.canonical(row.get("expected")), actual);
                        JsonNode result = StrictJson.parse(actual);
                        checkNoEffectCredit(result);
                        assertEquals(result, StrictJson.parse(StrictJson.canonical(result)));
                    }
                }))));
    }

    @Test
    void frozenCorpusHasAllOriginalMethodsAndExactSourcePins() throws IOException {
        Corpus corpus = corpus();
        ObjectNode header = corpus.header();
        assertEquals("g2.war-outcome-stakes-golden/v1", header.path("schema").textValue());
        assertEquals("SOURCE_ONLY", header.path("service_decision_consumer_status").textValue());
        assertEquals(11, header.path("tests_run").intValue());
        assertEquals(0, header.path("skips").intValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue());
        assertEquals(ReviewedSourceRegistry.SHA256, header.path("registry_sha256").textValue());
        assertEquals(corpus.vectors().size(), header.path("vector_count").intValue());
        assertFalse(StrictJson.text(header.get("machine_id")).isEmpty());
        StrictJson.text(header.get("observed_at_utc"));
        ObjectNode pins = object(header, "source_sha256");
        assertEquals("e59b71b5479e98c0c225b36c45c91fda49403b3e1f897f59904d415b32256457",
            pins.path("tools/g2_saved_campaign/war_outcome_stakes_v1.py").textValue());
        assertEquals("0d55a99940be581981695906b693a74a84f4b9265971ae09494f3bb2c5f2fb76",
            pins.path("tools/g2_saved_campaign/test_war_outcome_stakes_v1.py").textValue());
        assertEquals(ReviewedSourceRegistry.SHA256,
            pins.path("tools/g2_saved_campaign/fixtures/war_outcome_stakes_source_v1.json").textValue());
        for (String name : List.of("war_contract.py", "native_driver.py", "version_identity.py")) {
            assertTrue(pins.path("ck3_autonomous_player/src/xar_autoplayer/bridge/" + name)
                .textValue().matches("[0-9a-f]{64}"));
        }
        Set<String> methods = new HashSet<>();
        header.path("test_methods").forEach(row -> assertTrue(methods.add(StrictJson.text(row))));
        assertEquals(ORIGINAL_METHODS, methods);
        Set<String> captured = new HashSet<>();
        int ordinal = 0;
        for (ObjectNode vector : corpus.vectors()) {
            assertEquals(++ordinal, vector.path("ordinal").intValue());
            captured.add(StrictJson.text(vector.get("test_method")));
            assertTrue(Set.of("result", "invalid_contract").contains(vector.path("expected_kind").textValue()));
            StrictJson.parse(StrictJson.text(vector.get("input_json")).getBytes(StandardCharsets.UTF_8));
        }
        assertEquals(ORIGINAL_METHODS, captured);
    }

    @Test
    void outerWireRejectsDuplicateMissingAliasExtraAndWrongTypes() throws IOException {
        ObjectNode base = baseRequest();
        for (JsonNode wrong : List.of(StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)),
                DoubleNode.valueOf(88.0),
                StrictJson.parse("\"88\"".getBytes(StandardCharsets.UTF_8)))) {
            ObjectNode request = base.deepCopy(); request.set("war_id", wrong);
            invalid(request);
        }
        ObjectNode request = base.deepCopy(); request.remove("campaign_root"); invalid(request);
        request = base.deepCopy(); request.set("root", request.remove("campaign_root")); invalid(request);
        request = base.deepCopy(); request.put("extra", true); invalid(request);
        String raw = new String(bytes(base), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> projector.project(
            ("{\"war_id\":88," + raw.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> projector.project((raw + " null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> projector.project(new byte[] {(byte) 0xff}));
        assertThrows(ContractViolationException.class, () -> projector.project(new byte[StrictJson.INPUT_MAX_BYTES + 1]));
    }

    @Test
    void incompleteConditionalAndContradictoryUnknownPublicResultsAreRejected() throws IOException {
        WarOutcomeStakesResult good = typed(baseRequest());
        assertEquals(WarOutcomeStakesResult.Status.SOURCE_REVIEWED_CONDITIONAL, good.status());
        assertThrows(ContractViolationException.class, () -> copyResult(good, good.status(), good.reason(),
            Optional.empty(), good.casusBelli(), good.querySequence(), good.queryCollection()));
        assertThrows(ContractViolationException.class, () -> copyResult(good, good.status(), good.reason(),
            good.side(), Optional.empty(), good.querySequence(), good.queryCollection()));
        assertThrows(ContractViolationException.class, () -> copyResult(good, good.status(), good.reason(),
            good.side(), good.casusBelli(), Optional.empty(), good.queryCollection()));
        assertThrows(ContractViolationException.class, () -> copyResult(good, good.status(), good.reason(),
            good.side(), good.casusBelli(), good.querySequence(), WarOutcomeStakesResult.QueryCollection.MISSING));
        assertThrows(ContractViolationException.class, () -> new WarOutcomeStakesResult(
            WarOutcomeStakesResult.Status.UNKNOWN, WarOutcomeStakesResult.Reason.SOURCE_REVIEWED_CONDITIONAL_EFFECTS,
            good.context(), good.frame(), good.warId(), good.side(), good.casusBelli(), Optional.empty(), List.of(),
            Map.of(), good.queryCollection(), good.querySequence(), good.liegeRelation(), good.targetTitles()));
        assertThrows(ContractViolationException.class, () -> new WarOutcomeStakesResult(
            good.status(), good.reason(), good.context(), good.frame(), good.warId(), good.side(), good.casusBelli(),
            Optional.of(""), good.exposures(), good.consultedSources(), good.queryCollection(), good.querySequence(),
            good.liegeRelation(), good.targetTitles()));
        assertThrows(ContractViolationException.class, () -> new WarOutcomeStakesResult(
            good.status(), good.reason(), good.context(), good.frame(), good.warId(), good.side(), good.casusBelli(),
            good.profileId(), good.exposures(), Map.of("common/source.txt", "x"), good.queryCollection(),
            good.querySequence(), good.liegeRelation(), good.targetTitles()));
    }

    @Test
    void publicQueryModelsRejectInvalidIdsNullsAndUnobservedCbIdentity() {
        var binding = new NativeTerminationOptions.QueryBinding(BigInteger.ONE, "native:90", BigInteger.ONE,
            BigInteger.ONE, "episode", BigInteger.ONE);
        assertThrows(ContractViolationException.class, () -> new NativeTerminationOptions.QueryBinding(
            BigInteger.ZERO, "native:90", BigInteger.ONE, BigInteger.ONE, "episode", BigInteger.ONE));
        assertThrows(ContractViolationException.class, () -> new NativeTerminationOptions.QueryBinding(
            StrictJson.UINT64_MAX.add(BigInteger.ONE), "native:90", BigInteger.ONE, BigInteger.ONE, "episode", BigInteger.ONE));
        assertThrows(ContractViolationException.class, () -> new NativeTerminationOptions.QueryBinding(
            BigInteger.ONE, "native:90", null, BigInteger.ONE, "episode", BigInteger.ONE));
        assertThrows(ContractViolationException.class, () -> new NativeTerminationOptions(
            0, WarSide.DEFENDER, true, -75, NativeTerminationOptions.Truth.TRUE, Optional.empty(), binding));
        assertThrows(NullPointerException.class, () -> new NativeTerminationOptions(
            88, null, true, -75, NativeTerminationOptions.Truth.TRUE, Optional.empty(), binding));
        assertThrows(ContractViolationException.class, () -> new NativeTerminationOptions(
            88, WarSide.DEFENDER, true, -75, NativeTerminationOptions.Truth.UNKNOWN,
            Optional.of(new NativeTerminationOptions.CasusBelli(0, "claim_cb")), binding));
    }

    @Test
    void completeNativeValidationRunsBeforeStaleAndPreservesPartialUnknownFacts() throws IOException {
        ObjectNode request = baseRequest();
        query(request).put("queried_snapshot_id", "native:89");
        JsonNode unknown = result(request);
        assertEquals("query_frame_or_war_identity_changed", unknown.path("reason").textValue());
        assertEquals("defender", unknown.path("player_side").textValue());
        assertEquals(111, unknown.path("query_sequence").intValue());
        object(object(query(request), "options"), "surrender").remove("terms");
        invalid(request);
        request = baseRequest(); object(request, "snapshot").put("paused", false);
        object(request, "snapshot").set("war_termination_options", StrictJson.object().put("bad", true));
        unknown = result(request);
        assertEquals("paused_living_player_not_observed", unknown.path("reason").textValue());
        assertEquals("not_evaluated", unknown.path("termination_query_collection").textValue());
        assertTrue(unknown.path("player_side").isNull());
    }

    @Test
    void sourceExtrasAndUnknownCbDoNotInventEarlierValidationRequirements() throws IOException {
        ObjectNode request = baseRequest();
        object(request, "current_source_sha256").putNull("unrelated/extra/not-a-reviewed-sha");
        assertEquals("source_reviewed_conditional", result(request).path("status").textValue());
        request.putNull("current_source_sha256");
        assertEquals("source_contract_not_current", result(request).path("reason").textValue());
        object(query(request), "active_casus_belli_identity").put("canonical_key", "future_cb");
        request.putNull("campaign_root");
        assertEquals("cb_side_profile_not_reviewed", result(request).path("reason").textValue());
        request = baseRequest(); request.set("campaign_root", StrictJson.object().put("status", "unavailable"));
        assertEquals("exact_build_campaign_root_not_observed", result(request).path("reason").textValue());
    }

    @Test
    void targetsRemainOrderedDuplicatedDetachedAndPresenceDistinct() throws IOException {
        ObjectNode request = baseRequest();
        ArrayNode targets = war(request).putArray("targeted_title_ids"); targets.add(2254).add(2254).add(5);
        WarOutcomeStakesResult projected = typed(request);
        targets.add(999);
        assertEquals(List.of(2254, 2254, 5), projected.targetTitles().valueIfPresent().orElseThrow());
        assertThrows(UnsupportedOperationException.class,
            () -> projected.targetTitles().valueIfPresent().orElseThrow().add(999));
        war(request).remove("targeted_title_ids");
        assertTrue(typed(request).targetTitles() instanceof JsonPresence.Missing<?>);
        war(request).putNull("targeted_title_ids");
        assertTrue(typed(request).targetTitles() instanceof JsonPresence.Null<?>);
        war(request).putArray("targeted_title_ids");
        assertEquals(List.of(), typed(request).targetTitles().valueIfPresent().orElseThrow());
    }

    @Test
    void normalizedIntegerAiScaleIsStrictAndSignedScorePairCannotOverflow() throws IOException {
        ObjectNode request = baseRequest();
        ObjectNode surrender = object(object(query(request), "options"), "surrender");
        surrender.put("context_constructed", true).put("native_validator_passed", true).put("available", true);
        surrender.put("ai_acceptance_observable", true);
        ObjectNode acceptance = surrender.putObject("ai_acceptance");
        acceptance.put("raw", BigInteger.valueOf(Long.MIN_VALUE)); acceptance.put("scale", 100000);
        checkNoEffectCredit(result(request));
        acceptance.put("raw", BigInteger.valueOf(Long.MAX_VALUE)); checkNoEffectCredit(result(request));
        acceptance.put("raw", BigInteger.valueOf(Long.MAX_VALUE).add(BigInteger.ONE)); invalid(request);
        acceptance.put("raw", 0); acceptance.put("scale", 100000.0); invalid(request);
        // This float-scale rejection is an explicit stricter wire rule, not old-oracle parity.
        request = baseRequest(); query(request).put("attacker_war_score", Integer.MIN_VALUE);
        query(request).put("defender_war_score", Integer.MIN_VALUE); invalid(request);
    }

    @Test
    void registryExactBytesAndCurrentMachineAreSeparateFromReviewMachine() throws IOException {
        try (InputStream stream = getClass().getResourceAsStream(
                "/org/xar/ck3/control/warpolicy/war_outcome_stakes_source_v1.json")) {
            assertTrue(stream != null);
            byte[] raw = stream.readAllBytes();
            byte[] changed = java.util.Arrays.copyOf(raw, raw.length + 1); changed[raw.length] = ' ';
            assertThrows(ContractViolationException.class, () -> ReviewedSourceRegistry.fromBytes(changed));
        }
        WarOutcomeStakesResult projected = typed(baseRequest());
        assertNotEquals(projected.context().machineId(), ReviewedSourceRegistry.bundled().reviewedMachineId());
    }

    private WarOutcomeStakesResult typed(ObjectNode request) {
        return projector.project(request.get("snapshot"), WarJson.positive32(request.get("war_id")),
            request.get("campaign_root"), request.get("current_source_sha256"),
            ObservationContext.fromJson(request.get("observation_context")));
    }
    private static WarOutcomeStakesResult copyResult(WarOutcomeStakesResult good, WarOutcomeStakesResult.Status status,
            WarOutcomeStakesResult.Reason reason, Optional<WarSide> side,
            Optional<NativeTerminationOptions.CasusBelli> cb, Optional<BigInteger> sequence,
            WarOutcomeStakesResult.QueryCollection collection) {
        return new WarOutcomeStakesResult(status, reason, good.context(), good.frame(), good.warId(), side, cb,
            good.profileId(), good.exposures(), good.consultedSources(), collection, sequence,
            good.liegeRelation(), good.targetTitles());
    }
    private void invalid(ObjectNode request) { assertThrows(ContractViolationException.class, () -> projector.project(bytes(request))); }
    private JsonNode result(ObjectNode request) { return StrictJson.parse(projector.project(bytes(request))); }
    private static byte[] bytes(ObjectNode request) { return request.toString().getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode object(JsonNode parent, String field) {
        JsonNode value = parent.get(field);
        assertTrue(value instanceof ObjectNode, field);
        return (ObjectNode) value;
    }
    private static ObjectNode query(ObjectNode request) {
        return (ObjectNode) object(request, "snapshot").path("war_termination_options").get(0);
    }
    private static ObjectNode war(ObjectNode request) {
        return (ObjectNode) object(request, "snapshot").path("active_wars").get(0);
    }
    private static void checkNoEffectCredit(JsonNode result) {
        assertFalse(result.path("actual_effects_verified").booleanValue());
        assertFalse(result.path("material_terms_complete").booleanValue());
        assertFalse(result.path("automatic_surrender_qualified").booleanValue());
        assertTrue(result.path("continue_legal_war_processing").booleanValue());
        for (String key : List.of("resolved_title_changes", "resource_deltas", "actual_war_result", "selected_action")) {
            assertTrue(result.path(key).isNull(), key);
        }
    }
    private static ObjectNode baseRequest() throws IOException {
        return corpus().vectors().stream().filter(row -> "result".equals(row.path("expected_kind").textValue())
                && "test_actual_normalizer_cache_and_json_roundtrip_claim_defender".equals(row.path("test_method").textValue()))
            .map(row -> (ObjectNode) StrictJson.parse(StrictJson.text(row.get("input_json")).getBytes(StandardCharsets.UTF_8)))
            .findFirst().orElseThrow(() -> new AssertionError("base producer vector absent"));
    }
    private record Corpus(ObjectNode header, List<ObjectNode> vectors) { }
    private static Corpus corpus() throws IOException {
        try (InputStream stream = WarOutcomeStakesGoldenTest.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) { throw new AssertionError("committed producer/oracle golden missing; CI cannot skip"); }
            byte[] raw = stream.readNBytes(CORPUS_MAX_BYTES + 1);
            assertTrue(raw.length > 0 && raw.length <= CORPUS_MAX_BYTES);
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            String[] rows = text.split("\n", -1); assertEquals("", rows[rows.length - 1]);
            assertTrue(rows.length > 2);
            ObjectNode header = (ObjectNode) StrictJson.parse(rows[0].getBytes(StandardCharsets.UTF_8));
            List<ObjectNode> vectors = new ArrayList<>();
            for (int index = 1; index < rows.length - 1; index++) {
                vectors.add((ObjectNode) StrictJson.parse(rows[index].getBytes(StandardCharsets.UTF_8)));
            }
            return new Corpus(header, List.copyOf(vectors));
        }
    }
}
