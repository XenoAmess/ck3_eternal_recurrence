package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual raw frame/Driver projection -> sole lifecycle factory -> command/read codecs. No current authority is faked. */
final class LifecycleOriginContractTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final BigInteger OLD = BigInteger.valueOf(29829);
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    private static ExactRef ref(String name, char hash) { return new ExactRef("D:/lifecycle-source-fixture/" + name, 10, String.valueOf(hash).repeat(64)); }
    private static final G2Source SOURCE = new G2Source("lifecycle-origin-fixture", NOW.toString(), "1.20.0.4", ref("source.java", 'a'));
    private static final ExactRef HELLO = ref("hello.packet", 'b'), SOURCE_PROOF = ref("source-proof.json", 'c');
    private record Fixture(DriverObservationAssembler.FullSnapshot full, ExactRef driver) { }
    private static Fixture fixture(LifecycleIdentity.CurrentPlayer player, OpportunityJson.Value originalReason) {
        var raw = new LinkedHashMap<String, OpportunityJson.Value>();
        raw.put("date_raw", new OpportunityJson.IntegerValue(BigInteger.valueOf(100))); raw.put("paused", new OpportunityJson.Bool(true)); raw.put("map_ready", new OpportunityJson.Bool(false));
        if (player instanceof LifecycleIdentity.Null) raw.put("played_character", OpportunityJson.Nil.INSTANCE);
        if (player instanceof LifecycleIdentity.Character character)
            raw.put("played_character", new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(character.characterId()), "alive", new OpportunityJson.Bool(character.alive()))));
        var nativeState = new OpportunityJson.Obj(raw); byte[] state = DriverJson.encode(nativeState);
        String envelope = "{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"native:5\",\"revision\":5,\"state\":" + new String(state, StandardCharsets.UTF_8) + "}";
        byte[] payload = envelope.getBytes(StandardCharsets.UTF_8); byte[] packet = ByteBuffer.allocate(payload.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        var transport = new NativeObservationPort.TransportSession(SOURCE.machineId(), GAME, new BigInteger("18446744073709551615"), "terminal-session");
        var actual = new NativeObservationPort.ObservedFrame(transport, "native:5", BigInteger.valueOf(5), new RawJson(state), packet, NOW);
        var empty = new DriverStateSnapshot.NullValue();
        var driver = new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("\\\\.\\pipe\\life", 123, OLD, "old-life"), List.of(), empty, empty, empty, empty, empty, empty, empty);
        var semantic = new LinkedHashMap<String, OpportunityJson.Value>(raw);
        semantic.put("snapshot_id", new OpportunityJson.Text("native:5")); semantic.put("native_revision", new OpportunityJson.IntegerValue(BigInteger.valueOf(5)));
        semantic.put("revision", new OpportunityJson.IntegerValue(BigInteger.valueOf(8))); semantic.put("episode_run_id", new OpportunityJson.Text("old-life"));
        semantic.put("one_life_terminal_reason", originalReason); semantic.put("succession_reconciliation", OpportunityJson.Nil.INSTANCE); semantic.put("one_life_settlement", OpportunityJson.Nil.INSTANCE);
        var full = new OpportunityJson.Obj(semantic);
        var facts = new DriverObservationFacts(driver, 7, 3, transport, actual.snapshotId(), actual.nativeRevision(), ActionCodec.sha256(state), BigInteger.valueOf(8), 1, SOURCE, full, ref("facts.json", 'd'));
        var evidence = new ExactRef("D:/lifecycle-source-fixture/native.packet", packet.length, ActionCodec.sha256(packet));
        var driverRef = new ExactRef("D:/lifecycle-source-fixture/driver.json", driver.encode().length, ActionCodec.sha256(driver.encode()));
        return new Fixture(new DriverObservationAssembler.FullSnapshot(actual, facts, full, evidence, DriverObservationAssembler.bindingSha256(full)), driverRef);
    }
    private static LifecycleOriginFactory.Projected project(Fixture f) {
        return assertInstanceOf(LifecycleOriginFactory.Projected.class, LifecycleOriginFactory.project(f.full(), HELLO, f.driver(), SOURCE_PROOF));
    }
    private static List<ExpectedValue> noCredit() {
        return List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), false), new ExpectedBoolean(new FieldKey("timeline.advance_verified"), false),
                new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), false));
    }
    private static ActionCommand command(LifecycleIdentity identity) {
        return new ActionCommand("actual-terminal", new CommandOrigin.LifecycleTerminal(identity), SOURCE, identity.sessionId(),
                LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL.key(), new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.LifecycleTerminal(new LifecycleExpectedPostcondition(identity, SOURCE, "lifecycle-fixture/v1",
                        LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL, noCredit())), new Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static GuardEvidence guard(LifecycleIdentity identity, OperationKey operation) {
        return new GuardEvidence(new CommandOrigin.LifecycleTerminal(identity), SOURCE, identity.sessionId(), identity.connectionGeneration(), operation,
                identity.nativeEvidence(), identity.capabilityEvidence(), "terminal-authority", NOW, NOW.plusSeconds(30), List.of(ref("guard-basis.json", 'e')));
    }
    @Test void missingAndExplicitNullRemainDifferentActualPlayerBranchesAndPreserveOriginalNullReason() {
        var missing = project(fixture(new LifecycleIdentity.Missing(), OpportunityJson.Nil.INSTANCE));
        var nullPlayer = project(fixture(new LifecycleIdentity.Null(), OpportunityJson.Nil.INSTANCE));
        assertInstanceOf(LifecycleIdentity.Missing.class, missing.identity().currentPlayer()); assertInstanceOf(LifecycleIdentity.Null.class, nullPlayer.identity().currentPlayer());
        assertNotEquals(missing.identity().currentPlayer(), nullPlayer.identity().currentPlayer());
        assertEquals(OLD, missing.identity().subject().characterId()); assertFalse(missing.identity().frame().mapReady());
        assertEquals(LifecycleIdentity.TerminalReason.MISSING, missing.identity().terminalReason());
        var provenance = OpportunityJson.object(missing.semantic().get("lifecycle_origin_reason_projection"), "provenance");
        assertEquals(OpportunityJson.Nil.INSTANCE, provenance.get("original_value")); assertEquals(new OpportunityJson.Bool(true), provenance.get("present"));
        assertEquals(new OpportunityJson.Text("played_character_missing"), missing.semantic().get("one_life_terminal_reason"));
    }
    @Test void actualDeadAndChangedActorNeverBecomeOrdinaryGameplayOrAnInventedSubject() {
        var dead = project(fixture(new LifecycleIdentity.Character(OLD, false), OpportunityJson.Nil.INSTANCE));
        var changed = project(fixture(new LifecycleIdentity.Character(BigInteger.valueOf(30000), true), OpportunityJson.Nil.INSTANCE));
        assertEquals(LifecycleIdentity.TerminalReason.DEAD, dead.identity().terminalReason()); assertEquals(LifecycleIdentity.TerminalReason.CHANGED, changed.identity().terminalReason());
        assertEquals(OLD, changed.identity().subject().characterId()); assertEquals(BigInteger.valueOf(30000), ((LifecycleIdentity.Character) changed.identity().currentPlayer()).characterId());
        var command = command(dead.identity()); assertThrows(IllegalStateException.class, command::before); assertThrows(IllegalStateException.class, command::expected);
        assertThrows(IllegalStateException.class, command.origin()::requireFrontend);
        assertInstanceOf(LifecycleOriginFactory.Unavailable.class, LifecycleOriginFactory.project(fixture(new LifecycleIdentity.Character(OLD, true), OpportunityJson.Nil.INSTANCE).full(), HELLO,
                fixture(new LifecycleIdentity.Character(OLD, true), OpportunityJson.Nil.INSTANCE).driver(), SOURCE_PROOF));
    }
    @Test void publicCommandAndReadCodecsRoundTripTheActualOriginWithoutLivingFlags() {
        var identity = project(fixture(new LifecycleIdentity.Null(), OpportunityJson.Nil.INSTANCE)).identity(); var command = command(identity);
        var encoded = ActionCodec.encodeCommand(command); assertEquals(command, ActionCodec.decodeCommand(encoded));
        assertEquals(ActionCodec.LIFECYCLE_COMMAND_SCHEMA, StrictJson.parse(encoded, ActionCodec.MAX_COMMAND_BYTES).get("schema").textValue());
        var operation = new OperationKey("query-current-timeline-blocker-context-v1"); var binding = guard(identity, operation);
        var guarded = new PlanningReadGuard(binding, new PlanningReadGuard.LifecycleTerminal(), identity.bindingSha256());
        assertEquals(ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION, guarded.guardMode()); assertThrows(IllegalStateException.class, guarded::playerAlive);
        assertEquals(guarded, CommandOriginCodec.planningGuard(CommandOriginCodec.planningGuard(guarded)));
        var request = new PlanningReadRequest(command.origin(), SOURCE, identity.sessionId(), operation, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(30));
        var row = CommandOriginCodec.planningRequest(request, ref("arguments.json", 'f')); assertFalse(row.has("before"));
        assertEquals(request, CommandOriginCodec.planningRequest(row, request.arguments())); assertThrows(IllegalStateException.class, request::before);
    }
    @Test void terminalReadContractCannotBeBorrowedByAFrontendOrOrdinaryReadiness() {
        var identity = project(fixture(new LifecycleIdentity.Missing(), OpportunityJson.Nil.INSTANCE)).identity(); var operation = new OperationKey("query-current-timeline-blocker-context-v1");
        var contract = new ReadContract<String>("terminal-query/v1", operation, Optional.of("game.command." + operation.value()), "actual-terminal-source",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,
                SOURCE.sourceRef(), request -> new NativeRequest(operation.value(), "game.command." + operation.value(), new RawJson("{}".getBytes(StandardCharsets.UTF_8))), ignored -> "data");
        var request = new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(identity), SOURCE, identity.sessionId(), operation, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(30));
        assertEquals(operation.value(), contract.prepare(request, "terminal-read-1").step());
        assertThrows(IllegalArgumentException.class, () -> new PlanningReadGuard(guard(identity, operation), true, true, true, identity.bindingSha256()));
        assertThrows(IllegalArgumentException.class, () -> new GuardEvidence(request.origin(), SOURCE, identity.sessionId(), identity.connectionGeneration(), operation,
                identity.nativeEvidence(), identity.capabilityEvidence(), "terminal-authority", NOW, NOW.plusSeconds(30)));
    }
    @Test void typedIdentityRejectsMissingWrongTypesEpochDriftAndFloatingIdentityTokens() {
        var identity = project(fixture(new LifecycleIdentity.Character(OLD, false), OpportunityJson.Nil.INSTANCE)).identity();
        var row = LifecycleIdentityCodec.encode(identity); assertEquals(identity, LifecycleIdentityCodec.decode(row));
        assertEquals("18446744073709551615", row.get("connection_generation").textValue());
        var missing = row.deepCopy(); missing.remove("subject"); assertThrows(IllegalArgumentException.class, () -> LifecycleIdentityCodec.decode(missing));
        var wrong = row.deepCopy(); wrong.put("connection_generation", new BigInteger("18446744073709551615")); assertThrows(IllegalArgumentException.class, () -> LifecycleIdentityCodec.decode(wrong));
        var bool = row.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) bool.get("subject")).put("driver_version", true); assertThrows(IllegalArgumentException.class, () -> LifecycleIdentityCodec.decode(bool));
        var falseDead = row.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) falseDead.get("current_player")).put("alive", true); assertThrows(IllegalArgumentException.class, () -> LifecycleIdentityCodec.decode(falseDead));
    }
    @Test void absentSourceMetadataRoundtripsWithoutChangingTheActualNativeGameAndPlayer() {
        Fixture f=fixture(new LifecycleIdentity.Character(OLD,false),OpportunityJson.Nil.INSTANCE);
        var projected=assertInstanceOf(LifecycleOriginFactory.Projected.class,LifecycleOriginFactory.project(f.full(),HELLO,f.driver(),Optional.empty()));
        var identity=projected.identity();
        assertTrue(identity.evidence().completeSourceQualification().isEmpty());
        assertEquals(GAME,identity.game());assertEquals(OLD,identity.subject().characterId());
        var row=LifecycleIdentityCodec.encode(identity);
        assertTrue(row.path("evidence").get("complete_source_qualification").isNull());
        assertEquals(identity,LifecycleIdentityCodec.decode(row));
        assertEquals(command(identity),ActionCodec.decodeCommand(ActionCodec.encodeCommand(command(identity))));
        ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("evidence")).remove("complete_source_qualification");
        assertEquals(identity,LifecycleIdentityCodec.decode(row));
        ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("evidence")).put("complete_source_qualification",true);
        assertThrows(IllegalArgumentException.class,()->LifecycleIdentityCodec.decode(row));
        var physical=new PhysicalStatusIdentity(f.full().actual().session(),f.full().actual().snapshotId(),f.full().actual().nativeRevision(),SOURCE,
                f.full().originalEvidence(),HELLO,ref("heartbeat.packet",'e'),Optional.empty(),Optional.empty(),NOW);
        var status=PhysicalStatusIdentityCodec.encode(physical);
        assertTrue(status.get("source_qualification").isNull());assertTrue(status.get("epoch_manifest").isNull());
        assertEquals(physical,PhysicalStatusIdentityCodec.decode(status));
        status.remove("source_qualification");status.remove("epoch_manifest");
        assertEquals(physical,PhysicalStatusIdentityCodec.decode(status));
        status.putArray("source_qualification");assertThrows(IllegalArgumentException.class,()->PhysicalStatusIdentityCodec.decode(status));
    }
    @Test void subjectVersionMayAdvanceInsideTheSameEpisodeButMustNeverRegressOrChangeEpoch() {
        var original = project(fixture(new LifecycleIdentity.Null(), OpportunityJson.Nil.INSTANCE)).identity();
        var next = new LifecycleIdentity(original.machineId(), original.game(), original.sessionId(), original.connectionGeneration(),
                new LifecycleIdentity.Subject(OLD, "old-life", 3, 8), original.frame(), original.currentPlayer(), original.terminalReason(), original.evidence(), NOW);
        assertTrue(original.sameEpisode(next)); assertTrue(original.sameGuardFrame(next)); assertFalse(next.sameGuardFrame(original));
        var epoch = new LifecycleIdentity(original.machineId(), original.game(), original.sessionId(), original.connectionGeneration(),
                new LifecycleIdentity.Subject(OLD, "old-life", 4, 8), original.frame(), original.currentPlayer(), original.terminalReason(), original.evidence(), NOW);
        assertFalse(original.sameSession(epoch));
    }
    @Test void historicalSnapshotAndArchivedFullProjectionUseTheSameFactoryAndRejectContradictoryReason() {
        Fixture f = fixture(new LifecycleIdentity.Character(OLD, false), OpportunityJson.Nil.INSTANCE); var actual = f.full().actual(); var facts = f.full().facts();
        var known = new DriverSnapshotFacts.Known(facts.driver(), new DriverSnapshotFacts.Stamp(7, 3, GAME, "old-life", ActionCodec.sha256(facts.driver().encode())),
                ref("history-basis.json", 'e'), List.of(), new OpportunityJson.Obj(Map.of()), Optional.empty(), Optional.of(facts));
        var observed = new LifecycleObservationPort.Snapshot(actual, SOURCE, f.full().semantic(), known, f.full().originalEvidence());
        assertEquals(project(f), LifecycleOriginFactory.project(observed, facts, HELLO, f.driver(), SOURCE_PROOF));
        var derived = project(f);
        var reprojected = new DriverObservationAssembler.FullSnapshot(actual, facts, derived.semantic(), f.full().originalEvidence(), DriverObservationAssembler.bindingSha256(derived.semantic()));
        assertEquals(derived, LifecycleOriginFactory.project(reprojected, HELLO, f.driver(), SOURCE_PROOF));
        Fixture contradiction = fixture(new LifecycleIdentity.Character(OLD, false), new OpportunityJson.Text("played_character_changed"));
        assertInstanceOf(LifecycleOriginFactory.Unavailable.class, LifecycleOriginFactory.project(contradiction.full(), HELLO, contradiction.driver(), SOURCE_PROOF));
    }
    @Test void actualNativeEnvelopeAndUnknownAliveFieldsAreValidatedBeforeAProjectionExists() {
        Fixture f = fixture(new LifecycleIdentity.Null(), OpportunityJson.Nil.INSTANCE); var actual = f.full().actual();
        byte[] malformed = java.util.Arrays.copyOf(actual.originalPacket(), actual.originalPacket().length + 1);
        var changed = new NativeObservationPort.ObservedFrame(actual.session(), actual.snapshotId(), actual.nativeRevision(), actual.state(), malformed, actual.observedAt());
        var ref = new ExactRef("D:/lifecycle-source-fixture/malformed.packet", malformed.length, ActionCodec.sha256(malformed));
        var full = new DriverObservationAssembler.FullSnapshot(changed, f.full().facts(), f.full().semantic(), ref, f.full().fullBindingSha256());
        assertInstanceOf(LifecycleOriginFactory.Unavailable.class, LifecycleOriginFactory.project(full, HELLO, f.driver(), SOURCE_PROOF));
        var missingAlive = new OpportunityJson.Obj(Map.of("played_character", new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(OLD)))));
        assertThrows(IllegalArgumentException.class, () -> LifecycleOriginFactory.currentPlayer(missingAlive));
        var numericAlive = new OpportunityJson.Obj(Map.of("played_character", new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(OLD), "alive", new OpportunityJson.IntegerValue(BigInteger.ZERO)))));
        assertThrows(IllegalArgumentException.class, () -> LifecycleOriginFactory.currentPlayer(numericAlive));
    }
}
