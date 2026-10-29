package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;

class HistoricalCommittedProofTest {
    @TempDir Path root;
    private static List<ExactRef> sources(WriterFixture fixture) throws IOException {
        return List.of(LedgerFiles.read(fixture.source, 65_536).pin().reference());
    }
    private static ContinuityWriter readOnly(WriterFixture fixture) throws IOException {
        return new ContinuityWriter(fixture.layout, sources(fixture), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState state, Request request) { throw new AssertionError("historical publication cannot query a new authority"); }
            @Override public ContinuityState reduce(ContinuityState state, Request request) { throw new AssertionError("historical publication cannot replay a reducer"); }
        }, StorageWriteGuardTestSupport.forLayout(fixture.layout));
    }
    private static Prepared changedReduction(Prepared original, ContinuityState reduced) {
        return new Prepared(original.predecessor(), original.request(), original.sources(), original.evidence(), reduced, original.preconditionDigest());
    }
    @Test void exactDurableEventAfterActualCommitExceptionIsFoundWithoutRepeatingCommitOrRepair() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("query-uncertain"));
        Prepared original = fixture.writer.preview(WriterFixture.settled("uncertain-child", 1024, 2));
        byte[] before = Files.readAllBytes(fixture.layout.snapshot());
        ContinuityWriter reader = readOnly(fixture);
        assertTrue(reader.locked(session -> session.queryCommitted(original)).isEmpty());
        TransitionAuthority actual = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState head, Request request) { return ContinuityJson.digest(request.detailsObject()); }
            @Override public ContinuityState reduce(ContinuityState head, Request request) {
                return org.xar.ck3.control.continuity.OriginalWindowReducer.reduce(head, request);
            }
        };
        ContinuityWriter failing = new ContinuityWriter(fixture.layout, sources(fixture), actual, Clock.systemUTC(), ContinuityWriter.Extensions.none(), StorageWriteGuardTestSupport.forLayout(fixture.layout), (boundary, sequence) -> { if (boundary == WriterFaultProbe.Boundary.EVENT_PUBLISHED) throw new IOException("actual post-event exception"); });
        assertThrows(CommitUncertainException.class, () -> failing.commit(original));
        Receipt retained = reader.locked(session -> session.queryCommitted(original)).orElseThrow();
        assertEquals(Disposition.ALREADY_COMMITTED, retained.disposition()); assertEquals(0, retained.writes());
        assertFalse(retained.recoveredCommittedReceipt()); assertEquals(1L, retained.head().sequence());
        reader.locked(session -> { session.requireCommitted(original, retained); return null; });
        assertArrayEquals(before, Files.readAllBytes(fixture.layout.snapshot()));
        assertFalse(Files.exists(fixture.layout.sourceIndex(original.request().sourceKey())));
        assertFalse(Files.exists(fixture.layout.event(2)));
    }
    @Test void originalCommittedChildRemainsProvableAfterLaterHeadWithoutAnyAuthorityOrLedgerWrite() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("history"));
        Prepared original = fixture.writer.preview(WriterFixture.settled("original-child", 1024, 2));
        Receipt receipt = fixture.writer.commit(original);
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("later-parent", 1048, 3)));
        byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
        byte[] first = Files.readAllBytes(fixture.layout.event(1)), second = Files.readAllBytes(fixture.layout.event(2));
        ContinuityWriter verifier = readOnly(fixture);
        verifier.locked(session -> {
            session.requireCommitted(original, receipt);
            session.requireCommitted(original, receipt);
            assertEquals(2L, session.head().state().sequence());
            assertEquals(WriterFixture.state().get("pending_cycle"), session.head().state().toJson().get("pending_cycle"));
            return null;
        });
        assertArrayEquals(snapshot, Files.readAllBytes(fixture.layout.snapshot()));
        assertArrayEquals(first, Files.readAllBytes(fixture.layout.event(1)));
        assertArrayEquals(second, Files.readAllBytes(fixture.layout.event(2)));
        assertFalse(Files.exists(fixture.layout.event(3)));
        Receipt duplicate = fixture.writer.commit(original);
        assertEquals(Disposition.ALREADY_COMMITTED, duplicate.disposition()); assertEquals(2L, duplicate.head().sequence());
        verifier.locked(session -> { session.requireCommitted(original, duplicate); return null; });
    }
    @Test void changedDetailsReducedStateReceiptIdentityOrUnrelatedHeadCannotBorrowHistoricalCredit() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("forged"));
        Prepared original = fixture.writer.preview(WriterFixture.settled("one-child", 1024, 2)); Receipt receipt = fixture.writer.commit(original);
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("later", 1048, 3)));
        var changed = original.reduced().toJson(); changed.put("last_settled_cycles", 999);
        Prepared wrongReduced = changedReduction(original, ContinuityState.fromJson(changed, WriterFixture.MACHINE));
        Request wrongDetails = WriterFixture.settled("one-child", 1048, 3);
        Prepared changedRequest = new Prepared(original.predecessor(), wrongDetails, original.sources(), original.evidence(), original.reduced(), original.preconditionDigest());
        var invented = receipt.head().toJson(); invented.put("last_settled_cycles", 999);
        Receipt wrongHead = new Receipt(Disposition.COMMITTED, ContinuityState.fromJson(invented, WriterFixture.MACHINE), receipt.eventIdentity(), 0, false);
        Receipt changedDetailsReceipt = new Receipt(Disposition.COMMITTED, receipt.head(), wrongDetails.identity(), 0, false);
        Receipt wrongIdentity = new Receipt(Disposition.COMMITTED, receipt.head(), "0".repeat(64), 0, false);
        Receipt noChange = new Receipt(Disposition.NO_CHANGE, receipt.head(), receipt.eventIdentity(), 0, false);
        readOnly(fixture).locked(session -> {
            assertThrows(ContractViolationException.class, () -> session.requireCommitted(wrongReduced, receipt));
            assertThrows(ContractViolationException.class, () -> session.requireCommitted(changedRequest, changedDetailsReceipt));
            assertThrows(ContractViolationException.class, () -> session.requireCommitted(original, wrongHead));
            assertThrows(ContractViolationException.class, () -> session.requireCommitted(original, wrongIdentity));
            assertThrows(ContractViolationException.class, () -> session.requireCommitted(original, noChange));
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(3)));
    }
    @Test void preparedButNeverCommittedRequestAndChangedSourceDoNotQualify() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("not-committed"));
        Prepared original = fixture.writer.preview(WriterFixture.settled("uncommitted", 1024, 2));
        var projected = original.reduced().toJson(); projected.put("sequence", 1); projected.put("last_event_identity", original.request().identity());
        Receipt invented = new Receipt(Disposition.COMMITTED, ContinuityState.fromJson(projected, WriterFixture.MACHINE), original.request().identity(), 0, false);
        readOnly(fixture).locked(session -> {
            assertThrows(IOException.class, () -> session.requireCommitted(original, invented)); return null;
        });
        assertFalse(Files.exists(fixture.layout.event(1)));
        Receipt actual = fixture.writer.commit(original);
        ContinuityWriter unchangedAuthority = readOnly(fixture);
        Files.writeString(fixture.source, "changed actual source");
        assertThrows(IOException.class, () -> unchangedAuthority.locked(session -> { session.requireCommitted(original, actual); return null; }));
    }
    @Test void missingSourceIndexDoesNotTriggerRepairDuringReadOnlyHistoricalVerification() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("missing-index"));
        Prepared original = fixture.writer.preview(WriterFixture.settled("durable-child", 1024, 2)); Receipt receipt = fixture.writer.commit(original);
        Path index = fixture.layout.sourceIndex(original.request().sourceKey()); Files.delete(index);
        byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
        readOnly(fixture).locked(session -> { session.requireCommitted(original, receipt); return null; });
        assertFalse(Files.exists(index)); assertFalse(Files.exists(fixture.layout.event(2)));
        assertArrayEquals(snapshot, Files.readAllBytes(fixture.layout.snapshot()));
    }
    @Test void readPinnedReturnsExactDetachedBytesAndRejectsReplacedIdentityOrOversizedReads() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root.resolve("pinned-read"));
        Pin pin = LedgerFiles.read(fixture.source, 65_536).pin(); byte[] expected = Files.readAllBytes(fixture.source);
        fixture.writer.locked(session -> {
            byte[] returned = session.readPinned(pin, 65_536); assertArrayEquals(expected, returned); returned[0] ^= 7;
            assertArrayEquals(expected, session.readPinned(pin, 65_536));
            assertThrows(ContractViolationException.class, () -> session.readPinned(pin, 0));
            assertThrows(ContractViolationException.class, () -> session.readPinned(pin, MAX_PIN_BYTES + 1));
            assertThrows(IOException.class, () -> session.readPinned(pin, 1));
            Path replacement = fixture.source.resolveSibling("same-bytes.txt"); Files.write(replacement, expected);
            Files.move(replacement, fixture.source, StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class, () -> session.readPinned(pin, 65_536));
            return null;
        });
    }
    @Test void domainEvidenceMayRetainTheFullNativePacketBeyondTheDomainBodyBound() throws Exception {
        assertTrue(Platform.isWindows());
        for (DomainBodies.Slot slot : List.of(DomainBodies.Slot.COUNCIL_CONTINUATION, DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS)) {
        WriterFixture fixture = new WriterFixture(root.resolve("full-evidence-" + slot));
        Path archiveRoot = fixture.layout.snapshot().getParent().resolve("archive"); Files.createDirectory(archiveRoot);
        var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archiveRoot, fixture.layout.lock(), 4_194_304), StorageWriteGuardTestSupport.forOriginalLock(fixture.layout.lock()));
        var registration = new DomainBodies.Registration(slot, "fixture.continuation/v1", 65_536, sources(fixture),
                (head, previous, request, body) -> LedgerFiles.sha(body));
        TransitionAuthority unused = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState head, Request request) { throw new AssertionError("domain has its one actual verifier"); }
            @Override public ContinuityState reduce(ContinuityState head, Request request) { throw new AssertionError("domain cannot use an ordinary reducer"); }
        };
        ContinuityWriter writer = new ContinuityWriter(fixture.layout, sources(fixture), unused, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(artifacts), Optional.empty()), StorageWriteGuardTestSupport.forLayout(fixture.layout));
        Path packet = fixture.layout.snapshot().getParent().resolve("original-native-packet.bin");
        byte[] raw = new byte[ContinuityJson.DOMAIN_MAX_BYTES + 17]; raw[0] = 71; raw[raw.length - 1] = 92; Files.write(packet, raw);
        ExactRef nativePacket = LedgerFiles.read(packet, MAX_PIN_BYTES).pin().reference();
        Path body = fixture.layout.snapshot().getParent().resolve("original-domain-body.json");
        Files.writeString(body, "{\"schema\":\"fixture.continuation/v1\",\"pending\":null}");
        var input = new DomainBodies.ImportRequest(registration.slot(), registration.contractSchema(), LedgerFiles.read(body, 65_536).pin().reference(),
                "{\"source\":\"actual-original-producer\"}".getBytes(StandardCharsets.UTF_8), List.of(nativePacket), "actual-full-native");
        Receipt committed = writer.commitImport(writer.previewImport(input)); assertEquals(Disposition.COMMITTED, committed.disposition());
        var available = assertInstanceOf(DomainBodies.Available.class, writer.read(registration.slot()));
        assertEquals(slot, available.reference().slot());
        assertEquals(available.reference(), DomainBodies.BodyRef.fromJson(available.reference().toJson()));
        assertArrayEquals(raw, Files.readAllBytes(packet));
        assertEquals(WriterFixture.state().get("pending_cycle"), committed.head().toJson().get("pending_cycle"));
        }
    }

    @Test void sameSessionHistoricalProofSeesTheNextActualCommitWithoutResubmittingAbsence() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("retained-next-head"));
        Prepared first = fixture.writer.preview(WriterFixture.settled("retained-first", 1024, 2));
        Receipt firstReceipt = fixture.writer.commit(first);
        fixture.writer.locked(same -> {
            same.requireCommitted(first, firstReceipt);
            same.requireCommitted(first, firstReceipt);
            assertEquals(1L, same.head().state().sequence());
            Prepared next = same.preview(WriterFixture.settled("retained-next", 1048, 3));
            assertTrue(same.queryCommitted(next).isEmpty());
            assertFalse(Files.exists(fixture.layout.event(2)));
            Receipt nextReceipt = same.commit(next);
            assertEquals(Disposition.COMMITTED, nextReceipt.disposition());
            same.requireCommitted(first, firstReceipt);
            same.requireCommitted(next, nextReceipt);
            Receipt retained = same.queryCommitted(first).orElseThrow();
            assertEquals(Disposition.ALREADY_COMMITTED, retained.disposition());
            assertEquals(2L, retained.head().sequence());
            assertEquals(0, retained.writes());
            assertEquals(2L, same.head().state().sequence());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(3)));
    }
    @Test void retainedHistoricalProofRejectsEqualByteEventReplacementWithinTheSameSession() throws Exception {
        WriterFixture fixture = new WriterFixture(root.resolve("retained-event-identity"));
        Prepared original = fixture.writer.preview(WriterFixture.settled("retained-original", 1024, 2));
        Receipt receipt = fixture.writer.commit(original);
        byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
        fixture.writer.locked(same -> {
            same.requireCommitted(original, receipt);
            Path replacement = root.resolve("equal-event-with-new-native-identity.json");
            Files.copy(fixture.layout.event(1), replacement);
            Files.move(replacement, fixture.layout.event(1), StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class, () -> same.requireCommitted(original, receipt));
            return null;
        });
        assertArrayEquals(snapshot, Files.readAllBytes(fixture.layout.snapshot()));
        assertFalse(Files.exists(fixture.layout.event(2)));
    }
}
