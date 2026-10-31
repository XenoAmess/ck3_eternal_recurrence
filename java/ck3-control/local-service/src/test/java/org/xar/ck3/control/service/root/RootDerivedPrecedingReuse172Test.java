package org.xar.ck3.control.service.root;

import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.application.action.ActionJournal;
import java.io.IOException;
import static org.junit.jupiter.api.Assertions.assertSame;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.driver.DriverActionHistoryPublisher;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.action.NativeActionPort;
import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CompositeExecution;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.ReadPublicationRequiredException;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Real archive reads around one pure private method; no installed derived/Native authority. */
final class RootDerivedPrecedingReuse172Test {
    @TempDir Path temporary;

    @Test void precedingReadsOneValidatedProjectionPerCallAndPreservesOrder() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("preceding"), false)) {
            var publisher = new DriverActionHistoryPublisher(fixture.driverAuthority(), fixture.journal,
                    fixture.archive, actualZeroMaterials(fixture), List.of(fixture.observationSource().sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND, publisher);
            var parent = fixture.command("preceding-parent");
            var firstCommand = fixture.command(ActionIds.child(parent.actionId(), 1, parent.operation()));
            var first = canonicalZero(fixture, firstCommand);
            publishZero(fixture, publisher, first);
            var secondCommand = fixture.command(ActionIds.child(parent.actionId(), 2, parent.operation()));
            var second = canonicalZero(fixture, secondCommand);
            publishZero(fixture, publisher, second);
            var current = fixture.command(ActionIds.child(parent.actionId(), 3, parent.operation()));
            var guard = ((ActionState.RejectedBeforeDispatch) first.state()).attempt().guard();
            var execution = new CompositeExecution("preceding-test-only", Instant.now(), guard,
                    List.of(key(firstCommand), key(secondCommand), key(current)));
            var running = new ActionReceipt(1, second.sequence(), parent, ActionCodec.bodySha256(parent),
                    new ActionState.CompositeRunning(execution));
            var zero = new ActionReceipt(1, second.sequence(), parent, ActionCodec.bodySha256(parent),
                    new ActionState.CompositeRunning(new CompositeExecution("preceding-test-only", Instant.now(),
                            guard, List.of(key(firstCommand)))));
            var snapshotBefore = fixture.ledgerBytes();
            int writesBefore = fixture.nativeActionWrites();
            fixture.writer.locked(same -> {
                var state = same.head().state();
                var actualArchive = fixture.archive.withSession(same);
                var loads = new AtomicInteger();
                var counted = counting(actualArchive, loads);
                var canonical = ContinuityActionJournal.receipts(state, counted);
                int completeTraversal = loads.get();
                assertTrue(completeTraversal > 0, "actual canonical records must have been read");
                assertTrue(canonical.indexOf(second) < canonical.indexOf(first),
                        "canonical latest-first order differs from reserved-child order");
                loads.set(0);
                assertEquals(List.of(first, second), preceding(state, running, current, counted));
                assertEquals(completeTraversal, loads.get(), "one complete original chain traversal");
                loads.set(0);
                assertEquals(List.of(first, second), preceding(state, running, current, counted));
                assertEquals(completeTraversal, loads.get(), "next call verifies its own complete projection");
                loads.set(0);
                assertEquals(List.of(), preceding(state, zero, firstCommand, counted));
                assertEquals(0, loads.get(), "zero prior keys do not read an archive");
                assertArrayEquals(snapshotBefore, fixture.ledgerBytes());
                assertEquals(writesBefore, fixture.nativeActionWrites());
                return null;
            });
            assertArrayEquals(snapshotBefore, fixture.ledgerBytes());
            assertEquals(0, writesBefore);
            assertEquals(writesBefore, fixture.nativeActionWrites());
        }
    }

    private static void publishZero(ActionWriterIntegrationFixture fixture,
            DriverActionHistoryPublisher publisher, ActionReceipt actual) throws IOException {
        fixture.writer.locked(same -> {
            assertInstanceOf(DriverActionHistoryPublisher.Published.class, publisher.completed(same, actual));
            return null;
        });
    }

    private static DriverActionHistoryPublisher.MaterialSource actualZeroMaterials(ActionWriterIntegrationFixture fixture) {
        return new DriverActionHistoryPublisher.MaterialSource() {
            @Override public void requireOwner(DriverStateAssembler authority, ActionJournal journal, ActionPorts.OutcomeArchive archive) {
                assertSame(fixture.driverAuthority(), authority);
                assertSame(fixture.journal, journal);
                assertSame(fixture.archive, archive);
            }

            @Override public List<ExactRef> sources() {
                return List.of(fixture.observationSource().sourceRef());
            }

            @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same, ActionReceipt actual, ActionPorts.OutcomeArchive originals) throws IOException {
                fixture.writer.requireSession(same);
                if (!(actual.state() instanceof ActionState.RejectedBeforeDispatch)) {
                    throw new IllegalArgumentException("actual zero material requires RejectedBeforeDispatch state");
                }
                var rejected = (ActionState.RejectedBeforeDispatch) actual.state();
                var attempt = rejected.attempt();
                var dispatch = rejected.dispatch();
                if (!(dispatch instanceof NativeActionPort.RejectedBeforeDispatch)) {
                    throw new IllegalArgumentException("actual zero material requires RejectedBeforeDispatch dispatch outcome");
                }
                var proof = dispatch.proof();
                if (proof.stage() != NativeActionPort.ZeroDispatchStage.BEFORE_WRITE || proof.requestBytesWritten() != 0) {
                    throw new IllegalArgumentException("actual zero-dispatch proof must be BEFORE_WRITE with zero bytes");
                }
                var guard = attempt.guard();
                var nativeEvidence = guard.nativeEvidence();
                var dispatchRef = originals.referenceOf(dispatch);
                var receiptRef = originals.receiptReferenceOf(actual);
                var recordRef = ContinuityActionJournal.requireHistoricalReceipt(same.head().state(), actual, originals);

                var evidence = List.of(
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME, nativeEvidence),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL, dispatchRef),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.ACTION_RECEIPT, receiptRef),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.ACTION_RECORD, recordRef)
                );
                var producers = List.of(fixture.observationSource().sourceRef());

                var material = new DriverActionHistoryCodec.CanonicalOnly(
                    DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,
                    evidence,
                    producers
                );

                requireOriginal(same, actual, material, originals);
                return material;
            }

            @Override public void requireOriginal(Session same, ActionReceipt actual, DriverActionHistoryCodec.OriginalMaterial captured, ActionPorts.OutcomeArchive originals) throws IOException {
                fixture.writer.requireSession(same);
                if (!(actual.state() instanceof ActionState.RejectedBeforeDispatch)) {
                    throw new IllegalArgumentException("requireOriginal: actual state must be RejectedBeforeDispatch");
                }
                var rejected = (ActionState.RejectedBeforeDispatch) actual.state();
                var attempt = rejected.attempt();
                var dispatch = rejected.dispatch();
                if (!(dispatch instanceof NativeActionPort.RejectedBeforeDispatch)) {
                    throw new IllegalArgumentException("requireOriginal: dispatch must be RejectedBeforeDispatch");
                }
                var proof = dispatch.proof();
                if (proof.stage() != NativeActionPort.ZeroDispatchStage.BEFORE_WRITE || proof.requestBytesWritten() != 0) {
                    throw new IllegalArgumentException("requireOriginal: zero-dispatch proof must be BEFORE_WRITE with zero bytes");
                }
                if (!(captured instanceof DriverActionHistoryCodec.CanonicalOnly)) {
                    throw new IllegalArgumentException("requireOriginal: captured material must be CanonicalOnly");
                }
                var canonical = (DriverActionHistoryCodec.CanonicalOnly) captured;
                if (canonical.reason() != DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER) {
                    throw new IllegalArgumentException("requireOriginal: canonical reason must be DIRECT_API_WITHOUT_LEGACY_RECORDER");
                }

                var guard = attempt.guard();
                var nativeEvidence = guard.nativeEvidence();
                var dispatchRef = originals.referenceOf(dispatch);
                var receiptRef = originals.receiptReferenceOf(actual);
                var recordRef = ContinuityActionJournal.requireHistoricalReceipt(same.head().state(), actual, originals);

                var expectedEvidence = List.of(
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME, nativeEvidence),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL, dispatchRef),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.ACTION_RECEIPT, receiptRef),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.ACTION_RECORD, recordRef)
                );

                if (!canonical.evidence().equals(expectedEvidence)) {
                    throw new IllegalArgumentException("requireOriginal: evidence must exactly match actual native frame, receipt and record references");
                }
                if (!canonical.producers().equals(List.of(fixture.observationSource().sourceRef()))) {
                    throw new IllegalArgumentException("requireOriginal: producers must match actual observation source");
                }

                // Verify actual archive data integrity without writing new blobs
                var loadedDispatch = originals.load(dispatchRef);
                if (!loadedDispatch.equals(dispatch)) {
                    throw new IllegalArgumentException("requireOriginal: archived dispatch differs from actual");
                }
                var loadedReceipt = originals.loadReceipt(receiptRef);
                if (!loadedReceipt.equals(actual)) {
                    throw new IllegalArgumentException("requireOriginal: archived receipt differs from actual");
                }
                var loadedRecord = originals.loadRecord(recordRef);
                if (!loadedRecord.receipt().equals(actual)) {
                    throw new IllegalArgumentException("requireOriginal: archived record receipt differs from actual");
                }

                // Validate command body and canonical membership
                StrictJson.require(actual.bodySha256().equals(ActionCodec.bodySha256(actual.command())), "canonical action body mismatch");
                StrictJson.require(ContinuityActionJournal.requireHistoricalReceipt(same.head().state(), actual, originals).equals(recordRef), "actual action record membership mismatch");
                DriverActionHistoryCodec.requireSource(actual, DriverActionHistoryCodec.source(actual, recordRef, receiptRef, canonical), originals);
            }
        };
    }

    private static ActionReceipt canonicalZero(ActionWriterIntegrationFixture fixture, ActionCommand command) {
        int writesBefore = fixture.nativeActionWrites();
        // Existing coordinator/fixture has four real checks before the native write.
        fixture.stopAtIntentBarrier.set(fixture.intentBarrierChecks.get() + 4);
        try {
            ActionReceipt receipt;
            try { receipt = fixture.coordinator.execute(command); }
            catch (ReadPublicationRequiredException publication) {
                receipt = publication.zeroDispatchReceipt().orElseThrow(
                        () -> new AssertionError("real barrier must retain the canonical zero-dispatch receipt"));
            }
            assertInstanceOf(ActionState.RejectedBeforeDispatch.class, receipt.state());
            assertEquals(ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH, receipt.outcome());
            assertTrue(receipt.settled());
            assertEquals(writesBefore, fixture.nativeActionWrites());
            return receipt;
        } finally {
            fixture.stopAtIntentBarrier.set(0);
        }
    }

    private static CompositeExecution.Child key(ActionCommand command) {
        return new CompositeExecution.Child(command.actionId(), ActionCodec.bodySha256(command));
    }

    private static ActionPorts.OutcomeArchive counting(ActionPorts.OutcomeArchive original, AtomicInteger count) {
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, arguments) -> {
                    if (method.getName().equals("loadRecord")) count.incrementAndGet();
                    try { return method.invoke(original, arguments); }
                    catch (InvocationTargetException failure) { throw failure.getCause(); }
                });
    }

    private static List<ActionReceipt> preceding(ContinuityState state, ActionReceipt parent,
            ActionCommand child, ActionPorts.OutcomeArchive archive) {
        try {
            Method method = RootDerivedChildAuthority.class.getDeclaredMethod("preceding", ContinuityState.class,
                    ActionReceipt.class, ActionCommand.class, ActionPorts.OutcomeArchive.class);
            method.setAccessible(true);
            Object actual = method.invoke(null, state, parent, child, archive);
            if (!(actual instanceof List<?> values)) throw new AssertionError("preceding returned a non-list");
            return values.stream().map(ActionReceipt.class::cast).toList();
        } catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof RuntimeException runtime) throw runtime;
            if (failure.getCause() instanceof Error error) throw error;
            throw new AssertionError("unexpected checked preceding failure", failure.getCause());
        } catch (ReflectiveOperationException failure) {
            throw new AssertionError("actual preceding method unavailable", failure);
        }
    }
}
