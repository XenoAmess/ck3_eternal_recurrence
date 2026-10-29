package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Actual Windows original-writer regression. Fixtures provide no actual Game or runtime admission. */
public final class LifecycleWriterIntegrationTest {
    @TempDir Path temporary;
    private record Fixture(LifecycleBusinessFixture business,LifecycleContinuityAuthority authority,ContinuityWriter writer,LifecycleChild child) { }
    private Fixture fixture() throws Exception { return fixture(false); }
    private Fixture fixture(boolean retainedOldLifecycleStamp) throws Exception {
        var f=new LifecycleBusinessFixture(temporary);var reduction=f.reduction();var delta=LifecycleJson.row();delta.set("result",LifecycleJson.parse(reduction.result(),LifecycleProofCodec.MAX_RESULT_BYTES));
        var child=new LifecycleChild(f.parent,LifecycleChild.Phase.DEATH_RECORDED,f.snapshot.facts().stamp(),reduction.driver(),reduction.auxiliary(),
                f.parent.origin().game(),delta,List.of(f.snapshot.originalEvidence(),f.snapshot.facts().originalHistoryBasis()));
        var authority=new LifecycleContinuityAuthority();authority.bind((actualHead,actualChild)->{
            var original=f.files.observe(Path.of(f.snapshot.originalEvidence().path())).orElseThrow();
            if(!original.reference().equals(f.snapshot.originalEvidence()))throw new IOException("actual original terminal packet changed");f.files.verify(original);
            var rerun=f.reduction();assertArrayEquals(rerun.driver().encode(),actualChild.replacement().encode());
            var checked=LifecycleJson.row();checked.put("native_sha256",original.reference().sha256());checked.put("actual_reducer_sha256",LifecycleJson.sha(rerun.result()));
            return ContinuityJson.digest(checked);
        });authority.register(child);
        var state=LifecycleJson.row();state.put("schema","root.ck3.continuity-window/v1");state.put("machine_id","test-machine");state.put("sequence",0);state.put("window_id",1);
        state.put("start_date_raw",0);state.put("target_date_raw",480);state.put("target_days",20);state.put("status","running");state.put("last_settled_cycles",0);state.put("last_settled_date_raw",240);
        state.put("NEXT",11559);state.putObject("pending_cycle").put("auto_sequence",11558).put("stage","auto_unsettled");
        if(retainedOldLifecycleStamp){var history=state.putObject(LifecycleContinuityAuthority.STATE_FIELD);history.put("driver_sha256","b".repeat(64));history.put("driver_version",17);history.putObject("transitions");}
        Path ledger=temporary.resolve("ROOT-CONTINUITY-WINDOW.json");Files.write(ledger,LifecycleJson.bytes(state));var anchor=f.files.createNew(temporary.resolve("anchor.json"),LifecycleJson.bytes(state)).reference();
        Files.createFile(temporary.resolve("ROOT-CONTINUITY-WINDOW.lock"));Files.createDirectory(temporary.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var layout=new WriterContracts.Layout(ledger,anchor,"test-machine");
        var storage=org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport.create(layout);
        var writer=new ContinuityWriter(layout,List.of(f.parent.source().sourceRef()),authority,storage);
        assertSame(storage,writer.storageGuard());
        return new Fixture(f,authority,writer,child);
    }
    @Test void actualReducerDoesNotOwnSequenceAndOriginalCommitProducesStableRecordedProof() throws Exception {
        var f=fixture();LifecycleComposites.validateScope(f.business.parent,f.business.snapshot);
        assertThrows(IllegalStateException.class,()->f.business.parent.before());assertThrows(IllegalStateException.class,()->f.business.parent.expected());
        f.writer.locked(session->{
            var prepared=session.preview(f.child.request());assertEquals(0,prepared.reduced().sequence());
            f.child.rememberPrepared(prepared);f.child.rememberPrepared(prepared);assertSame(prepared,f.child.prepared().orElseThrow());
            assertThrows(IllegalArgumentException.class,()->f.child.rememberPrepared(session.preview(f.child.request())));
            var receipt=session.commit(prepared);var commit=new LifecycleCommit(prepared,receipt,session.head().documents());
            assertEquals(1,receipt.head().sequence());assertEquals(11559,receipt.head().toJson().get("NEXT").intValue());
            assertEquals(11558,receipt.head().toJson().get("pending_cycle").get("auto_sequence").intValue());
            var proof=new LifecycleTransitionProof.Death(this,f.business.parent,commit,List.of(f.business.snapshot.originalEvidence()),f.business.reduction().result());
            proof.validateParent(f.business.parent);byte[] encoded=proof.encode();assertTrue(encoded.length>128*1024);
            var retained=LifecycleProofCodec.decodeRecorded(encoded);retained.validateParent(f.business.parent);assertArrayEquals(encoded,retained.encode());
            var wire=LifecycleJson.parse(encoded,LifecycleProofCodec.MAX_PROOF_BYTES);
            assertTrue(wire.get("committed_documents").get(0).get("native_identity").get("file_id").isTextual());return null;
        });
    }
    @Test void physicalSourceDriftAfterPreviewPreventsAnyLifecycleCommit() throws Exception {
        var f=fixture();f.writer.locked(session->{var prepared=session.preview(f.child.request());
            Files.writeString(Path.of(f.business.snapshot.originalEvidence().path()),"tampered original terminal packet");
            assertThrows(Exception.class,()->session.commit(prepared));assertEquals(0,session.head().state().sequence());return null;
        });
    }
    @Test void oldLifecycleHistoryStampDoesNotOverrideActualCurrentDriverSourceGuard() throws Exception {
        var f=fixture(true);f.writer.locked(session->{
            var prepared=session.preview(f.child.request());var receipt=session.commit(prepared);
            new LifecycleCommit(prepared,receipt,session.head().documents());
            assertEquals(1,receipt.head().sequence());assertEquals(1,receipt.head().toJson().get(LifecycleContinuityAuthority.STATE_FIELD).get("driver_version").longValue());return null;
        });
    }
    @Test void callerStateCannotQualifyLifecycleWithoutActualHeadAndRegisteredPrivateChild() throws Exception {
        var f=fixture();f.writer.locked(session->{
            assertThrows(IOException.class,()->f.authority.revalidate(session.head().state(),f.child.request()));
            var changed=LifecycleJson.parse(f.child.request().details(),LifecycleProofCodec.MAX_RESULT_BYTES);changed.put("token","unregistered-private-token");
            var forged=new WriterContracts.Request(LifecycleChild.KIND,LifecycleJson.bytes(changed),f.child.request().evidence());
            assertThrows(IllegalArgumentException.class,()->session.preview(forged));assertEquals(0,session.head().state().sequence());return null;
        });
    }
}
