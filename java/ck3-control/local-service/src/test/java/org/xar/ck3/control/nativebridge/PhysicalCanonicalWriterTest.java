package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.finance.CanonicalFundingPending;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootGuiPhysicalControlAssertions;
import org.xar.ck3.control.contracts.presentation.*;
import org.xar.ck3.control.continuity.writer.*;

/** Actual canonical INTENT/SUBMITTING -> private permit -> sole transport software memory algorithm -> archive/cold.
 * Process/packet/memory edges are explicitly SOFTWARE fixtures; this does not mint Managed/Game or frontend qualification. */
final class PhysicalCanonicalWriterTest {
    @TempDir Path root;
    private static final OperationKey OP = new OperationKey("software-camera-presentation");
    private static final class ActualProducer implements PhysicalActionRegistry.Producer {
        final ActionWriterIntegrationFixture actual; final NativePresentationMemoryFixture.Scenario memory; final boolean changeFrame;
        ActualProducer(ActionWriterIntegrationFixture actual, NativePresentationMemoryFixture.Scenario memory) { this(actual, memory, false); }
        ActualProducer(ActionWriterIntegrationFixture actual, NativePresentationMemoryFixture.Scenario memory, boolean changeFrame) { this.actual = actual; this.memory = memory; this.changeFrame = changeFrame; }
        @Override public GuardEvidence guard(WriterContracts.Head head, ActionCommand command) throws IOException { return actual.physicalSoftwareGuard(head, command); }
        @Override public PreparedAction prepare(ContinuityStorePort.Session same, ActionCommand command, String id) throws IOException {
            actual.writer.requireSession(same); var source = guard(same.head(), command); var raw = memory.request(id); var before = command.before();
            return new PreparedAction.MmapRequest(new PresentationRequest(id, raw.preparedAt(), raw.owner(),
                    new PresentationRequest.Frame(before.frame().snapshotId(), (changeFrame ? before.frame().revision().add(java.math.BigInteger.ONE) : before.frame().revision()).toString(), before.frame().identity().nativeRevision().toString(),
                            before.frame().identity().player().intValueExact(), before.frame().identity().dateRaw().intValueExact()),
                    raw.mode(), raw.previousRequestSequence(), raw.requestSequence(), raw.baselineResultSequence(), raw.expiresUptimeMs(), raw.hwnd(), raw.paddingFloatBits(), raw.titleKey(), raw.tracking(),
                    List.of(source.nativeEvidence(), source.capabilityEvidence())));
        }
        @Override public PhysicalOutcome post(PhysicalSubmission permit, PreparedAction exact, Instant deadline) {
            assertInstanceOf(PresentationPermit.class, permit); var request = ((PreparedAction.MmapRequest) exact).value();
            var posted = memory.transport().post((PresentationPermit) permit, request, deadline);
            if (posted instanceof OriginalOutcome.Posted) {
                // This is the fixture's explicit native side, after the actual even publication, never an invented Java ACK.
                ByteBuffer result = ByteBuffer.allocate(PresentationRequest.RESULT_BYTES).order(ByteOrder.LITTLE_ENDIAN);
                result.putInt((int) request.requestSequence()).putInt(PresentationObservation.Status.SETTLED.wireCode())
                        .putInt(request.frame().actor()).putInt(request.frame().dateRaw()).putInt(1).putInt(1280).putInt(720).putInt(3);
                for (int offset = 48; offset < 96; offset += 4) result.putFloat(offset, 1.0f);
                memory.publishOriginalResult(result.array(), new byte[PresentationRequest.DIAGNOSTICS_BYTES]);
            }
            return new PhysicalOutcome.MmapOutcome(posted);
        }
        @Override public PhysicalActionRegistry.Observation observe(ContinuityStorePort.Session same, ActionCommand command, PhysicalActionState retained, Instant deadline) throws IOException {
            actual.writer.requireSession(same); var request = ((PreparedAction.MmapRequest) retained.request()).value();
            var observation = memory.transport().observe(request, deadline); var ref = actual.archive.preservePresentationObservation(observation);
            if (observation instanceof PresentationObservation.Acknowledged acknowledged && acknowledged.status() == PresentationObservation.Status.SETTLED) {
                requireObserved(request, acknowledged, actual.archive);
                return new PhysicalActionRegistry.Completed(List.of(ref));
            }
            return new PhysicalActionRegistry.Pending("actual original software result is not independently settled", List.of(ref));
        }
        @Override public void verifyArchived(WriterContracts.Head head, ActionReceipt receipt, ActionPorts.OutcomeArchive archive) throws IOException {
            assertEquals(OP, receipt.command().operation()); assertEquals(actual.observationIdentity(), new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(
                    receipt.command().origin().machineId(), receipt.command().origin().game(), receipt.command().sessionId()));
            if (receipt.state() instanceof ActionState.IntentDurable) return;
            var physical = assertInstanceOf(PhysicalActionState.class, receipt.state()); var request = ((PreparedAction.MmapRequest) physical.request()).value();
            assertEquals(RequestIds.forCommand(receipt.command()), request.requestId()); assertEquals(memory.owner(), request.owner());
            var preparedRef = archive.materialReferenceOf(new RawJson(request.encode())); assertArrayEquals(request.encode(), archive.loadMaterial(preparedRef).bytes());
            var same = actual.journal.borrowedWriterSession();
            for (var ref : PhysicalActionCodec.references(physical, archive)) same.verifyPin(same.capturePin(ref, WriterContracts.MAX_PIN_BYTES));
            if (physical.outcome().isPresent()) {
                var outcome = ((PhysicalOutcome.MmapOutcome) physical.outcome().orElseThrow()).value();
                assertEquals(outcome, archive.loadPresentationOutcome(archive.presentationOutcomeReferenceOf(outcome)));
            }
            if (physical.phase() == PhysicalActionState.Phase.COMPLETED) {
                assertEquals(1, physical.evidence().size()); var observation = archive.loadPresentationObservation(physical.evidence().getFirst());
                var acknowledged = assertInstanceOf(PresentationObservation.Acknowledged.class, observation); assertEquals(PresentationObservation.Status.SETTLED, acknowledged.status());
                requireObserved(request, acknowledged, archive);
            }
        }
    }
    private static void requireObserved(PresentationRequest request, PresentationObservation.Acknowledged actual, ActionPorts.OutcomeArchive archive) {
        assertEquals(request, actual.request()); var capture = actual.capture();
        byte[] result = archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.RESULT, capture.originalResult()).bytes();
        actual.verifyOriginal(archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.HEADER, capture.originalHeader()).bytes(), result,
                archive.loadPresentationArtifact(PresentationOriginals.ArtifactRole.DIAGNOSTICS, capture.originalDiagnostics()).bytes());
        ByteBuffer nativeResult = ByteBuffer.wrap(result).order(ByteOrder.LITTLE_ENDIAN);
        assertEquals(request.frame().actor(), nativeResult.getInt(8)); assertEquals(request.frame().dateRaw(), nativeResult.getInt(12));
    }
    private static ActionWriterIntegrationFixture fixture(Path path) throws IOException {
        return new ActionWriterIntegrationFixture(path, false, new ActionWriterIntegrationFixture.SoftwareActionScenario(OP, "software.camera.presentation",
                (command, attempt, outcome) -> new ActionPorts.Pending("native pipe is not this physical plane", List.of()), () -> { throw new AssertionError("physical request entered Native pipe"); }));
    }
    private static PresentationRequest.Owner owner(ActionWriterIntegrationFixture actual) throws Exception {
        var identity = actual.observationIdentity(); return new PresentationRequest.Owner(identity.machineId(), identity.sessionId(), identity.game().pid(),
                identity.game().creationFiletime().value().toString(), PresentationRequest.EXECUTABLE_SHA256, actual.command("software-owner-data").before().frame().episodeRunId(), actual.physicalInputs().transport().originalHello().connectionGeneration().toString());
    }
    private static void install(ActionWriterIntegrationFixture actual, NativePresentationMemoryFixture.Scenario memory) throws IOException {
        actual.bindPhysicalActions(new PhysicalActionRegistry(List.of(new PhysicalActionRegistry.Binding(OP, TransportKind.PRESENTATION_MMAP,
                List.of(actual.physicalInputs().source().sourceRef()), new ActualProducer(actual, memory)))));
    }
    @Test void actualCanonicalPermitPostsOnceAndTwoIndependentCompletedRequestsDoNotBecomeGameEffects() throws Exception {
        try (var actual = fixture(root.resolve("completed")); var memory = NativePresentationMemoryFixture.create(owner(actual), actual.archive)) {
            install(actual, memory);
            for (String id : List.of("physical-first", "physical-second")) {
                var transport = actual.physicalInputs().transport();
                var heartbeatBefore = transport.diagnostics().latestHeartbeat().orElseThrow();
                var command = actual.command(id,Duration.ofMinutes(2));
                var heartbeatAfter = transport.diagnostics().latestHeartbeat().orElseThrow();
                assertFalse(java.util.Arrays.equals(heartbeatBefore.original().packet().value(), heartbeatAfter.original().packet().value()),
                        "the actual software source must emit a new original heartbeat with its next idle snapshot");
                assertFalse(heartbeatAfter.observedAt().isBefore(heartbeatBefore.observedAt()));
                var receipt = actual.coordinator.execute(command);
                var physical = assertInstanceOf(PhysicalActionState.class, receipt.state()); assertEquals(PhysicalActionState.Phase.COMPLETED, physical.phase(), receipt::toString);
                RootGuiPhysicalControlAssertions.requireZeroBusiness(receipt);
                assertEquals(CanonicalFundingPending.Phase.PHYSICAL_COMPLETED,CanonicalFundingPending.phase(receipt.state()));
                assertTrue(CanonicalFundingPending.phase(receipt.state()).settled());
                assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT, receipt.outcome()); assertTrue(receipt.settled());
                assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance()); assertTrue(receipt.ack().isEmpty());
                assertEquals(receipt, actual.archive.loadReceipt(actual.archive.receiptReferenceOf(receipt)));
                var parsed=ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,actual.archive),actual.archive);
                assertEquals(CanonicalFundingPending.Phase.PHYSICAL_COMPLETED,CanonicalFundingPending.phase(parsed.state()));
                assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,parsed.outcome());assertFalse(parsed.visibleGameplay());assertFalse(parsed.eligibleAdvance());
                int writes = memory.actualWriteAttempts(); assertEquals(receipt, actual.reopenAndReturnExisting(command)); assertEquals(writes, memory.actualWriteAttempts());
            }
            assertEquals(2, memory.actualSuccessfulOddClaims()); assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void changedPreparedFrameIsRejectedBeforeCanonicalIntentOrAnyPhysicalWrite() throws Exception {
        try (var actual = fixture(root.resolve("wrong-frame")); var memory = NativePresentationMemoryFixture.create(owner(actual), actual.archive)) {
            actual.bindPhysicalActions(new PhysicalActionRegistry(List.of(new PhysicalActionRegistry.Binding(OP, TransportKind.PRESENTATION_MMAP,
                    List.of(actual.physicalInputs().source().sourceRef()), new ActualProducer(actual, memory, true)))));
            long before = actual.writer.locked(same -> same.head().state().sequence());
            assertThrows(IllegalArgumentException.class, () -> actual.coordinator.execute(actual.command("physical-wrong-frame",Duration.ofMinutes(2))));
            long after = actual.writer.locked(same -> same.head().state().sequence()); assertEquals(before, after);
            assertEquals(0, memory.actualSuccessfulOddClaims()); assertEquals(0, actual.nativeActionWrites());
        }
    }
    @Test void actualOddWriteFailureRemainsUnknownAndBlocksAnotherIdWithoutRepost() throws Exception {
        try (var actual = fixture(root.resolve("unknown")); var memory = NativePresentationMemoryFixture.create(owner(actual), actual.archive)) {
            install(actual, memory); memory.failAfterPhysicalOdd(); var command = actual.command("physical-unknown",Duration.ofMinutes(2));
            var receipt = actual.coordinator.execute(command); assertFalse(receipt.settled(), receipt::toString);
            assertEquals(PhysicalActionState.Phase.UNKNOWN, ((PhysicalActionState) receipt.state()).phase());
            RootGuiPhysicalControlAssertions.requireUnresolvedBlocked(receipt);
            assertEquals(CanonicalFundingPending.Phase.PHYSICAL_UNKNOWN,CanonicalFundingPending.phase(receipt.state()));
            assertFalse(CanonicalFundingPending.phase(receipt.state()).settled());
            var parsed=ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,actual.archive),actual.archive);
            assertEquals(CanonicalFundingPending.Phase.PHYSICAL_UNKNOWN,CanonicalFundingPending.phase(parsed.state()));assertFalse(parsed.settled());
            assertEquals(1, memory.actualSuccessfulOddClaims()); int writes = memory.actualWriteAttempts();
            assertEquals(receipt, actual.reopenAndReturnExisting(command));
            var another = actual.command("physical-different",Duration.ofMinutes(2)); assertThrows(IllegalArgumentException.class, () -> actual.coordinator.execute(another));
            assertEquals(writes, memory.actualWriteAttempts()); assertEquals(0, actual.nativeActionWrites());
        }
    }
}
