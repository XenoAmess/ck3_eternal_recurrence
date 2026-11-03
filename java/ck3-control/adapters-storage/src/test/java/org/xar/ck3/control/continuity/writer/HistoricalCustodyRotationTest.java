package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** New bounded-custody behavior; owned Windows originals and actual software Writer session only. */
final class HistoricalCustodyRotationTest {
    private static final int LIMIT = 4096;
    private static final String MACHINE = "historical-custody-rotation-software";
    private static final byte[] FIRST = "first literal owned payload\n".getBytes(StandardCharsets.UTF_8);
    private static final byte[] SECOND = "second literal \u00c5 \u4e2d \uD83C\uDF0B payload\n".getBytes(StandardCharsets.UTF_8);
    @TempDir Path temporary;

    @Test void entryAndHandlePressureReleaseOldPairsAndReacquireExactOriginals() throws Exception {
        int[][] limits = { {1, 8}, {4, 4} };
        for (int i = 0; i < limits.length; i++) {
            try (Fixture f = new Fixture(temporary.resolve("pressure-" + i))) {
                int entries = limits[i][0], handles = limits[i][1];
                f.writer.locked(session -> {
                    Pin first = f.store.publish(FIRST, LIMIT);
                    Pin second = f.store.publish(SECOND, LIMIT);
                    var writesBefore = f.storage.successfulBatches();
                    try (var reads = f.store.beginHistoricalReads(session, entries, 65536, handles,
                            () -> session.requireWriter(f.layout.lock()))) {
                        reads.requireActive();
                        assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                        assertPairWriteDenied(f, first);
                        byte[] detached = f.store.read(second.reference(), LIMIT);
                        assertArrayEquals(SECOND, detached);
                        assertPairWriteAllowed(f, first);
                        assertPairWriteDenied(f, second);
                        Arrays.fill(detached, (byte) 0);
                        assertArrayEquals(SECOND, f.store.read(second, LIMIT));

                        // A is no longer held: returning to it must establish new complete custody.
                        assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                        assertPairWriteAllowed(f, second);
                        assertPairWriteDenied(f, first);
                    }
                    assertPairWriteAllowed(f, first);
                    assertPairWriteAllowed(f, second);
                    assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                    assertArrayEquals(SECOND, f.store.read(second, LIMIT));
                    assertEquals(writesBefore, f.storage.successfulBatches());
                    assertFalse(f.storage.hasUnknownWrite());
                    assertCanonicalUnchanged(f);
                    return null;
                });
            }
        }
    }

    @Test void inadmissiblePayloadPreservesOldCustodyAndRetiredTamperPoisonsScope() throws Exception {
        try (Fixture f = new Fixture(temporary.resolve("byte-inadmissible"))) {
            f.writer.locked(session -> {
                byte[] large = new byte[2048];
                Arrays.fill(large, (byte) 0x5a);
                Pin first = f.store.publish(FIRST, LIMIT);
                Pin second = f.store.publish(large, LIMIT);
                long budget = Files.size(Path.of(first.reference().path())) + Files.size(commit(f, first));
                assertTrue(FIRST.length <= budget / 2);
                assertTrue(large.length > budget / 2);
                var writesBefore = f.storage.successfulBatches();
                try (var reads = f.store.beginHistoricalReads(session, 1, budget, 4,
                        () -> session.requireWriter(f.layout.lock()))) {
                    reads.requireActive();
                    assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                    assertPairWriteDenied(f, first);
                    assertArrayEquals(large, f.store.read(second, LIMIT));
                    // Retiring A could not admit B: A must remain held, B uses the full strict reader.
                    assertPairWriteDenied(f, first);
                    assertPairWriteAllowed(f, second);
                    assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                }
                assertPairWriteAllowed(f, first);
                assertEquals(writesBefore, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertCanonicalUnchanged(f);
                return null;
            });
        }
        try (Fixture f = new Fixture(temporary.resolve("retired-tamper"))) {
            f.writer.locked(session -> {
                Pin first = f.store.publish(FIRST, LIMIT);
                Pin second = f.store.publish(SECOND, LIMIT);
                var writesBefore = f.storage.successfulBatches();
                IOException[] original = new IOException[1];
                IOException closeFailure = assertThrows(IOException.class, () -> {
                    try (var reads = f.store.beginHistoricalReads(session, 1, 65536, 4,
                            () -> session.requireWriter(f.layout.lock()))) {
                        reads.requireActive();
                        assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                        assertArrayEquals(SECOND, f.store.read(second, LIMIT));
                        assertPairWriteAllowed(f, first);
                        byte[] changed = FIRST.clone();
                        changed[0] ^= 1;
                        Files.write(Path.of(first.reference().path()), changed);
                        original[0] = assertThrows(IOException.class, () -> f.store.read(first, LIMIT));
                        assertTrue(original[0].getMessage().contains("bytes/SHA/path changed"));
                        IOException blocked = assertThrows(IOException.class, () -> f.store.read(second, LIMIT));
                        assertTrue(blocked.getMessage().contains("already failed"));
                        // Catching both errors must not grant successful completion of this scope.
                    }
                });
                assertTrue(closeFailure.getMessage().contains("caught failure cannot grant a result"));
                assertSame(original[0], closeFailure.getCause());
                assertPairWriteAllowed(f, second);
                assertArrayEquals(SECOND, f.store.read(second, LIMIT));
                assertEquals(writesBefore, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertCanonicalUnchanged(f);
                return null;
            });
        }
    }

    private static Path commit(Fixture f, Pin pin) {
        return f.archive.resolve(pin.reference().sha256() + ".commit.json");
    }

    private static void writeOpen(Path path) throws IOException {
        try (var channel = Files.newByteChannel(path, StandardOpenOption.WRITE)) {
            assertTrue(channel.isOpen());
        }
    }

    private static void assertPairWriteDenied(Fixture f, Pin pin) {
        assertThrows(IOException.class, () -> writeOpen(Path.of(pin.reference().path())));
        assertThrows(IOException.class, () -> writeOpen(commit(f, pin)));
    }

    private static void assertPairWriteAllowed(Fixture f, Pin pin) throws IOException {
        writeOpen(Path.of(pin.reference().path()));
        writeOpen(commit(f, pin));
    }

    private static void assertCanonicalUnchanged(Fixture f) throws IOException {
        assertArrayEquals(f.initial, Files.readAllBytes(f.layout.snapshot()));
        try (var entries = Files.newDirectoryStream(f.layout.events())) { assertFalse(entries.iterator().hasNext()); }
    }

    private static ObjectNode initial() {
        ObjectNode row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1")
                .put("machine_id", MACHINE).put("sequence", 0).put("window_id", 1)
                .put("start_date_raw", 1000).put("target_date_raw", 1024).put("target_days", 1)
                .put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 1000);
        row.putArray("unknown_requests").add("keep-exact");
        return row.put("NEXT", 73).putNull("pending_checkpoint");
    }

    private static ExactRef ref(Path path) throws Exception {
        byte[] raw = Files.readAllBytes(path);
        return new ExactRef(path.toAbsolutePath().normalize().toString(), raw.length,
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }

    private static final class Fixture implements AutoCloseable {
        private final Layout layout;
        private final Path archive;
        private final byte[] initial;
        private final StorageWriteGuardTestSupport storage;
        private final ContinuityWriter writer;
        private final ImmutableArtifactStore store;
        private Fixture(Path directory) throws Exception {
            Path root = directory.toAbsolutePath().normalize();
            assertTrue(root.startsWith(Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize()));
            Files.createDirectory(root);
            initial = ContinuityJson.canonical(initial());
            Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
            Files.write(snapshot, initial);
            Files.write(anchor, initial);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path source = root.resolve("owned-source.txt");
            Files.writeString(source, "finite original software input");
            layout = new Layout(snapshot, ref(anchor), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            writer = new ContinuityWriter(layout, List.of(ref(source)), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) {
                    throw new AssertionError("This fixture performs no Writer state transition");
                }
                @Override public ContinuityState reduce(ContinuityState before, Request request) {
                    throw new AssertionError("This fixture performs no Writer state transition");
                }
            }, Clock.fixed(Instant.parse("2023-01-01T00:00:00Z"), ZoneOffset.UTC), storage);
            archive = root.resolve("archive");
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive, layout.lock(), 64L * 1024 * 1024), storage);
        }
        @Override public void close() throws IOException { storage.close(); }
    }
}
