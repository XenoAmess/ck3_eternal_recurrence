package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.SuccessorUiQueueModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m3.M3Research;

final class SuccessorUiQueueTest {
    @TestFactory Stream<DynamicTest> originalRegisteredAppQueueCasesCrossM3AndPersistence() throws Exception {
        byte[] bytes = goldenBytes(); JsonNode golden = golden();
        G2Source source = new G2Source(golden.path("machine_id").textValue(), golden.path("observed_at_utc").textValue(),
                "offline-registered-app-fixture", new ExactRef("/g2/m3/original-resident-ui-golden.json", bytes.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))));
        assertTrue(golden.path("source_refs_unchanged").booleanValue());
        assertTrue(golden.path("synthetic_fixture").booleanValue());
        assertEquals(12, golden.path("original_suite").path("tests").intValue());
        for (String key : List.of("failures", "errors", "skipped")) assertEquals(0, golden.path("original_suite").path(key).intValue());
        assertTrue(golden.path("cases").size() >= 3, "actual deferred/Close/clear original route required");
        return StreamSupport.stream(golden.path("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
            byte[] input = SuccessionCodec.encode(row.get("request"));
            G2Request request = new G2Request(row.path("name").textValue(), Milestone.M3, source,
                    ProjectionJson.object(input, ProjectionJson.MAX_BYTES));
            var response = G2Wire.decodeResponse(G2Wire.encodeResponse(new M3Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)))));
            assertEquals(source, response.source()); assertEquals(request.requestId(), response.requestId());
            assertEquals(row.get("expected"), SuccessionCodec.parse(response.result().bytes()));
            Result observed = SuccessorUiQueueCodec.decodeResult(response.result().bytes());
            assertInstanceOf(Observed.class, observed);
            assertEquals(row.get("expected"), SuccessionCodec.parse(SuccessorUiQueueCodec.encode(observed)));
            assertEquals(row.get("request"), SuccessionCodec.parse(input), "caller-owned originals survive unchanged");
        }));
    }

    @TestFactory Stream<DynamicTest> actualOriginalQueueFailurePathsRemainRejected() throws IOException {
        JsonNode rejected = golden().path("rejected"); assertEquals(6, rejected.size());
        return StreamSupport.stream(rejected.spliterator(), false).map(row -> DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
            assertEquals("ValueError", row.path("error_type").textValue());
            assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.apply(SuccessionCodec.encode(row.get("request"))));
        }));
    }

    @Test void coldReconnectIsTypedUnavailableAndCannotReuseAClaimedClearance() throws IOException {
        ObjectNode base = first();
        object(base.get("app_response")).set("cold_resume_binding", SuccessionCodec.objectNode().put("connection_rebound", true).put("opaque_original_owner_proof", true));
        Result result = SuccessorUiQueueCodec.evaluate(SuccessionCodec.encode(base));
        Unavailable unavailable = assertInstanceOf(Unavailable.class, result);
        assertEquals(UnavailableReason.ORIGINAL_APP_COLD_RECONNECT_VALIDATION_REQUIRED, unavailable.reason());
        assertEquals(result, SuccessorUiQueueCodec.decodeResult(SuccessorUiQueueCodec.encode(result)));
        JsonNode output = SuccessionCodec.parse(SuccessorUiQueueCodec.encode(result));
        assertTrue(output.get("pending").isNull()); assertTrue(output.get("player_decision_pending").isNull());
        assertFalse(output.path("submission_authorized").booleanValue());
        assertTrue(output.path("original_app_queue_verification_required").booleanValue());
    }

    @Test void originalNewConnectionInputsRemainOwnedByOriginalAppValidation() throws IOException {
        JsonNode rows = golden().path("cold_owner_required_cases");
        assertTrue(rows.isArray() && !rows.isEmpty(), "actual original reconnected Queue input required");
        for (JsonNode row : rows) {
            Unavailable unavailable = assertInstanceOf(Unavailable.class,
                    SuccessorUiQueueCodec.evaluate(SuccessionCodec.encode(row.get("request"))));
            assertEquals(UnavailableReason.ORIGINAL_APP_COLD_RECONNECT_VALIDATION_REQUIRED, unavailable.reason());
        }
    }

    @Test void exactWrapperAndOriginalIntegerTokensRejectBeforeProjection() throws IOException {
        ObjectNode base = first();
        for (String key : List.of("schema", "operation", "transition", "app_response", "independent_snapshot")) {
            ObjectNode missing = base.deepCopy(); missing.remove(key);
            assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.apply(SuccessionCodec.encode(missing)), key);
        }
        ObjectNode unknown = base.deepCopy(); unknown.put("submission_authorized", true);
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.apply(SuccessionCodec.encode(unknown)));
        for (JsonNode token : List.of(SuccessionCodec.parse("true".getBytes(StandardCharsets.UTF_8)),
                SuccessionCodec.parse("1.0".getBytes(StandardCharsets.UTF_8)), SuccessionCodec.parse("\"1\"".getBytes(StandardCharsets.UTF_8)))) {
            ObjectNode bad = base.deepCopy(); object(bad.get("independent_snapshot")).set("revision", token);
            assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.apply(SuccessionCodec.encode(bad)));
        }
        ObjectNode nullSnapshot = base.deepCopy(); nullSnapshot.putNull("independent_snapshot");
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.apply(SuccessionCodec.encode(nullSnapshot)));
        String raw = new String(SuccessionCodec.encode(base), StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.apply((raw + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.apply((raw.substring(0, raw.length()-1) + ",\"operation\":\"consume_resume\"}").getBytes(StandardCharsets.UTF_8)));
    }

    @Test void resultCannotPromoteAuthorityOrLoseNullAndEmptySemantics() throws IOException {
        byte[] output = SuccessorUiQueueCodec.apply(SuccessionCodec.encode(first()));
        for (String flag : List.of("submission_authorized", "action_replay_authorized")) {
            ObjectNode changed = object(SuccessionCodec.parse(output)).deepCopy(); changed.put(flag, true);
            assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.decodeResult(SuccessionCodec.encode(changed)));
        }
        ObjectNode floatCredit = object(SuccessionCodec.parse(output)).deepCopy(); floatCredit.put("ordinary_cycle_credit", 0.0);
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.decodeResult(SuccessionCodec.encode(floatCredit)));
        ObjectNode missing = object(SuccessionCodec.parse(output)).deepCopy(); missing.remove("unavailable_reason");
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueCodec.decodeResult(SuccessionCodec.encode(missing)));
    }

    @Test void unresolvedAndContradictoryClearDoNotGainPermission() throws IOException {
        Input observed = SuccessorUiQueueCodec.decode(SuccessionCodec.encode(first()));
        Result result = SuccessorUiQueueModel.evaluate(new Input(Status.UI_UNRESOLVED, true, observed.claimed(), observed.independent(),
                observed.expectedEpisodeRunId(), observed.expectedSuccessorId(), observed.originalSource(), false, false));
        assertInstanceOf(Observed.class, result);
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueModel.evaluate(new Input(Status.CLEAR, true,
                observed.claimed(), observed.independent(), observed.expectedEpisodeRunId(), observed.expectedSuccessorId(),
                observed.originalSource(), false, false)));
        SourceFrame source = observed.independent().source();
        LivingFrame drift = new LivingFrame(new SourceFrame(source.snapshotId(), source.revision(), source.nativeRevision(), source.dateRaw(),
                source.bridgePid().add(BigInteger.ONE), source.connectionGeneration()), observed.independent().episodeRunId(), observed.expectedSuccessorId());
        assertThrows(IllegalArgumentException.class, () -> SuccessorUiQueueModel.evaluate(new Input(Status.UI_UNRESOLVED, true,
                drift, drift, observed.expectedEpisodeRunId(), observed.expectedSuccessorId(), observed.originalSource(), false, false)));
    }

    /** Software role-boundary variants of the unchanged registered-App golden; no new Native or action authority. */
    @Test void signedModernSuccessorsReachTheRealClientRequestM3RouteAndResultCodec() throws Exception {
        for(int actor:List.of(Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE)) {
            ObjectNode input=withModernSuccessor(first(),SuccessionCodec.objectNode().put("id",actor).get("id"));
            byte[] before=SuccessionCodec.encode(input);
            byte[] originalBytes=goldenBytes();
            var source=new G2Source(golden().path("machine_id").textValue(),golden().path("observed_at_utc").textValue(),
                    "software-signed-ui-variant",new ExactRef("/g2/m3/original-resident-ui-golden.json",originalBytes.length,
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(originalBytes))));
            var originals=new SuccessorUiQueueClient.OriginalInputs(ProjectionJson.object(SuccessionCodec.encode(input.get("transition")),ProjectionJson.MAX_BYTES),
                    ProjectionJson.object(SuccessionCodec.encode(input.get("app_response")),ProjectionJson.MAX_BYTES),
                    ProjectionJson.object(SuccessionCodec.encode(input.get("independent_snapshot")),ProjectionJson.MAX_BYTES));
            G2Request request=SuccessorUiQueueClient.request("signed-ui-"+actor,source,originals);
            var response=G2Wire.decodeResponse(G2Wire.encodeResponse(new M3Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)))));
            var result=assertInstanceOf(Observed.class,SuccessorUiQueueCodec.decodeResult(response.result().bytes()));
            assertEquals(BigInteger.valueOf(actor),result.frame().successorCharacterId());
            assertEquals(result,SuccessorUiQueueCodec.decodeResult(SuccessorUiQueueCodec.encode(result)));
            JsonNode wire=SuccessionCodec.parse(response.result().bytes());
            assertFalse(wire.get("submission_authorized").booleanValue());assertFalse(wire.get("action_replay_authorized").booleanValue());
            assertEquals(0,wire.get("queries_performed").intValue());assertEquals(0,wire.get("new_natural_succession_credit").intValue());
            assertArrayEquals(before,SuccessionCodec.encode(input),"software variant input is caller-owned immutable DATA");
        }
    }

    @Test void currentActorTokensRejectAbsentAndUnsignedAliasesAcrossRequestAndResult() throws Exception {
        for(String token:List.of("-1","-2147483649","2147483648","4294967294","true","1.0","\"-2\"","null")) {
            JsonNode value=SuccessionCodec.parse(token.getBytes(StandardCharsets.UTF_8));
            ObjectNode input=withModernSuccessor(first(),value);
            assertThrows(IllegalArgumentException.class,()->SuccessorUiQueueCodec.evaluate(SuccessionCodec.encode(input)),token);
            ObjectNode output=object(SuccessionCodec.parse(SuccessorUiQueueCodec.apply(SuccessionCodec.encode(first())))).deepCopy();
            object(output.get("frame")).set("successor_character_id",value);
            assertThrows(IllegalArgumentException.class,()->SuccessorUiQueueCodec.decodeResult(SuccessionCodec.encode(output)),token);
        }
    }

    @Test void signedActorChangeDoesNotWidenSourceCountersOrReinterpretHistoricalGoalOrigin() throws Exception {
        ObjectNode input=first();
        // Origin is retained lineage DATA, not the current actor. Its original raw equality contract stays unchanged.
        JsonNode origin=SuccessionCodec.objectNode().put("id",new BigInteger("4294967294")).get("id");
        ObjectNode transition=object(input.get("transition")),app=object(input.get("app_response"));
        object(transition.get("campaign_goal_after")).set("origin_character_id",origin);
        for(JsonNode snapshot:List.of(app.get("snapshot"),input.get("independent_snapshot")))object(object(snapshot).get("campaign_goal")).set("origin_character_id",origin);
        if(app.get("transition") instanceof ObjectNode retained && retained.get("campaign_goal_after") instanceof ObjectNode goal)goal.set("origin_character_id",origin);
        assertInstanceOf(Observed.class,SuccessorUiQueueCodec.evaluate(SuccessionCodec.encode(input)));
        SourceFrame valid=SuccessorUiQueueCodec.decode(SuccessionCodec.encode(first())).originalSource();
        for(BigInteger invalid:List.of(BigInteger.ZERO,BigInteger.valueOf(-2))) {
            assertThrows(IllegalArgumentException.class,()->new SourceFrame(valid.snapshotId(),invalid,valid.nativeRevision(),valid.dateRaw(),valid.bridgePid(),valid.connectionGeneration()));
            assertThrows(IllegalArgumentException.class,()->new SourceFrame(valid.snapshotId(),valid.revision(),invalid,valid.dateRaw(),valid.bridgePid(),valid.connectionGeneration()));
            assertThrows(IllegalArgumentException.class,()->new SourceFrame(valid.snapshotId(),valid.revision(),valid.nativeRevision(),valid.dateRaw(),invalid,valid.connectionGeneration()));
            assertThrows(IllegalArgumentException.class,()->new SourceFrame(valid.snapshotId(),valid.revision(),valid.nativeRevision(),valid.dateRaw(),valid.bridgePid(),invalid));
        }
    }

    private static ObjectNode withModernSuccessor(ObjectNode input,JsonNode actor) {
        ObjectNode transition=object(input.get("transition")),app=object(input.get("app_response"));
        transition.set("successor_character_id",actor);object(transition.get("campaign_goal_after")).set("current_character_id",actor);
        if(app.get("transition") instanceof ObjectNode retained) {
            retained.set("successor_character_id",actor);
            if(retained.get("campaign_goal_after") instanceof ObjectNode goal)goal.set("current_character_id",actor);
        }
        for(JsonNode node:List.of(app.get("snapshot"),input.get("independent_snapshot"))) {
            ObjectNode snapshot=object(node);snapshot.set("episode_character_id",actor);object(snapshot.get("played_character")).set("character_id",actor);
            object(snapshot.get("campaign_goal")).set("current_character_id",actor);
        }
        return input;
    }

    private static ObjectNode first() throws IOException { return object(golden().path("cases").get(0).get("request")).deepCopy(); }
    private static ObjectNode object(JsonNode node) { if (node instanceof ObjectNode object) return object; throw new IllegalArgumentException("fixture object required"); }
    static JsonNode golden() throws IOException {
        return JsonMapper.builder(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS, DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                        DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).build().readTree(goldenBytes());
    }
    static byte[] goldenBytes() throws IOException {
        try (InputStream input = SuccessorUiQueueTest.class.getResourceAsStream("/g2/m3/original-resident-ui-golden.json")) {
            assertNotNull(input, "actual original registered-App capture required; missing environment fails");
            return input.readAllBytes();
        }
    }
}
