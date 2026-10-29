package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual held Win32 digest regression for the observed prelaunch full-guard amplification. */
final class MsvcImageGuardScheduleTest {
    @TempDir Path temporary;

    @Test void completeSourceChecksDoNotRepeatForEvery64KiBImageChunk() throws IOException {
        Path image = image("digest.exe");
        var original = ControlBuild.FileRef.measure(image);
        var identity = SharedSourceFiles.observe(image);
        var checks = new AtomicInteger();
        long start = System.nanoTime();
        var actual = MsvcAuxiliaryPolicy.observeImage(image, Instant.now().plusSeconds(30), () -> {
            checks.incrementAndGet();
            try { original.verify(); }
            catch (IOException failure) { throw new IllegalStateException(failure); }
        });
        long elapsed = System.nanoTime() - start;
        assertEquals(original.bytes(), actual.bytes());
        assertEquals(original.sha256(), actual.sha256());
        assertEquals(identity.nativeFile().volumeSerialDecimal(), actual.volumeSerialDecimal());
        assertEquals(identity.nativeFile().fileIdDecimal(), actual.fileIdDecimal());
        SharedSourceFiles.assertUnchanged(identity);
        assertTrue(checks.get() >= 2, "Complete source checks are required before and after the digest");
        assertTrue(checks.get() <= 2 + TimeUnit.NANOSECONDS.toSeconds(elapsed),
                "Full source checks must follow elapsed one-second periods, not 64KiB read count: " + checks.get());
        System.out.println("MSVC_IMAGE_GUARD bytes=" + original.bytes() + " fullChecks=" + checks.get() + " elapsedNanos=" + elapsed);
    }

    @Test void finalCompleteSourceFailureRejectsTheDigestAndClosesItsImage() throws IOException {
        Path image = image("guard-failure.exe");
        var checks = new AtomicInteger();
        var failure = assertThrows(IllegalStateException.class, () -> MsvcAuxiliaryPolicy.observeImage(
                image, Instant.now().plusSeconds(30), () -> {
                    if (checks.incrementAndGet() == 2) throw new IllegalStateException("actual complete source guard rejected");
                }));
        assertEquals("actual complete source guard rejected", failure.getMessage());
        assertEquals(2, checks.get());
        Files.writeString(image, "image handle released after guard rejection");
        Files.delete(image);
    }

    @Test void cancellationDuringHeldObservationIsPreservedAndClosesItsImage() throws IOException {
        Path image = image("cancel.exe");
        var checks = new AtomicInteger();
        try {
            var failure = assertThrows(IOException.class, () -> MsvcAuxiliaryPolicy.observeImage(
                    image, Instant.now().plusSeconds(30), () -> {
                        if (checks.incrementAndGet() == 2) Thread.currentThread().interrupt();
                    }));
            assertTrue(failure.getMessage().contains("interrupted"));
            assertTrue(Thread.currentThread().isInterrupted(), "The production reader must preserve cancellation");
        } finally { Thread.interrupted(); }
        Files.writeString(image, "image handle released after cancellation");
        Files.delete(image);
    }

    private Path image(String name) throws IOException {
        Path result = temporary.resolve(name);
        byte[] block = new byte[65536];
        for (int index = 0; index < block.length; index++) block[index] = (byte) index;
        try (var output = Files.newOutputStream(result)) {
            for (int index = 0; index < 64; index++) output.write(block);
        }
        return result;
    }
}
