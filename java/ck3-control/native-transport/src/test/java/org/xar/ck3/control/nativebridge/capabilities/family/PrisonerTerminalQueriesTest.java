package org.xar.ck3.control.nativebridge.capabilities.family;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;

/** Synthetic origin/packet regression only. Real owning-writer session and original custody integration remain Root checks. */
final class PrisonerTerminalQueriesTest {
    private static final Instant NOW = Instant.parse("2026-10-23T18:45:00Z");
    private static final BigInteger REV = BigInteger.valueOf(56), NATIVE = BigInteger.valueOf(90);
    private static final long OLD = 101, NEW = 202;
    private static final String MACHINE = "synthetic-terminal-machine", SESSION = "synthetic-terminal-session";
    private static final OperationKey OPERATION = new OperationKey(PrisonerNativeQueries.STEP);
    private static ExactRef ref(String role) { return new ExactRef("synthetic/" + role, 1, Integer.toHexString(role.hashCode()).repeat(64).substring(0, 64)); }
    private static G2Source source() { return new G2Source(MACHINE, NOW.toString(), FamilyObligations.Build.CURRENT4.exactBuild(), ref("source")); }
    private static LifecycleIdentity identity() {
        return new LifecycleIdentity(MACHINE, new GameGeneration(321, new PythonOnlyUInt64(new BigInteger("133700000000000001"))), SESSION, BigInteger.valueOf(2),
                new LifecycleIdentity.Subject(BigInteger.valueOf(OLD), "original-old-episode", 3, 4),
                new LifecycleIdentity.Frame("native:90", REV, NATIVE, BigInteger.valueOf(53220000), true, true),
                new LifecycleIdentity.Character(BigInteger.valueOf(NEW), true), LifecycleIdentity.TerminalReason.CHANGED,
                new LifecycleIdentity.Evidence(ref("native"), ref("hello"), ref("manifest"), ref("driver"), ref("qualification")), NOW);
    }
    private static PlanningReadRequest request() {
        LifecycleIdentity actual = identity();
        return new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(actual), source(), SESSION, OPERATION, PrisonerTerminalQueries.arguments(actual), NOW.plusSeconds(30));
    }
    @Test void terminalProfileUsesActualNewActorAndRetainedOldTargetWithoutGameplayIdentity() throws Exception {
        PlanningReadRequest request = request(); assertThrows(IllegalStateException.class, request::before);
        var contract = PrisonerTerminalQueries.contract(ref("definition"), (original, actual, arguments) -> {
            assertEquals(BigInteger.valueOf(OLD), actual.subject().characterId()); assertEquals(OptionalLong.of(OLD), arguments.materialTarget());
        });
        assertEquals(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, contract.guardMode());
        NativeRequest nativeRequest = contract.prepare(request, "synthetic-read");
        assertEquals(StrictJson.object().put("release_material_target_character_id", OLD), StrictJson.parse(nativeRequest.additionalFields().bytes()));
        byte[] encoded = NativeWire.execute("synthetic-read", nativeRequest.step(), identity().frame().nativeRevision(), nativeRequest.additionalFields().bytes());
        JsonNode sent = NativeWire.parse(java.util.Arrays.copyOfRange(encoded, 4, encoded.length));
        assertEquals(NATIVE, sent.get("expected_revision").bigIntegerValue()); assertNotEquals(REV, sent.get("expected_revision").bigIntegerValue());
        var decoded = PrisonerTerminalQueries.decode(receipt(request, packet(new PrisonerMaterial12004.Dead(materialFrame()))));
        assertInstanceOf(PrisonerMaterial12004.Dead.class, decoded.retainedCustody().orElseThrow());
        ObjectNode normalized = assertInstanceOf(ObjectNode.class, StrictJson.parse(decoded.normalized().bytes()));
        assertEquals(OLD, normalized.get("queried_release_material_target_character_id").longValue());
        assertEquals(NEW, normalized.path("player_prisoner_collection").get("played_character_id").longValue());
        assertEquals(REV, normalized.get("queried_revision").bigIntegerValue()); assertEquals(NATIVE, normalized.get("queried_native_revision").bigIntegerValue());
    }
    @Test void terminalReadinessCannotBorrowOrdinaryFlagsAndWrongTargetCannotPrepare() {
        PlanningReadRequest original = request(); PlanningReadGuard guard = guard(original, identity(), "synthetic-authority");
        assertThrows(IllegalStateException.class, guard::paused); assertThrows(IllegalStateException.class, guard::playerAlive);
        var contract = PrisonerTerminalQueries.contract(ref("definition"), (actual, identity, arguments) -> { });
        var wrongArguments = PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(), OptionalLong.of(303));
        var wrong = new PlanningReadRequest(original.origin(), original.source(), original.sessionId(), original.operation(), wrongArguments, original.deadline());
        assertThrows(IllegalArgumentException.class, () -> contract.prepare(wrong, "synthetic-read"));
        var missing = new PlanningReadRequest(original.origin(), original.source(), original.sessionId(), original.operation(),
                PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(), OptionalLong.empty()), original.deadline());
        assertThrows(IllegalArgumentException.class, () -> contract.prepare(missing, "synthetic-read"));
    }
    @Test void actualOldStateFreeOrUnavailableIsPreservedAndNeverAssumedDead() throws Exception {
        for (PrisonerMaterial12004.Custody custody : List.of(new PrisonerMaterial12004.Free(materialFrame()), new PrisonerMaterial12004.UnavailableCustody(materialFrame(), "native_read_unavailable"))) {
            var decoded = PrisonerTerminalQueries.decode(receipt(request(), packet(custody)));
            assertEquals(custody, decoded.retainedCustody().orElseThrow()); assertFalse(decoded.retainedCustody().orElseThrow() instanceof PrisonerMaterial12004.Dead);
            assertArrayEquals(PrisonerMaterial12004.encode(custody), PrisonerMaterial12004.encode(decoded.retainedCustody().orElseThrow()));
        }
    }
    @Test void missingRetainedGroupWrongCurrentPlayerAndWrongNativeDateFailClosed() throws Exception {
        ObjectNode missing = packet(new PrisonerMaterial12004.Dead(materialFrame())); missing.remove("prisoner_retained_target_state");
        assertThrows(IllegalArgumentException.class, () -> PrisonerTerminalQueries.decode(receipt(request(), missing)));
        ObjectNode wrongActor = packet(new PrisonerMaterial12004.Dead(materialFrame())); ((ObjectNode) wrongActor.get("player_prisoner_collection")).put("played_character_id", OLD);
        assertThrows(IllegalArgumentException.class, () -> PrisonerTerminalQueries.decode(receipt(request(), wrongActor)));
        ObjectNode wrongDate = packet(new PrisonerMaterial12004.Dead(materialFrame())); ((ObjectNode) wrongDate.get("prisoner_retained_target_state")).put("date_raw", 1);
        assertThrows(IllegalArgumentException.class, () -> PrisonerTerminalQueries.decode(receipt(request(), wrongDate)));
        ObjectNode booleanTarget = packet(new PrisonerMaterial12004.Dead(materialFrame())); ((ObjectNode) booleanTarget.get("prisoner_retained_target_state")).put("target_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> PrisonerTerminalQueries.decode(receipt(request(), booleanTarget)));
    }
    @Test void originalActorStillCurrentOrDeadCannotObtainSuccessorReadAdmission() {
        LifecycleIdentity base = identity();
        LifecycleIdentity dead = new LifecycleIdentity(base.machineId(), base.game(), base.sessionId(), base.connectionGeneration(), base.subject(), base.frame(),
                new LifecycleIdentity.Character(BigInteger.valueOf(OLD), false), LifecycleIdentity.TerminalReason.DEAD, base.evidence(), base.observedAt());
        assertThrows(IllegalArgumentException.class, () -> PrisonerTerminalQueries.arguments(dead));
        LifecycleIdentity missing = new LifecycleIdentity(base.machineId(), base.game(), base.sessionId(), base.connectionGeneration(), base.subject(), base.frame(),
                new LifecycleIdentity.Missing(), LifecycleIdentity.TerminalReason.MISSING, base.evidence(), base.observedAt());
        assertThrows(IllegalArgumentException.class, () -> PrisonerTerminalQueries.arguments(missing));
        LifecycleIdentity noMap = new LifecycleIdentity(base.machineId(), base.game(), base.sessionId(), base.connectionGeneration(), base.subject(),
                new LifecycleIdentity.Frame(base.frame().snapshotId(), REV, NATIVE, base.frame().dateRaw(), true, false), base.currentPlayer(), base.terminalReason(), base.evidence(), base.observedAt());
        assertThrows(IllegalArgumentException.class, () -> PrisonerTerminalQueries.arguments(noMap));
    }
    private static PrisonerMaterial12004.Frame materialFrame() { return new PrisonerMaterial12004.Frame(NATIVE, 53220000, NEW, OLD); }
    private static ObjectNode packet(PrisonerMaterial12004.Custody custody) {
        ObjectNode root = StrictJson.object().put("step", PrisonerNativeQueries.STEP).put("accepted", true).put("status", "available").put("query_sequence", 11).put("observation_revision", 12).put("snapshot_revision", NATIVE)
                .put("private_build", true).put("read_only", true).put("advertised", false).put("backend_id", "native-headless");
        ObjectNode collection = StrictJson.object().put("schema", "player-prisoner-collection-private-v1").put("schema_version", 7).put("snapshot_revision", NATIVE).put("status", "available").put("date_raw", 53220000)
                .put("played_character_id", NEW).put("total_count", 0).put("returned_count", 0).put("collection_complete", true).put("played_dread_raw", 0);
        collection.putNull("unavailable_reason").putNull("played_house_id").putNull("played_dynasty_id"); collection.putArray("prisoners"); root.set("player_prisoner_collection", collection);
        root.set("prisoner_release_material_opinion", StrictJson.parse(PrisonerMaterial12004.encode(new PrisonerMaterial12004.UnavailableMaterial(materialFrame(), "retained_target_dead"))));
        root.set("prisoner_retained_target_state", StrictJson.parse(PrisonerMaterial12004.encode(custody))); return root;
    }
    private static PlanningReadGuard guard(PlanningReadRequest request, LifecycleIdentity actual, String authority) {
        GuardEvidence binding = new GuardEvidence(new CommandOrigin.LifecycleTerminal(actual), request.source(), request.sessionId(), actual.connectionGeneration(), request.operation(),
                actual.nativeEvidence(), actual.capabilityEvidence(), authority, NOW, NOW.plusSeconds(60), actual.supportingEvidence());
        return new PlanningReadGuard(binding, new PlanningReadGuard.LifecycleTerminal(), "1".repeat(64));
    }
    private static PlanningReadReceipt receipt(PlanningReadRequest request, ObjectNode nativeResult) throws Exception {
        String requestId = "synthetic-read"; ObjectNode frame = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", requestId).put("ok", true); frame.set("result", nativeResult);
        byte[] body = StrictJson.canonical(frame); NativeActionPort.AckReceived ack = new NativeActionPort.AckReceived(requestId, true, Optional.of(new RawJson(StrictJson.canonical(nativeResult))), new RawJson(body), NativeWire.packet(body));
        PlanningReadGuard guard = guard(request, identity(), "synthetic-authority");
        return new PlanningReadReceipt(request, PrisonerTerminalQueries.CONTRACT_ID, requestId, guard, guard, ack);
    }
}
