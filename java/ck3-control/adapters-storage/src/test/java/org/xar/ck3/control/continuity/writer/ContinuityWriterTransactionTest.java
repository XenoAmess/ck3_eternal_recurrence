package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityEvent;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

class ContinuityWriterTransactionTest {
    @TempDir Path root;
    @Test void realTemporaryLedgerRoundTripsIntoOriginalPythonConsumerAndRetainsUnknown() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root);
        Request request = WriterFixture.settled("batch-one", 1024, 2);
        var result = fixture.writer.commit(fixture.writer.preview(request));
        assertEquals(Disposition.COMMITTED, result.disposition()); assertEquals(1, result.head().sequence()); assertEquals(3, result.writes());
        assertTrue(ContinuityJson.same(WriterFixture.state().get("pending_cycle"), result.head().toJson().get("pending_cycle")));
        assertEquals(11559, result.head().toJson().get("NEXT").intValue());
        assertEquals(Disposition.ALREADY_COMMITTED, fixture.writer.commit(fixture.writer.preview(request)).disposition());
        String script = "import sys,json\nsys.path.insert(0,sys.argv[1])\nfrom tools.g2_saved_campaign.root_continuity_window import WindowLedger\nv=WindowLedger(sys.argv[2]).load()\nprint(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')))\n";
        Process child = new ProcessBuilder(WindowsWriterInteropTest.python(), "-B", "-X", "utf8", "-c", script,
                WindowsWriterInteropTest.repository().toString(), fixture.layout.snapshot().toString()).redirectErrorStream(true).start();
        try {
            assertTrue(child.waitFor(15, java.util.concurrent.TimeUnit.SECONDS)); byte[] raw = child.getInputStream().readAllBytes(); assertEquals(0, child.exitValue());
            assertTrue(ContinuityJson.same(result.head().toJson(), object(raw)));
        } finally { child.destroyForcibly(); }
        assertEquals(0, fixture.writer.commit(fixture.writer.preview(request)).writes());
    }
    @Test void changedSourcesSameBytesNewFileIdentityAndStaleHeadRejectBeforeWrite() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root);
        var prepared = fixture.writer.preview(WriterFixture.settled("one", 1024, 2));
        byte[] old = Files.readAllBytes(fixture.source); Path replacement = root.resolve("source-replacement.txt"); Files.write(replacement, old);
        Files.move(replacement, fixture.source, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        assertThrows(java.io.IOException.class, () -> fixture.writer.commit(prepared));
        assertFalse(Files.exists(fixture.layout.event(1)));
        WriterFixture second = new WriterFixture(root.resolve("second"));
        var stale = second.writer.preview(WriterFixture.settled("old", 1024, 2));
        second.writer.commit(second.writer.preview(WriterFixture.settled("new", 1048, 3)));
        assertThrows(ContractViolationException.class, () -> second.writer.commit(stale)); assertFalse(Files.exists(second.layout.event(2)));
    }
    @Test void exactCommittedEventRepairsSnapshotAndIndexWithoutReplayingTransition() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root);
        Request request = WriterFixture.settled("crash-event", 1024, 2);
        ContinuityState old = ContinuityState.fromJson(WriterFixture.state(), WriterFixture.MACHINE);
        ObjectNode after = OriginalWindowReducer.reduce(old, request).toJson(); after.put("sequence", 1); after.put("last_event_identity", request.identity());
        ContinuityEvent event = new ContinuityEvent(1, "2026-10-23T00:00:00Z", request.kind(), request.details(), request.identity(),
                ContinuityJson.digest(old.toJson()), ContinuityState.fromJson(after, WriterFixture.MACHINE));
        StorageWriteGuardTestSupport.atomic(fixture.layout.event(1), ContinuityJson.canonical(event.toJson()), false);
        Request next = WriterFixture.settled("following", 1048, 3);
        var committed = fixture.writer.commit(fixture.writer.preview(next));
        assertEquals(2, committed.head().sequence()); assertTrue(committed.recoveredCommittedReceipt()); assertEquals(5, committed.writes());
        assertTrue(Files.exists(fixture.layout.sourceIndex(request.sourceKey())));
    }
    @Test void commitRechecksHistoricalIdentityAndMissingIndexAfterActualRevalidation() throws Exception {
        assertTrue(Platform.isWindows());
        for (boolean appearIndex : List.of(false, true)) {
            WriterFixture fixture = new WriterFixture(root.resolve(appearIndex ? "appeared-index" : "replaced-event"));
            Request first = WriterFixture.settled("committed-before-revalidation", 1024, 2);
            Receipt committed = fixture.writer.commit(fixture.writer.preview(first));
            assertEquals(Disposition.COMMITTED, committed.disposition());
            assertEquals(1, committed.head().sequence());
            byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
            byte[] event = Files.readAllBytes(fixture.layout.event(1));
            Path index = fixture.layout.sourceIndex(first.sourceKey());
            byte[] indexBytes = Files.readAllBytes(index);
            if (appearIndex) Files.delete(index);
            java.util.concurrent.atomic.AtomicInteger checks = new java.util.concurrent.atomic.AtomicInteger();
            ContinuityWriter guarded = new ContinuityWriter(fixture.layout,
                    List.of(LedgerFiles.read(fixture.source, 65_536).pin().reference()), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request request) throws java.io.IOException {
                    if (checks.incrementAndGet() == 2) {
                        if (appearIndex) Files.write(index, indexBytes);
                        else {
                            Path replacement = fixture.layout.snapshot().getParent().resolve("equal-original-replacement.json");
                            Files.write(replacement, event);
                            Files.move(replacement, fixture.layout.event(1), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                        }
                    }
                    return ContinuityJson.digest(request.detailsObject());
                }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) {
                    return OriginalWindowReducer.reduce(predecessor, request);
                }
            }, StorageWriteGuardTestSupport.forLayout(fixture.layout));
            Request next = WriterFixture.settled("must-not-publish-after-head-change", 1048, 3);
            Prepared prepared = guarded.preview(next);
            assertEquals(1, checks.get());
            assertThrows(java.io.IOException.class, () -> guarded.commit(prepared));
            assertEquals(2, checks.get(), "mutation occurred after the commit's first fresh projection");
            assertArrayEquals(snapshot, Files.readAllBytes(fixture.layout.snapshot()));
            assertArrayEquals(event, Files.readAllBytes(fixture.layout.event(1)));
            assertFalse(Files.exists(fixture.layout.event(2)));
            assertFalse(Files.exists(fixture.layout.sourceIndex(next.sourceKey())));
            assertTrue(ContinuityJson.same(committed.head().toJson().get("pending_cycle"),
                    ContinuityJson.parseObject(snapshot, ContinuityJson.LEDGER_MAX_BYTES).get("pending_cycle")));
            assertEquals(11559, committed.head().toJson().get("NEXT").intValue());
        }
    }
    @Test void immutableEventConflictNeverOverwritesAndPendingRemovalIsRejected() throws Exception {
        assertTrue(Platform.isWindows()); WriterFixture fixture = new WriterFixture(root);
        Path target = fixture.layout.event(1); StorageWriteGuardTestSupport.atomic(target, "{}".getBytes(java.nio.charset.StandardCharsets.UTF_8), false);
        assertThrows(java.io.IOException.class, () -> StorageWriteGuardTestSupport.atomic(target, "{\"x\":1}".getBytes(java.nio.charset.StandardCharsets.UTF_8), false));
        assertEquals("{}\n", Files.readString(target));
        WriterFixture clean = new WriterFixture(root.resolve("clean"));
        ContinuityWriter unsafe = new ContinuityWriter(clean.layout, List.of(LedgerFiles.read(clean.source, 65_536).pin().reference()), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState head, Request request) { return request.identity(); }
            @Override public ContinuityState reduce(ContinuityState head, Request request) {
                ObjectNode state = head.toJson(); state.remove("pending_cycle"); return ContinuityState.fromJson(state, head.machineId());
            }
        }, StorageWriteGuardTestSupport.forLayout(clean.layout));
        assertThrows(ContractViolationException.class, () -> unsafe.preview(WriterFixture.settled("unsafe", 1024, 2)));
        assertFalse(Files.exists(clean.layout.event(1)));
    }
}
