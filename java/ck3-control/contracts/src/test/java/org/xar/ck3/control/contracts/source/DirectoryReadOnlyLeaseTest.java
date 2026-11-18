package org.xar.ck3.control.contracts.source;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real directory handles; an empty-directory rename cannot be rejected by an unrelated child-file lease. */
final class DirectoryReadOnlyLeaseTest {
    @TempDir Path temporary;
    private static HANDLE openWrite(Path directory) {
        return Kernel32.INSTANCE.CreateFile(directory.toString(),0x40000000,7,null,3,0x02000000,null);
    }
    @Test void actualDirectoryHandleDeniesWriteAndDeleteThenCloseRestoresBoth()throws Exception {
        Path directory=Files.createDirectory(temporary.resolve("plain-directory"));Path moved=temporary.resolve("moved-directory");
        var lease=IdentityBearingFileAttributes.leaseDirectoryWindows(directory);
        try {
            assertTrue(lease.verifyCurrent().isDirectory());
            HANDLE denied=openWrite(directory);
            if(!WinBase.INVALID_HANDLE_VALUE.equals(denied)) {
                Kernel32.INSTANCE.CloseHandle(denied);fail("real directory GENERIC_WRITE was not denied");
            }
            assertEquals(32,Native.getLastError());
            assertThrows(IOException.class,()->Files.move(directory,moved,StandardCopyOption.ATOMIC_MOVE));
            assertThrows(IOException.class,()->Files.delete(directory));
            lease.verifyCurrent();
        }finally{lease.close();}
        assertThrows(IOException.class,lease::verifyCurrent);lease.close();
        HANDLE writer=openWrite(directory);assertNotEquals(WinBase.INVALID_HANDLE_VALUE,writer);assertTrue(Kernel32.INSTANCE.CloseHandle(writer));
        Files.move(directory,moved,StandardCopyOption.ATOMIC_MOVE);assertTrue(Files.isDirectory(moved));
    }
    @Test void directoryMetadataDriftFailsPermanentlyWithoutPreventingOwnerCleanup()throws Exception {
        Path directory=Files.createDirectory(temporary.resolve("metadata-drift"));
        try(var lease=IdentityBearingFileAttributes.leaseDirectoryWindows(directory)) {
            FileTime before=lease.verifyCurrent().lastModifiedTime();
            Files.setLastModifiedTime(directory,FileTime.fromMillis(before.toMillis()+2000));
            assertThrows(IOException.class,lease::verifyCurrent);
            Files.setLastModifiedTime(directory,before);assertThrows(IOException.class,lease::verifyCurrent);
        }
        Files.move(directory,temporary.resolve("released-drift"),StandardCopyOption.ATOMIC_MOVE);
    }
    @Test void regularFileIsRejectedWithoutLeavingAnUnexpectedReadLock()throws Exception {
        Path file=Files.writeString(temporary.resolve("not-directory.bin"),"ordinary file");
        assertThrows(IOException.class,()->IdentityBearingFileAttributes.leaseDirectoryWindows(file));
        try(var writer=FileChannel.open(file,StandardOpenOption.WRITE)){assertTrue(writer.isOpen());}
        Files.delete(file);assertFalse(Files.exists(file));
    }
}
