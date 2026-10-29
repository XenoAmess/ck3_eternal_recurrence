package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real Windows metadata regressions; UNC cases exercise spelling without accessing a network share. */
final class SharedSourceFilesNativePathTest {
    @TempDir Path directory;

    @Test void driveUncAndExistingExtendedSpellingsHaveOnePrefix() throws Exception {
        Path ordinary = directory.resolve("child").resolve("..").resolve("source.txt");
        assertEquals("\\\\?\\" + ordinary.toAbsolutePath().normalize(),
                SharedSourceFiles.nativePath(ordinary));
        String unc = "\\\\server\\share\\folder\\leaf.txt";
        assertEquals("\\\\?\\UNC\\server\\share\\folder\\leaf.txt",
                SharedSourceFiles.nativePath(Path.of(unc)));
        String extendedDrive = "\\\\?\\C:\\folder\\leaf.txt";
        String extendedUnc = "\\\\?\\UNC\\server\\share\\folder\\leaf.txt";
        assertEquals(extendedDrive, SharedSourceFiles.nativePathValue(extendedDrive));
        assertEquals(extendedUnc, SharedSourceFiles.nativePathValue(extendedUnc));
        assertEquals("\\\\?\\C:\\", SharedSourceFiles.nativePathValue("C:\\"));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativePath(Path.of("relative.txt")));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativePathValue("C:relative.txt"));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativePathValue("relative.txt"));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativePathValue("C:\\bad\0name"));
    }

    @Test void longLeafUsesAncestorAndHandleApisWithoutChangingItsIdentityOrBytes() throws Exception {
        Path parent = longDirectory("metadata");
        Path leaf = parent.resolve("actual-native-long-leaf.json");
        byte[] bytes = "{\"source\":\"long-native-metadata\"}\n".getBytes(StandardCharsets.UTF_8);
        Files.write(leaf, bytes);
        assertTrue(leaf.toString().length() > 260);
        SharedSourceFiles.plainAncestors(leaf);
        var directoryIdentity = SharedSourceFiles.nativeDirectory(parent);
        var before = SharedSourceFiles.observe(leaf);
        var nativeFile = SharedSourceFiles.nativeFile(leaf);
        assertEquals(before.nativeFile(), nativeFile);
        assertEquals(bytes.length, nativeFile.logicalBytes());
        assertArrayEquals(bytes, Files.readAllBytes(leaf));
        assertEquals(ControlBuild.FileRef.measure(leaf), before.source());
        assertEquals(before, SharedSourceFiles.observe(leaf));
        assertEquals(directoryIdentity, SharedSourceFiles.nativeDirectory(parent));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeDirectory(leaf));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeFile(parent));
    }

    @Test void longLinkedViewsStillKeepProtectedSiblingIdentityDuringPrivateReplacement() throws Exception {
        Path parent = longDirectory("linked");
        Path original = Files.writeString(parent.resolve("original.py"), "original = 1\n");
        var protectedSource = SharedSourceFiles.observe(original);
        Path consumer = parent.resolve("consumer/source.py");
        var linked = SharedSourceFiles.linkObserved(original, consumer);
        assertEquals(protectedSource.nativeFile().identityKey(), linked.destinationAfter().nativeFile().identityKey());
        SharedSourceFiles.assertUnchanged(protectedSource);
        Path privateRoot = Files.createDirectory(consumer.getParent().resolve(".assembly"));
        byte[] replacement = "consumer = 2\n".getBytes(StandardCharsets.UTF_8);
        var replaced = SharedSourceFiles.replacePrivate(consumer, privateRoot, replacement, List.of(protectedSource));
        assertNotEquals(protectedSource.nativeFile().identityKey(), replaced.nativeFile().identityKey());
        assertArrayEquals(replacement, Files.readAllBytes(consumer));
        SharedSourceFiles.assertUnchanged(protectedSource);
        assertEquals("original = 1\n", Files.readString(original));
    }

    @Test void heldDirectoryUsesTheSameNativeDecoderAndRejectsAFile() throws Exception {
        Path parent = Files.createDirectory(directory.resolve("held-native-directory"));
        var api = com.sun.jna.platform.win32.Kernel32.INSTANCE;
        var held = api.CreateFile(SharedSourceFiles.nativePath(parent), 0x80, 3, null, 3, 0x02200000, null);
        assertNotEquals(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE, held);
        var directoryHandle = held;
        try {
            var actual = SharedSourceFiles.nativeHeldDirectory(directoryHandle);
            assertEquals(SharedSourceFiles.nativeDirectory(parent), new SharedSourceFiles.DirectoryIdentity(
                    actual.volumeSerialDecimal(), actual.fileIdDecimal(), actual.creationFiletimeDecimal()));
            assertTrue(actual.allocatedBytes() >= 0); assertTrue(actual.linkCount() > 0);
            assertThrows(IOException.class, () -> SharedSourceFiles.nativeHeldFile(directoryHandle));
        } finally { assertTrue(api.CloseHandle(held)); }
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeHeldDirectory(null));
        Path leaf = Files.writeString(parent.resolve("file.txt"), "file");
        held = api.CreateFile(SharedSourceFiles.nativePath(leaf), 0x80, 3, null, 3, 0x00200000, null);
        var fileHandle = held;
        try { assertThrows(IOException.class, () -> SharedSourceFiles.nativeHeldDirectory(fileHandle)); }
        finally { assertTrue(api.CloseHandle(held)); }
    }

    @Test void heldSnapshotsStillRejectRealFileAndDirectoryRacesWithTypedFacts() throws Exception {
        Path parent = Files.createDirectory(directory.resolve("native-facts"));
        Path file = Files.write(parent.resolve("exact-file.bin"), new byte[1]);
        Files.setLastModifiedTime(file, java.nio.file.attribute.FileTime.fromMillis(1000));
        var api = com.sun.jna.platform.win32.Kernel32.INSTANCE;
        var handle = api.CreateFile(SharedSourceFiles.nativePath(file), 0x80, 7, null, 3, 0x00200000, null);
        assertNotEquals(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE, handle);
        try {
            var mismatch = assertThrows(SharedSourceFiles.NativeFactsChangedException.class,
                    () -> SharedSourceFiles.nativeHeldFile(handle, () -> Files.write(file, new byte[4096])));
            assertEquals(1, mismatch.standardFacts().logicalBytes());
            assertEquals(4096, mismatch.legacyFacts().logicalBytes());
            assertTrue(mismatch.onlyMutableFactsChanged());
            assertEquals(mismatch.standardFacts().creationFiletimeDecimal(), mismatch.legacyFacts().creationFiletimeDecimal());
            assertEquals(4096, SharedSourceFiles.nativeHeldFile(handle).logicalBytes());
        } finally { assertTrue(api.CloseHandle(handle)); }

        Files.setLastModifiedTime(parent, java.nio.file.attribute.FileTime.fromMillis(1000));
        var heldDirectory = api.CreateFile(SharedSourceFiles.nativePath(parent), 0x80, 7, null, 3, 0x02200000, null);
        assertNotEquals(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE, heldDirectory);
        try {
            var mismatch = assertThrows(SharedSourceFiles.NativeFactsChangedException.class,
                    () -> SharedSourceFiles.nativeHeldDirectory(heldDirectory,
                            () -> Files.write(parent.resolve("new-entry.bin"), new byte[1])));
            assertTrue(mismatch.onlyMutableFactsChanged());
            assertNotEquals(mismatch.standardFacts().lastWriteFiletimeDecimal(), mismatch.legacyFacts().lastWriteFiletimeDecimal());
            assertEquals(SharedSourceFiles.nativeDirectory(parent).fileIdDecimal(),
                    SharedSourceFiles.nativeHeldDirectory(heldDirectory).fileIdDecimal());
        } finally { assertTrue(api.CloseHandle(heldDirectory)); }
    }

    private Path longDirectory(String label) throws IOException {
        Path path = directory.resolve(label);
        while (path.toString().length() < 310) path = path.resolve("ordinary-native-source-path-segment");
        return Files.createDirectories(path);
    }
    @Test void heldDeletePendingEntriesStayStrictAndCarryExactTypedFlags() throws Exception {
        Path path = Files.write(directory.resolve("held-delete-pending.bin"), new byte[4096]);
        var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path),
                0x80, 7, null, 3, 0x00200000, null);
        assertNotEquals(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE, handle);
        try {
            assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.DeleteFile(SharedSourceFiles.nativePath(path)));
            var failure = assertThrows(SharedSourceFiles.NativeEntryStateException.class,
                    () -> SharedSourceFiles.nativeHeldFile(handle));
            assertTrue(failure.state().onlyDeletePending()); assertFalse(failure.state().directory());
            assertFalse(failure.state().reparse()); assertFalse(failure.state().expectedDirectory());
            assertTrue(failure.getMessage().startsWith("ordinary non-reparse non-delete-pending source required"));
        } finally {
            assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle));
        }
        assertThrows(IllegalArgumentException.class, () -> new SharedSourceFiles.NativeEntryStateException(
                new SharedSourceFiles.NativeEntryState(false, false, false, false)));
    }

}

