package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;

/** Tiny real-file DATA regressions; no store/source issuer, Game or live transport is created. */
final class LedgerFilesRebindIsolation276Test {
    @TempDir Path temporary;

    private static ExactRef reference(Path file, byte[] bytes) {
        return new ExactRef(file.toAbsolutePath().normalize().toString(), bytes.length, LedgerFiles.sha(bytes));
    }

    @Test void exactRebindPreservesExpectedReferenceAndDefensiveCopiesAndRejectsChangedOriginal() throws IOException {
        byte[] bytes = "actual-exact-original".getBytes(StandardCharsets.UTF_8);
        Path file = temporary.resolve("exact.bin");
        Files.write(file, bytes, StandardOpenOption.CREATE_NEW);
        ExactRef expected = reference(file, bytes);
        LedgerFiles.Document actual = LedgerFiles.exact(expected, 1024);
        assertSame(expected, actual.pin().reference());
        assertArrayEquals(bytes, actual.bytes());

        byte[] returned = actual.bytes();
        returned[0] ^= 0x7f;
        assertArrayEquals(bytes, actual.bytes(), "same Document must not expose its internal array");

        // Ordinary constructor DATA only, using the actual file-derived Pin; not a qualified source.
        byte[] constructorInput = bytes.clone();
        LedgerFiles.Document detached = new LedgerFiles.Document(actual.pin(), constructorInput);
        constructorInput[1] ^= 0x3f;
        assertArrayEquals(bytes, detached.bytes(), "constructor defensive copy must remain");
        byte[] detachedReturn = detached.bytes();
        detachedReturn[2] ^= 0x3f;
        assertArrayEquals(bytes, detached.bytes(), "constructor and getter must both remain defensive");
        assertArrayEquals(bytes, actual.bytes(), "detached DATA must not mutate the real read result");

        assertThrows(IOException.class, () -> LedgerFiles.exact(expected, bytes.length - 1));
        byte[] changed = bytes.clone();
        changed[0] ^= 0x01;
        Files.write(file, changed, StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class, () -> LedgerFiles.exact(expected, 1024));
    }

    @Test void leasedRebindPreservesExpectedReferenceAndCurrentReadThenRejectsAfterClose() throws IOException {
        byte[] bytes = "actual-leased-original".getBytes(StandardCharsets.UTF_8);
        Path file = temporary.resolve("leased.bin");
        Files.write(file, bytes, StandardOpenOption.CREATE_NEW);
        ExactRef expected = reference(file, bytes);
        assertThrows(IOException.class, () -> LedgerFiles.lease(expected, bytes.length - 1));

        LedgerFiles.LeasedDocument lease = LedgerFiles.lease(expected, 1024);
        LedgerFiles.Document acquisition = lease.original();
        try (lease) {
            assertSame(expected, acquisition.pin().reference());
            assertArrayEquals(bytes, acquisition.bytes());
            byte[] returned = acquisition.bytes();
            returned[0] ^= 0x7f;
            assertArrayEquals(bytes, acquisition.bytes());

            LedgerFiles.Document current = lease.read();
            assertSame(acquisition, current);
            assertSame(expected, current.pin().reference());
            assertArrayEquals(bytes, current.bytes());
            byte[] currentReturn = current.bytes();
            currentReturn[1] ^= 0x3f;
            assertArrayEquals(bytes, lease.read().bytes());
        }
        assertThrows(IOException.class, lease::read);
        // Acquisition DATA may remain detached after close; it does not grant a current read.
        assertArrayEquals(bytes, acquisition.bytes());
        byte[] changed = bytes.clone();
        changed[0] ^= 0x01;
        Files.write(file, changed, StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class, () -> LedgerFiles.lease(expected, 1024));
    }
}
