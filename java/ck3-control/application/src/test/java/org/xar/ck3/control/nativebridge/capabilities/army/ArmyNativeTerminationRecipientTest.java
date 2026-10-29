package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.zip.GZIPInputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.planning.military.NativeWarEndConditions;
import org.xar.ck3.control.g2.m0.RaiktorWhitePeaceProjectionProducer;
import org.xar.ck3.control.g2.m0.RaiktorRawOperations;
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.application.planning.warexit.WarExitCapabilities;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence;
import org.xar.ck3.control.application.planning.warexit.WarExitReads;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual C++ query + shared production serializer bytes. Software callbacks and outer observation
 * confer no Native/Game authority, actual acceptance, terminal effect or cold qualification.
 * Generation source/binary/command receipt: D:/ck3-state/ck3-java-g2-resume63-m0-native01/M0-CORPUS-PROVENANCE02.json (14102 bytes, SHA-256 d3ed8fc13f0f824f3c896d01234ca742a58d68b4c326adc8814e54459934ab16).
 * Roles generation: m0-context-role01/CORPUS-PROVENANCE01.json 44129B/a9ca7aa69d905276f3494d5d99acbb2f1a87f56682cc3db7885558b3a0baff6b.
 * Persistent CI regenerates the roles corpus and compares bytes with its distinct bundled resource. */
final class ArmyNativeTerminationRecipientTest {
    private static final String RESOURCE = "native-termination-recipient-resume63.ndjson";
    private static final String CORPUS_SHA256 = "bba94a92c96e04d73055005f5474437fa0fec3d3d1e5ad2cfc809e8243dec659";
    private static final String CONTEXT_RESOURCE = "native-termination-context-resume63.ndjson";
    private static final String CONTEXT_SHA256 = "610c5aeecc0681ab016dda7354d727e1671a34db4aa01640dfd25aa41d761669";
    private static final int WAR = 33554435, ACTOR = 50331652, DATE = 53175816;
    private static final Set<String> CAPS = Set.of("game.command.query-war-termination-options-N",
            "game.command.offer-white-peace-N", "game.command.surrender-war-N");
    private record Expected(boolean attacker, Integer status, boolean valid, boolean callback) {
        boolean observable() { return valid && callback && status != null && status <= 2; }
        boolean finalAccepts() { return observable() && status != 2; }
        boolean proposal() { return valid && (!attacker || finalAccepts()); }
    }
    private static final Map<String, Expected> EXPECTED = Map.of(
            "attacker-status-0", new Expected(true, 0, true, true),
            "attacker-status-1", new Expected(true, 1, true, true),
            "attacker-status-2", new Expected(true, 2, true, true),
            "attacker-status-3", new Expected(true, 3, true, true),
            "attacker-status-255", new Expected(true, 255, true, true),
            "attacker-no-callback", new Expected(true, null, true, false),
            "attacker-invalid", new Expected(true, null, false, true),
            "defender-status-2", new Expected(false, 2, true, true),
            "defender-no-callback", new Expected(false, null, true, false));

    private static void assertJsonValueEquals(JsonNode expected, JsonNode actual, String context) {
        assertArrayEquals(StrictJson.canonical(expected, StrictJson.EXPLICIT_MAX_BYTES),
                StrictJson.canonical(actual, StrictJson.EXPLICIT_MAX_BYTES), context);
    }

    @Test void actualQuerySerializerCorpusReachesOriginalPublicCacheAndPolicyConsumers() throws Exception {
        Map<String, NativeRow> rows = corpus();
        for (var entry : rows.entrySet()) {
            String name = entry.getKey(); Expected expected = EXPECTED.get(name);
            Consumed consumed = consume(entry.getValue());
            JsonNode originalAnswer = entry.getValue().top().at("/result/war_termination_options/options/white_peace/recipient_response");
            assertEquals(expected.observable() ? "available" : "unavailable", originalAnswer.path("status").textValue(), name);
            if (expected.observable()) {
                assertEquals(expected.status().intValue(), originalAnswer.path("decision_status_raw").intValue(), name);
                assertEquals(expected.finalAccepts(), originalAnswer.path("would_accept_now").booleanValue(), name);
            } else {
                assertTrue(originalAnswer.path("decision_status_raw").isNull(), name);
                assertTrue(originalAnswer.path("would_accept_now").isNull(), name);
            }
            assertEquals(originalAnswer, ArmyJson.parse(consumed.originalWire().bytes())
                    .at("/war_termination_options/options/white_peace/recipient_response"), name);
            assertEquals(originalAnswer, OpportunityJson.toNode(ArmyPublicWire.decodeExactSourceBound(consumed.publicWire(), context()))
                    .at("/war_termination_options/options/white_peace/recipient_response"), name);
            assertEquals(consumed.observed(), consume(entry.getValue()).observed(), name);
            var options = WarExitEvidence.currentOptions(consumed.snapshot(), WAR).orElseThrow();
            assertEquals(expected.finalAccepts(), options.whitePeace().finalAccepts(), name);
            var decision = OrdinaryWhitePeacePolicy.evaluate(immutable(consumed.snapshot()), WAR);
            assertEquals(expected.proposal(), decision.ready(), name);
            if (decision instanceof OrdinaryWhitePeacePolicy.Ready ready)
                assertEquals(expected.attacker() ? OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE
                        : OrdinaryWhitePeacePolicy.Variant.DEFENDER_DE_JURE, ready.variant(), name);
            assertEquals(expected.proposal(), WarExitCapabilities.steps(immutable(consumed.snapshot()), List.of(), CAPS)
                    .contains(new OperationKey("offer-white-peace-" + WAR)), name);
            assertEquals(immutable(consumed.snapshot()), DriverJson.object(
                    DriverJson.encode(immutable(consumed.snapshot())), DriverJson.MAX_NATIVE_BYTES), name);
        }
    }

    @Test void malformedFinalAnswersAndFullWarIdentityCannotPassTheActualReceiptDecoder() throws Exception {
        NativeRow original = corpus().get("attacker-status-0");
        ObjectNode baseline = original.top();
        for (String raw : List.of("true", "1.0", "3", "-1", "null", "\"1\"")) {
            NativeRow malformed = withStatusToken(original, raw);
            if (raw.equals("1.0")) {
                assertTrue(malformed.top().at("/result/war_termination_options/options/white_peace/recipient_response/decision_status_raw")
                        .isFloatingPointNumber(), "actual malformed TOP must retain its float token");
                assertTrue(ArmyJson.parse(resultToken(malformed.original()).bytes())
                        .at("/war_termination_options/options/white_peace/recipient_response/decision_status_raw")
                        .isFloatingPointNumber(), "original result token must retain the same float");
            }
            assertThrows(IllegalArgumentException.class, () -> consume(malformed), raw);
        }
        for (String field : List.of("status", "decision_status_raw", "would_accept_now")) {
            ObjectNode top = baseline.deepCopy();
            ((ObjectNode) top.at("/result/war_termination_options/options/white_peace/recipient_response")).remove(field);
            assertThrows(IllegalArgumentException.class, () -> consume(top), field);
        }
        ObjectNode contradiction = baseline.deepCopy();
        ((ObjectNode) contradiction.at("/result/war_termination_options/options/white_peace/recipient_response"))
                .put("status", "unavailable");
        assertThrows(IllegalArgumentException.class, () -> consume(contradiction));
        ObjectNode missing = baseline.deepCopy();
        ((ObjectNode) missing.at("/result/war_termination_options/options/white_peace")).putNull("recipient_response");
        assertThrows(IllegalArgumentException.class, () -> consume(missing));
        ObjectNode generation = baseline.deepCopy();
        ((ObjectNode) generation.at("/result/war_termination_options")).put("war_id", 50331651);
        assertThrows(IllegalArgumentException.class, () -> consume(generation));
    }


    @Test void actualFinalizedRolesSurvivePublicCacheSignaturesAndOrdinaryConsumers() throws Exception {
        Map<String, NativeRow> rows = contextCorpus();
        for (var entry : rows.entrySet()) {
            String name = entry.getKey(); NativeRow row = entry.getValue();
            Context source = roleContext(row);
            Consumed consumed = consume(row, source);
            int warId = row.top().at("/result/war_termination_options/war_id").intValue();
            JsonNode rawOptions = row.top().at("/result/war_termination_options/options");
            JsonNode originalOptions = ArmyJson.parse(consumed.originalWire().bytes()).at("/war_termination_options/options");
            JsonNode publicOptions = OpportunityJson.toNode(ArmyPublicWire.decodeExactSourceBound(consumed.publicWire(), source))
                    .at("/war_termination_options/options");
            ObjectNode cached = (ObjectNode) consumed.snapshot().path("war_termination_options").get(0);
            JsonNode cachedOptions = cached.path("options");
            var typed = NativeTerminationOptions.normalizeNativePacket(row.top().at("/result/war_termination_options"), warId);
            JsonNode signature = WarTerminationReadProjection.negativeSignature(typed).path("options");
            for (String option : List.of("surrender", "white_peace", "victory")) {
                JsonNode expected = rawOptions.path(option).get(NativeInteractionRoles.FIELD);
                NativeInteractionRoles decoded = NativeInteractionRoles.fromOption(rawOptions.path(option));
                assertJsonValueEquals(expected, originalOptions.path(option).get(NativeInteractionRoles.FIELD), name + "/original/" + option);
                assertJsonValueEquals(expected, publicOptions.path(option).get(NativeInteractionRoles.FIELD), name + "/public/" + option);
                assertJsonValueEquals(expected, cachedOptions.path(option).get(NativeInteractionRoles.FIELD), name + "/cache/" + option);
                assertJsonValueEquals(expected, signature.path(option).get(NativeInteractionRoles.FIELD), name + "/signature/" + option);
                assertEquals(decoded, NativeInteractionRoles.fromOption(cachedOptions.path(option)), name);
                if (decoded instanceof NativeInteractionRoles.Observed observed) {
                    int expectedActor = name.equals("zero-actor") ? 0 : name.equals("raiktor-projection-context") ? 29829 : ACTOR;
                    int expectedRecipient = switch (name) {
                        case "redirected-recipient" -> 43;
                        case "negative-recipient" -> -2147483643;
                        case "same-slot-new-generation" -> 67108906;
                        case "raiktor-projection-context" -> 17117;
                        case "distinct-three-option-tuples" -> option.equals("surrender") ? 43 : option.equals("victory") ? 44 : 42;
                        default -> 42;
                    };
                    assertEquals(NativeCharacterId.of(expectedActor), observed.actorCharacterId(), name);
                    assertEquals(NativeCharacterId.of(expectedRecipient), observed.recipientCharacterId(), name);
                    assertEquals(name.equals("intermediary-present") ? Optional.of(NativeCharacterId.of(45)) : Optional.empty(),
                            observed.intermediaryCharacterId(), name);
                } else {
                    var unknown = assertInstanceOf(NativeInteractionRoles.Unavailable.class, decoded, name);
                    assertEquals(switch (name) {
                        case "stale-generation-unresolved" -> NativeInteractionRoles.Reason.IDENTITY_UNRESOLVED;
                        case "answer-mutates-recipient" -> NativeInteractionRoles.Reason.ROLES_CHANGED;
                        case "unconstructed-context" -> NativeInteractionRoles.Reason.CONTEXT_NOT_CONSTRUCTED;
                        default -> throw new AssertionError("unexpected actual unknown " + name);
                    }, unknown.reason());
                }
            }
            var policyOptions = WarExitEvidence.currentOptions(consumed.snapshot(), warId).orElseThrow();
            assertEquals(NativeInteractionRoles.fromOption(rawOptions.path("white_peace")), policyOptions.whitePeace().recipientContext(), name);
            ObjectNode war = (ObjectNode) consumed.snapshot().path("active_wars").get(0);
            JsonNode conditions = OpportunityJson.toNode(NativeWarEndConditions.assess(immutable(war), immutable(cached)));
            JsonNode summary = OpportunityJson.toNode(NativeWarEndConditions.summaries(immutable(consumed.snapshot()), List.of(immutable(war))).getFirst());
            for (String option : List.of("surrender", "white_peace", "victory")) {
                JsonNode roles = rawOptions.path(option).get(NativeInteractionRoles.FIELD);
                assertJsonValueEquals(roles, conditions.at("/native_options/" + option).get(NativeInteractionRoles.FIELD), name);
                assertJsonValueEquals(roles, summary.at("/war_exit_assessment/eu_inputs/option_evidence/" + option).get(NativeInteractionRoles.FIELD), name);
            }
            boolean unknownRoles = policyOptions.whitePeace().recipientContext() instanceof NativeInteractionRoles.Unavailable;
            if (unknownRoles) {
                assertFalse(policyOptions.whitePeace().nativeLegal(), name);
                assertFalse(OrdinaryWhitePeacePolicy.evaluate(immutable(consumed.snapshot()), warId).ready(), name);
                // A defender still cannot turn an unknown v1 receiver into legacy positive-diagnostic permission.
                ObjectNode defender = consumed.snapshot().deepCopy();
                ((ObjectNode) defender.path("active_wars").get(0)).put("player_side", "defender");
                ((ObjectNode) defender.path("war_termination_options").get(0)).put("player_side", "defender");
                assertFalse(OrdinaryWhitePeacePolicy.evaluate(immutable(defender), warId).ready(), name + "/defender");
            }
            if (name.equals("defender-status-2-roles") || name.equals("defender-no-callback-roles"))
                assertTrue(OrdinaryWhitePeacePolicy.evaluate(immutable(consumed.snapshot()), warId).ready(), name + "/observed defender");
            if (name.equals("attacker-status-2-roles") || name.equals("attacker-status-3-roles") || name.equals("attacker-status-255-roles"))
                assertFalse(OrdinaryWhitePeacePolicy.evaluate(immutable(consumed.snapshot()), warId).ready(), name);
            archiveAndContinue(consumed);
        }
        assertNotEquals(WarTerminationReadProjection.negativeSignature(NativeTerminationOptions.normalizeNativePacket(
                        rows.get("attacker-status-0-roles").top().at("/result/war_termination_options"), WAR)),
                WarTerminationReadProjection.negativeSignature(NativeTerminationOptions.normalizeNativePacket(
                        rows.get("same-slot-new-generation").top().at("/result/war_termination_options"), WAR)),
                "same slot with another full generation must change the real negative signature");
        for (NativeRow old : corpus().values()) {
            Consumed consumed = consume(old);
            assertInstanceOf(NativeInteractionRoles.LegacyWithoutRoles.class,
                    WarExitEvidence.currentOptions(consumed.snapshot(), WAR).orElseThrow().whitePeace().recipientContext());
            assertFalse(ArmyJson.parse(consumed.originalWire().bytes()).at("/war_termination_options/options/white_peace")
                    .has(NativeInteractionRoles.FIELD), "legacy archives keep absence explicit");
            archiveAndContinue(consumed);
        }
    }

    @Test void actualContextCompanionCannotBeDowngradedOrLoseStrictTokenTypes() throws Exception {
        NativeRow original = contextCorpus().get("attacker-status-0-roles");
        String wire = new String(original.original().bytes(), StandardCharsets.UTF_8);
        for (String field : List.of("actor_character_id", "recipient_character_id", "intermediary_character_id", "reason", "schema_version", "state")) {
            ObjectNode top = original.top().deepCopy();
            ((ObjectNode) top.at("/result/war_termination_options/options/white_peace/" + NativeInteractionRoles.FIELD)).remove(field);
            assertThrows(IllegalArgumentException.class, () -> consume(top, new RawJson(ArmyJson.bytes(top)), roleContext(original)), field);
        }
        for (String token : List.of("true", "1.0", "-1", "null", "\"50331652\"", "2147483648")) {
            String changed = wire.replaceFirst("\"actor_character_id\":50331652", "\"actor_character_id\":" + token);
            assertNotEquals(wire, changed);
            RawJson raw = new RawJson(changed.getBytes(StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class,
                    () -> consume(new NativeRow(ArmyJson.parse(raw.bytes()), raw), roleContext(original)), token);
        }
        ObjectNode absent = original.top().deepCopy();
        ((ObjectNode) absent.at("/result/war_termination_options/options/white_peace")).remove(NativeInteractionRoles.FIELD);
        assertThrows(IllegalArgumentException.class, () -> consume(absent, new RawJson(ArmyJson.bytes(absent)), roleContext(original)), "mixed profile");
        ObjectNode explicitNull = original.top().deepCopy();
        ((ObjectNode) explicitNull.at("/result/war_termination_options/options/white_peace")).putNull(NativeInteractionRoles.FIELD);
        assertThrows(IllegalArgumentException.class, () -> consume(explicitNull, new RawJson(ArmyJson.bytes(explicitNull)), roleContext(original)), "explicit null");
        ObjectNode extra = original.top().deepCopy();
        ((ObjectNode) extra.at("/result/war_termination_options/options/white_peace/" + NativeInteractionRoles.FIELD)).put("primary_opponent", 42);
        assertThrows(IllegalArgumentException.class, () -> consume(extra, new RawJson(ArmyJson.bytes(extra)), roleContext(original)), "extra identity alias");
        ObjectNode unknownVersion = original.top().deepCopy();
        ((ObjectNode) unknownVersion.at("/result/war_termination_options/options/white_peace/" + NativeInteractionRoles.FIELD)).put("schema_version", 2);
        assertThrows(IllegalArgumentException.class, () -> consume(unknownVersion, new RawJson(ArmyJson.bytes(unknownVersion)), roleContext(original)));
    }


    @Test void actualRedirectedRaiktorQueryReachesProjectionResultCodecAndPersistedConsumer() throws Exception {
        NativeRow nativeRow = contextCorpus().get("raiktor-projection-context");
        Consumed consumed = consume(nativeRow, roleContext(nativeRow));
        JsonNode originalFixture;
        try (var resource = getClass().getResourceAsStream("/g2/m0/original-producer01.json.gz")) {
            assertNotNull(resource, "shared retained original outer producer input is required");
            try (var gzip = new GZIPInputStream(resource)) {
                byte[] bytes = gzip.readNBytes(StrictJson.EXPLICIT_MAX_BYTES + 1);
                assertTrue(bytes.length <= StrictJson.EXPLICIT_MAX_BYTES);
                originalFixture = StrictJson.parse(bytes, StrictJson.EXPLICIT_MAX_BYTES);
            }
        }
        JsonNode session = originalFixture.path("immediate_cases").get(0).path("request").get(1);
        // Only the outer terms fixture is authored software DATA, using the retained original six-domain values.
        // The Native19 query bytes and all three finalized role companions remain the actual generated bytes.
        ObjectNode termsQuery = ArmyJson.empty().put("accepted", true).put("status", "available")
                .put("queried_snapshot_id", "fixture-native:91").put("queried_revision", 91)
                .put("queried_native_revision", 7).put("queried_connection_generation", 12)
                .put("episode_run_id", "fixture-native-29829-episode");
        termsQuery.set("war_termination_terms", softwareRaiktorTerms());
        termsQuery.set("raiktor_surrender_aggregate_session", session);
        JsonNode optionsQuery = OpportunityJson.toNode(consumed.observed().normalizedResult());
        JsonNode produced = RaiktorWhitePeaceProjectionProducer.produce(consumed.snapshot(), optionsQuery, termsQuery, false);
        assertTrue(produced.path("observation_ready").booleanValue());
        assertFalse(produced.path("production_live").booleanValue());
        JsonNode actual = RaiktorRawOperations.validateResult(RaiktorRawOperations.Operation.WHITE, produced);
        JsonNode expectedRoles = nativeRow.top().at("/result/war_termination_options/options/white_peace/recipient_context_v1");
        assertJsonValueEquals(expectedRoles, actual.at("/white_peace_observation/option/recipient_context_v1"), "white-peace roles");
        assertJsonValueEquals(expectedRoles, actual.at("/white_peace_observation/option/same_frame_surrender/recipient_context_v1"), "surrender roles");
        assertEquals(17116, actual.at("/white_peace_observation/frame/primary_defender_character_id").intValue());
        assertEquals(17117, actual.at("/white_peace_observation/option/recipient_context_v1/recipient_character_id").intValue());
        DataReadArchive data = new DataReadArchive();
        ExactRef persisted = data.preserveMaterial(new RawJson(ArmyJson.bytes(actual)));
        JsonNode replay = RaiktorRawOperations.validateResult(RaiktorRawOperations.Operation.WHITE,
                ArmyJson.parse(data.loadMaterial(persisted).bytes()));
        assertJsonValueEquals(actual, replay, "persisted result");
        ObjectNode mixed = (ObjectNode) actual.deepCopy();
        ((ObjectNode) mixed.at("/white_peace_observation/option/same_frame_surrender")).remove(NativeInteractionRoles.FIELD);
        assertThrows(IllegalArgumentException.class,
                () -> RaiktorRawOperations.validateResult(RaiktorRawOperations.Operation.WHITE, mixed));

        ObjectNode observation = (ObjectNode) actual.path("white_peace_observation");
        assertJsonValueEquals(observation, RaiktorExitObservationCodec.normalizeObservation(observation).toJson(), "direct observation codec");
        String observationWire = new String(ArmyJson.bytes(observation), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "null", "-1", "\"17117\"")) {
            String changed = observationWire.replaceFirst("\"recipient_character_id\":17117", "\"recipient_character_id\":" + token);
            assertNotEquals(observationWire, changed);
            byte[] direct = ("{\"operation\":\"normalize-white-peace-observation\",\"value\":" + changed + "}").getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> RaiktorExitObservationCodec.execute(direct), token);
        }
        for (String field : NativeInteractionRoles.WIRE_FIELDS) {
            ObjectNode partial = observation.deepCopy();
            ((ObjectNode) partial.at("/option/recipient_context_v1")).remove(field);
            assertThrows(IllegalArgumentException.class, () -> RaiktorExitObservationCodec.normalizeObservation(partial), field);
        }
        ObjectNode extraContext = observation.deepCopy();
        ((ObjectNode) extraContext.at("/option/recipient_context_v1")).put("primary_opponent", 17116);
        assertThrows(IllegalArgumentException.class, () -> RaiktorExitObservationCodec.normalizeObservation(extraContext));
        ObjectNode nullContext = observation.deepCopy();
        ((ObjectNode) nullContext.path("option")).putNull(NativeInteractionRoles.FIELD);
        assertThrows(IllegalArgumentException.class, () -> RaiktorExitObservationCodec.normalizeObservation(nullContext));
        ObjectNode versionContext = observation.deepCopy();
        ((ObjectNode) versionContext.at("/option/recipient_context_v1")).put("schema_version", 2);
        assertThrows(IllegalArgumentException.class, () -> RaiktorExitObservationCodec.normalizeObservation(versionContext));
        ObjectNode unconstructed = observation.deepCopy();
        ((ObjectNode) unconstructed.path("option")).put("context_constructed", false);
        assertThrows(IllegalArgumentException.class, () -> RaiktorExitObservationCodec.normalizeObservation(unconstructed));
        ObjectNode impossibleAnswer = observation.deepCopy();
        ((ObjectNode) impossibleAnswer.path("option")).set(NativeInteractionRoles.FIELD, NativeInteractionRoles.toJson(
                new NativeInteractionRoles.Unavailable(NativeInteractionRoles.Reason.ROLES_CHANGED)));
        assertThrows(IllegalArgumentException.class, () -> RaiktorExitObservationCodec.normalizeObservation(impossibleAnswer));

        assertThrows(IllegalArgumentException.class,
                () -> RaiktorExitObservationCodec.normalizeObservation(mixed.path("white_peace_observation")));

    }

    private static ObjectNode softwareRaiktorTerms() {
        return (ObjectNode) StrictJson.parse("""
                {
                  "schema_version": 1,
                  "status": "available",
                  "war_id": 50331699,
                  "casus_belli": {
                    "database_index": 411,
                    "canonical_key": "raiktor_claim_cb"
                  },
                  "supported_slice": "raiktor_claim_cb_attacker_defeat_disposition",
                  "claimant_character_id": 41001,
                  "target_title_ids": [
                    1800
                  ],
                  "claims": [
                    {
                      "implicit": false,
                      "present": true,
                      "state": "strong_explicit",
                      "strong": true,
                      "title_id": 1800
                    }
                  ],
                  "attacker_defeat": {
                    "claim_disposition": "remove_declared_target_claims",
                    "declared_title_disposition": "unchanged"
                  },
                  "gold_reparations": {
                    "direction": "primary_attacker_to_primary_defender",
                    "factor": 3,
                    "positive_income_basis": "primary_attacker_yearly_income",
                    "fallback_condition": "landless_adventurer_or_nonpositive_monthly_income",
                    "fallback_basis": "primary_attacker_medium_gold_value",
                    "defender_culture_multiplier": "2_if_primary_defender_has_more_gold_for_successful_defensive_wars_else_1",
                    "actual_amount_observable": true,
                    "attacker_current_gold": {
                      "character_id": 29829,
                      "value": {
                        "raw": 35000000,
                        "scale": 100000
                      }
                    },
                    "defender_current_gold": {
                      "character_id": 17116,
                      "value": {
                        "raw": 80000000,
                        "scale": 100000
                      }
                    },
                    "attacker_authoritative_monthly_gold_income": {
                      "character_id": 29829,
                      "value": {
                        "raw": 500001,
                        "scale": 100000
                      }
                    },
                    "defender_authoritative_monthly_gold_income": {
                      "character_id": 17116,
                      "value": {
                        "raw": 800000,
                        "scale": 100000
                      }
                    },
                    "actual_transfer": {
                      "from_character_id": 29829,
                      "to_character_id": 17116,
                      "value": {
                        "raw": 15000000,
                        "scale": 100000
                      }
                    }
                  },
                  "attacker_fame": {
                    "resource": "prestige",
                    "base": "cb_prestige_factor",
                    "scale": -10,
                    "limit_rule": "loss_capped_at_1000",
                    "actual_delta_observable": true,
                    "attacker_current_prestige": {
                      "character_id": 29829,
                      "value": {
                        "raw": 12345678,
                        "scale": 100000
                      }
                    },
                    "cb_prestige_factor": {
                      "raw": 700000,
                      "scale": 100000
                    },
                    "attacker_prestige_delta": {
                      "character_id": 29829,
                      "value": {
                        "raw": -7000000,
                        "scale": 100000
                      }
                    }
                  },
                  "truce": {
                    "direction": "primary_attacker_toward_primary_defender",
                    "result": "defeat",
                    "evaluated_days_observable": true,
                    "evaluated_days": 1825,
                    "actual_expiry_observable": false,
                    "expiry_date_raw": null
                  },
                  "prisoner_release": {
                    "rule": "war_result_primary_and_first_three_heirs",
                    "actual_pairs_observable": true,
                    "attacker_participant_ids": [
                      29829,
                      30001
                    ],
                    "defender_participant_ids": [
                      17116
                    ],
                    "attacker_release_candidate_ids": [
                      29829,
                      30003
                    ],
                    "defender_release_candidate_ids": [
                      17116
                    ],
                    "release_pairs": [
                      {
                        "jailer_character_id": 17116,
                        "prisoner_character_id": 30003,
                        "reason": "opposite_primary_or_first_three_successors"
                      }
                    ],
                    "full_participant_scan": true,
                    "primary_and_first_three_successors_scanned": true
                  },
                  "conditional_favor_hook": {
                    "rule": "attacker_on_claimant_if_distinct_and_can_add_favor_hook",
                    "actual_applies_observable": true,
                    "claimant_distinct_from_attacker": true,
                    "original_visible_root_traversed": true,
                    "will_apply": true
                  },
                  "generic_war_bound_current": null,
                  "attacker_legitimacy_delta": {
                    "raw": 0,
                    "scale": 100000
                  },
                  "attacker_influence_delta": {
                    "raw": 0,
                    "scale": 100000
                  },
                  "hostages_allowed": false,
                  "unobserved_dynamic_effects": [
                    "actual_truce_expiry",
                    "targeting_faction_discontent_delta",
                    "glory_hound_vassal_opinion_rows",
                    "antagonistic_clan_vassal_opinion_rows",
                    "existing_house_feud_score_delta",
                    "attacker_mandala_piety_experience_delta",
                    "defender_mandala_serenity",
                    "defender_accolade_glory",
                    "laamp_actual_settlement_outside_cb_effect",
                    "war_bound_army_losses"
                  ],
                  "readiness": {
                    "identity_ready": true,
                    "targets_ready": true,
                    "claim_rows_ready": true,
                    "attacker_defeat_rule_ready": true,
                    "static_formula_ready": true,
                    "finance_ready": true,
                    "gold_ready": true,
                    "fame_factor_ready": true,
                    "attacker_prestige_delta_ready": true,
                    "truce_ready": true,
                    "prisoner_release_ready": true,
                    "favor_hook_ready": true,
                    "same_frame_stable": true,
                    "war_bound_armies_ready": false,
                    "dynamic_deltas_ready": false,
                    "decision_ready": false,
                    "automatic_surrender_ready": false,
                    "ready": false
                  },
                  "provenance": {
                    "game_version": "1.19.0.6",
                    "executable_sha256": "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
                    "native_reader": "CWar+0x270/+0x290;0x28B1AA0",
                    "present_claim_lifecycle": "present_only_vtable_slot_0_delete_flags_0",
                    "event_war_script_sha256": "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707",
                    "casus_belli_effects_script_sha256": "9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C",
                    "war_effects_script_sha256": "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D",
                    "war_interactions_script_sha256": "5C99B8F14893929A9BC2DBB5B258CDD2D4233D5805091952209413DE876EE09F",
                    "bookmark_events_script_sha256": "75CF485E379E522D4AAED9EF889FCC411A0D9DFCC28BCFB250ABDCC93A757EFF",
                    "truce_observer": "ck3-1.19.0.6-native-raiktor-surrender-truce-v1"
                  }
                }
                """.getBytes(StandardCharsets.UTF_8));
    }

    private static Context roleContext(NativeRow row) {
        boolean raiktor = row.top().path("request_id").textValue().equals("raiktor-projection-context");
        var source = new G2Source("software-native-query-no-game", "2026-10-26T00:00:00Z", "1.20.0.4",
                new ExactRef("actual-native-query-serializer-corpus/" + CONTEXT_RESOURCE, 48771, CONTEXT_SHA256));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(raiktor ? 29829 : ACTOR),
                BigInteger.valueOf(raiktor ? 7 : 3), BigInteger.valueOf(DATE)), raiktor ? "fixture-native:91" : "native:3",
                BigInteger.valueOf(raiktor ? 91 : 2), raiktor ? "fixture-native-29829-episode" : "software-native-query-corpus");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(raiktor ? 51268 : 42,
                new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "software-native-query-session",
                Instant.parse("2026-10-26T00:01:00Z"));
    }

    /** Source-bound DATA retention and pure original decoder replay, never SAVE or a new native query. */
    private static void archiveAndContinue(Consumed consumed) {
        PlanningReadReceipt original = consumed.receipt();
        ReadContract<ArmyWarReadCodec.Observation> contract = new ReadContract<>(original.contractId(), original.request().operation(),
                Optional.of("game.command.query-war-termination-options-N"), "software-native-corpus-read",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, consumed.context().source().sourceRef(),
                (request, id) -> { throw new AssertionError("pure replay must not prepare or send"); },
                receipt -> ArmyWarReadCodec.decode(consumed.scope(), receipt),
                receipt -> ArmyWarReadCodec.decode(consumed.scope(), receipt));
        RootReadContractCatalog catalog = RootReadContractCatalog.staticOnly(List.of(contract));
        DataReadArchive archive = new DataReadArchive();
        ExactRef receiptRef = archive.preserveRead(original);
        var known = new PlanningReadResult.Known<ArmyWarReadCodec.Observation>(consumed.observed(), original, receiptRef);
        var candidate = DriverReadHistoryRowProducer.prepare(archive, catalog, contract, known, 1);
        var decoded = DriverReadHistoryRowProducer.decode(candidate.row().encode());
        assertEquals(candidate.row(), decoded);
        assertEquals(consumed.observed().normalizedResult(), decoded.result());
        var nil = new DriverStateSnapshot.NullValue();
        var driver = new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-corpus-only",
                consumed.context().before().game().pid(), consumed.context().playerId(),
                consumed.context().before().frame().episodeRunId()), List.of(candidate.historyEntry()),
                nil, nil, nil, nil, nil, nil, nil);
        DriverStateSnapshot.Complete continued = DriverStateSnapshot.decodeComplete(driver.encode());
        assertEquals(driver, continued);
        var historical = DriverReadHistoryRowProducer.decode(continued.commandHistory().getFirst().originalRow().json());
        int writes = archive.materials.size();
        var replay = DriverReadHistoryRowProducer.replayCanonical(archive, catalog, contract, historical);
        assertEquals(consumed.observed(), replay.value());
        assertEquals(writes, archive.materials.size(), "continuation interprets original bytes without minting another observation");
    }

    /** Minimal in-memory original DATA store. It has no writer, effect, save or native transport authority. */
    private static final class DataReadArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,PlanningReadReceipt> reads = new HashMap<>();
        private final Map<ExactRef,RawJson> materials = new HashMap<>();
        public ExactRef preserveRead(PlanningReadReceipt value) {
            ExactRef ref = dataRef("read", value.original().originalPacket()); reads.put(ref, value); return ref;
        }
        public PlanningReadReceipt loadRead(ExactRef ref) { return required(reads, ref); }
        public ExactRef readReferenceOf(PlanningReadReceipt value) {
            ExactRef ref = dataRef("read", value.original().originalPacket()); assertEquals(value, loadRead(ref)); return ref;
        }
        public ExactRef preserveMaterial(RawJson value) { ExactRef ref = dataRef("material", value.bytes()); materials.put(ref, value); return ref; }
        public RawJson loadMaterial(ExactRef ref) { return required(materials, ref); }
        public ExactRef materialReferenceOf(RawJson value) {
            ExactRef ref = dataRef("material", value.bytes()); assertEquals(value, loadMaterial(ref)); return ref;
        }
        public ExactRef preserve(NativeActionPort.DispatchOutcome value) { throw unavailable(); }
        public NativeActionPort.DispatchOutcome load(ExactRef ref) { throw unavailable(); }
        public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { throw unavailable(); }
        public ExactRef preserveRequest(NativeRequest value) { throw unavailable(); }
        public NativeRequest loadRequest(ExactRef ref) { throw unavailable(); }
        public ExactRef requestReferenceOf(NativeRequest value) { throw unavailable(); }
        public ExactRef preserveRecord(ActionRecord value) { throw unavailable(); }
        public ActionRecord loadRecord(ExactRef ref) { throw unavailable(); }
        public ExactRef recordReferenceOf(ActionRecord value) { throw unavailable(); }
        public ExactRef preserveReceipt(ActionReceipt value) { throw unavailable(); }
        public ActionReceipt loadReceipt(ExactRef ref) { throw unavailable(); }
        public ExactRef receiptReferenceOf(ActionReceipt value) { throw unavailable(); }
        public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw unavailable(); }
        public byte[] loadNativeFrame(ExactRef ref) { throw unavailable(); }
        private static UnsupportedOperationException unavailable() { return new UnsupportedOperationException("read DATA only"); }
        private static <T> T required(Map<ExactRef,T> values, ExactRef ref) {
            T value = values.get(ref); assertNotNull(value, "original DATA is required"); return value;
        }
    }
    private static ExactRef dataRef(String role, byte[] bytes) {
        return new ExactRef("software-native-corpus/" + role + "/" + DriverJson.sha256(bytes), bytes.length, DriverJson.sha256(bytes));
    }
    private static Map<String,NativeRow> contextCorpus() throws Exception {
        byte[] bytes;
        try (var input = ArmyNativeTerminationRecipientTest.class.getResourceAsStream(CONTEXT_RESOURCE)) {
            assertNotNull(input, "real query/shared serializer context corpus required"); bytes = input.readAllBytes();
        }
        assertEquals(48771, bytes.length);
        assertEquals(CONTEXT_SHA256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        Map<String,NativeRow> rows = new LinkedHashMap<>();
        for (String line : new String(bytes, StandardCharsets.UTF_8).lines().toList()) {
            RawJson raw = new RawJson(line.getBytes(StandardCharsets.UTF_8));
            ObjectNode top = ArmyJson.parse(raw.bytes());
            String name = StrictJson.text(top.get("request_id"));
            assertNull(rows.put(name, new NativeRow(top, raw)), "duplicate original context case");
            assertEquals(17, top.at("/result/query_sequence").intValue());
            int war = top.at("/result/war_termination_options/war_id").intValue();
            assertEquals("query-war-termination-options-" + war, top.at("/result/step").textValue());
        }
        assertEquals(19, rows.size());
        return rows;
    }

    private record NativeRow(ObjectNode top, RawJson original) { }
    private record Consumed(ArmyWarReadCodec.Options observed, RawJson originalWire, RawJson publicWire,
            ObjectNode snapshot, Context context, ArmyWarReadCodec.Scope scope, PlanningReadReceipt receipt) { }
    private static Consumed consume(NativeRow row) { return consume(row.top(), row.original()); }
    private static Consumed consume(ObjectNode top) { return consume(top, new RawJson(ArmyJson.bytes(top))); }
    private static Consumed consume(ObjectNode top, RawJson originalTop) { return consume(top, originalTop, context()); }
    private static Consumed consume(NativeRow row, Context context) { return consume(row.top(), row.original(), context); }
    private static Consumed consume(ObjectNode top, RawJson originalTop, Context context) {
        ObjectNode snapshot = snapshot(top, context);
        int warId = top.at("/result/war_termination_options/war_id").intValue();
        var call = new ArmyCalls.War(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,
                new ArmyCalls.Revision(new Present<>(context.before().frame().revision())), BigInteger.valueOf(warId));
        var args = DriverJson.object(ArmyCallCodec.encode(call).bytes(), DriverJson.MAX_NATIVE_BYTES);
        assertEquals(call, ArmyCallCodec.decode(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS, ArmyCallCodec.encode(call)));
        var request = new PlanningReadRequest(context.before(), context.source(), context.sessionId(),
                new OperationKey("query-war-termination-options-" + warId), args, context.deadline());
        var receipt = receipt(request, "software-native-query-corpus", top, originalTop);
        var scope = new ArmyWarReadCodec.Scope(call, context, immutable(snapshot), Optional.empty());
        var observed = assertInstanceOf(ArmyWarReadCodec.Options.class, ArmyWarReadCodec.decode(scope, receipt));
        RawJson original = ArmyWarOriginalResultCodec.encode(scope, receipt, observed);
        RawJson publicResult = ArmyWarPublicResultCodec.encode(scope, receipt, observed, Optional.empty());

        // Use the existing real options cache producer; do not hand-copy frame binding fields.
        var planning = new PlanningRequest(context.before(), context.source(), context.sessionId(), context.deadline(),
                new PlanningObservation(immutable(snapshot), List.of(), Set.of(), CAPS, Optional.empty(),
                        List.of(), Optional.empty(), Optional.empty(), false));
        var registered = WarExitReads.contractsFor(planning, context.source().sourceRef()).stream()
                .filter(item -> item.key().kind() == WarExitReads.Kind.OPTIONS).findFirst().orElseThrow();
        var cacheRequest = new PlanningReadRequest(context.before(), context.source(), context.sessionId(),
                registered.contract().operation(), immutable(ArmyJson.empty()), context.deadline());
        registered.contract().prepare(cacheRequest, top.path("request_id").textValue());
        var cacheQuery = registered.contract().decode(receipt(cacheRequest, registered.contract().contractId(), top, originalTop));
        snapshot.putArray("war_termination_options").add(cacheQuery.envelope().get("war_termination_options"));
        return new Consumed(observed, original, publicResult, snapshot, context, scope, receipt);
    }
    private static PlanningReadReceipt receipt(PlanningReadRequest request, String contract, ObjectNode top, RawJson originalTop) {
        var guard = new PlanningReadGuard(new GuardEvidence(request.before(), request.source(), request.sessionId(),
                request.before().frame().identity().player().intValue() == 29829 ? BigInteger.valueOf(12) : BigInteger.ONE, request.operation(), request.source().sourceRef(), request.source().sourceRef(),
                "software-native-query-corpus", Instant.parse("2026-10-26T00:00:00Z"), request.deadline()),
                true, true, true, "b".repeat(64));
        RawJson raw = originalTop;
        var ack = new NativeActionPort.AckReceived(top.path("request_id").textValue(), true,
                Optional.of(resultToken(raw)), raw, ArmyOriginalPacketFixture.packet(raw));
        return new PlanningReadReceipt(request, contract, top.path("request_id").textValue(), guard, guard, ack);
    }
    private static NativeRow withStatusToken(NativeRow original, String replacement) {
        String wire = new String(original.original().bytes(), StandardCharsets.UTF_8);
        int white = wire.indexOf("\"white_peace\":{");
        assertTrue(white >= 0, "actual shared serializer white-peace object required");
        String field = "\"decision_status_raw\":";
        int fieldAt = wire.indexOf(field, white);
        assertTrue(fieldAt > white, "actual shared serializer answer token required");
        int tokenAt = fieldAt + field.length();
        assertEquals('0', wire.charAt(tokenAt), "mutate only the original status-0 case");
        assertEquals(',', wire.charAt(tokenAt + 1), "original answer must be the complete integer token");
        RawJson malformed = new RawJson((wire.substring(0, tokenAt) + replacement + wire.substring(tokenAt + 1))
                .getBytes(StandardCharsets.UTF_8));
        return new NativeRow(ArmyJson.parse(malformed.bytes()), malformed);
    }
    /** The actual shared C++ frame writes result last. Preserve that token's bytes, including 1.0.
     * Tree re-encoding here would normalize DecimalNode(1.0) to the integer wire token 1. */
    private static RawJson resultToken(RawJson frame) {
        String wire = new String(frame.bytes(), StandardCharsets.UTF_8);
        String field = "\"result\":";
        int start = wire.indexOf(field);
        int outerEnd = wire.lastIndexOf('}');
        assertTrue(start >= 0 && outerEnd > start + field.length(), "actual result-last C++ frame required");
        RawJson result = new RawJson(wire.substring(start + field.length(), outerEnd).getBytes(StandardCharsets.UTF_8));
        assertEquals(ArmyJson.parse(frame.bytes()).get("result"), ArmyJson.parse(result.bytes()),
                "preserved result token must be the exact original field");
        return result;
    }
    private static ObjectNode snapshot(ObjectNode top) { return snapshot(top, context()); }
    private static ObjectNode snapshot(ObjectNode top, Context context) {
        ObjectNode packet = (ObjectNode) top.at("/result/war_termination_options");
        var frame = context.before().frame();
        ObjectNode snapshot = ArmyJson.empty().put("snapshot_id", frame.snapshotId()).put("revision", frame.revision())
                .put("native_revision", frame.identity().nativeRevision()).put("date_raw", frame.identity().dateRaw())
                .put("episode_run_id", frame.episodeRunId()).put("episode_character_id", frame.identity().player())
                .put("paused", true).put("map_ready", true);
        snapshot.putObject("played_character").put("character_id", frame.identity().player()).put("alive", true);
        snapshot.putObject("diagnostics").put("connection_generation", frame.identity().player().intValue() == 29829 ? 12 : 1).put("bridge_pid", context.before().game().pid());
        ObjectNode war = snapshot.putArray("active_wars").addObject();
        for (String field : List.of("war_id", "player_side", "player_is_primary_war_leader", "player_relative_war_score"))
            war.set(field, packet.get(field));
        war.put("primary_opponent_character_id", frame.identity().player().intValue() == 29829 ? 17116 : 42);
        // Target title is an authored outer observation, never attributed to the native options query.
        war.putArray("targeted_title_ids").add(frame.identity().player().intValue() == 29829 ? 1800 : 101);
        snapshot.putArray("player_armies"); snapshot.putArray("war_termination_options");
        snapshot.putArray("war_termination_terms");
        snapshot.putArray("war_termination_exit_terms");
        return snapshot;
    }
    private static Context context() {
        var source = new G2Source("software-native-query-no-game", "2026-10-26T00:00:00Z", "1.20.0.4",
                new ExactRef("actual-native-query-serializer-corpus/" + RESOURCE, 18501, CORPUS_SHA256));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(ACTOR),
                BigInteger.valueOf(3), BigInteger.valueOf(DATE)), "native:3", BigInteger.TWO, "software-native-query-corpus");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42,
                new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "software-native-query-session",
                Instant.parse("2026-10-26T00:01:00Z"));
    }
    private static Map<String, NativeRow> corpus() throws Exception {
        byte[] bytes;
        try (var input = ArmyNativeTerminationRecipientTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(input, "actual Native fixture corpus is required"); bytes = input.readAllBytes();
        }
        assertTrue(bytes.length > 0 && bytes.length <= 32768, "bounded actual Native corpus");
        assertEquals(CORPUS_SHA256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        Map<String, NativeRow> rows = new LinkedHashMap<>();
        for (String line : new String(bytes, StandardCharsets.UTF_8).lines().toList()) {
            assertFalse(line.isBlank()); ObjectNode top = (ObjectNode) StrictJson.parse(line.getBytes(StandardCharsets.UTF_8));
            String name = StrictJson.text(top.get("request_id"));
            assertNull(rows.put(name, new NativeRow(top, new RawJson(line.getBytes(StandardCharsets.UTF_8)))), "duplicate original Native case");
            assertEquals(17, top.path("result").path("query_sequence").intValue(), name);
            assertEquals("query-war-termination-options-" + WAR, top.path("result").path("step").textValue(), name);
        }
        assertEquals(EXPECTED.keySet(), rows.keySet()); return rows;
    }
    private static OpportunityJson.Obj immutable(ObjectNode value) {
        return DriverJson.object(ArmyJson.bytes(value), DriverJson.MAX_NATIVE_BYTES);
    }
}

