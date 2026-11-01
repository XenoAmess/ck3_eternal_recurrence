package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Protocol parsing reuse over a real software archive; no Game or live session ledger is touched. */
final class ProtocolParseScope220Test {
    private static final String MACHINE = "archive-test-fixture";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final Set<StorageWriteGuardTestSupport> storageScopes = new java.util.LinkedHashSet<>();
    @AfterEach void closeStorageScopes() throws IOException {
        IOException failure = null;
        for (StorageWriteGuardTestSupport storage : storageScopes) {
            try { storage.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        storageScopes.clear();
        if (failure != null) throw failure;
    }
    private final class Fixture {
        final Path root;
        final Layout layout;
        final ExactRef source;
        final ImmutableArtifactStore artifacts;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root) throws IOException { this(root, false); }
        Fixture(Path root, boolean reopen) throws IOException {
            this.root = root;
            if (!reopen) {
                Files.createDirectory(root); byte[] state = ContinuityJson.canonical(state());
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
                Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
                Files.writeString(root.resolve("reviewed-source.txt"), "archive fixture source", StandardOpenOption.CREATE_NEW);
            }
            source = LedgerFiles.read(root.resolve("reviewed-source.txt"), 100).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65_536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = reopen ? StorageWriteGuardTestSupport.forLayout(layout) : StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            assertSame(storage, artifacts.storageGuard());
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { throw new IllegalStateException("archive fixture must never commit a ledger event"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(artifacts, writer);
        }
        G2Source source() { return new G2Source(MACHINE, NOW.toString(), "1.20.0.4", source); }
        static ObjectNode state() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
            row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
            row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
            row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0); var game = row.putObject("game_binding");
            game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
        }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    @FunctionalInterface private interface IoCall<T> { T run() throws IOException; }
    private static <T> T io(IoCall<T> work) {
        try { return work.run(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    private static long leafCount(Path directory) throws IOException {
        try (var entries = Files.list(directory)) { return entries.count(); }
    }

    @Test void sameScopeProtocolReuseAndDetachedBytes() throws IOException {
        Fixture f = fixture("protocol-reuse");
        RawJson original = raw("{\"retained\":true}");
        ExactRef ref = f.archive.preserveMaterial(original);

        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            RawJson first = bound.loadMaterial(ref);
            RawJson second = bound.loadMaterial(ref);
            assertSame(first, second);

            byte[] detached = first.bytes();
            detached[0] = 0;

            RawJson third = bound.loadMaterial(ref);
            assertSame(first, third);
            assertArrayEquals(original.bytes(), third.bytes());
            return null;
        }));
    }

    @Test void profileIsolationAndProtocolBound() throws IOException {
        Fixture f = fixture("profile-isolation");
        ExactRef normalRef = f.archive.preserveMaterial(raw("{\"small\":true}"));
        byte[] large = ("{\"large\":" + "7".repeat(5000) + "}").getBytes(StandardCharsets.UTF_8);
        RawJson fullOriginal = RawJson.fullMaterial(large);
        assertThrows(IllegalArgumentException.class, () -> new RawJson(large));
        assertThrows(IllegalArgumentException.class, fullOriginal::requireProtocolBound);
        ExactRef fullRef = f.archive.preserveMaterial(fullOriginal);
        for (boolean fullFirst : List.of(true, false)) {
            f.writer.locked(session -> f.archive.inSession(session, bound -> {
                RawJson normalNative = bound.loadMaterial(normalRef);
                RawJson normalFull = bound.loadFullMaterial(normalRef);
                assertSame(normalNative, bound.loadMaterial(normalRef));
                assertSame(normalFull, bound.loadFullMaterial(normalRef));
                if (!fullFirst) assertThrows(IllegalArgumentException.class, () -> bound.loadMaterial(fullRef));
                RawJson loadedFull = bound.loadFullMaterial(fullRef);
                assertSame(loadedFull, bound.loadFullMaterial(fullRef));
                assertArrayEquals(large, loadedFull.bytes());
                assertThrows(IllegalArgumentException.class, () -> bound.loadMaterial(fullRef));
                assertThrows(IllegalArgumentException.class, () -> bound.loadMaterial(fullRef));
                assertSame(loadedFull, bound.loadFullMaterial(fullRef));
                assertSame(normalNative, bound.loadMaterial(normalRef));
                assertSame(normalFull, bound.loadFullMaterial(normalRef));
                return null;
            }));
        }
    }

    @Test void scopeCleanupAndExceptionSafety() throws IOException {
        Fixture f = fixture("scope-cleanup");
        ExactRef ref = f.archive.preserveMaterial(raw("{\"scope\":true}"));
        AtomicReference<ActionPorts.OutcomeArchive> escaped = new AtomicReference<>();
        AtomicReference<RawJson> previous = new AtomicReference<>();
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            escaped.set(bound); RawJson loaded = bound.loadMaterial(ref); previous.set(loaded);
            assertSame(loaded, bound.loadMaterial(ref));
            return null;
        }));
        assertThrows(IllegalArgumentException.class, () -> escaped.get().loadMaterial(ref));
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            RawJson loaded = bound.loadMaterial(ref);
            assertNotSame(previous.get(), loaded); assertSame(loaded, bound.loadMaterial(ref));
            return null;
        }));
        f.writer.locked(session -> {
            assertThrows(AssertionError.class, () -> f.archive.inSession(session, bound -> {
                RawJson loaded = bound.loadMaterial(ref); previous.set(loaded);
                assertSame(loaded, bound.loadMaterial(ref)); throw new AssertionError("outer Error");
            }));
            return null;
        });
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            RawJson loaded = bound.loadMaterial(ref);
            assertNotSame(previous.get(), loaded); assertSame(loaded, bound.loadMaterial(ref));
            return null;
        }));
    }

    @Test void physicalOriginalsCheckedOnCacheHit() throws IOException {
        for (int mutation = 0; mutation < 3; mutation++) {
            Fixture f = fixture("protocol-tamper-" + mutation);
            RawJson original = raw("{\"retained\":true}");
            ExactRef ref = f.archive.preserveMaterial(original);
            byte[] ledger = Files.readAllBytes(f.layout.snapshot());
            int change = mutation;
            f.writer.locked(session -> f.archive.inSession(session, bound -> io(() -> {
                RawJson first = bound.loadMaterial(ref);
                assertSame(first, bound.loadMaterial(ref));
                byte[] detached = first.bytes(); detached[0] = 0;
                assertArrayEquals(original.bytes(), bound.loadMaterial(ref).bytes());
                Path payload = Path.of(ref.path());
                Path commit = payload.resolveSibling(ref.sha256() + ".commit.json");
                assertTrue(payload.startsWith(f.root)); assertTrue(commit.startsWith(f.root));
                if (change == 0) Files.writeString(payload,"{\"retained\":false}",StandardOpenOption.TRUNCATE_EXISTING);
                else if (change == 1) {
                    Path retained = payload.resolveSibling("kept-old-original.bin");
                    Files.move(payload, retained);
                    Files.write(payload, original.bytes(), StandardOpenOption.CREATE_NEW);
                    assertNotEquals(LedgerFiles.identity(retained).fileIdDecimal(), LedgerFiles.identity(payload).fileIdDecimal());
                } else Files.delete(commit);
                byte[] changed = Files.readAllBytes(payload);
                long count = leafCount(f.root.resolve("artifacts"));
                assertThrows(UncheckedIOException.class, () -> bound.loadMaterial(ref));
                assertArrayEquals(changed, Files.readAllBytes(payload));
                assertEquals(count, leafCount(f.root.resolve("artifacts")));
                if (change == 2) assertFalse(Files.exists(commit));
                return null;
            })));
            assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()));
        }
    }
}
