package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;

/** Runs the actual write path, then reopens the real temporary ledger after each injected failure. */
class WriterCustodyAndCrashTest {
    @TempDir Path root;
    private static final TransitionAuthority ORDINARY = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState head, Request request) { return ContinuityJson.digest(request.detailsObject()); }
        @Override public ContinuityState reduce(ContinuityState head, Request request) { return OriginalWindowReducer.reduce(head, request); }
    };
    private static List<ExactRef> sources(WriterFixture fixture) throws IOException {
        return List.of(LedgerFiles.read(fixture.source, ContinuityJson.DOCUMENT_MAX_BYTES).pin().reference());
    }
    private static ContinuityWriter faulting(WriterFixture fixture, WriterFaultProbe probe) throws IOException {
        return new ContinuityWriter(fixture.layout, sources(fixture), ORDINARY, Clock.systemUTC(), ContinuityWriter.Extensions.none(), StorageWriteGuardTestSupport.forLayout(fixture.layout), probe);
    }
    @Test void borrowedSessionRejectsOtherWriterCrossThreadAndEscapeAndVerifiesNativePins() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("custody"));
        WriterFixture other = new WriterFixture(root.resolve("other"));
        ContinuityWriter sameLayout = new ContinuityWriter(fixture.layout, sources(fixture), ORDINARY, StorageWriteGuardTestSupport.forLayout(fixture.layout));
        AtomicReference<ContinuityStorePort.Session> escaped = new AtomicReference<>();
        fixture.writer.locked(session -> {
            session.requireWriter(fixture.layout.lock()); escaped.set(session);
            assertEquals(0,session.head().state().sequence());
            fixture.writer.requireSession(session);
            assertThrows(IOException.class, () -> sameLayout.requireSession(session), "same lock path does not grant this writer's authority");
            assertThrows(ContractViolationException.class, () -> session.requireWriter(other.layout.lock()));
            Pin pin = session.capturePin(sources(fixture).getFirst(), ContinuityJson.DOCUMENT_MAX_BYTES);
            session.verifyPin(pin);
            AtomicReference<Throwable> wrongThread = new AtomicReference<>();
            Thread thread = new Thread(() -> { try { session.head(); } catch (Throwable failure) { wrongThread.set(failure); } });
            thread.start();
            try { thread.join(5_000); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
            assertFalse(thread.isAlive()); assertInstanceOf(ContractViolationException.class, wrongThread.get());
            Path replacement = fixture.source.resolveSibling("same-bytes.txt"); Files.write(replacement, Files.readAllBytes(fixture.source));
            Files.move(replacement, fixture.source, StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class, () -> session.verifyPin(pin));
            return null;
        });
        assertThrows(ContractViolationException.class, () -> escaped.get().head());
        assertThrows(ContractViolationException.class, () -> escaped.get().requireWriter(fixture.layout.lock()));
        assertThrows(ContractViolationException.class, () -> fixture.writer.requireSession(escaped.get()));
    }
    @Test void sameCallbackHeadAdvancesAfterCommitAndRejectsOldPrepared() throws Exception {
        WriterFixture fixture=new WriterFixture(root.resolve("same-callback"));
        fixture.writer.locked(session->{
            assertEquals(0,session.head().state().sequence());
            Prepared stale=session.preview(WriterFixture.settled("old-plan",1024,2));
            Receipt committed=session.commit(session.preview(WriterFixture.settled("new-plan",1048,3)));
            assertEquals(Disposition.COMMITTED,committed.disposition());
            assertEquals(1,session.head().state().sequence());
            assertEquals(1048,session.head().state().settledDateRaw());
            assertThrows(ContractViolationException.class,()->session.commit(stale));
            assertEquals(1,session.head().state().sequence());
            assertFalse(Files.exists(fixture.layout.event(2)));
            return null;
        });
    }
    @Test void sameCallbackHeadSeesEventPublishedBeforeCommitFailure() throws Exception {
        WriterFixture fixture=new WriterFixture(root.resolve("failed-head"));
        Request request=WriterFixture.settled("failed-event",1024,2);
        ContinuityWriter failing=faulting(fixture,(boundary,sequence)->{
            if(boundary==WriterFaultProbe.Boundary.EVENT_PUBLISHED)throw new IOException("actual event published");
        });
        AtomicReference<Prepared> original=new AtomicReference<>();
        failing.locked(session->{
            assertEquals(0,session.head().state().sequence());
            original.set(session.preview(request));
            assertThrows(CommitUncertainException.class,()->session.commit(original.get()));
            Head durable=session.head();
            assertEquals(1,durable.state().sequence());
            assertTrue(durable.snapshotNeedsRecovery());
            assertEquals(1,durable.indexRepairs().size());
            return null;
        });
        fixture.storage.reconcileStorageOnly();
        Receipt recovered=fixture.writer.commit(original.get());
        assertEquals(Disposition.ALREADY_COMMITTED,recovered.disposition());
        fixture.writer.locked(session->{
            assertEquals(1,session.head().state().sequence());
            assertFalse(session.head().snapshotNeedsRecovery());
            assertTrue(session.head().indexRepairs().isEmpty());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(2)));
    }
    @Test void sameCallbackHeadFindsExternalEventWithOldSnapshot() throws Exception {
        WriterFixture fixture=new WriterFixture(root.resolve("external-event"));
        fixture.writer.locked(session->{
            Head before=session.head();
            Request request=WriterFixture.settled("external-event",1024,2);
            ObjectNode after=OriginalWindowReducer.reduce(before.state(),request).toJson();
            after.put("sequence",1).put("last_event_identity",request.identity());
            var event=new org.xar.ck3.control.continuity.ContinuityEvent(1,"2026-10-29T00:00:00Z",
                    request.kind(),request.details(),request.identity(),before.digest(),
                    ContinuityState.fromJson(after,WriterFixture.MACHINE));
            StorageWriteGuardTestSupport.atomic(fixture.layout.event(1),ContinuityJson.canonical(event.toJson()),false);
            Head changed=session.head();
            assertEquals(1,changed.state().sequence());
            assertTrue(changed.snapshotNeedsRecovery());
            assertEquals(1,changed.indexRepairs().size());
            return null;
        });
    }
    @Test void sameCallbackHeadReflectsSnapshotReplacementIdentity() throws Exception {
        WriterFixture fixture=new WriterFixture(root.resolve("replaced-snapshot"));
        fixture.writer.locked(session->{
            Head before=session.head();
            Path snapshot=fixture.layout.snapshot();
            StorageWriteGuardTestSupport.atomic(snapshot,Files.readAllBytes(snapshot),true);
            Pin current=session.capturePin(LedgerFiles.read(snapshot,ContinuityJson.LEDGER_MAX_BYTES).pin().reference(),
                    ContinuityJson.LEDGER_MAX_BYTES);
            assertFalse(before.documents().contains(current));
            assertTrue(session.head().documents().contains(current));
            assertEquals(0,session.head().state().sequence());
            return null;
        });
    }
    @Test void originalPacketsLargerThanDomainBodyRemainUnmodifiedAndExactlyPinned() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("packet"));
        Path packet = root.resolve("native-original.bin"); byte[] raw = new byte[ContinuityJson.DOMAIN_MAX_BYTES + 17]; raw[raw.length - 1] = 73;
        Files.write(packet, raw); ExactRef reference = LedgerFiles.read(packet, MAX_PIN_BYTES).pin().reference();
        fixture.writer.locked(session -> {
            assertThrows(IOException.class, () -> session.capturePin(reference, ContinuityJson.DOMAIN_MAX_BYTES));
            Pin pin = session.capturePin(reference, raw.length); session.verifyPin(pin);
            assertEquals(raw.length, pin.reference().bytes()); return null;
        });
        assertArrayEquals(raw, Files.readAllBytes(packet));
    }
    @Test void everyOrdinaryDurableBoundaryRecoversCommittedReceiptWithoutRerunningAuthority() throws Exception {
        assertTrue(Platform.isWindows()); int position = 0;
        for (WriterFaultProbe.Boundary boundary : WriterFaultProbe.Boundary.values()) {
            WriterFixture fixture = new WriterFixture(root.resolve(boundary.name())); Request request = WriterFixture.settled("same-id", 1024, 2);
            Prepared prepared = fixture.writer.preview(request);
            ContinuityWriter failing = faulting(fixture, (actual, sequence) -> { if (actual == boundary) throw new IOException("injected after actual " + boundary); });
            assertThrows(CommitUncertainException.class, () -> failing.commit(prepared));
            fixture.storage.reconcileStorageOnly();
            ContinuityWriter reopened = new ContinuityWriter(fixture.layout, sources(fixture), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState state, Request supplied) { throw new AssertionError("committed action must not run authority again"); }
                @Override public ContinuityState reduce(ContinuityState state, Request supplied) { throw new AssertionError("committed action must not run reducer again"); }
            }, StorageWriteGuardTestSupport.forLayout(fixture.layout));
            Receipt recovered = reopened.commit(prepared); assertEquals(Disposition.ALREADY_COMMITTED, recovered.disposition());
            assertEquals(2 - position++, recovered.writes()); assertEquals(1, recovered.head().sequence());
            assertTrue(ContinuityJson.same(WriterFixture.state().get("pending_cycle"), recovered.head().toJson().get("pending_cycle")));
            assertEquals(11559, recovered.head().toJson().get("NEXT").intValue());
            assertEquals(0, reopened.commit(prepared).writes()); assertFalse(Files.exists(fixture.layout.event(2)));
        }
    }
    @Test void changedEvidenceIdPayloadAfterDurableEventCannotCommitSecondEventBeforeIndexRecovery() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("changed-id"));
        Request original = WriterFixture.settled("one-identity", 1024, 2); Prepared prepared = fixture.writer.preview(original);
        ContinuityWriter failing = faulting(fixture, (boundary, sequence) -> { if (boundary == WriterFaultProbe.Boundary.EVENT_PUBLISHED) throw new IOException("crash before index"); });
        assertThrows(CommitUncertainException.class, () -> failing.commit(prepared));
        assertThrows(ContractViolationException.class, () -> fixture.writer.preview(WriterFixture.settled("one-identity", 1048, 3)));
        assertFalse(Files.exists(fixture.layout.event(2))); assertFalse(Files.exists(fixture.layout.sourceIndex(original.sourceKey())));
        fixture.storage.reconcileStorageOnly();
        assertEquals(Disposition.ALREADY_COMMITTED, fixture.writer.commit(prepared).disposition());
        assertFalse(Files.exists(fixture.layout.event(2)));
    }
    @Test void actualTwoEventTransactionRecoversAfterEveryDurableWriteAndKeepsUnknownFields() throws Exception {
        assertTrue(Platform.isWindows());
        for (int boundary = 1; boundary <= 6; boundary++) {
            var fixture = new CanonicalContinuityTransactionsTest.PairFixture(root.resolve("pair-" + boundary));
            RollbackPair.Plan plan = fixture.writer.previewRollback(fixture.evidence.proof());
            AtomicInteger operations = new AtomicInteger(); int crashAt = boundary;
            var extensions = new ContinuityWriter.Extensions(List.of(), Optional.empty(), Optional.of((head, proof) -> fixture.evidence));
            ContinuityWriter failing = new ContinuityWriter(fixture.layout, sources(fixture.initial), ORDINARY, Clock.systemUTC(), extensions, StorageWriteGuardTestSupport.forLayout(fixture.layout), (kind, sequence) -> { if (operations.incrementAndGet() == crashAt) throw new IOException("actual pair crash " + crashAt); });
            assertThrows(CommitUncertainException.class, () -> failing.commitRollback(plan));
            fixture.initial.storage.reconcileStorageOnly();
            RollbackPair.Commit recovered = fixture.writer.commitRollback(plan); assertEquals(6 - boundary, recovered.writes());
            assertEquals(3, recovered.committedSequence()); assertEquals(0, fixture.writer.commitRollback(plan).writes());
            ContinuityState actual = fixture.writer.locked(session -> session.head().state());
            assertEquals(1, actual.settledCycles()); assertEquals(1000, actual.settledDateRaw());
            for (String field : PRESERVED_RUNTIME_FIELDS) {
                assertEquals(plan.originalHead().state().toJson().get(field), actual.toJson().get(field));
            }
        }
    }
    @Test void immutableDomainImportCrashRepairsSnapshotAndSourceIndexBeforeReturningKnownReceipt() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("domain-crash"));
        Path archiveRoot = fixture.layout.snapshot().getParent().resolve("archive"); Files.createDirectory(archiveRoot);
        var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archiveRoot, fixture.layout.lock(), 4_194_304), StorageWriteGuardTestSupport.forOriginalLock(fixture.layout.lock()));
        DomainBodies.Registration registration = new DomainBodies.Registration(DomainBodies.Slot.COUNCIL, "fixture.domain/v1", 65_536, sources(fixture),
                (head, previous, request, original) -> LedgerFiles.sha(original));
        var extensions = new ContinuityWriter.Extensions(List.of(registration), Optional.of(artifacts), Optional.empty());
        ContinuityWriter failing = new ContinuityWriter(fixture.layout, sources(fixture), ORDINARY, Clock.systemUTC(), extensions, StorageWriteGuardTestSupport.forLayout(fixture.layout), (boundary, sequence) -> { if (boundary == WriterFaultProbe.Boundary.EVENT_PUBLISHED) throw new IOException("actual domain commit crash"); });
        Path body = root.resolve("original-domain.json"); Files.writeString(body, "{\"schema\":\"fixture.domain/v1\",\"pending\":null,\"applied\":[]}");
        var request = new DomainBodies.ImportRequest(DomainBodies.Slot.COUNCIL, "fixture.domain/v1", LedgerFiles.read(body, 65_536).pin().reference(),
                "{\"source\":\"actual-original-producer\"}".getBytes(StandardCharsets.UTF_8), List.of(), "one-domain");
        DomainBodies.PreparedImport prepared = failing.previewImport(request);
        assertThrows(CommitUncertainException.class, () -> failing.commitImport(prepared));
        fixture.storage.reconcileStorageOnly();
        ContinuityWriter reopened = new ContinuityWriter(fixture.layout, sources(fixture), ORDINARY, Clock.systemUTC(), extensions, StorageWriteGuardTestSupport.forLayout(fixture.layout));
        Receipt recovered = reopened.commitImport(prepared); assertEquals(Disposition.ALREADY_COMMITTED, recovered.disposition()); assertEquals(2, recovered.writes());
        assertInstanceOf(DomainBodies.Available.class, reopened.read(DomainBodies.Slot.COUNCIL));
        boolean snapshotNeedsRecovery = reopened.locked(session -> session.head().snapshotNeedsRecovery());
        assertFalse(snapshotNeedsRecovery); assertEquals(0, reopened.commitImport(prepared).writes());
    }
    @Test void actualWriterLockAndWriteThroughRenameSupportLongOriginalPaths() throws Exception {
        assertTrue(Platform.isWindows()); Path longRoot = root.resolve("long-writer");
        while (longRoot.toAbsolutePath().toString().length() < 320) longRoot = longRoot.resolve("native-writer-original-path-component");
        WriterFixture fixture = new WriterFixture(longRoot); Request request = WriterFixture.settled("long-original", 1024, 2);
        Receipt receipt = fixture.writer.commit(fixture.writer.preview(request)); assertEquals(Disposition.COMMITTED, receipt.disposition());
        assertEquals(request.identity(), receipt.head().toJson().get("last_event_identity").textValue());
        long sequence = fixture.writer.locked(session -> session.head().state().sequence()); assertEquals(1L, sequence);
        fixture.writer.locked(session -> { session.requireWriter(fixture.layout.lock()); return null; });
    }
}
