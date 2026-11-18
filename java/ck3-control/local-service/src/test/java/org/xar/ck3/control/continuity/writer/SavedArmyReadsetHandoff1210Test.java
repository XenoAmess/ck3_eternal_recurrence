package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths;

/** Real owned Windows reader -> peer HANDLE -> independent saved DATA custody.
 * Numeric JSON is controlled test DATA, never a Native receipt, saved issuer or current Game. */
final class SavedArmyReadsetHandoff1210Test {
    private static final Instant NOW = Instant.parse("2026-11-18T00:00:00Z"), EXPIRY = NOW.plusSeconds(60);
    private static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(64, 8L << 20, 132);
    private static final ArmyQueryHistoryReference.ReplayReadLimits ARMY_LIMITS = new ArmyQueryHistoryReference.ReplayReadLimits(4, 1L << 20);
    private static final TransitionAuthority NEVER = new TransitionAuthority() {
        @Override public String revalidate(ContinuityState before, Request request) { throw new AssertionError("no preview"); }
        @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new AssertionError("no commit"); }
    };
    @TempDir Path temporary;
    @BeforeEach void actualWindows() { assertTrue(Platform.isWindows(), "actual Windows custody is required"); }

    private static ObjectNode state() {
        var row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", "army-handoff1210-owned");
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0); row.putNull("latest_binding");
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static final class Fixture implements AutoCloseable {
        final Path root; final Layout layout; final ExactRef source; final StorageWriteGuardTestSupport storage;
        final ImmutableArtifactStore.Config config; final ContinuityWriter writer;
        Fixture(Path root) throws IOException {
            this.root = root; Files.createDirectory(root); byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "reviewed owned source", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), "army-handoff1210-owned");
            storage = StorageWriteGuardTestSupport.create(layout);
            config = new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8L << 20);
            var store = new ImmutableArtifactStore(config, storage);
            writer = new ContinuityWriter(layout, List.of(source), NEVER, CLOCK,
                    new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
        }
        @Override public void close() throws IOException { storage.close(); }
    }
    private static final class Reader implements AutoCloseable {
        final StorageWriteGuard noWrites = StorageWriteGuard.noWrites();
        final ContinuityWriter writer; final NativeOutcomeArchive archive;
        Reader(Fixture source) throws IOException {
            var store = ImmutableArtifactStore.readOnlyExisting(source.config, noWrites);
            writer = ContinuityWriter.readOnlyExisting(source.layout, List.of(source.source), NEVER, CLOCK,
                    new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), noWrites);
            archive = new NativeOutcomeArchive(store, writer);
        }
        @Override public void close() throws IOException { noWrites.close(); }
    }
    private record Sidecar(Path folder, Path file, RawJson summary, byte[] numeric, long artifactBytes) { }
    private static Sidecar sidecar(Path folder) throws IOException {
        Files.createDirectory(folder);
        var body = StrictJson.object(); body.put("step", ArmyStrengths.STEP); body.put("accepted", true);
        body.put("query_sequence", 1); body.put("queried_snapshot_id", "controlled-sidecar");
        body.put("queried_revision", 1); body.put("queried_native_revision", 1); body.putArray("army_strengths");
        byte[] numeric = StrictJson.canonical(body), artifact = Arrays.copyOf(numeric, numeric.length + 1); artifact[numeric.length] = 10;
        Path file = folder.resolve("army-query-" + "1".repeat(32) + ".json"); Files.write(file, artifact, StandardOpenOption.CREATE_NEW);
        var summary = body.deepCopy(); summary.remove("army_strengths"); summary.put("history_summary_schema", ArmyQueryHistoryStore.SUMMARY_SCHEMA);
        summary.put("full_result_preserved", true); summary.put("army_count", 0);
        summary.putObject("raw_result_reference").put("path", file.toString()).put("bytes", artifact.length)
                .put("sha256", LedgerFiles.sha(artifact)).put("kind", ArmyQueryHistoryStore.REFERENCE_KIND).put("wire_bytes_preserved", false);
        return new Sidecar(folder, file, new RawJson(StrictJson.canonical(summary)), numeric, artifact.length);
    }
    private static void held(Path path, boolean expected) throws IOException {
        for (int access : new int[] { 0x40000000, 0x10000 }) {
            HANDLE handle = Kernel32.INSTANCE.CreateFile(path.toString(), access, 7, null, 3, 0x80, null);
            int error = Kernel32.INSTANCE.GetLastError();
            if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
                if (!expected) throw new IOException("owned access qualification failed: " + error);
                assertEquals(32, error); continue;
            }
            try { assertFalse(expected, "held leaf permitted current write/delete access"); }
            finally { if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("owned qualification close failed"); }
        }
    }
    private static void verify(Fixture caller, Reader old, NativeOutcomeArchive.SavedPreReadReadSet<?> saved) throws IOException {
        caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame -> {
            saved.requireCurrent(old.archive, sourceSame); return null;
        }));
    }
    @Test void authenticatedArmyLeafStaysHeldAfterProducerScopeAndOldSessionBothEnd() throws Exception {
        try (var source = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(source)) {
            var input = sidecar(source.root.resolve("army-evidence")); var captures = new AtomicInteger();
            var original = new AtomicReference<ArmyQueryHistoryReference.AuthenticatedReplayOriginal>();
            try (var saved = caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame ->
                    old.archive.sealSavedPreReadHistory(sourceSame, LIMITS, CLOCK, EXPIRY, bound ->
                        ArmyQueryHistoryReference.inReplayReadScope(ARMY_LIMITS, CLOCK, EXPIRY, authenticated -> {
                            captures.incrementAndGet(); original.set(authenticated);
                            old.archive.retainSavedPreReadArmyOriginal(sourceSame, authenticated);
                        }, () -> {
                            var first = ArmyQueryHistoryReference.read(input.summary(), input.folder(), input.artifactBytes());
                            var second = ArmyQueryHistoryReference.read(input.summary(), input.folder(), input.artifactBytes());
                            assertSame(first, second); return second.completeDriver();
                        }))))) {
                assertEquals(1, captures.get()); assertArrayEquals(input.numeric(), saved.value().bytes());
                assertEquals(input.artifactBytes(), original.get().pin().reference().bytes());
                original.get().requireCurrent(); held(input.file(), true); verify(caller, old, saved);
            }
            held(input.file(), false);
        }
    }
    @Test void caughtWrongSourceSessionHandoffCannotReturnASealedCandidate() throws Exception {
        try (var source = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(source)) {
            var input = sidecar(source.root.resolve("army-evidence"));
            assertThrows(IOException.class, () -> caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame ->
                    old.archive.sealSavedPreReadHistory(sourceSame, LIMITS, CLOCK, EXPIRY, bound -> {
                        assertThrows(IOException.class, () -> ArmyQueryHistoryReference.inReplayReadScope(ARMY_LIMITS, CLOCK, EXPIRY,
                                authenticated -> old.archive.retainSavedPreReadArmyOriginal(newSame, authenticated),
                                () -> ArmyQueryHistoryReference.read(input.summary(), input.folder(), input.artifactBytes())));
                        return "caught handoff failure must not escape";
                    }))));
            held(input.file(), false); held(source.layout.snapshot(), false);
        }
    }
    @Test void failedAuthenticatedDomainGuardInvalidatesTheActualConsumerReadset() throws Exception {
        try (var source = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(source)) {
            var input = sidecar(source.root.resolve("army-evidence"));
            var authenticated = new AtomicReference<ArmyQueryHistoryReference.AuthenticatedReplayOriginal>();
            try (var saved = caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame ->
                    old.archive.sealSavedPreReadHistory(sourceSame, LIMITS, CLOCK, EXPIRY, bound ->
                        ArmyQueryHistoryReference.inReplayReadScope(ARMY_LIMITS, CLOCK, EXPIRY, original -> {
                            authenticated.set(original); old.archive.retainSavedPreReadArmyOriginal(sourceSame, original);
                        }, () -> ArmyQueryHistoryReference.read(input.summary(), input.folder(), input.artifactBytes())))))) {
                CompletableFuture.runAsync(() -> assertThrows(IOException.class, authenticated.get()::requireCurrent)).get(5, TimeUnit.SECONDS);
                assertThrows(IOException.class, () -> verify(caller, old, saved));
                held(input.file(), true);
            }
            held(input.file(), false);
        }
    }
    @Test void peerHandleIsQuotedBeforeAcquiringAnAdditionalConsumerHandle() throws Exception {
        try (var source = new Fixture(temporary.resolve("source")); var caller = new Fixture(temporary.resolve("caller")); var old = new Reader(source)) {
            var input = sidecar(source.root.resolve("army-evidence"));
            var failure = assertThrows(ImmutableArtifactStore.SavedReadsetUnavailable.class, () ->
                    caller.writer.locked(newSame -> old.writer.readOnlyFrom(newSame, sourceSame -> {
                        var base = new HashSet<Path>();
                        for (var pin : sourceSame.head().documents()) base.add(Path.of(pin.reference().path()).toAbsolutePath().normalize());
                        base.add(Path.of(sourceSame.persistedHead().path()).toAbsolutePath().normalize());
                        for (var pin : sourceSame.captureSources()) base.add(Path.of(pin.reference().path()).toAbsolutePath().normalize());
                        var limit = new ActionPorts.HistoricalReadLimits(64, 8L << 20, base.size() + 3);
                        return old.archive.sealSavedPreReadHistory(sourceSame, limit, CLOCK, EXPIRY, bound ->
                            ArmyQueryHistoryReference.inReplayReadScope(ARMY_LIMITS, CLOCK, EXPIRY,
                                original -> old.archive.retainSavedPreReadArmyOriginal(sourceSame, original),
                                () -> ArmyQueryHistoryReference.read(input.summary(), input.folder(), input.artifactBytes())));
                    })));
            assertEquals(ImmutableArtifactStore.SavedReadsetFailure.HANDLE_BOUND, failure.reason());
            held(input.file(), false); held(source.layout.snapshot(), false);
        }
    }
}
