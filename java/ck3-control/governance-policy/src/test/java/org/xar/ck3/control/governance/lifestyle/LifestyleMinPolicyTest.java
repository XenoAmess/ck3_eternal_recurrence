package org.xar.ck3.control.governance.lifestyle;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.FieldState;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksCodec;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel;

final class LifestyleMinPolicyTest {
    private static final String GOLDEN = "/lifestyle/original-producer-golden-v1.json";
    private static JsonNode golden() throws IOException {
        try (InputStream input = LifestyleMinPolicyTest.class.getResourceAsStream(GOLDEN)) {
            assertNotNull(input, "committed original producer golden is required; never skip or execute Python by default");
            JsonNode root = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).readTree(input);
            assertEquals("lifestyle-min-original-producer-golden-v1", root.path("schema").textValue());
            assertTrue(root.path("synthetic_inputs").booleanValue());
            assertFalse(root.path("native_business_qualification").booleanValue());
            assertTrue(root.path("source_sha256").textValue().matches("[0-9a-f]{64}"));
            return root;
        }
    }
    @TestFactory
    Stream<DynamicTest> originalProducerDifferential() throws IOException {
        JsonNode cases = golden().path("cases");
        assertTrue(cases.size() >= 50, "whole committed original producer capture required");
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : cases) {
            tests.add(DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
                byte[] request = StrictJson.canonical(row.get("request"));
                byte[] actual = row.path("operation").textValue().equals("minimum")
                        ? LifestyleMinCodec.evaluate(request) : LifestyleMinCodec.evaluateFirstFocus(request);
                assertEquals(row.get("expected"), StrictJson.parse(actual));
                if (row.path("operation").textValue().equals("minimum")) {
                    assertEquals(row.get("request"), StrictJson.parse(LifestyleMinCodec.encode(LifestyleMinCodec.decode(request))));
                } else {
                    assertEquals(row.get("request"), StrictJson.parse(LifestyleMinCodec.encode(LifestyleMinCodec.decodeFirstFocus(request))));
                }
            }));
        }
        return tests.stream();
    }
    private static ObjectNode minimumRequest() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            if (row.path("name").textValue().equals("build_cost")) { return (ObjectNode) row.get("request").deepCopy(); }
        }
        throw new AssertionError("original build_cost case missing");
    }
    @Test void integerTokensNeverCoerce() throws IOException {
        ObjectNode request = minimumRequest();
        for (String invalid : List.of("true", "1.0", "\"1\"", "[]", "{}")) {
            ObjectNode bad = request.deepCopy();
            ((ObjectNode) bad.get("snapshot")).set("public_revision", new ObjectMapper().readTree(invalid));
            assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode(StrictJson.canonical(bad)));
        }
        ObjectNode fractional = request.deepCopy();
        String raw = new String(StrictJson.canonical(fractional), StandardCharsets.UTF_8)
                .replace("\"public_revision\":701", "\"public_revision\":701.0");
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode(raw.getBytes(StandardCharsets.UTF_8)));
    }
    @Test void requiredEnvelopeAndUnknownFieldsReject() throws IOException {
        ObjectNode missing = minimumRequest(); missing.remove("at_peace");
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode(StrictJson.canonical(missing)));
        ObjectNode extra = minimumRequest(); extra.put("allow_inferred_legality", true);
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode(StrictJson.canonical(extra)));
        ObjectNode v3 = minimumRequest(); ((ObjectNode) v3.get("snapshot")).putObject("all_lifestyle_progress_v3");
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode(StrictJson.canonical(v3)),
                "V3 must use typed routed consumer, never silently enter the legacy frontier");
    }
    @Test void duplicatesTrailingTokensAndInvalidUtf8Reject() throws IOException {
        byte[] valid = StrictJson.canonical(minimumRequest());
        String text = new String(valid, StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode(
                text.replaceFirst("\\{", "{\"schema\":\"duplicate\",").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode((text + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
    @Test void missingNullAndEmptyCollectionsRetainIdentity() throws IOException {
        ObjectNode missing = minimumRequest(); ((ObjectNode) missing.get("snapshot")).remove("owned_perk_keys");
        ObjectNode nullValue = minimumRequest(); ((ObjectNode) nullValue.get("snapshot")).putNull("owned_perk_keys");
        ObjectNode empty = minimumRequest(); ((ObjectNode) empty.get("snapshot")).putArray("owned_perk_keys");
        var missingModel = LifestyleMinCodec.decode(StrictJson.canonical(missing));
        var nullModel = LifestyleMinCodec.decode(StrictJson.canonical(nullValue));
        var emptyModel = LifestyleMinCodec.decode(StrictJson.canonical(empty));
        assertEquals(FieldState.MISSING, missingModel.snapshot().value().ownedPerks().state());
        assertEquals(FieldState.NULL, nullModel.snapshot().value().ownedPerks().state());
        assertEquals(FieldState.PRESENT, emptyModel.snapshot().value().ownedPerks().state());
        assertEquals(missing, StrictJson.parse(LifestyleMinCodec.encode(missingModel)));
        assertEquals(nullValue, StrictJson.parse(LifestyleMinCodec.encode(nullModel)));
        assertEquals(empty, StrictJson.parse(LifestyleMinCodec.encode(emptyModel)));
    }
    @Test void pendingEmptyAndNullStatusRemainUnknown() throws IOException {
        for (boolean nullStatus : List.of(false, true)) {
            ObjectNode request = minimumRequest(); ObjectNode pending = request.putObject("pending_action");
            if (nullStatus) { pending.putNull("status"); }
            var parsed = LifestyleMinCodec.decode(StrictJson.canonical(request));
            assertEquals(LifestyleMinPolicy.Status.ACTION_STATE_UNKNOWN, LifestyleMinPolicy.choose(parsed).status());
            assertEquals(request, StrictJson.parse(LifestyleMinCodec.encode(parsed)));
        }
    }
    @Test void authoredFrontierIsCompleteAndOrdered() {
        assertEquals(27, LifestyleMinPolicy.STEWARDSHIP_ORDER.size());
        assertEquals(27, LifestyleMinPolicy.STEWARDSHIP_ORDER.stream().distinct().count());
        assertEquals(List.of("cutting_corners_perk", "professional_workforce_perk", "centralization_perk", "tax_man_perk"),
                LifestyleMinPolicy.STEWARDSHIP_ORDER.subList(0, 4));
        assertTrue(LifestyleMinPolicy.STEWARDSHIP_ORDER.indexOf("defensive_measures_perk")
                < LifestyleMinPolicy.STEWARDSHIP_ORDER.indexOf("golden_obligations_perk"));
    }
    @Test void exactLargeIntegerBindingsNeverRoundTripThroughDouble() throws IOException {
        ObjectNode request = minimumRequest();
        java.math.BigInteger exact = new java.math.BigInteger("18446744073709551615");
        ((ObjectNode) request.get("snapshot")).put("player_character_id", exact);
        JsonNode output = StrictJson.parse(LifestyleMinCodec.evaluate(StrictJson.canonical(request)));
        assertEquals(exact, output.path("selected_action").path("expected").path("expected_player_character_id").bigIntegerValue());
        assertEquals(request, StrictJson.parse(LifestyleMinCodec.encode(LifestyleMinCodec.decode(StrictJson.canonical(request)))));
    }
    private static ObjectNode v3Input() throws IOException {
        try (InputStream input = LifestyleMinPolicyTest.class.getResourceAsStream("/lifestyleperks/legacy-golden-v1.json")) {
            assertNotNull(input, "the real V3 producer golden must accompany the typed delegate");
            return (ObjectNode) new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
                    .readTree(input).path("cases").get(0).get("input").deepCopy();
        }
    }
    private static ObjectNode alignedMinimum(ObjectNode v3) throws IOException {
        ObjectNode minimum = minimumRequest(); ObjectNode snapshot = (ObjectNode) minimum.get("snapshot");
        JsonNode source = v3.get("snapshot");
        for (String key : List.of("snapshot_id", "episode_run_id", "public_revision", "native_revision", "proof_epoch", "date_raw", "player_character_id")) {
            snapshot.set(key, source.get(key));
        }
        snapshot.set("owned_perk_keys", v3.get("owned"));
        ObjectNode candidates = ((ObjectNode) source.get("legal_perk_candidates")).deepCopy(); candidates.remove("scope");
        snapshot.set("legal_perk_candidates", candidates);
        ((ObjectNode) snapshot.get("readiness")).remove("lifestyle_progress_ready");
        return minimum;
    }
    @Test void routedV3UsesRealTypedDelegateAndRetainsScopePendingAndExactBinding() throws IOException {
        ObjectNode v3 = v3Input(); ObjectNode minimum = alignedMinimum(v3);
        var input = LifestylePerksCodec.decode(StrictJson.canonical(v3));
        var request = LifestyleMinCodec.decode(StrictJson.canonical(minimum));
        var result = LifestyleMinPolicy.chooseRouted(request, Field.of(input));
        assertInstanceOf(LifestyleMinPolicy.AllLifestyleDecision.class, result);
        assertEquals(LifestyleMinPolicy.Status.RECOMMEND_ACTION, result.status());
        JsonNode output = StrictJson.parse(LifestyleMinCodec.encode(result));
        assertEquals("g2-m4-lifestyle-min-v1", output.path("policy_id").textValue());
        assertEquals(input.candidates() instanceof LifestylePerksModel.LegalCandidates legal ? legal.items().getFirst().key() : "invalid",
                output.path("selected_action").path("target_key").textValue());
        ObjectNode pending = minimum.deepCopy(); pending.putObject("pending_action").put("status", "submitted_verification_pending");
        assertEquals(LifestyleMinPolicy.Status.VERIFY_PENDING_RECEIPT,
                LifestyleMinPolicy.chooseRouted(LifestyleMinCodec.decode(StrictJson.canonical(pending)), Field.nullValue()).status());
        ObjectNode stale = minimum.deepCopy(); ((ObjectNode) stale.get("snapshot")).put("proof_epoch", input.binding().expectedProofEpoch().add(java.math.BigInteger.ONE));
        assertThrows(ContractViolationException.class, () -> LifestyleMinPolicy.chooseRouted(LifestyleMinCodec.decode(StrictJson.canonical(stale)), Field.of(input)));
        ObjectNode wrongCandidates = minimum.deepCopy(); ((ObjectNode) wrongCandidates.at("/snapshot/legal_perk_candidates/items/0")).put("key", "other_perk");
        assertThrows(ContractViolationException.class, () -> LifestyleMinPolicy.chooseRouted(LifestyleMinCodec.decode(StrictJson.canonical(wrongCandidates)), Field.of(input)));
    }
    @Test void explicitRoutedCodecCannotSilentlyFallBackWhenV3EvidenceUnknown() throws IOException {
        ObjectNode root = StrictJson.object().put("schema", LifestyleMinCodec.ROUTED_SCHEMA).put("progress_route", "life2");
        root.set("minimum", minimumRequest()); root.putNull("all_lifestyle");
        assertEquals(LifestyleMinPolicy.Status.RECOMMEND_ACTION.wire(), StrictJson.parse(LifestyleMinCodec.evaluateRouted(StrictJson.canonical(root))).path("status").textValue());
        root.put("progress_route", "all_lifestyle_v3");
        JsonNode unknown = StrictJson.parse(LifestyleMinCodec.evaluateRouted(StrictJson.canonical(root)));
        assertEquals("observation_unavailable", unknown.path("status").textValue());
        assertEquals("all_lifestyle_progress_binding_invalid", unknown.path("reason").textValue());
        assertTrue(unknown.path("selected_action").isNull());
        root.put("progress_route", "future_route");
        assertThrows(ContractViolationException.class, () -> LifestyleMinCodec.evaluateRouted(StrictJson.canonical(root)));
    }
    @Test void focuslessV3NoPointFallsThroughToExistingFirstFocusWithoutLegacyProgressReadiness() throws IOException {
        ObjectNode v3 = v3Input(); ObjectNode minimum = alignedMinimum(v3);
        var original = LifestylePerksCodec.decode(StrictJson.canonical(v3));
        List<LifestylePerksModel.ProgressRow> rows = new ArrayList<>();
        for (var lifestyle : LifestylePerksModel.Lifestyle.values()) {
            rows.add(new LifestylePerksModel.AvailableProgress(lifestyle, java.math.BigInteger.ZERO, java.math.BigInteger.ZERO,
                    java.math.BigInteger.valueOf(1000), java.math.BigInteger.ZERO, java.math.BigInteger.ZERO));
        }
        var input = new LifestylePerksModel.Input(original.snapshotFrame(),
                new LifestylePerksModel.ProgressObservation(original.snapshotFrame(), LifestylePerksModel.Completeness.COMPLETE, rows),
                new LifestylePerksModel.LegalCandidates("policy_target", List.of()), original.binding(), original.owned());
        ObjectNode snapshot = (ObjectNode) minimum.get("snapshot");
        snapshot.putObject("current_focus").put("presence", "absent");
        snapshot.putObject("current_lifestyle_progress").put("presence", "absent");
        snapshot.putObject("target_lifestyle_progress").put("presence", "present").put("lifestyle_key", "stewardship_lifestyle").put("unspent_perk_points", 0);
        snapshot.putObject("legal_perk_candidates").put("status", "available").putArray("items");
        snapshot.putObject("legal_focus_candidates").put("status", "available").putArray("items")
                .addObject().put("key", "stewardship_wealth_focus").put("lifestyle_key", "stewardship_lifestyle");
        var result = LifestyleMinPolicy.chooseRouted(LifestyleMinCodec.decode(StrictJson.canonical(minimum)), Field.of(input));
        assertInstanceOf(LifestyleMinPolicy.MinimumDecision.class, result);
        JsonNode output = StrictJson.parse(LifestyleMinCodec.encode(result));
        assertEquals("focus", output.path("selected_action").path("kind").textValue());
        assertEquals("stewardship_wealth_focus", output.path("selected_action").path("target_key").textValue());
    }
}
