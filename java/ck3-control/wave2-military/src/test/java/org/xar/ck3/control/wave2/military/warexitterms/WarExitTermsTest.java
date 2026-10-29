package org.xar.ck3.control.wave2.military.warexitterms;

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
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTermsAdapter.BoundPreview;

class WarExitTermsTest {
    private static final int WAR_ID = 16_777_300;

    @Test
    void actualPythonNormalizerGoldenRoundTripsAcrossAllDataConsumers() throws IOException {
        byte[] golden = resource("normalized.json");
        WarExitTerms terms = WarExitTermsCodec.decode(golden, WAR_ID);
        assertArrayEquals(golden, WarExitTermsCodec.encode(terms));
        assertEquals(terms, WarExitTermsCodec.decode(WarExitTermsCodec.encode(terms)));
        assertEquals(14, terms.primaryResourceBalances().size());
        assertEquals(12, terms.attackerDefeat().primaryResourceDeltas().size());
        BoundPreview bound = bound(golden, StrictJson.UINT64_MAX);
        assertArrayEquals(resource("driver-result.json"), WarExitTermsAdapter.encodeDriverResult(bound));
        assertArrayEquals(resource("snapshot-cache.json"), WarExitTermsAdapter.encodeSnapshotCache(List.of(bound)));
        JsonNode driver = StrictJson.parse(WarExitTermsAdapter.encodeDriverResult(bound));
        JsonNode service = StrictJson.parse(WarExitTermsAdapter.encodeServiceResult(bound));
        JsonNode cache = StrictJson.parse(WarExitTermsAdapter.encodeSnapshotCache(List.of(bound)));
        JsonNode comparison = StrictJson.parse(WarExitTermsAdapter.encodeComparisonInput(WarExitTermsAdapter.comparisonInput(bound)));
        assertEquals(StrictJson.UINT64_MAX, driver.get("query_sequence").bigIntegerValue());
        assertTrue(driver.get("query_sequence").isIntegralNumber());
        assertEquals(WAR_ID, service.get("war_id").intValue());
        assertEquals(driver.get("war_termination_exit_terms"), service.get("war_termination_exit_terms"));
        assertEquals(driver.get("war_termination_exit_terms"), comparison.get("structured_exit_terms"));
        assertEquals(StrictJson.UINT64_MAX, cache.get(0).get("query_sequence").bigIntegerValue());
        assertEquals("campaign_outcome_forecast", comparison.get("unknown_fields").get(0).textValue());
        assertEquals("opponent_acceptance", comparison.get("unknown_fields").get(1).textValue());
        assertFalse(comparison.get("automatic_termination_enabled").booleanValue());
        assertFalse(WarExitTermsAdapter.comparisonInput(bound).automaticTerminationEnabled());
        assertThrows(UnsupportedOperationException.class, () -> terms.targetTitleIds().add(123));
        assertThrows(UnsupportedOperationException.class, () -> terms.primaryResourceBalances().clear());
    }

    @Test
    void disabledCollectorStaysDisabledEvenWithCompleteData() throws IOException {
        assertFalse(WarExitTerms.PRODUCTION_ENABLED);
        assertEquals(WarExitTermsAdapter.ProductionAdmission.DISABLED_NATIVE_PREVIEW_CRASH, WarExitTermsAdapter.productionAdmission());
        assertTrue(WarExitTermsAdapter.productionQuerySteps().isEmpty());
        assertEquals(0, StrictJson.parse(WarExitTermsAdapter.productionSnapshotProjection()).size());
        assertFalse(WarExitTermsAdapter.comparisonInput(bound(resource("normalized.json"), BigInteger.ONE)).automaticTerminationEnabled());
    }

    @Test
    void canonicalQueryGrammarAndNativeWarIdDomain() {
        assertEquals(WAR_ID, WarExitTermsAdapter.parseQueryStep(WarExitTermsAdapter.queryStep(WAR_ID)).orElseThrow());
        for (String suffix : List.of("0", "01", "+1", "-1", "1.0", "2147483648", "١", "1-extra", "")) {
            assertTrue(WarExitTermsAdapter.parseQueryStep(WarExitTerms.QUERY_PREFIX + suffix).isEmpty(), suffix);
        }
        assertTrue(WarExitTermsAdapter.parseQueryStep(null).isEmpty());
        assertThrows(ContractViolationException.class, () -> WarExitTermsAdapter.queryStep(0));
    }

    @Test
    void exactIntegerTokensRejectFloatBoolStringEvenWhenMathematicallyEqual() throws IOException {
        String input = new String(resource("normalized.json"), StandardCharsets.UTF_8);
        for (String replacement : List.of("true", "2.0", "\"2\"")) {
            assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(input.replace("\"schema_version\":2", "\"schema_version\":" + replacement).getBytes(StandardCharsets.UTF_8)));
        }
        for (String replacement : List.of("100000.0", "true", "\"100000\"")) {
            assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(input.replace("\"scale\":100000", "\"scale\":" + replacement).getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(input.replace("\"war_id\":" + WAR_ID, "\"war_id\":true").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(input.replace("\"raw\":35000000", "\"raw\":35000000.0").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode((input + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(input.replaceFirst("\\{", "{\"schema_version\":2,").getBytes(StandardCharsets.UTF_8)));
    }

    @Test
    void completeUnionRejectsMissingWrongNullAndReorderedDomains() throws IOException {
        List<Consumer<ObjectNode>> mutations = List.of(
                row -> row.put("extra", true), row -> row.remove("claims"), row -> row.put("status", "partial"),
                row -> row.put("player_side", "defender"), row -> row.putNull("primary_resource_balances"),
                row -> row.withObject("/readiness").put("exit_terms_ready", false),
                row -> row.withObject("/readiness").put("exit_terms_ready", 1),
                row -> row.withObject("/provenance").put("game_version", "1.20.0.4"),
                row -> row.withObject("/provenance").put("native_contract_sha256", "a".repeat(64)),
                row -> row.withObject("/outcomes/white_peace").putNull("truce"),
                row -> row.withObject("/outcomes/attacker_defeat/truce").put("expiry_date_raw", 1),
                row -> row.withObject("/outcomes/attacker_defeat/recipient_response").put("decision_status_raw", 3),
                row -> row.withObject("/outcomes/white_peace/recipient_response").put("would_accept_now", false),
                row -> row.withObject("/outcomes/white_peace/recipient_response").put("native_validator_passed", false),
                row -> row.withObject("/outcomes/attacker_defeat/cb_prestige_factor").put("raw", 1),
                row -> row.withObject("/outcomes/attacker_defeat/claim_disposition").put("declared_title_disposition", "transfer"),
                row -> ((ArrayNode) row.at("/primary_resource_balances/values")).remove(0),
                row -> ((ArrayNode) row.at("/primary_monthly_gold_income/values")).remove(0),
                row -> ((ArrayNode) row.at("/outcomes/white_peace/primary_resource_deltas/values")).remove(0),
                row -> ((ArrayNode) row.at("/outcomes/attacker_defeat/primary_gold_transfers/values")).removeAll(),
                row -> row.withArray("/target_title_ids").add(16_777_321),
                row -> row.withObject("/claims/0").put("present", false),
                row -> row.withObject("/claims/0").put("state", "strong_explicit"),
                row -> row.withObject("/outcomes/attacker_defeat/primary_gold_transfers/values/0").put("from_character_id", 5));
        for (Consumer<ObjectNode> mutation : mutations) {
            ObjectNode root = original(); mutation.accept(root);
            assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(StrictJson.canonical(root)));
        }
        ObjectNode reordered = original(); ArrayNode rows = (ArrayNode) reordered.at("/primary_resource_balances/values");
        JsonNode first = rows.get(0); JsonNode second = rows.get(1); rows.set(0, second); rows.set(1, first);
        assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(StrictJson.canonical(reordered)));
    }

    @Test
    void fullSignedFixedPointDomainAndNativeClaimDispositionSurviveRoundTrip() throws IOException {
        ObjectNode input = original();
        input.withObject("/primary_resource_balances/values/0").put("raw", Long.MIN_VALUE);
        input.withObject("/primary_resource_balances/values/1").put("raw", Long.MAX_VALUE);
        input.withObject("/claims/0").put("strong", true).put("state", "strong_explicit");
        input.withObject("/outcomes/white_peace/claim_disposition").put("claim_disposition", "retain_no_strength_change_already_strong");
        byte[] raw = StrictJson.canonical(input);
        assertArrayEquals(raw, WarExitTermsCodec.normalize(raw));
        input.withObject("/primary_resource_balances/values/0").put("raw", BigInteger.ONE.shiftLeft(63));
        assertThrows(ContractViolationException.class, () -> WarExitTermsCodec.decode(StrictJson.canonical(input)));
    }

    @Test
    void bindingAndCacheConsumeActualSnapshotsAndRejectFrameOrIdentityDrift() throws IOException {
        byte[] golden = resource("normalized.json");
        BoundPreview preview = bound(golden, StrictJson.UINT64_MAX);
        ObjectNode snapshot = snapshot(); snapshot.put("sdk_extension", "allowed");
        assertTrue(WarExitTermsAdapter.sameFrameCacheProjection(preview, StrictJson.canonical(snapshot)).isPresent());
        snapshot.put("revision", 42);
        assertTrue(WarExitTermsAdapter.sameFrameCacheProjection(preview, StrictJson.canonical(snapshot)).isEmpty());
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                row -> row.put("native_revision", 41), row -> row.put("paused", false),
                row -> row.put("snapshot_id", "native:changed"), row -> row.put("episode_run_id", "different"),
                row -> row.withObject("/diagnostics").put("connection_generation", 2),
                row -> row.withArray("/active_wars").removeAll())) {
            ObjectNode after = snapshot(); mutation.accept(after);
            assertThrows(ContractViolationException.class, () -> WarExitTermsAdapter.bindReturnedPreview(
                    receipt(golden, BigInteger.ONE), StrictJson.canonical(snapshot()), StrictJson.canonical(after), WAR_ID));
        }
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                row -> row.withObject("/active_wars/0").put("player_side", "defender"),
                row -> row.withObject("/active_wars/0").put("player_is_primary_war_leader", false),
                row -> row.withObject("/played_character").put("character_id", 3),
                row -> row.withObject("/active_wars/0").put("primary_opponent_character_id", 3),
                row -> row.withObject("/active_wars/0").withArray("targeted_title_ids").removeAll())) {
            ObjectNode before = snapshot(); mutation.accept(before);
            assertThrows(ContractViolationException.class, () -> WarExitTermsAdapter.bindReturnedPreview(
                    receipt(golden, BigInteger.ONE), StrictJson.canonical(before), StrictJson.canonical(before), WAR_ID));
        }
        assertThrows(ContractViolationException.class, () -> bound(golden, BigInteger.ZERO));
        assertThrows(ContractViolationException.class, () -> bound(golden, StrictJson.UINT64_MAX.add(BigInteger.ONE)));
        String rawReceipt = new String(receipt(golden, BigInteger.ONE), StandardCharsets.UTF_8);
        for (String token : List.of("1.0", "true", "\"1\"")) {
            assertThrows(ContractViolationException.class, () -> WarExitTermsAdapter.bindReturnedPreview(
                    rawReceipt.replace("\"query_sequence\":1", "\"query_sequence\":" + token).getBytes(StandardCharsets.UTF_8),
                    StrictJson.canonical(snapshot()), StrictJson.canonical(snapshot()), WAR_ID));
        }
    }

    @Test
    void independentOptionLegalityAndAcceptanceNeverBecomeExitAuthority() throws IOException {
        BoundPreview preview = bound(resource("normalized.json"), BigInteger.ONE);
        ObjectNode options = nativeOptions();
        WarExitTermsAdapter.ComparisonInput complete = WarExitTermsAdapter.comparisonInput(preview, StrictJson.canonical(options));
        assertEquals(List.of(WarExitTermsAdapter.UnknownField.CAMPAIGN_OUTCOME_FORECAST), complete.unknownFields());
        assertFalse(complete.automaticTerminationEnabled());
        ObjectNode surrender = options.withObject("/options/surrender");
        surrender.put("ai_acceptance_observable", false).putNull("ai_acceptance");
        assertEquals(List.of(WarExitTermsAdapter.UnknownField.CAMPAIGN_OUTCOME_FORECAST, WarExitTermsAdapter.UnknownField.OPPONENT_ACCEPTANCE),
                WarExitTermsAdapter.comparisonInput(preview, StrictJson.canonical(options)).unknownFields());
        options.put("queried_revision", 42);
        assertThrows(ContractViolationException.class, () -> WarExitTermsAdapter.comparisonInput(preview, StrictJson.canonical(options)));
    }

    private static ObjectNode original() throws IOException { return (ObjectNode) StrictJson.parse(resource("normalized.json")); }
    private static BoundPreview bound(byte[] golden, BigInteger sequence) {
        byte[] snapshot = StrictJson.canonical(snapshot());
        return WarExitTermsAdapter.bindReturnedPreview(receipt(golden, sequence), snapshot, snapshot, WAR_ID);
    }
    private static byte[] receipt(byte[] golden, BigInteger sequence) {
        ObjectNode row = StrictJson.object(); row.put("step", WarExitTermsAdapter.queryStep(WAR_ID)); row.put("accepted", true);
        row.put("status", "available"); row.put("query_sequence", sequence); row.put("backend_id", "native-headless");
        row.set("war_termination_exit_terms", StrictJson.parse(golden)); return StrictJson.canonical(row);
    }
    private static ObjectNode snapshot() {
        ObjectNode row = StrictJson.object(); row.put("paused", true); row.put("snapshot_id", "native:40"); row.put("revision", 41);
        row.put("native_revision", 40); row.put("episode_run_id", "synthetic-exit-terms-replay");
        row.putObject("diagnostics").put("connection_generation", 1); row.putObject("played_character").put("character_id", 16_777_218);
        ObjectNode war = row.putArray("active_wars").addObject(); war.put("war_id", WAR_ID); war.put("player_side", "attacker");
        war.put("player_is_primary_war_leader", true); war.put("primary_opponent_character_id", 16_777_219);
        war.putArray("targeted_title_ids").add(16_777_221); return row;
    }
    private static ObjectNode nativeOptions() {
        ObjectNode row = StrictJson.object(); row.put("war_id", WAR_ID); row.put("player_side", "attacker");
        row.put("player_is_primary_war_leader", true); row.put("player_relative_war_score", 17); row.put("war_duration_days", 203);
        row.put("active_casus_belli_present", true); ObjectNode cb = row.putObject("active_casus_belli_identity");
        cb.put("database_index", 3); cb.put("canonical_key", "claim_cb"); row.put("cb_allows_white_peace", true);
        row.put("absolute_war_scores_observable", true); row.put("attacker_war_score", 17); row.put("defender_war_score", -17);
        row.putNull("war_score_breakdown"); row.put("query_sequence", 1); row.put("queried_snapshot_id", "native:40");
        row.put("queried_revision", 41); row.put("queried_native_revision", 40); row.put("episode_run_id", "synthetic-exit-terms-replay");
        row.put("queried_connection_generation", 1); row.put("source", "native"); ObjectNode options = row.putObject("options");
        for (String name : List.of("surrender", "white_peace", "victory")) {
            ObjectNode option = options.putObject(name); option.put("outcome", name.equals("surrender") ? "attacker_defeat"
                    : name.equals("victory") ? "attacker_victory" : "white_peace");
            boolean legal = !name.equals("victory"); option.put("hostage_variant", "none"); option.put("context_constructed", true);
            option.put("native_validator_passed", legal); option.put("available", legal); option.put("terms_observable", false);
            ObjectNode terms = option.putObject("terms"); terms.put("status", "unavailable"); terms.put("reason", "cb_specific_terms_not_observable");
            option.put("ai_acceptance_observable", true); ObjectNode acceptance = option.putObject("ai_acceptance"); acceptance.put("raw", 0); acceptance.put("scale", 100_000);
            option.put("auto_accept_observable", true); option.put("auto_accept", false); ObjectNode response = option.putObject("recipient_response");
            response.put("status", legal ? "available" : "unavailable");
            if (legal) { response.put("decision_status_raw", 0); response.put("would_accept_now", true); }
            else { response.putNull("decision_status_raw"); response.putNull("would_accept_now"); }
        }
        return row;
    }
    private static byte[] resource(String name) throws IOException {
        try (InputStream stream = WarExitTermsTest.class.getResourceAsStream("/warexitterms/" + name)) {
            if (stream == null) { throw new IOException("M7 producer golden missing: " + name); }
            return stream.readAllBytes();
        }
    }
}
