package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;

import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.AclEntry;
import java.nio.file.attribute.AclEntryPermission;
import java.nio.file.attribute.AclEntryType;
import java.nio.file.attribute.AclFileAttributeView;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.ReadOnlyLease;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.WindowsFileIdentity;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;

/** Owned Windows originals only. This does not validate Store/History or establish runtime safety. */
final class LeasedOriginal222Test {
    @TempDir Path temporary;

    @BeforeEach void actualWindows() {
        assertTrue(Platform.isWindows(), "actual Windows is required, not an optional skipped backend");
        assertTrue(temporary.isAbsolute(), "runner must supply a private absolute temporary directory");
    }

    private static byte[] bytes(int length) {
        byte[] value = new byte[length];
        for (int index = 0; index < length; index++)
            value[index] = (byte) ((index * 73) ^ (index >>> 7) ^ (index >>> 16) ^ 0x35);
        return value;
    }
    private static String sha(byte[] value) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));
    }
    private static String nativePath(Path supplied) {
        String value = supplied.toAbsolutePath().normalize().toString();
        if (value.startsWith("\\\\?\\")) return value;
        return value.startsWith("\\\\") ? "\\\\?\\UNC\\" + value.substring(2) : "\\\\?\\" + value;
    }
    private static FileIdentity identity(BasicFileAttributes attributes) {
        WindowsFileIdentity key = (WindowsFileIdentity) attributes.fileKey();
        return new FileIdentity(key.volumeSerialDecimal(), key.fileIdDecimal(), key.creationFiletimeDecimal(),
                attributes.lastModifiedTime().toInstant().toString(), attributes.size());
    }
    private static void closeRaw(HANDLE handle) throws IOException {
        if (!Kernel32.INSTANCE.CloseHandle(handle))
            throw new IOException("owned test HANDLE close failed: Win32=" + Native.getLastError());
    }
    private static final class OwnedHandle implements AutoCloseable {
        private HANDLE value;
        private OwnedHandle(HANDLE value) throws IOException {
            if (value == null || WinBase.INVALID_HANDLE_VALUE.equals(value))
                throw new IOException("owned native setup open failed: Win32=" + Native.getLastError());
            this.value = value;
        }
        @Override public void close() throws IOException {
            HANDLE actual = value;
            if (actual != null) { value = null; closeRaw(actual); }
        }
    }
    private static final class OwnedView implements AutoCloseable {
        private Pointer value;
        private OwnedView(Pointer value) throws IOException {
            if (value == null) throw new IOException("owned file mapping view failed: Win32=" + Native.getLastError());
            this.value = value;
        }
        @Override public void close() throws IOException {
            Pointer actual = value;
            if (actual != null) {
                value = null;
                if (!Kernel32.INSTANCE.UnmapViewOfFile(actual))
                    throw new IOException("owned view unmap failed: Win32=" + Native.getLastError());
            }
        }
    }
    private static OwnedHandle open(Path file, int access) throws IOException {
        return new OwnedHandle(Kernel32.INSTANCE.CreateFile(nativePath(file), access, 7, null, 3, 0x02200000, null));
    }
    private static void deniedOpen(Path file, int access) throws Exception {
        HANDLE actual = Kernel32.INSTANCE.CreateFile(nativePath(file), access, 7, null, 3, 0x02200000, null);
        if (!WinBase.INVALID_HANDLE_VALUE.equals(actual)) {
            try (OwnedHandle unexpected = new OwnedHandle(actual)) {
                assertNotNull(unexpected.value);
                fail("a forbidden current native access open succeeded");
            }
        }
    }
    private static IOException deniedLease(Path file, int cap) throws Exception {
        ReadOnlyLease granted;
        try { granted = IdentityBearingFileAttributes.leaseBoundedWindows(file, cap); }
        catch (IOException denied) { return denied; }
        try (granted) { fail("mutable original was accepted as an immutable-custody lease"); }
        throw new AssertionError("unreachable successful lease");
    }

    @Test void fullBytesCurrentIdentityDetachedCopiesAndExactPin() throws Exception {
        byte[] expected = bytes(70_013);
        Path file = temporary.resolve("large.bin");
        Files.write(file, expected, StandardOpenOption.CREATE_NEW);
        FileIdentity independent = identity(IdentityBearingFileAttributes.read(file));
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, expected.length)) {
            var captured = lease.originalRead();
            assertArrayEquals(expected, captured.bytes());
            assertEquals(independent, identity(captured.attributes()));
            captured.bytes()[0] ^= (byte) 0xff;
            assertArrayEquals(expected, lease.originalRead().bytes());
            var first = lease.read();
            assertEquals(independent, identity(first.attributes()));
            assertEquals(sha(expected), sha(first.bytes()));
            first.bytes()[first.bytes().length - 1] ^= (byte) 0xff;
            var second = lease.read();
            assertEquals(independent, identity(second.attributes()));
            assertArrayEquals(expected, second.bytes());
        }
        ExactRef ref = new ExactRef(file.toAbsolutePath().normalize().toString(), expected.length, sha(expected));
        try (LedgerFiles.LeasedDocument lease = LedgerFiles.lease(ref, expected.length)) {
            LedgerFiles.Document original = lease.original();
            assertEquals(ref, original.pin().reference());
            assertEquals(independent, original.pin().identity());
            byte[] detached = original.bytes(); detached[0] ^= (byte) 0xff;
            assertArrayEquals(expected, original.bytes());
            assertEquals(original.pin(), lease.read().pin());
            assertArrayEquals(expected, lease.read().bytes());
        }
        ExactRef wrong = new ExactRef(ref.path(), ref.bytes(), "0".repeat(64));
        assertThrows(IOException.class, () -> {
            try (LedgerFiles.LeasedDocument unexpected = LedgerFiles.lease(wrong, expected.length)) {
                assertNotNull(unexpected.original());
            }
        });
    }

    @Test void exactFiniteCapsAndEmptyZeroCap() throws Exception {
        Path file = temporary.resolve("cap.bin");
        Files.write(file, bytes(129), StandardOpenOption.CREATE_NEW);
        assertThrows(IOException.class, () -> {
            try (ReadOnlyLease unexpected = IdentityBearingFileAttributes.leaseBoundedWindows(file, 128)) {
                assertNotNull(unexpected.originalRead());
            }
        });
        assertThrows(IllegalArgumentException.class, () -> IdentityBearingFileAttributes.leaseBoundedWindows(file, -1));
        assertThrows(IllegalArgumentException.class, () -> IdentityBearingFileAttributes.leaseBoundedWindows(file, Integer.MAX_VALUE));
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 129)) {
            assertArrayEquals(bytes(129), lease.read().bytes());
        }
        Path empty = temporary.resolve("empty.bin");
        Files.write(empty, new byte[0], StandardOpenOption.CREATE_NEW);
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(empty, 0)) {
            assertEquals(0, lease.read().bytes().length);
        }
    }

    @Test void actualWriterDeleteAndRenameSharing() throws Exception {
        Path file = temporary.resolve("sharing.bin");
        Files.write(file, bytes(64), StandardOpenOption.CREATE_NEW);
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            assertNotNull(lease.verifyCurrent());
            deniedOpen(file, 0x40000000);
            deniedOpen(file, 0x00010000);
            assertThrows(IOException.class, () -> Files.delete(file));
            assertThrows(IOException.class, () -> Files.move(file, temporary.resolve("renamed.bin")));
        }
        try (OwnedHandle writer = open(file, 0xC0000000)) {
            assertNotNull(writer.value);
            assertNotNull(deniedLease(file, 64));
        }
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            assertArrayEquals(bytes(64), lease.read().bytes());
        }
        try (OwnedHandle writer = open(file, 0x40000000)) { assertNotNull(writer.value); }
    }

    @Test void writableViewSurvivesBothCreatorHandlesWithoutSafeLeaseGrant() throws Exception {
        Path file = temporary.resolve("mapped.bin");
        Files.write(file, bytes(64), StandardOpenOption.CREATE_NEW);
        try (ReadOnlyLease baseline = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            assertArrayEquals(bytes(64), baseline.read().bytes());
        }
        try (OwnedHandle creator = open(file, 0xC0000000)) {
            try (OwnedHandle section = new OwnedHandle(Kernel32.INSTANCE.CreateFileMapping(creator.value, null, 4, 0, 0, null))) {
                try (OwnedView view = new OwnedView(Kernel32.INSTANCE.MapViewOfFile(section.value, 2, 0, 0, 0))) {
                    view.value.setByte(0, (byte) 0x5a);
                    assertEquals((byte) 0x5a, view.value.getByte(0));
                    section.close(); creator.close();
                    view.value.setByte(1, (byte) 0x6b);
                    assertEquals((byte) 0x6b, view.value.getByte(1));
                    assertNotNull(deniedLease(file, 64));
                    view.value.setByte(2, (byte) 0x7c);
                    assertEquals((byte) 0x7c, view.value.getByte(2));
                }
            }
        }
        try (ReadOnlyLease afterUnmap = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            assertEquals(64, afterUnmap.verifyCurrent().size());
            byte[] actual = afterUnmap.read().bytes();
            assertEquals((byte) 0x5a, actual[0]);
            assertEquals((byte) 0x6b, actual[1]);
            assertEquals((byte) 0x7c, actual[2]);
        }
    }

    @Test void metadataChangesRemainActualAndPoisonFailedLease() throws Exception {
        Path file = temporary.resolve("metadata.bin");
        Files.write(file, bytes(64), StandardOpenOption.CREATE_NEW);
        FileTime before = Files.getLastModifiedTime(file, LinkOption.NOFOLLOW_LINKS);
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            try {
                FileTime changed = FileTime.from(before.toInstant().plusSeconds(4));
                Files.setLastModifiedTime(file, changed);
                assertNotEquals(before, Files.getLastModifiedTime(file, LinkOption.NOFOLLOW_LINKS));
                assertThrows(IOException.class, lease::verifyCurrent);
                assertThrows(IOException.class, lease::read);
            } finally { Files.setLastModifiedTime(file, before); }
        }
        try (ReadOnlyLease fresh = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            assertArrayEquals(bytes(64), fresh.read().bytes());
        }
    }

    @Test void currentReadDataAclCannotBeBypassedByOldHandle() throws Exception {
        Path file = temporary.resolve("acl.bin");
        Files.write(file, bytes(64), StandardOpenOption.CREATE_NEW);
        AclFileAttributeView view = Files.getFileAttributeView(file, AclFileAttributeView.class, LinkOption.NOFOLLOW_LINKS);
        assertNotNull(view, "required owned-file Windows ACL view");
        List<AclEntry> original = List.copyOf(view.getAcl());
        var principal = file.getFileSystem().getUserPrincipalLookupService()
                .lookupPrincipalByName(System.getProperty("user.name"));
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            try {
                List<AclEntry> changed = new ArrayList<>(original);
                changed.add(0, AclEntry.newBuilder().setType(AclEntryType.DENY).setPrincipal(principal)
                        .setPermissions(AclEntryPermission.READ_DATA).build());
                view.setAcl(changed);
                deniedOpen(file, 0x80000000);
                assertThrows(IOException.class, lease::verifyCurrent);
                assertThrows(IOException.class, lease::read);
            } finally { view.setAcl(original); }
        }
        try (ReadOnlyLease fresh = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            assertArrayEquals(bytes(64), fresh.read().bytes());
        }
    }

    @Test void sameBytesAndMtimeCannotHideNativePathRebinding() throws Exception {
        Path parent = Files.createDirectory(temporary.resolve("current"));
        Path moved = temporary.resolve("moved");
        Path file = parent.resolve("leaf.bin");
        byte[] expected = bytes(64);
        Files.write(file, expected, StandardOpenOption.CREATE_NEW);
        Path replacement = temporary.resolve("replacement.bin");
        Files.write(replacement, expected, StandardOpenOption.CREATE_NEW);
        FileTime mtime = Files.getLastModifiedTime(file);
        Files.setLastModifiedTime(replacement, mtime);
        FileIdentity before = identity(IdentityBearingFileAttributes.read(file));
        FileIdentity replacementId = identity(IdentityBearingFileAttributes.read(replacement));
        assertEquals(before.volumeSerialDecimal(), replacementId.volumeSerialDecimal());
        assertNotEquals(before.fileIdDecimal(), replacementId.fileIdDecimal());
        boolean rebound = false;
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            IOException denied = null;
            try { Files.move(parent, moved); } catch (IOException failure) { denied = failure; }
            if (denied != null) {
                assertTrue(Files.isDirectory(parent, LinkOption.NOFOLLOW_LINKS));
                assertFalse(Files.exists(moved, LinkOption.NOFOLLOW_LINKS));
                assertEquals(before, identity(IdentityBearingFileAttributes.read(file)));
                assertArrayEquals(expected, lease.read().bytes());
                System.out.println("222 namespace mutation rejected; no successful rebind claimed: " + denied.getClass().getSimpleName());
            } else {
                rebound = true;
                Files.createDirectory(parent);
                Files.move(replacement, file);
                assertEquals(mtime, Files.getLastModifiedTime(file));
                assertArrayEquals(expected, Files.readAllBytes(file));
                assertEquals(replacementId, identity(IdentityBearingFileAttributes.read(file)));
                assertThrows(IOException.class, lease::verifyCurrent);
                assertThrows(IOException.class, lease::read);
                System.out.println("222 namespace rebound; old lease rejected distinct native identity");
            }
        }
        ExactRef sameContent = new ExactRef(file.toAbsolutePath().normalize().toString(), 64, sha(expected));
        try (LedgerFiles.LeasedDocument fresh = LedgerFiles.lease(sameContent, 64)) {
            assertArrayEquals(expected, fresh.read().bytes());
            assertEquals(rebound ? replacementId : before, fresh.read().pin().identity());
        }
    }

    @Test void exactOwnerThreadAndClosedLifetime() throws Exception {
        Path file = temporary.resolve("thread.bin");
        Files.write(file, bytes(64), StandardOpenOption.CREATE_NEW);
        try (ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64)) {
            AtomicReference<Throwable> result = new AtomicReference<>();
            Thread worker = new Thread(() -> {
                try {
                    assertThrows(IOException.class, lease::read);
                    assertThrows(IOException.class, lease::verifyCurrent);
                    assertThrows(IOException.class, lease::close);
                } catch (Throwable failure) { result.set(failure); }
            }, "owned-lease222-wrong-thread");
            worker.setDaemon(true); worker.start(); worker.join(3000);
            if (worker.isAlive()) { worker.interrupt(); worker.join(1000); }
            assertFalse(worker.isAlive(), "bounded worker must terminate");
            assertNull(result.get(), () -> "wrong-thread rejection failed: " + result.get());
            assertArrayEquals(bytes(64), lease.read().bytes());
            lease.close(); lease.close();
            assertThrows(IOException.class, lease::read);
            assertThrows(IOException.class, lease::verifyCurrent);
        }
    }

    @Test void actualCloseFailureIsNotSwallowedInControlledCorruptFieldFixture() throws Exception {
        Path file = temporary.resolve("close-fault.bin");
        Files.write(file, bytes(64), StandardOpenOption.CREATE_NEW);
        ReadOnlyLease lease = IdentityBearingFileAttributes.leaseBoundedWindows(file, 64);
        HANDLE original = null;
        boolean detached = false;
        try {
            Field field = ReadOnlyLease.class.getDeclaredField("handle");
            field.setAccessible(true);
            original = (HANDLE) field.get(lease);
            assertNotNull(original);
            assertFalse(WinBase.INVALID_HANDLE_VALUE.equals(original));
            HANDLE nullHandle = new HANDLE(Pointer.NULL);
            assertEquals(0L, Pointer.nativeValue(nullHandle.getPointer()));
            assertFalse(Kernel32.INSTANCE.CloseHandle(nullHandle), "NULL has no owned native object to close");
            assertEquals(6, Native.getLastError(), "actual ERROR_INVALID_HANDLE precondition");
            field.set(lease, nullHandle);
            detached = true;
            assertSame(nullHandle, field.get(lease));
            // The original HANDLE remains open, so its numeric value cannot be recycled into a stranger.
            assertThrows(IOException.class, lease::close);
            assertThrows(IOException.class, lease::read);
        } finally {
            if (detached) {
                try { lease.close(); } finally { closeRaw(original); }
            } else { lease.close(); }
        }
    }
}
