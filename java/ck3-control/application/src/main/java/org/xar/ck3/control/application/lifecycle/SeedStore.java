package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Original first-SAVE seed freeze, with CREATE_NEW publication and no overwrite of orphan/history seeds. */
public final class SeedStore implements CheckpointService.SeedAdoptionPort {
    @FunctionalInterface public interface StorageGuard { void require(long fullCopyBytes) throws IOException; }
    private final CheckpointFiles files;
    private final DriverCheckpointStore drivers;
    private final Path seedPath, metadataPath, historyPath;
    private final StorageGuard storage;
    public SeedStore(CheckpointFiles files, DriverCheckpointStore drivers, Path stateRoot, Path saveGames, StorageGuard storage) {
        this.files=Objects.requireNonNull(files); this.drivers=Objects.requireNonNull(drivers); this.storage=Objects.requireNonNull(storage);
        StrictJson.require(stateRoot.isAbsolute() && saveGames.isAbsolute(), "exact configured original state/profile roots required");
        seedPath=saveGames.resolve(SeedArtifact.NAME).normalize(); metadataPath=stateRoot.resolve("native-session/episode-seed.json").normalize();
        historyPath=stateRoot.resolve("strategy/one-life-history.json").normalize();
    }
    /** Construction custody only: a second equal-looking adapter or Driver store is not the staged producer. */
    public void requireBacking(CheckpointFiles expectedFiles,DriverCheckpointStore expectedDrivers)throws IOException {
        if(files!=Objects.requireNonNull(expectedFiles)||drivers!=Objects.requireNonNull(expectedDrivers))
            throw new IOException("SeedStore does not use the actual staged checkpoint files and DriverCheckpointStore instances");
    }
    public synchronized SeedAdoption read() throws IOException {
        var metadata=files.observe(metadataPath); var seed=files.observe(seedPath);
        if (metadata.isPresent()) {
            if (seed.isEmpty()) return new SeedAdoption.Unknown("seed metadata exists but immutable SAVE is absent",List.of(metadata.orElseThrow().reference()));
            try { return new SeedAdoption.Available(decode(files,seed.orElseThrow(),metadata.orElseThrow()),SeedAdoption.Origin.EXISTING); }
            catch (IOException|IllegalArgumentException failure) { return new SeedAdoption.Unknown("existing seed failed exact readback: "+failure.getMessage(),List.of(metadata.orElseThrow().reference(),seed.orElseThrow().reference())); }
        }
        if (seed.isPresent()) return new SeedAdoption.Unavailable(SeedAdoption.Reason.ORPHAN_SEED,List.of(seed.orElseThrow().reference()));
        return new SeedAdoption.Unavailable(SeedAdoption.Reason.INVALID_IDENTITY,List.of());
    }
    @Override public synchronized SeedAdoption freezeFirst(CheckpointPair pair,ActionReceipt appliedSave) throws IOException {
        Objects.requireNonNull(pair); Objects.requireNonNull(appliedSave); drivers.verify(pair);
        StrictJson.require(appliedSave.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                && appliedSave.command().operation().value().equals("save-checkpoint")
                && appliedSave.command().actionId().equals(pair.saveActionId())
                && appliedSave.command().before().game().equals(pair.frame().game())
                && appliedSave.command().before().frame().episodeRunId().equals(pair.frame().frame().episodeRunId())
                && appliedSave.ack().isPresent()
                && LifecycleJson.sha(appliedSave.ack().orElseThrow().originalPacket()).equals(pair.nativeAckRef().sha256()),"same confirmed original SAVE authority receipt required");
        var present=read();
        if (!(present instanceof SeedAdoption.Unavailable unavailable) || unavailable.reason()!=SeedAdoption.Reason.INVALID_IDENTITY) return present;
        var history=files.observe(historyPath);
        if (history.isPresent()) {
            try {
                ObjectNode prior=LifecycleJson.parse(files.read(history.orElseThrow(),4<<20),4<<20);
                StrictJson.require(prior.get("episodes")!=null && prior.get("episodes").isArray(),"actual episode history must contain an episodes array");
                if (!prior.get("episodes").isEmpty())
                    return new SeedAdoption.Unavailable(SeedAdoption.Reason.PRIOR_EPISODES,List.of(history.orElseThrow().reference()));
            } catch (IOException|IllegalArgumentException failure) { return new SeedAdoption.Unavailable(SeedAdoption.Reason.HISTORY_UNREADABLE,List.of(history.orElseThrow().reference())); }
        }
        BigInteger actor=pair.frame().frame().identity().player(); String run=pair.frame().frame().episodeRunId();
        try{NativeCharacterId.of(actor);}catch(IllegalArgumentException invalid){return new SeedAdoption.Unavailable(SeedAdoption.Reason.INVALID_IDENTITY,List.of(pair.driver().reference()));}
        if (run.isEmpty()) return new SeedAdoption.Unavailable(SeedAdoption.Reason.INVALID_IDENTITY,List.of(pair.driver().reference()));
        storage.require(Math.addExact(pair.save().reference().bytes(),65536));
        FileWitness seed=null;
        try {
            drivers.verify(pair); seed=files.copyNew(pair.save(),seedPath);
            ObjectNode row=LifecycleJson.row(); row.put("format_version",1); row.put("name",SeedArtifact.NAME); row.put("path",seed.reference().path());
            row.put("size",seed.reference().bytes()); row.put("sha256",seed.reference().sha256()); row.put("date_raw",pair.frame().frame().identity().dateRaw());
            row.put("character_id",actor); row.put("source_run_id",run); row.put("source_checkpoint_name","xar_checkpoint.ck3"); row.put("immutable",true);
            if (files.observe(metadataPath).isPresent()) return new SeedAdoption.Unknown("seed metadata appeared after CREATE_NEW; no overwrite",List.of(seed.reference()));
            FileWitness metadata=files.createNew(metadataPath,LifecycleJson.bytes(row));
            SeedArtifact actual=decode(files,seed,metadata); drivers.verify(pair);
            return new SeedAdoption.Available(actual,SeedAdoption.Origin.FIRST_FREEZE);
        } catch (IOException|IllegalArgumentException failure) {
            // A successful immutable copy followed by failure stays an orphan. Never copy the current SAVE over it.
            return new SeedAdoption.Unknown("first seed freeze requires read-only reconciliation: "+failure.getMessage(),seed==null?List.of(pair.save().reference()):List.of(seed.reference()));
        }
    }
    static SeedArtifact decode(CheckpointFiles files,FileWitness seed,FileWitness metadata) throws IOException {
        files.verify(seed); ObjectNode row=LifecycleJson.parse(files.read(metadata,65536),65536);
        LifecycleJson.exact(row,Set.of("format_version","name","path","size","sha256","date_raw","character_id","source_run_id","source_checkpoint_name","immutable"));
        StrictJson.require(LifecycleJson.integer(row.get("format_version"),BigInteger.ONE).equals(BigInteger.ONE)
                && LifecycleJson.text(row.get("name")).equals(SeedArtifact.NAME)
                && Path.of(LifecycleJson.text(row.get("path"))).equals(Path.of(seed.reference().path()))
                && LifecycleJson.integer(row.get("size"),BigInteger.ONE).equals(BigInteger.valueOf(seed.reference().bytes()))
                && LifecycleJson.text(row.get("sha256")).equals(seed.reference().sha256())
                && LifecycleJson.text(row.get("source_checkpoint_name")).equals("xar_checkpoint.ck3")
                && LifecycleJson.bool(row.get("immutable")),"immutable seed original bytes/identity differ");
        StrictJson.require(Path.of(seed.reference().path()).getFileName().toString().equals(SeedArtifact.NAME),"current checkpoint cannot masquerade as seed");
        BigInteger date=LifecycleJson.integer(row.get("date_raw"),BigInteger.ZERO),actor=NativeCharacterId.fromJson(row.get("character_id")).asBigInteger();
        StrictJson.require(date.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"seed date must remain an exact safe integer");
        files.verify(seed);files.verify(metadata);
        return new SeedArtifact(seed,metadata,date,actor,LifecycleJson.text(row.get("source_run_id")));
    }
}
