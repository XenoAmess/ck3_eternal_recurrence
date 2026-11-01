package org.xar.ck3.control.contracts.source;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.time.Instant;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import com.sun.jna.Platform;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class BoundedFileRead219Test {
    @TempDir Path temporary;

    private static void assertWindows() {
        assertTrue(Platform.isWindows(), "Windows native identity required");
    }

    private static byte[] deterministicPayload(int length) {
        byte[] payload = new byte[length];
        for (int index = 0; index < length; index++) {
            payload[index] = (byte) (index * 31 + (index >>> 8) * 17 + (index >>> 16) * 73 + 7);
        }
        return payload;
    }

    @Test void largePatternAndCompatibleReadHandle() throws Exception {
        assertWindows();
        Path file = temporary.resolve("large-pattern.bin");
        byte[] expected = deterministicPayload(150_003);
        Files.write(file, expected, StandardOpenOption.CREATE_NEW);

        String nativePath = IdentityBearingFileAttributes.nativePath(file.toString());
        HANDLE compatible = Kernel32.INSTANCE.CreateFile(nativePath, 0x80000000, 7, null, 3, 0x02200000, null);
        assertNotNull(compatible);
        assertFalse(WinBase.INVALID_HANDLE_VALUE.equals(compatible));

        try {
            IdentityBearingFileAttributes.BoundedFileRead read = IdentityBearingFileAttributes.readBoundedWindows(file, expected.length);
            assertArrayEquals(expected, read.bytes());
            assertEquals(expected.length, read.attributes().size());
            assertTrue(read.attributes().isRegularFile());
            assertFalse(read.attributes().isSymbolicLink());
            assertFalse(read.attributes().isDirectory());

            BasicFileAttributes mature = IdentityBearingFileAttributes.read(file);
            assertEquals(mature.fileKey(), read.attributes().fileKey());
            assertInstanceOf(IdentityBearingFileAttributes.WindowsFileIdentity.class, read.attributes().fileKey());
            assertEquals(mature.size(), read.attributes().size());
            assertEquals(mature.lastModifiedTime(), read.attributes().lastModifiedTime());
            assertEquals(mature.creationTime(), read.attributes().creationTime());

            byte[] mutated = read.bytes();
            mutated[0] = (byte) ~mutated[0];
            IdentityBearingFileAttributes.BoundedFileRead second = IdentityBearingFileAttributes.readBoundedWindows(file, expected.length);
            assertArrayEquals(expected, second.bytes());
            assertNotSame(mutated, second.bytes());
        } finally {
            assertTrue(Kernel32.INSTANCE.CloseHandle(compatible));
        }
    }

    @Test void finiteBoundaries() throws Exception {
        assertWindows();
        Path empty = temporary.resolve("empty.bin");
        Files.write(empty, new byte[0], StandardOpenOption.CREATE_NEW);
        IdentityBearingFileAttributes.BoundedFileRead emptyRead = IdentityBearingFileAttributes.readBoundedWindows(empty, 0);
        assertEquals(0, emptyRead.bytes().length);

        Path small = temporary.resolve("small.bin");
        byte[] payload = deterministicPayload(128);
        Files.write(small, payload, StandardOpenOption.CREATE_NEW);
        assertArrayEquals(payload, IdentityBearingFileAttributes.readBoundedWindows(small, payload.length).bytes());
        assertArrayEquals(payload, IdentityBearingFileAttributes.readBoundedWindows(small, payload.length + 1).bytes());

        assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(small, payload.length - 1));
        assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(small, -1));

        Path missing = temporary.resolve("missing.bin");
        assertThrows(NoSuchFileException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(missing, 10));

        Path directory = Files.createDirectory(temporary.resolve("directory"));
        assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(directory, 10));

        assertThrows(IllegalArgumentException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(small, Integer.MAX_VALUE));
    }

    @Test void realReplacementAndCleanDeleteAfterContent() throws Exception {
        assertWindows();
        Path file = temporary.resolve("replacement.bin");
        byte[] payload = deterministicPayload(1024);
        Files.write(file, payload, StandardOpenOption.CREATE_NEW);
        BasicFileAttributes before = IdentityBearingFileAttributes.read(file);
        FileTime originalMtime = before.lastModifiedTime();

        AtomicBoolean callbackRan = new AtomicBoolean(false);
        IOException replacementFailure = assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(file, payload.length, (HANDLE handle) -> {
            try {
                Path retained = temporary.resolve("retained.bin");
                Files.move(file, retained, StandardCopyOption.REPLACE_EXISTING);
                Files.write(file, payload, StandardOpenOption.CREATE_NEW);
                Files.setLastModifiedTime(file, originalMtime);
                callbackRan.set(true);
            } catch (IOException failure) {
                throw new UncheckedIOException(failure);
            }
        }));
        assertTrue(callbackRan.get());
        assertFalse(replacementFailure instanceof NoSuchFileException);

        BasicFileAttributes after = IdentityBearingFileAttributes.read(file);
        assertEquals(before.size(), after.size());
        assertEquals(before.lastModifiedTime(), after.lastModifiedTime());
        assertNotEquals(before.fileKey(), after.fileKey());
        var beforeKey = assertInstanceOf(IdentityBearingFileAttributes.WindowsFileIdentity.class, before.fileKey());
        var afterKey = assertInstanceOf(IdentityBearingFileAttributes.WindowsFileIdentity.class, after.fileKey());
        assertEquals(beforeKey.volumeSerialDecimal(), afterKey.volumeSerialDecimal());
        assertNotEquals(beforeKey.fileIdDecimal(), afterKey.fileIdDecimal());

        Path deleteFile = temporary.resolve("delete.bin");
        Files.write(deleteFile, payload, StandardOpenOption.CREATE_NEW);
        AtomicBoolean deleted = new AtomicBoolean(false);
        assertThrows(NoSuchFileException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(deleteFile, payload.length, (HANDLE handle) -> {
            try {
                Files.delete(deleteFile);
                deleted.set(true);
            } catch (IOException failure) {
                throw new UncheckedIOException(failure);
            }
        }));
        assertTrue(deleted.get());
        assertFalse(Files.exists(deleteFile, LinkOption.NOFOLLOW_LINKS));
    }

    @Test void realCloseAbsenceDoubleFailure() throws Exception {
        assertWindows();
        Path file = temporary.resolve("close-absence.bin");
        byte[] payload = deterministicPayload(64);
        Files.write(file, payload, StandardOpenOption.CREATE_NEW);

        AtomicBoolean closed = new AtomicBoolean(false);
        AtomicBoolean deleted = new AtomicBoolean(false);
        IOException error = assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readBoundedWindows(file, payload.length, (HANDLE handle) -> {
            closed.set(Kernel32.INSTANCE.CloseHandle(handle));
            try {
                Files.delete(file);
                deleted.set(true);
            } catch (IOException failure) {
                throw new UncheckedIOException(failure);
            }
        }));
        assertTrue(closed.get());
        assertTrue(deleted.get());
        assertFalse(error instanceof NoSuchFileException);
        assertFalse(Files.exists(file, LinkOption.NOFOLLOW_LINKS));
    }

    @Test void longPathAndParentJunctionCompatibility() throws Exception {
        assertWindows();
        Path deep = temporary.resolve("a".repeat(80)).resolve("b".repeat(80)).resolve("c".repeat(80)).resolve("d".repeat(80));
        Files.createDirectories(deep);
        Path file = deep.resolve("source.bin");
        byte[] payload = deterministicPayload(256);
        Files.write(file, payload, StandardOpenOption.CREATE_NEW);
        assertTrue(file.toString().length() > 260);

        IdentityBearingFileAttributes.BoundedFileRead ordinary = IdentityBearingFileAttributes.readBoundedWindows(file, payload.length);
        assertArrayEquals(payload, ordinary.bytes());
        String extended = IdentityBearingFileAttributes.nativePath(file.toString());
        IdentityBearingFileAttributes.BoundedFileRead extendedRead = IdentityBearingFileAttributes.readBoundedWindows(Path.of(extended), payload.length);
        assertArrayEquals(payload, extendedRead.bytes());
        assertEquals(ordinary.attributes().fileKey(), extendedRead.attributes().fileKey());

        Path junctionTarget = Files.createDirectory(temporary.resolve("junction-target"));
        Path junctionSource = junctionTarget.resolve("source.bin");
        Files.write(junctionSource, payload, StandardOpenOption.CREATE_NEW);
        BasicFileAttributes junctionMature = IdentityBearingFileAttributes.read(junctionSource);
        Path junction = temporary.resolve("junction");
        Process process = new ProcessBuilder("cmd.exe", "/d", "/c", "mklink", "/J", junction.toString(), junctionTarget.toString())
                .redirectErrorStream(true).start();
        try {
            assertTrue(process.waitFor(10, TimeUnit.SECONDS), "junction creation timed out");
            assertEquals(0, process.exitValue(), new String(process.getInputStream().readNBytes(8192), java.nio.charset.StandardCharsets.UTF_8));
            assertTrue(Files.isSameFile(junctionTarget, junction));
            int junctionAttributes = Kernel32.INSTANCE.GetFileAttributes(IdentityBearingFileAttributes.nativePath(junction.toString()));
            assertNotEquals(-1, junctionAttributes);
            assertEquals(0x410, junctionAttributes & 0x410);
            Path viaJunction = junction.resolve("source.bin");
            IdentityBearingFileAttributes.BoundedFileRead throughJunction = IdentityBearingFileAttributes.readBoundedWindows(viaJunction, payload.length);
            assertArrayEquals(payload, throughJunction.bytes());
            assertEquals(junctionMature.fileKey(), throughJunction.attributes().fileKey());
            assertThrows(IOException.class, () -> IdentityBearingFileAttributes.readWithOrdinaryParents(viaJunction));
        } finally {
            if (process.isAlive()) {
                process.destroyForcibly();
                assertTrue(process.waitFor(5, TimeUnit.SECONDS), "owned junction process did not terminate");
            }
            Files.deleteIfExists(junction);
        }
    }
}