package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.contracts.*;

/** Registered real temporary domain producer -> original guarded writer -> typed committed/historical readers. */
final class DomainImportCommittedHistoryTest {
    @TempDir Path directory;
    private record Fixture(WriterFixture files,ContinuityWriter writer,DomainBodies.ImportRequest request,AtomicInteger calls){ }
    private Fixture fixture()throws IOException {
        var files=new WriterFixture(directory);Path archive=directory.resolve("archive");Files.createDirectory(archive);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive,files.layout.lock(),4_194_304),files.storage);
        Path body=directory.resolve("original-life.json");Files.writeString(body,"{ \"schema\" : \"fixture.life/v1\", \"pending\" : null }\n");
        Path evidence=directory.resolve("actual-source-packet");Files.write(evidence,new byte[]{1,4,9});
        List<ExactRef> sources=List.of(LedgerFiles.read(files.source,65_536).pin().reference());AtomicInteger calls=new AtomicInteger();
        Path producer=directory.resolve("producer.class");Files.writeString(producer,"original business implementation");
        var producerSources=List.of(LedgerFiles.read(producer,65_536).pin().reference());
        var registration=new DomainBodies.Registration(DomainBodies.Slot.LIFE,"fixture.life/v1",65_536,producerSources,(before,previous,request,raw)->{
            calls.incrementAndGet();var parsed=ContinuityJson.parseObject(raw,65_536);
            StrictJson.require(StrictJson.text(parsed.get("schema")).equals(request.contractSchema())&&parsed.has("pending")&&parsed.get("pending").isNull(),"real fixture domain producer shape");
            StrictJson.require(request.evidence().equals(List.of(LedgerFiles.read(evidence,65_536).pin().reference())),"original source packet differs");
            return ContinuityJson.digest(parsed);
        });
        TransitionAuthority other=new TransitionAuthority(){
            @Override public String revalidate(ContinuityState before,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState before,Request request){return OriginalWindowReducer.reduce(before,request);}
        };
        var writer=new ContinuityWriter(files.layout,sources,other,Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(registration),Optional.of(artifacts),Optional.empty()),files.storage);
        var request=new DomainBodies.ImportRequest(DomainBodies.Slot.LIFE,"fixture.life/v1",LedgerFiles.read(body,65_536).pin().reference(),
                ContinuityJson.canonical(StrictJson.object().put("actual_input",1)),List.of(LedgerFiles.read(evidence,65_536).pin().reference()),"first-life");
        return new Fixture(files,writer,request,calls);
    }
    @Test void businessProducerRebuildDoesNotAuditHistoricalClassButActualEvidenceStillMatters()throws Exception {
        var f=fixture();Path producer=directory.resolve("producer.class");
        var historical=LedgerFiles.read(producer,65_536).pin().reference();
        Files.writeString(producer,"updated business implementation");
        f.writer().locked(same->{
            Head original=same.head();var prepared=same.previewImport(f.request());
            assertSame(original,prepared.predecessor(),"domain preview reuses the actual prewrite head");
            assertEquals(1,prepared.sources().size(),"only the writer source lane is physically pinned");
            var receipt=same.commitImport(prepared);same.requireCommitted(prepared,receipt);
            assertEquals(List.of(historical),DomainBodies.reference(receipt.head(),DomainBodies.Slot.LIFE).orElseThrow().producerSources());
            return null;
        });
        assertFalse(Files.exists(f.files().layout.event(2)));
        Files.write(Path.of(f.request().evidence().getFirst().path()),new byte[]{8,8,8});
        assertThrows(IOException.class,()->f.writer().previewImport(f.request()),"changed actual input remains rejected");
    }

    @Test void actualImportReceiptAndHistoricalHeadRetainFullPinsWithoutCallingProducerAgainOrWriting()throws Exception {
        var f=fixture();var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());int calls=f.calls().get();
        f.writer().locked(same->{
            same.requireCommitted(prepared,receipt);
            var historical=same.requireHistoricalHead(receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()));
            assertFalse(historical.documents().isEmpty());assertEquals(receipt.head().toJson(),historical.state().toJson());
            var body=DomainBodies.reference(historical.state(),DomainBodies.Slot.LIFE).orElseThrow();
            var pin=historical.documents().stream().filter(value->value.reference().equals(body.payload())).findFirst().orElseThrow();
            assertEquals(body.identity(),pin.identity());assertTrue(ContinuityJson.parseObject(same.readPinned(pin,65_536),65_536).get("pending").isNull());
            var original=same.requireHistoricalHead(prepared.predecessor().state().sequence(),prepared.predecessor().digest());
            assertEquals(prepared.predecessor().state().toJson(),original.state().toJson());assertFalse(original.documents().isEmpty());
            assertThrows(IllegalArgumentException.class,()->same.requireHistoricalHead(receipt.head().sequence(),"0".repeat(64)));return null;
        });
        assertEquals(calls,f.calls().get(),"historical verification must not re-run current live producer authority");
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void exactPreparedImportBodyInputProofAndReceiptAreRequiredRatherThanGenericShape()throws Exception {
        var f=fixture();var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        var changedInput=new DomainBodies.ImportRequest(f.request().slot(),f.request().contractSchema(),f.request().originalBody(),
                ContinuityJson.canonical(StrictJson.object().put("actual_input",2)),f.request().evidence(),f.request().evidenceId());
        var detached=new DomainBodies.PreparedImport(prepared.predecessor(),changedInput,prepared.originalBody(),prepared.sources(),prepared.evidence(),prepared.preconditionDigest());
        var wrongProof=new DomainBodies.PreparedImport(prepared.predecessor(),prepared.request(),prepared.originalBody(),prepared.sources(),prepared.evidence(),"0".repeat(64));
        f.writer().locked(same->{
            assertThrows(IOException.class,()->same.requireCommitted(detached,receipt));
            assertThrows(IllegalArgumentException.class,()->same.requireCommitted(wrongProof,receipt));
            var noChange=new Receipt(Disposition.NO_CHANGE,receipt.head(),receipt.eventIdentity(),0,false);
            assertThrows(IllegalArgumentException.class,()->same.requireCommitted(prepared,noChange));
            same.requireCommitted(prepared,receipt);return null;
        });
    }
    @Test void changedNativeOriginalOrSourceCannotBeAcceptedThroughAnAlreadyCommittedReceipt()throws Exception {
        var f=fixture();var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        Files.writeString(Path.of(f.request().originalBody().path()),"{\"different\":true}");
        f.writer().locked(same->{assertThrows(IOException.class,()->same.requireCommitted(prepared,receipt));return null;});
        assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void actualRecordedImportReadsDurableIdentityAfterExternalCasInputIsGoneWithoutFabricatingWarmPins()throws Exception {
        var f=fixture();var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        int calls=f.calls().get();byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());
        // Test-owned input is no longer a live CAS source. The immutable recorded body remains genuine.
        Files.delete(Path.of(f.request().originalBody().path()));
        f.writer().locked(same->{
            var recorded=same.requireHistoricalImport(DomainBodies.Slot.LIFE,receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()));
            assertEquals(Disposition.ALREADY_COMMITTED,recorded.receipt().disposition());
            assertEquals(f.request().originalBody(),recorded.request().originalBody());
            assertArrayEquals(f.request().producerInput(),recorded.request().producerInput());assertEquals(f.request().evidence(),recorded.request().evidence());
            assertEquals(prepared.predecessor().digest(),recorded.predecessor().digest());
            assertEquals(DomainBodies.reference(receipt.head(),DomainBodies.Slot.LIFE).orElseThrow(),recorded.body());
            assertTrue(recorded.currentInputs().stream().anyMatch(pin->pin.reference().equals(recorded.body().payload())&&pin.identity().equals(recorded.body().identity())));
            assertTrue(recorded.currentInputs().stream().anyMatch(pin->pin.reference().equals(recorded.canonicalEvent())));
            assertThrows(IOException.class,()->same.requireCommitted(prepared,receipt),"historical DATA does not manufacture a now-missing warm CAS input");return null;
        });
        assertEquals(calls,f.calls().get());assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void recordedImportRequiresExactEventSlotDigestAndOriginalEvidenceContent()throws Exception {
        var f=fixture();var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        f.writer().locked(same->{
            assertThrows(IOException.class,()->same.requireHistoricalImport(DomainBodies.Slot.CROWN,receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson())));
            assertThrows(IllegalArgumentException.class,()->same.requireHistoricalImport(DomainBodies.Slot.LIFE,receipt.head().sequence(),"0".repeat(64)));
            assertThrows(IllegalArgumentException.class,()->same.requireHistoricalImport(DomainBodies.Slot.LIFE,0,ContinuityJson.digest(receipt.head().toJson())));return null;
        });
        Files.write(Path.of(f.request().evidence().getFirst().path()),new byte[]{4,4,4});
        f.writer().locked(same->{assertThrows(IOException.class,()->same.requireHistoricalImport(DomainBodies.Slot.LIFE,receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson())));return null;});
        assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void sharedPinSerdePreservesNativeIdentityAndEqualNativeBytesDoNotPretendToProveReceiveIndependence()throws Exception {
        var f=fixture();Pin pin=LedgerFiles.read(f.files().source,65_536).pin();assertEquals(pin,Pin.fromJson(pin.toJson()));
        var malformed=pin.toJson();((com.fasterxml.jackson.databind.node.ObjectNode)malformed.get("identity")).put("bytes",1.0);
        assertThrows(IllegalArgumentException.class,()->Pin.fromJson(malformed));
        ExactRef packet=f.request().evidence().getFirst();ExactRef oldDriver=pin.reference();ExactRef newDriver=f.request().originalBody();
        var originals=new EpisodeWindow.OperatorOriginals(packet,packet,packet,packet,oldDriver,newDriver,packet,packet);
        assertEquals(originals,EpisodeWindow.OperatorOriginals.fromJson(originals.toJson()));
        assertThrows(IllegalArgumentException.class,()->new EpisodeWindow.OperatorOriginals(packet,packet,packet,packet,oldDriver,oldDriver,packet,packet));
        // This is only typed DATA. No actual receive timestamp/custody, Root proof or submission permit is constructed.
    }
    @Test void actualConfiguredSourcesAndCanonicalTransitionReadRetainOriginalPinsWithoutReconstructingPrepared()throws Exception {
        var f=fixture();var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot());int calls=f.calls().get();
        ContinuityStorePort.Session[] escaped=new ContinuityStorePort.Session[1];
        f.writer().locked(same->{
            escaped[0]=same;var sources=same.captureSources();assertEquals(List.of(LedgerFiles.read(f.files().source,65_536).pin()),sources);
            var pin=same.head().documents().stream().filter(value->Path.of(value.reference().path()).toAbsolutePath().normalize().equals(f.files().layout.event(receipt.head().sequence()))).findFirst().orElseThrow();
            var actual=same.readHistoricalTransition(pin);assertEquals(DomainBodies.IMPORT_KIND,actual.kind());
            assertEquals(receipt.head().sequence(),actual.sequence());assertEquals(receipt.eventIdentity(),actual.eventIdentity());assertEquals(pin,actual.eventPin());
            assertEquals(prepared.predecessor().state().toJson(),actual.before().toJson());assertEquals(receipt.head().toJson(),actual.after().toJson());
            assertEquals(DomainBodies.IMPORT_KIND,ContinuityJson.parseObject(Files.readAllBytes(f.files().layout.event(actual.sequence())),65_536).get("kind").textValue());
            byte[] detached=actual.details();detached[0]='[';assertEquals((byte)'{',actual.details()[0]);
            assertEquals(actual.eventIdentity(),same.readHistoricalTransition(pin).eventIdentity());
            return null;
        });
        assertThrows(IllegalArgumentException.class,()->escaped[0].captureSources());
        assertEquals(calls,f.calls().get());assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void historicalTransitionRejectsNonEventAndForeignNativeIdentityAndSourceCaptureRejectsChangedConfiguredFile()throws Exception {
        var f=fixture();var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        f.writer().locked(same->{
            var source=same.captureSources().getFirst();assertThrows(IOException.class,()->same.readHistoricalTransition(source));
            var event=same.head().documents().stream().filter(value->Path.of(value.reference().path()).toAbsolutePath().normalize().equals(f.files().layout.event(receipt.head().sequence()))).findFirst().orElseThrow();
            var identity=event.identity();var foreign=new FileIdentity(identity.volumeSerialDecimal(),identity.fileIdDecimal().equals("0")?"1":"0",identity.creationFiletimeDecimal(),identity.modifiedInstant(),identity.bytes());
            assertThrows(IOException.class,()->same.readHistoricalTransition(new Pin(event.reference(),foreign)));
            return null;
        });
        Files.writeString(f.files().source,"changed actual configured source");
        f.writer().locked(same->{assertThrows(IOException.class,same::captureSources);return null;});
        assertFalse(Files.exists(f.files().layout.event(2)));
    }
}
