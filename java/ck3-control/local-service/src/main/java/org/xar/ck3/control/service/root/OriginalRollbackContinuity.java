package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.service.root.OriginalRollbackSavedFrontier.*;

/** Uses this writer's real source-index/event ancestry; a frontier JSON digest alone never qualifies recovery. */
public final class OriginalRollbackContinuity {
    private OriginalRollbackContinuity(){ }
    public static void verify(OriginalRollbackFiles.Scope files,OriginalRollbackProof proof,Saved saved,OriginalRollbackTail.Tail tail)throws IOException {
        ObjectNode row=load(files,proof.sources().continuityFrontier(),32768);
        exact(row,Set.of("schema","machine_id","observed_at_utc","canonical_path","anchor_ref","head_event_ref","writer_source_ref","head_sequence","head_digest"));
        eq(row,"schema","xar.current-saved-historical-rollback-frontier/v1");eq(row,"machine_id",proof.machineId());utc(row,"observed_at_utc");
        Path canonical=Path.of(text(row,"canonical_path"));files.requireCanonicalLedger(canonical);
        require(ref(row,"anchor_ref").equals(ref(obj(saved.basis().get("refs")),"ledger")),"saved business ledger must remain the immutable rollback anchor");
        var source=ref(row,"writer_source_ref");require(Path.of(source.path()).equals(proof.runtimeRoot().resolve("root_continuity_window_c23_100.py")),"original frozen P37 writer source differs");files.read(source,131072);
        long sequence=n(row,"head_sequence",1);String digest=text(row,"head_digest");WriterContracts.requireDigest(digest);
        require(sequence==files.originalHead().state().sequence()&&digest.equals(files.originalHead().digest()),"proof frontier differs from actual original rollback predecessor");
        var anchor=load(files,ref(row,"anchor_ref"),65536);long anchorSequence=n(anchor,"sequence",0);
        files.session().requireHistoricalState(anchorSequence,ContinuityJson.digest(anchor));
        var eventRef=ref(row,"head_event_ref");require(Path.of(eventRef.path()).equals(canonical.getParent().resolve("ROOT-CONTINUITY-WINDOW-EVENTS")
                .resolve(String.format(java.util.Locale.ROOT,"%08d.json",sequence))),"historical rollback predecessor must be its actual canonical event file");
        ObjectNode event=load(files,eventRef,ContinuityJson.DOCUMENT_MAX_BYTES),state=obj(event.get("after"));
        require(sequence>anchorSequence&&n(event,"sequence",1)==sequence&&n(state,"sequence",1)==sequence&&ContinuityJson.digest(state).equals(digest)
                &&text(event,"identity").equals(text(state,"last_event_identity")),"captured predecessor does not match its original immutable event");
        ContinuityState actual=files.session().requireHistoricalState(sequence,digest);
        require(same(actual.toJson(),state)&&same(actual.toJson(),files.originalHead().state().toJson())&&actual.settledCycles()==tail.cycles()
                &&actual.settledDateRaw()==tail.frame().dateRaw(),"actual canonical predecessor differs from completed FULL tail");
    }
}
