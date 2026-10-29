package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual cold Request-to-preview recovery; old in-memory Prepared is deliberately discarded. */
class CommittedRequestRecoveryTest {
    @TempDir Path root;
    private static final TransitionAuthority ORDINARY = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState state, Request request) { return request.identity(); }
        @Override public ContinuityState reduce(ContinuityState state, Request request) { return OriginalWindowReducer.reduce(state, request); }
    };
    private static final TransitionAuthority EXPIRED = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState state, Request request) {
            throw new AssertionError("durable recovery must not requalify expired business preconditions");
        }
        @Override public ContinuityState reduce(ContinuityState state, Request request) {
            throw new AssertionError("durable recovery must not replay the business reducer");
        }
    };
    private static List<ExactRef> sources(WriterFixture fixture) throws IOException {
        return List.of(LedgerFiles.read(fixture.source, ContinuityJson.DOCUMENT_MAX_BYTES).pin().reference());
    }
    private static ContinuityWriter reopen(WriterFixture fixture, TransitionAuthority authority) throws IOException {
        return new ContinuityWriter(fixture.layout, sources(fixture), authority, StorageWriteGuardTestSupport.forLayout(fixture.layout));
    }
    private static Prepared roundTrip(Prepared prepared) {
        return WriterTransactionCodec.decodePrepared(WriterTransactionCodec.encodePrepared(prepared), WriterFixture.MACHINE);
    }

    @Test void coldRequestAfterEachActualDurableBoundaryRecoversWithoutExpiredBusinessAuthority() throws Exception {
        assertTrue(Platform.isWindows());
        for (WriterFaultProbe.Boundary boundary : WriterFaultProbe.Boundary.values()) {
            WriterFixture fixture = new WriterFixture(root.resolve(boundary.name()));
            Request request = WriterFixture.settled("cold-request", 1024, 2);
            ContinuityWriter faulting = new ContinuityWriter(fixture.layout, sources(fixture), ORDINARY, Clock.systemUTC(),
                    ContinuityWriter.Extensions.none(), StorageWriteGuardTestSupport.forLayout(fixture.layout),
                    (actual, sequence) -> { if (actual == boundary) throw new IOException("crash after " + boundary); });
            assertThrows(CommitUncertainException.class, () -> faulting.commit(faulting.preview(request)));
            fixture.storage.reconcileStorageOnly();
            byte[] oldSnapshot = Files.readAllBytes(fixture.layout.snapshot());
            byte[] committedEvent = Files.readAllBytes(fixture.layout.event(1));
            boolean hadIndex = Files.exists(fixture.layout.sourceIndex(request.sourceKey()));

            ContinuityWriter cold = reopen(fixture, EXPIRED);
            Prepared recovery = roundTrip(cold.preview(request));
            assertArrayEquals(oldSnapshot, Files.readAllBytes(fixture.layout.snapshot()), "preview remains read-only");
            assertEquals(hadIndex, Files.exists(fixture.layout.sourceIndex(request.sourceKey())));
            assertEquals(request.identity(), recovery.preconditionDigest(), "known identity is DATA, not fresh business qualification");
            assertTrue(ContinuityJson.same(recovery.predecessor().state().toJson(), recovery.reduced().toJson()));

            Receipt receipt = cold.commit(recovery);
            int expectedWrites = switch (boundary) {
                case EVENT_PUBLISHED -> 2;
                case SNAPSHOT_PUBLISHED -> 1;
                case SOURCE_INDEX_PUBLISHED -> 0;
            };
            assertEquals(Disposition.ALREADY_COMMITTED, receipt.disposition());
            assertEquals(expectedWrites, receipt.writes());
            assertEquals(expectedWrites > 0, receipt.recoveredCommittedReceipt());
            assertEquals(1, receipt.head().sequence());
            assertEquals(WriterFixture.state().get("pending_cycle"), receipt.head().toJson().get("pending_cycle"));
            assertEquals(11559, receipt.head().toJson().get("NEXT").intValue());
            assertArrayEquals(committedEvent, Files.readAllBytes(fixture.layout.event(1)));
            assertFalse(Files.exists(fixture.layout.event(2)));
            Receipt decoded = WriterTransactionCodec.decodeReceipt(WriterTransactionCodec.encodeReceipt(receipt), WriterFixture.MACHINE);
            assertEquals(receipt.disposition(), decoded.disposition());
            assertEquals(receipt.writes(), decoded.writes());
            assertTrue(ContinuityJson.same(receipt.head().toJson(), decoded.head().toJson()));
            assertEquals(0, cold.commit(roundTrip(cold.preview(request))).writes());
        }
    }

    @Test void duplicateRequestAfterARealDescendantRetainsNewestHeadAndNeverAddsCredit() throws Exception {
        assertTrue(Platform.isWindows());
        WriterFixture fixture = new WriterFixture(root.resolve("descendant"));
        Request first = WriterFixture.settled("first", 1024, 2);
        fixture.writer.commit(fixture.writer.preview(first));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("next", 1048, 3)));
        ContinuityWriter cold = reopen(fixture, EXPIRED);
        Receipt recovered = cold.locked(same -> same.commit(roundTrip(same.preview(first))));
        assertEquals(Disposition.ALREADY_COMMITTED, recovered.disposition());
        assertEquals(0, recovered.writes()); assertEquals(2, recovered.head().sequence());
        assertEquals(1048, recovered.head().settledDateRaw()); assertEquals(3, recovered.head().settledCycles());
        assertFalse(Files.exists(fixture.layout.event(3)));
    }

    @Test void changedSameIdPayloadIsRejectedBeforeAuthorityOrRecoveryWrites() throws Exception {
        assertTrue(Platform.isWindows());
        WriterFixture fixture = new WriterFixture(root.resolve("conflict"));
        Request request = WriterFixture.settled("fixed-id", 1024, 2);
        ContinuityWriter faulting = new ContinuityWriter(fixture.layout, sources(fixture), ORDINARY, Clock.systemUTC(),
                ContinuityWriter.Extensions.none(), StorageWriteGuardTestSupport.forLayout(fixture.layout),
                (actual, sequence) -> { if (actual == WriterFaultProbe.Boundary.EVENT_PUBLISHED) throw new IOException("event-only crash"); });
        assertThrows(CommitUncertainException.class, () -> faulting.commit(faulting.preview(request)));
        fixture.storage.reconcileStorageOnly();
        byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
        ContinuityWriter cold = reopen(fixture, EXPIRED);
        assertThrows(ContractViolationException.class, () -> cold.preview(WriterFixture.settled("fixed-id", 1048, 3)));
        assertArrayEquals(snapshot, Files.readAllBytes(fixture.layout.snapshot()));
        assertFalse(Files.exists(fixture.layout.sourceIndex(request.sourceKey())));
        assertFalse(Files.exists(fixture.layout.event(2)));
    }

    @Test void uncommittedRequestStillUsesActualSameLockAuthorityAndReducerInPreviewAndCommit() throws Exception {
        assertTrue(Platform.isWindows());
        WriterFixture fixture = new WriterFixture(root.resolve("new-request"));
        AtomicInteger validations = new AtomicInteger(), reductions = new AtomicInteger();
        TransitionAuthority actual = new TransitionAuthority() {
            @Override public String revalidate(ContinuityState state, Request request) throws IOException {
                WindowsLedgerLock.requireHeld(fixture.layout.lock()); validations.incrementAndGet(); return request.identity();
            }
            @Override public ContinuityState reduce(ContinuityState state, Request request) throws IOException {
                WindowsLedgerLock.requireHeld(fixture.layout.lock()); reductions.incrementAndGet(); return OriginalWindowReducer.reduce(state, request);
            }
        };
        ContinuityWriter writer = reopen(fixture, actual);
        Prepared fresh = roundTrip(writer.preview(WriterFixture.settled("new-request", 1024, 2)));
        assertEquals(1, validations.get()); assertEquals(1, reductions.get());
        assertEquals(Disposition.COMMITTED, writer.commit(fresh).disposition());
        assertEquals(2, validations.get()); assertEquals(2, reductions.get());
    }

    @Test void actualOriginalPythonApplyAlsoReturnsCommittedResultBeforeInvokingTransition() throws Exception {
        assertTrue(Platform.isWindows());
        WriterFixture fixture = new WriterFixture(root.resolve("java-original-parity"));
        Request request = WriterFixture.settled("original-exact-id", 1024, 2);
        Receipt first = fixture.writer.commit(fixture.writer.preview(request));
        ObjectNode input = org.xar.ck3.control.contracts.StrictJson.object();
        input.set("before", WriterFixture.state()); input.set("details", request.detailsObject());
        input.put("path", root.resolve("python-original/ROOT-CONTINUITY-WINDOW.json").toString());
        String program = """
                import json,sys
                from pathlib import Path
                sys.path.insert(0,sys.argv[1])
                from tools.g2_saved_campaign import root_continuity_window as original
                value=json.load(sys.stdin)
                path=Path(value['path'])
                path.parent.mkdir(parents=True)
                original._atomic(path,value['before'])
                ledger=original.WindowLedger(path)
                first=ledger.apply('settled_batch',value['details'])
                def expired(*args,**kwargs):
                    raise AssertionError('exact duplicate invoked original transition')
                original.transition=expired
                again=ledger.apply('settled_batch',value['details'])
                assert first==again
                print(json.dumps(again,sort_keys=True,ensure_ascii=False,separators=(',',':')))
                """;
        Process child = new ProcessBuilder(WindowsWriterInteropTest.python(), "-B", "-X", "utf8", "-c", program,
                WindowsWriterInteropTest.repository().toString()).redirectErrorStream(true).start();
        try {
            child.getOutputStream().write(ContinuityJson.canonical(input)); child.getOutputStream().close();
            assertTrue(child.waitFor(15, TimeUnit.SECONDS), "original Python duplicate consumer timed out");
            byte[] output = child.getInputStream().readAllBytes();
            assertEquals(0, child.exitValue(), new String(output, StandardCharsets.UTF_8));
            assertTrue(ContinuityJson.same(first.head().toJson(), object(output)));
            Receipt cold = reopen(fixture, EXPIRED).locked(same -> same.commit(roundTrip(same.preview(request))));
            assertTrue(ContinuityJson.same(cold.head().toJson(), object(output)));
        } finally { child.destroyForcibly(); }
    }
}
