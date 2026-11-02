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
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Owned small-file software archive regressions; no live ledger, Game or private issuer. */
final class NativeArchiveConcreteRead308Test {
    private static final String MACHINE = "archive-test-fixture";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final Set<StorageWriteGuardTestSupport> scopes = new LinkedHashSet<>();
    @AfterEach void closeScopes() throws IOException {
        IOException failure = null;
        for (var scope : scopes) {
            try { scope.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        scopes.clear();
        if (failure != null) throw failure;
    }
    private final class Fixture {
        final Layout layout;
        final ImmutableArtifactStore artifacts;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(String name) throws IOException {
            Path root = Files.createDirectory(temp.resolve(name));
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("reviewed-source.txt"), "archive fixture source", StandardOpenOption.CREATE_NEW);
            ExactRef source = LedgerFiles.read(root.resolve("reviewed-source.txt"), 100).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65_536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout); scopes.add(storage);
            artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { throw new IllegalStateException("fixture must never commit"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(artifacts, writer);
        }
    }
    private static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0); var game = row.putObject("game_binding");
        game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static NativeRequest request(String text) { return new NativeRequest("query-player-status", Optional.of("fixture-capability"), new RawJson(bytes(text))); }
    @FunctionalInterface private interface IoCall<T> { T run() throws IOException; }
    private static <T> T io(IoCall<T> work) {
        try { return work.run(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    @Test void genericOriginalBytesKeepsBoundsLengthHashAndFailure() {
        var calls = new AtomicInteger();
        ExactRef ref = new ExactRef("fixture-only.json", 2, "0".repeat(64));
        var wrongHash = new NativeArchiveDataCodec((original, maximum) -> { calls.incrementAndGet(); return bytes("{}"); });
        assertEquals("retained DATA hash differs from original ref", assertThrows(IOException.class, () -> wrongHash.decodePreparedRequestData(ref)).getMessage());
        assertEquals(1, calls.get());
        var wrongLength = new NativeArchiveDataCodec((original, maximum) -> { calls.incrementAndGet(); return bytes("{ }"); });
        assertEquals("retained DATA length differs from original ref", assertThrows(IOException.class, () -> wrongLength.decodePreparedRequestData(ref)).getMessage());
        assertEquals(2, calls.get());
        ExactRef oversized = new ExactRef("fixture-only.json", StrictJson.EXPLICIT_MAX_BYTES + 1L, "0".repeat(64));
        assertEquals("explicit finite original DATA bound required", assertThrows(IOException.class, () -> wrongHash.decodePreparedRequestData(oversized)).getMessage());
        assertEquals(2, calls.get());
        IOException originalFailure = new IOException("provider original failure");
        var failing = new NativeArchiveDataCodec((original, maximum) -> { calls.incrementAndGet(); throw originalFailure; });
        assertSame(originalFailure, assertThrows(IOException.class, () -> failing.decodePreparedRequestData(ref)));
        assertEquals(3, calls.get());
    }
    @Test void storeBackedRequestRoundTripKeepsDetachedBytes() throws IOException {
        Fixture f = new Fixture("round-trip");
        NativeRequest request = request(" { \"missing_value\":null, \"opaque\":1844674407370955161600001, \"decimal\":1.2500 } ");
        ExactRef ref = f.archive.preserveRequest(request);
        byte[] ledgerBefore = Files.readAllBytes(f.layout.snapshot());
        NativeRequest concrete = f.archive.loadRequest(ref);
        NativeRequest generic = new NativeArchiveDataCodec(f.artifacts::read).decodePreparedRequestData(ref);
        assertEquals(request, concrete); assertEquals(request, generic);
        byte[] detached = concrete.additionalFields().bytes(); detached[0] = 0;
        assertArrayEquals(request.additionalFields().bytes(), f.archive.loadRequest(ref).additionalFields().bytes());
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            NativeRequest reread = bound.loadRequest(ref);
            assertEquals(request.step(), reread.step()); assertEquals(request.requiredCapability(), reread.requiredCapability());
            assertArrayEquals(request.additionalFields().bytes(), reread.additionalFields().bytes());
            return null;
        }));
        assertArrayEquals(ledgerBefore, Files.readAllBytes(f.layout.snapshot()));
        try (var events = Files.list(f.layout.snapshot().getParent().resolve("ROOT-CONTINUITY-WINDOW-EVENTS"))) { assertEquals(0, events.count()); }
    }
    @Test void concreteReadStillRejectsLaterOwnPayloadCorruption() throws IOException {
        Fixture f = new Fixture("corruption");
        NativeRequest request = request("{\"value\":1}");
        ExactRef ref = f.archive.preserveRequest(request); assertEquals(request, f.archive.loadRequest(ref));
        byte[] ledgerBefore = Files.readAllBytes(f.layout.snapshot());
        ObjectNode metadata = (ObjectNode) StrictJson.parse(f.artifacts.read(ref, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES);
        ExactRef fields = ExactRef.fromJson(metadata.get("additional_fields_ref"));
        Path path = Path.of(fields.path()); assertTrue(path.startsWith(temp));
        assertEquals(fields.bytes(), bytes("{\"value\":2}").length);
        Files.write(path, bytes("{\"value\":2}"), StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(UncheckedIOException.class, () -> f.archive.loadRequest(ref));
        assertArrayEquals(bytes("{\"value\":2}"), Files.readAllBytes(path));
        assertArrayEquals(ledgerBefore, Files.readAllBytes(f.layout.snapshot()));
    }
    @Test void escapedBorrowedCodecStillRequiresLiveSession() throws IOException {
        Fixture f = new Fixture("closed-session");
        NativeRequest request = request("{\"value\":1}"); ExactRef ref = f.archive.preserveRequest(request);
        AtomicReference<NativeArchiveDataCodec> escaped = new AtomicReference<>();
        f.writer.locked(session -> {
            var bound = (NativeOutcomeArchive) f.archive.withSession(session);
            NativeArchiveDataCodec codec = NativeArchiveDataCodec.forArchive(bound);
            assertEquals(request, io(() -> codec.decodePreparedRequestData(ref))); escaped.set(codec); return null;
        });
        assertNotNull(escaped.get());
        IllegalArgumentException failure = assertThrows(IllegalArgumentException.class, () -> escaped.get().decodePreparedRequestData(ref));
        assertEquals("live original-lock session on owning thread required", failure.getMessage());
    }
}
