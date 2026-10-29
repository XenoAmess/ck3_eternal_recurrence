package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual temporary Windows persistence. The software card never grants production Root/Game authority. */
final class WriterStorageAdmissionTest {
    @TempDir Path temporary;
    @Test void completeCommitQuoteRejectsBeforeAnyPendingOrCanonicalWrite()throws Exception {
        assertTrue(Platform.isWindows());
        long unit=Math.max(4096,Files.getFileStore(temporary).getBlockSize());
        WriterFixture f=new WriterFixture(temporary.resolve("over-cap"),Math.multiplyExact(8,unit));
        byte[] snapshot=Files.readAllBytes(f.layout.snapshot());long before=f.storage.successfulBatches();
        Prepared proposed=f.writer.preview(WriterFixture.settled("whole-plan",1024,2));
        assertThrows(CommitUncertainException.class,()->f.writer.commit(proposed));
        assertEquals(before,f.storage.successfulBatches());assertFalse(f.storage.hasUnknownWrite(),"admission refused before invoking IO");
        assertArrayEquals(snapshot,Files.readAllBytes(f.layout.snapshot()));assertFalse(Files.exists(f.layout.event(1)));
        try(var files=Files.list(f.layout.events())){assertEquals(0,files.count());}
    }
    @Test void sameBytesOnAnotherOriginalLockFileIdCannotAcquireStoragePermission()throws Exception {
        assertTrue(Platform.isWindows());WriterFixture f=new WriterFixture(temporary.resolve("lock-id"));
        Prepared proposed=f.writer.preview(WriterFixture.settled("actual-lock-id",1024,2));byte[] snapshot=Files.readAllBytes(f.layout.snapshot());
        Path replacement=f.layout.lock().resolveSibling("replacement-lock");Files.write(replacement,Files.readAllBytes(f.layout.lock()));
        Files.move(replacement,f.layout.lock(),StandardCopyOption.REPLACE_EXISTING);
        assertThrows(CommitUncertainException.class,()->f.writer.commit(proposed));
        assertArrayEquals(snapshot,Files.readAllBytes(f.layout.snapshot()));assertFalse(Files.exists(f.layout.event(1)));
        assertEquals(0,f.storage.successfulBatches());
    }
    @Test void createThenRenameRechecksTheObservedOriginalNativeFileIdAndRetainsFailure()throws Exception {
        assertTrue(Platform.isWindows());WriterFixture f=new WriterFixture(temporary.resolve("source-id"));
        Path source=f.layout.snapshot().resolveSibling("original.pending"),target=source.resolveSibling("final.json");
        var create=new StorageWriteGuard.FileCreate(source,2);var rename=new StorageWriteGuard.FileRename(source,target,false);
        var plan=new StorageWriteGuard.WritePlan(f.layout.lock(),List.of(create,rename));AtomicInteger actualRenames=new AtomicInteger();
        f.writer.locked(same->{
            assertThrows(IOException.class,()->f.storage.write(plan,()->{
                f.storage.write(new StorageWriteGuard.WritePlan(f.layout.lock(),List.of(create)),()->{Files.write(source,new byte[]{1,2});return null;});
                // Fault injection touches only this temporary software fixture, replacing the observed file with equal bytes.
                Path other=source.resolveSibling("replacement");Files.write(other,new byte[]{1,2});Files.move(other,source,StandardCopyOption.REPLACE_EXISTING);
                return f.storage.write(new StorageWriteGuard.WritePlan(f.layout.lock(),List.of(rename)),()->{
                    actualRenames.incrementAndGet();Files.move(source,target);return null;
                });
            }));
            assertEquals(0,actualRenames.get());assertFalse(Files.exists(target));assertTrue(f.storage.hasUnknownWrite());
            assertThrows(IOException.class,()->f.storage.write(plan,()->{fail("UNKNOWN cannot replay physical writes");return null;}));
            return null;
        });
        f.storage.reconcileStorageOnly();assertFalse(f.storage.hasUnknownWrite());assertFalse(Files.exists(target));
        assertEquals(0,f.writer.locked(ContinuityStorePort.Session::head).state().sequence(),"storage reconciliation cannot invent a ledger/action result");
    }
    @Test void closedAllocationOwnerCannotBeReusedForAnotherPhysicalCommit()throws Exception {
        assertTrue(Platform.isWindows());WriterFixture f=new WriterFixture(temporary.resolve("closed"));
        Prepared proposed=f.writer.preview(WriterFixture.settled("after-close",1024,2));
        byte[] snapshot=Files.readAllBytes(f.layout.snapshot());f.storage.close();
        assertThrows(CommitUncertainException.class,()->f.writer.commit(proposed));
        assertThrows(IOException.class,()->StorageWriteGuardTestSupport.forOriginalLock(f.layout.lock()));
        assertArrayEquals(snapshot,Files.readAllBytes(f.layout.snapshot()));assertFalse(Files.exists(f.layout.event(1)));
    }
}
