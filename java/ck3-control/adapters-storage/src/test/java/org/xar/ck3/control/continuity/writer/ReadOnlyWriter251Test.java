package org.xar.ck3.control.continuity.writer;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Pure denial tests. The owner had reviewed production; no physical source/lock is opened. */
final class ReadOnlyWriter251Test {
    private static final Path ROOT = Path.of("D:/__readonly_writer_251_pure_input__").toAbsolutePath().normalize();
    private static final ExactRef SOURCE = new ExactRef(ROOT.resolve("source.json").toString(), 1, "1".repeat(64));
    private static final Layout LAYOUT = new Layout(ROOT.resolve("continuity.json"), SOURCE, "pure-reader251");
    private static final TransitionAuthority NEVER = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState before, Request request) {
            throw new AssertionError("readonly construction/denial must not call an authority");
        }
        @Override public ContinuityState reduce(ContinuityState before, Request request) {
            throw new AssertionError("readonly construction/denial must not call a reducer");
        }
    };

    private static StorageWriteGuard foreignGuard() {
        return new StorageWriteGuard() {
            @Override public void close() { }
            @Override public void requireInitialization(Path lock, List<Path> roots) {
                throw new AssertionError("a role mismatch must not invoke initialization");
            }
            @Override public <T> T write(WritePlan plan, PhysicalWrite<T> io) {
                throw new AssertionError("a role mismatch must not invoke writing");
            }
        };
    }

    private static ContinuityWriter reader(StorageWriteGuard guard) throws IOException {
        return ContinuityWriter.readOnlyExisting(LAYOUT, List.of(SOURCE), NEVER,
                Clock.systemUTC(), ContinuityWriter.Extensions.none(), guard);
    }

    private static void denies(org.junit.jupiter.api.function.Executable operation, String exactMessage) {
        IOException failure = assertThrows(IOException.class, operation);
        assertEquals(exactMessage, failure.getMessage());
    }

    @Test void nominalRoleIsIndependentAndCannotBeClaimedByAnOrdinaryGuard() throws Exception {
        StorageWriteGuard first = StorageWriteGuard.noWrites();
        StorageWriteGuard second = StorageWriteGuard.noWrites();
        assertNotSame(first, second);
        assertTrue(StorageWriteGuard.isNoWrites(first));
        assertTrue(StorageWriteGuard.isNoWrites(second));
        assertFalse(StorageWriteGuard.isNoWrites(null));
        StorageWriteGuard foreign = foreignGuard();
        assertFalse(StorageWriteGuard.isNoWrites(foreign));
        denies(() -> StorageWriteGuard.requireNoWritesOpen(null), "NoWrites role required");
        denies(() -> StorageWriteGuard.requireNoWritesOpen(foreign), "NoWrites role required");
        StorageWriteGuard.requireNoWritesOpen(first);
        first.close();
        first.close();
        assertTrue(StorageWriteGuard.isNoWrites(first));
        denies(() -> StorageWriteGuard.requireNoWritesOpen(first), "NoWrites role is closed");
        StorageWriteGuard.requireNoWritesOpen(second);
        second.close();
    }

    @Test void noWritesRejectsInitializationQuotaAndIoCallbackBeforeUsingInputs() throws Exception {
        StorageWriteGuard guard = StorageWriteGuard.noWrites();
        AtomicBoolean callback = new AtomicBoolean();
        denies(() -> guard.requireInitialization(null, null), "NoWrites guard denies initialization");
        denies(() -> guard.enforcedAggregateMaximumBytes(null, null), "NoWrites guard denies quota enforcement");
        denies(() -> guard.write(null, () -> { callback.set(true); return null; }), "NoWrites guard denies writes");
        denies(() -> guard.write(null, null), "NoWrites guard denies writes");
        assertFalse(callback.get());
        guard.close();
        denies(() -> guard.requireInitialization(null, null), "NoWrites guard denies initialization");
        denies(() -> guard.enforcedAggregateMaximumBytes(null, null), "NoWrites guard denies quota enforcement");
        denies(() -> guard.write(null, () -> { callback.set(true); return null; }), "NoWrites guard denies writes");
        assertFalse(callback.get());
    }

    @Test void readOnlyFactoryAndPublicMutationsDenyBeforeArgumentsAuthorityOrPhysicalAccess() throws Exception {
        StorageWriteGuard guard = StorageWriteGuard.noWrites();
        ContinuityWriter writer = reader(guard);
        assertSame(guard, writer.storageGuard());
        assertEquals(LAYOUT.lock(), writer.originalLockPath());
        assertTrue(writer.artifactStore().isEmpty());
        denies(() -> writer.preview(null), "readonly writer cannot preview");
        denies(() -> writer.commit(null), "readonly writer cannot commit");
        denies(() -> writer.previewImport(null), "readonly writer cannot preview import");
        denies(() -> writer.commitImport(null), "readonly writer cannot commit import");
        denies(() -> writer.previewRollback(null), "readonly writer cannot preview rollback");
        denies(() -> writer.commitRollback(null), "readonly writer cannot commit rollback");
        denies(() -> ContinuityWriter.initializeFresh(null, null, null, guard),
                "genesis cannot use a no-writes denial guard");
        guard.close();
    }

    @Test void mutableConstructionAndClosedReaderRejectBeforeInitializationOrCanonicalLock() throws Exception {
        StorageWriteGuard guard = StorageWriteGuard.noWrites();
        ContinuityWriter writer = reader(guard);
        denies(() -> new ContinuityWriter(LAYOUT, List.of(SOURCE), NEVER, guard),
                "mutable writer cannot use a NoWrites role");
        denies(() -> ContinuityWriter.readOnlyExisting(null, null, null, null, null, foreignGuard()),
                "NoWrites role required");
        guard.close();
        denies(() -> reader(guard), "NoWrites role is closed");
        denies(() -> new ContinuityWriter(LAYOUT, List.of(SOURCE), NEVER, guard),
                "mutable writer cannot use a NoWrites role");
        denies(() -> writer.locked(null), "NoWrites role is closed");
        denies(writer::persistedHead, "NoWrites role is closed");
    }
}
