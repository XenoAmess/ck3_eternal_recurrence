package org.xar.ck3.control.wave2.governance.government;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.m7.CheckpointContinuity;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.KernelCheckpointContinuity;
import org.xar.ck3.control.g2.m7.M7KernelPlanConsumer;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;

/** Persistent CI coverage of the new result boundary using the actual old producer corpus. */
final class GovernmentContextPersistenceTest {
    @Test void actualProducerCasesSurviveTypedPersistenceWithoutChangingTheSource() throws IOException {
        JsonNode golden = golden();
        assertEquals(15, golden.get("cases").size());
        for (JsonNode row : golden.get("cases")) {
            ObjectNode request = (ObjectNode) golden.get("base_request").deepCopy();
            for (JsonNode patch : row.get("request_patch")) {
                String pointer = patch.get("path").textValue(); int index = pointer.lastIndexOf('/');
                ObjectNode parent = (ObjectNode) (index == 0 ? request : request.at(pointer.substring(0, index)));
                String field = pointer.substring(index + 1).replace("~1", "/").replace("~0", "~");
                if (patch.get("op").textValue().equals("remove")) { parent.remove(field); }
                else { parent.set(field, patch.get("value").deepCopy()); }
            }
            byte[] input = raw(request);
            byte[] produced = GovernmentContextCodec.compose(input);
            byte[] restored = GovernmentContextCodec.encode(GovernmentContextCodec.decodeContext(produced));
            assertEquals(StrictJson.parse(produced), StrictJson.parse(restored), row.get("name").textValue());
            assertArrayEquals(restored, GovernmentContextCodec.encode(GovernmentContextCodec.decodeContext(restored)));
            assertArrayEquals(input, raw(request));
        }
    }

    @Test void missingWrongAndForgedResultFieldsCannotClaimThePreservedObservation() throws IOException {
        ObjectNode valid = result();
        List<String> fields = new ArrayList<>(); valid.fieldNames().forEachRemaining(fields::add);
        assertEquals(16, fields.size());
        for (String field : fields) {
            ObjectNode missing = valid.deepCopy(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.decodeContext(raw(missing)), field);
        }
        for (String field : List.of("current_character_id", "snapshot_revision", "date_raw", "schema_version")) {
            ObjectNode wrong = valid.deepCopy(); wrong.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.decodeContext(raw(wrong)), field);
            wrong.put(field, 1.0);
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.decodeContext(raw(wrong)), field);
        }
        for (String field : List.of("government_key", "adapter_family", "adapter_status", "status")) {
            ObjectNode wrong = valid.deepCopy(); wrong.put(field, "forged");
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.decodeContext(raw(wrong)), field);
        }
        ObjectNode noObservation = valid.deepCopy(); noObservation.putNull("government_runtime_adapter");
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.decodeContext(raw(noObservation)));
    }

    @Test void absentObservationAndDefaultOffRemainUnqualifiedAcrossPersistence() throws IOException {
        ObjectNode request = (ObjectNode) golden().get("base_request").deepCopy();
        request.put("query_permitted", false);
        byte[] produced = GovernmentContextCodec.compose(raw(request));
        GovernmentContext.Context result = GovernmentContextCodec.decodeContext(produced);
        assertEquals(GovernmentContext.Status.NOT_QUERIED, result.status());
        assertFalse(result.identityObservationReady()); assertFalse(result.coreAdapterReady());
        assertFalse(result.ordinaryGoalContextReady());
        assertEquals(StrictJson.parse(produced), StrictJson.parse(GovernmentContextCodec.encode(result)));
    }

    @Test void parsedNestedDecimalTokensRemainInvalidBeforeAnySecondEncoding() throws IOException {
        ObjectNode valid = result();
        for (String field : List.of("schema_version", "snapshot_revision", "player_character_id", "date_raw")) {
            ObjectNode wrong = valid.deepCopy();
            ObjectNode observation = (ObjectNode) wrong.get("government_runtime_adapter");
            observation.put(field, observation.get(field).doubleValue());
            byte[] originalFloat = raw(wrong);
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.decodeContext(originalFloat), field);
            JsonNode alreadyParsed = StrictJson.parse(originalFloat);
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.parseContext(alreadyParsed), field);
        }
        ObjectNode count = valid.deepCopy();
        ((ObjectNode) count.get("government_runtime_adapter").get("effective_feature_flags")).put("native_count", 44.0);
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.parseContext(StrictJson.parse(raw(count))));
        ObjectNode index = valid.deepCopy();
        ((ObjectNode) index.get("government_runtime_adapter").get("effective_feature_flags").get("items").get(0)).put("native_index", 0.0);
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.parseContext(StrictJson.parse(raw(index))));
    }

    @Test void currentPlayerBindingUsesTheNativePlayerAndAllowsAbsentProfiles() throws IOException {
        ObjectNode request = (ObjectNode) golden().get("base_request").deepCopy();
        var actual = GovernmentContextCodec.decodeAndBuild(raw(request));
        java.math.BigInteger player = request.get("snapshot").get("played_character").get("character_id").bigIntegerValue();
        GovernmentContextCodec.requireCurrentPlayerBinding(actual, player);
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.requireCurrentPlayerBinding(actual, player.add(java.math.BigInteger.ONE)));
        ((ObjectNode) request.get("snapshot").get("campaign_goal"))
                .put("origin_character_id", 100).put("current_character_id", 100);
        var mismatch = GovernmentContextCodec.decodeAndBuild(raw(request));
        assertEquals("ordinary_goal_current_ruler_not_matched", mismatch.unavailableReason());
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.requireCurrentPlayerBinding(mismatch, java.math.BigInteger.valueOf(100)));
        request.put("query_permitted", false);
        var absent = GovernmentContextCodec.decodeAndBuild(raw(request));
        GovernmentContextCodec.requireCurrentPlayerBinding(absent, java.math.BigInteger.valueOf(100));
    }

    @Test void signedNativeCharacterDomainSurvivesProducerPersistenceAndBinding() throws IOException {
        for (BigInteger actor : nativeActors()) {
            ObjectNode request = nativeRequest(actor);
            byte[] original = raw(request);
            var context = GovernmentContextCodec.decodeContext(GovernmentContextCodec.compose(original));
            assertEquals(actor, context.currentCharacterId());
            assertTrue(context.ordinaryGoalContextReady());
            GovernmentContextCodec.requireCurrentPlayerBinding(context, actor);
            byte[] encoded = GovernmentContextCodec.encode(context);
            assertEquals(actor, StrictJson.parse(encoded).path("government_runtime_adapter").path("player_character_id").bigIntegerValue());
            assertArrayEquals(encoded, GovernmentContextCodec.encode(GovernmentContextCodec.decodeContext(encoded)));
            assertArrayEquals(original, raw(request));
            ObjectNode normalize = request.deepCopy(); normalize.put("schema", GovernmentContextCodec.NORMALIZE_SCHEMA);
            normalize.remove("query_permitted");
            assertEquals(StrictJson.parse(raw(request.get("government_observation"))),
                    StrictJson.parse(GovernmentContextCodec.normalizeAdapter(raw(normalize))));
        }
    }

    @Test void presentGovernmentTraversesBothM7ConsumersAcrossEveryPublication() throws IOException {
        for (BigInteger actor : nativeActors()) {
            ObjectNode request = nativeRequest(actor);
            var context = GovernmentContextCodec.decodeContext(GovernmentContextCodec.compose(raw(request)));
            var goal = GoalCodec.decodeGoal(raw(request.path("snapshot").get("campaign_goal")));
            long revision = request.path("snapshot").get("native_revision").bigIntegerValue().longValueExact();
            long date = request.path("snapshot").get("date_raw").bigIntegerValue().longValueExact();
            var legacy = new CheckpointContinuity.Observation("government-domain-software-fixture", "a".repeat(64),
                    new CheckpointContinuity.GameIdentity(101, "20261023081234.123456+480", "D:/software-fixture/ck3.exe"),
                    "native:" + revision, 42, revision, "software-episode", actor.longValueExact(), date, goal,
                    context.governmentKey(), context.adapterFamily());
            var kernel = new KernelCheckpointContinuity.Observation("government-domain-software-fixture", "a".repeat(64),
                    new G2RetainedNativeSourceProvider.GameIdentity(101, "18446744073709551615"),
                    new ExactRef("software-fixture/ck3.exe", 1, "b".repeat(64)), "native:" + revision, 42, revision,
                    "software-episode", actor.longValueExact(), date, goal, context.governmentKey(), context.adapterFamily());
            for (M7OrdinaryPlanConsumer.Publication publication : M7OrdinaryPlanConsumer.Publication.values()) {
                byte[] ordinaryWire = M7OrdinaryPlanConsumer.encode(
                        M7OrdinaryPlanConsumer.consume(publication, legacy, "life-advance", Optional.of(context)));
                var ordinary = M7OrdinaryPlanConsumer.decode(ordinaryWire);
                assertEquals(actor.longValueExact(), ordinary.observation().actorCharacterId());
                assertEquals(context, ordinary.campaignGovernmentContextUsed().orElseThrow());
                assertFalse(ordinary.gameActionsSubmitted()); assertFalse(ordinary.coldAuthorityGranted()); assertFalse(ordinary.replayAuthorized());
                byte[] exactWire = M7KernelPlanConsumer.encode(
                        M7KernelPlanConsumer.consume(publication, kernel, "life-advance", Optional.of(context)));
                var exact = M7KernelPlanConsumer.decode(exactWire);
                assertEquals(actor.longValueExact(), exact.observation().actorCharacterId());
                assertEquals(context, exact.government().orElseThrow());
                assertEquals("18446744073709551615", exact.observation().game().creationFiletime());
                assertFalse(exact.gameActionsSubmitted()); assertFalse(exact.coldAuthorityGranted()); assertFalse(exact.replayAuthorized());
                assertEquals(0, exact.savedDayCredit());
                if (actor.signum() == 0 && publication == M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN) {
                    rejectChangedPersistedGovernment(ordinaryWire, "campaign_government_context_used", false);
                    rejectChangedPersistedGovernment(exactWire, "government_context", true);
                }
            }
        }
    }

    @Test void nativeCharacterRolesRejectSentinelOverflowAndActualWrongTokens() throws IOException {
        for (String path : List.of("/snapshot/campaign_goal/origin_character_id", "/snapshot/campaign_goal/current_character_id",
                "/snapshot/played_character/character_id", "/government_observation/player_character_id")) {
            for (JsonNode invalid : invalidCharacterTokens()) {
                ObjectNode request = nativeRequest(BigInteger.ZERO); replace(request, path, invalid);
                assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(raw(request)), path + "=" + invalid);
            }
        }
        ObjectNode valid = (ObjectNode) StrictJson.parse(GovernmentContextCodec.compose(raw(nativeRequest(BigInteger.ZERO))));
        for (String path : List.of("/current_character_id", "/government_runtime_adapter/player_character_id")) {
            for (JsonNode invalid : invalidCharacterTokens()) {
                ObjectNode wrong = valid.deepCopy(); replace(wrong, path, invalid);
                assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.parseContext(wrong), path + "=" + invalid);
                // The DoubleNode still emits the actual 0.0 token before byte decoding.
                assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.decodeContext(raw(wrong)), path + "=" + invalid);
            }
        }
        var context = GovernmentContextCodec.decodeContext(raw(valid));
        for (BigInteger actor : List.of(BigInteger.valueOf(-1), BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE), new BigInteger("4294967294"))) {
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.requireCurrentPlayerBinding(context, actor));
        }
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.requireCurrentPlayerBinding(context, null));
        ObjectNode normalize = nativeRequest(BigInteger.ZERO); normalize.put("schema", GovernmentContextCodec.NORMALIZE_SCHEMA);
        normalize.remove("query_permitted");
        for (JsonNode invalid : invalidCharacterTokens()) {
            ObjectNode wrong = normalize.deepCopy(); replace(wrong, "/snapshot/played_character/character_id", invalid);
            replace(wrong, "/government_observation/player_character_id", invalid);
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.normalizeAdapter(raw(wrong)));
        }
    }

    @Test void unavailableAndUnobservedNullsPreserveTheirActualDistinctContracts() throws IOException {
        for (boolean missing : List.of(true, false)) {
            ObjectNode request = nativeRequest(BigInteger.ZERO);
            ObjectNode observed = (ObjectNode) request.get("government_observation");
            observed.put("status", "unavailable").put("unavailable_reason", "software-unavailable");
            ((ObjectNode) observed.get("readiness")).put("same_frame_ready", false).put("core_adapter_ready", false);
            if (missing) observed.remove("player_character_id"); else observed.putNull("player_character_id");
            var context = GovernmentContextCodec.decodeContext(GovernmentContextCodec.compose(raw(request)));
            assertFalse(context.identityObservationReady()); assertFalse(context.ordinaryGoalContextReady());
            JsonNode retained = StrictJson.parse(GovernmentContextCodec.encode(context)).get("government_runtime_adapter");
            assertEquals(!missing, retained.has("player_character_id"));
            if (!missing) assertTrue(retained.get("player_character_id").isNull());
            assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.requireCurrentPlayerBinding(context, BigInteger.ZERO));
        }
        ObjectNode absent = nativeRequest(BigInteger.ZERO); absent.put("query_permitted", false);
        ((ObjectNode) absent.get("snapshot")).remove("campaign_goal");
        var notQueried = GovernmentContextCodec.decodeContext(GovernmentContextCodec.compose(raw(absent)));
        assertEquals(null, notQueried.currentCharacterId());
        GovernmentContextCodec.requireCurrentPlayerBinding(notQueried, BigInteger.ZERO);
        ObjectNode missingCurrent = (ObjectNode) StrictJson.parse(GovernmentContextCodec.encode(notQueried));
        missingCurrent.remove("current_character_id");
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.parseContext(missingCurrent));
        ObjectNode explicit = nativeRequest(BigInteger.ZERO); explicit.putNull("government_observation");
        assertFalse(GovernmentContextCodec.decodeContext(GovernmentContextCodec.compose(raw(explicit))).identityObservationReady());
        explicit.remove("government_observation");
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.compose(raw(explicit)));
    }

    @Test void legalIdZeroDoesNotExcuseUnreconciledGoalDriftOrCrossedPlayerFrames() throws IOException {
        ObjectNode original = (ObjectNode) golden().get("base_request").deepCopy();
        ((ObjectNode) original.path("snapshot").get("campaign_goal")).put("origin_character_id", 0);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(raw(original.path("snapshot").get("campaign_goal"))));
        assertFalse(GovernmentContextCodec.decodeAndBuild(raw(original)).ordinaryGoalContextReady());
        ObjectNode coherent = nativeRequest(BigInteger.ZERO);
        assertTrue(GovernmentContextCodec.decodeAndBuild(raw(coherent)).ordinaryGoalContextReady());
        for (boolean falseCount : List.of(true, false)) {
            ObjectNode wrong = coherent.deepCopy();
            ObjectNode progress = (ObjectNode) wrong.path("snapshot").path("campaign_goal").get("progress");
            if (falseCount) progress.put("reconciled_successions", 1); else progress.putObject("last_succession");
            assertFalse(GovernmentContextCodec.decodeAndBuild(raw(wrong)).ordinaryGoalContextReady());
        }
        ObjectNode crossed = nativeRequest(BigInteger.valueOf(-2));
        ((ObjectNode) crossed.get("snapshot")).set("campaign_goal", coherent.path("snapshot").get("campaign_goal").deepCopy());
        var context = GovernmentContextCodec.decodeContext(GovernmentContextCodec.compose(raw(crossed)));
        assertEquals("ordinary_goal_current_ruler_not_matched", context.unavailableReason());
        assertFalse(context.ordinaryGoalContextReady());
        assertThrows(IllegalArgumentException.class, () -> GovernmentContextCodec.requireCurrentPlayerBinding(context, BigInteger.ZERO));
    }

    private static List<BigInteger> nativeActors() {
        return List.of(BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(-2), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));
    }
    private static List<JsonNode> invalidCharacterTokens() {
        var nodes = JsonNodeFactory.instance;
        return List.of(nodes.numberNode(-1), nodes.numberNode(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                nodes.numberNode(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)), nodes.numberNode(new BigInteger("4294967294")),
                nodes.booleanNode(true), nodes.numberNode(0.0), nodes.textNode("0"));
    }
    private static ObjectNode nativeRequest(BigInteger actor) throws IOException {
        ObjectNode request = (ObjectNode) golden().get("base_request").deepCopy();
        ObjectNode snapshot = (ObjectNode) request.get("snapshot");
        String campaign = snapshot.path("campaign_goal").get("campaign_id").textValue();
        snapshot.set("campaign_goal", StrictJson.parse(GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal(campaign, actor.longValueExact()))));
        ((ObjectNode) snapshot.get("played_character")).put("character_id", actor);
        ((ObjectNode) request.get("government_observation")).put("player_character_id", actor);
        return request;
    }
    private static void replace(ObjectNode root, String pointer, JsonNode value) {
        int split = pointer.lastIndexOf('/');
        ObjectNode parent = split == 0 ? root : (ObjectNode) root.at(pointer.substring(0, split));
        parent.set(pointer.substring(split + 1), value.deepCopy());
    }
    private static void rejectChangedPersistedGovernment(byte[] original, String governmentField, boolean kernel) {
        for (String role : List.of("/current_character_id", "/government_runtime_adapter/player_character_id")) {
            for (JsonNode invalid : invalidCharacterTokens()) {
                ObjectNode changed = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES);
                replace(changed, "/" + governmentField + role, invalid);
                rejectPersistedConsumer(raw(changed), kernel);
            }
            ObjectNode explicit = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES);
            replace(explicit, "/" + governmentField + role, JsonNodeFactory.instance.nullNode());
            rejectPersistedConsumer(raw(explicit), kernel);
            ObjectNode missing = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES);
            String path = "/" + governmentField + role;
            ((ObjectNode) missing.at(path.substring(0, path.lastIndexOf('/')))).remove(path.substring(path.lastIndexOf('/') + 1));
            rejectPersistedConsumer(raw(missing), kernel);
        }
        ObjectNode missing = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES);
        missing.remove(governmentField); rejectPersistedConsumer(raw(missing), kernel);
        ObjectNode nullable = (ObjectNode) StrictJson.parse(original, M7OrdinaryPlanConsumer.MAX_BYTES);
        nullable.putNull(governmentField);
        if (kernel) assertTrue(M7KernelPlanConsumer.decode(raw(nullable)).government().isEmpty());
        else assertTrue(M7OrdinaryPlanConsumer.decode(raw(nullable)).campaignGovernmentContextUsed().isEmpty());
    }
    private static void rejectPersistedConsumer(byte[] value, boolean kernel) {
        if (kernel) assertThrows(IllegalArgumentException.class, () -> M7KernelPlanConsumer.decode(value));
        else assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(value));
    }

    private static ObjectNode result() throws IOException {
        return (ObjectNode) StrictJson.parse(GovernmentContextCodec.compose(raw(golden().get("base_request"))));
    }
    private static JsonNode golden() throws IOException {
        try (var input = GovernmentContextPersistenceTest.class.getResourceAsStream("/government/original-producer-golden.json")) {
            assertNotNull(input, "actual original producer corpus is required, never skipped");
            return StrictJson.parse(input.readAllBytes());
        }
    }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
