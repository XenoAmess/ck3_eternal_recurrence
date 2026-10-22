package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Metadata serialization only; actual Java HTTP/kernel consumers run in MapAdmissionCi. */
final class MapAdmissionServiceOwnerTest {
    @Test
    void completeLargeManifestRoundtripsAllActualSourceRefsAboveSmallReceiptCap(@TempDir Path temporary) throws Exception {
        List<ControlBuild.FileRef> sources = new ArrayList<>();
        for (int index = 0; index < 512; index++) {
            Path source = temporary.resolve("source-file-" + index + ".java"); Files.writeString(source, "// measured source " + index);
            sources.add(ControlBuild.FileRef.measure(source));
        }
        ControlBuild.FileRef first = sources.getFirst();
        MapAdmissionServiceOwner.ProgramManifest produced = manifest(temporary, sources, first);
        Path path = temporary.resolve("program-manifest.json");
        ControlBuild.FileRef reference = MapAdmissionServiceOwner.publishProgramManifest(path, produced);
        assertTrue(reference.bytes() > MapAdmissionServiceOwner.MAX_SMALL_RECEIPT_BYTES);
        assertTrue(reference.bytes() <= MapAdmissionServiceOwner.MAX_PROGRAM_MANIFEST_BYTES);
        reference.verify();
        MapAdmissionServiceOwner.ProgramManifest consumed = ControlBuild.strictMapper().readValue(Files.readAllBytes(path), MapAdmissionServiceOwner.ProgramManifest.class);
        assertEquals(produced, consumed);
        assertEquals(sources, consumed.sourceRefs());
        for (ControlBuild.FileRef source : consumed.sourceRefs()) source.verify();
        MapAdmissionServiceOwner.RunningReceipt running = new MapAdmissionServiceOwner.RunningReceipt(
                "xar.java-map-service-running/v1", "synthetic-metadata-test", Instant.now().toString(), "ACTUAL_RUNNING",
                MapAdmissionServiceOwner.PRODUCER, MapAdmissionServiceOwner.PRODUCER_VERSION,
                "http://127.0.0.1:8089/v1/map-admissions/compose", reference, sources,
                new MapAdmissionServiceOwner.ProcessWire(1, "18446744073709551615", first.path()));
        Path rejected = temporary.resolve("oversized-running.json");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.publish(rejected, running));
        assertTrue(Files.notExists(rejected), "existing running evidence consumer remains bounded at 64 KiB");
    }

    @Test
    void programManifestStillRejectsWholeBodyAboveItsFrozenConsumerLimitBeforeWriting(@TempDir Path temporary) throws Exception {
        Path source = temporary.resolve("actual-source.java"); Files.writeString(source, "// actual");
        ControlBuild.FileRef reference = ControlBuild.FileRef.measure(source);
        MapAdmissionServiceOwner.ProgramManifest oversized = manifest(temporary, Collections.nCopies(10000, reference), reference);
        Path rejected = temporary.resolve("oversized-manifest.json");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.publishProgramManifest(rejected, oversized));
        assertTrue(Files.notExists(rejected));
    }

    private static MapAdmissionServiceOwner.ProgramManifest manifest(Path deployment, List<ControlBuild.FileRef> sources,
                                                                    ControlBuild.FileRef reference) {
        return new MapAdmissionServiceOwner.ProgramManifest("xar.java-map-complete-fastjar-deployment/v1", "synthetic-metadata-test",
                Instant.now().toString(), deployment.toString(), List.of(reference), List.copyOf(sources), reference, reference, true, true);
    }
}
