package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ContractViolationException;

class ContinuityStoreReadTest {
    @TempDir Path root;

    private WriterFixture committed(String directory) throws IOException {
        WriterFixture fixture=new WriterFixture(root.resolve(directory));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("first",1024,2)));
        return fixture;
    }
    private static ObjectNode json(Path path) throws IOException {
        return ContinuityJson.parseObject(Files.readAllBytes(path),ContinuityJson.LEDGER_MAX_BYTES);
    }
    @Test void coldHeadRetainsOriginalDocumentsAndWholeCanonicalState() throws Exception {
        WriterFixture fixture=committed("valid");
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("second",1048,3)));
        fixture.writer.locked(session->{
            Head actual=new ContinuityStore(fixture.layout).head();
            assertEquals(2,actual.state().sequence());
            assertEquals(1048,actual.state().settledDateRaw());
            assertEquals(3,actual.state().settledCycles());
            assertEquals(6,actual.documents().size());
            assertFalse(actual.snapshotNeedsRecovery());
            assertTrue(actual.indexRepairs().isEmpty());
            assertTrue(actual.absent().contains(fixture.layout.event(3)));
            for(Pin original:actual.documents())
                assertEquals(original,session.capturePin(original.reference(),ContinuityJson.LEDGER_MAX_BYTES));
            return null;
        });
    }
    @Test void coldHeadRejectsAnchorContentChangedBeforeRead() throws Exception {
        WriterFixture fixture=new WriterFixture(root.resolve("anchor-corrupt"));
        Path anchor=Path.of(fixture.layout.anchor().path());
        ObjectNode changed=json(anchor);changed.put("last_settled_cycles",999);
        Files.write(anchor,ContinuityJson.canonical(changed));
        fixture.writer.locked(session->{
            assertThrows(IOException.class,()->new ContinuityStore(fixture.layout).head());
            return null;
        });
    }
    @Test void coldHeadRejectsEventPredecessorChangedBeforeRead() throws Exception {
        WriterFixture fixture=committed("event-corrupt");
        Path event=fixture.layout.event(1);ObjectNode changed=json(event);
        changed.put("previous_sha256","0".repeat(64));Files.write(event,ContinuityJson.canonical(changed));
        fixture.writer.locked(session->{
            assertThrows(ContractViolationException.class,()->new ContinuityStore(fixture.layout).head());
            return null;
        });
    }
    @Test void coldHeadRejectsSourceIndexChangedBeforeRead() throws Exception {
        WriterFixture fixture=committed("index-corrupt");
        Path index=fixture.layout.sourceIndex(WriterFixture.settled("first",1024,2).sourceKey());
        ObjectNode changed=json(index);changed.put("identity","0".repeat(64));Files.write(index,ContinuityJson.canonical(changed));
        fixture.writer.locked(session->{
            assertThrows(ContractViolationException.class,()->new ContinuityStore(fixture.layout).head());
            return null;
        });
    }
    @Test void coldHeadRejectsSnapshotDivergingFromSameSequenceEvent() throws Exception {
        WriterFixture fixture=committed("snapshot-corrupt");
        ObjectNode changed=json(fixture.layout.snapshot());changed.put("last_settled_cycles",999);
        Files.write(fixture.layout.snapshot(),ContinuityJson.canonical(changed));
        fixture.writer.locked(session->{
            assertThrows(ContractViolationException.class,()->new ContinuityStore(fixture.layout).head());
            return null;
        });
    }
    @Test void coldHeadKeepsMissingIndexAndStaleSnapshotRecovery() throws Exception {
        WriterFixture fixture=new WriterFixture(root.resolve("recover"));
        Request request=WriterFixture.settled("first",1024,2);
        Prepared prepared=fixture.writer.preview(request);
        var authority=new TransitionAuthority(){
            @Override public String revalidate(ContinuityState before,Request actual){return ContinuityJson.digest(actual.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState before,Request actual){return OriginalWindowReducer.reduce(before,actual);}
        };
        ContinuityWriter failing=new ContinuityWriter(fixture.layout,
                List.of(LedgerFiles.read(fixture.source,ContinuityJson.DOCUMENT_MAX_BYTES).pin().reference()),authority,
                Clock.systemUTC(),ContinuityWriter.Extensions.none(),StorageWriteGuardTestSupport.forLayout(fixture.layout),
                (boundary,sequence)->{if(boundary==WriterFaultProbe.Boundary.EVENT_PUBLISHED)throw new IOException("actual event published");});
        assertThrows(CommitUncertainException.class,()->failing.commit(prepared));
        assertTrue(Files.exists(fixture.layout.event(1)));
        assertFalse(Files.exists(fixture.layout.sourceIndex(request.sourceKey())));
        fixture.writer.locked(session->{
            Head interrupted=new ContinuityStore(fixture.layout).head();
            assertEquals(1,interrupted.state().sequence());
            assertTrue(interrupted.snapshotNeedsRecovery());
            assertEquals(1,interrupted.indexRepairs().size());
            assertEquals(fixture.layout.sourceIndex(request.sourceKey()),interrupted.indexRepairs().getFirst().path());
            return null;
        });
        fixture.storage.reconcileStorageOnly();
        Receipt recovered=fixture.writer.commit(prepared);
        assertEquals(Disposition.ALREADY_COMMITTED,recovered.disposition());
        fixture.writer.locked(session->{
            Head actual=new ContinuityStore(fixture.layout).head();
            assertEquals(1,actual.state().sequence());
            assertFalse(actual.snapshotNeedsRecovery());
            assertTrue(actual.indexRepairs().isEmpty());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(2)));
    }
}

