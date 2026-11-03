package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
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
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Tiny owned Windows originals and the actual software Writer lock; no Root/Game authority. */
final class PublicationLocalCopyTest {
    private static final int LIMIT = 4096;
    private static final String MACHINE = "publication-local-copy-software";
    private static final byte[] FIRST = "first literal owned payload\n".getBytes(StandardCharsets.UTF_8);
    private static final byte[] SECOND = "second literal \u00c5 \u4e2d \uD83C\uDF0B payload\n".getBytes(StandardCharsets.UTF_8);
    @TempDir Path temporary;

    @Test void publishedAndFallbackReadsRemainExactAndDetached() throws Exception {
        try (Fixture f = new Fixture(temporary.resolve("valid"))) {
            f.writer.locked(session -> {
                Pin first = f.store.publish(FIRST, LIMIT);
                Pin second = f.store.publish(SECOND, LIMIT);
                assertEquals(second, f.store.referenceOf(SECOND, LIMIT));
                assertEquals(second, f.store.referenceOf(second.reference().sha256(), SECOND.length, LIMIT));
                assertArrayEquals(SECOND, f.store.read(second, LIMIT));
                byte[] outside = f.store.read(second.reference(), LIMIT);
                outside[0] ^= 0x7f;
                assertArrayEquals(SECOND, f.store.read(second, LIMIT));

                // Four handles admit the first retained pair plus its transient qualification handles.
                // The second distinct ref then uses the existing bounded fallback, without a new policy.
                try (var reads = f.store.beginHistoricalReads(session, 4, 65536, 4,
                        () -> session.requireWriter(f.layout.lock()))) {
                    reads.requireActive();
                    assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                    byte[] detached = f.store.read(second.reference(), LIMIT);
                    assertArrayEquals(SECOND, detached);
                    Arrays.fill(detached, (byte) 0);
                    assertArrayEquals(SECOND, f.store.read(second, LIMIT));
                    assertEquals(second, f.store.referenceOf(SECOND, LIMIT));
                }
                assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                assertArrayEquals(SECOND, Files.readAllBytes(Path.of(second.reference().path())));
                assertCanonicalUnchanged(f);
                assertFalse(f.storage.hasUnknownWrite());
                return null;
            });
        }
    }

    @Test void freshTamperPoisonsScopeAndMetadataFailurePrecedesMissingPayload() throws Exception {
        try (Fixture f = new Fixture(temporary.resolve("fallback-tamper"))) {
            f.writer.locked(session -> {
                Pin first = f.store.publish(FIRST, LIMIT);
                Pin second = f.store.publish(SECOND, LIMIT);
                var writesBefore = f.storage.successfulBatches();
                IOException poisoned = assertThrows(IOException.class, () -> {
                    try (var reads = f.store.beginHistoricalReads(session, 4, 65536, 4,
                            () -> session.requireWriter(f.layout.lock()))) {
                        reads.requireActive();
                        assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                        assertArrayEquals(SECOND, f.store.read(second, LIMIT));
                        byte[] changed = SECOND.clone();
                        changed[0] ^= 1;
                        Files.write(Path.of(second.reference().path()), changed);
                        IOException rejected = assertThrows(IOException.class, () -> f.store.read(second, LIMIT));
                        assertTrue(rejected.getMessage().startsWith("named source bytes/SHA/path changed: path="));
                        assertTrue(rejected.getMessage().contains("expected_bytes=" + SECOND.length));
                        assertTrue(rejected.getMessage().contains("expected_sha256=" + second.reference().sha256()));
                        // The caught original failure cannot let the surrounding historical scope succeed.
                    }
                });
                assertTrue(poisoned.getMessage().contains("caught failure cannot grant a result"));
                assertEquals(writesBefore, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertCanonicalUnchanged(f);
                // No byte restoration/old-Pin assumption: only the untouched independent first original is read.
                assertArrayEquals(FIRST, f.store.read(first, LIMIT));
                return null;
            });
        }
        try (Fixture f = new Fixture(temporary.resolve("metadata-first"))) {
            f.writer.locked(session -> {
                Pin second = f.store.publish(SECOND, LIMIT);
                Path commit = f.archive.resolve(second.reference().sha256() + ".commit.json");
                Files.writeString(commit, "{", StandardCharsets.UTF_8);
                Files.delete(Path.of(second.reference().path()));
                var writesBefore = f.storage.successfulBatches();
                assertThrows(ContractViolationException.class, () -> f.store.read(second, LIMIT));
                assertEquals(writesBefore, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertCanonicalUnchanged(f);
                return null;
            });
        }
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
