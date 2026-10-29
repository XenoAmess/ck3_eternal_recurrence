package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real held transport/physical archive/writer/issuer/Root guard/coordinator; no Root or Driver substitute. */
final class NativeFrontendReadScopeTest {
    private static final String MACHINE = "frontend-read-scope-fixture";
    private static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String CAPABILITY = "game.command.query-frontend-gui-route-v1";
    private static final OperationKey QUERY = new OperationKey("query-frontend-gui-route-v1");
    @TempDir Path temporary;
    private static byte[] packet(String json) throws IOException { return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8)); }
    private static final class TestClock extends Clock {
        private Duration offset = Duration.ZERO;
        void advance(Duration by) { offset = offset.plus(by); }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException("UTC fixture clock"); return this; }
        @Override public Instant instant() { return Instant.now().plus(offset); }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets = new ArrayDeque<>();
        int bootstrapRoutes, pureReads, writes; boolean failVerify;
        Replay() throws IOException {
            packets.add(packet("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":123,\"connection_generation\":18446744073709551615,"
                    + "\"bridge_version\":\"frontend-fixture-v1\",\"expected_ck3_version\":\"1.20.0.4\",\"expected_ck3_sha256\":\"" + SHA
                    + "\",\"game_adapter_id\":\"ck3-1.20.0.4-msvc-x64\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,"
                    + "\"capabilities\":[\"" + CAPABILITY + "\"]}"));
        }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public void verify() throws IOException { if (failVerify) throw new IOException("held endpoint identity changed"); }
        @Override public byte[] readPacket(Instant deadline) throws IOException {
            if (packets.isEmpty()) throw new IOException("fixture has no further original packets"); return packets.removeFirst();
        }
        @Override public void writePacket(byte[] request, Instant deadline) throws IOException {
            var row = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(request, 4, request.length)));
            assertEquals(QUERY.value(), NativeWire.text(row.get("step")));
            assertEquals(BigInteger.ZERO, row.get("expected_revision").bigIntegerValue()); assertEquals(5, row.size());
            String id = NativeWire.text(row.get("request_id"));
            if (id.startsWith("frontend-route-")) bootstrapRoutes++; else pureReads++;
            writes++;
            packets.add(packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":" + writes + "}"));
            packets.add(packet("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id
                    + "\",\"ok\":true,\"result\":{\"step\":\"query-frontend-gui-route-v1\",\"accepted\":true,\"status\":\"main_menu\"}}"));
        }
        @Override public void close() { }
    }
    private static ObjectNode state() {
        var row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        var game = row.putObject("game_binding"); game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z");
        row.putNull("latest_binding"); row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558);
        row.put("NEXT", 11559); return row;
    }
    private static final class Fixture implements AutoCloseable {
        final Path sourcePath; final TestClock clock = new TestClock(); final Replay replay;
        final ContinuityWriter writer; final NativeOutcomeArchive archive; final NativeGameTransport transport;
        final G2Source source; final RootReadContractCatalog catalog; final ReadContract<FrontendRulesData.ObservedRoute> query;
        final FrontendObservationSequence sequence; final NativeFrontendAuthority authority;
        final StorageWriteGuardTestSupport storage; int snapshotLookups;
        Fixture(Path root) throws IOException {
            Files.createDirectory(root); byte[] initial = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
            sourcePath = root.resolve("source.java"); Files.writeString(sourcePath, "exact controlled frontend read source", StandardOpenOption.CREATE_NEW);
            ExactRef ref = LedgerFilesFixtureAccess.read(sourcePath, 100).pin().reference();
            var layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFilesFixtureAccess.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 4 << 20), storage);
            writer = new ContinuityWriter(layout, List.of(ref), new TransitionAuthority() {
                // This fixture exercises no canonical transition. These methods do not claim to intercept scope writes.
                @Override public String revalidate(ContinuityState predecessor, Request request) { throw new IllegalStateException("no test business reducer installed"); }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { throw new IllegalStateException("no test business reducer installed"); }
            }, clock, new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(artifacts, writer); replay = new Replay();
            var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
            var config = new NativePipeEndpoint.Config("\\\\.\\pipe\\frontend-test", MACHINE, game, "frontend-test-session", "frontend-fixture-v1", SHA, "ck3-1.20.0.4-msvc-x64");
            transport = new NativeGameTransport(replay, config, 16, 32);
            source = new G2Source(MACHINE, Instant.now().toString(), "1.20.0.4", ref);
            query = new ReadContract<>("frontend-route-read-scope-fixture-v1", QUERY, Optional.of(CAPABILITY), "frontend-route-query",
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.FRONTEND_SESSION, ref,
                    (request, id) -> new NativeRequest(QUERY.value(), CAPABILITY, new RawJson(new byte[] {'{', '}'})),
                    receipt -> {
                        var identity = receipt.request().origin().requireFrontend();
                        var nativeSource = new FrontendRulesData.Source(new FrontendRulesData.Binding(identity.bridgePid(), identity.connectionGeneration()),
                                FrontendRulesData.Build.require("1.20.0.4", SHA));
                        return FrontendRulesCodec.route(receipt.original().originalResultToken().orElseThrow(), nativeSource, identity.frame().querySequence());
                    });
            catalog = RootReadContractCatalog.staticOnly(List.of(query));
            var installed = RootExecutableBindings.freeze(List.of(), catalog, List.of(), 4);
            var admission = new FrontendRouteAdmission(QUERY, Set.of(FrontendRulesData.Route.MAIN_MENU), FrontendRouteAdmission.FrameMode.MENU, ref);
            sequence = new FrontendObservationSequence(transport, archive, source, installed, List.of(admission),
                    () -> { snapshotLookups++; return Optional.empty(); },
                    (borrowed, held, exactSource, route, received, deadline) -> {
                        // Controlled software qualification over real archived packets and the physical source pin.
                        writer.requireSession(borrowed); var pin = borrowed.capturePin(ref, 100); borrowed.verifyPin(pin);
                        assertEquals(source, exactSource); assertEquals(held, received.session().orElseThrow());
                        assertTrue(((NativeWire.CommandResult) NativeWire.decode(archive.readArtifact(borrowed, route, 65536))).nativeOk());
                        var proof = StrictJson.object(); proof.put("schema", "controlled.frontend-test-source/v1");
                        proof.set("source", ref.toJson()); proof.set("route", route.toJson()); proof.put("machine_id", MACHINE);
                        ExactRef originalProof = archive.preserveArtifact(borrowed, ContinuityJson.canonical(proof), 65536);
                        return new SourceQualification(originalProof, same -> {
                            writer.requireSession(same); if (same != borrowed) throw new IOException("source qualification escaped its actual writer"); same.verifyPin(pin);
                        });
                    }, clock, Duration.ofSeconds(5), Duration.ofSeconds(10), 32);
            authority = new NativeFrontendAuthority(sequence);
        }
        Instant deadline() { return clock.instant().plusSeconds(30); }
        RootFrontendReadGuard guard(FrontendAuthority actualAuthority) {
            return new RootFrontendReadGuard(actualAuthority, () -> {
                try { return writer.borrowedSession(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }, archive, source, clock, "frontend-read-test-authority", new ArchiveOriginalEvidencePort(archive), catalog);
        }
        PlanningReadCoordinator coordinator(PlanningReadCoordinator.ReadGuardPort actualGuard) {
            return new PlanningReadCoordinator(catalog, new ContinuityActionJournal(writer, archive), actualGuard, transport, archive, clock);
        }
        PlanningReadRequest request(FrontendAuthority.LeaseSnapshot lease, Instant deadline) {
            return new PlanningReadRequest(new CommandOrigin.Frontend(lease.identity()), source, lease.identity().frontendSessionId(), QUERY,
                    new OpportunityJson.Obj(Map.of()), deadline);
        }
        @Override public void close() throws IOException { try(storage) { transport.close(); } }
    }

    @Test void realPureQueryUsesBothRootGuardsAndOriginalArchiveWithinOneIssuedScope() throws IOException {
        try (var f = new Fixture(temporary.resolve("real-read"))) {
            f.writer.locked(same -> f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), lease -> {
                var result = f.coordinator(f.guard(f.authority)).read(same, f.query, f.request(lease, f.deadline()));
                assertInstanceOf(PlanningReadResult.Known.class, result);
                if (!(result instanceof PlanningReadResult.Known<FrontendRulesData.ObservedRoute> known)) throw new AssertionError(result);
                assertEquals(FrontendRulesData.Route.MAIN_MENU, known.value().route());
                var receipt = known.receipt(); assertEquals(receipt.before(), receipt.after());
                assertEquals(lease.identity(), receipt.before().binding().origin().requireFrontend());
                assertEquals(lease.identity().nativeEvidence(), receipt.after().binding().nativeEvidence());
                assertEquals(receipt, f.archive.withSession(same).loadRead(known.originalReceipt()));
                assertEquals(receipt.before(), CommandOriginCodec.planningGuard(CommandOriginCodec.planningGuard(receipt.before())));
                var originals = new ArchiveOriginalEvidencePort(f.archive);
                RootFrontendGuardEvidence.verify(receipt.before().binding(), f.archive.withSession(same), same, originals);
                RootFrontendGuardEvidence.verify(receipt.after().binding(), f.archive.withSession(same), same, originals);
                assertThrows(IllegalStateException.class, receipt.before()::paused);
                assertEquals(0, same.head().state().sequence()); assertEquals(0, f.snapshotLookups);
                return null;
            }));
            assertEquals(1, f.replay.bootstrapRoutes); assertEquals(1, f.replay.pureReads); assertEquals(2, f.replay.writes);
        }
    }

    @Test void nestedReadsBorrowTheExactLeaseAndActionFacadeGateRejectsBeforeIntent() throws IOException {
        try (var f = new Fixture(temporary.resolve("nested"))) {
            f.writer.locked(same -> {
                FrontendIdentity origin = f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), lease -> {
                    assertSame(lease, f.authority.current(same, lease.identity(), f.deadline(), actual -> actual));
                    assertSame(lease, f.authority.currentSourceBoundRead(same, lease.identity(), f.deadline(), actual -> actual));
                    assertSame(lease, f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), actual -> actual));
                    assertEquals(lease.identity(), CommandOriginCodec.frontend(CommandOriginCodec.frontend(lease.identity())));
                    var malformed = CommandOriginCodec.frontend(lease.identity());
                    ((ObjectNode) malformed.get("frame")).put("query_sequence", true);
                    assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontend(malformed));
                    var extraAlias = CommandOriginCodec.frontend(lease.identity()); extraAlias.put("actor", 123);
                    assertThrows(IllegalArgumentException.class, () -> CommandOriginCodec.frontend(extraAlias));
                    assertThrows(IllegalArgumentException.class, () -> f.authority.requireOutsideSourceBoundFrontendRead());
                    assertThrows(IllegalArgumentException.class, () -> f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.SNAPSHOT, f.deadline(), actual -> null));
                    assertThrows(IllegalArgumentException.class, () -> f.sequence.observeMenu(same, f.deadline()));
                    assertEquals(1, f.replay.bootstrapRoutes); assertEquals(0, f.snapshotLookups); return lease.identity();
                });
                f.authority.requireOutsideSourceBoundFrontendRead();
                assertThrows(IOException.class, () -> f.authority.currentSourceBoundRead(same, origin, f.deadline(), actual -> null));
                assertEquals(1, f.replay.bootstrapRoutes);
                // current outside the scope keeps its previous refresh semantics.
                f.authority.current(same, origin, f.deadline(), actual -> { assertNotEquals(origin.nativeEvidence(), actual.identity().nativeEvidence()); return null; });
                assertEquals(2, f.replay.bootstrapRoutes); assertEquals(0, same.head().state().sequence()); return null;
            });
        }
    }

    @Test void originalIssuedIdentityAndSameWriterCannotBeReplacedByFabricatedDataOrEscapedSession() throws IOException {
        try (var f = new Fixture(temporary.resolve("identity")); var foreign = new Fixture(temporary.resolve("foreign"))) {
            var foreignSession = foreign.writer.locked(other -> other);
            ContinuityStorePort.Session[] escaped = new ContinuityStorePort.Session[1];
            FrontendIdentity origin = f.writer.locked(same -> {
                escaped[0] = same;
                return f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), lease -> {
                    var old = lease.identity(); var invented = new FrontendIdentity(old.machineId(), old.game(), old.frontendSessionId(), old.connectionGeneration(), old.bridgePid(),
                            new FrontendFrame.Menu(BigInteger.valueOf(999)), old.nativeEvidence(), old.capabilityEvidence());
                    assertThrows(IllegalArgumentException.class, () -> f.authority.current(same, invented, f.deadline(), actual -> null));
                    assertThrows(IOException.class, () -> f.authority.currentSourceBoundRead(foreignSession, old, f.deadline(), actual -> null));
                    assertEquals(1, f.replay.bootstrapRoutes); return old;
                });
            });
            assertThrows(IOException.class, () -> f.authority.currentSourceBoundRead(escaped[0], origin, f.deadline(), actual -> null));
            assertThrows(IOException.class, () -> f.authority.current(escaped[0], origin, f.deadline(), actual -> null));
            assertEquals(1, f.replay.bootstrapRoutes);
        }
    }

    @Test void postWorkSourceEndpointAndLeaseExpiryAreRevalidatedWithoutAnotherObservation() throws IOException {
        try (var f = new Fixture(temporary.resolve("source-drift"))) {
            f.writer.locked(same -> { assertThrows(IOException.class, () -> f.authority.withSourceBoundFrontendRead(same,
                    FrontendRouteAdmission.FrameMode.MENU, f.deadline(), actual -> { Files.writeString(f.sourcePath, "changed controlled source"); return null; })); return null; });
            assertEquals(1, f.replay.bootstrapRoutes);
        }
        try (var f = new Fixture(temporary.resolve("endpoint-drift"))) {
            f.writer.locked(same -> { assertThrows(IOException.class, () -> f.authority.withSourceBoundFrontendRead(same,
                    FrontendRouteAdmission.FrameMode.MENU, f.deadline(), actual -> { f.replay.failVerify = true; return null; })); return null; });
            assertEquals(1, f.replay.bootstrapRoutes);
        }
        try (var f = new Fixture(temporary.resolve("expired-lease"))) {
            f.writer.locked(same -> { assertThrows(IllegalArgumentException.class, () -> f.authority.withSourceBoundFrontendRead(same,
                    FrontendRouteAdmission.FrameMode.MENU, f.deadline(), actual -> { f.clock.advance(Duration.ofSeconds(6)); return null; })); return null; });
            assertEquals(1, f.replay.bootstrapRoutes);
        }
    }

    @Test void snapshotRequiresTheActualAdoptedDriverAndMenuNeverConsultsOne() throws IOException {
        try (var f = new Fixture(temporary.resolve("no-driver"))) {
            f.writer.locked(same -> {
                f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), actual -> null);
                assertEquals(0, f.snapshotLookups);
                f.replay.packets.add(packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native:1\",\"revision\":1,\"state\":{\"paused\":true,\"map_ready\":false,\"date_raw\":1000,\"played_character\":null,\"episode_run_id\":null}}"));
                var failure = assertThrows(IOException.class, () -> f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.SNAPSHOT, f.deadline(), actual -> null));
                assertTrue(failure.getMessage().contains("not yet adopted")); assertEquals(1, f.snapshotLookups);
                f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), actual -> null);
                assertEquals(1, f.snapshotLookups); assertEquals(0, same.head().state().sequence()); return null;
            });
            assertEquals(3, f.replay.bootstrapRoutes); assertEquals(0, f.replay.pureReads);
        }
    }

    @Test void legacyAuthorityAndDefaultCoordinatorHookCannotGrantEqualEvidenceContinuation() throws IOException {
        try (var f = new Fixture(temporary.resolve("deny-default"))) {
            f.writer.locked(same -> f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), lease -> {
                FrontendAuthority legacy = new FrontendAuthority() {
                    @Override public <T> T current(ContinuityStorePort.Session retained, FrontendIdentity expected, Instant deadline, CheckedWork<T> work) throws IOException {
                        return f.authority.current(retained, expected, deadline, work);
                    }
                };
                assertThrows(IOException.class, () -> legacy.currentSourceBoundRead(same, lease.identity(), f.deadline(), actual -> null));
                var request = f.request(lease, f.deadline()); var actualGuard = f.guard(legacy);
                var denied = f.coordinator(actualGuard).read(same, f.query, request);
                assertInstanceOf(PlanningReadResult.Unavailable.class, denied);
                if (!(denied instanceof PlanningReadResult.Unavailable<FrontendRulesData.ObservedRoute> unavailable)) throw new AssertionError(denied);
                assertTrue(unavailable.original().isPresent()); assertInstanceOf(NativeActionPort.AckReceived.class, unavailable.original().orElseThrow());
                PlanningReadCoordinator.ReadGuardPort missingContinuation = actualGuard::verify;
                assertThrows(IllegalStateException.class, () -> missingContinuation.verifyFrontendReadContinuation(same.head(), request, f.query,
                        actualGuard.verify(same.head(), request, f.query), actualGuard.verify(same.head(), request, f.query)));
                assertEquals(0, same.head().state().sequence()); return null;
            }));
            assertEquals(1, f.replay.bootstrapRoutes); assertEquals(1, f.replay.pureReads);
        }
    }

    @Test void physicalGuardOriginalProducerRequiresTheActualActiveSourceBoundScope() throws IOException {
        try (var f = new Fixture(temporary.resolve("physical-guard-originals"))) {
            var operation = new OperationKey("prepare-frontend-coat-of-arms-framebuffer-v1");
            f.writer.locked(same -> {
                FrontendIdentity issued = f.authority.withSourceBoundFrontendRead(same, FrontendRouteAdmission.FrameMode.MENU, f.deadline(), lease -> {
                    var archive = f.archive.withSession(same); var originals = new ArchiveOriginalEvidencePort(f.archive);
                    var guard = RootFrontendGuardEvidence.sourceBound(f.authority, lease.identity(), f.source, lease.identity().frontendSessionId(),
                            operation, f.deadline(), same.head(), "physical-guard-originals-test", f.clock, same, archive, originals);
                    assertEquals(operation, guard.operation()); assertEquals(lease.identity(), guard.origin().requireFrontend());
                    RootFrontendGuardEvidence.verify(guard, archive, same, originals);
                    FrontendAuthority legacy = new FrontendAuthority() {
                        @Override public <T> T current(ContinuityStorePort.Session session, FrontendIdentity expected, Instant deadline, CheckedWork<T> work) {
                            throw new AssertionError("source-bound guard cannot refresh or fall back to legacy current");
                        }
                    };
                    assertThrows(IOException.class, () -> RootFrontendGuardEvidence.sourceBound(legacy, lease.identity(), f.source,
                            lease.identity().frontendSessionId(), operation, f.deadline(), same.head(), "physical-guard-originals-test", f.clock, same, archive, originals));
                    assertEquals(1, f.replay.bootstrapRoutes); assertEquals(0, f.replay.pureReads);
                    assertEquals(0, same.head().state().sequence()); return lease.identity();
                });
                assertThrows(IOException.class, () -> RootFrontendGuardEvidence.sourceBound(f.authority, issued, f.source,
                        issued.frontendSessionId(), operation, f.deadline(), same.head(), "physical-guard-originals-test", f.clock,
                        same, f.archive.withSession(same), new ArchiveOriginalEvidencePort(f.archive)));
                assertEquals(1, f.replay.writes); return null;
            });
        }
    }
}
