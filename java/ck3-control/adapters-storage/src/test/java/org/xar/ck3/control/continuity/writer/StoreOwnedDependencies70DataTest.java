package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileTime;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/**
 * Store70 owned-dependency tracing regression draft.
 * Exercises real ImmutableArtifactStore HistoricalReads/DependencyTrace APIs
 * against real Windows storage fixtures via WriterFixture.
 */
final class StoreOwnedDependencies70DataTest {
    @TempDir Path temp;

    private record Fixture(WriterFixture original, ImmutableArtifactStore store) { }
    private Fixture fixture(String name) throws IOException {
        WriterFixture original=new WriterFixture(temp.resolve(name));
        var store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(
                original.layout.snapshot().getParent().resolve("artifacts"),original.layout.lock(),2L<<20), original.storage);
        return new Fixture(original,store);
    }

    @Test void nestedTracesRetainActualReadsAndRestoreOuterScope() throws IOException {
        Fixture f = fixture("nested");
        try {
            byte[] payload1 = "nested-trace-data-1".getBytes(StandardCharsets.UTF_8);
            byte[] payload2 = "nested-trace-data-2".getBytes(StandardCharsets.UTF_8);
            Pin pin1, pin2;
            pin1 = f.original.writer.locked(session -> f.store.publish(payload1, 100));
            pin2 = f.original.writer.locked(session -> f.store.publish(payload2, 100));
            long beforeFiles = countFiles(f.original.layout.snapshot().getParent().resolve("artifacts"));
            long beforeBytes = f.store.retainedNativeBytes();

            f.original.writer.locked(session -> {
                var store = f.store;
                try (var reads = store.beginHistoricalReads(session, 4, 65536, 8, () -> session.requireWriter(f.original.layout.lock()))) {
                    try (var outer = reads.traceDependencies()) {
                        byte[] read1 = store.read(pin1, 100);
                        assertArrayEquals(payload1, read1);
                        try (var inner = reads.traceDependencies()) {
                            byte[] read2 = store.read(pin2, 100);
                            assertArrayEquals(payload2, read2);
                            var innerRefs = inner.retainedDependencies().orElseThrow();
                            assertEquals(1, innerRefs.size());
                            assertTrue(innerRefs.contains(pin2.reference()));
                        }
                        var outerRefs = outer.retainedDependencies().orElseThrow();
                        assertEquals(2, outerRefs.size());
                        assertTrue(outerRefs.contains(pin1.reference()));
                        assertTrue(outerRefs.contains(pin2.reference()));
                        assertTrue(reads.verifyRetainedDependencies(outerRefs));
                    }
                }
                return null;
            });
            long afterFiles = countFiles(f.original.layout.snapshot().getParent().resolve("artifacts"));
            long afterBytes = f.store.retainedNativeBytes();
            assertEquals(beforeFiles, afterFiles);
            assertEquals(beforeBytes, afterBytes);
        } finally {
            f.original.storage.close();
        }
    }

    @Test void budgetFallbackDisqualifiesTraceAndPreventsRetention() throws IOException {
        Fixture f = fixture("budget");
        try {
            byte[] payload1 = "budget-test-data-1".getBytes(StandardCharsets.UTF_8);
            byte[] payload2 = "budget-test-data-2".getBytes(StandardCharsets.UTF_8);
            Pin pin1, pin2;
            pin1 = f.original.writer.locked(session -> f.store.publish(payload1, 100));
            pin2 = f.original.writer.locked(session -> f.store.publish(payload2, 100));

            f.original.writer.locked(session -> {
                var store = f.store;
                // Entry limit 1: first read retained, second falls back and disqualifies
                try (var reads = store.beginHistoricalReads(session, 1, 65536, 8, () -> session.requireWriter(f.original.layout.lock()))) {
                    try (var trace = reads.traceDependencies()) {
                        byte[] read1 = store.read(pin1, 100);
                        assertArrayEquals(payload1, read1);
                        byte[] read2 = store.read(pin2, 100);
                        assertArrayEquals(payload2, read2);
                        var refs = trace.retainedDependencies();
                        assertTrue(refs.isEmpty());
                        assertFalse(reads.verifyRetainedDependencies(Set.of(pin1.reference(), pin2.reference())));
                    }
                }
                return null;
            });

            // New scope does not inherit old refs
            f.original.writer.locked(session -> {
                var store = f.store;
                try (var reads = store.beginHistoricalReads(session, 4, 65536, 8, () -> session.requireWriter(f.original.layout.lock()))) {
                    try (var trace = reads.traceDependencies()) {
                        var refs = trace.retainedDependencies().orElseThrow();
                        assertEquals(0, refs.size());
                    }
                }
                return null;
            });
        } finally {
            f.original.storage.close();
        }
    }


    @Test void disqualificationIsStickyAcrossNestedTracesAndAuthorityFailurePoisonsOnlyItsOwnedScope() throws IOException {
        Fixture f=fixture("poison");
        try {
            byte[] bytes="poison-original".getBytes(StandardCharsets.UTF_8);
            Pin pin=f.original.writer.locked(session->f.store.publish(bytes,100));
            f.original.writer.locked(session->{
                try(var reads=f.store.beginHistoricalReads(session,4,65536,8,()->session.requireWriter(f.original.layout.lock()));
                        var outer=reads.traceDependencies()) {
                    assertArrayEquals(bytes,f.store.read(pin,100));
                    try(var inner=reads.traceDependencies()) {
                        reads.disqualifyDependencies();
                        assertTrue(inner.retainedDependencies().isEmpty());
                    }
                    assertTrue(outer.retainedDependencies().isEmpty());
                    assertTrue(reads.verifyRetainedDependencies(Set.of(pin.reference())));
                    assertTrue(outer.retainedDependencies().isEmpty(),"fresh custody cannot erase an actual opaque dependency");
                }
                return null;
            });
            IOException marker=new IOException("actual authority callback failure");
            AtomicBoolean active=new AtomicBoolean(true);
            IOException escaping=assertThrows(IOException.class,()->f.original.writer.locked(session->{
                try(var reads=f.store.beginHistoricalReads(session,4,65536,8,()->{
                        session.requireWriter(f.original.layout.lock());if(!active.get())throw marker;
                    });var trace=reads.traceDependencies()) {
                    assertArrayEquals(bytes,f.store.read(pin,100));
                    var dependencies=trace.retainedDependencies().orElseThrow();
                    active.set(false);
                    assertSame(marker,assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies)));
                    active.set(true);
                    IOException poisoned=assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies));
                    assertTrue(contains(poisoned,marker));
                }
                return null;
            }));
            assertTrue(contains(escaping,marker));
            f.original.writer.locked(session->{
                try(var reads=f.store.beginHistoricalReads(session,4,65536,8,()->session.requireWriter(f.original.layout.lock()));
                        var trace=reads.traceDependencies()) {
                    assertTrue(trace.retainedDependencies().orElseThrow().isEmpty());
                    assertArrayEquals(bytes,f.store.read(pin,100));
                    assertTrue(reads.verifyRetainedDependencies(trace.retainedDependencies().orElseThrow()));
                }
                return null;
            });
        } finally { f.original.storage.close(); }
    }

    @Test void heldHandlesDoNotHideChangedPayloadMetadataAndFailedRevalidationRemainsPoisoned() throws IOException {
        Fixture f=fixture("metadata");
        try {
            byte[] bytes="held-metadata-original".getBytes(StandardCharsets.UTF_8);
            Pin pin=f.original.writer.locked(session->f.store.publish(bytes,100));
            Path payload=Path.of(pin.reference().path());
            FileTime original=Files.getLastModifiedTime(payload);
            IOException escaping=assertThrows(IOException.class,()->f.original.writer.locked(session->{
                try(var reads=f.store.beginHistoricalReads(session,4,65536,8,()->session.requireWriter(f.original.layout.lock()));
                        var trace=reads.traceDependencies()) {
                    assertArrayEquals(bytes,f.store.read(pin,100));
                    var dependencies=trace.retainedDependencies().orElseThrow();
                    assertTrue(reads.verifyRetainedDependencies(dependencies));
                    try {
                        Files.setLastModifiedTime(payload,FileTime.fromMillis(original.toMillis()+10000));
                        assertNotEquals(original,Files.getLastModifiedTime(payload));
                        assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies));
                    } finally { Files.setLastModifiedTime(payload,original); }
                    assertThrows(IOException.class,()->reads.verifyRetainedDependencies(dependencies),
                            "restoring metadata never erases the already observed failure");
                }
                return null;
            }));
            assertNotNull(escaping);
            assertEquals(original,Files.getLastModifiedTime(payload));
            assertArrayEquals(bytes,f.store.read(pin,100));
        } finally { f.original.storage.close(); }
    }
    private static boolean contains(Throwable failure,Throwable expected) {
        if(failure==expected)return true;
        if(failure.getCause()!=null&&contains(failure.getCause(),expected))return true;
        for(Throwable suppressed:failure.getSuppressed())if(contains(suppressed,expected))return true;
        return false;
    }

    private static long countFiles(Path path) throws IOException {
        try (var stream = Files.list(path)) { return stream.count(); }
    }
}