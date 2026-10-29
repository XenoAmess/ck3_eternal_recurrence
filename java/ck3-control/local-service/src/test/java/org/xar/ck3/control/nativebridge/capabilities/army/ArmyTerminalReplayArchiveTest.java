package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Actual primitive/transport/writer/archive consumers with software packet I/O.
 * The controlled refusal is not a CK3 outcome, native legality, or live terminal qualification. */
final class ArmyTerminalReplayArchiveTest {
    @TempDir Path root;
    private static final BigInteger FIRST = BigInteger.valueOf(16_777_239);
    private static final BigInteger NEXT_GENERATION = BigInteger.valueOf(33_554_455);
    private static final RawJson REFUSAL = new RawJson(
            "{\"software_terminal_result\":\"rejected\"}".getBytes(StandardCharsets.UTF_8));

    private static ArmyTypes.Context context(ActionCommand command) {
        return new ArmyTypes.Context(command.before(), command.source(), command.sessionId(), command.deadline());
    }
    private static ArmyCalls.War war(PublicMethod method, BigInteger id, ArmyTypes.Context scope) {
        return new ArmyCalls.War(method, new ArmyCalls.Revision(new ArmyTypes.Present<>(scope.before().frame().revision())), id);
    }
    private static ArmyTypes.Context later(ArmyTypes.Context original, long elapsed) {
        var before = original.before(); var frame = before.frame(); var identity = frame.identity();
        var changed = new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(identity.player(), identity.nativeRevision(), identity.dateRaw().add(BigInteger.valueOf(elapsed))),
                frame.snapshotId(), frame.revision(), frame.episodeRunId());
        return new ArmyTypes.Context(new ProposalLifecycle.ObservationIdentity(before.machineId(), before.game(),
                changed, before.observationVersion()), original.source(), original.sessionId(), original.deadline());
    }
    private static ActionCommand terminalCommand(ActionWriterIntegrationFixture actual, String id) throws Exception {
        var basis = actual.command(id); var scope = context(basis);
        var call = war(PublicMethod.OFFER_WHITE_PEACE, FIRST, scope);
        var arguments = new ArmyOrdinaryActionArguments(ArmyOrdinaryActionPreparation.kind(call), ArmyCallCodec.encode(call), List.of());
        return new ActionCommand(basis.actionId(), basis.origin(), basis.source(), basis.sessionId(), basis.operation(),
                arguments.encode(), basis.expectation(), ArmyOrdinaryActionPreparation.claims(call, scope),
                basis.deadline(), basis.protocolIdentity());
    }
    private static ActionWriterIntegrationFixture.SoftwareActionScenario scenario(
            AtomicReference<ActionWriterIntegrationFixture> owner, boolean confirmedRefusal) {
        ActionPorts.PreparationPort primitive = command -> {
            var arguments = ArmyOrdinaryActionArguments.decode(command.arguments());
            var call = ArmyCallCodec.decode(PublicMethod.OFFER_WHITE_PEACE, arguments.publicArguments());
            return ArmyOrdinaryActionPreparation.primitive(call, context(command), List.of());
        };
        return new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("offer-white-peace-" + FIRST),
                "game.command.offer-white-peace-N", (command, attempt, dispatch) -> {
                    if (!confirmedRefusal) return new ActionPorts.Pending("software postcondition remains unknown", List.of());
                    var ack = assertInstanceOf(NativeActionPort.AckReceived.class, dispatch);
                    assertTrue(ack.nativeOk());
                    var original = ack.originalResultToken().orElseThrow();
                    assertEquals(REFUSAL, original);
                    var evidence = owner.get().archive.preserveMaterial(original);
                    return new ActionPorts.RejectionObserved(new ActionState.Rejected(
                            attempt.requestId(), "software terminal refusal", evidence));
                }, () -> { }, Optional.of(() -> REFUSAL), Optional.empty(), false, Optional.of(primitive));
    }
    private static List<ActionReceipt> archived(ActionWriterIntegrationFixture actual, ActionReceipt retained) throws Exception {
        var reference = actual.archive.receiptReferenceOf(retained);
        assertEquals(retained, actual.archive.loadReceipt(reference));
        byte[] encoded = ActionReceiptCodec.encodeReceipt(retained, actual.archive);
        assertEquals(retained, ActionReceiptCodec.decodeReceipt(encoded, actual.archive));
        assertEquals(retained, actual.reopenAndReturnExisting(retained.command()));
        return actual.writer.locked(same -> {
            var rows = ContinuityActionJournal.receipts(same.head().state(), actual.archive.withSession(same));
            assertEquals(List.of(retained), rows); return rows;
        });
    }
    @Test void settledTerminalKeepsCompleteWarIdentityAfterTheActualArchiveAndWriterReopen() throws Exception {
        var owner = new AtomicReference<ActionWriterIntegrationFixture>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("settled"), false, scenario(owner, true))) {
            owner.set(actual);
            actual.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(
                    new OperationKey("offer-white-peace-" + FIRST), actual.observationSource().sourceRef(),
                    (head, proposed, archive) -> {
                        var settled = assertInstanceOf(ActionState.Settled.class, proposed.state());
                        var ack = assertInstanceOf(NativeActionPort.AckReceived.class, settled.dispatch());
                        var rejected = assertInstanceOf(ActionState.Rejected.class, settled.settlement());
                        assertTrue(ack.nativeOk()); assertEquals(REFUSAL, ack.originalResultToken().orElseThrow());
                        assertEquals(REFUSAL, archive.loadMaterial(rejected.originalEvidence()));
                        assertEquals(archive.materialReferenceOf(ack.originalResultToken().orElseThrow()), rejected.originalEvidence());
                    }));
            var command = terminalCommand(actual, "settled-white-original");
            var retained = actual.coordinator.execute(command);
            assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED, retained.outcome());
            var history = archived(actual, retained); var scope = context(command);
            long sequence = actual.sequence(); byte[] ledger = actual.ledgerBytes();
            assertEquals(1, actual.nativeActionWrites());
            assertTrue(command.claims().overlaps(ArmyOrdinaryActionPreparation.claims(
                    war(PublicMethod.SURRENDER_WAR, NEXT_GENERATION, scope), scope)));
            assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectReplay(history,
                    war(PublicMethod.SURRENDER_WAR, NEXT_GENERATION, scope), scope));
            assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectReplay(history,
                    war(PublicMethod.OFFER_WHITE_PEACE, NEXT_GENERATION, scope), scope));
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(history,
                    war(PublicMethod.SURRENDER_WAR, FIRST, scope), scope));
            assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(history,
                    war(PublicMethod.OFFER_WHITE_PEACE, FIRST, scope), later(scope, 719)));
            assertDoesNotThrow(() -> ArmyOrdinaryActionService.rejectReplay(history,
                    war(PublicMethod.OFFER_WHITE_PEACE, FIRST, scope), later(scope, 720)));
            assertEquals(sequence, actual.sequence()); assertArrayEquals(ledger, actual.ledgerBytes());
            assertEquals(1, actual.nativeActionWrites(), "a released settled-history fence grants no second submission");
        }
    }
    @Test void actualUnknownStaysFencedForAnotherFullWarIdAfterArchiveAndColdSameIdLookup() throws Exception {
        var owner = new AtomicReference<ActionWriterIntegrationFixture>();
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("unknown"), false, scenario(owner, false))) {
            owner.set(actual); var command = terminalCommand(actual, "unknown-white-original");
            var retained = actual.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class, retained.state());
            var history = archived(actual, retained); var scope = context(command);
            long sequence = actual.sequence(); byte[] ledger = actual.ledgerBytes();
            for (PublicMethod method : List.of(PublicMethod.SURRENDER_WAR, PublicMethod.OFFER_WHITE_PEACE))
                assertThrows(IllegalArgumentException.class, () -> ArmyOrdinaryActionService.rejectReplay(history,
                        war(method, NEXT_GENERATION, scope), scope));
            assertEquals(retained, actual.coordinator.execute(command));
            assertEquals(sequence, actual.sequence()); assertArrayEquals(ledger, actual.ledgerBytes());
            assertEquals(1, actual.nativeActionWrites(), "UNKNOWN collection must not repeat the original native request");
        }
    }
}
