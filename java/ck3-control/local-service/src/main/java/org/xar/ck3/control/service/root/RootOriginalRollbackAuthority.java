package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.RollbackPair;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Concrete original completed-tail verifier. Every call borrows the actual writer lock and runs the actual two-event reducer. */
public final class RootOriginalRollbackAuthority implements RollbackPair.Authority {
    @FunctionalInterface public interface WriterAccess { ContinuityWriter requireWriter()throws IOException; }
    public enum PreCoreStatus { REQUIRES_BOUND_WRITER_REDUCER }
    private final WriterAccess access;
    private final CheckpointFiles files;
    private final ExactRef configuredProof;
    private final String machine;
    private final Path runtimeRoot;
    private final Clock clock;
    private final Instant reviewAt;
    private ContinuityWriter boundWriter;
    private RootColdCheckpointValidator physical;

    private RootOriginalRollbackAuthority(WriterAccess access,CheckpointFiles files,ExactRef proof,String machine,Path runtimeRoot,Clock clock,Instant reviewAt) {
        this.access=Objects.requireNonNull(access);this.files=Objects.requireNonNull(files);configuredProof=Objects.requireNonNull(proof);
        this.machine=Objects.requireNonNull(machine);this.runtimeRoot=Objects.requireNonNull(runtimeRoot);this.clock=Objects.requireNonNull(clock);this.reviewAt=Objects.requireNonNull(reviewAt);
    }
    /** Reads exact configured proof only. This construction explicitly grants no preview, attachment, Game or cold readiness. */
    public static RootOriginalRollbackAuthority prepare(WriterAccess access,CheckpointFiles files,ExactRef proof,String machine,Path runtimeRoot,Clock clock,Instant reviewAt)throws IOException {
        StrictJson.text(machine);Objects.requireNonNull(runtimeRoot);Objects.requireNonNull(clock);Objects.requireNonNull(reviewAt);
        StrictJson.require(runtimeRoot.isAbsolute()&&runtimeRoot.normalize().equals(runtimeRoot)&&clock.instant().isBefore(reviewAt),"fresh actual original rollback scope required");
        var observed=files.observe(Path.of(proof.path())).orElseThrow(()->new IOException("actual original rollback proof unavailable"));
        StrictJson.require(observed.reference().equals(proof)&&proof.bytes()>0&&proof.bytes()<=32768,"actual bounded original rollback proof required");
        byte[] bytes=files.read(observed,32768);files.verify(observed);var decoded=OriginalRollbackProof.decode(bytes,machine);
        StrictJson.require(decoded.runtimeRoot().equals(runtimeRoot),"configured rollback proof crossed runtime source");
        return new RootOriginalRollbackAuthority(access,files,proof,machine,runtimeRoot,clock,reviewAt);
    }
    public PreCoreStatus preCoreStatus(){return PreCoreStatus.REQUIRES_BOUND_WRITER_REDUCER;}
    @Override public RollbackPair.Evidence revalidate(WriterContracts.Head original,ExactRef requestedProof)throws IOException {
        try {
            StrictJson.require(configuredProof.equals(requestedProof)&&clock.instant().isBefore(reviewAt),"actual configured rollback proof or source review changed");
            ContinuityWriter writer=requireWriter();var same=writer.borrowedSession();writer.requireSession(same);
            StrictJson.require(machine.equals(original.state().machineId()),"original rollback belongs to another machine");
            var originals=new OriginalRollbackFiles(writer,files).open(same,original);
            OriginalRollbackProof proof=OriginalRollbackProof.decode(originals.read(configuredProof,32768).bytes(),machine);
            StrictJson.require(proof.runtimeRoot().equals(runtimeRoot),"original rollback runtime scope drifted");
            var saved=OriginalRollbackSavedFrontier.verify(originals,proof);
            var tail=OriginalRollbackTail.verify(originals,proof,saved);
            OriginalRollbackInventory.verify(originals,proof,saved,tail);
            var closed=OriginalRollbackEpoch.verify(originals,proof,saved,tail);
            OriginalRollbackCanonicalQualification.verify(originals,proof,saved,closed);
            OriginalRollbackContinuity.verify(originals,proof,saved,tail);
            Path profile=Path.of(closed.save().path()).getParent().getParent();
            var expected=new RootColdCheckpointValidator.Expected(closed.driver(),closed.driverIdentity(),closed.save(),closed.saveIdentity(),closed.pipeName(),profile,
                    DriverJson.object(StrictJson.canonical(saved.rawCheckpoint()),65536),DriverJson.object(StrictJson.canonical(saved.basis().get("checkpoint")),65536),closed.historyRows());
            var measured=physical.verifyLegacy(same,expected);requireCurrentDriver(measured.driverPayload(),closed,tail);
            originals.requireCurrent();
            // The writer's own post-authority TOCTOU guard must include both physical files as well as metadata.
            // Its current pin contract is explicitly bounded; an oversized file is unavailable, never silently omitted.
            var closure=new java.util.ArrayList<>(originals.pins());
            closure.add(same.capturePin(closed.driver(),WriterContracts.MAX_PIN_BYTES));closure.add(same.capturePin(closed.save(),WriterContracts.MAX_PIN_BYTES));
            // Bind only the original predecessor and exact immutable source/FileID closure. Partial two-event recovery
            // can legitimately have a later current head, but must re-prove this identical retained original predecessor.
            var condition=StrictJson.object();condition.put("schema","xar.java-original-rollback-precondition/v1");
            condition.set("proof",configuredProof.toJson());condition.put("original_head_sha256",original.digest());
            condition.set("physical_driver",closed.driver().toJson());condition.set("driver_identity",closed.driverIdentity().toJson());
            condition.set("physical_save",closed.save().toJson());condition.set("save_identity",closed.saveIdentity().toJson());
            var sourceRows=condition.putArray("original_sources");for(var pin:closure) {
                var row=sourceRows.addObject();row.set("ref",pin.reference().toJson());var id=pin.identity();
                row.put("volume",id.volumeSerialDecimal());row.put("file",id.fileIdDecimal());row.put("creation",id.creationFiletimeDecimal());row.put("modified",id.modifiedInstant());row.put("bytes",id.bytes());
            }
            var evidence=new RollbackPair.Evidence(configuredProof,StrictJson.canonical(saved.basis()),StrictJson.canonical(tail.frame().toJson()),tail.cycles(),closure,ContinuityJson.digest(condition));
            // Real production reducer preflight is mandatory even when invoked during a commit retry.
            RollbackPair.Plan actual=RollbackPair.plan(original,evidence);RollbackPair.validate(actual);
            originals.requireCurrent();physical.requireCurrentLegacy(same,measured);for(var pin:closure)same.verifyPin(pin);writer.requireSession(same);return evidence;
        }catch(IllegalArgumentException invalid){throw new IOException("actual original completed-tail rollback verification rejected",invalid);}
    }
    private synchronized ContinuityWriter requireWriter()throws IOException {
        ContinuityWriter actual=access.requireWriter();
        if(boundWriter==null){boundWriter=Objects.requireNonNull(actual);physical=new RootColdCheckpointValidator(actual);}
        if(boundWriter!=actual)throw new IOException("original rollback authority cannot be rebound to a different writer instance");return actual;
    }
    private static void requireCurrentDriver(Obj actual,OriginalRollbackEpoch.Closed closed,OriginalRollbackTail.Tail tail) {
        StrictJson.require(OpportunityJson.integer(actual.get("bridge_pid"),"current original Driver PID").longValueExact()==closed.gamePid()
                &&OpportunityJson.integer(actual.get("episode_character_id"),"current original Driver actor").longValueExact()==tail.frame().actorCharacterId()
                &&OpportunityJson.text(actual.get("episode_run_id"),"current original Driver episode").equals(tail.frame().episodeRunId()),"physical current Driver differs from the actually closed original Game/episode");
        var observation=OriginalRollbackSavedFrontier.obj(OriginalRollbackSavedFrontier.obj(closed.review().get("Driver")).get("recorded_identity"));
        var binding=OriginalRollbackSavedFrontier.obj(observation.get("session_binding_observation"));
        boolean present=OriginalRollbackSavedFrontier.bool(binding.get("present"));
        StrictJson.require(actual.members().containsKey("session_binding")==present,"physical current Driver session-binding presence changed");
        if(present)StrictJson.require(DriverJson.object(StrictJson.canonical(binding.get("value")),16384).equals(actual.get("session_binding")),"physical current Driver optional session binding changed");
    }
}
