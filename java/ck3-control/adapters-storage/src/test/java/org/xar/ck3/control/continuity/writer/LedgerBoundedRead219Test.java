package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.continuity.writer.WriterContracts.Pin;
import com.sun.jna.Platform;

final class LedgerBoundedRead219Test {
    @TempDir Path temporary;

    private static String sha(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }

    @Test void largeNonuniformReadIdentityAndExactRef() throws Exception {
        assertTrue(Platform.isWindows(), "Windows required");
        Path file = temporary.resolve("large.bin");
        int length = 70_013;
        byte[] content = new byte[length];
        for (int i = 0; i < length; i++) content[i] = (byte) ((i * 73) ^ (i >>> 7) ^ (i >>> 16));
        Files.write(file, content);

        var doc = LedgerFiles.read(file, length);
        assertArrayEquals(content, doc.bytes());
        assertEquals(length, doc.pin().reference().bytes());
        assertEquals(sha(content), doc.pin().reference().sha256());
        assertEquals(file.toAbsolutePath().normalize().toString(), doc.pin().reference().path());

        var ibfa = IdentityBearingFileAttributes.read(file);
        var nativeKey = (IdentityBearingFileAttributes.WindowsFileIdentity) ibfa.fileKey();
        var identity = doc.pin().identity();
        assertEquals(nativeKey.volumeSerialDecimal(), identity.volumeSerialDecimal());
        assertEquals(nativeKey.fileIdDecimal(), identity.fileIdDecimal());
        assertEquals(nativeKey.creationFiletimeDecimal(), identity.creationFiletimeDecimal());
        assertEquals(ibfa.lastModifiedTime().toInstant().toString(), identity.modifiedInstant());
        assertEquals(ibfa.size(), identity.bytes());

        var ref = new ExactRef(file.toAbsolutePath().normalize().toString(), length, sha(content));
        var exactDoc = LedgerFiles.exact(ref, length);
        assertArrayEquals(content, exactDoc.bytes());
        assertEquals(ref, exactDoc.pin().reference());

        var wrongSha = new ExactRef(ref.path(), ref.bytes(), "0".repeat(64));
        assertNotEquals(ref.sha256(), wrongSha.sha256());
        assertThrows(IOException.class, () -> LedgerFiles.exact(wrongSha, length));
        var wrongCount = new ExactRef(ref.path(), length - 1, ref.sha256());
        assertThrows(IOException.class, () -> LedgerFiles.exact(wrongCount, length));
    }

    @Test void optionalMissingEmptyAndDirectoryReject() throws Exception {
        assertTrue(Platform.isWindows(), "Windows required");
        Path missing = temporary.resolve("missing.json");
        assertTrue(LedgerFiles.optional(missing).isEmpty());

        Path dir = Files.createDirectory(temporary.resolve("dir"));
        assertThrows(IOException.class, () -> LedgerFiles.optional(dir));
    }

    @Test void capBoundsAndEmpty() throws Exception {
        assertTrue(Platform.isWindows(), "Windows required");
        Path file = temporary.resolve("cap.txt");
        Files.write(file, new byte[]{1, 2, 3});
        assertThrows(IOException.class, () -> LedgerFiles.read(file, 2));
        assertThrows(IOException.class, () -> LedgerFiles.read(file, -1));

        Path empty = temporary.resolve("empty.txt");
        Files.write(empty, new byte[]{});
        var doc = LedgerFiles.read(empty, 0);
        assertEquals(0, doc.bytes().length);
        assertEquals(0, doc.pin().reference().bytes());
    }

    @Test void defensiveCopiesAndPinStability() throws Exception {
        assertTrue(Platform.isWindows(), "Windows required");
        Path file = temporary.resolve("copy.txt");
        byte[] original = new byte[]{10, 20, 30};
        Files.write(file, original);

        var doc = LedgerFiles.read(file, 100);
        Pin originalPin = doc.pin();
        var bytes1 = doc.bytes();
        var bytes2 = doc.bytes();
        assertNotSame(bytes1, bytes2);
        assertArrayEquals(bytes1, bytes2);
        assertArrayEquals(original, bytes1);

        bytes1[0] = 99;
        assertNotEquals(99, doc.bytes()[0]);
        assertEquals(10, doc.bytes()[0]);
        assertEquals(original.length, doc.pin().reference().bytes());
        assertEquals(sha(original), doc.pin().reference().sha256());
        assertArrayEquals(original, doc.bytes());
        assertSame(originalPin, doc.pin());

        byte[] constructorInput = original.clone();
        var constructed = new LedgerFiles.Document(originalPin, constructorInput);
        constructorInput[0] = 99;
        assertArrayEquals(original, constructed.bytes());
        assertSame(originalPin, constructed.pin());
        byte[] constructorReturned = constructed.bytes();
        constructorReturned[1] = 88;
        assertArrayEquals(original, constructed.bytes());
    }

    @Test void replacementSameBytesMtimeDistinctIdRejectsOldPin() throws Exception {
        assertTrue(Platform.isWindows(), "Windows required");
        Path original = temporary.resolve("orig.txt");
        Path replacement = temporary.resolve("repl.txt");
        byte[] content = new byte[]{1, 2, 3, 4};
        Files.write(original, content);
        Files.write(replacement, content);
        FileTime originalMtime = Files.getLastModifiedTime(original);
        Files.setLastModifiedTime(replacement, originalMtime);

        var originalGeneral = IdentityBearingFileAttributes.read(original);
        var replacementGeneral = IdentityBearingFileAttributes.read(replacement);
        var originalKey = (IdentityBearingFileAttributes.WindowsFileIdentity) originalGeneral.fileKey();
        var replacementKey = (IdentityBearingFileAttributes.WindowsFileIdentity) replacementGeneral.fileKey();
        assertEquals(originalKey.volumeSerialDecimal(), replacementKey.volumeSerialDecimal());
        assertNotEquals(originalKey.fileIdDecimal(), replacementKey.fileIdDecimal());
        assertEquals(originalGeneral.lastModifiedTime(), replacementGeneral.lastModifiedTime());
        assertArrayEquals(content, Files.readAllBytes(replacement));

        Pin oldPin = LedgerFiles.read(original, 100).pin();
        FileIdentity oldId = oldPin.identity();
        assertEquals(originalKey.fileIdDecimal(), oldId.fileIdDecimal());
        Files.move(replacement, original, StandardCopyOption.REPLACE_EXISTING);

        assertArrayEquals(content, Files.readAllBytes(original));
        assertEquals(originalMtime, Files.getLastModifiedTime(original));
        var afterGeneral = IdentityBearingFileAttributes.read(original);
        var afterKey = (IdentityBearingFileAttributes.WindowsFileIdentity) afterGeneral.fileKey();
        assertEquals(replacementKey.volumeSerialDecimal(), afterKey.volumeSerialDecimal());
        assertEquals(replacementKey.fileIdDecimal(), afterKey.fileIdDecimal());
        assertNotEquals(originalKey.fileIdDecimal(), afterKey.fileIdDecimal());

        var newDoc = LedgerFiles.read(original, 100);
        FileIdentity independentlyObservedAfter = new FileIdentity(
                afterKey.volumeSerialDecimal(), afterKey.fileIdDecimal(), afterKey.creationFiletimeDecimal(),
                afterGeneral.lastModifiedTime().toInstant().toString(), afterGeneral.size());
        assertEquals(independentlyObservedAfter, newDoc.pin().identity());
        assertArrayEquals(content, newDoc.bytes());
        assertEquals(oldId.bytes(), newDoc.pin().identity().bytes());
        assertEquals(oldId.modifiedInstant(), newDoc.pin().identity().modifiedInstant());
        assertThrows(IOException.class, () -> LedgerFiles.verify(oldPin));
    }

    @Test void sharingDenialIsNotOptionalAbsenceAndOwnedHandleCanClose() throws Exception {
        assertTrue(Platform.isWindows(), "Windows required");
        Path file = temporary.resolve("sharing-denial.bin");
        byte[] expected = new byte[]{41, 42, 43, 44};
        Files.write(file, expected);
        String absolute = file.toAbsolutePath().normalize().toString();
        String nativePath = absolute.startsWith("\\\\?\\") ? absolute : "\\\\?\\" + absolute;
        var handle = com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(
                nativePath, 0x80000000, 0, null, 3, 0x02200000, null);
        assertNotNull(handle);
        assertFalse(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle));
        try {
            IOException failure = assertThrows(IOException.class, () -> LedgerFiles.optional(file));
            assertFalse(failure instanceof java.nio.file.NoSuchFileException);
        } finally {
            assertTrue(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle));
        }
        assertArrayEquals(expected, LedgerFiles.read(file, expected.length).bytes());
    }
}
