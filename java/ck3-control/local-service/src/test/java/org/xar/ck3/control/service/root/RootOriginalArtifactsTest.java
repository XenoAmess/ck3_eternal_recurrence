package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.writer.ArchiveOriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

import static org.junit.jupiter.api.Assertions.*;

final class RootOriginalArtifactsTest {
    @TempDir Path root;

    @Test void retainedDriverAndExactPhysicalSourceUseTheirOwnStorageRoles() throws Exception {
        var genesis = new FreshContinuityGenesis.Plan("software-machine", 1, 10958);
        var layout = new WriterContracts.InitialLayout(root.resolve("continuity.json"), root.resolve("anchor.json"), genesis.machineId());
        Files.createFile(layout.lock());
        var storage = StorageWriteGuardTestSupport.create(root, layout.lock(), 32L << 20);
        var initialized = ContinuityWriter.initializeFresh(genesis,
                write("genesis.json", FreshContinuityGenesis.encode(genesis)), layout, storage);
        byte[] sourceBytes = {1, 2, 3};
        var source = write("original-runtime.jar", sourceBytes);
        var otherSource = write("another-runtime.jar", sourceBytes);
        var artifacts = new ImmutableArtifactStore(
                new ImmutableArtifactStore.Config(root.resolve("objects"), layout.lock(), 16L << 20), storage);
        var writer = new ContinuityWriter(initialized.layout(), List.of(source), new RootAuthorityRouter(), Clock.systemUTC(),
                new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
        var archive = new NativeOutcomeArchive(artifacts, writer);
        writer.locked(same -> {
            byte[] driverBytes = {4, 5, 6};
            var driver = archive.preserveArtifact(same, driverBytes, ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
            var archiveOnly = new ArchiveOriginalEvidencePort(archive);
            var failure = assertThrows(IllegalArgumentException.class,
                    () -> archiveOnly.read(same, driver, DriverCheckpointStore.MAX_DRIVER_BYTES));
            assertEquals("finite immutable artifact bound required", failure.getMessage());
            assertArrayEquals(driverBytes, RootOriginalArtifacts.read(writer, archive, same, driver,
                    DriverCheckpointStore.MAX_DRIVER_BYTES, source));
            assertArrayEquals(sourceBytes, RootOriginalArtifacts.read(writer, archive, same, source,
                    DriverJson.MAX_NATIVE_BYTES, source));
            assertThrows(IOException.class,
                    () -> RootOriginalArtifacts.read(writer, archive, same, otherSource, DriverJson.MAX_NATIVE_BYTES, source));
            assertThrows(IOException.class, () -> RootOriginalArtifacts.read(writer, archive, same, source, 2, source));
            return null;
        });
    }

    private ExactRef write(String name, byte[] bytes) throws IOException {
        var path = Files.write(root.resolve(name), bytes);
        return new ExactRef(path.toString(), bytes.length, ActionCodec.sha256(bytes));
    }
}
