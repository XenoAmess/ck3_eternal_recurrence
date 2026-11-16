package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Tiny actual Store/Writer/Archive scopes and Win32 custody; no Root, Game, Driver or fabricated Session.
 * Proof continuity and optional payload residency are separate. No heap or payload-I/O count is inferred.
 * Existing ordinary Ledger identity/alias and historical poison/finish assertions are not modified here.
 */
final class HistoricalPayloadProofRetentionTest {
    private static final String MACHINE = "historical-payload-proof-software";
    private static final int MAXIMUM = 1 << 20;
    private static final long RESIDENT_BUDGET = 128L << 10;
    private static final ActionPorts.HistoricalReadLimits NORMAL = new ActionPorts.HistoricalReadLimits(4, RESIDENT_BUDGET, 12);
    @TempDir Path temporary;

    @Test void payloadRotationKeepsBothOriginalPairsAndVerifiedDependenciesUntilScopeClose() throws Exception {
        try (var f = new Fixture(temporary.resolve("rotation"))) {
            byte[] first = payload(80 << 10, 0x41), second = payload(80 << 10, 0x42);
            f.writer.locked(same -> {
                Pin a = f.store.publish(first, MAXIMUM), b = f.store.publish(second, MAXIMUM);
                var inventory = f.inventory();
                long writes = f.storage.successfulBatches();
                assertTrue((long) first.length + second.length > RESIDENT_BUDGET,
                        "both payload byte snapshots cannot be retained together within the declared byte budget");
                f.archive.inHistoricalReadScope(same, NORMAL, bound -> {
                    var reads = f.store.currentHistoricalReadsFor(same);
                    assertNotNull(reads);
                    try (var trace = reads.traceDependencies()) {
                        assertArrayEquals(first, f.store.read(a, MAXIMUM));
                        pairAccess(f, a.reference(), false);
                        assertArrayEquals(second, f.store.read(b, MAXIMUM));
                        pairAccess(f, a.reference(), false);
                        pairAccess(f, b.reference(), false);
                        var dependencies = trace.retainedDependencies().orElseThrow();
                        assertEquals(Set.of(a.reference(), b.reference()), dependencies);
                        assertTrue(reads.verifyRetainedDependencies(dependencies),
                                "optional payload rotation cannot retire either original proof pair");
                        pairAccess(f, a.reference(), false);
                        pairAccess(f, b.reference(), false);

                        // A is the FIFO payload victim; original custody remains continuous while its bytes are read again.
                        byte[] detached = f.store.read(a, MAXIMUM);
                        assertArrayEquals(first, detached);
                        Arrays.fill(detached, (byte) 0x7f);
                        assertArrayEquals(first, f.store.read(a, MAXIMUM));
                        assertArrayEquals(second, f.store.read(b, MAXIMUM));
                        assertTrue(reads.verifyRetainedDependencies(dependencies));
                        assertEquals(dependencies, trace.retainedDependencies().orElseThrow());
                        pairAccess(f, a.reference(), false);
                        pairAccess(f, b.reference(), false);
                    }
                    return null;
                });
                pairAccess(f, a.reference(), true);
                pairAccess(f, b.reference(), true);
                assertEquals(writes, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertEquals(inventory, f.inventory());
                f.assertCanonicalUnchanged();
                return null;
            });
        }
    }

    @Test void entryHandleAndMandatoryMetadataFallbackCannotBeRelabelledAsRetainedProof() throws Exception {
        try (var f = new Fixture(temporary.resolve("fallback"))) {
            byte[] first = payload(16, 0x31), second = payload(17, 0x32);
            f.writer.locked(same -> {
                Pin a = f.store.publish(first, MAXIMUM), b = f.store.publish(second, MAXIMUM);
                var inventory = f.inventory();
                long writes = f.storage.successfulBatches();
                var limits = List.of(new ActionPorts.HistoricalReadLimits(1, RESIDENT_BUDGET, 12),
                        new ActionPorts.HistoricalReadLimits(4, RESIDENT_BUDGET, 4));
                for (var limit : limits) {
                    f.archive.inHistoricalReadScope(same, limit, bound -> {
                        var reads = f.store.currentHistoricalReadsFor(same);
                        assertNotNull(reads);
                        try (var trace = reads.traceDependencies()) {
                            assertArrayEquals(first, f.store.read(a, MAXIMUM));
                            assertEquals(Set.of(a.reference()), trace.retainedDependencies().orElseThrow());
                            assertArrayEquals(second, f.store.read(b, MAXIMUM));
                            assertTrue(trace.retainedDependencies().isEmpty());
                            assertFalse(reads.verifyRetainedDependencies(Set.of(b.reference())));
                            pairAccess(f, a.reference(), false);
                            pairAccess(f, b.reference(), true);
                            assertTrue(reads.verifyRetainedDependencies(Set.of(a.reference())));
                            assertArrayEquals(first, f.store.read(a, MAXIMUM));
                            assertTrue(trace.retainedDependencies().isEmpty(),
                                    "a later held hit cannot repair an earlier unheld dependency in the same trace");
                            try (var inner = reads.traceDependencies()) {
                                assertArrayEquals(first, f.store.read(a, MAXIMUM));
                                assertEquals(Set.of(a.reference()), inner.retainedDependencies().orElseThrow());
                            }
                            assertTrue(trace.retainedDependencies().isEmpty());
                        }
                        return null;
                    });
                    pairAccess(f, a.reference(), true);
                    pairAccess(f, b.reference(), true);
                }

                long mandatoryMetadata = Files.size(f.commit(a.reference()));
                assertTrue(mandatoryMetadata > 1);
                var tooSmall = new ActionPorts.HistoricalReadLimits(4, mandatoryMetadata - 1, 12);
                f.archive.inHistoricalReadScope(same, tooSmall, bound -> {
                    var reads = f.store.currentHistoricalReadsFor(same);
                    assertNotNull(reads);
                    try (var trace = reads.traceDependencies()) {
                        assertArrayEquals(first, f.store.read(a, MAXIMUM));
                        assertTrue(trace.retainedDependencies().isEmpty());
                        assertFalse(reads.verifyRetainedDependencies(Set.of(a.reference())));
                        pairAccess(f, a.reference(), true);
                        assertArrayEquals(first, f.store.read(a, MAXIMUM));
                        assertTrue(trace.retainedDependencies().isEmpty());
                    }
                    return null; // Capacity fallback is a successful full read, not a caught validation failure.
                });
                pairAccess(f, a.reference(), true);
                assertEquals(writes, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertEquals(inventory, f.inventory());
                f.assertCanonicalUnchanged();
                return null;
            });
        }
    }

    @Test void releasingOnlyHistoricalPayloadKeepsItsPinAndCustodyWhileColdReadsStayDetached() throws Exception {
        try (var f = new Fixture(temporary.resolve("ledger"))) {
            byte[] input = payload(80 << 10, 0x55);
            f.writer.locked(same -> {
                Pin a = f.store.publish(input, MAXIMUM);
                var inventory = f.inventory();
                long writes = f.storage.successfulBatches();
                try (var metadata = LedgerFiles.lease(f.commit(a.reference()), 64 << 10);
                        var data = LedgerFiles.leaseHistorical(a.reference(), MAXIMUM)) {
                    Pin original = data.verifyCurrent();
                    assertSame(a.reference(), original.reference());
                    assertEquals(input.length, data.retainedBytes());
                    assertArrayEquals(input, data.read(MAXIMUM).bytes());
                    pairAccess(f, a.reference(), false);
                    assertEquals(input.length, data.releasePayload());
                    assertEquals(0, data.retainedBytes());
                    assertSame(original, data.verifyCurrent());
                    assertEquals(0, data.retainedBytes(), "fresh Pin verification must not refill the retired payload");
                    assertTrue(metadata.retainedBytes() > 0);
                    pairAccess(f, a.reference(), false);

                    var cold = data.read(MAXIMUM);
                    assertEquals(original, cold.pin());
                    assertArrayEquals(input, cold.bytes());
                    byte[] detached = cold.bytes();
                    Arrays.fill(detached, (byte) 0x7f);
                    assertArrayEquals(input, data.read(MAXIMUM).bytes());
                    assertEquals(0, data.retainedBytes(), "a detached cold result is not an implicit residency admission");
                    pairAccess(f, a.reference(), false);
                }
                pairAccess(f, a.reference(), true);
                assertEquals(writes, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertEquals(inventory, f.inventory());
                f.assertCanonicalUnchanged();
                return null;
            });
        }
    }

    private static byte[] payload(int length, int value) {
        byte[] bytes = new byte[length];
        Arrays.fill(bytes, (byte) value);
        return bytes;
    }

    /** Permission qualification only: no write, deletion, truncation, rename or disposition is requested. */
    private static void access(Path path, int requested, boolean allowed) throws IOException {
        HANDLE handle = Kernel32.INSTANCE.CreateFile(LedgerFiles.winPath(path), requested, 1 | 2 | 4, null, 3, 0x80, null);
        int error = Kernel32.INSTANCE.GetLastError();
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            if (allowed) throw new IOException("owned access qualification unexpectedly failed, Win32=" + error + ": " + path);
            assertEquals(32, error, "continuous custody must deny sharing, not rely on missing files or ACL rejection");
            return;
        }
        if (!Kernel32.INSTANCE.CloseHandle(handle))
            throw new IOException("owned access qualification CloseHandle failed, Win32=" + Kernel32.INSTANCE.GetLastError());
        assertTrue(allowed, "access unexpectedly opened while original custody should remain held: " + path);
    }

    private static void pairAccess(Fixture f, ExactRef ref, boolean allowed) throws IOException {
        for (Path path : List.of(Path.of(ref.path()), f.commit(ref))) {
            access(path, 0x40000000, allowed); // GENERIC_WRITE, OPEN_EXISTING only.
            access(path, 0x00010000, allowed); // DELETE access only; no deletion API is invoked.
        }
    }

    private static final class Fixture implements AutoCloseable {
        final Path root;
        final Path artifacts;
        final Layout layout;
        final byte[] initial;
        final StorageWriteGuardTestSupport storage;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;

        Fixture(Path directory) throws IOException {
            root = directory.toAbsolutePath().normalize();
            assertTrue(root.startsWith(Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize()));
            Files.createDirectory(root);
            var row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE)
                    .put("sequence", 0).put("window_id", 1).put("start_date_raw", 1000).put("target_date_raw", 1024)
                    .put("target_days", 1).put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 1000);
            initial = ContinuityJson.canonical(row);
            Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
            Files.write(snapshot, initial, StandardOpenOption.CREATE_NEW);
            Files.write(anchor, initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            artifacts = root.resolve("artifacts");
            Files.createDirectory(artifacts);
            Path sourceFile = root.resolve("source.txt");
            Files.writeString(sourceFile, "actual tiny historical proof fixture", StandardOpenOption.CREATE_NEW);
            var source = LedgerFiles.read(sourceFile, 1024).pin().reference();
            layout = new Layout(snapshot, LedgerFiles.read(anchor, 65536).pin().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifacts, layout.lock(), 8L << 20), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) {
                    throw new AssertionError("payload proof fixture cannot preview a canonical transition");
                }
                @Override public ContinuityState reduce(ContinuityState before, Request request) {
                    throw new AssertionError("payload proof fixture cannot commit a canonical transition");
                }
            }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), java.util.Optional.of(store), java.util.Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }

        Path commit(ExactRef reference) { return artifacts.resolve(reference.sha256() + ".commit.json"); }
        Set<String> inventory() throws IOException {
            try (var files = Files.list(artifacts)) {
                return files.map(path -> path.getFileName().toString()).collect(java.util.stream.Collectors.toCollection(TreeSet::new));
            }
        }
        void assertCanonicalUnchanged() throws IOException {
            assertArrayEquals(initial, Files.readAllBytes(layout.snapshot()));
            try (var events = Files.list(layout.events())) { assertEquals(0, events.count()); }
        }
        @Override public void close() throws IOException { storage.close(); }
    }
}
