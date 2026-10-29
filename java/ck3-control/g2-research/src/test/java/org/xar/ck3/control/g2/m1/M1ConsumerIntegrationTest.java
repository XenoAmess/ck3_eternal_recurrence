package org.xar.ck3.control.g2.m1;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.planning.campaigncadence.MonthlyObservation;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipCodec;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult;
import org.xar.ck3.control.wave3.planning.realmmembership.RealmMembershipFeedback;

/** Real captured Python producer -> Java API -> typed response consumer, with source-bound resources. */
final class M1ConsumerIntegrationTest {

    @Test void signedMonthlyRolesTraverseEngineWireAndTypedConsumer() throws Exception {
        for (String role : List.of("actor", "episode", "founder", "opponent")) {
            for (int identity : new int[] {-2, 0, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
                ObjectNode input = monthlyRoleInput();
                setMonthlyInputRole(input, role, StrictJson.object().put("value", identity).get("value"));
                G2Response response = monthlyEngine(input);
                MonthlyObservation copied = M1ResultConsumers.monthlyObservation(response.result().bytes()).orElseThrow();
                BigInteger actual = switch (role) {
                    case "actor" -> copied.frame().actorCharacterId();
                    case "episode" -> copied.frame().episodeCharacterId();
                    case "founder" -> copied.campaignAnchor().founderCharacterId();
                    case "opponent" -> copied.observedPlayerWars().getFirst().primaryOpponentCharacterId();
                    default -> throw new IllegalArgumentException(role);
                };
                assertEquals(BigInteger.valueOf(identity), actual, role);
                assertEquals(parse(response.result().bytes()), parse(write(copied.toJson())));
                assertFalse(copied.toJson().get("score_or_complete_history_claimed").booleanValue());
                assertEquals(0, copied.toJson().get("new_RPC_calls").intValue());
            }
        }
    }

    @Test void invalidMonthlyRolesRejectProducerAndTypedImport() throws Exception {
        for (String role : List.of("actor", "episode", "founder", "opponent")) {
            ObjectNode good = monthlyRoleInput();
            setMonthlyInputRole(good, role, parse(utf8("17")));
            ObjectNode original = (ObjectNode) parse(monthlyEngine(good).result().bytes());
            for (String token : List.of("2147483648", "4294967294", "4294967295", "-1", "-2147483649", "true", "0.0", "\"0\"")) {
                JsonNode invalid = parse(utf8(token));
                ObjectNode input = monthlyRoleInput();
                setMonthlyInputRole(input, role, invalid);
                assertThrows(IllegalArgumentException.class, () -> monthlyEngine(input), role + ":" + token);
                ObjectNode recorded = original.deepCopy();
                setMonthlyOutputRole(recorded, role, invalid);
                assertThrows(IllegalArgumentException.class,
                        () -> M1ResultConsumers.monthlyObservation(write(recorded)), role + ":" + token);
            }
        }
    }

    @Test void monthlyRoleCorrectionPreservesOtherIdsNullsAndNonBoundary() throws Exception {
        ObjectNode input = monthlyRoleInput();
        BigInteger maximum = new BigInteger("4294967295");
        ((ObjectNode) input.get("campaign_anchor")).put("founding_house_id", maximum).put("founding_dynasty_id", maximum);
        setMonthlyInputRole(input, "opponent", parse(utf8("17")));
        MonthlyObservation copied = M1ResultConsumers.monthlyObservation(monthlyEngine(input).result().bytes()).orElseThrow();
        assertEquals(maximum, copied.campaignAnchor().foundingHouseId());
        assertEquals(maximum, copied.campaignAnchor().foundingDynastyId());
        assertEquals(maximum, copied.observedPlayerWars().getFirst().warId());
        for (String nonCharacter : List.of("founding_house_id", "founding_dynasty_id", "war_id")) {
            ObjectNode zero = input.deepCopy();
            if (nonCharacter.equals("war_id")) {
                ((ObjectNode) zero.path("snapshot").path("active_wars").get(0)).put(nonCharacter, 0);
            } else ((ObjectNode) zero.get("campaign_anchor")).put(nonCharacter, 0);
            assertThrows(IllegalArgumentException.class, () -> monthlyEngine(zero), nonCharacter);
        }
        for (boolean missing : new boolean[] {false, true}) {
            ObjectNode optional = input.deepCopy();
            ObjectNode snapshot = (ObjectNode) optional.get("snapshot");
            ObjectNode player = (ObjectNode) snapshot.get("played_character");
            ObjectNode war = (ObjectNode) snapshot.path("active_wars").get(0);
            if (missing) {
                snapshot.remove("episode_character_id"); player.remove("character_id"); war.remove("primary_opponent_character_id");
            } else {
                snapshot.putNull("episode_character_id"); player.putNull("character_id"); war.putNull("primary_opponent_character_id");
            }
            MonthlyObservation absent = M1ResultConsumers.monthlyObservation(monthlyEngine(optional).result().bytes()).orElseThrow();
            assertNull(absent.frame().actorCharacterId()); assertNull(absent.frame().episodeCharacterId());
            assertNull(absent.observedPlayerWars().getFirst().primaryOpponentCharacterId());
        }
        ObjectNode nonBoundary = input.deepCopy();
        ObjectNode snapshot = (ObjectNode) nonBoundary.get("snapshot");
        snapshot.put("date_raw", snapshot.get("date_raw").intValue() + 1);
        ((ObjectNode) snapshot.get("played_character")).put("character_id", -1);
        ((ObjectNode) nonBoundary.get("campaign_anchor")).put("founder_character_id", true);
        assertTrue(M1ResultConsumers.monthlyObservation(monthlyEngine(nonBoundary).result().bytes()).isEmpty());
    }

    private static ObjectNode monthlyRoleInput() throws Exception {
        JsonNode golden = parse(resource("monthly-observation.json",
                "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae"));
        for (JsonNode row : golden.path("cases")) {
            if (row.path("id").asText().equals("sample-baseline")) return ((ObjectNode) row.get("request")).deepCopy();
        }
        throw new IOException("original exact-slot template missing");
    }

    private static void setMonthlyInputRole(ObjectNode input, String role, JsonNode value) {
        ObjectNode snapshot = (ObjectNode) input.get("snapshot");
        switch (role) {
            case "actor" -> ((ObjectNode) snapshot.get("played_character")).set("character_id", value);
            case "episode" -> snapshot.set("episode_character_id", value);
            case "founder" -> ((ObjectNode) input.get("campaign_anchor")).set("founder_character_id", value);
            case "opponent" -> snapshot.putArray("active_wars").addObject().put("war_id", 4_294_967_295L)
                    .put("player_side", "attacker").put("player_relative_war_score", 0).set("primary_opponent_character_id", value);
            default -> throw new IllegalArgumentException(role);
        }
    }

    private static void setMonthlyOutputRole(ObjectNode output, String role, JsonNode value) {
        switch (role) {
            case "actor", "episode" -> {
                String field = role.equals("actor") ? "actor_character_id" : "episode_character_id";
                ((ObjectNode) output.get("frame")).set(field, value);
                ((ObjectNode) output.path("sources").get(0).get("binding")).set(field, value);
            }
            case "founder" -> ((ObjectNode) output.get("campaign_anchor")).set("founder_character_id", value);
            case "opponent" -> ((ObjectNode) output.path("observed_player_wars").get(0)).set("primary_opponent_character_id", value);
            default -> throw new IllegalArgumentException(role);
        }
    }

    private static G2Response monthlyEngine(ObjectNode input) throws Exception {
        byte[] payload = wrapper("monthly-observation", write(input));
        String digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload));
        G2Source software = new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-29T16:30:00Z",
                "software-m1-character-domain", new ExactRef("memory:m1-character-domain", payload.length, digest));
        G2Request supplied = new G2Request("m1-character-domain", Milestone.M1, software,
                ProjectionJson.object(payload, M1Research.MAX_BYTES));
        G2Request decoded = G2Wire.decodeRequest(G2Wire.encodeRequest(supplied));
        assertArrayEquals(payload, decoded.payload().bytes());
        G2Response response = new G2ResearchEngine(List.of(new M1Research())).evaluate(decoded);
        G2Response consumed = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertEquals(software, consumed.source()); assertEquals(supplied.requestId(), consumed.requestId());
        assertArrayEquals(response.result().bytes(), consumed.result().bytes());
        return consumed;
    }

    @Test void allOriginalMembershipCapturesReachTypedConsumerWithoutPromotingUnknownSets() throws Exception {
        List<String> lines = new String(resource("saved-membership.jsonl",
                "da6297b603c7f2388b350eb8214a66911ba7761fff642d5e3a3de3145bea9e96"), StandardCharsets.UTF_8).lines().toList();
        JsonNode header = parse(utf8(lines.getFirst()));
        assertEquals(11, header.path("original_tests_run").intValue());
        assertEquals(0, header.path("original_skips").intValue());
        assertEquals(34, header.path("unique_vector_count").intValue());
        assertEquals(35, lines.size());
        boolean complete = false, incomplete = false, explicitEmpty = false;
        for (String line : lines.subList(1, lines.size())) {
            JsonNode vector = parse(utf8(line));
            byte[] original = utf8(vector.path("input_json").textValue());
            byte[] before = original.clone();
            M1ProducerApi.SavedProjection projected = M1ProducerApi.savedMembership(original);
            SavedMembershipResult consumed = M1ResultConsumers.savedMembership(projected.wireJson());
            assertEquals(vector.get("expected"), parse(projected.wireJson()), vector.path("ordinal").asText());
            assertEquals(projected.result(), consumed);
            assertEquals(vector.get("expected"), parse(SavedMembershipCodec.encode(consumed)));
            assertArrayEquals(before, original);
            complete |= consumed.realm().complete();
            incomplete |= !consumed.realm().complete();
            explicitEmpty |= consumed.realm().complete() && consumed.realm().known().isEmpty();
            if (!consumed.realm().complete()) {
                assertFalse(consumed.titleCensusComplete() && consumed.realm().unknown().isEmpty()
                        && consumed.realm().countUpper().isPresent() && consumed.realm().countUpper().getAsInt() == 0);
            }
        }
        assertTrue(complete); assertTrue(incomplete); assertTrue(explicitEmpty);
    }

    @Test void completeRealmFeedbackAndEveryCapturedRejectionReachConsumerWithOriginalFrames() throws Exception {
        JsonNode golden = realmGolden();
        assertEquals(29, golden.path("cases").size());
        int parity = 0, stricterBoundary = 0;
        for (JsonNode vector : golden.path("cases")) {
            String name = vector.path("name").textValue();
            ObjectNode input = materialize(golden, vector);
            byte[] raw = write(input);
            RealmMembershipFeedback.Result producer = assertDoesNotThrow(() -> M1ProducerApi.realmFeedback(raw), name);
            M1ResultConsumers.DecodedFeedback decoded = M1ResultConsumers.realmFeedback(producer.wireJson());
            if (name.equals("nonobject-binding-keeps-original-envelope-semantics")) {
                assertEquals("available", vector.path("expected").path("status").textValue());
                assertEquals("faction_result_binding_invalid",
                        assertInstanceOf(M1ResultConsumers.UnavailableFeedback.class, decoded).reason());
                stricterBoundary++;
            } else {
                assertEquals(vector.get("expected"), parse(producer.wireJson()), name);
                parity++;
            }
            if (producer instanceof RealmMembershipFeedback.VerifiedFeedback verified) {
                var consumed = assertInstanceOf(M1ResultConsumers.AvailableFeedback.class, decoded);
                assertEquals(verified.observation(), consumed.observation());
                assertEquals(verified.difference(), consumed.difference());
                assertEquals(verified.realmCountyCount(), consumed.observation().component().countyTitleIds().size());
                assertEquals(verified.difference(), M1ResultConsumers.nativeDifference(write(verified.difference().toJson())));
            } else {
                assertInstanceOf(M1ResultConsumers.UnavailableFeedback.class, decoded);
            }
            assertArrayEquals(raw, write(input), name);
        }
        assertEquals(28, parity); assertEquals(1, stricterBoundary);
        var empty = assertInstanceOf(M1ResultConsumers.AvailableFeedback.class,
                M1ResultConsumers.realmFeedback(M1ProducerApi.realmFeedback(write(golden.path("bases").path("zero"))).wireJson()));
        assertTrue(empty.observation().component().countyTitleIds().isEmpty());
        var unknown = assertInstanceOf(M1ResultConsumers.UnavailableFeedback.class,
                M1ResultConsumers.realmFeedback(M1ProducerApi.realmFeedback(utf8("{\"snapshot\":{}}")).wireJson()));
        assertFalse(unknown.reason().isEmpty());
    }

    @Test void everyActualMonthlyCandidateKeepsExactSlotNullEmptyWarsAndDecimalWallet() throws Exception {
        JsonNode golden = parse(resource("monthly-observation.json",
                "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae"));
        int captured = 0, rejected = 0;
        boolean absentSlot = false, negativeWallet = false, unknownWars = false, emptyWars = false;
        for (JsonNode vector : golden.path("cases")) {
            JsonNode request = vector.get("request");
            if (!request.path("operation").textValue().equals("ordinary_sample_candidate")) { continue; }
            captured++;
            byte[] raw = write(request);
            if (vector.path("expected").path("status").textValue().equals("rejected")) {
                assertThrows(IllegalArgumentException.class, () -> M1ProducerApi.monthlyObservation(raw));
                rejected++; continue;
            }
            M1ProducerApi.MonthlyProjection producer = M1ProducerApi.monthlyObservation(raw);
            Optional<MonthlyObservation> decoded = M1ResultConsumers.monthlyObservation(producer.wireJson());
            assertEquals(producer.observation(), decoded);
            assertEquals(vector.path("expected").get("value"), parse(producer.wireJson()), vector.path("id").asText());
            assertArrayEquals(raw, write(request));
            absentSlot |= decoded.isEmpty();
            if (decoded.isPresent()) {
                MonthlyObservation observation = decoded.orElseThrow();
                negativeWallet |= observation.observedGold() != null && observation.observedGold().startsWith("-");
                unknownWars |= observation.observedPlayerWars() == null;
                emptyWars |= observation.observedPlayerWars() != null && observation.observedPlayerWars().isEmpty();
                assertEquals(request.path("campaign_anchor"), parse(write(observation.campaignAnchor().toJson())));
            }
        }
        assertEquals(8, captured); assertEquals(1, rejected);
        assertTrue(absentSlot); assertTrue(negativeWallet); assertTrue(unknownWars); assertTrue(emptyWars);
    }

    @Test void allOriginalDatedPlannerSummariesRetainHistoricalUnknownAndBoundedLossSemantics() throws Exception {
        JsonNode golden = parse(resource("dated-summary.json", "7bc6d62177f58fe3f7763d302cfab9d739f7821ae37937485bd088d5622418fc"));
        assertEquals(7, golden.path("original_test_count").intValue());
        assertEquals(0, golden.path("original_test_skipped").intValue());
        assertEquals(12, golden.path("cases").size());
        for (JsonNode row : golden.path("cases")) {
            G2Response response = evaluate("dated-summary", write(row.get("request")));
            assertEquals(row.path("expected").get("value"), parse(response.result().bytes()), row.path("id").asText());
            var summary = M1ResultConsumers.datedSummary(response.result().bytes());
            if (row.path("expected").path("value").path("status").asText().equals("unavailable")) {
                assertEquals(M1ResultConsumers.NoQualifiedSummary.INSTANCE, summary);
            } else {
                var retained = assertInstanceOf(M1ResultConsumers.RetainedSummary.class, summary);
                assertEquals(row.path("expected").path("value").path("last_observed_realm_county_count").intValue(), retained.lastObservedCount());
                if (row.path("id").asText().equals("long-loss")) {
                    assertEquals(12, retained.loss().orElseThrow().lostCount());
                    assertEquals(8, retained.loss().orElseThrow().firstEightLost().size());
                    assertTrue(retained.loss().orElseThrow().truncated());
                }
            }
        }
    }

    @Test void realResponseBoundariesRejectWrongFieldsTypesAndMissingValues() throws Exception {
        List<String> savedLines = new String(resource("saved-membership.jsonl",
                "da6297b603c7f2388b350eb8214a66911ba7761fff642d5e3a3de3145bea9e96"), StandardCharsets.UTF_8).lines().toList();
        JsonNode vector = parse(utf8(savedLines.get(1)));
        ObjectNode saved = (ObjectNode) parse(M1ProducerApi.savedMembership(utf8(vector.path("input_json").textValue())).wireJson());
        ObjectNode missing = saved.deepCopy(); missing.remove("date");
        assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.savedMembership(write(missing)));
        for (String token : List.of("true", "1.0", "\"1\"")) {
            ObjectNode wrong = saved.deepCopy(); wrong.set("actor_id", parse(utf8(token)));
            assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.savedMembership(write(wrong)));
        }
        ObjectNode feedback = (ObjectNode) parse(M1ProducerApi.realmFeedback(write(realmGolden().path("bases").path("first"))).wireJson());
        ObjectNode missingObservation = feedback.deepCopy(); missingObservation.remove("observation");
        assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.realmFeedback(write(missingObservation)));
        ObjectNode zeroFromUnknown = (ObjectNode) parse(M1ProducerApi.realmFeedback(utf8("{\"snapshot\":{}}")).wireJson());
        ((ObjectNode) zeroFromUnknown.path("raw_metrics").path("realm_county_count")).put("value", "0");
        assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.realmFeedback(write(zeroFromUnknown)));
        ObjectNode month = firstMonth();
        for (String token : List.of("true", "1.0", "\"1\"")) {
            ObjectNode wrong = month.deepCopy();
            ((ObjectNode) wrong.get("frame")).set("revision", parse(utf8(token)));
            assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.monthlyObservation(write(wrong)));
        }
        ObjectNode absentWars = month.deepCopy(); absentWars.remove("observed_player_wars");
        assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.monthlyObservation(write(absentWars)));
        assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.nativeDifference(
                utf8("{\"status\":\"unavailable\",\"lost_county_title_ids\":[],\"gained_county_title_ids\":null,\"unavailable_reason\":\"unknown\"}")));
        assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.monthlyObservation(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> M1ResultConsumers.realmFeedback(utf8("{\"schema\":1,\"schema\":2}")));
    }

    @Test void sourceFrameExtensionDecimalsAndUint64RevisionsRetainExactJsonTokens() throws Exception {
        ObjectNode input = (ObjectNode) realmGolden().path("bases").path("first").deepCopy();
        ObjectNode source = (ObjectNode) input.get("source_frame");
        source.set("sdk_extension", parse(utf8("1.0")));
        var produced = assertInstanceOf(RealmMembershipFeedback.VerifiedFeedback.class, M1ProducerApi.realmFeedback(write(input)));
        var consumed = assertInstanceOf(M1ResultConsumers.AvailableFeedback.class, M1ResultConsumers.realmFeedback(produced.wireJson()));
        assertTrue(consumed.observation().sourceFrame().get("sdk_extension").isFloatingPointNumber());
        assertEquals(source.get("sdk_extension"), consumed.observation().sourceFrame().get("sdk_extension"));
        ObjectNode observation = (ObjectNode) parse(produced.wireJson()).get("observation");
        BigInteger exact = new BigInteger("9007199254740993");
        ((ObjectNode) observation.get("source_frame")).put("revision", exact);
        assertEquals(exact, org.xar.ck3.control.wave2.planning.realmcompare.RealmObservation.parse(observation).frame().revision());
    }

    @Test void originalProducersReachResearchAndCommonWireWithEveryConsumerRoute() throws Exception {
        JsonNode realm = realmGolden();
        byte[] realmInput = write(realm.path("bases").path("first"));
        G2Response feedback = evaluate("realm-feedback", realmInput);
        assertArrayEquals(M1ProducerApi.realmFeedback(realmInput).wireJson(), feedback.result().bytes());
        var nativeResult = assertInstanceOf(M1ResultConsumers.AvailableFeedback.class,
                M1ResultConsumers.realmFeedback(feedback.result().bytes()));
        JsonNode nativeWire = parse(feedback.result().bytes()).get("observation");
        ObjectNode nativePair = StrictJson.object(); nativePair.set("cached", nativeWire); nativePair.set("current", nativeWire);
        assertEquals(M1RealmComparisons.CacheStatus.CURRENT,
                M1ResultConsumers.cache(evaluate("native-cache", write(nativePair)).result().bytes()));
        ObjectNode difference = StrictJson.object(); difference.putNull("previous"); difference.set("observation", nativeWire);
        assertInstanceOf(org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference.Unavailable.class,
                M1ResultConsumers.nativeDifference(evaluate("native-difference", write(difference)).result().bytes()));
        assertEquals(3, nativeResult.observation().component().countyTitleIds().size());

        JsonNode monthly = parse(resource("monthly-observation.json",
                "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae"));
        JsonNode monthInput = null;
        for (JsonNode row : monthly.path("cases")) {
            if (row.path("id").asText().equals("sample-baseline")) { monthInput = row.get("request"); break; }
        }
        assertNotNull(monthInput);
        G2Response month = evaluate("monthly-observation", write(monthInput));
        assertTrue(M1ResultConsumers.monthlyObservation(month.result().bytes()).isPresent());
        ObjectNode monthlyPair = StrictJson.object(); monthlyPair.set("cached", monthInput); monthlyPair.set("current", monthInput);
        assertEquals(M1RealmComparisons.CacheStatus.CURRENT,
                M1ResultConsumers.cache(evaluate("monthly-cache", write(monthlyPair)).result().bytes()));

        List<String> lines = new String(resource("saved-membership.jsonl",
                "da6297b603c7f2388b350eb8214a66911ba7761fff642d5e3a3de3145bea9e96"), StandardCharsets.UTF_8).lines().toList();
        byte[] savedInput = utf8(parse(utf8(lines.get(1))).path("input_json").textValue());
        var saved = M1ResultConsumers.savedMembership(evaluate("saved-membership", savedInput).result().bytes());
        assertTrue(saved.realm().complete());
        ObjectNode savedPair = StrictJson.object(); savedPair.set("previous", parse(savedInput));
        savedPair.set("current", parse(savedInput)); savedPair.put("scope", "realm");
        var unknown = assertInstanceOf(M1RealmComparisons.SavedUnavailable.class,
                M1ResultConsumers.savedDifference(evaluate("saved-difference", write(savedPair)).result().bytes()));
        assertEquals(M1RealmComparisons.Reason.DATE_NOT_STRICTLY_EARLIER, unknown.reason());
    }

    @Test void outerResearchKeepsFractionTokensAndRejectsWrongVersionMilestoneAndPayload() throws Exception {
        ObjectNode raw = (ObjectNode) realmGolden().path("bases").path("first").deepCopy();
        ((ObjectNode) raw.get("source_frame")).set("sdk_extension", parse(utf8("1.0")));
        byte[] payload = wrapper("realm-feedback", write(raw));
        G2Request request = request(payload);
        byte[] encoded = G2Wire.encodeRequest(request);
        assertArrayEquals(payload, G2Wire.decodeRequest(encoded).payload().bytes());
        G2Response response = new M1Research().evaluate(G2Wire.decodeRequest(encoded));
        G2Response restored = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertArrayEquals(response.result().bytes(), restored.result().bytes());
        assertTrue(assertInstanceOf(M1ResultConsumers.AvailableFeedback.class,
                M1ResultConsumers.realmFeedback(restored.result().bytes())).observation().sourceFrame().get("sdk_extension").isFloatingPointNumber());
        String wire = new String(encoded, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> G2Wire.decodeRequest(utf8(wire.replace("\"schema_version\":1", "\"schema_version\":1.0"))));
        assertThrows(IllegalArgumentException.class, () -> G2Wire.decodeRequest(utf8(wire.replace("\"schema_version\":1", "\"schema_version\":true"))));
        assertThrows(IllegalArgumentException.class, () -> new M1Research().evaluate(
                new G2Request(request.requestId(), Milestone.M0, request.source(), request.payload())));
        assertThrows(IllegalArgumentException.class, () -> new M1Research().evaluate(request(utf8("{\"operation\":\"realm-feedback\"}"))));
        ObjectNode invalidSequence = raw.deepCopy();
        ((ObjectNode) invalidSequence.get("faction_result")).set("query_sequence", parse(utf8("1.0")));
        var rejected = assertInstanceOf(M1ResultConsumers.UnavailableFeedback.class,
                M1ResultConsumers.realmFeedback(evaluate("realm-feedback", write(invalidSequence)).result().bytes()));
        assertEquals("faction_original_query_sequence_unavailable", rejected.reason());
    }

    private static G2Response evaluate(String operation, byte[] input) throws Exception {
        G2Request supplied = request(wrapper(operation, input));
        G2Request decoded = G2Wire.decodeRequest(G2Wire.encodeRequest(supplied));
        assertArrayEquals(supplied.payload().bytes(), decoded.payload().bytes());
        G2Response response = new M1Research().evaluate(decoded);
        G2Response consumed = G2Wire.decodeResponse(G2Wire.encodeResponse(response));
        assertEquals(supplied.requestId(), consumed.requestId()); assertEquals(Milestone.M1, consumed.milestone());
        assertEquals(supplied.source(), consumed.source());
        assertArrayEquals(response.result().bytes(), consumed.result().bytes());
        return consumed;
    }
    private static G2Request request(byte[] payload) throws Exception {
        String operation = parse(payload).path("operation").asText();
        byte[] corpus;
        JsonNode metadata;
        String fixture;
        String machine;
        String observed;
        String build;
        if (operation.startsWith("saved-")) {
            fixture = "saved-membership.jsonl";
            corpus = resource(fixture, "da6297b603c7f2388b350eb8214a66911ba7761fff642d5e3a3de3145bea9e96");
            metadata = parse(utf8(new String(corpus, StandardCharsets.UTF_8).lines().findFirst().orElseThrow()));
            machine = metadata.path("machine_id").textValue(); observed = metadata.path("observed_at_utc").textValue();
            build = "pure-producer:" + metadata.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py").textValue();
        } else if (operation.equals("dated-summary")) {
            fixture = "dated-summary.json";
            corpus = resource(fixture, "7bc6d62177f58fe3f7763d302cfab9d739f7821ae37937485bd088d5622418fc");
            metadata = parse(corpus);
            machine = metadata.path("machine_id").textValue(); observed = metadata.path("observed_at_utc").textValue();
            build = "pure-producer:" + metadata.path("producer").path("sha256").textValue();
        } else if (operation.startsWith("monthly-")) {
            fixture = "monthly-observation.json";
            corpus = resource(fixture, "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae");
            metadata = parse(corpus);
            machine = metadata.path("machine_id").textValue(); observed = metadata.path("observed_at_utc").textValue();
            build = "pure-producer:" + metadata.path("producer").path("sha256").textValue();
        } else {
            fixture = "realm-membership.json";
            corpus = resource(fixture, "21fd8f8bd03a822add8bb67321549e8b35e50cefcd547042e483bc7c76dbb253");
            metadata = parse(corpus);
            machine = metadata.path("capture").path("machine_id").textValue(); observed = metadata.path("capture").path("observed_at_utc").textValue();
            JsonNode hello = metadata.path("bases").path("first").path("snapshot").path("diagnostics").path("hello");
            build = hello.path("game_version").textValue() + ":" + hello.path("executable_sha256").textValue();
        }
        G2Source source = new G2Source(machine, Instant.parse(observed).toString(), build,
                new ExactRef("classpath:/m1/" + fixture, corpus.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(corpus))));
        return new G2Request("m1-original-producer", Milestone.M1, source, ProjectionJson.object(payload, M1Research.MAX_BYTES));
    }
    private static byte[] wrapper(String operation, byte[] input) {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        output.writeBytes(utf8("{\"operation\":\"" + operation + "\",\"input\":"));
        output.writeBytes(input); output.write('}'); return output.toByteArray();
    }

    private static ObjectNode firstMonth() throws Exception {
        JsonNode golden = parse(resource("monthly-observation.json",
                "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae"));
        for (JsonNode row : golden.path("cases")) {
            if (row.path("id").asText().equals("sample-baseline")) {
                return (ObjectNode) parse(M1ProducerApi.monthlyObservation(write(row.get("request"))).wireJson());
            }
        }
        throw new IOException("required actual baseline producer case missing");
    }
    private static JsonNode realmGolden() throws Exception {
        return parse(resource("realm-membership.json", "21fd8f8bd03a822add8bb67321549e8b35e50cefcd547042e483bc7c76dbb253"));
    }
    private static ObjectNode materialize(JsonNode golden, JsonNode vector) {
        ObjectNode root = ((ObjectNode) golden.path("bases").get(vector.path("base").textValue())).deepCopy();
        for (JsonNode operation : vector.path("operations")) {
            String path = operation.path("path").textValue();
            int split = path.lastIndexOf('/');
            JsonNode parent = root.at(path.substring(0, split));
            String key = path.substring(split + 1);
            if (parent instanceof ObjectNode object) {
                if (operation.path("remove").asBoolean()) { object.remove(key); }
                else { object.set(key, operation.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (operation.path("remove").asBoolean()) { array.remove(Integer.parseInt(key)); }
                else { array.set(Integer.parseInt(key), operation.get("value").deepCopy()); }
            } else { fail("actual producer operation path invalid: " + path); }
        }
        return root;
    }
    private static byte[] resource(String name, String sha256) throws Exception {
        try (InputStream stream = M1ConsumerIntegrationTest.class.getResourceAsStream("/m1/" + name)) {
            assertNotNull(stream, "actual producer resource required; missing environment is not a skip");
            byte[] raw = stream.readAllBytes();
            assertEquals(sha256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)), name);
            return raw;
        }
    }
    private static JsonNode parse(byte[] raw) { return StrictJson.parse(raw, M1ResultConsumers.MAX_BYTES); }
    private static byte[] write(JsonNode node) { return SdkProjectionJson.encode(node, M1ResultConsumers.MAX_BYTES); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
