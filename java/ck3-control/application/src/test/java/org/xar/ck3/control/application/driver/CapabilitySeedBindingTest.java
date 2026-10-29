package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.capabilities.CapabilityFileProbe;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.application.lifecycle.SeedArtifact;
import org.xar.ck3.control.application.lifecycle.SeedStore;
import org.xar.ck3.control.application.session.FrozenDriverSnapshotSupplier;

/** Actual SeedStore.read is reached only after binding the identical stage-owned product. No SAVE is created. */
final class CapabilitySeedBindingTest {
    @TempDir Path temporary;
    @Test void lateActualStageSeedBindingPreservesUnknownBeforeBindingAndCannotSwitchOwners() {
        var fixture=DriverCapabilityStateProducerTest.fresh();var known=fixture.current();
        var files=new ReadOnlyFiles();Path state=temporary.resolve("state"),saves=temporary.resolve("saves");
        var assembler=new DriverStateAssembler(new ActionSnapshotReader(new DriverStateAssemblerTest.Journal(DriverStateAssemblerTest.snapshot(known,List.of()))),
                new DriverFactsRepository(known),actual->{throw new AssertionError("seed file capture cannot refresh a Native observation");});
        var drivers=new DriverCheckpointStore(files,state.resolve("driver.json"),known.driver().session().pipeName(),new FrozenDriverSnapshotSupplier(assembler));
        var stage=new SeedStore(files,drivers,state,saves,bytes->{throw new AssertionError("read-only seed capability capture cannot reserve or freeze a SAVE");});
        var config=new DynamicCapabilities.Configuration(Optional.of(state),Optional.of(saves),3,3,false,false);
        var probe=new CapabilityFileProbe(files,Optional.empty());
        var unbound=probe.capture(fixture.frame(),known.stamp(),config,true);
        assertInstanceOf(SeedAdoption.Unknown.class,unbound.seed().orElseThrow());
        assertEquals(List.of(saves.resolve("xar_checkpoint.ck3")),files.observed);
        probe.bindSeeds(stage);probe.bindSeeds(stage);files.observed.clear();
        var bound=probe.capture(fixture.frame(),known.stamp(),config,true);
        assertEquals(SeedAdoption.Reason.INVALID_IDENTITY,assertInstanceOf(SeedAdoption.Unavailable.class,bound.seed().orElseThrow()).reason());
        assertEquals(List.of(saves.resolve("xar_checkpoint.ck3"),state.resolve("native-session/episode-seed.json"),saves.resolve(SeedArtifact.NAME)),files.observed);
        var other=new SeedStore(files,drivers,state,saves,bytes->{throw new AssertionError("no seed write");});
        assertThrows(IllegalArgumentException.class,()->probe.bindSeeds(other));
        var legacy=new CapabilityFileProbe(files,Optional.of(stage));legacy.bindSeeds(stage);
        assertThrows(IllegalArgumentException.class,()->legacy.bindSeeds(other));
        files.failure=state.resolve("native-session/episode-seed.json");
        assertInstanceOf(SeedAdoption.Unknown.class,probe.capture(fixture.frame(),known.stamp(),config,true).seed().orElseThrow());
        files.observed.clear();assertTrue(probe.capture(fixture.frame(),known.stamp(),config,false).seed().isEmpty());
        assertEquals(List.of(saves.resolve("xar_checkpoint.ck3")),files.observed);
    }
    private static final class ReadOnlyFiles implements CheckpointFiles {
        final List<Path> observed=new ArrayList<>();Path failure;
        @Override public Optional<FileWitness> observe(Path actual)throws IOException {observed.add(actual);if(actual.equals(failure))throw new IOException("actual seed input unavailable");return Optional.empty();}
        @Override public byte[] read(FileWitness expected,int maximumBytes){throw new AssertionError("absent seed has no readable bytes");}
        @Override public FileWitness replace(Path target,byte[] bytes){throw new AssertionError("file capability capture cannot write");}
        @Override public FileWitness createNew(Path target,byte[] bytes){throw new AssertionError("file capability capture cannot create");}
        @Override public FileWitness copyNew(FileWitness source,Path target){throw new AssertionError("file capability capture cannot copy");}
    }
}
