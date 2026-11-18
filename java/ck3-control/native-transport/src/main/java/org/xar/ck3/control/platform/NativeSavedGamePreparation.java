package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * Materializes the actual Saved load file before initial-policy preparation.
 * The caller supplies its genuinely admitted CheckpointFiles adapter and creates
 * the save directory through its existing storage owner first. This class grants
 * no storage, writer, process, Game or launch authority and writes no ENV/sidecar.
 */
public final class NativeSavedGamePreparation {
    private NativeSavedGamePreparation() { }

    public static NativeSavedGameClone.Observation prepare(NativeLaunchPlan identicalPlan,
            FileWitness originalSave, CheckpointFiles admittedFiles, Clock clock) throws IOException {
        Objects.requireNonNull(identicalPlan);Objects.requireNonNull(originalSave);
        Objects.requireNonNull(admittedFiles);Objects.requireNonNull(clock);
        requireBeforeDeadline(identicalPlan,clock);
        Path actual=NativeSavedGameClone.actualPath(identicalPlan);
        var saved=(NativeLaunchPlan.SavedGame)identicalPlan.load();
        var declared=new ExactRef(saved.save().path(),saved.save().bytes(),saved.save().sha256());
        if(!declared.equals(originalSave.reference()))
            throw new IOException("preparation requires the original exact Saved pair witness");
        SharedSourceFiles.plainAncestors(identicalPlan.profileDirectory());
        SharedSourceFiles.plainAncestors(actual.getParent());
        if(!Files.isDirectory(actual.getParent(),LinkOption.NOFOLLOW_LINKS))
            throw new IOException("the storage owner must prepare the exact save directory first");
        admittedFiles.verify(originalSave);
        var existing=admittedFiles.observe(actual);
        if(existing.isEmpty()) {
            // copyNew owns its exact bounded write through the caller's actual adapter.
            // No raw Files.copy or low-level lifecycle materializer bypasses that adapter.
            var copied=admittedFiles.copyNew(originalSave,actual);
            if(!copied.reference().path().equals(actual.toString())
                    ||copied.reference().bytes()!=originalSave.reference().bytes()
                    ||!copied.reference().sha256().equals(originalSave.reference().sha256()))
                throw new IOException("admitted prelaunch SAVE copy differs from the original source");
            admittedFiles.verify(copied);
        } else if(existing.orElseThrow().reference().bytes()!=originalSave.reference().bytes()
                ||!existing.orElseThrow().reference().sha256().equals(originalSave.reference().sha256())) {
            throw new IOException("a conflicting actual load target is retained without replacement");
        }
        admittedFiles.verify(originalSave);
        requireBeforeDeadline(identicalPlan,clock);
        var observation=NativeSavedGameClone.observe(identicalPlan,originalSave);
        observation.requireCurrent(identicalPlan,originalSave);
        return observation;
    }
    private static void requireBeforeDeadline(NativeLaunchPlan plan,Clock clock)throws IOException {
        if(!clock.instant().isBefore(plan.deadline()))throw new IOException("original Saved preparation deadline expired");
    }

    /** Actual allocated input census. DATA alone never grants a copy, storage or Game permission. */
    public record ExistingCensus(String schema,String machineId,String requestId,String sessionId,
            java.time.Instant observedAt,FileWitness originalSave,FileWitness actualSave,
            SharedSourceFiles.NativeFile actualNativeFile,long existingAllocatedUpperBytes,long newGrowthBytes) {
        public ExistingCensus {
            if(!"xar.java-existing-saved-clone-census/v1".equals(schema)||machineId==null||requestId==null||sessionId==null)
                throw new IllegalArgumentException("exact existing clone census identity required");
            Objects.requireNonNull(observedAt);Objects.requireNonNull(originalSave);Objects.requireNonNull(actualSave);
            Objects.requireNonNull(actualNativeFile);
            if(newGrowthBytes!=0||actualSave.reference().bytes()!=actualNativeFile.logicalBytes()
                    ||existingAllocatedUpperBytes!=Math.max(actualNativeFile.logicalBytes(),actualNativeFile.allocatedBytes()))
                throw new IllegalArgumentException("existing clone census cannot declare unspent output growth");
        }
    }
    /** Opaque current physical input. No copy port or output admission is exposed by this role. */
    public static final class Existing {
        private final NativeLaunchPlan plan;private final FileWitness source;
        private final NativeSavedGameClone.Observation observation;private final ExistingCensus census;private final Clock clock;
        private Existing(NativeLaunchPlan plan,FileWitness source,NativeSavedGameClone.Observation observation,
                ExistingCensus census,Clock clock) {
            this.plan=plan;this.source=source;this.observation=observation;this.census=census;this.clock=clock;
        }
        public void requireCurrent()throws IOException {
            requireBeforeDeadline(plan,clock);observation.requireCurrent(plan,source);
            if(!SharedSourceFiles.nativeFile(Path.of(census.actualSave().reference().path())).equals(census.actualNativeFile()))
                throw new IOException("existing actual SAVE allocation or native identity changed");
        }
        public NativeSavedGameClone.Observation observation()throws IOException{requireCurrent();return observation;}
        public ExistingCensus census()throws IOException{requireCurrent();return census;}
    }
    /**
     * Producer pre-quote path for a clone that already exists. Missing/conflicting inputs
     * fail here; this method does not call prepare(), copyNew(), mkdir or any writer.
     */
    public static Existing requirePrepared(NativeLaunchPlan identicalPlan,FileWitness originalSave,Clock clock)throws IOException {
        Objects.requireNonNull(identicalPlan);Objects.requireNonNull(originalSave);Objects.requireNonNull(clock);
        requireBeforeDeadline(identicalPlan,clock);
        var observed=NativeSavedGameClone.observe(identicalPlan,originalSave);
        var actual=observed.actualSave();var nativeFile=SharedSourceFiles.nativeFile(Path.of(actual.reference().path()));
        var census=new ExistingCensus("xar.java-existing-saved-clone-census/v1",identicalPlan.sources().review().machineId(),
                identicalPlan.requestId(),identicalPlan.sessionId(),clock.instant(),originalSave,actual,nativeFile,
                Math.max(nativeFile.logicalBytes(),nativeFile.allocatedBytes()),0);
        var result=new Existing(identicalPlan,originalSave,observed,census,clock);result.requireCurrent();return result;
    }
}
