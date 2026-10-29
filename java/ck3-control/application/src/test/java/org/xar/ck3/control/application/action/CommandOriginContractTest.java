package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual command/read/effect contracts share one codec; fixtures confer no runtime permission. */
final class CommandOriginContractTest {
    private static final Instant NOW = Instant.parse("2026-10-23T15:00:00Z");
    private static final String MACHINE = "test-machine";
    private static final BigInteger CONNECTION = new BigInteger("9007199254740993");
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    private static final ExactRef BEFORE = ref("frontend-before", 'a');
    private static final ExactRef AFTER = ref("frontend-after", 'b');
    private static final ExactRef HELLO = ref("capabilities", 'c');
    private static final G2Source SOURCE = new G2Source(MACHINE, NOW.toString(), "1.20.0.4", ref("source", 'd'));
    private static final JointBudgetSelector.Claims EMPTY = new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of());
    private static final List<ExpectedValue> VALUES = List.of(new ExpectedBoolean(new FieldKey("ready"), true),
            new ExpectedNull(new FieldKey("nullable")), new ExpectedAbsent(new FieldKey("absent")));
    private static ExactRef ref(String name, char digest) {
        return new ExactRef(java.nio.file.Path.of("synthetic-contract-fixture", name + ".json").toAbsolutePath().normalize().toString(),
                1, String.valueOf(digest).repeat(64));
    }
    private static FrontendIdentity frontend(FrontendFrame frame, ExactRef packet) {
        return new FrontendIdentity(MACHINE, GAME, "frontend-1", CONNECTION, GAME.pid(), frame, packet, HELLO);
    }
    private static FrontendIdentity menu(int sequence, ExactRef packet) { return frontend(new FrontendFrame.Menu(BigInteger.valueOf(sequence)), packet); }
    private static ActionCommand ordinary(FrontendIdentity origin) {
        return new ActionCommand("frontend-action", new CommandOrigin.Frontend(origin), SOURCE, origin.frontendSessionId(),
                new OperationKey("query-rules-fixture"), new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.Frontend(new FrontendExpectedPostcondition(origin, SOURCE, "frontend-fixture/v1", VALUES)), EMPTY, NOW.plusSeconds(30));
    }
    private static List<ExpectedValue> entryValues() {
        return List.of(new ExpectedText(new FieldKey("selected_bookmark_key"), "bm_1066_rags_to_riches"),
                new ExpectedText(new FieldKey("selected_character_name_key"), "bookmark_rags_to_riches_duke_robert"),
                new ExpectedInteger(new FieldKey("date_raw"), BigInteger.valueOf(100)),
                new ExpectedBoolean(new FieldKey("map_ready"), true), new ExpectedBoolean(new FieldKey("paused"), true));
    }
    private static ActionCommand entry(FrontendIdentity origin) {
        return new ActionCommand("start-action", new CommandOrigin.Frontend(origin), SOURCE, origin.frontendSessionId(),
                new OperationKey("start-selected-fixture"), new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.GameplayEntry(new FrontendGameplayExpectedPostcondition(origin, SOURCE, "entry-fixture/v1",
                        "bm_1066_rags_to_riches", "bookmark_rags_to_riches_duke_robert", 100, entryValues())), EMPTY, NOW.plusSeconds(30));
    }
    private static GuardEvidence guard(FrontendIdentity origin, OperationKey operation) {
        return new GuardEvidence(new CommandOrigin.Frontend(origin), SOURCE, origin.frontendSessionId(), origin.connectionGeneration(), operation,
                origin.nativeEvidence(), origin.capabilityEvidence(), "authority-1", NOW, NOW.plusSeconds(20));
    }
    private static NativeRequest nativeRequest(OperationKey operation) {
        return new NativeRequest(operation.value(), "game.command.fixture", new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
    }
    private static ActionState.Attempt attempt(ActionCommand command) {
        return new ActionState.Attempt("submitted-request", NOW, guard(command.origin().requireFrontend(), command.operation()), nativeRequest(command.operation()));
    }
    private static ObservationIdentity gameplay(BigInteger actor) {
        return new ObservationIdentity(MACHINE, GAME, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(actor, BigInteger.TWO, BigInteger.valueOf(100)), "native:2", BigInteger.TWO, "episode-new"), 1);
    }
    private static SemanticEvidence semantic(BigInteger actor, Instant at, ExactRef packet) {
        return new SemanticEvidence(gameplay(actor), ref("semantic", 'e'), packet, ref("stamp", 'f'), ref("driver", '0'), at);
    }
    private static FrontendGameplayObservation entered(ActionCommand command, BigInteger actor, Instant at, ExactRef packet) {
        return new FrontendGameplayObservation(command.origin().requireFrontend(), SOURCE,
                new SessionIdentity(MACHINE, GAME, "gameplay-1"), CONNECTION, "entry-fixture/v1", entryValues(), semantic(actor, at, packet),
                rootRead(actor, at, packet), List.of(ref("start-basis", '8')));
    }
    private static PlanningReadReceipt rootRead(BigInteger actor, Instant at, ExactRef packet) {
        var operation = new OperationKey("query-campaign-root-context-v1");
        var binding = new GuardEvidence(gameplay(actor), SOURCE, "gameplay-1", CONNECTION, operation, packet, HELLO,
                "campaign-root-fixture-authority", at, at.plusSeconds(20));
        var guard = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
        var request = new PlanningReadRequest(gameplay(actor), SOURCE, "gameplay-1", operation, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(30));
        var ack = new NativeActionPort.AckReceived("campaign-root-read", true, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[]{1});
        return new PlanningReadReceipt(request, "campaign-root-fixture/v1", "campaign-root-read", guard, guard, ack);
    }
    private static ObjectNode object(byte[] bytes) { return (ObjectNode) StrictJson.parse(bytes, ActionCodec.MAX_COMMAND_BYTES); }
    private static byte[] bytes(ObjectNode value) { return ProposalLifecycleCodec.encodePayload(value); }

    @Test void menuHasNoGameplayPlayerEpisodeOrReadinessFlags() {
        ActionCommand command = ordinary(menu(1, BEFORE));
        assertEquals(BigInteger.ZERO, command.origin().expectedRevision());
        assertThrows(IllegalStateException.class, command::before); assertThrows(IllegalStateException.class, command::expected);
        assertThrows(IllegalStateException.class, () -> guard(command.origin().requireFrontend(), command.operation()).observed());
        PlanningReadGuard read = new PlanningReadGuard(guard(command.origin().requireFrontend(), command.operation()), "a".repeat(64));
        assertEquals(ReadContract.GuardMode.FRONTEND_SESSION, read.guardMode());
        assertThrows(IllegalStateException.class, read::paused); assertThrows(IllegalStateException.class, read::mapReady);
        ObjectNode wire = object(ActionCodec.encodeCommand(command));
        assertFalse(wire.has("before")); assertFalse(wire.get("origin").get("identity").has("player"));
        assertEquals(command, ActionCodec.decodeCommand(bytes(wire)));
    }
    @Test void snapshotKeepsExactPositiveNativeRevisionAndOneShotPermit() {
        BigInteger nativeRevision = new BigInteger("9007199254740995");
        ActionCommand command = ordinary(frontend(new FrontendFrame.Snapshot("frontend:9", BigInteger.valueOf(9), nativeRevision, -1, BigInteger.ONE), BEFORE));
        SubmissionPermit permit = new SubmissionPermit(command, ActionCodec.bodySha256(command), 1, "request", NOW,
                guard(command.origin().requireFrontend(), command.operation()), nativeRequest(command.operation()));
        assertEquals(nativeRevision, permit.expectedRevision()); assertEquals(command.origin(), permit.origin());
        assertThrows(IllegalStateException.class, permit::before); permit.consumeOnce(); assertThrows(IllegalStateException.class, permit::consumeOnce);
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
    }
    @Test void processBirthAndConnectionStayCanonicalDecimalStrings() {
        FrontendIdentity origin = menu(1, BEFORE); ObjectNode wire = CommandOriginCodec.frontend(origin);
        assertEquals("133700000000000001", wire.get("game").get("creation_filetime").textValue());
        assertEquals(CONNECTION.toString(), wire.get("connection_generation").textValue());
        assertEquals(origin, CommandOriginCodec.frontend(wire));
        ObjectNode booleanPid = wire.deepCopy(); ((ObjectNode) booleanPid.get("game")).put("pid", true);
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontend(booleanPid));
        ObjectNode numericBirth = wire.deepCopy(); ((ObjectNode) numericBirth.get("game")).put("creation_filetime", new BigInteger("133700000000000001"));
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontend(numericBirth));
        ObjectNode floatConnection = wire.deepCopy(); floatConnection.put("connection_generation", 1.0);
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontend(floatConnection));
        ObjectNode leadingZero = wire.deepCopy(); leadingZero.put("connection_generation", "01");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontend(leadingZero));
    }
    @Test void boundaryRejectsMissingNullWrongFieldAndCrossPhaseSchema() {
        ActionCommand command = ordinary(menu(1, BEFORE)); ObjectNode wire = object(ActionCodec.encodeCommand(command));
        ObjectNode missing = wire.deepCopy(); missing.remove("expectation");
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(missing)));
        ObjectNode nulled = wire.deepCopy(); nulled.putNull("origin");
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(nulled)));
        ObjectNode alias = wire.deepCopy(); alias.put("before", "unmigrated");
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(alias)));
        ObjectNode gameplayOrigin = wire.deepCopy(); gameplayOrigin.set("origin", CommandOriginCodec.origin(new CommandOrigin.Gameplay(gameplay(BigInteger.ONE))));
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(gameplayOrigin)));
        ObjectNode wrongKind = wire.deepCopy(); ((ObjectNode) wrongKind.get("expectation")).put("kind", "GAMEPLAY");
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(bytes(wrongKind)));
    }
    @Test void frontendGuardRoundtripNeverUsesGameplayObservationOrNumericIdentity() {
        GuardEvidence value = guard(menu(1, BEFORE), new OperationKey("read-fixture"));
        ObjectNode encoded = CommandOriginCodec.guard(value); assertFalse(encoded.has("observed"));
        assertEquals(value, CommandOriginCodec.guard(encoded));
        ObjectNode unknown = encoded.deepCopy(); unknown.put("schema", "xar.frontend-guard/v2");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.guard(unknown));
        ObjectNode extra = encoded.deepCopy(); extra.put("observed", "fake-gameplay");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.guard(extra));
    }
    @Test void supportingGuardClosureUsesStrictV2AndNeverReplacesOriginalHello() {
        GuardEvidence legacy = guard(menu(1, BEFORE), new OperationKey("read-fixture"));
        GuardEvidence value = new GuardEvidence(legacy.origin(), legacy.source(), legacy.sessionId(), legacy.connectionGeneration(), legacy.operation(),
                legacy.nativeEvidence(), legacy.capabilityEvidence(), legacy.authorityId(), legacy.observedAt(), legacy.validUntil(), List.of(ref("support-basis", '2')));
        ObjectNode wire = CommandOriginCodec.guard(value);
        assertEquals("xar.command-guard/v2", wire.get("schema").textValue()); assertEquals(HELLO.toJson(), wire.get("capability_evidence"));
        assertEquals(value, CommandOriginCodec.guard(wire));
        ObjectNode missing = wire.deepCopy(); missing.remove("supporting_evidence");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.guard(missing));
        ObjectNode empty = wire.deepCopy(); empty.putArray("supporting_evidence");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.guard(empty));
        ObjectNode duplicated = wire.deepCopy(); ((com.fasterxml.jackson.databind.node.ArrayNode) duplicated.get("supporting_evidence")).add(value.supportingEvidence().get(0).toJson());
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.guard(duplicated));
    }
    @Test void frontendEffectNeedsIndependentLaterNativeReadAndRetainsNullVersusAbsent() {
        ActionCommand command = ordinary(menu(1, BEFORE)); ActionState.Attempt attempt = attempt(command);
        FrontendEffectObservation valid = new FrontendEffectObservation(menu(2, AFTER), SOURCE, "frontend-1", "frontend-fixture/v1", VALUES,
                "independent-read", NOW.plusSeconds(1), AFTER);
        assertDoesNotThrow(() -> valid.validate(command, attempt));
        assertEquals(valid, CommandOriginCodec.frontendEffect(CommandOriginCodec.frontendEffect(valid)));
        FrontendEffectObservation ack = new FrontendEffectObservation(menu(2, AFTER), SOURCE, "frontend-1", "frontend-fixture/v1", VALUES,
                attempt.requestId(), NOW.plusSeconds(1), AFTER);
        assertThrows(IllegalArgumentException.class, () -> ack.validate(command, attempt));
        ExactRef alias = new ExactRef("D:/synthetic-contract-fixture/copied-before.json", BEFORE.bytes(), BEFORE.sha256());
        FrontendEffectObservation oldPacket = new FrontendEffectObservation(menu(2, alias), SOURCE, "frontend-1", "frontend-fixture/v1", VALUES,
                "independent-read", NOW.plusSeconds(1), alias);
        assertThrows(IllegalArgumentException.class, () -> oldPacket.validate(command, attempt));
        FrontendEffectObservation sameSequence = new FrontendEffectObservation(menu(1, AFTER), SOURCE, "frontend-1", "frontend-fixture/v1", VALUES,
                "independent-read", NOW.plusSeconds(1), AFTER);
        assertThrows(IllegalArgumentException.class, () -> sameSequence.validate(command, attempt));
        ObjectNode absentWithNull = CommandOriginCodec.frontendEffect(valid); ((ObjectNode) absentWithNull.get("actual").get(2)).putNull("value");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontendEffect(absentWithNull));
    }
    @Test void readReceiptPreservesFrontendPhaseAndRejectsFalseAckOrConnectionDrift() {
        ActionCommand template = ordinary(menu(1, BEFORE)); OperationKey op = template.operation();
        PlanningReadRequest request = new PlanningReadRequest(template.origin(), SOURCE, template.sessionId(), op, template.arguments(), template.deadline());
        PlanningReadGuard before = new PlanningReadGuard(guard(menu(1, BEFORE), op), "a".repeat(64));
        PlanningReadGuard after = new PlanningReadGuard(guard(menu(2, AFTER), op), "a".repeat(64));
        NativeActionPort.AckReceived ack = new NativeActionPort.AckReceived("read-1", true, Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)), new byte[]{1});
        PlanningReadReceipt receipt = new PlanningReadReceipt(request, "contract", "read-1", before, after, ack);
        assertEquals(ReadContract.GuardMode.FRONTEND_SESSION, receipt.after().guardMode());
        NativeActionPort.AckReceived rejected = new NativeActionPort.AckReceived("read-1", false, Optional.empty(), ack.originalFrame(), ack.originalPacket());
        assertThrows(IllegalArgumentException.class, () -> new PlanningReadReceipt(request, "contract", "read-1", before, after, rejected));
        FrontendIdentity changed = new FrontendIdentity(MACHINE, GAME, "frontend-1", CONNECTION.add(BigInteger.ONE), GAME.pid(), new FrontendFrame.Menu(BigInteger.TWO), AFTER, HELLO);
        PlanningReadGuard drift = new PlanningReadGuard(guard(changed, op), "a".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> new PlanningReadReceipt(request, "contract", "read-1", before, drift, ack));
    }
    @Test void archivedReadRequestAndReadinessUseTheirOneStrictCodec() {
        ActionCommand template = ordinary(menu(1, BEFORE));
        PlanningReadRequest request = new PlanningReadRequest(template.origin(), SOURCE, template.sessionId(), template.operation(), template.arguments(), template.deadline());
        ObjectNode wire = CommandOriginCodec.planningRequest(request, ref("arguments", '1'));
        assertEquals(request, CommandOriginCodec.planningRequest(wire, request.arguments()));
        PlanningReadGuard readGuard = new PlanningReadGuard(guard(menu(1, BEFORE), template.operation()), "a".repeat(64));
        assertEquals(readGuard, CommandOriginCodec.planningGuard(CommandOriginCodec.planningGuard(readGuard)));
        ObjectNode wrong = CommandOriginCodec.planningGuard(readGuard); wrong.set("readiness", CommandOriginCodec.readiness(new PlanningReadGuard.Gameplay(true, true, true)));
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.planningGuard(wrong));
        ObjectNode missing = wire.deepCopy(); missing.remove("arguments_ref");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.planningRequest(missing, request.arguments()));
        ObjectNode booleanReadiness = StrictJson.object(); booleanReadiness.put("paused", 1); booleanReadiness.put("map_ready", true); booleanReadiness.put("player_alive", true);
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.readiness(booleanReadiness));
    }
    @Test void gameplayEntryHasDedicatedExpectationAndOriginalUnsolicitedSemanticPublication() {
        ActionCommand command = entry(menu(1, BEFORE));
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        assertInstanceOf(CommandOrigin.Frontend.class, command.expectation().origin());
        assertThrows(IllegalStateException.class, command.expectation()::requireFrontend);
        FrontendGameplayObservation valid = entered(command, BigInteger.valueOf(29829), NOW.plusSeconds(1), AFTER);
        assertDoesNotThrow(() -> valid.validate(command, attempt(command)));
        ObjectNode wire = CommandOriginCodec.gameplayEntry(valid, ignored -> ref("root-read", '9')); assertFalse(wire.has("read_request_id"));
        assertEquals(valid, CommandOriginCodec.gameplayEntry(wire, actual -> { assertEquals(ref("root-read", '9'), actual); return valid.campaignRootRead(); }));
        assertEquals(5, valid.references().size());
        assertThrows(IllegalStateException.class, () -> valid.validate(ordinary(menu(1, BEFORE)), attempt(command)));
    }
    @Test void gameplayEntryRejectsRootActorDriftPriorPacketAndCrossBirth() {
        ActionCommand command = entry(menu(1, BEFORE)); ActionState.Attempt attempt = attempt(command);
        assertThrows(IllegalArgumentException.class, () -> new FrontendGameplayObservation(command.origin().requireFrontend(), SOURCE,
                new SessionIdentity(MACHINE, GAME, "gameplay-1"), CONNECTION, "entry-fixture/v1", entryValues(),
                semantic(BigInteger.valueOf(29829), NOW.plusSeconds(1), AFTER), rootRead(BigInteger.ONE, NOW.plusSeconds(1), AFTER), List.of(ref("start-basis", '8'))));
        assertThrows(IllegalArgumentException.class, () -> entered(command, BigInteger.valueOf(29829), NOW.minusSeconds(1), AFTER).validate(command, attempt));
        assertThrows(IllegalArgumentException.class, () -> entered(command, BigInteger.valueOf(29829), NOW.plusSeconds(1), BEFORE).validate(command, attempt));
        GameGeneration replacement = new GameGeneration(GAME.pid(), new PythonOnlyUInt64(GAME.creationFiletime().value().add(BigInteger.ONE)));
        assertThrows(IllegalArgumentException.class, () -> new FrontendGameplayObservation(command.origin().requireFrontend(), SOURCE,
                new SessionIdentity(MACHINE, replacement, "gameplay-1"), CONNECTION, "entry-fixture/v1", entryValues(),
                semantic(BigInteger.valueOf(29829), NOW.plusSeconds(1), AFTER), rootRead(BigInteger.valueOf(29829), NOW.plusSeconds(1), AFTER), List.of(ref("start-basis", '8'))));
        FrontendIdentity snapshot = frontend(new FrontendFrame.Snapshot("frontend:1", BigInteger.ONE, BigInteger.ONE, 100, BigInteger.ONE), BEFORE);
        assertThrows(IllegalArgumentException.class, () -> entry(snapshot));
    }
    @Test void gameplayEntryExpectationUsesTheActualSelectedKeysAndRejectsTheOldInventedActorField() {
        var command = entry(menu(1, BEFORE)); var encoded = CommandOriginCodec.expectation(command.expectation());
        assertFalse(encoded.has("player_character_id")); assertEquals("bm_1066_rags_to_riches", encoded.get("selected_bookmark_key").textValue());
        assertEquals(command.expectation(), CommandOriginCodec.expectation(encoded));
        var staleActor = encoded.deepCopy(); staleActor.put("player_character_id", 29829);
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.expectation(staleActor));
        var booleanDate = encoded.deepCopy(); booleanDate.put("selected_date_raw", true);
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.expectation(booleanDate));
        var missingName = encoded.deepCopy(); missingName.remove("selected_character_name_key");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.expectation(missingName));
        var valid = entered(command, BigInteger.valueOf(29829), NOW.plusSeconds(1), AFTER);
        var wire = CommandOriginCodec.gameplayEntry(valid, ignored -> ref("root-read", '9'));
        var missingRoot = wire.deepCopy(); missingRoot.remove("campaign_root_read");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.gameplayEntry(missingRoot, ignored -> valid.campaignRootRead()));
        var emptyProof = wire.deepCopy(); emptyProof.putArray("supporting_evidence");
        assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.gameplayEntry(emptyProof, ignored -> valid.campaignRootRead()));
    }
    @Test void composedActionArgumentsHaveTheirExplicitBoundaryAndRoundtripPastOldCaps() {
        ActionCommand template = ordinary(menu(1, BEFORE));
        int overhead = DriverJson.encode(new OpportunityJson.Obj(Map.of("payload", new OpportunityJson.Text("")))).length;
        OpportunityJson.Obj full = new OpportunityJson.Obj(Map.of("payload", new OpportunityJson.Text("x".repeat(ActionCommand.MAX_ARGUMENT_BYTES - overhead))));
        assertEquals(ActionCommand.MAX_ARGUMENT_BYTES, DriverJson.encode(full).length);
        ActionCommand command = new ActionCommand(template.actionId(), template.origin(), template.source(), template.sessionId(), template.operation(),
                full, template.expectation(), template.claims(), template.deadline());
        byte[] encoded = ActionCodec.encodeCommand(command); assertTrue(encoded.length > 262_144); assertTrue(encoded.length <= ActionCodec.MAX_COMMAND_BYTES);
        assertEquals(command, ActionCodec.decodeCommand(encoded));
        OpportunityJson.Obj oversized = new OpportunityJson.Obj(Map.of("payload", new OpportunityJson.Text("x".repeat(ActionCommand.MAX_ARGUMENT_BYTES - overhead + 1))));
        assertThrows(IllegalArgumentException.class, () -> new ActionCommand(template.actionId(), template.origin(), template.source(), template.sessionId(), template.operation(),
                oversized, template.expectation(), template.claims(), template.deadline()));
        byte[] tooLargeCommand = new byte[ActionCodec.MAX_COMMAND_BYTES + 1]; java.util.Arrays.fill(tooLargeCommand, (byte) ' ');
        System.arraycopy(encoded, 0, tooLargeCommand, 0, encoded.length);
        assertThrows(IllegalArgumentException.class, () -> ActionCodec.decodeCommand(tooLargeCommand));
    }
    @Test void revisionlessCouncilMailboxProfileRequiresItsExactSourceQualifiedGameplayContract() {
        OperationKey operation = new OperationKey("private-council-application-main-status-v1");
        java.util.function.Function<PlanningReadRequest, NativeRequest> prepare = request -> new NativeRequest(operation.value(), Optional.empty(), new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        ReadContract<String> contract = new ReadContract<>("council-status/v1", operation, Optional.empty(), "council-source",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, SOURCE.sourceRef(), prepare, receipt -> "observed");
        assertEquals(ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS, contract.wireProfile());
        assertThrows(IllegalArgumentException.class, () -> new ReadContract<>("bad", operation, Optional.empty(), "council-source",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, SOURCE.sourceRef(), prepare, receipt -> "observed"));
        assertThrows(IllegalArgumentException.class, () -> new ReadContract<>("bad", operation, Optional.empty(), "council-source",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS,
                ReadContract.GuardMode.FRONTEND_SESSION, SOURCE.sourceRef(), prepare, receipt -> "observed"));
        assertThrows(IllegalArgumentException.class, () -> new ReadContract<>("bad", new OperationKey("another-op"), Optional.empty(), "council-source",
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, SOURCE.sourceRef(), prepare, receipt -> "observed"));
    }
}
