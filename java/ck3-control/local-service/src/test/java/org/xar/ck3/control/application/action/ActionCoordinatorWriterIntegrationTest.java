package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual software producer graph. Game/source/process edges are controlled test inputs, never live qualification. */
final class ActionCoordinatorWriterIntegrationTest {
    @TempDir Path temporary;
    @Test void actualCollectorNestedReadsRootGuardsAndWriterPreserveUnknownWithoutReplay() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("unknown"), true)) {
            var command = fixture.command("action-unknown"); assertTrue(fixture.nestedPlanningReads.get() > 0); assertTrue(fixture.sourceChecks.get() > 0);
            AtomicReference<ContinuityStorePort.Session> original = new AtomicReference<>();
            ActionReceipt unresolved = fixture.writer.locked(session -> { original.set(session); return fixture.coordinator.execute(session, command); });
            assertInstanceOf(ActionState.Unknown.class, unresolved.state()); assertEquals(1, fixture.nativeActionWrites());
            assertEquals(2, fixture.getGuardObservations(command.actionId()).size(), "only coordinator preparation and submission sample live readiness");
            assertSame(original.get(), fixture.originalHookSession.get()); assertEquals(1, fixture.pendingPreparations.get());
            assertEquals(ActionTransitions.attempt(unresolved.state()).orElseThrow().preparedRequest(), fixture.originalPreparedAtHook.get());
            assertEquals(unresolved, fixture.completedAttempt.get()); assertEquals(1, fixture.attemptCompletions.get());
            assertEquals(unresolved, fixture.coordinator.execute(command)); assertEquals(1, fixture.nativeActionWrites()); assertEquals(1, fixture.pendingPreparations.get());
            assertEquals(1, fixture.attemptCompletions.get(), "returning retained UNKNOWN is not a new attempt");
            assertEquals(2, fixture.getGuardObservations(command.actionId()).size(), "retained UNKNOWN performs no live guard or replay");
            var changed = new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(), command.operation(), command.arguments(), command.expected(), command.claims(), command.deadline().plusSeconds(1));
            assertThrows(IllegalArgumentException.class, () -> fixture.coordinator.execute(changed)); assertEquals(1, fixture.nativeActionWrites());
            long beforeReconcile = fixture.sequence(); ActionReceipt reconciled = fixture.coordinator.reconcile(command.actionId());
            assertInstanceOf(ActionState.Unknown.class, reconciled.state()); assertTrue(fixture.sequence() >= beforeReconcile); assertEquals(1, fixture.nativeActionWrites());
            var snapshot = fixture.snapshot(); assertEquals(1, snapshot.actions().size()); assertEquals(reconciled, snapshot.actions().getFirst());
            assertTrue(snapshot.originalHistory() instanceof ActionJournal.BoundHistoryBasis); assertFalse(reconciled.visibleGameplay()); assertFalse(reconciled.eligibleAdvance());
            assertTrue(fixture.nativeReadWrites() > 0);
            byte[] persisted = fixture.ledgerBytes(); assertEquals(reconciled, fixture.reopenAndReturnExisting(command));
            assertArrayEquals(persisted, fixture.ledgerBytes()); assertEquals(1, fixture.nativeActionWrites());
        }
    }
    @Test void intentRetainsHistoricalSourceMetadataWithoutPinningRebuiltBusinessBytes() throws Exception {
        try (var fixture=new ActionWriterIntegrationFixture(temporary.resolve("source-metadata"),false)) {
            var original=fixture.command("metadata-intent");
            Path implementation=temporary.resolve("historical-business.class");
            java.nio.file.Files.writeString(implementation,"original implementation");
            byte[] bytes=java.nio.file.Files.readAllBytes(implementation);
            var ref=new org.xar.ck3.control.contracts.ExactRef(implementation.toString(),bytes.length,ActionCodec.sha256(bytes));
            var source=new org.xar.ck3.control.g2.common.G2Source(original.source().machineId(),
                    Instant.now().toString(),original.source().exactBuild(),ref);
            var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(
                    1,original.before(),source,"paused/v1",original.expected().values());
            var command=new ActionCommand(original.actionId(),original.before(),source,original.sessionId(),
                    original.operation(),original.arguments(),expected,original.claims(),original.deadline());
            java.nio.file.Files.writeString(implementation,"rebuilt implementation has different bytes");
            var receipt=fixture.journal.locked(locked->locked.append(command,ActionCodec.bodySha256(command),new ActionState.IntentDurable()));
            assertInstanceOf(ActionState.IntentDurable.class,receipt.state());
            assertEquals(source,receipt.command().source());assertEquals(0,fixture.nativeActionWrites());
            assertEquals(receipt,fixture.snapshot().actions().getFirst());
            assertEquals(receipt,fixture.archive.loadReceipt(fixture.archive.receiptReferenceOf(receipt)));
            var record=fixture.journal.locked(locked->ContinuityActionJournal.recordHead(locked.head().state()).orElseThrow());
            java.nio.file.Files.writeString(Path.of(record.path()),"changed actual action record");
            assertThrows(RuntimeException.class,fixture::snapshot,"actual canonical record DATA still has to match");
            assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void installedReadIdentityAndPhysicalReceiptSurviveTheActualNestedCollector() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("reads"), false)) {
            var command = fixture.command("query-basis"); var read = fixture.lastNestedRead.get();
            assertEquals(read, fixture.archive.loadRead(fixture.archive.readReferenceOf(read)));
            long sequence = fixture.sequence(); int writes = fixture.nativeReadWrites();
            var forged = ActionWriterIntegrationFixture.contract(fixture.readContract.sourceRef());
            var request = new PlanningReadRequest(command.before(), command.source(), command.sessionId(), fixture.readContract.operation(), command.arguments(), command.deadline());
            assertThrows(IllegalArgumentException.class, () -> fixture.reads.read(forged, request));
            assertEquals(writes, fixture.nativeReadWrites()); assertEquals(sequence, fixture.sequence());
        }
    }
    @Test void acknowledgedPrimitiveWithCompositePoststateBecomesDurableUnknown() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("bad-poststate"), false)) {
            var command = fixture.command("bad-composite"); fixture.requestMalformedPrimitiveCompositeResult(command);
            ActionReceipt result = assertDoesNotThrow(() -> fixture.coordinator.execute(command));
            var unknown = assertInstanceOf(ActionState.Unknown.class, result.state());
            assertTrue(unknown.reason().contains("composite control cannot settle a primitive")); assertTrue(result.ack().isPresent());
            assertEquals(1, fixture.nativeActionWrites()); assertEquals(result, fixture.coordinator.execute(command));
            assertEquals(result, fixture.archive.loadReceipt(fixture.archive.receiptReferenceOf(result)));
        }
    }
    @Test void pendingImportFailureOccursBeforeDurableIntentOrNativeAction() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("pending-failure"), false)) {
            var command = fixture.command("pending-failure"); byte[] before = fixture.ledgerBytes(); fixture.failPendingPreparation();
            assertThrows(IllegalStateException.class, () -> fixture.coordinator.execute(command));
            assertArrayEquals(before, fixture.ledgerBytes()); assertEquals(0, fixture.sequence()); assertEquals(0, fixture.nativeActionWrites()); assertTrue(fixture.snapshot().actions().isEmpty());
            assertEquals(0, fixture.attemptCompletions.get(), "pre-intent failures have no durable attempt to complete");
        }
    }
    @Test void failedReadOnlyPrimitivePreparationDoesNotCreatePendingOrIntentOrCompleteAnAttempt() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("prepare-failure"), false)) {
            var command = fixture.command("prepare-failure"); byte[] before = fixture.ledgerBytes(); fixture.failPrimitivePreparation.set(true);
            assertThrows(IllegalStateException.class, () -> fixture.coordinator.execute(command));
            assertArrayEquals(before, fixture.ledgerBytes()); assertEquals(0, fixture.pendingPreparations.get()); assertEquals(0, fixture.attemptCompletions.get());
            assertEquals(0, fixture.nativeActionWrites()); assertTrue(fixture.snapshot().actions().isEmpty());
        }
    }
    @Test void actualCompositeRegistersTheExactChildBeforeItsFirstGuardAndKeepsAckObservationInTheSameScope() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("parent-child"), false, false, true)) {
            var command = fixture.command("parent-child"); var result = fixture.coordinator.execute(command);
            var parent = assertInstanceOf(ActionState.CompositeUnknown.class, result.state()); assertEquals(1, parent.execution().children().size());
            assertTrue(fixture.childInitialGuardChecks.get() > 0); assertTrue(fixture.childAckObservationChecks.get() > 0);
            var child = fixture.snapshot().actions().stream().filter(value -> value.command().actionId().equals(fixture.childActionId.get())).findFirst().orElseThrow();
            assertInstanceOf(ActionState.Unknown.class, child.state()); assertTrue(child.ack().isPresent()); assertEquals(1, fixture.nativeActionWrites());
            assertEquals(result, fixture.coordinator.execute(command)); assertEquals(1, fixture.nativeActionWrites());
            assertTrue(ActionCommandScope.current().isEmpty());
            fixture.writer.locked(same -> { assertTrue(assertDoesNotThrow(() -> ActionChildPlanningScope.current(same, same.head())).isEmpty()); return null; });
        }
    }
    @Test void anotherRealWriterSessionIsRejectedBeforeHookOrDispatch() throws Exception {
        try (var first = new ActionWriterIntegrationFixture(temporary.resolve("first"), false);
                var second = new ActionWriterIntegrationFixture(temporary.resolve("second"), false)) {
            var command = first.command("crossed");
            second.writer.locked(other -> { assertThrows(RuntimeException.class, () -> first.coordinator.execute(other, command)); return null; });
            assertEquals(0, first.pendingPreparations.get()); assertEquals(0, first.nativeActionWrites()); assertEquals(0, first.sequence());
        }
    }
    @Test void expiredCallerReadinessDeadlineConsumesNoNativePacketOrWriterEvent() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("expired-readiness"), false)) {
            var command = fixture.command("expired"); int packetReads = fixture.nativePacketReads(); int readWrites = fixture.nativeReadWrites();
            byte[] persisted = fixture.ledgerBytes();
            fixture.writer.locked(session -> {
                org.xar.ck3.control.application.readiness.ReadinessAuthority authority = fixture.collector;
                assertThrows(IllegalArgumentException.class, () -> authority.current(session, command.before(), Instant.now().minusNanos(1), lease -> { throw new AssertionError("expired caller must not receive a lease"); }));
                return null;
            });
            var expired = new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(), command.operation(),
                    command.arguments(), command.expected(), command.claims(), Instant.now().minusNanos(1));
            assertThrows(IllegalArgumentException.class, () -> fixture.coordinator.execute(expired));
            assertEquals(packetReads, fixture.nativePacketReads()); assertEquals(readWrites, fixture.nativeReadWrites());
            assertEquals(0, fixture.nativeActionWrites()); assertArrayEquals(persisted, fixture.ledgerBytes());
        }
    }
    @Test void borrowedObservationUsesTheActualHeldWriterWithoutOpeningAnotherStoreLock() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("borrow-observation"), false)) {
            fixture.ready(); int locks = fixture.collectorLocks.get(), reads = fixture.nestedPlanningReads.get(); byte[] before = fixture.ledgerBytes();
            fixture.writer.locked(same -> {
                var originalHead = same.head();
                var ready = assertInstanceOf(org.xar.ck3.control.application.session.SessionPorts.Ready.class,
                        assertDoesNotThrow(() -> fixture.collector.observe(same, fixture.observationIdentity(), Instant.now().plusSeconds(10))));
                assertEquals(ready.request(), fixture.lastPublishedReady.get()); assertEquals(originalHead.digest(), same.head().digest());
                return null;
            });
            assertEquals(locks, fixture.collectorLocks.get(), "borrowed observation must never reacquire store.locked");
            assertEquals(reads + 1, fixture.nestedPlanningReads.get(), "one actual nested query uses the same frozen producer");
            assertArrayEquals(before, fixture.ledgerBytes()); assertEquals(0, fixture.nativeActionWrites());
        }
    }
    @Test void escapedAndForeignObservationSessionsAreRejectedBeforeAnyNativeIo() throws Exception {
        try (var first = new ActionWriterIntegrationFixture(temporary.resolve("observe-own"), false);
                var second = new ActionWriterIntegrationFixture(temporary.resolve("observe-foreign"), false)) {
            var escaped = new AtomicReference<ContinuityStorePort.Session>(); first.writer.locked(same -> { escaped.set(same); return null; });
            int packets = first.nativePacketReads(), writes = first.nativeReadWrites(), locks = first.collectorLocks.get();
            assertThrows(Exception.class, () -> first.collector.observe(escaped.get(), first.observationIdentity(), Instant.now().plusSeconds(10)));
            second.writer.locked(other -> {
                assertThrows(Exception.class, () -> first.collector.observe(other, first.observationIdentity(), Instant.now().plusSeconds(10))); return null;
            });
            assertEquals(packets, first.nativePacketReads()); assertEquals(writes, first.nativeReadWrites()); assertEquals(locks, first.collectorLocks.get());
            assertEquals(0, first.sequence()); assertEquals(0, first.nativeActionWrites());
        }
    }
    @Test void publicationBarrierBeforeIntentPreservesNoAttemptAndDoesNotInvokePendingProducer() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("read-before-intent"), false)) {
            var command = fixture.command("read-before-intent"); byte[] before = fixture.ledgerBytes(); fixture.stopAtIntentBarrier.set(2);
            var stopped = assertThrows(ReadPublicationRequiredException.class, () -> fixture.coordinator.execute(command));
            assertEquals(command, stopped.command()); assertTrue(stopped.zeroDispatchReceipt().isEmpty());
            assertArrayEquals(before, fixture.ledgerBytes()); assertEquals(0, fixture.pendingPreparations.get()); assertEquals(0, fixture.attemptCompletions.get());
            assertEquals(0, fixture.nativeActionWrites()); assertTrue(fixture.snapshot().actions().isEmpty());
            fixture.writer.locked(same -> { assertThrows(IllegalArgumentException.class, () -> ActionReadPublicationScope.requireClearBeforeIntent(same, command)); return null; });
        }
    }
    @Test void publicationBarrierAfterIntentRecordsOnlyTheOriginalNeverWrittenRequest() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("read-after-intent"), false)) {
            var command = fixture.command("read-after-intent"); fixture.stopAtIntentBarrier.set(4);
            var stopped = assertThrows(ReadPublicationRequiredException.class, () -> fixture.coordinator.execute(command));
            var receipt = stopped.zeroDispatchReceipt().orElseThrow(); var rejected = assertInstanceOf(ActionState.RejectedBeforeDispatch.class, receipt.state());
            assertEquals(RequestIds.forActionBody(receipt.bodySha256()), rejected.attempt().requestId()); assertEquals(0, rejected.dispatch().proof().requestBytesWritten());
            assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, rejected.dispatch().proof().stage());
            assertEquals(receipt, fixture.archive.loadReceipt(fixture.archive.receiptReferenceOf(receipt))); assertEquals(receipt, fixture.snapshot().actions().getFirst());
            assertEquals(2, fixture.sequence()); assertEquals(1, fixture.pendingPreparations.get()); assertEquals(1, fixture.attemptCompletions.get());
            assertEquals(0, fixture.nativeActionWrites()); assertEquals(receipt, fixture.coordinator.execute(command)); assertEquals(0, fixture.nativeActionWrites());
        }
    }
    @Test void preparationChecksTheActualBarrierBeforeConsumingAnIrreversibleClaim() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("read-before-claim"), false)) {
            var command = fixture.command("read-before-claim"); fixture.checkBarrierInsidePreparation.set(true); fixture.stopAtIntentBarrier.set(2);
            var stopped = assertThrows(ReadPublicationRequiredException.class, () -> fixture.coordinator.execute(command));
            assertTrue(stopped.zeroDispatchReceipt().isEmpty()); assertEquals(0, fixture.preparationClaimConsumptions.get());
            assertEquals(0, fixture.pendingPreparations.get()); assertEquals(0, fixture.nativeActionWrites()); assertEquals(0, fixture.sequence());
        }
    }
    @Test void compositeDoesNotSwallowAChildPublicationBarrierOrReplayItsUnresolvedParent() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("read-composite"), false, false, true)) {
            var command = fixture.command("read-composite"); fixture.stopAtIntentBarrier.set(4);
            var stopped = assertThrows(ReadPublicationRequiredException.class, () -> fixture.coordinator.execute(command));
            assertEquals(fixture.childActionId.get(), stopped.command().actionId()); assertTrue(stopped.zeroDispatchReceipt().isEmpty());
            var parentReceipt = fixture.snapshot().actions().getFirst(); var parent = assertInstanceOf(ActionState.CompositeUnknown.class, parentReceipt.state());
            assertEquals(1, parent.execution().children().size()); assertEquals(stopped.command().actionId(), parent.execution().children().getFirst().actionId());
            assertEquals(1, fixture.snapshot().actions().size(), "an unsent child without completed preparation must not gain a fabricated attempt");
            assertEquals(0, fixture.nativeActionWrites()); assertEquals(0, fixture.attemptCompletions.get());
            assertEquals(parentReceipt, fixture.coordinator.execute(command)); assertEquals(0, fixture.nativeActionWrites());
            long retainedSequence = fixture.sequence(); assertEquals(parentReceipt, fixture.coordinator.reconcile(command.actionId()));
            assertEquals(retainedSequence, fixture.sequence()); assertEquals(0, fixture.nativeActionWrites());
        }
    }
}
