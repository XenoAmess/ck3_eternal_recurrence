package org.xar.ck3.control.contracts.source;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.platform.win32.Kernel32;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class IdentityBearingFileAttributesLongPathTest {
    @TempDir Path temporary;
    @Test void nativeDriveUncAndExistingExtendedFormsAreEncodedExactlyOnce() {
        assertEquals("\\\\?\\D:\\source\\file", IdentityBearingFileAttributes.nativePath("D:\\source\\file"));
        assertEquals("\\\\?\\UNC\\server\\share\\file", IdentityBearingFileAttributes.nativePath("\\\\server\\share\\file"));
        assertEquals("\\\\?\\D:\\source\\file", IdentityBearingFileAttributes.nativePath("\\\\?\\D:\\source\\file"));
        assertEquals("\\\\?\\UNC\\server\\share\\file", IdentityBearingFileAttributes.nativePath("\\\\?\\UNC\\server\\share\\file"));
        assertThrows(IllegalArgumentException.class, () -> IdentityBearingFileAttributes.nativePath("relative\\file"));
        assertThrows(IllegalArgumentException.class, () -> IdentityBearingFileAttributes.nativePath("\\\\.\\PhysicalDrive0"));
        assertThrows(IllegalArgumentException.class, () -> IdentityBearingFileAttributes.nativePath("\\\\?\\GLOBALROOT\\Device"));
    }
    @Test void actualLongFileUsesTheSameAttributesAndNativeIdentityThroughBothPathForms() throws IOException {
        Path directory = Files.createDirectories(temporary.resolve("a".repeat(80)).resolve("b".repeat(80)).resolve("c".repeat(80)).resolve("d".repeat(80)));
        Path file = Files.writeString(directory.resolve("source.txt"), "source bytes beyond MAX_PATH");
        assertTrue(file.toString().length() > 260);
        var ordinary = IdentityBearingFileAttributes.read(file);
        assertTrue(ordinary.isRegularFile()); assertNotNull(ordinary.fileKey());
        assertEquals(ordinary.fileKey(), IdentityBearingFileAttributes.read(file).fileKey());
        if (Platform.isWindows()) {
            var wholePath = IdentityBearingFileAttributes.readWithOrdinaryParents(file);
            assertEquals(ordinary.fileKey(), wholePath.fileKey());
            assertEquals(ordinary.lastModifiedTime(), wholePath.lastModifiedTime());
            Native.setLastError(0);
            int plain = Kernel32.INSTANCE.GetFileAttributes(file.toString()); int plainError = Native.getLastError();
            Native.setLastError(0);
            String extended = IdentityBearingFileAttributes.nativePath(file.toString());
            int exact = Kernel32.INSTANCE.GetFileAttributes(extended); int exactError = Native.getLastError();
            System.out.println("NATIVE_LONG_PATH length=" + file.toString().length() + " plain_attributes=" + plain
                + " plain_win32_error=" + plainError + " extended_attributes=" + exact + " extended_win32_error=" + exactError
                + " native_identity=" + ordinary.fileKey());
            assertNotEquals(-1, exact, "extended metadata entry must work on this actual file");
            assertEquals(ordinary.fileKey(), IdentityBearingFileAttributes.read(Path.of(extended)).fileKey());
            assertEquals(ordinary.lastModifiedTime(), IdentityBearingFileAttributes.read(Path.of(extended)).lastModifiedTime());
            assertEquals(ordinary.fileKey(), IdentityBearingFileAttributes.readWithOrdinaryParents(Path.of(extended)).fileKey());
        }
    }
    @Test void sameBytesSameMtimeLongPathReplacementHasANewIdentity() throws IOException {
        Path directory = Files.createDirectories(temporary.resolve("c".repeat(80)).resolve("d".repeat(80)).resolve("e".repeat(80)).resolve("f".repeat(80)));
        Path file = Files.writeString(directory.resolve("source.txt"), "same bytes");
        var original = IdentityBearingFileAttributes.read(file);
        Path replacement = Files.writeString(directory.resolve("replacement.txt"), "same bytes");
        Files.setLastModifiedTime(replacement, original.lastModifiedTime());
        Files.move(replacement, file, StandardCopyOption.REPLACE_EXISTING);
        var changed = IdentityBearingFileAttributes.read(file);
        assertEquals(original.size(), changed.size()); assertEquals(original.lastModifiedTime(), changed.lastModifiedTime());
        assertNotEquals(original.fileKey(), changed.fileKey());
        if (Platform.isWindows()) {
            assertEquals(changed.fileKey(), IdentityBearingFileAttributes.readWithOrdinaryParents(file).fileKey());
            assertNotEquals(original.fileKey(), IdentityBearingFileAttributes.readWithOrdinaryParents(file).fileKey());
        }
        assertNotNull(IdentityBearingFileAttributes.read(directory).fileKey());
    }
}

