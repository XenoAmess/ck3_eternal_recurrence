package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m7.CheckpointContinuity;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.GameIdentity;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.Observation;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Context;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** Actual common Quarkus/client route; all game, process and inheritance data are software fixtures. */
@QuarkusTest
class M7ConsumerHttpTest {
    private static final String MACHINE = "synthetic-m7-http";
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @TempDir Path temporary;
    private long sequence;

    @Test void originalProducerReachesOrdinaryConsumerPersistenceAndSuccessorThroughTheSameHost() throws Exception {
        byte[] originalOracle = oracle(); JsonNode corpus = StrictJson.parse(originalOracle, StrictJson.EXPLICIT_MAX_BYTES);
        G2Source source = source(originalOracle);
        try (G2JavaClient client = client()) {
            ObjectNode initialInput = StrictJson.object(); initialInput.put("campaign_id", "m7-original-producer-fixture"); initialInput.put("character_id", 100);
            Goal initial = GoalCodec.decodeGoal(call(client, source, "goal_new", initialInput).result().bytes());

            // The native primitive is retained; actor variation below is explicitly synthetic.
            ObjectNode governmentInput = (ObjectNode) corpus.path("government_cases").get(0).get("input").deepCopy();
            ObjectNode snapshot = (ObjectNode) governmentInput.get("snapshot");
            snapshot.set("campaign_goal", StrictJson.parse(GoalCodec.encodeGoal(initial)));
            ((ObjectNode) snapshot.get("played_character")).put("character_id", initial.currentCharacterId());
            ((ObjectNode) governmentInput.get("government_observation")).put("player_character_id", initial.currentCharacterId());
            Context context = GovernmentContextCodec.decodeContext(call(client, source, "government_context", governmentInput).result().bytes());
            Observation frame = frame(initial, snapshot.get("native_revision").longValue(), snapshot.get("date_raw").longValue(),
                    "synthetic-initial-episode", context.governmentKey(), context.adapterFamily());
            G2Response ordinary = call(client, source, "ordinary_plan_consume", input(frame, "ordinary_plan", Optional.of(context)));
            var consumed = M7OrdinaryPlanConsumer.decode(ordinary.result().bytes());
            assertEquals(frame, consumed.observation()); assertFalse(consumed.replayAuthorized());

            Path receipt = temporary.resolve("ordinary-consumer-wire.receipt.json");
            byte[] retained = G2Wire.encodeResponse(ordinary); Files.write(receipt, retained, StandardOpenOption.CREATE_NEW);
            G2Response freshWire = G2Wire.decodeResponse(Files.readAllBytes(receipt));
            var freshConsumer = M7OrdinaryPlanConsumer.decode(freshWire.result().bytes());
            assertEquals(source, freshWire.source()); assertEquals(frame, freshConsumer.observation());

            ObjectNode continuation = StrictJson.object();
            continuation.set("goal", StrictJson.parse(GoalCodec.encodeGoal(freshConsumer.observation().goal())));
            continuation.set("reconciliation", corpus.get("complete_reconciliation").deepCopy());
            Goal successor = GoalCodec.decodeGoal(call(client, source, "goal_continue", continuation).result().bytes());
            Observation successorFrame = frame(successor, frame.nativeRevision() + 1L, frame.dateRaw() + 24L,
                    "synthetic-successor-episode", null, null);
            G2Response following = call(client, source, "ordinary_plan_consume", input(successorFrame, "successor_plan", Optional.empty()));
            var followingConsumer = M7OrdinaryPlanConsumer.decode(following.result().bytes());
            assertEquals(initial.campaignId(), followingConsumer.observation().goal().campaignId());
            assertEquals(initial.originCharacterId(), followingConsumer.observation().goal().originCharacterId());
            assertEquals(successor.currentCharacterId(), followingConsumer.campaignGoalPlanUsed().currentCharacterId());
            assertEquals(successor.progress(), followingConsumer.campaignGoalPlanUsed().progress());
            assertFalse(followingConsumer.gameActionsSubmitted()); assertFalse(followingConsumer.coldAuthorityGranted());

            ObjectNode unknown = continuation.deepCopy(); ((ObjectNode) unknown.get("reconciliation")).put("verdict", "unknown");
            G2ClientException rejected = assertThrows(G2ClientException.class, () -> call(client, source, "goal_continue", unknown));
            assertEquals(G2ClientException.Reason.HTTP_REJECTED, rejected.reason());
            assertEquals(G2HttpError.Code.DOMAIN_REJECTED, rejected.httpError().orElseThrow().code());
            assertTrue(rejected.evidence().actualHttpInvoked()); assertTrue(rejected.evidence().responseComplete());
            assertArrayEquals(retained, Files.readAllBytes(receipt), "UNKNOWN did not rewrite or replay the retained ordinary input");
        }
    }

    @Test void originalFloatingControlTokenIsRejectedByActualHttpBeforeAnyConsumerReceipt() throws Exception {
        G2Source source = source(oracle());
        Goal goal = new Goal("synthetic-http-float", 100, 100,
                new org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Progress(0, Optional.empty()));
        ObjectNode consumerInput = input(frame(goal, 8, 53279400, "synthetic-float-episode", null, null), "ordinary_plan", Optional.empty());
        String valid = new String(raw(consumerInput), StandardCharsets.UTF_8);
        String bad = valid.replace("\"revision\":42", "\"revision\":42.0"); assertNotEquals(valid, bad);
        byte[] originalPayload = ("{\"operation\":\"ordinary_plan_consume\",\"input\":" + bad + "}").getBytes(StandardCharsets.UTF_8);
        G2Request request = new G2Request("m7-http-original-float", Milestone.M7, source,
                ProjectionJson.object(originalPayload, ProjectionJson.MAX_BYTES));
        try (G2JavaClient client = client()) {
            G2ClientException rejected = assertThrows(G2ClientException.class, () -> client.evaluate(request));
            assertEquals(G2ClientException.Reason.HTTP_REJECTED, rejected.reason());
            assertEquals(G2HttpError.Code.DOMAIN_REJECTED, rejected.httpError().orElseThrow().code());
            assertTrue(rejected.evidence().actualHttpInvoked()); assertTrue(rejected.evidence().responseComplete());
        }
    }

    private G2Response call(G2JavaClient client, G2Source source, String operation, ObjectNode input) {
        ObjectNode payload = StrictJson.object(); payload.put("operation", operation); payload.set("input", input);
        G2Request request = new G2Request("m7-http-" + ++sequence, Milestone.M7, source,
                ProjectionJson.object(raw(payload), ProjectionJson.MAX_BYTES));
        var evaluated = client.evaluateWithEvidence(request);
        assertTrue(evaluated.evidence().actualHttpInvoked()); assertTrue(evaluated.evidence().responseComplete());
        assertEquals(200, evaluated.evidence().httpStatus().orElseThrow());
        assertEquals(source, evaluated.response().source()); assertEquals(request.requestId(), evaluated.response().requestId());
        return evaluated.response();
    }
    private G2JavaClient client() {
        return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()),
                Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES));
    }
    private G2Source source(byte[] oracle) throws IOException {
        Path path = temporary.resolve("original-producer-oracle.json"); Files.write(path, oracle, StandardOpenOption.CREATE_NEW);
        return new G2Source(MACHINE, Instant.now().toString(), "software-fixture-only-no-native-qualification",
                new ExactRef(path.toString(), oracle.length, sha256(oracle)));
    }
    private static ObjectNode input(Observation frame, String publication, Optional<Context> context) {
        ObjectNode row = StrictJson.object(); row.put("schema", M7OrdinaryPlanConsumer.INPUT_SCHEMA);
        row.put("publication", publication); row.set("observation", StrictJson.parse(CheckpointContinuity.encodeObservation(frame)));
        row.put("selected_step", "life-advance");
        if (context.isPresent()) row.set("government_context", StrictJson.parse(GovernmentContextCodec.encode(context.orElseThrow())));
        else row.putNull("government_context");
        return row;
    }
    private static Observation frame(Goal goal, long nativeRevision, long date, String episode, String key, String family) {
        return new Observation(MACHINE, "a".repeat(64),
                new GameIdentity(101, "20261023123045.123456+480", "C:/synthetic/ck3.exe"), "synthetic:m7:http", 42,
                nativeRevision, episode, goal.currentCharacterId(), date, goal, key, family);
    }
    private static byte[] oracle() throws IOException {
        try (var input = M7ConsumerHttpTest.class.getResourceAsStream("/m7/original-producer-golden-v1.json")) {
            assertNotNull(input, "mandatory exact original M7 producer resource missing; HTTP consumer test cannot be skipped");
            byte[] raw = input.readNBytes(262145); assertTrue(raw.length > 0 && raw.length <= 262144);
            JsonNode corpus = StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES);
            assertEquals("xar.g2-m7-original-producer-golden/v1", corpus.path("schema").textValue());
            assertTrue(corpus.path("source_refs_unchanged").booleanValue()); return raw;
        }
    }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException("SHA-256 required by Java", error); }
    }
}
