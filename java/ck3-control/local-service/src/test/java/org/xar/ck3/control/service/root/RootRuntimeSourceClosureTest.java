package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Actual native file-identity regressions: unavailable Windows metadata must fail, never skip as PASS. */
class RootRuntimeSourceClosureTest {
    @TempDir Path directory;

    @Test void retainsMeasuredProducerAndDeduplicatesRepeatedConsumerReference() throws IOException {
        Path source = Files.writeString(directory.resolve("producer.java"), "actual producer source");
        FileRef reference = FileRef.measure(source);
        var retained = RootRuntimeSourceClosure.captureReferences(List.of(reference, reference), List.of());
        assertEquals(1, retained.retainedInputCount());
        assertDoesNotThrow(retained::requireCurrent);
    }

    @Test void sameBytesAtAnotherFileIdentityCannotReplaceThePreparedProducer() throws IOException {
        Path source = Files.writeString(directory.resolve("producer.java"), "immutable body");
        var retained = RootRuntimeSourceClosure.captureReferences(List.of(FileRef.measure(source)), List.of());
        Path replacement = Files.writeString(directory.resolve("replacement.java"), "immutable body");
        Files.setLastModifiedTime(replacement, Files.getLastModifiedTime(source));
        Files.move(replacement, source, StandardCopyOption.REPLACE_EXISTING);
        assertThrows(IOException.class, retained::requireCurrent);
    }

    @Test void sourceContentMutationCannotSurviveTheNextAdmission() throws IOException {
        Path source = Files.writeString(directory.resolve("producer.java"), "original body");
        var retained = RootRuntimeSourceClosure.captureReferences(List.of(FileRef.measure(source)), List.of());
        Files.writeString(source, "modified body");
        assertThrows(IOException.class, retained::requireCurrent);
    }

    @Test void conflictingConfiguredReferencesRefuseBeforeMintingCustody() throws IOException {
        Path source = Files.writeString(directory.resolve("producer.java"), "original body");
        FileRef original = FileRef.measure(source);
        Files.writeString(source, "modified body");
        FileRef changed = FileRef.measure(source);
        assertThrows(IOException.class,
                () -> RootRuntimeSourceClosure.captureReferences(List.of(original, changed), List.of()));
    }

    @Test void explicitHistoryAbsenceRemainsDifferentFromNewHistory() throws IOException {
        Path source = Files.writeString(directory.resolve("producer.java"), "actual body");
        Path absent = directory.resolve("one-life-history.json");
        var retained = RootRuntimeSourceClosure.captureReferences(List.of(FileRef.measure(source)), List.of(absent));
        assertDoesNotThrow(retained::requireCurrent);
        Files.writeString(absent, "{}");
        assertThrows(IOException.class, retained::requireCurrent);
    }

    @Test void mismatchedProducerBytesOrPresentAbsentConflictCannotQualify() throws IOException {
        Path source = Files.writeString(directory.resolve("producer.java"), "actual body");
        FileRef original = FileRef.measure(source);
        FileRef wrong = new FileRef(original.path(), original.bytes(), "0".repeat(64));
        assertThrows(IOException.class, () -> RootRuntimeSourceClosure.captureReferences(List.of(wrong), List.of()));
        assertThrows(IOException.class, () -> RootRuntimeSourceClosure.captureReferences(List.of(original), List.of(source)));
        assertThrows(IOException.class, () -> RootRuntimeSourceClosure.captureReferences(List.of(), List.of()));
    }
}
