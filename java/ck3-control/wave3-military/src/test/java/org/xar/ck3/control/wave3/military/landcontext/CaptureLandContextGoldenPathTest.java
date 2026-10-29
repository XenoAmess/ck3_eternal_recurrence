package org.xar.ck3.control.wave3.military.landcontext;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class CaptureLandContextGoldenPathTest {
    @TempDir Path root;

    @Test void createsOnlyNewScratchInsideExplicitRoot() throws IOException {
        Path scratch = root.resolve("scratch");
        Path output = root.resolve("full-land-context-golden-v1.json");
        assertEquals(scratch, CaptureLandContextGolden.prepareScratch(root.toString(), scratch, output));
        assertTrue(Files.isDirectory(scratch));
        assertFalse(Files.exists(output));
    }

    @Test void missingExplicitRootRejectsBeforeWriting() {
        Path scratch = root.resolve("scratch");
        assertThrows(IOException.class, () -> CaptureLandContextGolden.prepareScratch(null, scratch, root.resolve("golden")));
        assertFalse(Files.exists(scratch));
    }

    @Test void outputOutsideRootRejectsBeforeWriting() {
        Path scratch = root.resolve("scratch");
        assertThrows(IOException.class, () -> CaptureLandContextGolden.prepareScratch(
                root.toString(), scratch, root.resolve("outside/golden")));
        assertFalse(Files.exists(scratch));
    }

    @Test void scratchOutsideRootRejectsBeforeWriting() {
        Path scratch = root.resolve("outside/scratch");
        assertThrows(IOException.class, () -> CaptureLandContextGolden.prepareScratch(
                root.toString(), scratch, root.resolve("golden")));
        assertFalse(Files.exists(scratch));
    }

    @Test void existingEvidenceAndScratchAreNeverReused() throws IOException {
        Path scratch = root.resolve("scratch"), output = root.resolve("golden");
        Files.createFile(output);
        assertThrows(IOException.class, () -> CaptureLandContextGolden.prepareScratch(root.toString(), scratch, output));
        assertFalse(Files.exists(scratch));
        assertEquals(0L, Files.size(output));
        Files.createDirectory(scratch);
        assertThrows(IOException.class, () -> CaptureLandContextGolden.prepareScratch(
                root.toString(), scratch, root.resolve("other-golden")));
    }

    @Test void aliasesAndSameOutputScratchRejectBeforeWriting() {
        Path scratch = root.resolve("scratch");
        assertThrows(IOException.class, () -> CaptureLandContextGolden.prepareScratch(
                root.resolve(".").toString(), scratch, root.resolve("golden")));
        assertThrows(IOException.class, () -> CaptureLandContextGolden.prepareScratch(root.toString(), scratch, scratch));
        assertFalse(Files.exists(scratch));
    }

}
