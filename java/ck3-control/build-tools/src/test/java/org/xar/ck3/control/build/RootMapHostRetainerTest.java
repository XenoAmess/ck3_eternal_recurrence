package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class RootMapHostRetainerTest {
    @TempDir Path root;
    @Test void actualDelegatedProducerDeduplicatesAndRejectsConflictingSourcesAndContentDrift() throws IOException {
        Path path = root.resolve("source.txt"); Files.write(path, new byte[]{1,2,3});
        var ref = ControlBuild.FileRef.measure(path);
        var observed = RootMapHostRetainer.observeSources(List.of(List.of(ref), List.of(ref)));
        assertEquals(1, observed.size());
        assertThrows(IOException.class, () -> RootMapHostRetainer.observeSources(List.of(List.of(ref,
                new ControlBuild.FileRef(ref.path(), ref.bytes(), "0".repeat(64))))));
        Files.write(path, new byte[]{3,2,1});
        assertThrows(IOException.class, () -> SharedSourceFiles.assertUnchanged(observed.getFirst()));
    }
    @Test void sameBytesCannotHideReplacementOfActualDelegatedSourceIdentity() throws IOException {
        Path path = root.resolve("identity.txt"); Files.write(path, new byte[]{1,2,3});
        var observed = RootMapHostRetainer.observeSources(List.of(List.of(ControlBuild.FileRef.measure(path))));
        Files.delete(path); Files.write(path, new byte[]{1,2,3}, StandardOpenOption.CREATE_NEW);
        assertThrows(IOException.class, () -> SharedSourceFiles.assertUnchanged(observed.getFirst()));
    }
}
