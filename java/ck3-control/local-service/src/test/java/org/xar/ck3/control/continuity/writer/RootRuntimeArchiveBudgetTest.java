package org.xar.ck3.control.continuity.writer;
import org.xar.ck3.control.service.root.RootRuntimeStorageGuard;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.*;
import java.time.Clock;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.writer.*;

final class RootRuntimeArchiveBudgetTest {
    @TempDir Path temporary;
    private record Scope(Path state,Path archive,Path lock,RootRuntimeStorageGuard guard) implements AutoCloseable {
        @Override public void close() throws IOException { guard.close(); }
    }
    private Scope scope(long cap) throws IOException {
        Path state=Files.createDirectory(temporary.resolve("state"));
        Path continuity=Files.createDirectory(temporary.resolve("continuity"));
        Path archive=Files.createDirectory(continuity.resolve("artifacts"));
        var layout=new WriterContracts.InitialLayout(continuity.resolve("snapshot.json"),continuity.resolve("anchor.json"),WindowsJobProcess.currentMachineId());
        var guard=RootRuntimeStorageGuard.ordinary(layout,archive,()->{throw new IOException("writer not constructed");},List.of(state,continuity),cap,Clock.systemUTC());
        guard.requireInitialization(layout.lock(),List.of(state,continuity,archive));
        return new Scope(state,archive,layout.lock(),guard);
    }
    @Test void boundBelongsToTheSameOriginalLockAndManagedDirectory() throws IOException {
        try(var s=scope(1L<<20)) {
            assertEquals(1L<<20,s.guard.enforcedAggregateMaximumBytes(s.lock,s.archive).orElseThrow());
            assertThrows(IOException.class,()->s.guard.enforcedAggregateMaximumBytes(s.lock,temporary.resolve("foreign")));
            assertThrows(IOException.class,()->s.guard.enforcedAggregateMaximumBytes(temporary.resolve("another.lock"),s.archive));
        }
    }
    @Test void narrowerArchiveCapStillRejectsBeforeAnyPhysicalMutation() throws IOException {
        try(var s=scope(1L<<20)) {
            var store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(s.archive,s.lock,8192),s.guard);
            try(var held=WindowsLedgerLock.acquire(s.lock)) {
                assertThrows(IOException.class,()->store.publish(new byte[4096],4096));
            }
            try(var paths=Files.list(s.archive)) { assertEquals(0,paths.count()); }
            assertEquals(4096,store.retainedNativeBytes());
            assertEquals(0,s.guard.accounting().unresolvedWrites());
        }
    }
    @Test void anotherManagedRootStillConsumesTheSameAggregateCap() throws IOException {
        try(var s=scope(256L<<10)) {
            var store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(s.archive,s.lock,1L<<20),s.guard);
            Path other=s.state.resolve("other.bin");
            s.guard.write(new StorageWriteGuard.WritePlan(s.lock,List.of(new StorageWriteGuard.FileCreate(other,128L<<10))),()->Files.write(other,new byte[128<<10],StandardOpenOption.CREATE_NEW));
            try(var held=WindowsLedgerLock.acquire(s.lock)) {
                assertThrows(IOException.class,()->store.publish(new byte[128<<10],128<<10));
            }
            assertEquals(128L<<10,Files.size(other));
            try(var paths=Files.list(s.archive)) { assertEquals(0,paths.count()); }
            assertEquals(0,s.guard.accounting().unresolvedWrites());
        }
    }
    @Test void coveredArchiveKeepsExactAuditReadbackAndDeduplication() throws IOException {
        try(var s=scope(1L<<20)) {
            var store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(s.archive,s.lock,1L<<20),s.guard);
            byte[] body=new byte[4096];body[0]=7;
            try(var held=WindowsLedgerLock.acquire(s.lock)) {
                var pin=store.publish(body,body.length);
                long before=s.guard.accounting().roots().stream().mapToLong(RootRuntimeStorageGuard.RootAccounting::measuredChargedUpperBytes).sum();
                assertEquals(pin,store.publish(body,body.length));
                assertArrayEquals(body,store.read(pin,body.length));
                assertEquals(before,s.guard.accounting().roots().stream().mapToLong(RootRuntimeStorageGuard.RootAccounting::measuredChargedUpperBytes).sum());
                assertTrue(store.retainedNativeBytes()>=4096+body.length);
            }
            assertEquals(0,s.guard.accounting().unresolvedWrites());
        }
    }
}
