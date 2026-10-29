package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real bounded temporary source files -> registered producer -> writer/archive -> newly opened canonical reader.
 * The fixture proves the shared evidence contract, not M3/Root/Game qualification. */
final class NaturalDomainEvidenceClosureTest {
    @TempDir Path directory;
    private record Fixture(WriterFixture files,List<ExactRef> sources,TransitionAuthority other,
            ContinuityWriter.Extensions extensions,ContinuityWriter writer,DomainBodies.ImportRequest request,
            AtomicInteger calls) {
        ContinuityWriter reopen()throws IOException {
            return new ContinuityWriter(files.layout,sources,other,Clock.systemUTC(),extensions,files.storage);
        }
    }
    private Fixture fixture(DomainBodies.Slot slot,int count)throws IOException {
        var files=new WriterFixture(directory);Path archive=directory.resolve("archive");Files.createDirectory(archive);
        var store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive,files.layout.lock(),4_194_304),files.storage);
        Path body=directory.resolve("domain-original.json");
        Files.writeString(body,"{\"schema\":\"fixture.domain-evidence/v1\",\"pending\":null}");
        List<ExactRef> mutable=new ArrayList<>();
        for(int index=0;index<count;index++) {
            Path original=directory.resolve(String.format(java.util.Locale.ROOT,"material-%03d.json",index));
            Files.write(original,ContinuityJson.canonical(StrictJson.object().put("original_index",index).put("source","temporary-real-producer")));
            mutable.add(LedgerFiles.read(original,65_536).pin().reference());
        }
        List<ExactRef> evidence=List.copyOf(mutable),sources=List.of(LedgerFiles.read(files.source,65_536).pin().reference());
        AtomicInteger calls=new AtomicInteger();
        var registered=new DomainBodies.Registration(slot,"fixture.domain-evidence/v1",65_536,sources,(before,previous,request,raw)->{
            calls.incrementAndGet();var parsed=ContinuityJson.parseObject(raw,65_536);
            StrictJson.require(request.slot()==slot&&StrictJson.text(parsed.get("schema")).equals(request.contractSchema())
                    &&parsed.has("pending")&&parsed.get("pending").isNull()&&request.evidence().equals(evidence),
                    "actual fixture original body/slot/full evidence closure differs");
            for(int index=0;index<evidence.size();index++) {
                var actual=LedgerFiles.exact(evidence.get(index),65_536);
                var data=ContinuityJson.parseObject(actual.bytes(),65_536);
                StrictJson.require(StrictJson.integer(data.get("original_index"),0,127)==index,
                        "actual source material identity/index differs");
                LedgerFiles.verify(actual.pin());
            }
            return ContinuityJson.digest(parsed);
        });
        TransitionAuthority other=new TransitionAuthority(){
            @Override public String revalidate(ContinuityState before,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState before,Request request){return OriginalWindowReducer.reduce(before,request);}
        };
        var extensions=new ContinuityWriter.Extensions(List.of(registered),Optional.of(store),Optional.empty());
        var writer=new ContinuityWriter(files.layout,sources,other,Clock.systemUTC(),extensions,files.storage);
        var request=new DomainBodies.ImportRequest(slot,registered.contractSchema(),LedgerFiles.read(body,65_536).pin().reference(),
                ContinuityJson.canonical(StrictJson.object().put("actual_material_count",count)),evidence,"all-materials-retained");
        return new Fixture(files,sources,other,extensions,writer,request,calls);
    }
    @Test void all128NaturalOriginalsSurviveActualWriterArchiveEventSerdeAndNewWriterHistoricalReplay()throws Exception {
        var f=fixture(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,128);
        var prepared=f.writer().previewImport(f.request());assertEquals(128,prepared.evidence().size());
        var receipt=f.writer().commitImport(prepared);int calls=f.calls().get();
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot()),eventBytes=Files.readAllBytes(f.files().layout.event(1));
        var event=ContinuityJson.parseObject(eventBytes,ContinuityJson.DOCUMENT_MAX_BYTES);
        var serialized=event.get("details").get("source").get("evidence");assertEquals(128,serialized.size());
        for(int index=0;index<128;index++)assertEquals(f.request().evidence().get(index),ExactRef.fromJson(serialized.get(index)));
        f.writer().locked(same->{same.requireCommitted(prepared,receipt);return null;});
        f.reopen().locked(same->{
            var recorded=same.requireHistoricalImport(f.request().slot(),receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()));
            assertEquals(f.request().evidence(),recorded.request().evidence());assertEquals(128,recorded.request().evidence().size());
            assertArrayEquals(f.request().producerInput(),recorded.request().producerInput());
            for(var original:f.request().evidence()) {
                var pin=recorded.currentInputs().stream().filter(value->value.reference().equals(original)).findFirst().orElseThrow();
                assertArrayEquals(Files.readAllBytes(Path.of(original.path())),same.readPinned(pin,65_536));
            }
            same.requireDomainImportContinuation(prepared.predecessor().state().sequence(),prepared.predecessor().digest());
            return null;
        });
        assertEquals(calls,f.calls().get(),"readonly cold replay must not invoke live producer or mint Prepared");
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));
        assertArrayEquals(eventBytes,Files.readAllBytes(f.files().layout.event(1)));assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void natural129AndEveryOtherSlot65StillRejectAndProducerSourcesKeepTheir64Bound()throws Exception {
        var f=fixture(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,128);var request=f.request();
        Path extra=directory.resolve("one-too-many.json");Files.writeString(extra,"{\"original_index\":128}");
        var excessive=new ArrayList<>(request.evidence());excessive.add(LedgerFiles.read(extra,65_536).pin().reference());
        assertEquals(128,DomainBodies.maximumEvidence(request.slot()));
        assertThrows(IllegalArgumentException.class,()->new DomainBodies.ImportRequest(request.slot(),request.contractSchema(),
                request.originalBody(),request.producerInput(),excessive,"over-limit"));
        for(var slot:DomainBodies.Slot.values())if(slot!=DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS) {
            assertEquals(64,DomainBodies.maximumEvidence(slot));
            assertThrows(IllegalArgumentException.class,()->new DomainBodies.ImportRequest(slot,request.contractSchema(),
                    request.originalBody(),request.producerInput(),request.evidence().subList(0,65),"ordinary-over-limit"));
        }
        assertThrows(NullPointerException.class,()->DomainBodies.maximumEvidence(null));
        assertThrows(IllegalArgumentException.class,()->new DomainBodies.Registration(request.slot(),request.contractSchema(),65_536,
                java.util.Collections.nCopies(65,f.sources().getFirst()),(before,previous,actual,raw)->ContinuityJson.digest(StrictJson.object())));
        var body=LedgerFiles.read(Path.of(request.originalBody().path()),65_536).pin();
        var bodyData=new DomainBodies.BodyRef(request.slot(),request.contractSchema(),body.reference(),body.identity(),f.sources()).toJson();
        var tooManySources=bodyData.putArray("producer_sources");
        for(int index=0;index<65;index++)tooManySources.add(f.sources().getFirst().toJson());
        assertThrows(IllegalArgumentException.class,()->DomainBodies.BodyRef.fromJson(bodyData));
        assertThrows(IllegalArgumentException.class,()->new Request("ordinary-test",ContinuityJson.canonical(
                StrictJson.object().put("evidence_id","not-domain").put("source","original")),request.evidence().subList(0,65)));
        assertFalse(Files.exists(f.files().layout.event(1)));
    }
    @Test void ordinary64DomainClosureStillUsesTheSameRealWriterAndHistoricalReader()throws Exception {
        var f=fixture(DomainBodies.Slot.LIFE,64);var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        f.reopen().locked(same->{var recorded=same.requireHistoricalImport(DomainBodies.Slot.LIFE,receipt.head().sequence(),
                ContinuityJson.digest(receipt.head().toJson()));assertEquals(f.request().evidence(),recorded.request().evidence());
            same.requireDomainImportContinuation(0,prepared.predecessor().digest());return null;});
        assertFalse(Files.exists(f.files().layout.event(2)));
    }
    @Test void changed128thMaterialFailsBothColdReadersRatherThanSilentlyTruncatingTheOriginalClosure()throws Exception {
        var f=fixture(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,128);var prepared=f.writer().previewImport(f.request());var receipt=f.writer().commitImport(prepared);
        byte[] snapshot=Files.readAllBytes(f.files().layout.snapshot()),event=Files.readAllBytes(f.files().layout.event(1));
        Files.writeString(Path.of(f.request().evidence().get(127).path()),"{\"changed\":true}");
        f.reopen().locked(same->{
            assertThrows(IOException.class,()->same.requireHistoricalImport(f.request().slot(),receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson())));
            assertThrows(IOException.class,()->same.requireDomainImportContinuation(0,prepared.predecessor().digest()));return null;
        });
        assertArrayEquals(snapshot,Files.readAllBytes(f.files().layout.snapshot()));assertArrayEquals(event,Files.readAllBytes(f.files().layout.event(1)));
        assertFalse(Files.exists(f.files().layout.event(2)));
    }
}
