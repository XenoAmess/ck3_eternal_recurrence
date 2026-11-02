package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown.Reduction;

/** New public Persistent replay wiring witnesses; owned software files grant no Root/Game authority. */
final class PersistentReplayScopedDecode363Test {
    private static final String MACHINE = "persistent-replay363";
    private static final Instant NOW = Instant.parse("2026-11-02T00:00:00Z");
    @TempDir Path temp;
    private final List<StorageWriteGuardTestSupport> storageScopes = new ArrayList<>();

    @AfterEach void closeStorage() throws IOException {
        IOException failure = null;
        for (var scope : storageScopes) try { scope.close(); }
        catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        final DriverFrameEvidenceLoader loader;
        final ExactRef source;
        Fixture(String name, boolean nominal) throws IOException {
            Path root = Files.createDirectory(temp.resolve(name));
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "finite software source363", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            var layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),
                    layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) {
                    return ContinuityJson.digest(request.detailsObject());
                }
                @Override public ContinuityState reduce(ContinuityState before, Request request) {
                    throw new IllegalStateException("no fixture ledger commits363");
                }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            loader = nominal ? new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true) : null;
            archive = nominal ? new NativeOutcomeArchive(store, writer, loader) : new NativeOutcomeArchive(store, writer);
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
        {"format_version":2,"pipe_name":"software363","bridge_pid":123,"episode_character_id":73,"episode_run_id":"episode363",
         "last_checkpoint":null,"command_history":[{"index":1,"opaque":{"n":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"goal363"},"rollback_war_failures":null}
        """;
    private static final String NATIVE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
         "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{},"original_metric":1.00}
        """;
    private record Originals(RawJson driver, ExactRef driverRef, RawJson manifest, ExactRef manifestRef,
            byte[] packet, ExactRef nativeRef, DriverObservationAssembler.Complete frame) { }
    private Originals originals(Fixture f) {
        byte[] raw = DriverStateSnapshot.decodeComplete(bytes(DRIVER)).encode();
        RawJson material = RawJson.fullMaterial(raw); ExactRef driverRef = f.archive.preserveMaterial(material);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var known = DriverFactsRepository.imported(driverRef, raw, 3, 7, game, new Obj(Map.of()));
        byte[] packetJson = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot363\",\"revision\":9,\"state\":" + NATIVE.strip() + "}");
        byte[] packet = ByteBuffer.allocate(packetJson.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(packetJson.length).put(packetJson).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game,
                BigInteger.valueOf(5), "session363"), "snapshot363", BigInteger.valueOf(9), new RawJson(bytes(NATIVE.strip())), packet, NOW);
        ExactRef nativeRef = f.archive.preserveNativeFrame(actual);
        var source = new G2Source(MACHINE, NOW.toString(), "source363", f.source);
        RawJson manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.TWO, 1, source, new Obj(Map.of()), driverRef);
        ExactRef manifestRef = f.archive.preserveMaterial(manifest);
        var frame = assertInstanceOf(DriverObservationAssembler.Complete.class,
                DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, material, packet, nativeRef));
        assertEquals(BigInteger.valueOf(73), frame.identity().frame().identity().player());
        assertEquals(new IntegerValue(new BigInteger("53144328")), frame.semantic().get("date_raw"));
        return new Originals(material, driverRef, manifest, manifestRef, packet, nativeRef, frame);
    }

    private record Chain(Obj auxiliary, ExactRef first, ExactRef last, List<String> reads) { }
    private static Chain chain(Fixture f, Originals original) {
        var frame = original.frame(); var identity = DeclarationOpportunityCooldown.frame(frame);
        var snapshot = DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic()));
        Reduction initial = DeclarationOpportunityCooldown.view(DeclarationOpportunityCooldown.initial(identity), snapshot, identity);
        Obj frameRefs = new Obj(Map.of("manifest", ref(original.manifestRef()), "native", ref(original.nativeRef())));
        Obj input = new Obj(Map.of("configured_path", new Text("D:/pure-data363/" + DeclarationOpportunityCooldown.LEGACY_FILENAME),
                "observed_at", new Text(NOW.toString()), "original", Nil.INSTANCE, "saved", Nil.INSTANCE, "baseline_receipts", new Arr(List.of())));
        ExactRef first = f.archive.preserveMaterial(new RawJson(DriverJson.encode(proof("INITIAL", Nil.INSTANCE, frameRefs, input, initial))));
        Reduction view = DeclarationOpportunityCooldown.view(initial.state(), snapshot, identity);
        ExactRef last = f.archive.preserveMaterial(new RawJson(DriverJson.encode(proof("VIEW", ref(first), frameRefs, Nil.INSTANCE, view))));
        Obj auxiliary = new Obj(Map.of(DriverPersistentPlanningState.COOLDOWN_SOURCE, ref(last),
                DriverPersistentPlanningState.COOLDOWN_STATE, node(DeclarationOpportunityCooldown.encode(view.state())),
                DeclarationOpportunityCooldown.VIEW_KEY, node(DeclarationOpportunityCooldown.encodeView(view.view()))));
        List<String> reads = List.of("M:" + last.sha256(), "M:" + first.sha256(),
                "M:" + original.manifestRef().sha256(), "N:" + original.nativeRef().sha256(), "M:" + original.driverRef().sha256(),
                "M:" + original.manifestRef().sha256(), "N:" + original.nativeRef().sha256(), "M:" + original.driverRef().sha256());
        return new Chain(auxiliary, first, last, reads);
    }

    private static Obj proof(String mode, Value previous, Obj frame, Value input, Reduction reduced) {
        return new Obj(Map.of("schema", new Text("xar.driver-persistent-planning-source/v2"), "mode", new Text(mode),
                "previous", previous, "frame", frame, "input", input, "state", node(DeclarationOpportunityCooldown.encode(reduced.state())),
                "view", node(DeclarationOpportunityCooldown.encodeView(reduced.view())), "processed", new Arr(List.of())));
    }
    private static Obj node(com.fasterxml.jackson.databind.JsonNode value) { return object(parse(StrictJson.canonical(value)), "typed cooldown DATA"); }
    private static Obj ref(ExactRef value) { return DriverObservationEvidenceReader.reference(value); }

    private static ActionPorts.OutcomeArchive observed(ActionPorts.OutcomeArchive target, List<String> reads,
            AtomicInteger decoders, AtomicInteger writes, boolean legacyDefault, boolean badNative) {
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    String name = method.getName();
                    if (name.startsWith("preserve")) { writes.incrementAndGet(); throw new AssertionError("replay cannot publish363"); }
                    if (name.equals("loadMaterial")) reads.add("M:" + ((ExactRef) args[0]).sha256());
                    if (name.equals("loadNativeFrame")) reads.add("N:" + ((ExactRef) args[0]).sha256());
                    if (name.equals("scopedDriverDecoder")) {
                        decoders.incrementAndGet();
                        if (legacyDefault) return InvocationHandler.invokeDefault(proxy, method, args);
                    }
                    try {
                        Object result = method.invoke(target, args);
                        if (badNative && name.equals("loadNativeFrame")) {
                            byte[] changed = ((byte[]) result).clone(); changed[changed.length - 1] ^= 1; return changed;
                        }
                        return result;
                    } catch (InvocationTargetException problem) { throw problem.getCause(); }
                });
    }

    @Test void persistentDefaultAndNominalReplayRetainBothProofsAndEveryOriginalRead() throws IOException {
        for (boolean nominal : List.of(false, true)) {
            var f = new Fixture(nominal ? "nominal" : "legacy", nominal); var original = originals(f); var chain = chain(f, original);
            f.writer.locked(session -> f.archive.inSession(session, bound -> {
                if (nominal) assertSame(f.loader, bound.scopedDriverDecoder()); else assertNull(bound.scopedDriverDecoder());
                var reads = new ArrayList<String>(); var decoders = new AtomicInteger(); var writes = new AtomicInteger();
                var counted = observed(bound, reads, decoders, writes, !nominal, false);
                if (nominal) f.loader.decodeCompleteDriverBytes(original.driver().bytes()); // Explicit DATA-only warm-up.
                DriverPersistentPlanningState.replay(chain.auxiliary(), counted);
                DriverPersistentPlanningState.replay(chain.auxiliary(), counted);
                var expected = new ArrayList<>(chain.reads()); expected.addAll(chain.reads());
                assertEquals(expected, reads); assertTrue(decoders.get() > 0); assertEquals(0, writes.get());
                return null;
            }));
        }
    }

    @Test void warmPersistentReplayStillReadsChangedDriverBeforeLaterNativeValidation() throws IOException {
        var f = new Fixture("late-driver", true); var original = originals(f); var chain = chain(f, original);
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            DriverPersistentPlanningState.replay(chain.auxiliary(), bound);
            var reads = new ArrayList<String>(); var decoders = new AtomicInteger(); var writes = new AtomicInteger();
            var counted = observed(bound, reads, decoders, writes, false, true);
            byte[] originalBytes = original.driver().bytes(); byte[] changed = originalBytes.clone(); changed[0] = '[';
            Path driverPath = Path.of(original.driverRef().path()).toAbsolutePath().normalize();
            assertTrue(driverPath.startsWith(temp.toAbsolutePath().normalize()), "tamper only this owned fixture artifact");
            try {
                try { Files.write(driverPath, changed); }
                catch (IOException problem) { throw new UncheckedIOException(problem); }
                var failure = assertThrows(UncheckedIOException.class,
                        () -> DriverPersistentPlanningState.replay(chain.auxiliary(), counted));
                assertInstanceOf(IOException.class, failure.getCause());
                assertEquals(chain.reads().subList(0, 5), reads, "fresh driver read fails before the later malformed native bytes are revalidated");
                assertEquals(0, writes.get());
            } finally {
                try { Files.write(driverPath, originalBytes); }
                catch (IOException problem) { throw new UncheckedIOException(problem); }
            }
            return null;
        }));
    }

    @Test void namedReplayKeepsOriginalFirstFailureStrictFallbackAndIncompleteBoundary() throws IOException {
        var f = new Fixture("reader-order", true); var original = originals(f);
        f.writer.locked(session -> f.archive.inSession(session, bound -> {
            f.loader.decodeCompleteDriverBytes(original.driver().bytes());
            RawJson invalidDriver = new RawJson(bytes("{}"));
            ExactRef wrongManifest = new ExactRef(original.manifestRef().path(), original.manifestRef().bytes() + 1, original.manifestRef().sha256());
            assertFirstFailure("semantic facts manifest exact bytes/SHA differ", wrongManifest, original.manifest(), invalidDriver, new byte[0], original.nativeRef(), f.loader);
            assertFirstFailure("bounded archived original native frame required", original.manifestRef(), original.manifest(), invalidDriver, new byte[0], original.nativeRef(), f.loader);
            byte[] badPacket = original.packet().clone(); badPacket[badPacket.length - 1] ^= 1;
            assertFirstFailure("archived native framing/manifest differs", original.manifestRef(), original.manifest(), invalidDriver, badPacket, original.nativeRef(), f.loader);
            assertFirstFailure("archived complete Driver exact bytes/SHA differ", original.manifestRef(), original.manifest(), invalidDriver, original.packet(), original.nativeRef(), f.loader);
            ExactRef invalidRef = new ExactRef("pure-invalid363.json", invalidDriver.bytes().length, DriverJson.sha256(invalidDriver.bytes()));
            Obj row = DriverJson.object(original.manifest().bytes(), DriverJson.MAX_NATIVE_BYTES).with("driver_ref", ref(invalidRef));
            RawJson changedManifest = RawJson.fullMaterial(DriverJson.encode(row));
            ExactRef changedRef = new ExactRef("pure-manifest363.json", changedManifest.bytes().length, DriverJson.sha256(changedManifest.bytes()));
            var oldFailure = assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginals(
                    changedRef, changedManifest, invalidDriver, original.packet(), original.nativeRef()));
            var newFailure = assertThrows(IllegalArgumentException.class, () -> DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(
                    changedRef, changedManifest, invalidDriver, original.packet(), original.nativeRef(), bound.scopedDriverDecoder()));
            assertEquals(oldFailure.getClass(), newFailure.getClass()); assertEquals(oldFailure.getMessage(), newFailure.getMessage());
            ExactRef wrongNative = new ExactRef(original.nativeRef().path(), original.nativeRef().bytes(), "0".repeat(64));
            var incomplete = assertInstanceOf(DriverObservationAssembler.Incomplete.class,
                    DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(original.manifestRef(), original.manifest(),
                            original.driver(), original.packet(), wrongNative, f.loader));
            assertEquals(List.of("native_driver_fact_join: original native evidence differs"), incomplete.reasons());
            return null;
        }));
    }

    private static void assertFirstFailure(String message, ExactRef manifestRef, RawJson manifest, RawJson driver,
            byte[] packet, ExactRef nativeRef, DriverFrameEvidenceLoader loader) {
        var legacy = assertThrows(IllegalArgumentException.class,
                () -> DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, driver, packet, nativeRef));
        var named = assertThrows(IllegalArgumentException.class,
                () -> DriverObservationEvidenceReader.replayOriginalsWithScopedDriverDecode(manifestRef, manifest, driver, packet, nativeRef, loader));
        assertEquals(message, legacy.getMessage()); assertEquals(message, named.getMessage()); assertEquals(legacy.getClass(), named.getClass());
    }
}
