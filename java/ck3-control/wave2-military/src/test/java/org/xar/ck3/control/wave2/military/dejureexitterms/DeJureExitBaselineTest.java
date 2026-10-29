package org.xar.ck3.control.wave2.military.dejureexitterms;

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
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.Frame;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.ObservedPredicate;
import org.xar.ck3.control.wave2.military.dejureexitterms.DeJureExitBaseline.StructuralCandidate;

class DeJureExitBaselineTest {
    private static final int WAR_ID = 16_777_231;
    private static final Frame FRAME = new Frame(WAR_ID, 3, 53_217_264, 29_829, 30_097, List.of(2128L));

    @Test
    void actualProducerGoldenPreservesBothRawAndProjectedRepresentations() throws IOException {
        for (String fixture : List.of("baseline", "truce", "storage")) {
            byte[] raw = resource(fixture + "-input.json");
            DeJureExitBaseline observed = DeJureExitBaselineCodec.decode(raw, FRAME);
            assertArrayEquals(raw, DeJureExitBaselineCodec.encodeRaw(observed));
            assertArrayEquals(resource(fixture + "-expected.json"), DeJureExitBaselineCodec.encodeProjection(observed));
            assertEquals(observed, DeJureExitBaselineCodec.decode(DeJureExitBaselineCodec.encodeRaw(observed), FRAME));
            JsonNode result = StrictJson.parse(DeJureExitBaselineCodec.encodeProjection(observed));
            assertTrue(result.get("recommended_outcome").isNull()); assertTrue(result.get("action_literal").isNull());
            assertTrue(result.get("directed_truce").isNull()); assertTrue(result.get("signed_resource_delta").isNull());
            assertTrue(result.get("title_vassal_delta").isNull()); assertFalse(result.get("material_complete").booleanValue());
            assertFalse(result.has("same_frame_stable")); assertFalse(result.has("casus_belli_key"));
            assertThrows(UnsupportedOperationException.class, () -> observed.primaryResourceBalances().clear());
        }
        DeJureExitBaseline baseline = DeJureExitBaselineCodec.decode(resource("baseline-input.json"), FRAME);
        assertTrue(baseline.truceInputs().isEmpty()); assertTrue(baseline.borderRaidStorageCandidate().isEmpty());
        DeJureExitBaseline truce = DeJureExitBaselineCodec.decode(resource("truce-input.json"), FRAME);
        assertEquals(new ObservedPredicate(false), truce.truceInputs().orElseThrow().nomadBoth());
        StructuralCandidate candidate = (StructuralCandidate) DeJureExitBaselineCodec.decode(resource("storage-input.json"), FRAME)
                .borderRaidStorageCandidate().orElseThrow();
        assertFalse(candidate.candidate()); assertEquals(17, candidate.storageCapacity());
    }

    @Test
    void balancesAreCurrentPrestateAndNeverInventMaterialEffectsOrStockQualification() throws IOException {
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                row -> row.put("material_complete", true), row -> row.putArray("signed_resource_delta"),
                row -> row.putObject("directed_truce").put("days", 0),
                row -> row.put("title_vassal_delta_unavailable_reason", "observed"),
                row -> row.putObject("h2743_stock_predicate_evidence_v1").put("same_frame_stable", true),
                row -> row.withObject("/truce_inputs_v1").put("evaluated_days", 730),
                row -> row.withObject("/truce_inputs_v1/short").put("status", "observed").put("value", false).putNull("unavailable_reason"),
                row -> row.withObject("/truce_inputs_v1/nomad_both").put("value", true),
                row -> row.withObject("/border_raid_storage_candidate_v1").put("native_condition_observed", true),
                row -> row.withObject("/border_raid_storage_candidate_v1").put("matching_war_count", 1),
                row -> row.withObject("/target_title_holder_prestate/0").put("holder_immediate_liege_character_id", 33435),
                row -> row.putNull("primary_monthly_gold_income"), row -> row.remove("same_frame_stable"))) {
            ObjectNode raw = original("storage"); mutation.accept(raw);
            assertThrows(ContractViolationException.class, () -> DeJureExitBaselineCodec.decode(StrictJson.canonical(raw), FRAME));
        }
        ObjectNode absent = original("baseline"); absent.putNull("truce_inputs_v1");
        assertThrows(ContractViolationException.class, () -> DeJureExitBaselineCodec.decode(StrictJson.canonical(absent), FRAME));
        ObjectNode zero = original("baseline");
        for (JsonNode row : zero.get("primary_resource_balances")) { ((ObjectNode) row.get("value")).put("raw", 0); }
        JsonNode projected = StrictJson.parse(DeJureExitBaselineCodec.normalize(StrictJson.canonical(zero), FRAME));
        assertTrue(projected.get("signed_resource_delta").isNull());
        assertEquals(0, projected.at("/primary_resource_balances/0/value/raw").intValue());
    }

    @Test
    void signedInt64IdentityAndFixedPointDomainsRetainExactValuesWithoutNumberCoercion() throws IOException {
        ObjectNode raw = original("baseline");
        raw.withObject("/primary_resource_balances/0/value").put("raw", Long.MIN_VALUE);
        raw.withObject("/primary_resource_balances/1/value").put("raw", Long.MAX_VALUE);
        byte[] exact = StrictJson.canonical(raw);
        assertArrayEquals(exact, DeJureExitBaselineCodec.encodeRaw(DeJureExitBaselineCodec.decode(exact, FRAME)));
        raw.withObject("/primary_resource_balances/0/value").put("raw", BigInteger.ONE.shiftLeft(63));
        assertThrows(ContractViolationException.class, () -> DeJureExitBaselineCodec.decode(StrictJson.canonical(raw), FRAME));
        String tokens = new String(resource("baseline-input.json"), StandardCharsets.UTF_8);
        for (String token : List.of("3.0", "true", "\"3\"")) {
            assertThrows(ContractViolationException.class, () -> DeJureExitBaselineCodec.decode(
                    tokens.replace("\"native_revision\":3", "\"native_revision\":" + token).getBytes(StandardCharsets.UTF_8), FRAME));
        }
        for (String token : List.of("100000.0", "true", "\"100000\"")) {
            assertThrows(ContractViolationException.class, () -> DeJureExitBaselineCodec.decode(
                    tokens.replace("\"scale\":100000", "\"scale\":" + token).getBytes(StandardCharsets.UTF_8), FRAME));
        }
        ObjectNode nullableLiege = original("baseline"); nullableLiege.withObject("/target_title_holder_prestate/0").putNull("holder_immediate_liege_character_id");
        assertTrue(DeJureExitBaselineCodec.decode(StrictJson.canonical(nullableLiege), FRAME).titleHolderPrestate().get(0).holderImmediateLiegeCharacterId().isEmpty());
    }

    @Test
    void nativeDriverAdapterBindsUnsignedSequenceAndFullWarIdentityWithExtensibleSnapshots() throws IOException {
        byte[] raw = receipt(resource("storage-input.json")); ObjectNode snapshot = snapshot();
        snapshot.put("sdk_extension", "allowed");
        DeJureExitBaselineAdapter.BoundBaseline bound = DeJureExitBaselineAdapter.bindReturnedBaseline(raw,
                StrictJson.canonical(snapshot), StrictJson.canonical(snapshot), WAR_ID);
        JsonNode output = StrictJson.parse(DeJureExitBaselineAdapter.encodeDriverResult(bound));
        assertEquals(StrictJson.UINT64_MAX, output.get("query_sequence").bigIntegerValue());
        assertEquals(StrictJson.parse(resource("storage-expected.json")), output.get("defender_de_jure_exit_terms_v1"));
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                row -> row.put("paused", false), row -> row.put("native_revision", 4),
                row -> row.put("episode_run_id", "changed"), row -> row.withObject("/diagnostics").put("connection_generation", 2),
                row -> row.withObject("/active_wars/0").put("player_relative_war_score", -2),
                row -> row.withArray("/active_wars").removeAll())) {
            ObjectNode after = snapshot(); mutation.accept(after);
            assertThrows(ContractViolationException.class, () -> DeJureExitBaselineAdapter.bindReturnedBaseline(
                    raw, StrictJson.canonical(snapshot()), StrictJson.canonical(after), WAR_ID));
        }
        ObjectNode wrongSide = snapshot(); wrongSide.withObject("/active_wars/0").put("player_side", "attacker");
        assertThrows(ContractViolationException.class, () -> DeJureExitBaselineAdapter.bindReturnedBaseline(raw,
                StrictJson.canonical(wrongSide), StrictJson.canonical(wrongSide), WAR_ID));
    }

    @Test
    void missingAndDuplicateResourceRowsCannotBeReplacedWithZeros() throws IOException {
        ObjectNode raw = original("baseline"); ArrayNode balances = (ArrayNode) raw.get("primary_resource_balances");
        balances.set(1, balances.get(0));
        assertThrows(ContractViolationException.class, () -> DeJureExitBaselineCodec.decode(StrictJson.canonical(raw), FRAME));
        ObjectNode missingIncome = original("baseline"); ((ArrayNode) missingIncome.get("primary_monthly_gold_income")).remove(0);
        byte[] missing = StrictJson.canonical(missingIncome);
        assertThrows(ContractViolationException.class, () -> DeJureExitBaselineCodec.decode(missing, FRAME));
    }

    private static ObjectNode original(String fixture) throws IOException { return (ObjectNode) StrictJson.parse(resource(fixture + "-input.json")); }
    private static ObjectNode snapshot() {
        ObjectNode root = StrictJson.object(); root.put("paused", true); root.put("snapshot_id", "native:3"); root.put("revision", 4);
        root.put("native_revision", 3); root.put("date_raw", 53_217_264); root.put("episode_run_id", "synthetic-dejure-baseline");
        root.putObject("played_character").put("character_id", 29_829); root.putObject("diagnostics").put("connection_generation", 1);
        ObjectNode war = root.putArray("active_wars").addObject(); war.put("war_id", WAR_ID); war.put("player_side", "defender");
        war.put("player_is_primary_war_leader", true); war.put("primary_opponent_character_id", 30_097); war.put("player_relative_war_score", -1);
        war.putArray("targeted_title_ids").add(2128); return root;
    }
    private static byte[] receipt(byte[] input) {
        ObjectNode result = StrictJson.object(); result.put("step", DeJureExitBaselineCodec.queryStep(WAR_ID)); result.put("accepted", true);
        result.put("status", "baseline_only"); result.put("query_sequence", StrictJson.UINT64_MAX); result.put("backend_id", "native-headless");
        result.set("defender_de_jure_exit_terms_v1", StrictJson.parse(input)); return StrictJson.canonical(result);
    }
    private static byte[] resource(String filename) throws IOException {
        try (InputStream stream = DeJureExitBaselineTest.class.getResourceAsStream("/dejureexitterms/" + filename)) {
            if (stream == null) { throw new IOException("M7 actual producer golden missing: " + filename); }
            return stream.readAllBytes();
        }
    }
}
