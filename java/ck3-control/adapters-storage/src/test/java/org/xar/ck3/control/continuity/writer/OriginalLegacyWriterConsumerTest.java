package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.contracts.*;

/** Shared closed reducer/cold-reader software integration. Fixture DATA is never a physical resume proof. */
final class OriginalLegacyWriterConsumerTest {
    @TempDir Path temporary;
    private record Fixture(WriterFixture files,Layout layout,ContinuityWriter writer,ExactRef original) { }
    private Fixture fixture(String name)throws IOException {
        assertTrue(Platform.isWindows());WriterFixture files=new WriterFixture(temporary.resolve(name));
        ObjectNode initial=WriterFixture.state();initial.putNull("pending_cycle");initial.putObject("unknown_requests").put("old_request","UNKNOWN");
        Files.write(files.layout.snapshot(),ContinuityJson.canonical(initial));Files.write(Path.of(files.layout.anchor().path()),ContinuityJson.canonical(initial));
        Layout layout=new Layout(files.layout.snapshot(),LedgerFiles.read(Path.of(files.layout.anchor().path()),65_536).pin().reference(),WriterFixture.MACHINE);
        Path data=layout.snapshot().resolveSibling("original-software-input.json");Files.writeString(data,"{\"software_input\":true}");
        ExactRef original=LedgerFiles.read(data,65_536).pin().reference();AtomicReference<ContinuityWriter> own=new AtomicReference<>();
        TransitionAuthority actualSoftwareAuthority=new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before,Request request)throws IOException {throw new IOException("actual original full Head/Session required");}
            @Override public String revalidate(Head before,Request request)throws IOException {
                var writer=own.get();var same=writer.borrowedSession();writer.requireSession(same);
                StrictJson.require(before.digest().equals(same.head().digest()),"actual same-lock resume software predecessor drift");
                var delta=OriginalLegacyResume.checked(before.state(),request);
                for(var ref:delta.evidence())same.verifyPin(same.capturePin(ref,65_536));
                return ContinuityJson.digest(delta.toJson());
            }
            @Override public ContinuityState reduce(ContinuityState before,Request request){return OriginalLegacyResume.reduce(before,request);}
        };
        ContinuityWriter writer=new ContinuityWriter(layout,List.of(LedgerFiles.read(files.source,65_536).pin().reference()),
                actualSoftwareAuthority,Clock.systemUTC(),ContinuityWriter.Extensions.none(),files.storage);own.set(writer);
        return new Fixture(files,layout,writer,original);
    }
    private OriginalLegacyResume.Delta delta(Fixture f)throws IOException {
        Head before=f.writer().locked(ContinuityStorePort.Session::head);ExactRef ref=f.original();
        return new OriginalLegacyResume.Delta(ref,WriterFixture.MACHINE,before.digest(),new OriginalLegacyResume.MissingHistory(),
                OriginalLegacyResume.Route.BIND_UNBOUND,"software-session","software-pipe",new OriginalLegacyResume.Game(42,"18446744073709551615"),
                43,"software-episode",1,0,ref,ref,ref,ref,ref,ref,ref,Optional.empty(),List.of(ref));
    }
    @Test void realWriterAndColdHistoryUseTheSameTypedClosedResumeReducer()throws Exception {
        Fixture f=fixture("cold");var delta=delta(f);assertEquals(delta,OriginalLegacyResume.decode(delta.toJson()));
        Receipt receipt=f.writer().locked(same->same.commit(same.preview(delta.request())));
        assertFalse(receipt.head().toJson().has(GAMEPLAY_ENTRY_FIELD));
        assertEquals(f.original(),ExactRef.fromJson(receipt.head().toJson().get(DRIVER_HISTORY_BASELINE_FIELD)));
        assertEquals("UNKNOWN",receipt.head().toJson().get("unknown_requests").get("old_request").textValue());
        assertTrue(receipt.head().toJson().get("pending_cycle").isNull());assertEquals(1,receipt.head().settledCycles());
        TransitionAuthority noLiveReplay=new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before,Request request){throw new AssertionError("cold read cannot mint physical resume authority");}
            @Override public ContinuityState reduce(ContinuityState before,Request request){throw new AssertionError("cold read cannot call live reducer");}
        };
        var reader=new ContinuityWriter(f.layout(),List.of(LedgerFiles.read(f.files().source,65_536).pin().reference()),noLiveReplay,f.files().storage);
        assertArrayEquals(receipt.head().canonicalBytes(),reader.locked(ContinuityStorePort.Session::head).state().canonicalBytes());
        ObjectNode event=ContinuityJson.parseObject(Files.readAllBytes(f.layout().event(1)),ContinuityJson.DOCUMENT_MAX_BYTES);
        ObjectNode after=ContinuityJson.object(event.get("after"));after.putObject("pending_cycle").put("fabricated","cleared-retry");
        Files.write(f.layout().event(1),ContinuityJson.canonical(event));Files.write(f.layout().snapshot(),ContinuityJson.canonical(after));
        assertThrows(ContractViolationException.class,()->reader.locked(ContinuityStorePort.Session::head));
        assertFalse(Files.exists(f.layout().event(2)),"cold validation cannot repair or append");
    }
    @Test void anotherAuthorityCannotModifyTheDedicatedOriginalResumeField()throws Exception {
        Fixture f=fixture("unrelated");
        TransitionAuthority wrongOwner=new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState before,Request request){
                ObjectNode changed=before.toJson();changed.putObject(OriginalLegacyResume.STATE_FIELD).put("fake","resume");
                return ContinuityState.fromJson(changed,before.machineId());
            }
        };
        var writer=new ContinuityWriter(f.layout(),List.of(LedgerFiles.read(f.files().source,65_536).pin().reference()),wrongOwner,f.files().storage);
        ObjectNode details=StrictJson.object();details.put("evidence_id","unrelated").put("source","actual-software-negative");
        assertThrows(ContractViolationException.class,()->writer.preview(new Request("fixture_unrelated",ContinuityJson.canonical(details),List.of())));
        assertFalse(Files.exists(f.layout().event(1)));assertEquals(0,f.files().storage.successfulBatches());
    }
}
