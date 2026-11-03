package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.Closeable;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Independent raw Win32 facts for one owned software file; no Game or source qualification. */
final class SharedSourceFilesNativeInfoWitnessTest {
    @TempDir Path directory;

    @Test
    @SuppressWarnings("try") // Ownership-only resources preserve primary failures through suppressed cleanup errors.
    void fullIdAndReusedFactsMatchFreshRawInfoOnTheSameHandle() throws Exception {
        SharedSourceFiles.plainAncestors(directory);
        Path file = Files.createTempFile(directory, "independent-native-info-", ".bin");
        try (Closeable ownedFile = () -> { Files.deleteIfExists(file); }) {
            byte[] payload = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17};
            Files.write(file, payload, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE);
            Files.setLastModifiedTime(file, FileTime.fromMillis(1000));
            SharedSourceFiles.plainAncestors(file);
            Kernel32 kernel = Kernel32.INSTANCE;
            HANDLE handle = kernel.CreateFile(SharedSourceFiles.nativePath(file), 0x80, 7, null, 3, 0x00200000, null);
            if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle))
                throw new IOException("independent native-info open Win32=" + Native.getLastError());
            try (Closeable ownedHandle = () -> {
                if (!kernel.CloseHandle(handle))
                    throw new IOException("independent native-info close Win32=" + Native.getLastError());
            }; Memory id = new Memory(24); Memory basic = new Memory(40); Memory standard = new Memory(24)) {
                id.clear(); basic.clear(); standard.clear();
                SharedSourceFiles.AttributeApi raw = Native.load("kernel32", SharedSourceFiles.AttributeApi.class);
                if (!raw.GetFileInformationByHandleEx(handle, 18, id, 24))
                    throw new IOException("independent FileIdInfo Win32=" + Native.getLastError());
                if (!raw.GetFileInformationByHandleEx(handle, 0, basic, 40))
                    throw new IOException("independent FileBasicInfo Win32=" + Native.getLastError());
                if (!raw.GetFileInformationByHandleEx(handle, 1, standard, 24))
                    throw new IOException("independent FileStandardInfo Win32=" + Native.getLastError());

                // Positional unsigned arithmetic is independent of the production reverse-array loop.
                byte[] rawId = id.getByteArray(8, 16);
                BigInteger expectedId = BigInteger.ZERO;
                for (int index = 0; index < 16; index++)
                    expectedId = expectedId.add(BigInteger.valueOf(rawId[index] & 0xffL).shiftLeft(8 * index));
                assertEquals((long) payload.length, standard.getLong(8));

                SharedSourceFiles.NativeFile actual = SharedSourceFiles.nativeHeldFile(handle);
                assertEquals(expectedId.toString(), actual.fileIdDecimal());
                assertEquals(Long.toUnsignedString(basic.getLong(0)), actual.creationFiletimeDecimal());
                assertEquals(Long.toUnsignedString(basic.getLong(16)), actual.lastWriteFiletimeDecimal());
                assertEquals(standard.getLong(8), actual.logicalBytes());
                assertEquals(Integer.toUnsignedLong(standard.getInt(16)), actual.linkCount());
            }
        }
    }
}
