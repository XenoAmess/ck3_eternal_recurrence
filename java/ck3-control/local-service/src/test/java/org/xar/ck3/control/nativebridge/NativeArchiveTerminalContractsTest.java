package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.time.Clock;
import java.util.ArrayDeque;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.PrisonerNativePackets12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;

/** Source-shaped original packets exercise sole production codecs/observers and a physical archive.
 * The fixture's real writer is reused; its source/hello are never relabeled as a qualified .4 package.
 * A separate explicitly synthetic .4 context is DATA only, with no readiness, submission or live credit.
 */
final class NativeArchiveTerminalContractsTest {
    @TempDir Path temp;
    private record Context(ActionWriterIntegrationFixture fixture, PlanningRequest base, G2Source source,
            ExactRef fullRef, RawJson fullDriver, ExactRef hello, ExactRef sourceProof, Instant now, Instant deadline) { }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static RawJson raw(String text) { return new RawJson(bytes(text)); }
    private static OpportunityJson.Obj empty() { return new OpportunityJson.Obj(Map.of()); }
    private static JointBudgetSelector.Claims noClaims() { return new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()); }
    private static Context context(ActionWriterIntegrationFixture fixture, boolean exactShape) throws Exception {
        var ready = fixture.ready(); var base = ready.request(); ExactRef full = ready.semanticEvidence().orElseThrow().originalDriver();
        G2Source source = exactShape ? new G2Source(base.source().machineId(), Instant.now().toString(),
                "1.20.0.4@sha256:" + CachedSuccession12004.EXE_SHA256, base.source().sourceRef()) : base.source();
        ExactRef hello;
        if (exactShape) {
            byte[] packet = NativeWire.packet(bytes("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":5,\"bridge_version\":\"controlled-source-shaped-test\",\"expected_ck3_sha256\":\""
                    + CachedSuccession12004.EXE_SHA256 + "\",\"expected_ck3_version\":\"1.20.0.4\",\"game_adapter_id\":\"ck3-1.20.0.4-msvc-x64\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}"));
            hello = fixture.writer.locked(session -> fixture.archive.preserveArtifact(session, packet, 65536));
        } else hello = fixture.lastNestedRead.get().after().binding().capabilityEvidence();
        ExactRef sourceProof = fixture.archive.preserveMaterial(raw("{\"controlled_source_context\":true,\"live_qualification\":false}"));
        return new Context(fixture, base, source, full, fixture.archive.loadMaterial(full), hello, sourceProof, Instant.now().minusSeconds(1), Instant.now().plusSeconds(25));
    }
    private static DriverObservationAssembler.Complete complete(Context c, NativeObservationPort.ObservedFrame frame) {
        ExactRef ref = c.fixture().archive.preserveNativeFrame(frame);
        var facts = NativeArchiveSupportingMaterialsTest.actualFacts(frame, c.source(), c.fullRef(), c.fullDriver(), c.fixture().archive);
        return assertInstanceOf(DriverObservationAssembler.Complete.class, new DriverObservationAssembler().assemble(frame, facts, ref));
    }
    private static GuardEvidence guard(Context c, DriverObservationAssembler.Complete frame, OperationKey operation) {
        return new GuardEvidence(frame.identity(), c.source(), frame.sessionId(), frame.connectionGeneration(), operation, frame.originalEvidence(), c.hello(),
                "controlled-software-guard", frame.observedAt(), c.deadline());
    }
    private static NativeActionPort.AckReceived reply(String id, byte[] result, NativeRequest prepared, BigInteger revision, boolean ok) throws IOException {
        byte[] packet = NativeWire.packet(bytes("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":" + ok + ",\"result\":" + new String(result, StandardCharsets.UTF_8) + "}"));
        var actual = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new NativeActionPort.AckReceived(id, ok, actual.result().token().map(value -> new RawJson(value.value())), new RawJson(actual.payload().value()), packet,
                Optional.of(new NativeActionPort.OutboundPacket(id, NativeWire.execute(id, prepared.step(), revision, prepared.additionalFields().bytes()))));
    }
    private static PlanningReadReceipt collection(Context c, DriverObservationAssembler.Complete frame, ReadContract<RawJson> contract,
            PlanningReadCoordinator reads, PrisonerSoftwarePackets packets, OpportunityJson.Obj arguments, byte[] result) {
        packets.nextResult = result.clone();
        var request = new PlanningReadRequest(frame.identity(), c.source(), frame.sessionId(), contract.operation(), arguments, c.deadline());
        var known = assertInstanceOf(PlanningReadResult.Known.class, reads.read(contract, request));
        var receipt = known.receipt(); receipt.original().custody().orElseThrow().verify(receipt); return receipt;
    }
    /** Only the external byte edge is controlled. The real native transport assigns endpoint order,
     * actual Instants, packet identities and custody epoch; no test constructs sampling chronology.
     */
    private static final class PrisonerSoftwarePackets implements NativePacketPort {
        final ArrayDeque<byte[]> queued = new ArrayDeque<>(); byte[] currentSnapshot; byte[] nextResult;
        PrisonerSoftwarePackets(byte[] hello, byte[] snapshot) { queued.add(hello.clone()); currentSnapshot = snapshot.clone(); queued.add(currentSnapshot.clone()); }
        void advance(byte[] snapshot) { currentSnapshot = snapshot.clone(); queued.addLast(currentSnapshot.clone()); }
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) { return queued.isEmpty() ? currentSnapshot.clone() : queued.removeFirst().clone(); }
        @Override public void writePacket(byte[] actual, Instant deadline) throws IOException {
            var request = NativeWire.decodeExecuteRequest(actual); assertNotNull(nextResult, "a complete raw schema6 response must be supplied");
            String result = new String(nextResult, StandardCharsets.UTF_8); nextResult = null;
            queued.addFirst(NativeWire.packet(bytes("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + request.requestId() + "\",\"ok\":true,\"result\":" + result + "}")));
        }
        @Override public void close() { }
    }
    @Test void actualFamilyDecoderPrisonerObserverArchiveAndSoleReplayKeepDeathAndTransferNonApplied() throws Exception {
        for (var terminal : PrisonerNativePackets12004.TerminalSource.values()) {
            try (var fixture = new ActionWriterIntegrationFixture(temp.resolve(terminal.name()), false)) {
                Context c = context(fixture, true);
                var nativeQueries = new PrisonerNativeQueries(c.source().sourceRef(), (ordinal, request, intent) -> {
                    assertEquals(0, ordinal); assertEquals(c.source(), request.source());
                });
                var contract = nativeQueries.contract(0);
                byte[] originalHello = fixture.writer.locked(session -> fixture.archive.readArtifact(session, c.hello(), 65536));
                var packets = new PrisonerSoftwarePackets(originalHello, NativeArchiveSupportingMaterialsTest.frame(c.base(), 9, false, c.now()).originalPacket());
                try (var transport = new NativeGameTransport(packets, new NativePipeEndpoint.Config("\\\\.\\pipe\\archive-prisoner-software", c.source().machineId(), c.base().before().game(),
                        c.base().sessionId(), "controlled-source-shaped-test", CachedSuccession12004.EXE_SHA256, "ck3-1.20.0.4-msvc-x64"), 64, 128)) {
                var before = complete(c, transport.observe(c.deadline()));
                var currentFrame = new java.util.concurrent.atomic.AtomicReference<>(before);
                var reads = new PlanningReadCoordinator(List.of(contract), fixture.journal, (head, request, installed) -> {
                    var actual = currentFrame.get(); assertEquals(request.before(), actual.identity()); assertEquals(c.source(), request.source());
                    return new PlanningReadGuard(guard(c, actual, installed.operation()), true, true, true, actual.fullBindingSha256());
                }, transport, fixture.archive, Clock.systemUTC());
                var selected = collection(c, before, contract, reads, packets, PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(), OptionalLong.empty()),
                        PrisonerNativePackets12004.selectedCollection(73, 88, before.identity().frame().identity().dateRaw().intValueExact(), BigInteger.valueOf(9), BigInteger.valueOf(11), BigInteger.valueOf(13)));
                ExactRef selectedRef = fixture.archive.readReferenceOf(selected);
                ObjectNode arguments = StrictJson.object().put("prisoner_character_id", 88).put("release_query_sequence", 11).put("release_option_mask_bits", 0);
                arguments.set("selected_collection_read", selectedRef.toJson()); arguments.putArray("active_war_ids"); arguments.putArray("war_retention_reads");
                OperationKey operation = PrisonerOrdinaryPolicy12004.RELEASE;
                var command = new ActionCommand("prisoner-terminal-" + terminal.name(), before.identity(), c.source(), before.sessionId(), operation,
                        OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(arguments)), "selected prisoner arguments"),
                        PrisonerActionBinding12004.expected(before.identity(), c.source(), operation, 88), PrisonerPlanningPorts.claims(88, 73), c.deadline());
                var preparation = new PrisonerActionBinding12004(fixture.archive, new PrisonerPlanningPorts.Queries(nativeQueries.contracts(), Map.of()));
                var prepared = preparation.prepare(command);
                var attempt = new ActionState.Attempt("prisoner-mutation", Instant.now(), guard(c, before, operation), prepared);
                var dispatch = new NativeActionPort.Unknown(attempt.requestId(), "controlled unknown original dispatch; never replay", new byte[0], Optional.empty());
                fixture.archive.preserve(dispatch);
                packets.advance(NativeArchiveSupportingMaterialsTest.frame(c.base(), 10, false, c.now()).originalPacket());
                var after = complete(c, transport.observe(c.deadline())); currentFrame.set(after);
                var afterRead = collection(c, after, contract, reads, packets, PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(), OptionalLong.of(88)),
                        PrisonerNativePackets12004.terminalCollection(73, 88, 99, after.identity().frame().identity().dateRaw().intValueExact(), BigInteger.TEN, BigInteger.valueOf(12), BigInteger.valueOf(14), terminal));
                var pair = new NativeEffectSnapshots.Pair(before, after);
                var projected = NativePrisonerEffects12004.projectOriginals(command, attempt, dispatch, pair, afterRead, preparation, contract, fixture.archive);
                var observation = assertInstanceOf(ActionPorts.TerminalObserved.class, projected.result()).observation();
                var original = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.NonAppliedTerminal(observation)));
                byte[] ledger = fixture.ledgerBytes(); ExactRef ref = fixture.archive.preserveReceipt(original); var restored = fixture.archive.loadReceipt(ref);
                assertEquals(original, restored); assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT, restored.outcome());
                assertFalse(restored.visibleGameplay()); assertFalse(restored.eligibleAdvance()); assertTrue(restored.settled());
                var frames = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
                assertDoesNotThrow(() -> NativePrisonerEffects12004.archivedVerifier(operation, c.source().sourceRef(), frames, contract, preparation).verifier().verify(null, restored, fixture.archive));
                RawJson previous = raw("{\"pending\":null,\"resolved\":{\"status\":\"older-retained-result\"}}");
                RawJson preparedPending = PrisonerLedgerReducer12004.prepare(PrisonerPlanningPorts.Family.RELEASE, previous, command, preparation.selected(command));
                RawJson retainedPending = fixture.archive.loadMaterial(fixture.archive.preserveMaterial(preparedPending));
                var pending = StrictJson.parse(retainedPending.bytes(), 1_048_576);
                assertTrue(pending.get("pending").isObject()); assertEquals("older-retained-result", pending.path("resolved").path("status").textValue());
                RawJson material = projected.compatibleResult().orElseThrow();
                var reduced = StrictJson.parse(PrisonerLedgerReducer12004.resolve(PrisonerPlanningPorts.Family.RELEASE, retainedPending, restored, material).bytes(), 1_048_576);
                assertTrue(reduced.get("pending").isNull());
                assertEquals(terminal == PrisonerNativePackets12004.TerminalSource.DEAD ? "dead" : "transferred", reduced.path("resolved").path("status").textValue());
                assertFalse(reduced.path("resolved").path("material_result").booleanValue());
                assertFalse(reduced.path("resolved").path("release_causation_observed").booleanValue());
                var unknown = new ActionReceipt(1, 1, command, original.bodySha256(), new ActionState.Unknown(Optional.of(attempt), Optional.of(dispatch), "retained UNKNOWN cannot clear pending", List.of()));
                assertThrows(IllegalArgumentException.class, () -> PrisonerLedgerReducer12004.resolve(PrisonerPlanningPorts.Family.RELEASE, retainedPending, unknown, material));
                for (String field : List.of("prisoner_character_id", "release_query_sequence")) {
                    ObjectNode wrongBody = (ObjectNode) StrictJson.parse(retainedPending.bytes(), 1_048_576);
                    ((ObjectNode) wrongBody.get("pending")).put(field, field.equals("prisoner_character_id") ? 89 : 10);
                    RawJson changedPending = new RawJson(StrictJson.canonical(wrongBody));
                    assertThrows(IllegalArgumentException.class, () -> PrisonerLedgerReducer12004.resolve(PrisonerPlanningPorts.Family.RELEASE, changedPending, restored, material));
                }
                assertArrayEquals(ledger, fixture.ledgerBytes());
                ExactRef wrongSubmission = fixture.archive.preserve(new NativeActionPort.Unknown("different-mutation", "other retained original", new byte[0], Optional.empty()));
                var changed = new ActionTerminalObservation(observation.commandBodySha256(), observation.attemptRequestId(), observation.disposition(), observation.before(), observation.after(),
                        observation.source(), observation.sessionId(), observation.provenance(), observation.observedAt(), observation.originalEvidence(), wrongSubmission,
                        observation.selectedCollection(), observation.afterCollection(), observation.supportingEvidence());
                var wrong = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, dispatch, new ActionState.NonAppliedTerminal(changed)));
                assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveReceipt(wrong));
                }
            }
        }
    }
    private static LifecycleIdentity lifecycle(Context c, int revision, String currentField) throws Exception {
        String state = "{\"paused\":true,\"map_ready\":false,\"speed\":3,\"date_raw\":" + c.base().before().frame().identity().dateRaw() + "," + currentField
                + "\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":42,\"connection_generation\":5}}";
        byte[] packet = NativeWire.packet(bytes("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"lifecycle-" + revision + "\",\"revision\":" + revision + ",\"state\":" + state + "}"));
        var received = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(c.base().before().machineId(), c.base().before().game(), BigInteger.valueOf(5), c.base().sessionId()),
                "lifecycle-" + revision, BigInteger.valueOf(revision), raw(state), packet, c.now().plusMillis(revision));
        ExactRef original = c.fixture().archive.preserveNativeFrame(received);
        var facts = NativeArchiveSupportingMaterialsTest.actualFacts(received, c.source(), c.fullRef(), c.fullDriver(), c.fixture().archive);
        var assembler = new DriverObservationAssembler();
        if (!currentField.contains("character_id")) assertInstanceOf(DriverObservationAssembler.Incomplete.class, assembler.assemble(received, facts, original));
        var projected = assertInstanceOf(LifecycleOriginFactory.Projected.class,
                LifecycleOriginFactory.project(assembler.projectFull(received, facts, original), c.hello(), c.fullRef(), c.sourceProof()));
        return projected.identity();
    }
    private static ActionReceipt lifecyclePending(Context c, LifecycleIdentity identity, String id) {
        var values = List.<ProposalLifecycle.ExpectedValue>of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), false),
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.advance_verified"), false),
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.checkpoint_eligible"), false));
        var expected = new LifecycleExpectedPostcondition(identity, c.source(), "controlled-lifecycle-data/v1", LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL, values);
        var command = new ActionCommand(id, new CommandOrigin.LifecycleTerminal(identity), c.source(), identity.sessionId(), expected.operation().key(), empty(),
                new CommandExpectation.LifecycleTerminal(expected), noClaims(), c.deadline());
        var guard = lifecycleGuard(c, identity, command.operation());
        var attempt = new ActionState.Attempt(id + "-request", identity.observedAt(), guard, new NativeRequest(command.operation().value(), Optional.empty(), raw("{}")));
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Unknown(Optional.of(attempt), Optional.empty(), "data only; no implicit native close or replay", List.of()));
    }
    private static GuardEvidence lifecycleGuard(Context c, LifecycleIdentity identity, OperationKey operation) {
        return new GuardEvidence(new CommandOrigin.LifecycleTerminal(identity), c.source(), identity.sessionId(), identity.connectionGeneration(), operation,
                identity.nativeEvidence(), identity.capabilityEvidence(), "controlled-lifecycle-guard", identity.observedAt(), c.deadline(), List.of(c.sourceProof()));
    }
    @Test void actualFullSnapshotProducerRetainsMissingAndNullCurrentPlayerWithoutInventingGameplayActor() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temp.resolve("lifecycle"), false)) {
            Context c = context(fixture, false); LifecycleIdentity missing = lifecycle(c, 11, ""), nil = lifecycle(c, 12, "\"played_character\":null,");
            assertInstanceOf(LifecycleIdentity.Missing.class, missing.currentPlayer()); assertInstanceOf(LifecycleIdentity.Null.class, nil.currentPlayer());
            assertEquals(BigInteger.valueOf(73), missing.subject().characterId()); assertEquals(BigInteger.valueOf(73), nil.subject().characterId());
            for (var original : List.of(lifecyclePending(c, missing, "missing-player"), lifecyclePending(c, nil, "null-player"))) {
                var restored = fixture.archive.loadReceipt(fixture.archive.preserveReceipt(original)); assertEquals(original, restored);
                assertEquals(ActionReceipt.Outcome.UNRESOLVED, restored.outcome()); assertThrows(IllegalStateException.class, restored.command()::before);
                assertFalse(restored.visibleGameplay()); assertFalse(restored.eligibleAdvance());
            }
            var forged = new LifecycleIdentity(missing.machineId(), missing.game(), missing.sessionId(), missing.connectionGeneration(), missing.subject(), missing.frame(),
                    new LifecycleIdentity.Null(), LifecycleIdentity.TerminalReason.MISSING, missing.evidence(), missing.observedAt());
            assertThrows(UncheckedIOException.class, () -> fixture.archive.preserveReceipt(lifecyclePending(c, forged, "wrong-presence-token")));
        }
    }
    private static PlanningReadReceipt status(Context c, LifecycleIdentity identity, String id, boolean modal) throws IOException {
        OperationKey operation = new OperationKey("private-timeline-clock-main-status-v1");
        var request = new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(identity), c.source(), identity.sessionId(), operation, empty(), c.deadline());
        var guard = new PlanningReadGuard(lifecycleGuard(c, identity, operation), new PlanningReadGuard.LifecycleTerminal(), identity.bindingSha256());
        var prepared = new NativeRequest(operation.value(), Optional.empty(), raw("{}"));
        return new PlanningReadReceipt(request, "controlled-lifecycle-status/v1", id, guard, guard,
                reply(id, bytes("{\"controlled_status\":true,\"death_modal_present\":" + modal + "}"), prepared, identity.frame().nativeRevision(), true));
    }
    @Test void lifecycleModalReceiptAutomaticallyArchivesInitialAndIndependentQueriesWithoutOrdinaryDayCredit() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temp.resolve("modal"), false)) {
            Context c = context(fixture, false); var before = lifecycle(c, 20, "\"played_character\":{\"character_id\":99,\"alive\":true},");
            var after = lifecycle(c, 21, "\"played_character\":{\"character_id\":99,\"alive\":true},");
            var values = List.<ProposalLifecycle.ExpectedValue>of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), false),
                    new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.advance_verified"), false),
                    new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.checkpoint_eligible"), false),
                    new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("lifecycle.death_modal_cleared"), true));
            var expected = new LifecycleExpectedPostcondition(before, c.source(), "xar.java.native-death-modal-close/v1", LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL, values);
            var command = new ActionCommand("modal-close", new CommandOrigin.LifecycleTerminal(before), c.source(), before.sessionId(), expected.operation().key(), empty(), new CommandExpectation.LifecycleTerminal(expected), noClaims(), c.deadline());
            var prepared = new NativeRequest(command.operation().value(), Optional.empty(), raw("{}"));
            var attempt = new ActionState.Attempt("modal-submit", before.observedAt().plusNanos(1), lifecycleGuard(c, before, command.operation()), prepared);
            var first = status(c, before, "initial-modal-status", true); var second = status(c, after, "independent-modal-status", false);
            var observation = new LifecycleControlObservation(after, c.source(), after.sessionId(), expected.observerSchema(), values, first, second, List.of(c.sourceProof()));
            var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt,
                    reply(attempt.requestId(), bytes("{\"status\":\"submitted\"}"), prepared, before.frame().nativeRevision(), true), new ActionState.LifecycleControlApplied(observation)));
            assertThrows(UncheckedIOException.class, () -> fixture.archive.readReferenceOf(second));
            var restored = fixture.archive.loadReceipt(fixture.archive.preserveReceipt(receipt)); assertEquals(receipt, restored);
            assertEquals(first, fixture.archive.loadRead(fixture.archive.readReferenceOf(first))); assertEquals(second, fixture.archive.loadRead(fixture.archive.readReferenceOf(second)));
            assertFalse(restored.visibleGameplay()); assertFalse(restored.eligibleAdvance());
        }
    }
}
