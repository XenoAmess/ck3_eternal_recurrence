package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real owned Win32 directories; mutable identity grants no immutable source authority. */
final class SharedSourceFilesMutableDirectoryIdentityTest {
    @TempDir Path directory;

    @Test void actualMutableDirectoryIdentitySurvivesTimestampAndChildChanges() throws Exception {
        Path scratch = Files.createDirectory(directory.resolve("scratch"));
        FileTime beforeTime = Files.getLastModifiedTime(scratch);
        var before = SharedSourceFiles.nativeMutableDirectoryIdentity(scratch);
        var duringMutation = SharedSourceFiles.nativeMutableDirectoryIdentity(scratch, () -> {
            Files.write(scratch.resolve("new-child.bin"), new byte[] {1, 2, 3});
            Files.setLastModifiedTime(scratch, FileTime.fromMillis(beforeTime.toMillis() + 30_000));
        });
        assertNotEquals(beforeTime, Files.getLastModifiedTime(scratch));
        assertEquals(before, duringMutation);
        assertEquals(before, SharedSourceFiles.nativeMutableDirectoryIdentity(scratch));

        HANDLE handle = openDirectory(scratch);
        try (Memory id = new Memory(24); Memory basic = new Memory(40)) {
            SharedSourceFiles.AttributeApi raw = Native.load("kernel32", SharedSourceFiles.AttributeApi.class);
            if (!raw.GetFileInformationByHandleEx(handle, 18, id, 24)
                    || !raw.GetFileInformationByHandleEx(handle, 0, basic, 40))
                throw new IOException("independent mutable identity Win32=" + Native.getLastError());
            BigInteger expectedId = BigInteger.ZERO;
            for (int index = 0; index < 16; index++)
                expectedId = expectedId.add(BigInteger.valueOf(id.getByte(8 + index) & 0xffL).shiftLeft(8 * index));
            assertEquals(Long.toUnsignedString(id.getLong(0)), before.volumeSerialDecimal());
            assertEquals(expectedId.toString(), before.fileIdDecimal());
            assertEquals(Long.toUnsignedString(basic.getLong(0)), before.creationFiletimeDecimal());
        } finally { closeDirectory(handle); }
    }

    @Test void immutableDirectoryWitnessStillRejectsAnActualTimestampChange() throws Exception {
        Path source = Files.createDirectory(directory.resolve("immutable-source"));
        HANDLE handle = openDirectory(source);
        try {
            var failure = assertThrows(SharedSourceFiles.NativeFactsChangedException.class,
                    () -> SharedSourceFiles.nativeHeldDirectory(handle, () ->
                            Files.setLastModifiedTime(source, FileTime.fromMillis(
                                    Files.getLastModifiedTime(source).toMillis() + 30_000))));
            assertTrue(failure.onlyMutableFactsChanged());
            assertNotEquals(failure.standardFacts().lastWriteFiletimeDecimal(),
                    failure.legacyFacts().lastWriteFiletimeDecimal());
            assertEquals(failure.standardFacts().creationFiletimeDecimal(),
                    failure.legacyFacts().creationFiletimeDecimal());
        } finally { closeDirectory(handle); }
    }

    @Test void filesAndMissingPathsCannotBecomeMutableDirectoryIdentities() throws Exception {
        Path file = Files.write(directory.resolve("ordinary-file.bin"), new byte[] {1});
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeMutableDirectoryIdentity(file));
        Path absent = directory.resolve("absent-directory");
        assertFalse(Files.exists(absent));
        assertThrows(IOException.class, () -> SharedSourceFiles.nativeMutableDirectoryIdentity(absent));
    }

    private static HANDLE openDirectory(Path path) throws IOException {
        HANDLE handle = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path),
                0x80, 7, null, 3, 0x00200000 | 0x02000000, null);
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle))
            throw new IOException("independent directory open Win32=" + Native.getLastError());
        return handle;
    }

    private static void closeDirectory(HANDLE handle) throws IOException {
        if (!Kernel32.INSTANCE.CloseHandle(handle))
            throw new IOException("independent directory close Win32=" + Native.getLastError());
    }
}
