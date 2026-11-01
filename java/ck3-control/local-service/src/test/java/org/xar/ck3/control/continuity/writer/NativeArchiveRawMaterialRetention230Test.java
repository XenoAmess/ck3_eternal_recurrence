package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.FileTime;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;

/** Real owned Windows archive/store integration for RawJson material retention policy. */
final class NativeArchiveRawMaterialRetention230Test {
    private static final String MACHINE = "raw-material-retention-fixture";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final java.util.Set<StorageWriteGuardTestSupport> scopes = new java.util.LinkedHashSet<>();

    @AfterEach void closeScopes() throws IOException {
        IOException failure = null;
        for (StorageWriteGuardTestSupport storage : scopes) {
            try { storage.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        scopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final Path root;
        final Layout layout;
        final ExactRef source;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root) throws IOException {
            this.root = root;
            Files.createDirectory(root);
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "actual reviewed fixture source", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = StorageWriteGuardTestSupport.create(layout);
            scopes.add(storage);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("archive fixture must not commit"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        static ObjectNode state() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
            row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
            row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
            row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
            row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
        }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }

    private static Path payload(ExactRef ref) { return Path.of(ref.path()); }
    private static Path commit(ExactRef ref) { return payload(ref).resolveSibling(ref.sha256() + ".commit.json"); }
    private static java.util.Set<String> inventory(Path root) throws IOException {
        try (var entries = Files.list(root)) {
            return entries.map(p -> p.getFileName().toString()).collect(Collectors.toUnmodifiableSet());
        }
    }
    private static void unchanged(Fixture f, byte[] snapshot, java.util.Set<String> entries) throws IOException {
        assertArrayEquals(snapshot, Files.readAllBytes(f.layout.snapshot()));
        assertEquals(entries, inventory(f.root.resolve("artifacts")));
    }
    private static ExactRef publish(Fixture f, byte[] value) throws IOException {
        return f.writer.locked(session -> f.archive.inSession(session,
                bound -> bound.preserveMaterial(new RawJson(value))));
    }


    private static final ActionPorts.HistoricalReadLimits LIMITS =
            new ActionPorts.HistoricalReadLimits(1, 1024 * 1024, 4);

    private static ExactRef publishFull(Fixture f, byte[] value) throws IOException {
        return f.writer.locked(session -> f.archive.inSession(session,
                bound -> bound.preserveMaterial(RawJson.fullMaterial(value))));
    }

    @Test void recentUseEvictionAllowsLaterAdmission() throws IOException {
        Fixture f = fixture("eviction");
        List<ExactRef> refs = new ArrayList<>();
        List<byte[]> known = new ArrayList<>();
        for (int i = 0; i < 65; i++) {
            byte[] input = bytes("{\"index\":" + i + "}");
            known.add(input);
            refs.add(publish(f, input));
        }
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            List<RawJson> warmed = new ArrayList<>();
            for (int i = 0; i < 64; i++) {
                RawJson value = bound.loadFullMaterial(refs.get(i));
                assertArrayEquals(known.get(i), value.bytes());
                warmed.add(value);
            }
            RawJson hotEarly = bound.loadFullMaterial(refs.get(0));
            assertSame(warmed.get(0), hotEarly);
            RawJson late = bound.loadFullMaterial(refs.get(64));
            assertArrayEquals(known.get(64), late.bytes());
            assertSame(late, bound.loadFullMaterial(refs.get(64)));
            assertSame(hotEarly, bound.loadFullMaterial(refs.get(0)));
            byte[] detached = late.bytes();
            detached[0] ^= 1;
            assertArrayEquals(known.get(64), late.bytes());
            return null;
        }));
        unchanged(f, snapshot, entries);
    }

    @Test void profileSeparationAndScopeExit() throws IOException {
        Fixture f = fixture("profile");
        byte[] known = bytes("{\"value\":" + "9".repeat(5000) + "}");
        ExactRef ref = publishFull(f, known);
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        ActionPorts.OutcomeArchive[] escaped = new ActionPorts.OutcomeArchive[1];
        RawJson first = f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            escaped[0] = bound;
            RawJson full = bound.loadFullMaterial(ref);
            assertArrayEquals(known, full.bytes());
            assertSame(full, bound.loadFullMaterial(ref));
            return full;
        }));
        assertNotNull(escaped[0]);
        assertThrows(IllegalArgumentException.class, () -> escaped[0].loadFullMaterial(ref));
        RawJson next = f.writer.locked(session -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
            RawJson full = bound.loadFullMaterial(ref);
            assertNotSame(first, full);
            assertArrayEquals(known, full.bytes());
            assertSame(full, bound.loadFullMaterial(ref));
            return full;
        }));
        assertNotSame(first, next);
        f.writer.locked(session -> {
            IOException poison = assertThrows(IOException.class,
                    () -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                        RawJson full = bound.loadFullMaterial(ref);
                        assertArrayEquals(known, full.bytes());
                        assertSame(full, bound.loadFullMaterial(ref));
                        assertThrows(IllegalArgumentException.class, () -> bound.loadMaterial(ref));
                        return "caught protocol failure cannot escape successfully";
                    }));
            assertNotNull(poison.getCause());
            return null;
        });
        unchanged(f, snapshot, entries);
    }

    @Test void warmMemoMetadataValidationPoison() throws IOException {
        Fixture f = fixture("poison");
        byte[] known = bytes("{\"cached\":true}");
        ExactRef ref = publish(f, known);
        byte[] snapshot = Files.readAllBytes(f.layout.snapshot());
        var entries = inventory(f.root.resolve("artifacts"));
        Path path = payload(ref);
        f.writer.locked(session -> {
            IOException poison = assertThrows(IOException.class,
                    () -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                        RawJson warm = bound.loadFullMaterial(ref);
                        assertArrayEquals(known, warm.bytes());
                        assertSame(warm, bound.loadFullMaterial(ref));
                        FileTime before = Files.getLastModifiedTime(path);
                        Files.setLastModifiedTime(path, FileTime.fromMillis(before.toMillis() + 2000));
                        assertNotEquals(before, Files.getLastModifiedTime(path));
                        UncheckedIOException failure = assertThrows(UncheckedIOException.class,
                                () -> bound.loadFullMaterial(ref));
                        assertNotNull(failure.getCause());
                        return "caught current-metadata failure cannot escape successfully";
                    }));
            assertNotNull(poison.getCause());
            return null;
        });
        unchanged(f, snapshot, entries);
    }
}
