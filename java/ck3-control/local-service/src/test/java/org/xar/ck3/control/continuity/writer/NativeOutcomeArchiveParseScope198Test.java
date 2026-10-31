package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Scoped full-material reuse over the real software archive; no Game or live session ledger is touched. */
final class NativeOutcomeArchiveParseScope198Test {
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
    @Test void sameScopeFullMaterialStillRejectsCommittedTamper() throws IOException {
        for (int mutation = 0; mutation < 3; mutation++) {
            Fixture f = fixture("full-tamper-" + mutation);
            RawJson original = raw("{\"retained\":true}");
            ExactRef ref = f.archive.preserveMaterial(original);
            byte[] ledger = Files.readAllBytes(f.layout.snapshot());
            int change = mutation;
            f.writer.locked(session -> f.archive.inSession(session, bound -> io(() -> {
                RawJson first = bound.loadFullMaterial(ref);
                assertSame(first, bound.loadFullMaterial(ref));
                byte[] detached = first.bytes(); detached[0] = 0;
                assertArrayEquals(original.bytes(), bound.loadFullMaterial(ref).bytes());
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
                assertThrows(UncheckedIOException.class, () -> bound.loadFullMaterial(ref));
                assertArrayEquals(changed, Files.readAllBytes(payload));
                assertEquals(count, leafCount(f.root.resolve("artifacts")));
                if (change == 2) assertFalse(Files.exists(commit));
                return null;
            })));
            assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()));
        }
    }
    @Test void fullLaneReuseClosesAcrossScopeAndKeepsOrdinaryBound() throws IOException {
        Fixture f = fixture("full-lane");
        byte[] bytes = ("{\"large\":" + "7".repeat(5000) + ",\"decimal\":-0.0}").getBytes(StandardCharsets.UTF_8);
        RawJson original = RawJson.fullMaterial(bytes);
        ExactRef ref = f.archive.preserveMaterial(original);
        AtomicReference<ActionPorts.OutcomeArchive> escaped = new AtomicReference<>();
        AtomicReference<RawJson> previous = new AtomicReference<>();
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            escaped.set(bound); RawJson loaded = bound.loadFullMaterial(ref); previous.set(loaded);
            assertSame(loaded, bound.loadFullMaterial(ref));
            assertThrows(IllegalArgumentException.class, () -> bound.loadMaterial(ref));
            byte[] detached = loaded.bytes(); detached[0] = 0;
            assertArrayEquals(bytes, bound.loadFullMaterial(ref).bytes());
            return null;
        }));
        assertThrows(IllegalArgumentException.class, () -> escaped.get().loadFullMaterial(ref));
        RawJson next = f.writer.locked(session -> f.archive.inSession(session, bound -> bound.loadFullMaterial(ref)));
        assertNotSame(previous.get(), next); assertArrayEquals(bytes, next.bytes());
    }
    @Test void scopeExceptionAndForeignSessionNeverPromoteUnknown() throws IOException {
        Fixture f = fixture("exception"), foreign = fixture("foreign");
        ExactRef material = f.archive.preserveMaterial(raw("{\"scope\":true}"));
        AtomicReference<RawJson> previous = new AtomicReference<>();
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            RawJson first = bound.loadFullMaterial(material); previous.set(first);
            assertThrows(IllegalStateException.class, () -> f.archive.inSession(session, nested -> {
                assertSame(first, nested.loadFullMaterial(material)); throw new IllegalStateException("nested fault");
            }));
            assertSame(first, bound.loadFullMaterial(material));
            return null;
        }));
        f.writer.locked(session -> {
            assertThrows(AssertionError.class, () -> f.archive.inSession(session, bound -> {
                RawJson current = bound.loadFullMaterial(material); previous.set(current); throw new AssertionError("outer Error");
            })); return null;
        });
        RawJson next = f.writer.locked(session -> f.archive.inSession(session, bound -> bound.loadFullMaterial(material)));
        assertNotSame(previous.get(), next);
        foreign.writer.locked(session -> { assertThrows(UncheckedIOException.class, () -> f.archive.withSession(session)); return null; });
        var unknown = new NativeActionPort.Unknown("uncertain", "never replay", new byte[] {1,2,3}, Optional.of(raw("{\"diagnostic\":true}")));
        ExactRef unknownRef = f.archive.preserve(unknown);
        byte[] ledger = Files.readAllBytes(f.layout.snapshot()); long count = leafCount(f.root.resolve("artifacts"));
        var loaded = f.archive.load(unknownRef);
        assertInstanceOf(NativeActionPort.Unknown.class, loaded); assertEquals(unknown, loaded);
        assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot())); assertEquals(count, leafCount(f.root.resolve("artifacts")));
        assertEquals(0L, f.writer.<Long>locked(session -> session.head().state().sequence()).longValue());
    }
}
