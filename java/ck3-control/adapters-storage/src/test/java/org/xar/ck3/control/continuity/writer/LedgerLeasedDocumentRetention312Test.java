package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;

final class LedgerLeasedDocumentRetention312Test {
    @TempDir Path directory;

    @Test void retainedDocumentKeepsDetachedBytesAndFreshChecksAfterRetirement() throws Exception {
        Path file = directory.resolve("document.bin");
        byte[] expected = {0, 9, 8, 7, -1};
        Files.write(file, expected);
        LedgerFiles.LeasedDocument lease = LedgerFiles.lease(file, expected.length);
        try {
            LedgerFiles.Document document = lease.original();
            assertEquals(expected.length, lease.retainedBytes());
            byte[] detached = document.bytes();
            detached[1] = 0;
            assertArrayEquals(expected, document.bytes());
            assertSame(document, lease.read());
            assertArrayEquals(expected, lease.read().bytes());
            assertThrows(IOException.class, () -> Files.write(file, new byte[] {5}));
        } finally { lease.close(); }
        assertThrows(IOException.class, lease::read);
        Files.write(file, new byte[] {5});
        assertArrayEquals(new byte[] {5}, Files.readAllBytes(file));
    }

    @Test void exactReferenceWrapperKeepsOneDocumentAndMismatchClosesCustody() throws Exception {
        Path file = directory.resolve("exact.bin");
        byte[] expected = {3, 1, 2, -1};
        Files.write(file, expected);
        ExactRef reference = new ExactRef(file.toAbsolutePath().normalize().toString(), expected.length,
                LedgerFiles.sha(expected));
        try (LedgerFiles.LeasedDocument lease = LedgerFiles.lease(reference, expected.length)) {
            assertEquals(reference, lease.original().pin().reference());
            assertEquals(expected.length, lease.retainedBytes());
            byte[] detached = lease.original().bytes();
            detached[0] = 9;
            assertArrayEquals(expected, lease.read().bytes());
        }
        ExactRef wrong = new ExactRef(reference.path(), reference.bytes(), "0".repeat(64));
        assertThrows(IOException.class, () -> {
            try (LedgerFiles.LeasedDocument unexpected = LedgerFiles.lease(wrong, expected.length)) {
                fail("mismatched reference granted custody");
            }
        });
        Files.write(file, new byte[] {9});
        assertArrayEquals(new byte[] {9}, Files.readAllBytes(file));
    }
}
