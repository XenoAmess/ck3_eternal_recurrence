package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Actual transport state machine -> physical archive -> concrete authority on one borrowed writer. */
final class NativeFrontendAuthorityTest {
    private static final String MACHINE = "frontend-authority-fixture";
    private static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    @TempDir Path temporary;
    private static byte[] packet(String json) throws IOException { return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8)); }
    private static byte[] hello() throws IOException {
        return packet("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":123,\"connection_generation\":18446744073709551615,"
                + "\"bridge_version\":\"frontend-fixture-v1\",\"expected_ck3_version\":\"1.20.0.4\",\"expected_ck3_sha256\":\"" + SHA
                + "\",\"game_adapter_id\":\"ck3-1.20.0.4-msvc-x64\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,"
                + "\"capabilities\":[\"game.command.query-frontend-gui-route-v1\"]}");
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets = new ArrayDeque<>(); int writes; boolean failVerify; boolean rejectRoute;
        Replay() throws IOException { packets.addLast(hello()); }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public void verify() throws IOException { if (failVerify) throw new IOException("original held process changed"); }
        @Override public byte[] readPacket(Instant deadline) throws IOException {
            if (packets.isEmpty()) throw new IOException("no more original replay frames"); return packets.removeFirst();
        }
        @Override public void writePacket(byte[] request, Instant deadline) throws IOException {
            writes++;
            var row = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(request, 4, request.length)));
            assertEquals("query-frontend-gui-route-v1", NativeWire.text(row.get("step")));
            assertEquals(BigInteger.ZERO, row.get("expected_revision").bigIntegerValue());
            assertEquals(5, row.size());
            String requestId = NativeWire.text(row.get("request_id"));
            packets.addLast(packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":" + writes + "}"));
            packets.addLast(packet("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + requestId
                    + "\",\"ok\":" + !rejectRoute + ",\"result\":{\"step\":\"query-frontend-gui-route-v1\",\"accepted\":true,\"status\":\"main_menu\"}}"));
        }
        @Override public void close() { }
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
    private static final class Fixture implements AutoCloseable {
        final Replay replay; final NativeGameTransport transport; final ContinuityWriter writer;
        final NativeOutcomeArchive archive; final FrontendObservationSequence sequence; final NativeFrontendAuthority authority;
        final StorageWriteGuardTestSupport storage;
        int snapshotLookups;
        Fixture(Path root) throws IOException {
            Files.createDirectory(root); byte[] initial = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.java"), "exact frontend fixture source", StandardOpenOption.CREATE_NEW);
            ExactRef ref = LedgerFilesFixtureAccess.read(root.resolve("source.java"), 100).pin().reference();
            var layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFilesFixtureAccess.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 4 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(ref), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request request) { throw new IllegalStateException("no ledger commit in frontend read test"); }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { throw new IllegalStateException("no ledger reduction in frontend read test"); }
            }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
            assertSame(storage, artifacts.storageGuard()); assertSame(storage, writer.storageGuard());
            archive = new NativeOutcomeArchive(artifacts, writer); replay = new Replay();
            var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
            var config = new NativePipeEndpoint.Config("\\\\.\\pipe\\frontend-test", MACHINE, game, "frontend-test-session", "frontend-fixture-v1", SHA, "ck3-1.20.0.4-msvc-x64");
            transport = new NativeGameTransport(replay, config, 16, 32);
            var bindings = RootExecutableBindings.freeze(List.of(), RootReadContractCatalog.staticOnly(List.of()), List.of(), 4);
            sequence = new FrontendObservationSequence(transport, archive, new G2Source(MACHINE, Instant.now().toString(), "1.20.0.4", ref),
                    bindings, List.of(), () -> { snapshotLookups++; return Optional.empty(); }, (borrowed, held, source, route, diagnostics, deadline) -> {
                        // Explicit software fixture source boundary; production Root supplies the actual package verifier.
                        writer.requireSession(borrowed); var pin = borrowed.capturePin(ref, 100); borrowed.verifyPin(pin);
                        var decoded = NativeWire.decode(archive.readArtifact(borrowed, route, 65536));
                        assertTrue(((NativeWire.CommandResult) decoded).nativeOk());
                        return new SourceQualification(ref, same -> { writer.requireSession(same); if (same != borrowed) throw new IOException("source guard session changed"); same.verifyPin(pin); });
                    }, Clock.systemUTC(), Duration.ofSeconds(5), Duration.ofSeconds(10), 16);
            authority = new NativeFrontendAuthority(sequence);
        }
        @Override public void close() throws IOException {
            try (storage) { transport.close(); }
        }
    }
    @Test void originalMenuPacketsRoundTripAndOnlyTheConcreteLiveScopeRefreshesTheOrigin() throws IOException {
        try (Fixture f = new Fixture(temporary.resolve("menu"))) {
            f.writer.locked(session -> {
                var first = f.sequence.observeMenu(session, Instant.now().plusSeconds(10));
                assertInstanceOf(FrontendFrame.Menu.class, first.identity().frame());
                assertEquals(BigInteger.ZERO, first.identity().frame().expectedRevision());
                assertEquals(new BigInteger("18446744073709551615"), first.identity().connectionGeneration());
                assertTrue(first.executableOperations().isEmpty()); assertEquals(1, first.supportingEvidence().size());
                assertArrayEquals(first.originalRoute().originalPacket(), f.archive.readArtifact(session, first.identity().nativeEvidence(), 65536));
                return f.authority.current(session, first.identity(), Instant.now().plusSeconds(10), actual -> {
                    assertTrue(actual.identity().frame().querySequence().compareTo(first.identity().frame().querySequence()) > 0);
                    assertNotEquals(actual.identity().nativeEvidence(), first.identity().nativeEvidence());
                    assertThrows(IllegalArgumentException.class, () -> f.sequence.observeMenu(session, Instant.now().plusSeconds(10)));
                    return null;
                });
            });
            assertEquals(2, f.replay.writes); assertEquals(0, f.snapshotLookups);
            assertTrue(f.storage.validations() > 0); assertTrue(f.storage.successfulBatches() > 0);
            assertFalse(f.storage.hasUnknownWrite());
        }
    }
    @Test void fabricatedAndEscapedOriginsCannotIssueNativeReadsAndProcessDriftRejects() throws IOException {
        try (Fixture f = new Fixture(temporary.resolve("custody"))) {
            final org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session[] escaped = new org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session[1];
            var origin = f.writer.locked(session -> { escaped[0] = session; return f.sequence.observeMenu(session, Instant.now().plusSeconds(10)).identity(); });
            assertThrows(IOException.class, () -> f.authority.current(escaped[0], origin, Instant.now().plusSeconds(10), actual -> null));
            f.writer.locked(session -> {
                var invented = new FrontendIdentity(origin.machineId(), origin.game(), origin.frontendSessionId(), origin.connectionGeneration(), origin.bridgePid(),
                        new FrontendFrame.Menu(BigInteger.valueOf(999)), origin.nativeEvidence(), origin.capabilityEvidence());
                assertThrows(IllegalArgumentException.class, () -> f.authority.current(session, invented, Instant.now().plusSeconds(10), actual -> null));
                f.replay.failVerify = true;
                assertThrows(IOException.class, () -> f.authority.current(session, origin, Instant.now().plusSeconds(10), actual -> null)); return null;
            });
            assertEquals(1, f.replay.writes);
        }
    }
    @Test void falseRouteAckIsRetainedButNeverMintsAFrontendIdentity() throws IOException {
        try (Fixture f = new Fixture(temporary.resolve("rejected"))) {
            f.replay.rejectRoute = true;
            f.writer.locked(session -> {
                assertThrows(IOException.class, () -> f.sequence.observeMenu(session, Instant.now().plusSeconds(10)));
                assertEquals(0, session.head().state().sequence()); return null;
            });
            assertEquals(1, f.replay.writes);
            try (var files = Files.list(f.archive.artifactStore().identity().root())) { assertTrue(files.findAny().isPresent()); }
        }
    }
    @Test void menuSequenceLooksUpTheCurrentContextOnlyWhenARealSnapshotNeedsAnAdoptedProducer() throws IOException {
        try (Fixture f = new Fixture(temporary.resolve("dynamic-context"))) {
            f.writer.locked(session -> {
                var menu = f.sequence.observeMenu(session, Instant.now().plusSeconds(10));
                assertEquals(0, f.snapshotLookups);
                f.replay.packets.addLast(packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native:1\",\"revision\":1,\"state\":{\"paused\":true,\"map_ready\":false,\"date_raw\":1000,\"played_character\":null,\"episode_run_id\":null}}"));
                IOException unavailable = assertThrows(IOException.class, () -> f.sequence.observeSnapshot(session, Instant.now().plusSeconds(10)));
                assertTrue(unavailable.getMessage().contains("not yet adopted")); assertEquals(1, f.snapshotLookups);
                var nextMenu = f.sequence.observeMenu(session, Instant.now().plusSeconds(10));
                assertEquals(menu.identity().frame().querySequence().add(BigInteger.ONE), nextMenu.identity().frame().querySequence());
                assertEquals(1, f.snapshotLookups); return null;
            });
            assertEquals(3, f.replay.writes);
        }
    }
    @Test void sourceMutationInsideTheLiveCallbackInvalidatesTheQualification() throws IOException {
        try (Fixture f = new Fixture(temporary.resolve("source-drift"))) {
            f.writer.locked(session -> {
                var first = f.sequence.observeMenu(session, Instant.now().plusSeconds(10));
                assertThrows(IOException.class, () -> f.authority.current(session, first.identity(), Instant.now().plusSeconds(10), actual -> {
                    Files.writeString(f.archive.artifactStore().identity().root().getParent().resolve("source.java"), "changed source");
                    return null;
                }));
                assertEquals(0, session.head().state().sequence()); return null;
            });
            assertEquals(2, f.replay.writes);
        }
    }
    @Test void closingTheFrontendConsumerReleasesItsOriginalStorageAfterActualArchiveWrites() throws IOException {
        Fixture f = new Fixture(temporary.resolve("closed-storage"));
        try (f) {
            f.writer.locked(session -> f.sequence.observeMenu(session, Instant.now().plusSeconds(10)));
            assertTrue(f.storage.successfulBatches() > 0);
            assertFalse(f.storage.hasUnknownWrite());
        }
        assertThrows(IOException.class, () -> StorageWriteGuardTestSupport.forOriginalLock(f.storage.originalLock()));
        int writes = f.replay.writes;
        assertThrows(IOException.class, () -> f.writer.locked(session -> f.archive.preserveArtifact(session,
                "closed frontend consumer".getBytes(StandardCharsets.UTF_8), 65536)));
        assertEquals(writes, f.replay.writes);
        assertFalse(f.storage.hasUnknownWrite());
    }
    @Test void failedPhysicalWriteRetainsTheSameFiniteGuardAndBlocksFurtherArchiveWrites() throws IOException {
        Path root = temporary.resolve("storage-unknown");
        try (Fixture f = new Fixture(root)) {
            f.writer.locked(session -> {
                Path target = root.toAbsolutePath().normalize().resolve("partial-original.bin");
                var plan = new StorageWriteGuard.WritePlan(f.storage.originalLock(),
                        List.of(new StorageWriteGuard.FileCreate(target, 1)));
                assertThrows(IOException.class, () -> f.storage.write(plan, () -> {
                    Files.write(target, new byte[] {7}, StandardOpenOption.CREATE_NEW);
                    throw new IOException("actual software fixture failure after the original create");
                }));
                assertTrue(Files.exists(target)); assertTrue(f.storage.hasUnknownWrite());
                assertSame(f.storage, StorageWriteGuardTestSupport.forOriginalLock(f.storage.originalLock()));
                assertSame(f.storage, StorageWriteGuardTestSupport.create(root, f.storage.originalLock(), 67_108_864));
                int writes = f.replay.writes;
                assertThrows(IOException.class, () -> f.archive.preserveArtifact(session,
                        "unadmitted followup".getBytes(StandardCharsets.UTF_8), 65536));
                assertEquals(writes, f.replay.writes); assertTrue(f.storage.hasUnknownWrite());
                assertEquals(0, session.head().state().sequence()); return null;
            });
        }
    }
}
