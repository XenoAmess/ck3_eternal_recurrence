package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.contracts.*;

/** Actual closed writer/cold-reader projection only; application must prove original action/Driver semantics. */
final class DriverActionHistoryWriterConsumerTest {
    @TempDir Path temporary;
    private ContinuityWriter writer(WriterFixture f,boolean corrupt)throws IOException {
        AtomicReference<ContinuityWriter> original=new AtomicReference<>();
        TransitionAuthority producer=new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before,Request request)throws IOException {throw new IOException("actual same-lock Head required");}
            @Override public String revalidate(Head before,Request request)throws IOException {
                var own=original.get();var same=own.borrowedSession();own.requireSession(same);
                StrictJson.require(before.digest().equals(same.head().digest()),"fixture publication crossed its actual canonical point");
                var ref=ExactRef.fromJson(request.detailsObject().get("source"));same.verifyPin(same.capturePin(ref,65_536));
                return ContinuityJson.digest(request.detailsObject());
            }
            @Override public ContinuityState reduce(ContinuityState before,Request request) {
                ObjectNode after=before.toJson();after.set(DRIVER_ACTION_HISTORY_FIELD,request.detailsObject());
                if(corrupt)after.put("last_settled_cycles",before.settledCycles()+1);
                return ContinuityState.fromJson(after,before.machineId());
            }
        };
        var writer=new ContinuityWriter(f.layout,List.of(LedgerFiles.read(f.source,65_536).pin().reference()),producer,f.storage);
        original.set(writer);return writer;
    }
    private static Request request(WriterFixture f)throws IOException {
        ObjectNode details=StrictJson.object();details.put("schema","fixture.driver-action-history-source/v1").put("evidence_id","actual-software-projection");
        details.set("source",LedgerFiles.read(f.source,65_536).pin().reference().toJson());
        details.put("original_decimal_identity","18446744073709551615");
        return new Request(DRIVER_ACTION_HISTORY_KIND,ContinuityJson.canonical(details),List.of());
    }
    @Test void actualPublicationAndHistoricalReaderPreserveTheExactFieldWithoutAnyOtherStateCredit()throws Exception {
        assertTrue(Platform.isWindows());WriterFixture f=new WriterFixture(temporary.resolve("cold"));var writer=writer(f,false);var request=request(f);
        var receipt=writer.locked(same->same.commit(same.preview(request)));
        assertTrue(ContinuityJson.same(request.detailsObject(),receipt.head().toJson().get(DRIVER_ACTION_HISTORY_FIELD)));
        assertTrue(ContinuityJson.same(WriterFixture.state().get("pending_cycle"),receipt.head().toJson().get("pending_cycle")));
        assertEquals(1,receipt.head().settledCycles());assertEquals(11559,receipt.head().toJson().get("NEXT").longValue());
        assertFalse(receipt.head().toJson().has(ACTION_LIFECYCLE_FIELD),"history publication cannot mint an action record");
        assertArrayEquals(receipt.head().canonicalBytes(),writer.locked(ContinuityStorePort.Session::head).state().canonicalBytes());
        ObjectNode event=ContinuityJson.parseObject(Files.readAllBytes(f.layout.event(1)),ContinuityJson.DOCUMENT_MAX_BYTES);
        ObjectNode after=ContinuityJson.object(event.get("after"));after.put("last_settled_cycles",2);
        Files.write(f.layout.event(1),ContinuityJson.canonical(event));Files.write(f.layout.snapshot(),ContinuityJson.canonical(after));
        assertThrows(ContractViolationException.class,()->writer.locked(ContinuityStorePort.Session::head));
        assertFalse(Files.exists(f.layout.event(2)));
    }
    @Test void aLivePublisherCannotBorrowItsKindToChangeCycleCredit()throws Exception {
        assertTrue(Platform.isWindows());WriterFixture f=new WriterFixture(temporary.resolve("wrong-reducer"));var wrong=writer(f,true);
        assertThrows(ContractViolationException.class,()->wrong.preview(request(f)));
        assertEquals(0,f.storage.successfulBatches());assertFalse(Files.exists(f.layout.event(1)));
    }
}
