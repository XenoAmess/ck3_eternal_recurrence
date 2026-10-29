package org.xar.ck3.control.nativebridge.capabilities.interactions;

import org.xar.ck3.control.contracts.NativeCharacterId;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePendingInteraction;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Explicit software Complete fixture exercises actual shared/domain/retained-argument consumers, not Root runtime admission. */
class NativePendingInteractionConsumerTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z"), DEADLINE = NOW.plusSeconds(30);
    private static final ExactRef SOURCE = new ExactRef("synthetic-pending-consumer-source", 1, "a".repeat(64));

    @Test void sharedNormalizedOriginalFlowsThroughRootProjectionAndExistingRetainedArgumentCodec() {
        for (int instance : new int[]{Integer.MIN_VALUE, -2, 0, 17, Integer.MAX_VALUE}) {
            ObjectNode original = StrictJson.object().put("instance_id", instance).put("sender_character_id", 501)
                    .put("auto_accept_notification", instance != 0).put("source", "discarded").put("extra", true);
            JsonNode normalized = NativePendingInteraction.normalize(original);
            Complete actual = fixture(normalized);
            Context projected = new RootInteractionContextProjection(Build.CROZIER4).project(actual, DEADLINE);
            assertEquals(new PendingId(instance), projected.controls().pending().instance());
            assertEquals(NativeCharacterId.of(501), projected.controls().pending().sender());
            assertEquals(instance != 0, projected.controls().pending().autoAcceptNotification());
            var request = new PlanningReadRequest(projected.before(), projected.source(), projected.sessionId(),
                    new OperationKey(PendingContextCodec.STEP), InteractionArguments.app(InteractionArguments.body(projected)), DEADLINE);
            assertEquals(projected, InteractionArguments.context(request));
            JsonNode wire = DriverJson.toNode(request.arguments());
            assertEquals(BigInteger.valueOf(instance), wire.path("group_context").path("controls").path("pending").path("instance_id").bigIntegerValue());
            RootInteractionContextProjection.requireExact(actual, projected);
        }
        assertNull(new RootInteractionContextProjection(Build.CROZIER4).project(fixture(NativePendingInteraction.normalize(
                StrictJson.object().path("absent"))), DEADLINE).controls().pending());
    }

    @Test void signedSenderPreservationAndInvalidSentinelRejection() {
        for (int sender : new int[]{Integer.MIN_VALUE, -2, 0, 17, Integer.MAX_VALUE}) {
            ObjectNode original = StrictJson.object().put("instance_id", 1).put("sender_character_id", sender).put("auto_accept_notification", false);
            JsonNode normalized = NativePendingInteraction.normalize(original);
            Complete actual = fixture(normalized);
            Context projected = new RootInteractionContextProjection(Build.CROZIER4).project(actual, DEADLINE);
            assertEquals(NativeCharacterId.of(sender), projected.controls().pending().sender());
            var request = new PlanningReadRequest(projected.before(), projected.source(), projected.sessionId(), new OperationKey(PendingContextCodec.STEP), InteractionArguments.app(InteractionArguments.body(projected)), DEADLINE);
            assertEquals(projected, InteractionArguments.context(request));
            ObjectNode wire = KnownPendingInteractionFixtures.wire(projected, "spar_with_knight_interaction");
            ObjectNode nativeContext = (ObjectNode) wire.get("pending_character_interaction_context");
            nativeContext.put("pending_interaction_id", projected.controls().pending().instance().value());
            ((ObjectNode) nativeContext.get("roles")).put("actor_character_id", sender);
            PendingContext decoded = PendingContextCodec.decode(InteractionJson.encode(wire), projected,
                    projected.controls().pending().instance());
            assertEquals(sender, decoded.roles().actor());
        }
        ObjectNode invalid = StrictJson.object().put("instance_id", 1).put("sender_character_id", -1).put("auto_accept_notification", false);
        assertThrows(IllegalArgumentException.class, () -> new RootInteractionContextProjection(Build.CROZIER4).project(fixture(NativePendingInteraction.normalize(invalid)), DEADLINE));
    }
    @Test void receiveIntegerParityDoesNotGrantDomainCharacterIdOrInvalidInstanceQualification() {
        ObjectNode original = StrictJson.object().put("instance_id", -2)
                .put("sender_character_id", new BigInteger("18446744073709551616123")).put("auto_accept_notification", false);
        JsonNode normalized = NativePendingInteraction.normalize(original);
        assertEquals(new BigInteger("18446744073709551616123"), normalized.get("sender_character_id").bigIntegerValue());
        assertThrows(IllegalArgumentException.class, () -> new RootInteractionContextProjection(Build.CROZIER4).project(fixture(normalized), DEADLINE));
        assertThrows(IllegalArgumentException.class, () -> new PendingId(-1));
        original.put("instance_id", -1);
        assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.normalize(original));
        original.put("instance_id", 0).put("sender_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> NativePendingInteraction.normalize(original));
    }
    @Test void signedPlayedEpisodeSpouseAndBetrothedUseTheSameDomainInActualAndRetainedContexts() {
        JsonNode pending=NativePendingInteraction.normalize(StrictJson.object().put("instance_id",-2).put("sender_character_id",17).put("auto_accept_notification",false));
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,17,Integer.MAX_VALUE}) {
            Complete actual=fixture(pending,actor,(long)Integer.MIN_VALUE,java.util.List.of(-2L,0L,(long)Integer.MAX_VALUE));
            Context c=new RootInteractionContextProjection(Build.CROZIER4).project(actual,DEADLINE);
            assertEquals(BigInteger.valueOf(actor),c.actor());assertEquals(actor,c.controls().episodeCharacterId());
            assertEquals((long)Integer.MIN_VALUE,c.controls().betrothedId());assertEquals(java.util.List.of(-2L,0L,(long)Integer.MAX_VALUE),c.controls().spouseIds());
            RootInteractionContextProjection.requireExact(actual,c);
            var request=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),new OperationKey(PendingContextCodec.STEP),InteractionArguments.app(InteractionArguments.body(c)),DEADLINE);
            assertEquals(c,InteractionArguments.context(request));
        }
        assertThrows(IllegalArgumentException.class,()->new RootInteractionContextProjection(Build.CROZIER4).project(fixture(pending,-1,null,java.util.List.of()),DEADLINE));
        assertThrows(IllegalArgumentException.class,()->new RootInteractionContextProjection(Build.CROZIER4).project(fixture(pending,707,-1L,java.util.List.of()),DEADLINE));
        assertThrows(IllegalArgumentException.class,()->new RootInteractionContextProjection(Build.CROZIER4).project(fixture(pending,707,null,java.util.List.of(-1L)),DEADLINE));
        assertThrows(IllegalArgumentException.class,()->new RootInteractionContextProjection(Build.CROZIER4).project(fixture(pending,707,null,java.util.List.of(-2L,-2L)),DEADLINE));
        var positive=new RootInteractionContextProjection(Build.CROZIER4).project(fixture(pending),DEADLINE);
        for(String field:java.util.List.of("episode_character_id","betrothed_id","spouse_ids")) {
            for(String token:java.util.List.of("-1","2147483648","4294967294","-2147483649","true","0.0","\"-2\"")) {
                ObjectNode body=InteractionArguments.body(positive);ObjectNode controls=(ObjectNode)body.path("group_context").get("controls");
                JsonNode value=DriverJson.toNode(DriverJson.object(("{\"value\":"+token+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8),65536)).get("value");
                controls.set(field,field.equals("spouse_ids")?StrictJson.object().putArray("ids").add(value):value);
                var invalid=new PlanningReadRequest(positive.before(),positive.source(),positive.sessionId(),new OperationKey(PendingContextCodec.STEP),InteractionArguments.app(body),DEADLINE);
                assertThrows(IllegalArgumentException.class,()->InteractionArguments.context(invalid),field+" token="+token);
            }
        }
    }

    private static Complete fixture(JsonNode pending) { return fixture(pending,707,null,java.util.List.of()); }
    static Complete fixture(JsonNode pending,int actor,Long betrothed,java.util.List<Long> spouses) {
        var identity = new ObservationIdentity("synthetic-pending-machine",
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(actor), BigInteger.valueOf(41), BigInteger.valueOf(24000)),
                        "synthetic-pending-frame", new BigInteger("9007199254740993"), "synthetic-pending-episode"), 1);
        var source = new G2Source(identity.machineId(), NOW.toString(), "1.20.0.4@sha256:" + Build.CROZIER4.sha256(), SOURCE);
        ObjectNode semantic = StrictJson.object().put("paused", true).put("map_ready", true).put("speed", 1)
                .put("local_player_id", 707).put("episode_character_id", actor).put("episode_run_id", identity.frame().episodeRunId());
        semantic.putNull("active_event"); semantic.set("pending_character_interaction", pending);
        ObjectNode player = semantic.putObject("played_character").put("character_id", actor).put("alive", true);
        if(betrothed==null)player.putNull("betrothed_id");else player.put("betrothed_id",betrothed);
        var spouseIds=player.putArray("spouse_ids");for(long spouse:spouses)spouseIds.add(spouse);
        semantic.putObject("diagnostics").putObject("hello").put("expected_ck3_version", Build.CROZIER4.version())
                .put("expected_ck3_sha256", Build.CROZIER4.sha256());
        return new Complete(identity, source, "synthetic-pending-session", BigInteger.ONE,
                DriverJson.object(DriverJson.encodeNode(semantic), 65536), SOURCE, NOW, "b".repeat(64));
    }
}
