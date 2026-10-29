package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real physical original-reader and sole-writer refusal paths. A well-shaped proof never becomes eligibility. */
final class RootOriginalRollbackAuthorityTest {
    @TempDir Path temporary;
    private static final String MACHINE="rollback-negative-fixture";
    private static final Clock CLOCK=Clock.fixed(Instant.parse("2026-10-24T00:00:00Z"),ZoneOffset.UTC);
    @Test void exactProofParsingRemainsExplicitlyUnqualifiedUntilTheBoundWriterReducerRuns()throws Exception {
        Path runtime=temporary.resolve("runtime");Files.createDirectory(runtime);ExactRef proof=proof(runtime);var writer=writer(runtime);
        var authority=RootOriginalRollbackAuthority.prepare(()->writer,new NativeCheckpointFiles(),proof,MACHINE,runtime,CLOCK,CLOCK.instant().plusSeconds(60));
        assertEquals(RootOriginalRollbackAuthority.PreCoreStatus.REQUIRES_BOUND_WRITER_REDUCER,authority.preCoreStatus());
        assertThrows(IOException.class,()->writer.locked(same->{
            // Prior basis '{}' is intentionally not a genuine saved frontier. Every document and Session is real.
            authority.revalidate(same.head(),proof);return null;
        }));
        writer.locked(same->{assertEquals(0,same.head().state().sequence());assertEquals(0,same.head().state().settledCycles());return null;});
    }
    @Test void authorityCannotAcquireAnotherWriterLockOrReuseAnUnrelatedConfiguredProof()throws Exception {
        Path runtime=temporary.resolve("runtime");Files.createDirectory(runtime);ExactRef proof=proof(runtime);var writer=writer(runtime);
        var authority=RootOriginalRollbackAuthority.prepare(()->writer,new NativeCheckpointFiles(),proof,MACHINE,runtime,CLOCK,CLOCK.instant().plusSeconds(60));
        var head=writer.locked(same->same.head());
        assertThrows(IOException.class,()->authority.revalidate(head,proof));
        ExactRef other=new ExactRef(proof.path(),proof.bytes(),"0".repeat(64));
        writer.locked(same->{assertThrows(IOException.class,()->authority.revalidate(same.head(),other));assertEquals(0,same.head().state().sequence());return null;});
    }
    @Test void prepareRejectsWrongMachineExpiredReviewReplacedProofAndNonP37JavaSchema()throws Exception {
        Path runtime=temporary.resolve("runtime");Files.createDirectory(runtime);ExactRef proof=proof(runtime);var writer=writer(runtime);
        assertThrows(Exception.class,()->RootOriginalRollbackAuthority.prepare(()->writer,new NativeCheckpointFiles(),proof,"other-machine",runtime,CLOCK,CLOCK.instant().plusSeconds(60)));
        assertThrows(Exception.class,()->RootOriginalRollbackAuthority.prepare(()->writer,new NativeCheckpointFiles(),proof,MACHINE,runtime,CLOCK,CLOCK.instant()));
        ObjectNode java=StrictJson.object();java.put("schema","xar.java-saved-checkpoint-material/v1");
        Files.write(Path.of(proof.path()),StrictJson.canonical(java));
        assertThrows(Exception.class,()->RootOriginalRollbackAuthority.prepare(()->writer,new NativeCheckpointFiles(),proof,MACHINE,runtime,CLOCK,CLOCK.instant().plusSeconds(60)));
        ExactRef current=ref(Path.of(proof.path()));
        assertThrows(Exception.class,()->RootOriginalRollbackAuthority.prepare(()->writer,new NativeCheckpointFiles(),current,MACHINE,runtime,CLOCK,CLOCK.instant().plusSeconds(60)));
    }
    private static ExactRef proof(Path runtime)throws IOException {
        Path empty=runtime.resolve("original-empty-basis.json");Files.writeString(empty,"{}");ExactRef source=ref(empty);
        var row=StrictJson.object();row.put("schema",OriginalRollbackProof.SCHEMA);row.put("status","CLOSED_COMPLETED_UNSAVED_TAIL");row.put("machine_id",MACHINE);
        row.put("observed_at_utc","2026-10-24T00:00:00Z");row.put("runtime_root",runtime.toString());row.put("new_ordinary_cycle_credit",0);row.put("new_game_day_credit",0);
        row.put("original_actions_replayed",false);row.put("Driver_history_truncated",false);var sources=row.putObject("sources");
        for(String field:List.of("prior_basis","prior_validation","raw_state","raw_governance","interruption","inventory","abnormal_closed_epoch","current_driver_review","actual_next","canonical_checkpoint_qualification","continuity_frontier"))sources.set(field,source.toJson());
        sources.putArray("successful_full_responses").add(source.toJson());Path proof=runtime.resolve("proof.json");Files.write(proof,StrictJson.canonical(row));return ref(proof);
    }
    private static ContinuityWriter writer(Path runtime)throws IOException {
        Path source=runtime.resolve("actual-source.java");Files.writeString(source,"original rollback fixture reviewed source");
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",MACHINE);row.put("sequence",0);row.put("window_id",1);row.put("status","running");
        row.put("target_days",10958);row.put("target_years",30);row.put("calendar_year_days",365.25);row.put("start_date_raw",1000);row.put("target_date_raw",263992);row.put("last_settled_date_raw",1000);
        row.put("last_settled_cycles",0);row.put("manual_repair_count",0);row.put("automatic_recovery_count",0);row.put("binding_lineage_count",0);row.putObject("game_binding").put("pid",42).put("creation_date","2026-10-24T00:00:00Z");
        row.putNull("latest_binding");row.putNull("pending_cycle");row.put("NEXT",1);
        Path snapshot=runtime.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=runtime.resolve("anchor.json");byte[] encoded=ContinuityJson.canonical(row);Files.write(snapshot,encoded);Files.write(anchor,encoded);
        Files.write(runtime.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(runtime.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var layout=new WriterContracts.Layout(snapshot,ref(anchor),MACHINE);return new ContinuityWriter(layout,List.of(ref(source)),new WriterContracts.TransitionAuthority(){
            @Override public String revalidate(ContinuityState previous,WriterContracts.Request request){throw new AssertionError("rollback negative cannot commit");}
            @Override public ContinuityState reduce(ContinuityState previous,WriterContracts.Request request){throw new AssertionError("rollback negative cannot reduce");}
        },CLOCK,org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport.create(layout));
    }
    private static ExactRef ref(Path path)throws IOException {byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toString(),bytes.length,DriverJson.sha256(bytes));}
}
