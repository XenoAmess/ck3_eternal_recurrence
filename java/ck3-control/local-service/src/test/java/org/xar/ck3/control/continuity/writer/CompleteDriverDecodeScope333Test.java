package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** New bounded software DATA tests. Real owned Windows writer/archive scope, no Game or speed claim. */
final class CompleteDriverDecodeScope333Test {
    private static final String MACHINE = "driver-complete333";
    private static final Instant NOW = Instant.parse("2026-11-02T00:00:00Z");
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(8, 4L * 1024 * 1024, 32);
    @TempDir Path temp;
    private final List<StorageWriteGuardTestSupport> storageScopes = new ArrayList<>();

    @AfterEach void closeStorage() throws IOException {
        IOException failure = null;
        for (var storage : storageScopes) try { storage.close(); }
        catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final DriverFrameEvidenceLoader loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        final Layout layout;
        final ExactRef source;
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
            Files.writeString(root.resolve("source.txt"), "finite software source320", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("no fixture ledger commits"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer, loader);
        }
    }
    private static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }


    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"software333","bridge_pid":123,"episode_character_id":73,"episode_run_id":"episode333",
         "last_checkpoint":null,"command_history":[{"index":1,"opaque":{"n":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"goal333"},"rollback_war_failures":null}
        """;
    private static byte[] driver(int revision) { return bytes(DRIVER.replace("goal333", "goal333-" + revision)); }
    private static final String NATIVE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
         "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{},"original_metric":1.00}
        """;

    @Test void legacyAndUnscopedPathsRemainStrictWithoutNewPortMethods() throws IOException {
        var legacy = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        assertNotSame(legacy.decodeCompleteDriverBytes(driver(0)), legacy.decodeCompleteDriverBytes(driver(0)));
        assertThrows(IllegalStateException.class, () -> legacy.bindDriverDecodeOwner(new Object(), ignored -> { }));
        var f = new Fixture("strict");
        assertNotSame(f.loader.decodeCompleteDriverBytes(driver(0)), f.loader.decodeCompleteDriverBytes(driver(0)));
        var calls = new AtomicInteger();
        var port = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    calls.incrementAndGet(); throw new AssertionError("unexpected new archive callback " + method.getName());
                });
        f.writer.locked(session -> {
            assertThrows(IllegalStateException.class, () -> legacy.inCompleteDriverDecodeScope(f.archive, session, port, a -> null));
            return null;
        });
        assertEquals(0, calls.get());
    }

    @Test void exactBytesPrivateKeysAndImmutableValuesReuseInOrdinarySameSessionScope() throws IOException {
        var f = new Fixture("bytes");
        var escaped = new AtomicReference<DriverStateSnapshot.Complete>();
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            byte[] input = driver(0);
            var first = f.loader.decodeCompleteDriverBytes(input); escaped.set(first);
            input[0] = '[';
            assertSame(first, f.loader.decodeCompleteDriverBytes(driver(0)));
            assertSame(first, bound.inSession(session, nested -> f.loader.decodeCompleteDriverBytes(driver(0))));
            assertNotSame(first, f.loader.decodeCompleteDriverBytes(bytes(" \n" + new String(driver(0), StandardCharsets.UTF_8))));
            assertNotSame(first, f.loader.decodeCompleteDriverBytes(driver(1)));
            assertThrows(UnsupportedOperationException.class, () -> first.commandHistory().clear());
            byte[] returned = first.commandHistory().get(0).originalRow().json(); returned[0] = '[';
            assertTrue(new String(first.commandHistory().get(0).originalRow().json(), StandardCharsets.UTF_8).contains("1.00E+2"));
            assertSame(first, f.loader.decodeCompleteDriverBytes(driver(0)));
            return null;
        }));
        assertNotSame(escaped.get(), f.loader.decodeCompleteDriverBytes(driver(0)));
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            assertNotSame(escaped.get(), f.loader.decodeCompleteDriverBytes(driver(0))); return null;
        }));
    }

    @Test void lruFailureAndExceptionalExitCannotRetainPriorValues() throws IOException {
        var f = new Fixture("lru");
        var escaped = new AtomicReference<DriverStateSnapshot.Complete>();
        f.writer.locked(session -> {
            assertThrows(IllegalArgumentException.class, () -> f.archive.inSession(session, bound -> {
                var first = f.loader.decodeCompleteDriverBytes(driver(0));
                var second = f.loader.decodeCompleteDriverBytes(driver(1));
                f.loader.decodeCompleteDriverBytes(driver(2)); f.loader.decodeCompleteDriverBytes(driver(3));
                assertSame(first, f.loader.decodeCompleteDriverBytes(driver(0)));
                f.loader.decodeCompleteDriverBytes(driver(4));
                assertSame(first, f.loader.decodeCompleteDriverBytes(driver(0)));
                assertNotSame(second, f.loader.decodeCompleteDriverBytes(driver(1)));
                assertThrows(IllegalArgumentException.class, () -> f.loader.decodeCompleteDriverBytes(bytes("{}")));
                var after = f.loader.decodeCompleteDriverBytes(driver(0)); assertNotSame(first, after); escaped.set(after);
                throw new IllegalArgumentException("owned finite scope failure333");
            }));
            f.archive.inSession(session, bound -> {
                assertNotSame(escaped.get(), f.loader.decodeCompleteDriverBytes(driver(0))); return null;
            });
            return null;
        });
    }

    @Test void actualOwnerThreadAndPoisonChecksPrecedeMemoHits() throws IOException {
        var f = new Fixture("owner");
        assertThrows(IllegalStateException.class, () -> f.loader.bindDriverDecodeOwner(new Object(), ignored -> { }));
        var prior = new AtomicReference<ContinuityStorePort.Session>();
        f.writer.locked(session -> { prior.set(session); return null; });
        f.writer.locked(session -> {
            assertThrows(IOException.class, () -> f.archive.inHistoricalReadScope(session, LIMITS, bound -> {
                f.loader.decodeCompleteDriverBytes(driver(0));
                assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,
                        () -> f.loader.inCompleteDriverDecodeScope(f.archive, prior.get(), bound, a -> null));
                assertThrows(UncheckedIOException.class, () -> f.loader.decodeCompleteDriverBytes(driver(0)));
                return null;
            }));
            f.archive.inSession(session, bound -> {
                var first = f.loader.decodeCompleteDriverBytes(driver(0));
                var threadFailure = new AtomicReference<Throwable>();
                Thread other = new Thread(() -> {
                    try { f.loader.inCompleteDriverDecodeScope(f.archive, session, bound, a -> null); }
                    catch (Throwable problem) { threadFailure.set(problem); }
                });
                other.start();
                try { other.join(5000); } catch (InterruptedException problem) { Thread.currentThread().interrupt(); throw new AssertionError(problem); }
                assertFalse(other.isAlive());
                assertInstanceOf(org.xar.ck3.control.contracts.ContractViolationException.class, threadFailure.get());
                assertSame(first, f.loader.decodeCompleteDriverBytes(driver(0))); return null;
            });
            return null;
        });
    }

    private record Originals(RawJson driver, RawJson manifest, ExactRef manifestRef, byte[] packet,
            ExactRef nativeRef, NativeEffectEvidence.FrameBasis basis) { }
    private Originals originals(Fixture f) {
        byte[] raw = DriverStateSnapshot.decodeComplete(driver(0)).encode();
        var material = RawJson.fullMaterial(raw); ExactRef driverRef = f.archive.preserveMaterial(material);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var known = DriverFactsRepository.imported(driverRef, raw, 3, 7, game, new OpportunityJson.Obj(Map.of()));
        byte[] packetJson = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot333\",\"revision\":9,\"state\":" + NATIVE.strip() + "}");
        byte[] packet = ByteBuffer.allocate(packetJson.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(packetJson.length).put(packetJson).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game, BigInteger.valueOf(5), "session333"),
                "snapshot333", BigInteger.valueOf(9), new RawJson(bytes(NATIVE.strip())), packet, NOW);
        ExactRef nativeRef = f.archive.preserveNativeFrame(actual);
        var source = new G2Source(MACHINE, NOW.toString(), "source333", f.source);
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.TWO, 1, source, new OpportunityJson.Obj(Map.of()), driverRef);
        ExactRef manifestRef = f.archive.preserveMaterial(manifest);
        return new Originals(material, manifest, manifestRef, packet, nativeRef, new NativeEffectEvidence.FrameBasis(nativeRef, manifestRef));
    }

    @Test void actualFullLoaderReopensEveryOriginalAfterPureDriverMemoHit() throws IOException {
        var f = new Fixture("fresh"); var original = originals(f);
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            var materialLoads = new AtomicInteger(); var nativeLoads = new AtomicInteger();
            var counted = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        if (method.getName().equals("loadFullMaterial")) materialLoads.incrementAndGet();
                        if (method.getName().equals("loadNativeFrame")) nativeLoads.incrementAndGet();
                        try { return method.invoke(bound, args); }
                        catch (java.lang.reflect.InvocationTargetException problem) { throw problem.getCause(); }
                    });
            var first = f.loader.loadFull(original.basis(), counted);
            var second = f.loader.loadFull(original.basis(), counted);
            assertNotSame(first, second); assertNotSame(first.facts(), second.facts());
            assertSame(first.facts().driver(), second.facts().driver());
            assertEquals(first.facts(), second.facts()); assertEquals(first.semantic(), second.semantic());
            assertEquals(first.fullBindingSha256(), second.fullBindingSha256()); assertEquals(first.originalEvidence(), second.originalEvidence());
            assertArrayEquals(first.actual().originalPacket(), second.actual().originalPacket()); assertEquals(4, materialLoads.get()); assertEquals(2, nativeLoads.get());
            byte[] tampered = original.driver().bytes(); tampered[0] = '[';
            try { Files.write(Path.of(DriverObservationEvidenceReader.currentDriverReference(original.manifestRef(), original.manifest()).path()), tampered); }
            catch (IOException problem) { throw new UncheckedIOException(problem); }
            assertThrows(UncheckedIOException.class, () -> f.loader.loadFull(original.basis(), counted));
            return null;
        }));
    }

    @Test void newReaderProjectionStillChecksManifestDriverNativeAndSemanticBindings() throws IOException {
        var f = new Fixture("reader"); var original = originals(f);
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            var first = f.loader.loadFull(original.basis(), bound);
            var actualAssembler = new DriverObservationAssembler();
            var second = DriverObservationEvidenceReader.projectOriginalsWithScopedDriverDecode(original.manifestRef(), original.manifest(),
                    original.driver(), original.packet(), original.nativeRef(), actualAssembler, f.loader);
            assertEquals(first.facts(), second.facts()); assertEquals(first.semantic(), second.semantic());
            assertEquals(first.fullBindingSha256(), second.fullBindingSha256()); assertEquals(first.originalEvidence(), second.originalEvidence());
            assertArrayEquals(first.actual().originalPacket(), second.actual().originalPacket()); assertSame(first.facts().driver(), second.facts().driver());
            var wrong = new ExactRef(original.manifestRef().path(), original.manifestRef().bytes() + 1, original.manifestRef().sha256());
            assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.projectOriginalsWithScopedDriverDecode(
                    wrong, original.manifest(), original.driver(), original.packet(), original.nativeRef(), actualAssembler, f.loader));
            assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.projectOriginalsWithScopedDriverDecode(
                    original.manifestRef(), original.manifest(), RawJson.fullMaterial(driver(7)), original.packet(), original.nativeRef(), actualAssembler, f.loader));
            byte[] packet = original.packet().clone(); packet[packet.length - 2] ^= 1;
            assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.projectOriginalsWithScopedDriverDecode(
                    original.manifestRef(), original.manifest(), original.driver(), packet, original.nativeRef(), actualAssembler, f.loader));
            var row = DriverJson.object(original.manifest().bytes(), DriverJson.MAX_NATIVE_BYTES);
            var source = OpportunityJson.object(row.get("source"), "source").with("machine_id", new OpportunityJson.Text("other333"));
            var changed = RawJson.fullMaterial(DriverJson.encode(row.with("source", source)));
            var changedRef = new ExactRef(original.manifestRef().path(), changed.bytes().length, DriverJson.sha256(changed.bytes()));
            assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.projectOriginalsWithScopedDriverDecode(
                    changedRef, changed, original.driver(), original.packet(), original.nativeRef(), actualAssembler, f.loader));
            assertSame(first.facts().driver(), f.loader.loadFull(original.basis(), bound).facts().driver());
            return null;
        }));
    }
}
