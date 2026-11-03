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
final class HistoricalSourceBoundariesTest {
    private static final int LIMIT = 4096;
    private static final String MACHINE = "historical-source-boundaries-software";
    private static final byte[] FIRST = "first literal owned payload\n".getBytes(StandardCharsets.UTF_8);
    private static final byte[] SECOND = "second literal \u00c5 \u4e2d \uD83C\uDF0B payload\n".getBytes(StandardCharsets.UTF_8);
    @TempDir Path temporary;

    @Test void rootIdentityReplacementPoisonsCurrentScopeWithoutPublishing() throws Exception {
        try (Fixture f = new Fixture(temporary.resolve("root-replacement"))) {
            f.writer.locked(session -> {
                Pin pin = f.store.publish(FIRST, LIMIT);
                var writesBefore = f.storage.successfulBatches();
                IOException[] first = new IOException[1];
                IOException poisoned = assertThrows(IOException.class, () -> {
                    try (var reads = f.store.beginHistoricalReads(session, 1, 65536, 4,
                            () -> session.requireWriter(f.layout.lock()))) {
                        reads.requireActive();
                        // No custody has been opened. Both directories remain under this owned fixture.
                        Files.move(f.archive, f.archive.resolveSibling("prior-archive"));
                        Files.createDirectory(f.archive);
                        first[0] = assertThrows(IOException.class, () -> f.store.read(pin, LIMIT));
                        assertEquals("artifact root native identity changed", first[0].getMessage());
                        assertThrows(IOException.class, reads::requireActive);
                    }
                });
                assertTrue(poisoned.getMessage().contains("caught failure cannot grant a result"));
                assertSame(first[0], poisoned.getCause());
                assertEquals(writesBefore, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertCanonicalUnchanged(f);
                return null;
            });
        }
    }

    @Test void currentMaximumRemainsStrictForHeldOriginalAndCaughtFailure() throws Exception {
        try (Fixture f = new Fixture(temporary.resolve("current-maximum"))) {
            f.writer.locked(session -> {
                Pin pin = f.store.publish(FIRST, LIMIT);
                var writesBefore = f.storage.successfulBatches();
                IOException[] first = new IOException[1];
                IOException poisoned = assertThrows(IOException.class, () -> {
                    try (var reads = f.store.beginHistoricalReads(session, 1, 65536, 4,
                            () -> session.requireWriter(f.layout.lock()))) {
                        reads.requireActive();
                        assertArrayEquals(FIRST, f.store.read(pin, LIMIT));
                        assertArrayEquals(FIRST, f.store.read(pin.reference(), LIMIT));
                        first[0] = assertThrows(IOException.class,
                                () -> f.store.read(pin.reference(), FIRST.length - 1));
                        assertEquals("artifact reference is outside its exact content-addressed root or declared bound",
                                first[0].getMessage());
                        IOException blocked = assertThrows(IOException.class, () -> f.store.read(pin, LIMIT));
                        assertTrue(blocked.getMessage().contains("already failed"));
                    }
                });
                assertSame(first[0], poisoned.getCause());
                assertTrue(poisoned.getMessage().contains("caught failure cannot grant a result"));
                assertArrayEquals(FIRST, f.store.read(pin, LIMIT));
                assertEquals(writesBefore, f.storage.successfulBatches());
                assertFalse(f.storage.hasUnknownWrite());
                assertCanonicalUnchanged(f);
                return null;
            });
        }
    }

    @Test void publicCommitStampPreservesAsciiLanguageAndFirstErrorOrdering() throws Exception {
        String[] invalid = { "00", "1\n", "\uFF11", "\uD835\uDFD9" };
        for (int index = 0; index < invalid.length; index++) {
            String replacement = invalid[index];
            try (Fixture f = new Fixture(temporary.resolve("stamp-invalid-" + index))) {
                f.writer.locked(session -> {
                    Pin pin = f.store.publish(FIRST, LIMIT);
                    ObjectNode row = (ObjectNode) StrictJson.parse(Files.readAllBytes(commit(f, pin)));
                    ((ObjectNode) row.get("commit_identity")).put("volume", replacement);
                    Files.write(commit(f, pin), StrictJson.canonical(row));
                    var writesBefore = f.storage.successfulBatches();
                    var failure = assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,
                            () -> f.store.read(pin, LIMIT));
                    assertEquals("canonical decimal native FileID required", failure.getMessage());
                    assertEquals(writesBefore, f.storage.successfulBatches());
                    assertFalse(f.storage.hasUnknownWrite());
                    assertCanonicalUnchanged(f);
                    return null;
                });
            }
        }
        try (Fixture f = new Fixture(temporary.resolve("stamp-text-first"))) {
            f.writer.locked(session -> {
                Pin pin = f.store.publish(FIRST, LIMIT);
                ObjectNode row = (ObjectNode) StrictJson.parse(Files.readAllBytes(commit(f, pin)));
                ObjectNode self = (ObjectNode) row.get("commit_identity");
                self.put("volume", "x");
                self.put("created", false);
                Files.write(commit(f, pin), StrictJson.canonical(row));
                var failure = assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,
                        () -> f.store.read(pin, LIMIT));
                // All text getters run before validating the earlier malformed decimal volume.
                assertEquals("JSON string required", failure.getMessage());
                assertCanonicalUnchanged(f);
                return null;
            });
        }
        try (Fixture f = new Fixture(temporary.resolve("stamp-empty-text-first"))) {
            f.writer.locked(session -> {
                Pin pin = f.store.publish(FIRST, LIMIT);
                ObjectNode row = (ObjectNode) StrictJson.parse(Files.readAllBytes(commit(f, pin)));
                ((ObjectNode) row.get("commit_identity")).put("volume", "");
                Files.write(commit(f, pin), StrictJson.canonical(row));
                var failure = assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,
                        () -> f.store.read(pin, LIMIT));
                assertEquals("nonempty bounded text required", failure.getMessage());
                assertCanonicalUnchanged(f);
                return null;
            });
        }
        for (int index = 0; index < 2; index++) {
            int variant = index;
            try (Fixture f = new Fixture(temporary.resolve("stamp-canonical-format-" + index))) {
                f.writer.locked(session -> {
                    Pin pin = f.store.publish(FIRST, LIMIT);
                    assertArrayEquals(FIRST, f.store.read(pin, LIMIT));
                    ObjectNode row = (ObjectNode) StrictJson.parse(Files.readAllBytes(commit(f, pin)));
                    ObjectNode self = (ObjectNode) row.get("commit_identity");
                    String replacement = variant == 0
                            ? (self.get("volume").textValue().equals("0") ? "1" : "0") : "9".repeat(80);
                    self.put("volume", replacement);
                    Files.write(commit(f, pin), StrictJson.canonical(row));
                    // Decimal format is valid, including wider than primitive integer ranges;
                    // fresh actual native self identity must still reject a different value.
                    IOException failure = assertThrows(IOException.class, () -> f.store.read(pin, LIMIT));
                    assertEquals("commit replaced under same name/FileID", failure.getMessage());
                    assertCanonicalUnchanged(f);
                    return null;
                });
            }
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
