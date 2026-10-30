package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;

final class DomainReadSessionReuseTest {
    @TempDir Path root;
    private record Fixture(WriterFixture files,ContinuityWriter writer,AtomicInteger calls) { }
    private Fixture fixture(String name)throws IOException { return fixture(name,WriterFaultProbe.NONE); }
    private Fixture fixture(String name,WriterFaultProbe faults)throws IOException {
        var files=new WriterFixture(root.resolve(name));
        Path archive=files.layout.snapshot().resolveSibling("domain-artifacts");Files.createDirectory(archive);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive,files.layout.lock(),4_194_304),StorageWriteGuardTestSupport.forOriginalLock(files.layout.lock()));
        List<ExactRef> sources=List.of(LedgerFiles.read(files.source,65_536).pin().reference());
        var calls=new AtomicInteger();
        var registrations=List.of(DomainBodies.Slot.OPENING_GATE,DomainBodies.Slot.FEAST,DomainBodies.Slot.OPTIONAL_CADENCE).stream().map(slot->
                new DomainBodies.Registration(slot,"fixture.domain-read/v1",65_536,sources,(head,previous,request,raw)->{
                    calls.incrementAndGet();return LedgerFiles.sha(raw);
                })).toList();
        var unused=new TransitionAuthority(){
            public String revalidate(ContinuityState state,Request request){throw new AssertionError("domain read cannot call ordinary authority");}
            public ContinuityState reduce(ContinuityState state,Request request){throw new AssertionError("domain read cannot replay ordinary authority");}
        };
        var writer=new ContinuityWriter(files.layout,sources,unused,Clock.systemUTC(),new ContinuityWriter.Extensions(registrations,Optional.of(artifacts),Optional.empty()),StorageWriteGuardTestSupport.forLayout(files.layout),faults);
        return new Fixture(files,writer,calls);
    }
    private DomainBodies.ImportRequest request(Fixture f,int ordinal)throws IOException {
        var row=org.xar.ck3.control.contracts.StrictJson.object();row.put("schema","fixture.domain-read/v1");row.put("ordinal",ordinal);
        byte[] raw=ContinuityJson.canonical(row);Path body=f.files().layout.snapshot().resolveSibling("original-"+ordinal+".json");Files.write(body,raw);
        return new DomainBodies.ImportRequest(DomainBodies.Slot.OPENING_GATE,"fixture.domain-read/v1",LedgerFiles.read(body,65_536).pin().reference(),
                raw,List.of(),"actual-"+ordinal);
    }
    private static void unavailable(DomainBodies.Read read,DomainBodies.Reason reason){
        assertEquals(reason,assertInstanceOf(DomainBodies.Unavailable.class,read).reason());
    }
    @Test void sameSessionReadsRetainBodiesAndSeeTheNextActualImport()throws Exception {
        var f=fixture("same-session");var first=request(f,1);var second=request(f,2);
        f.writer().commitImport(f.writer().previewImport(first));
        f.writer().locked(same->{
            var one=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.OPENING_GATE));
            unavailable(same.readDomain(DomainBodies.Slot.FEAST),DomainBodies.Reason.UNIMPORTED);
            unavailable(same.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE),DomainBodies.Reason.UNIMPORTED);
            unavailable(same.readDomain(DomainBodies.Slot.LIFE),DomainBodies.Reason.SLOT_UNREGISTERED);
            same.commitImport(same.previewImport(second));
            var two=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.OPENING_GATE));
            assertNotEquals(one.reference(),two.reference());assertArrayEquals(second.producerInput(),two.canonicalBody());
            assertEquals(2,same.head().state().sequence());
            int calls=f.calls().get();byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());
            assertArrayEquals(two.canonicalBody(),assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.OPENING_GATE)).canonicalBody());
            assertEquals(calls,f.calls().get());assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));
            Files.writeString(Path.of(two.reference().payload().path()),"{\"changed\":true}");
            unavailable(same.readDomain(DomainBodies.Slot.OPENING_GATE),DomainBodies.Reason.BODY_IDENTITY_CHANGED);
            return null;
        });
        assertFalse(Files.exists(f.files().layout.event(3)));
    }
    @Test void repeatedDomainReadsDoNotReopenTheCapturedLedgerSnapshot()throws Exception {
        var f=fixture("no-reopen");var request=request(f,1);
        f.writer().commitImport(f.writer().previewImport(request));
        f.writer().locked(same->{
            var first=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.OPENING_GATE));
            Path snapshot=f.files().layout.snapshot();Path moved=snapshot.resolveSibling("held-snapshot.json");
            Files.move(snapshot,moved);
            try {
                var repeated=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.OPENING_GATE));
                assertEquals(first.head(),repeated.head());assertArrayEquals(first.canonicalBody(),repeated.canonicalBody());
                unavailable(same.readDomain(DomainBodies.Slot.FEAST),DomainBodies.Reason.UNIMPORTED);
                unavailable(same.readDomain(DomainBodies.Slot.LIFE),DomainBodies.Reason.SLOT_UNREGISTERED);
            } finally { Files.move(moved,snapshot); }
            return null;
        });
    }
    @Test void aNewSessionReadsTheNextActualCommitAndCannotReuseTheOldView()throws Exception {
        var f=fixture("next-session");var first=request(f,1);var second=request(f,2);
        f.writer().commitImport(f.writer().previewImport(first));
        var before=assertInstanceOf(DomainBodies.Available.class,f.writer().read(DomainBodies.Slot.OPENING_GATE));
        f.writer().commitImport(f.writer().previewImport(second));
        var after=assertInstanceOf(DomainBodies.Available.class,f.writer().read(DomainBodies.Slot.OPENING_GATE));
        assertNotEquals(before.head(),after.head());assertNotEquals(before.reference(),after.reference());
        assertArrayEquals(second.producerInput(),after.canonicalBody());
        Path snapshot=f.files().layout.snapshot();Path moved=snapshot.resolveSibling("missing-snapshot.json");
        Files.move(snapshot,moved);
        try { assertThrows(IOException.class,()->f.writer().read(DomainBodies.Slot.OPENING_GATE)); }
        finally { Files.move(moved,snapshot); }
        assertInstanceOf(DomainBodies.Available.class,f.writer().read(DomainBodies.Slot.OPENING_GATE));
    }
    @Test void failedImportAndDuplicateRecoveryInvalidateTheSameSessionDomainView()throws Exception {
        var failures=new AtomicInteger();
        var f=fixture("failed-import",(boundary,sequence)->{
            if(boundary==WriterFaultProbe.Boundary.EVENT_PUBLISHED&&failures.getAndIncrement()==0)
                throw new IOException("actual event durable before snapshot/index");
        });
        var request=request(f,1);
        f.writer().locked(same->{
            unavailable(same.readDomain(DomainBodies.Slot.OPENING_GATE),DomainBodies.Reason.UNIMPORTED);
            var prepared=same.previewImport(request);
            assertThrows(CommitUncertainException.class,()->same.commitImport(prepared));
            unavailable(same.readDomain(DomainBodies.Slot.OPENING_GATE),DomainBodies.Reason.SOURCE_UNAVAILABLE);
            f.files().storage.reconcileStorageOnly();
            var recovered=same.commitImport(prepared);
            assertEquals(Disposition.ALREADY_COMMITTED,recovered.disposition());
            var actual=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.OPENING_GATE));
            assertArrayEquals(request.producerInput(),actual.canonicalBody());
            assertEquals(1,same.head().state().sequence());assertFalse(Files.exists(f.files().layout.event(2)));
            assertTrue(ContinuityJson.same(WriterFixture.state().get("pending_cycle"),same.head().state().toJson().get("pending_cycle")));
            return null;
        });
    }
    @Test void escapedDomainViewIsRejectedEvenWhileANewSessionHoldsTheSameLock()throws Exception {
        var f=fixture("escaped-domain");
        var escaped=new java.util.concurrent.atomic.AtomicReference<ContinuityStorePort.Session>();
        f.writer().locked(same->{
            unavailable(same.readDomain(DomainBodies.Slot.OPENING_GATE),DomainBodies.Reason.UNIMPORTED);
            escaped.set(same);return null;
        });
        f.writer().locked(current->{
            unavailable(current.readDomain(DomainBodies.Slot.OPENING_GATE),DomainBodies.Reason.UNIMPORTED);
            assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,
                    ()->escaped.get().readDomain(DomainBodies.Slot.OPENING_GATE));
            return null;
        });
    }

}
