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
final class NativeOutcomeArchiveContentEquality276Test {
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
    @Test void protocolAndFullCacheHitsStillReopenTheActualMaterial() throws IOException {
        Fixture f = fixture("protocol-full-cache");
        byte[] expected = "{\"value\":123}".getBytes(StandardCharsets.UTF_8);
        RawJson original = new RawJson(expected);
        ExactRef ref = f.archive.preserveMaterial(original);
        byte[] oldLedger = Files.readAllBytes(f.layout.snapshot());
        f.writer.locked(session -> f.archive.inSession(session, bound -> io(() -> {
            RawJson protocol = bound.loadMaterial(ref);
            RawJson full = bound.loadFullMaterial(ref);
            assertNotSame(protocol, full);
            assertSame(protocol, bound.loadMaterial(ref));
            assertSame(full, bound.loadFullMaterial(ref));
            assertArrayEquals(expected, protocol.bytes());
            assertArrayEquals(expected, full.bytes());
            byte[] detached = protocol.bytes(); detached[0] = 0;
            byte[] fullDetached = full.bytes(); fullDetached[0] = 0;
            assertArrayEquals(expected, bound.loadMaterial(ref).bytes());
            assertArrayEquals(expected, bound.loadFullMaterial(ref).bytes());
            Path payload = Path.of(ref.path());
            assertTrue(payload.startsWith(f.root));
            Files.writeString(payload, "{\"value\":456}", StandardOpenOption.TRUNCATE_EXISTING);
            assertThrows(UncheckedIOException.class, () -> bound.loadMaterial(ref));
            assertThrows(UncheckedIOException.class, () -> bound.loadFullMaterial(ref));
            assertEquals("{\"value\":456}", Files.readString(payload));
            return null;
        })));
        assertArrayEquals(oldLedger, Files.readAllBytes(f.layout.snapshot()));
    }
}
