package org.xar.ck3.control.application.capabilities;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.application.lifecycle.SeedStore;
import org.xar.ck3.control.contracts.StrictJson;

/** Read-only use of the same strong file/immutable-seed producers as SAVE and restore. */
public final class CapabilityFileProbe {
    public sealed interface FileState permits Present, Absent, Unavailable, Unconfigured { }
    public record Present(FileWitness witness) implements FileState { public Present { Objects.requireNonNull(witness); } }
    public record Absent(Path path) implements FileState { public Absent { Objects.requireNonNull(path); } }
    public record Unavailable(String reason) implements FileState { public Unavailable { StrictJson.text(reason); } }
    public record Unconfigured() implements FileState { }
    public record Capture(String frameBindingSha256, Stamp stamp, FileState checkpoint, Optional<SeedAdoption> seed) {
        public Capture { StrictJson.text(frameBindingSha256); Objects.requireNonNull(stamp); Objects.requireNonNull(checkpoint); Objects.requireNonNull(seed); }
    }
    private final CheckpointFiles files;
    private Optional<SeedStore> seeds;
    public CapabilityFileProbe(CheckpointFiles files,Optional<SeedStore> seeds) { this.files = Objects.requireNonNull(files); this.seeds = Objects.requireNonNull(seeds); }
    /** Installed only after the real first-SAVE stage has constructed its sole immutable-seed producer. */
    public synchronized void bindSeeds(SeedStore actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(seeds.isEmpty()||seeds.orElseThrow()==actual,"capability seed producer cannot change its actual stage owner");
        seeds=Optional.of(actual);
    }
    private synchronized Optional<SeedStore> currentSeeds(){return seeds;}

    /** Call once per held frame and share this capture between MCP and readiness. It never writes or copies a SAVE. */
    public Capture capture(Complete frame,Stamp stamp,DynamicCapabilities.Configuration config,boolean needSeed) {
        Objects.requireNonNull(frame); Objects.requireNonNull(stamp); Objects.requireNonNull(config);
        StrictJson.require(stamp.game().equals(frame.identity().game()) && stamp.episodeRunId().equals(frame.identity().frame().episodeRunId()),"file projection crossed the current Game/episode");
        return captureMaterial(frame.fullBindingSha256(),stamp,config,needSeed);
    }
    /** Same actual immutable-seed/file producers for a full raw terminal frame. The private scope
     * preserves missing/changed native actor data instead of manufacturing an ordinary Complete. */
    public Capture capturePublicTerminal(org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot full,
            org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known,
            org.xar.ck3.control.application.driver.DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,
            DynamicCapabilities.Configuration config,boolean needSeed)throws IOException {
        Objects.requireNonNull(scope).requireInputs(full,known);Objects.requireNonNull(config);
        StrictJson.require(known.stamp().game().equals(full.actual().session().game())
                &&known.stamp().episodeRunId().equals(full.facts().driver().session().episodeRunId()),
                "terminal file projection crossed its actual physical Game/episode");
        Capture result=captureMaterial(full.fullBindingSha256(),known.stamp(),config,needSeed);scope.requireCurrent();return result;
    }
    private Capture captureMaterial(String actualFrameBinding,Stamp stamp,DynamicCapabilities.Configuration config,boolean needSeed) {
        FileState checkpoint;
        if (config.stateDir().isEmpty() || config.saveDir().isEmpty()) checkpoint = new Unconfigured();
        else {
            Path path = config.saveDir().orElseThrow().resolve("xar_checkpoint.ck3").normalize();
            try { checkpoint = files.observe(path).<FileState>map(Present::new).orElseGet(() -> new Absent(path)); }
            catch (IOException failure) { checkpoint = new Unavailable(failure.getClass().getSimpleName() + ": " + Objects.toString(failure.getMessage(),"checkpoint native observation unavailable")); }
        }
        Optional<SeedAdoption> seed = Optional.empty();
        if (needSeed && config.stateDir().isPresent() && config.saveDir().isPresent()) {
            Optional<SeedStore> actualSeeds=currentSeeds();
            if (actualSeeds.isEmpty()) seed = Optional.of(new SeedAdoption.Unknown("actual immutable seed producer is not installed",java.util.List.of()));
            else try { seed = Optional.of(actualSeeds.orElseThrow().read()); }
            catch (IOException failure) { seed = Optional.of(new SeedAdoption.Unknown("actual immutable seed read failed: " + Objects.toString(failure.getMessage(),failure.getClass().getSimpleName()),java.util.List.of())); }
        }
        return new Capture(actualFrameBinding,stamp,checkpoint,seed);
    }
}
