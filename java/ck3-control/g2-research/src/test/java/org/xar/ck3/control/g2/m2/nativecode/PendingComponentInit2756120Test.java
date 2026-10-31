package org.xar.ck3.control.g2.m2.nativecode;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class PendingComponentInit2756120Test {
    @TempDir Path temporary;

    @Test void matchesTwoActuallyRecordedNativeRamCases() throws Exception {
        Path rows = temporary.resolve("native-rows186.tsv");
        try (InputStream original = Objects.requireNonNull(getClass().getResourceAsStream(
                "/m2-pending-component185/native-rows186.tsv"))) {
            Files.write(rows, original.readAllBytes());
        }
        PendingComponent185Consumer.main(new String[] { rows.toString() });
    }
}
