package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.contracts.*;

/** Real temporary canonical writer, registered domain producer and native original files. No Game qualification. */
final class DomainImportContinuationWriterTest {
    @TempDir Path root;
    private record Fixture(WriterFixture files,ContinuityWriter writer,AtomicInteger producerCalls,Path packet,
            ImmutableArtifactStore artifacts,List<DomainBodies.Registration> registrations){ }
    private static List<ExactRef> sources(WriterFixture f)throws IOException{return List.of(LedgerFiles.read(f.source,65_536).pin().reference());}
    private Fixture fixture(String name)throws IOException{
        return fixture(name,List.of(DomainBodies.Slot.LIFE,DomainBodies.Slot.ACTIVE_RETREAT),false);
    }
    private Fixture fixture(String name,List<DomainBodies.Slot> slots,boolean manyProducers)throws IOException{
        assertTrue(Platform.isWindows());WriterFixture files=new WriterFixture(root.resolve(name));
        Path archive=files.layout.snapshot().resolveSibling("domain-archive");Files.createDirectory(archive);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive,files.layout.lock(),4_194_304), StorageWriteGuardTestSupport.forOriginalLock(files.layout.lock()));
        Path packet=files.layout.snapshot().resolveSibling("original-packet.bin");Files.write(packet,new byte[]{0,7,1,92});
        AtomicInteger calls=new AtomicInteger();List<DomainBodies.Registration> registrations=new ArrayList<>();
        List<ExactRef> producerSources=sources(files);
        if(manyProducers){
            List<ExactRef> actual=new ArrayList<>();
            for(int index=0;index<32;index++){
                Path implementation=files.layout.snapshot().resolveSibling("actual-implementation-"+index+"-"+"x".repeat(90)+".class");
                Files.write(implementation,new byte[]{(byte)index});actual.add(LedgerFiles.read(implementation,65_536).pin().reference());
            }
            producerSources=List.copyOf(actual);
        }
        for(DomainBodies.Slot slot:slots){
            registrations.add(new DomainBodies.Registration(slot,"fixture.domain-continuation/v1",65_536,producerSources,(head,previous,request,raw)->{
                calls.incrementAndGet();ObjectNode decoded=ContinuityJson.parseObject(raw,65_536);
                StrictJson.require(StrictJson.text(decoded.get("slot")).equals(slot.name())
                        &&StrictJson.integer(decoded.get("ordinal"),1,100)==StrictJson.integer(WriterContracts.object(request.producerInput()).get("ordinal"),1,100),
                        "original fixture producer and complete body differ");
                StrictJson.require(request.evidence().equals(List.of(LedgerFiles.read(packet,65_536).pin().reference())),"actual original packet differs");
                return ContinuityJson.digest(decoded);
            }));
        }
        TransitionAuthority other=new TransitionAuthority(){
            @Override public String revalidate(ContinuityState head,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState head,Request request){
                ObjectNode next=head.toJson();
                if("fixture.read".equals(request.kind()))next.putNull("fixture_read_then_erased");
                else if("fixture.read-erased".equals(request.kind()))next.remove("fixture_read_then_erased");
                else return OriginalWindowReducer.reduce(head,request);
                return ContinuityState.fromJson(next,head.machineId());
            }
        };
        var writer=new ContinuityWriter(files.layout, sources(files), other, Clock.systemUTC(), new ContinuityWriter.Extensions(registrations,Optional.of(artifacts),Optional.empty()), StorageWriteGuardTestSupport.forLayout(files.layout));
        return new Fixture(files,writer,calls,packet,artifacts,List.copyOf(registrations));
    }
    private Receipt importBody(Fixture f,DomainBodies.Slot slot,int ordinal)throws IOException{
        Path original=f.files().layout.snapshot().resolveSibling("original-"+slot.name()+"-"+ordinal+".json");
        // Deliberate original whitespace is retained; the reader must compare actual original bytes.
        Files.writeString(original,"{ \"schema\" : \"fixture.domain-continuation/v1\", \"slot\" : \""+slot.name()+"\", \"ordinal\" : "+ordinal+", \"pending\" : null }\n");
        ObjectNode input=StrictJson.object();input.put("ordinal",ordinal);
        var request=new DomainBodies.ImportRequest(slot,"fixture.domain-continuation/v1",LedgerFiles.read(original,65_536).pin().reference(),
                ContinuityJson.canonical(input),List.of(LedgerFiles.read(f.packet(),65_536).pin().reference()),"source-"+slot.name()+"-"+ordinal);
        return f.writer().commitImport(f.writer().previewImport(request));
    }
    private static Request other(String kind,String evidence){
        ObjectNode details=StrictJson.object();details.put("evidence_id",evidence);details.put("source","actual-temporary-source");
        return new Request(kind,ContinuityJson.canonical(details),List.of());
    }
    @Test void zeroDistanceStillVerifiesTheActualOriginAndNeverWrites()throws Exception{
        var f=fixture("zero");Head original=f.writer().locked(ContinuityStorePort.Session::head);
        byte[] bytes=Files.readAllBytes(f.files().layout.snapshot());
        f.writer().locked(session->{
            session.requireDomainImportContinuation(original.state().sequence(),original.digest());
            assertThrows(IOException.class,()->session.requireDomainImportContinuation(0,"0".repeat(64)));
            assertThrows(IOException.class,()->session.requireDomainImportContinuation(-1,original.digest()));
            assertThrows(IOException.class,()->session.requireDomainImportContinuation(1,original.digest()));
            assertThrows(IOException.class,()->session.requireDomainImportContinuation(0,null));
            return null;
        });
        assertArrayEquals(bytes,Files.readAllBytes(f.files().layout.snapshot()));assertEquals(0,f.producerCalls().get());
        assertFalse(Files.exists(f.files().layout.event(1)));
    }
    @Test void actualImportsAcrossSlotsAndLegitimateSameSlotProgressRemainReadOnlyAndDoNotReplayProducers()throws Exception{
        var f=fixture("imports");Head original=f.writer().locked(ContinuityStorePort.Session::head);
        importBody(f,DomainBodies.Slot.LIFE,1);importBody(f,DomainBodies.Slot.ACTIVE_RETREAT,2);importBody(f,DomainBodies.Slot.LIFE,3);
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());int calls=f.producerCalls().get();
        f.writer().locked(session->{session.requireDomainImportContinuation(0,original.digest());return null;});
        assertEquals(calls,f.producerCalls().get(),"a historical lineage proof cannot invoke current live producer authority");
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));assertFalse(Files.exists(f.files().layout.event(4)));
        var state=f.writer().locked(ContinuityStorePort.Session::head).state();
        assertEquals(3,state.sequence());assertArrayEquals(ContinuityJson.canonical(WriterFixture.state().get("pending_cycle")),ContinuityJson.canonical(state.toJson().get("pending_cycle")));
        assertArrayEquals(ContinuityJson.canonical(WriterFixture.state().get("NEXT")),ContinuityJson.canonical(state.toJson().get("NEXT")));
    }
    @Test void anInterveningReadCannotBeHiddenByRestoringTheSameFinalFieldValues()throws Exception{
        var f=fixture("read-hidden");Head original=f.writer().locked(ContinuityStorePort.Session::head);
        f.writer().commit(f.writer().preview(other("fixture.read","read")));
        f.writer().commit(f.writer().preview(other("fixture.read-erased","erased")));
        importBody(f,DomainBodies.Slot.LIFE,1);
        assertFalse(f.writer().locked(ContinuityStorePort.Session::head).state().toJson().has("fixture_read_then_erased"));
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());
        f.writer().locked(session->{assertThrows(IOException.class,()->session.requireDomainImportContinuation(0,original.digest()));return null;});
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));assertFalse(Files.exists(f.files().layout.event(4)));
    }
    @Test void aCanonicalLookingDomainEventWithAnUnownedFieldMutationIsRejectedByTheRealPureReducer()throws Exception{
        var f=fixture("wrong-reducer");Head original=f.writer().locked(ContinuityStorePort.Session::head);importBody(f,DomainBodies.Slot.LIFE,1);
        ObjectNode event=ContinuityJson.parseObject(Files.readAllBytes(f.files().layout.event(1)),ContinuityJson.DOCUMENT_MAX_BYTES);
        ObjectNode after=(ObjectNode)event.get("after");after.putNull("fixture_illegal_import_field");
        // Corrupt only temporary test persistence. The finite chain still parses; kind/shape alone must not qualify it.
        Files.write(f.files().layout.event(1),ContinuityJson.canonical(event));Files.write(f.files().layout.snapshot(),ContinuityJson.canonical(after));
        f.writer().locked(session->{assertThrows(IOException.class,()->session.requireDomainImportContinuation(0,original.digest()));return null;});
        assertTrue(f.writer().locked(ContinuityStorePort.Session::head).state().toJson().has("fixture_illegal_import_field"));
        assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void missingIndexIsNotRepairedButChangedOriginalBytesCannotQualifyContinuation()throws Exception{
        var f=fixture("missing-index");Head original=f.writer().locked(ContinuityStorePort.Session::head);importBody(f,DomainBodies.Slot.LIFE,1);
        ObjectNode event=ContinuityJson.parseObject(Files.readAllBytes(f.files().layout.event(1)),ContinuityJson.DOCUMENT_MAX_BYTES);
        Request request=new Request(DomainBodies.IMPORT_KIND,ContinuityJson.canonical((ObjectNode)event.get("details")),List.of());
        Path index=f.files().layout.sourceIndex(request.sourceKey());Files.delete(index);
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());
        f.writer().locked(session->{session.requireDomainImportContinuation(0,original.digest());return null;});assertFalse(Files.exists(index));
        Path originalBody=Path.of(ExactRef.fromJson(event.path("details").path("source").path("original_body")).path());
        Files.writeString(originalBody,"{\"changed\":true}");
        f.writer().locked(session->{assertThrows(IOException.class,()->session.requireDomainImportContinuation(0,original.digest()));return null;});
        assertFalse(Files.exists(index));assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));
    }
    @Test void changedImplementationMetadataPreservesHistoricalBodiesWithoutReplayingProducers()throws Exception{
        var f=fixture("source-closure");Head original=f.writer().locked(ContinuityStorePort.Session::head);
        var committed=importBody(f,DomainBodies.Slot.LIFE,1);
        var retained=DomainBodies.reference(committed.head(),DomainBodies.Slot.LIFE).orElseThrow();
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());int calls=f.producerCalls().get();
        Path another=f.files().layout.snapshot().resolveSibling("different-producer.txt");Files.writeString(another,"different actual producer");
        var different=new DomainBodies.Registration(DomainBodies.Slot.LIFE,"fixture.domain-continuation/v1",65_536,
                List.of(LedgerFiles.read(another,65_536).pin().reference()),(head,previous,request,raw)->{throw new AssertionError("readonly history cannot call a new live authority");});
        Files.delete(another); // Implementation metadata is DATA, not a live body/evidence original.
        TransitionAuthority unused=new TransitionAuthority(){
            @Override public String revalidate(ContinuityState state,Request request){throw new AssertionError("no ordinary authority calls");}
            @Override public ContinuityState reduce(ContinuityState state,Request request){throw new AssertionError("no ordinary replay");}
        };
        var reader=new ContinuityWriter(f.files().layout, sources(f.files()), unused, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(different),Optional.of(f.artifacts()),Optional.empty()), StorageWriteGuardTestSupport.forLayout(f.files().layout));
        reader.locked(session->{
            session.requireDomainImportContinuation(0,original.digest());
            var available=assertInstanceOf(DomainBodies.Available.class,session.readDomain(DomainBodies.Slot.LIFE));
            assertEquals(retained,available.reference());
            assertEquals(1,StrictJson.integer(ContinuityJson.parseObject(available.canonicalBody(),65_536).get("ordinal"),1,100));
            var historical=session.requireHistoricalHead(committed.head().sequence(),ContinuityJson.digest(committed.head().toJson()));
            assertEquals(retained,DomainBodies.reference(historical.state(),DomainBodies.Slot.LIFE).orElseThrow());
            var recorded=session.requireHistoricalImport(DomainBodies.Slot.LIFE,committed.head().sequence(),ContinuityJson.digest(committed.head().toJson()));
            assertEquals(retained,recorded.body());
            assertEquals(List.of(LedgerFiles.read(f.packet(),65_536).pin().reference()),recorded.request().evidence());
            return null;
        });
        assertEquals(calls,f.producerCalls().get());
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));
        var wrongSchema=new DomainBodies.Registration(DomainBodies.Slot.LIFE,"fixture.domain-continuation/v2",65_536,
                different.producerSources(),different.verifier());
        var incompatible=new ContinuityWriter(f.files().layout,sources(f.files()),unused,Clock.systemUTC(),
                new ContinuityWriter.Extensions(List.of(wrongSchema),Optional.of(f.artifacts()),Optional.empty()),StorageWriteGuardTestSupport.forLayout(f.files().layout));
        incompatible.locked(session->{
            assertThrows(IOException.class,()->session.requireDomainImportContinuation(0,original.digest()));
            assertInstanceOf(DomainBodies.Unavailable.class,session.readDomain(DomainBodies.Slot.LIFE));return null;
        });
        assertFalse(Files.exists(f.files().layout.event(2)));
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));
    }
    @Test void aggregateHeadAndEventRoundTripWithoutChangingRequestBoundsOrReplayingImports()throws Exception{
        List<DomainBodies.Slot> slots=Arrays.asList(DomainBodies.Slot.values()).subList(0,9);
        var f=fixture("large-ledger",slots,true);Head origin=f.writer().locked(ContinuityStorePort.Session::head);
        for(int index=0;index<slots.size();index++){
            importBody(f,slots.get(index),index+1);
        }
        Head head=f.writer().locked(ContinuityStorePort.Session::head);
        assertTrue(head.state().canonicalBytes().length>ContinuityJson.DOCUMENT_MAX_BYTES);
        assertTrue(Files.size(f.files().layout.event(9))>ContinuityJson.DOCUMENT_MAX_BYTES);
        assertTrue(Files.size(f.files().layout.event(9))<=ContinuityJson.LEDGER_MAX_BYTES);
        int calls=f.producerCalls().get();String digest=head.digest();
        f.writer().locked(same->{
            same.requireDomainImportContinuation(origin.state().sequence(),origin.digest());
            assertEquals(digest,same.requireHistoricalHead(head.state().sequence(),digest).digest());
            for(DomainBodies.Slot slot:slots)assertInstanceOf(DomainBodies.Available.class,same.readDomain(slot));
            return null;
        });
        assertEquals(calls,f.producerCalls().get(),"history reads retain actual bodies without live producer replay");
        byte[] actualEvent=Files.readAllBytes(f.files().layout.event(9));
        assertThrows(ContractViolationException.class,()->ContinuityJson.parseObject(actualEvent,ContinuityJson.DOCUMENT_MAX_BYTES));
        ObjectNode event=ContinuityJson.parseObject(actualEvent,ContinuityJson.LEDGER_MAX_BYTES);
        var next=WriterFixture.settled("after-large-ledger",1024,2);
        Receipt result=f.writer().commit(f.writer().preview(next));
        assertEquals(10,result.head().sequence());assertFalse(result.recoveredCommittedReceipt());
        for(DomainBodies.Slot slot:slots)assertEquals(DomainBodies.reference(head.state(),slot),DomainBodies.reference(result.head(),slot));
        assertEquals(Disposition.ALREADY_COMMITTED,f.writer().commit(f.writer().preview(next)).disposition());
    }
    @Test void finiteLedgerProfileDoesNotRaiseGenericRequestsOrIntegerBounds()throws Exception{
        ObjectNode ordinary=StrictJson.object();ordinary.put("large","a".repeat(ContinuityJson.DOCUMENT_MAX_BYTES));
        assertThrows(ContractViolationException.class,()->ContinuityJson.canonical(ordinary));
        ObjectNode identity=StrictJson.object();identity.put("evidence_id","oversized");identity.set("source",ordinary);
        assertThrows(ContractViolationException.class,()->new Request("fixture.request",ContinuityJson.canonical(identity,ContinuityJson.LEDGER_MAX_BYTES),List.of()));
        ObjectNode state=WriterFixture.state();state.put("aggregate","a".repeat(ContinuityJson.LEDGER_MAX_BYTES));
        assertThrows(ContractViolationException.class,()->ContinuityState.fromJson(state,WriterFixture.MACHINE));
        ObjectNode largeInteger=WriterFixture.state();largeInteger.put("identity_number",new java.math.BigInteger("9007199254740992"));
        assertThrows(ContractViolationException.class,()->ContinuityState.fromJson(largeInteger,WriterFixture.MACHINE));
        ObjectNode old=WriterFixture.state();byte[] explicit=ContinuityJson.canonical(old,ContinuityJson.DOCUMENT_MAX_BYTES);
        assertArrayEquals(explicit,ContinuityJson.canonical(old));
        assertEquals(ContinuityJson.digest(old),ContinuityJson.digest(ContinuityJson.parseObject(explicit,ContinuityJson.DOCUMENT_MAX_BYTES)));
    }

}
