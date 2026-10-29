package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Fixed v1 contract fixtures, independent of the new origin encoder and native evidence. */
final class LegacyGameplayCompatibilityTest {
    private static final String REF = "{\"bytes\":1,\"path\":\"D:/synthetic-contract-fixture/original.json\",\"sha256\":\"" + "a".repeat(64) + "\"}";
    private static final String BEFORE = "{\"frame\":{\"date_raw\":\"100\",\"episode_run_id\":\"episode-1\",\"native_revision\":\"1\",\"played_character_id\":\"29829\",\"revision\":\"1\",\"snapshot_id\":\"native:1\"},\"game\":{\"creation_filetime\":\"133700000000000001\",\"pid\":123},\"machine_id\":\"test-machine\",\"observation_version\":1}";
    private static final String SOURCE = "{\"exact_build\":\"1.20.0.4\",\"machine_id\":\"test-machine\",\"observed_at_utc\":\"2026-10-23T15:00:00Z\",\"source_ref\":" + REF + "}";
    private static final String EXPECTED = "{\"before\":" + BEFORE + ",\"observer_schema\":\"paused/v1\",\"source\":" + SOURCE + ",\"values\":[{\"field\":\"paused\",\"kind\":\"BOOLEAN\",\"value\":true}],\"version\":1}";
    private static final String COMMAND = "{\"action_id\":\"legacy-1\",\"arguments\":{},\"before\":" + BEFORE + ",\"claims\":{\"ally_character_ids\":[],\"army_ids\":[],\"character_ids\":[],\"commitment_keys\":[]},\"deadline\":\"2026-10-23T15:00:30Z\",\"expected\":" + EXPECTED + ",\"operation\":\"pause-map\",\"schema\":\"xar.java-action-command/v1\",\"session_id\":\"session-1\",\"source\":" + SOURCE + "}";
    private static final String GUARD = "{\"authority_id\":\"authority-1\",\"capability_evidence\":" + REF + ",\"connection_generation\":\"1\",\"native_evidence\":" + REF + ",\"observed\":" + BEFORE + ",\"observed_at\":\"2026-10-23T15:00:00Z\",\"operation\":\"pause-map\",\"session_id\":\"session-1\",\"source\":" + SOURCE + ",\"valid_until\":\"2026-10-23T15:00:20Z\"}";
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    @Test void gameplayCommandV1RetainsOriginalBytesAndDigest() {
        ActionCommand command = ActionCodec.decodeCommand(bytes(COMMAND));
        assertInstanceOf(CommandOrigin.Gameplay.class, command.origin());
        assertArrayEquals(bytes(COMMAND), ActionCodec.encodeCommand(command));
        assertEquals(ActionCodec.sha256(bytes(COMMAND)), ActionCodec.bodySha256(command));
        assertEquals(command.before(), command.origin().requireGameplay());
    }
    @Test void gameplayGuardV1RetainsOriginalBytesAndOldReadGuardLayout() {
        GuardEvidence guard = CommandOriginCodec.guard(StrictJson.parse(bytes(GUARD), ActionCodec.MAX_COMMAND_BYTES));
        assertArrayEquals(bytes(GUARD), ProposalLifecycleCodec.encodePayload(CommandOriginCodec.guard(guard)));
        PlanningReadGuard readGuard = new PlanningReadGuard(guard, true, true, true, "b".repeat(64));
        ObjectNode wire = CommandOriginCodec.planningGuard(readGuard);
        assertFalse(wire.has("schema")); assertFalse(wire.has("readiness")); assertTrue(wire.get("paused").booleanValue());
        assertEquals(readGuard, CommandOriginCodec.planningGuard(wire));
        PlanningReadRequest request = new PlanningReadRequest(guard.observed(), guard.source(), guard.sessionId(), guard.operation(),
                ActionCodec.decodeCommand(bytes(COMMAND)).arguments(), java.time.Instant.parse("2026-10-23T15:00:30Z"));
        ObjectNode requestWire = CommandOriginCodec.planningRequest(request, new ExactRef("D:/synthetic-contract-fixture/args.json", 2, "c".repeat(64)));
        assertFalse(requestWire.has("schema")); assertTrue(requestWire.has("before"));
        assertEquals(request, CommandOriginCodec.planningRequest(requestWire, request.arguments()));
    }
    @Test void gameplayV1UsesCurrentSignedActorDomainWithoutChangingWireBytesOrDigest() {
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE}) {
            String original = COMMAND.replace("\"played_character_id\":\"29829\"", "\"played_character_id\":\"" + actor + "\"");
            ActionCommand command = ActionCodec.decodeCommand(bytes(original));
            assertEquals(java.math.BigInteger.valueOf(actor), command.before().frame().identity().player());
            assertEquals(command.before(), command.origin().requireGameplay());
            assertArrayEquals(bytes(original), ActionCodec.encodeCommand(command));
            assertEquals(ActionCodec.sha256(bytes(original)), ActionCodec.bodySha256(command));
        }
    }
    @Test void gameplayV1RejectsAbsentNoncanonicalOutOfRangeAndWrongActorTokens() {
        for (String actor : java.util.List.of("-1", "2147483648", "-2147483649", "4294967294", "+1", "-0", "01", "-01", " 0")) {
            String invalid = COMMAND.replace("\"played_character_id\":\"29829\"", "\"played_character_id\":\"" + actor + "\"");
            assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(invalid)), actor);
        }
        for (String actor : java.util.List.of("0", "-2", "true", "0.0", "null")) {
            String invalid = COMMAND.replace("\"played_character_id\":\"29829\"", "\"played_character_id\":" + actor);
            assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(invalid)), actor);
        }
    }
    @Test void gameplayV1RejectsBooleanObservationVersion() {
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(COMMAND.replace("\"observation_version\":1", "\"observation_version\":true"))));
    }
    @Test void gameplayV1RejectsFloatingObservationVersion() {
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(COMMAND.replace("\"observation_version\":1", "\"observation_version\":1.0"))));
    }

}
