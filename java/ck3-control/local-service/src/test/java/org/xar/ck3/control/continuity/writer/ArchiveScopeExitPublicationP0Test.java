package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts.Layout;
import org.xar.ck3.control.continuity.writer.WriterContracts.Request;
import org.xar.ck3.control.continuity.writer.WriterContracts.TransitionAuthority;

/** Real public Archive/Session DATA only; no Root issuer, Game or performance claim. */
final class ArchiveScopeExitPublicationP0Test {
    private static final String MACHINE = "archive-scope-exit-publication";
    private static final int ARTIFACT_LIMIT = 1024;
    private static final ActionPorts.HistoricalReadLimits LIMITS =
            new ActionPorts.HistoricalReadLimits(4, 1_048_576, 16);
    @TempDir Path temporary;

    @Test void normalAndCheckedScopeExitAllowPublicationInTheSameSession() throws IOException {
        verifyExit(temporary.resolve("normal"), false);
        verifyExit(temporary.resolve("checked"), true);
    }

    private static void verifyExit(Path root, boolean checked) throws IOException {
        byte[] seed = "{\"seed\":\"data\"}".getBytes(StandardCharsets.UTF_8);
        byte[] next = "{\"new\":\"artifact\"}".getBytes(StandardCharsets.UTF_8);
        IOException sentinel = new IOException("checked historical callback exit");
        try (Fixture fixture = new Fixture(root)) {
            fixture.writer.locked(session -> {
                String head = session.head().digest();
                byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
                ExactRef seedRef = fixture.archive.preserveArtifact(session, seed, ARTIFACT_LIMIT);
                ActionPorts.CheckedArchiveRead<String> work = bound -> {
                    NativeOutcomeArchive actual = (NativeOutcomeArchive) bound;
                    assertArrayEquals(seed, actual.readArtifact(session, seedRef, ARTIFACT_LIMIT));
                    assertArrayEquals(seed, actual.readArtifact(session, seedRef, ARTIFACT_LIMIT));
                    if (checked) throw sentinel;
                    return "historical callback complete";
                };
                if (checked) {
                    IOException received = assertThrows(IOException.class,
                            () -> fixture.archive.inHistoricalReadScope(session, LIMITS, work));
                    assertSame(sentinel, received, "the callback's original IOException remains primary");
                } else {
                    assertEquals("historical callback complete",
                            fixture.archive.inHistoricalReadScope(session, LIMITS, work));
                }

                // Historical finish has returned; the original writer callback is still active.
                fixture.writer.requireSession(session);
                assertSame(session, fixture.writer.borrowedSession());
                ExactRef nextRef = fixture.archive.preserveArtifact(session, next, ARTIFACT_LIMIT);
                assertArrayEquals(next, fixture.archive.readArtifact(session, nextRef, ARTIFACT_LIMIT));
                assertArrayEquals(next, fixture.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                    NativeOutcomeArchive actual = (NativeOutcomeArchive) bound;
                    assertArrayEquals(seed, actual.readArtifact(session, seedRef, ARTIFACT_LIMIT));
                    return actual.readArtifact(session, nextRef, ARTIFACT_LIMIT);
                }));
                assertLedgerUnchanged(fixture, session, head, snapshot);
                return null;
            });
        }
    }

    @Test void caughtHistoricalPublicationDeniesItsResultButExitRestoresWrites() throws IOException {
        byte[] seed = "{\"seed\":\"data\"}".getBytes(StandardCharsets.UTF_8);
        byte[] next = "{\"new\":\"after-refused-write\"}".getBytes(StandardCharsets.UTF_8);
        try (Fixture fixture = new Fixture(temporary.resolve("caught-publication"))) {
            fixture.writer.locked(session -> {
                String head = session.head().digest();
                byte[] snapshot = Files.readAllBytes(fixture.layout.snapshot());
                ExactRef seedRef = fixture.archive.preserveArtifact(session, seed, ARTIFACT_LIMIT);
                List<String> before = artifactLeaves(fixture.artifactsRoot);
                AtomicReference<IOException> attemptedPublication = new AtomicReference<>();
                AtomicBoolean callbackReachedReturn = new AtomicBoolean();

                IOException refused = assertThrows(IOException.class,
                        () -> fixture.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                            NativeOutcomeArchive actual = (NativeOutcomeArchive) bound;
                            assertArrayEquals(seed, actual.readArtifact(session, seedRef, ARTIFACT_LIMIT));
                            attemptedPublication.set(assertThrows(IOException.class,
                                    () -> actual.preserveArtifact(session, next, ARTIFACT_LIMIT)));
                            callbackReachedReturn.set(true);
                            return "caught publication cannot authorize a result";
                        }));
                assertTrue(callbackReachedReturn.get(), "the callback caught the refusal and reached return");
                assertNotNull(attemptedPublication.get());
                assertTrue(carries(refused, attemptedPublication.get()), "scope failure retains the caught refusal");
                assertEquals(before, artifactLeaves(fixture.artifactsRoot), "the rejected write created no artifact leaf");
                assertLedgerUnchanged(fixture, session, head, snapshot);

                // Do not leave writer.locked or acquire another Session to hide a leaked read scope.
                fixture.writer.requireSession(session);
                assertSame(session, fixture.writer.borrowedSession());
                ExactRef nextRef = fixture.archive.preserveArtifact(session, next, ARTIFACT_LIMIT);
                assertArrayEquals(next, fixture.archive.readArtifact(session, nextRef, ARTIFACT_LIMIT));
                assertArrayEquals(next, fixture.archive.inHistoricalReadScope(session, LIMITS, bound ->
                        ((NativeOutcomeArchive) bound).readArtifact(session, nextRef, ARTIFACT_LIMIT)));
                assertLedgerUnchanged(fixture, session, head, snapshot);
                return null;
            });
        }
    }

    private static List<String> artifactLeaves(Path root) throws IOException {
        try (var leaves = Files.list(root)) {
            return leaves.map(path -> path.getFileName().toString()).sorted().toList();
        }
    }

    private static void assertLedgerUnchanged(Fixture fixture, ContinuityStorePort.Session session,
            String head, byte[] snapshot) throws IOException {
        assertEquals(head, session.head().digest());
        assertArrayEquals(snapshot, Files.readAllBytes(fixture.layout.snapshot()));
        try (var events = Files.list(fixture.layout.events())) {
            assertEquals(0L, events.count(), "artifact operations did not write a canonical transition");
        }
    }

    private static boolean carries(Throwable failure, Throwable expected) {
        for (int depth = 0; failure != null && depth < 32; depth++, failure = failure.getCause()) {
            if (failure == expected) return true;
            for (Throwable suppressed : failure.getSuppressed()) if (suppressed == expected) return true;
        }
        return false;
    }

    private static final class Fixture implements AutoCloseable {
        final Layout layout;
        final Path artifactsRoot;
        final StorageWriteGuardTestSupport storage;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;

        Fixture(Path root) throws IOException {
            Files.createDirectory(root);
            byte[] original = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), original, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), original, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            artifactsRoot = Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "owned public Archive scope exit fixture", StandardOpenOption.CREATE_NEW);
            var source = LedgerFiles.read(root.resolve("source.txt"), ARTIFACT_LIMIT).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65_536).pin().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            try {
                store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(
                        artifactsRoot, layout.lock(), 8 * 1024 * 1024), storage);
                writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                    @Override public String revalidate(ContinuityState before, Request request) {
                        throw new AssertionError("fixture must not preview a canonical transition");
                    }
                    @Override public ContinuityState reduce(ContinuityState before, Request request) {
                        throw new AssertionError("fixture must not commit a canonical transition");
                    }
                }, Clock.fixed(Instant.parse("2026-11-03T00:00:00Z"), ZoneOffset.UTC),
                        new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
                archive = new NativeOutcomeArchive(store, writer);
            } catch (IOException | RuntimeException | Error failure) {
                try { storage.close(); } catch (IOException closing) { if (closing != failure) failure.addSuppressed(closing); }
                throw failure;
            }
        }

        @Override public void close() throws IOException { storage.close(); }
    }

    private static ObjectNode state() {
        ObjectNode row = StrictJson.object();
        row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running");
        row.put("target_days", 10958); row.put("target_years", 30); row.put("calendar_year_days", 365.25);
        row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z");
        row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558);
        row.put("NEXT", 11559);
        return row;
    }
}
