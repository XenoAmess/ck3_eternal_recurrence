package org.xar.ck3.control.contracts.source;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ReadLeaseContentRetirement312Test {
    @TempDir Path directory;

    @Test void retiredContentKeepsCustodyAndCurrentQualificationUntilClose() throws Exception {
        Path file = directory.resolve("retirement.bin");
        byte[] expected = {0, 1, -1, 42};
        Files.write(file, expected);
        try (var lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, expected.length)) {
            byte[] detached = lease.originalRead().bytes();
            detached[0] = 99;
            assertArrayEquals(expected, lease.read().bytes());
            lease.releaseOriginalBytes();
            lease.releaseOriginalBytes();
            assertEquals(expected.length, lease.verifyCurrent().size());
            assertTrue(assertThrows(IOException.class, lease::originalRead).getMessage().contains("retired"));
            assertTrue(assertThrows(IOException.class, lease::read).getMessage().contains("retired"));
            assertThrows(IOException.class, () -> Files.write(file, new byte[] {8},
                    StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING));
            assertThrows(IOException.class, () -> Files.delete(file));
            assertEquals(expected.length, lease.verifyCurrent().size());
        }
        Files.write(file, new byte[] {8}, StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING);
        assertArrayEquals(new byte[] {8}, Files.readAllBytes(file));
    }

    @Test void retiredContentStillRejectsMetadataDriftAndCannotRevive() throws Exception {
        Path file = directory.resolve("drift.bin");
        Files.write(file, new byte[] {1, 2, 3});
        try (var lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 3)) {
            FileTime original = lease.originalRead().attributes().lastModifiedTime();
            lease.releaseOriginalBytes();
            Files.setLastModifiedTime(file, FileTime.fromMillis(original.toMillis() + 2_000));
            assertThrows(IOException.class, lease::verifyCurrent);
            Files.setLastModifiedTime(file, original);
            assertThrows(IOException.class, lease::verifyCurrent);
            assertThrows(IOException.class, lease::releaseOriginalBytes);
        }
    }

    @Test void wrongThreadAndClosedLifetimeCannotRetireOwnersContent() throws Exception {
        Path file = directory.resolve("thread.bin");
        byte[] expected = {3, 1, 2};
        Files.write(file, expected);
        var lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, expected.length);
        try {
            AtomicReference<Throwable> observed = new AtomicReference<>();
            Thread foreign = new Thread(() -> {
                try { lease.releaseOriginalBytes(); }
                catch (Throwable problem) { observed.set(problem); }
            });
            foreign.start();
            foreign.join(5_000);
            assertFalse(foreign.isAlive());
            assertInstanceOf(IOException.class, observed.get());
            assertArrayEquals(expected, lease.originalRead().bytes());
            lease.close();
            assertThrows(IOException.class, lease::releaseOriginalBytes);
        } finally { lease.close(); }
    }
}
