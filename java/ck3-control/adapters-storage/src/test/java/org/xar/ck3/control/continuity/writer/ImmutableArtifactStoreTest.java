package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;

/** Native Windows filesystem tests. An unavailable native environment is a failure, never a passing skip. */
final class ImmutableArtifactStoreTest {
    @TempDir Path temp;
    private record Fixture(Path root, Path lock, StorageWriteGuardTestSupport guard, ImmutableArtifactStore store) { }
    private Fixture fixture(String name, long cap, ImmutableArtifactStore.FaultProbe fault) throws IOException {
        return fixture(name, cap, 64L << 20, fault);
    }
    private Fixture fixture(String name, long cap, long wholeCap, ImmutableArtifactStore.FaultProbe fault) throws IOException {
        Path base = Files.createDirectory(temp.resolve(name)); Path lock = base.resolve("original.lock");
        Files.write(lock, new byte[0], StandardOpenOption.CREATE_NEW); Path root = base.resolve("artifacts");
        StorageWriteGuardTestSupport guard = StorageWriteGuardTestSupport.create(base, lock, wholeCap);
        return new Fixture(root, lock, guard,
                new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root, lock, cap), guard, fault));
    }
    private Fixture fixture(String name) throws IOException { return fixture(name, 2 * 1024 * 1024, boundary -> { }); }
    private static long files(Path path) throws IOException { try (var stream = Files.list(path)) { return stream.count(); } }
    @Test void publicationRequiresOriginalNativeLockAndLookupNeverPreserves() throws IOException {
        Fixture f = fixture("lock"); byte[] original = "original".getBytes(StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> f.store.publish(original, 100));
        assertThrows(IOException.class, () -> f.store.referenceOf(original, 100)); assertEquals(0, files(f.root));
        try (var held = WindowsLedgerLock.acquire(f.lock)) {
            var pin = f.store.publish(original, 100); assertArrayEquals(original, f.store.read(pin, 100));
            long before = f.store.retainedNativeBytes(); assertEquals(pin, f.store.publish(original, 100));
            assertEquals(pin, f.store.referenceOf(original, 100)); assertEquals(before, f.store.retainedNativeBytes());
        }
        assertFalse(f.store.writerLockHeldByCurrentThread());
    }
    @Test void allFourDurabilityBoundariesRecoverWithoutOverwritingOriginals() throws IOException {
        for (ImmutableArtifactStore.Boundary failed : ImmutableArtifactStore.Boundary.values()) {
            AtomicBoolean failOnce = new AtomicBoolean(true);
            Fixture f = fixture(failed.name(), 2 * 1024 * 1024, reached -> {
                if (reached == failed && failOnce.getAndSet(false)) throw new IOException("injected crash at " + reached);
            });
            byte[] original = ("raw bytes at " + failed).getBytes(StandardCharsets.UTF_8);
            try (var held = WindowsLedgerLock.acquire(f.lock)) { assertThrows(IOException.class, () -> f.store.publish(original, 100)); }
            assertTrue(f.guard.hasUnknownWrite());
            // Reopening cannot erase an uncertain allocation. An actual complete storage scan is explicit.
            f.guard.reconcileStorageOnly();
            ImmutableArtifactStore reopened = new ImmutableArtifactStore(
                    new ImmutableArtifactStore.Config(f.root, f.lock, 2 * 1024 * 1024), f.guard);
            try (var held = WindowsLedgerLock.acquire(f.lock)) {
                var recovered = reopened.publish(original, 100); assertArrayEquals(original, reopened.read(recovered, 100));
                assertEquals(recovered, reopened.referenceOf(original, 100));
            }
        }
    }
    @Test void changedSameNamePayloadWithIdenticalBytesCannotAcquireOldIdentity() throws IOException {
        Fixture f = fixture("payload-id"); byte[] original = "retained original".getBytes(StandardCharsets.UTF_8); ExactRef ref;
        try (var held = WindowsLedgerLock.acquire(f.lock)) { ref = f.store.publish(original, 100).reference(); }
        Path target = Path.of(ref.path()); var before = LedgerFiles.identity(target);
        Files.move(target, target.resolveSibling("payload-retained-original.bin")); Files.write(target, original, StandardOpenOption.CREATE_NEW);
        assertNotEquals(before.fileIdDecimal(), LedgerFiles.identity(target).fileIdDecimal());
        assertThrows(IOException.class, () -> f.store.read(ref, 100));
        try (var held = WindowsLedgerLock.acquire(f.lock)) { assertThrows(IOException.class, () -> f.store.publish(original, 100)); }
    }
    @Test void sameNameCommitReplacementCannotMasqueradeAsItsOldSelf() throws IOException {
        Fixture f = fixture("commit-id"); byte[] original = "retained commit".getBytes(StandardCharsets.UTF_8); ExactRef ref;
        try (var held = WindowsLedgerLock.acquire(f.lock)) { ref = f.store.publish(original, 100).reference(); }
        Path commit = f.root.resolve(ref.sha256() + ".commit.json"); byte[] bytes = Files.readAllBytes(commit);
        var before = LedgerFiles.identity(commit); Files.move(commit, commit.resolveSibling("commit-retained-original.json"));
        Files.write(commit, bytes, StandardOpenOption.CREATE_NEW); assertNotEquals(before.fileIdDecimal(), LedgerFiles.identity(commit).fileIdDecimal());
        assertThrows(IOException.class, () -> f.store.read(ref, 100));
    }
    @Test void contentCorruptionAndWrongHashAreRejectedWithoutRepair() throws IOException {
        Fixture f = fixture("corruption"); byte[] original = "content".getBytes(StandardCharsets.UTF_8); ExactRef ref;
        try (var held = WindowsLedgerLock.acquire(f.lock)) { ref = f.store.publish(original, 100).reference(); }
        Files.write(Path.of(ref.path()), "CONTENT".getBytes(StandardCharsets.UTF_8), StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class, () -> f.store.read(ref, 100));
        assertArrayEquals("CONTENT".getBytes(StandardCharsets.UTF_8), Files.readAllBytes(Path.of(ref.path())));
        assertThrows(IOException.class, () -> f.store.read(new ExactRef(ref.path(), ref.bytes(), "0".repeat(64)), 100));
    }
    @Test void corruptPendingBytesRemainAsFailureEvidence() throws IOException {
        Fixture f = fixture("pending", 2 * 1024 * 1024, reached -> {
            if (reached == ImmutableArtifactStore.Boundary.RAW_DURABLE) throw new IOException("raw durable crash");
        });
        byte[] original = "pending".getBytes(StandardCharsets.UTF_8);
        try (var held = WindowsLedgerLock.acquire(f.lock)) { assertThrows(IOException.class, () -> f.store.publish(original, 100)); }
        Path pending = f.root.resolve(LedgerFiles.sha(original) + ".data.pending");
        Files.writeString(pending, "changed", StandardOpenOption.TRUNCATE_EXISTING);
        f.guard.reconcileStorageOnly();
        ImmutableArtifactStore reopened = new ImmutableArtifactStore(
                new ImmutableArtifactStore.Config(f.root, f.lock, 2 * 1024 * 1024), f.guard);
        try (var held = WindowsLedgerLock.acquire(f.lock)) { assertThrows(IOException.class, () -> reopened.publish(original, 100)); }
        assertEquals("changed", Files.readString(pending)); assertEquals(1, files(f.root));
    }
    @Test void finiteBudgetRejectsBeforeCreatingTheRawArtifact() throws IOException {
        Fixture f = fixture("budget", 8192, reached -> { });
        try (var held = WindowsLedgerLock.acquire(f.lock)) {
            assertThrows(IOException.class, () -> f.store.publish(new byte[4096], 4096));
        }
        assertEquals(0, files(f.root)); assertEquals(4096, f.store.retainedNativeBytes());
    }
    @Test void replacedRootIsRejectedEvenWhenThePathStillExists() throws IOException {
        Fixture f = fixture("root-id"); byte[] bytes = new byte[] {1}; ExactRef ref;
        try (var held = WindowsLedgerLock.acquire(f.lock)) { ref = f.store.publish(bytes, 10).reference(); }
        Files.move(f.root, f.root.resolveSibling("retained-artifacts")); Files.createDirectory(f.root);
        assertThrows(IOException.class, f.store::identity); assertThrows(IOException.class, () -> f.store.read(ref, 10));
    }
    @Test void wholeScopeCapRejectsBeforeAnyPublishPhaseEvenWhenArchiveCapHasSpace() throws IOException {
        Fixture f = fixture("whole-budget", 4L << 20, 64L << 10, reached -> { });
        long calls = f.guard.validations();
        try (var held = WindowsLedgerLock.acquire(f.lock)) {
            assertThrows(IOException.class, () -> f.store.publish(new byte[128 << 10], 128 << 10));
        }
        assertEquals(calls, f.guard.validations());
        assertFalse(f.guard.hasUnknownWrite());
        assertEquals(0, files(f.root)); assertEquals(4096, f.store.retainedNativeBytes());
    }
    @Test void actualCreationPublicationAndReopenRetainTheIdenticalWholeGuard() throws IOException {
        Fixture f = fixture("guard-reopen");
        assertTrue(Files.isDirectory(f.root)); assertSame(f.guard, f.store.storageGuard());
        assertTrue(f.guard.successfulBatches() > 0);
        byte[] original = "durable guarded original".getBytes(StandardCharsets.UTF_8);
        WriterContracts.Pin pin;
        try (var held = WindowsLedgerLock.acquire(f.lock)) { pin = f.store.publish(original, 100); }
        long calls = f.guard.validations(), retained = f.store.retainedNativeBytes();
        ImmutableArtifactStore reopened = new ImmutableArtifactStore(
                new ImmutableArtifactStore.Config(f.root, f.lock, 2L << 20), f.guard);
        assertSame(f.guard, reopened.storageGuard());
        assertArrayEquals(original, reopened.read(pin, 100));
        assertEquals(pin, reopened.referenceOf(original, 100));
        try (var held = WindowsLedgerLock.acquire(f.lock)) { assertEquals(pin, reopened.publish(original, 100)); }
        assertEquals(calls, f.guard.validations()); assertEquals(retained, reopened.retainedNativeBytes());
    }
    @Test void aForeignFiniteGuardRejectsBeforeArchiveDirectoryCreation() throws IOException {
        Fixture foreign = fixture("foreign-scope");
        Path base = Files.createDirectory(temp.resolve("actual-scope"));
        Path lock = base.resolve("original.lock"), root = base.resolve("artifacts");
        Files.write(lock, new byte[0], StandardOpenOption.CREATE_NEW);
        long calls = foreign.guard.validations();
        assertThrows(IOException.class, () -> new ImmutableArtifactStore(
                new ImmutableArtifactStore.Config(root, lock, 2L << 20), foreign.guard));
        assertFalse(Files.exists(root)); assertEquals(calls, foreign.guard.validations());
    }
    @Test void initializationRejectsAnUnfundedArchiveWithoutCreatingItsRoot() throws IOException {
        Path base = Files.createDirectory(temp.resolve("init-budget"));
        Path lock = base.resolve("original.lock"), root = base.resolve("artifacts");
        Files.write(lock, new byte[0], StandardOpenOption.CREATE_NEW);
        StorageWriteGuardTestSupport guard = StorageWriteGuardTestSupport.create(base, lock, 64L << 20);
        assertThrows(IOException.class, () -> new ImmutableArtifactStore(
                new ImmutableArtifactStore.Config(root, lock, 4095), guard));
        assertFalse(Files.exists(root)); assertEquals(0, guard.validations());
    }
    @Test void initializationUsesTheAlreadyHeldOriginalWriterLockForEveryMissingDirectory() throws IOException {
        Path base = Files.createDirectory(temp.resolve("held-init"));
        Path lock = base.resolve("original.lock"), root = base.resolve("archive-parent").resolve("artifacts");
        Files.write(lock, new byte[0], StandardOpenOption.CREATE_NEW);
        StorageWriteGuardTestSupport guard = StorageWriteGuardTestSupport.create(base, lock, 64L << 20);
        try (var held = WindowsLedgerLock.acquire(lock)) {
            ImmutableArtifactStore store = new ImmutableArtifactStore(
                    new ImmutableArtifactStore.Config(root, lock, 2L << 20), guard);
            assertSame(guard, store.storageGuard()); assertTrue(store.writerLockHeldByCurrentThread());
            assertTrue(Files.isDirectory(root));
            byte[] original = new byte[] {1, 2};
            assertArrayEquals(original, store.read(store.publish(original, 10), 10));
        }
        assertFalse(guard.hasUnknownWrite());
    }
    @Test void identicalBytesAtAReplacementOriginalLockCannotAuthorizeNewWrites() throws IOException {
        Fixture f = fixture("lock-id"); var original = LedgerFiles.identity(f.lock);
        Files.move(f.lock, f.lock.resolveSibling("retained-original.lock"));
        Files.write(f.lock, new byte[0], StandardOpenOption.CREATE_NEW);
        assertNotEquals(original.fileIdDecimal(), LedgerFiles.identity(f.lock).fileIdDecimal());
        long calls = f.guard.validations();
        try (var held = WindowsLedgerLock.acquire(f.lock)) {
            assertThrows(IOException.class, () -> f.store.publish(new byte[] {3}, 10));
        }
        assertEquals(calls, f.guard.validations()); assertEquals(0, files(f.root));
    }
    @Test void unknownPhysicalPhaseBlocksNewPublicationUntilAnActualStorageAudit() throws IOException {
        AtomicBoolean failOnce = new AtomicBoolean(true);
        Fixture f = fixture("unknown", 2L << 20, reached -> {
            if (reached == ImmutableArtifactStore.Boundary.RAW_DURABLE && failOnce.getAndSet(false))
                throw new IOException("physical write completed but outer publication failed");
        });
        byte[] original = new byte[] {4, 5, 6};
        try (var held = WindowsLedgerLock.acquire(f.lock)) {
            assertThrows(IOException.class, () -> f.store.publish(original, 10));
            assertTrue(f.guard.hasUnknownWrite()); long calls = f.guard.validations();
            assertThrows(IOException.class, () -> f.store.publish(new byte[] {7}, 10));
            assertEquals(calls, f.guard.validations()); assertEquals(1, files(f.root));
            f.guard.reconcileStorageOnly();
            assertFalse(f.guard.hasUnknownWrite());
            assertArrayEquals(original, f.store.read(f.store.publish(original, 10), 10));
        }
    }

    @Test void aLegacyGuardRetainsItsExactLocalBudgetCheckAfterExternalGrowth() throws IOException {
        Fixture f=fixture("legacy-growth",8192,reached -> {});
        assertTrue(f.guard.enforcedAggregateMaximumBytes(f.lock,f.root).isEmpty());
        Files.write(f.root.resolve("retained-foreign.bin"),new byte[16384],StandardOpenOption.CREATE_NEW);
        long calls=f.guard.validations();
        try(var held=WindowsLedgerLock.acquire(f.lock)){assertThrows(IOException.class,()->f.store.publish(new byte[]{1},10));}
        assertEquals(calls,f.guard.validations());
        assertTrue(f.store.retainedNativeBytes()>8192);
    }
}
