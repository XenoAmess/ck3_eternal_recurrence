package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Core/store/writer and separate JVMs. Fixture seed authority reads a real bounded directory;
 * this proves cold custody, never a live Native/Driver capture, next-intent permission or Game Ready.
 */
public final class RootOrdinaryClaimColdProcessTest {
    @TempDir Path temporary;
    private static final int LIMIT = OrdinaryOnceClaims.MAX_BYTES;
    private record Fixture(RootApplicationConfiguration configuration, ExactRef producer) { }
    private static ExactRef ref(Path path, byte[] raw) { return new ExactRef(path.toString(), raw.length, ActionCodec.sha256(raw)); }
    private static RootOrdinaryClaimRuntime.Sources sources(ExactRef actual) {
        return new RootOrdinaryClaimRuntime.Sources(actual, actual, actual, actual, actual, actual, List.of(actual));
    }
    private static Fixture initialize(Path root) throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(), "actual Core cold regression requires Windows");
        Files.createDirectories(root); String machine = WindowsJobProcess.currentMachineId();
        Path producer = root.resolve("reviewed-producer.txt"), launch = root.resolve("fixture-launch-source.json");
        byte[] sourceRaw = "controlled real ordinary cold-reducer fixture source".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(producer, sourceRaw); byte[] launchRaw = "{\"fixture\":\"no Game launch\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8); Files.write(launch, launchRaw);
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
        byte[] initial = ContinuityJson.canonical(initial(machine)); Files.write(snapshot, initial); Files.write(anchor, initial);
        Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]); Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var configuration = new RootApplicationConfiguration(machine, HostMode.HTTP, Instant.now().plusSeconds(3600), ref(launch, launchRaw),
                new WriterContracts.Layout(snapshot, ref(anchor, initial), machine), List.of(ref(producer, sourceRaw)), Files.createDirectory(root.resolve("archive")), 32L << 20);
        Files.write(root.resolve("configuration.json"), StrictJson.canonical(configuration.toJson()));
        return new Fixture(configuration, ref(producer, sourceRaw));
    }
    private static Fixture readFixture(Path root) throws IOException {
        var configuration = RootApplicationConfiguration.fromJson(StrictJson.parse(Files.readAllBytes(root.resolve("configuration.json")), LIMIT));
        return new Fixture(configuration, configuration.writerSources().getFirst());
    }
    private static ObjectNode initial(String machine) {
        ObjectNode n = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", machine).put("sequence", 0)
                .put("window_id", 1).put("status", "running").put("target_days", 10958).put("target_years", 30).put("calendar_year_days", 365.25)
                .put("start_date_raw", 1000).put("target_date_raw", 1000 + 10958 * 24).put("last_settled_date_raw", 1000)
                .put("last_settled_cycles", 1).put("manual_repair_count", 1).put("automatic_recovery_count", 0).put("binding_lineage_count", 0);
        n.putObject("game_binding").put("pid", 121).put("creation_date", "2026-10-23T01:00:00Z"); n.putNull("latest_binding");
        n.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); n.put("NEXT", 11559); return n;
    }
    private static OrdinaryOnceClaims.Request next(String machine, String id) {
        return next(machine, id, -33_554_431L);
    }
    private static OrdinaryOnceClaims.Request next(String machine, String id, long actor) {
        return new OrdinaryOnceClaims.Request(new OrdinaryOnceClaims.Identity(machine, 121, "134999999999999999", actor,
                "educate_child_interaction", 4_000_000_002L), new OrdinaryOnceClaims.Binding("native:11", "12", "11", "1000", "1", "episode"), id);
    }
    private static OrdinaryClaimDomain.Artifacts artifacts(AtomicReference<RootApplicationAssembly.Core> actual) {
        return new OrdinaryClaimDomain.Artifacts() {
            @Override public ExactRef publish(ContinuityStorePort.Session same, byte[] raw) {
                try { actual.get().writer().requireSession(same); return actual.get().archive().withSession(same).preserveMaterial(new RawJson(raw)); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
            @Override public byte[] read(ExactRef original) {
                try { var core = actual.get(); return core.archive().withSession(core.writer().borrowedSession()).loadMaterial(original).bytes(); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
        };
    }
    private static void produce(Path root, boolean legacy) throws Exception {
        Fixture fixture = initialize(root); Path original = Files.createDirectory(root.resolve("ordinary-interaction-actions"));
        if (legacy) Files.write(original.resolve("original.claim.json"), RootOrdinaryClaimOriginalsTest.legacy("legacy-original", "2147483647"));
        var captured = RootOrdinaryClaimOriginals.capture(original); var retained = new ArrayList<ExactRef>();
        var actual = new AtomicReference<RootApplicationAssembly.Core>(); var originalManifest = new AtomicReference<ExactRef>();
        var domain = new OrdinaryClaimDomain(fixture.configuration().ledger().lock(), artifacts(actual), new RootOrdinaryClaimRuntime.SourceConsumptionAuthority());
        var registration = domain.registration(List.of(fixture.producer()), (manifest, head) -> {
            try {
                assertNotNull(actual.get(), "Core construction must not invoke a live seed producer"); assertEquals(originalManifest.get(), manifest);
                assertEquals(fixture.configuration().machineId(), head.machineId()); captured.requireUnchanged();
                return captured.state(head.machineId(), retained);
            } catch (IOException failure) { throw new UncheckedIOException(failure); }
        });
        var storage = StorageWriteGuardTestSupport.create(fixture.configuration().ledger());
        actual.set(RootApplicationAssembly.open(fixture.configuration(), Clock.systemUTC(), List.of(registration), Optional.empty(), storage));
        var core = actual.get();
        core.writer().locked(same -> {
            for (var row : captured.originals()) retained.add(artifacts(actual).publish(same, row.bytes()));
            originalManifest.set(artifacts(actual).publish(same, StrictJson.canonical(StrictJson.object().put("schema", "controlled-real-directory-census/v1").put("actual_claim_count", retained.size()))));
            domain.importOriginal(same, originalManifest.get(), captured.state(fixture.configuration().machineId(), retained));
            if (!legacy) domain.claim(same, next(fixture.configuration().machineId(), "durable-unknown-original"));
            var state = (DomainBodies.Available) same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
            Files.write(root.resolve("expected-state.json"), state.canonicalBody()); Files.write(root.resolve("expected-body-ref.json"), StrictJson.canonical(state.reference().payload().toJson()));
            return null;
        });
    }
    private static byte[] input(String kind, OrdinaryOnceClaims.Request request, ExactRef claim, ExactRef manifest) {
        ObjectNode n = StrictJson.object().put("schema", OrdinaryClaimDomain.INPUT_SCHEMA).put("kind", kind);
        if (request == null) n.putNull("request"); else n.set("request", OrdinaryOnceClaims.request(request)); n.putNull("permit");
        if (claim == null) n.putNull("claim_ref"); else n.set("claim_ref", claim.toJson());
        if (manifest == null) n.putNull("original_claim_manifest"); else n.set("original_claim_manifest", manifest.toJson());
        return StrictJson.canonical(n);
    }
    private static void consumeCold(Path root) throws Exception { consumeCold(root, false); }
    private static void consumeCold(Path root, boolean updatedCurrentProducer) throws Exception {
        Fixture fixture = readFixture(root); byte[] before = Files.readAllBytes(fixture.configuration().ledger().snapshot());
        ExactRef currentProducer = fixture.producer();
        if (updatedCurrentProducer) {
            Path current = root.resolve("current-reviewed-producer.txt");
            byte[] raw = "updated implementation; retained claim knowledge".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            Files.write(current, raw); currentProducer = ref(current, raw);
            assertNotEquals(fixture.producer(), currentProducer);
        }
        var prepared = new RootOrdinaryClaimRuntime.Prepared(fixture.configuration().ledger().lock(), sources(currentProducer));
        var storage = StorageWriteGuardTestSupport.create(fixture.configuration().ledger());
        var core = RootApplicationAssembly.open(fixture.configuration(), Clock.systemUTC(), prepared.domainRegistrations(), Optional.empty(), storage);
        // Intentionally before bindCore: a historical read must never call the live SeedAuthority or Artifacts callback.
        var preBind = core.writer().read(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
        assertInstanceOf(DomainBodies.Available.class, preBind, preBind.toString());
        prepared.bindCore(core);
        core.writer().locked(same -> {
            var state = prepared.requireRetainedOriginal(same); assertArrayEquals(Files.readAllBytes(root.resolve("expected-state.json")), OrdinaryOnceClaims.encode(state));
            var current = (DomainBodies.Available) same.readDomain(DomainBodies.Slot.ORDINARY_ONCE_CLAIM);
            if (!state.claims().isEmpty()) {
                var request = next(fixture.configuration().machineId(), "cannot-resume-publication-after-cold");
                ExactRef retained = state.claims().getFirst().original();
                var attempt = new DomainBodies.ImportRequest(DomainBodies.Slot.ORDINARY_ONCE_CLAIM, OrdinaryOnceClaims.SCHEMA,
                        current.reference().payload(), input("CLAIM", request, retained, null), List.of(retained), "attempt-cold-new-claim");
                assertThrows(IllegalArgumentException.class, () -> same.previewImport(attempt), "historical read cannot mint the live claim ThreadLocal");
                assertThrows(RootOrdinaryClaimRuntime.PermitUnavailable.class,
                        () -> new RootOrdinaryClaimRuntime.SourceConsumptionAuthority().requireNextIntent(same, state, request));
            } else {
                assertFalse(state.legacyBlockers().isEmpty());
                assertThrows(IllegalArgumentException.class, () -> OrdinaryOnceClaims.prepareClaim(state, next(fixture.configuration().machineId(), "cannot-clear-old-blocker", state.legacyBlockers().getFirst().actorId())));
            }
            assertArrayEquals(current.canonicalBody(), OrdinaryOnceClaims.encode(prepared.requireRetainedOriginal(same))); return null;
        });
        assertArrayEquals(before, Files.readAllBytes(fixture.configuration().ledger().snapshot()), "cold knowledge and rejected retries never write the ledger");
    }
    /** Invoked only by these tests in a genuinely independent Java process. No Python, shell or Game. */
    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("exact mode and temporary fixture root required");
        Path root = Path.of(args[1]).toAbsolutePath().normalize();
        switch (args[0]) { case "produce-legacy" -> produce(root, true); case "produce-claim" -> produce(root, false); case "cold" -> consumeCold(root); case "cold-current-producer" -> consumeCold(root, true); default -> throw new IllegalArgumentException("closed cold test mode"); }
    }
    private int process(String mode, Path root, String logName) throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows());
        Path java = Path.of(System.getProperty("java.home"), "bin", "java.exe"); Path log = temporary.resolve(logName);
        String classpath = System.getProperty("surefire.test.class.path", System.getProperty("java.class.path"));
        Process child = new ProcessBuilder(java.toString(), "-Djna.tmpdir=" + System.getProperty("jna.tmpdir"), "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"), "-cp", classpath, RootOrdinaryClaimColdProcessTest.class.getName(), mode, root.toString())
                .directory(temporary.toFile()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        try {
            assertTrue(child.waitFor(45, TimeUnit.SECONDS), "independent cold Java process exceeded finite timeout");
            if (child.exitValue() != 0) assertTrue(Files.size(log) <= 65536, "bounded process failure output required");
            return child.exitValue();
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private Path produced(String name, boolean legacy) throws Exception {
        Path root = temporary.resolve(name); assertEquals(0, process(legacy ? "produce-legacy" : "produce-claim", root, name + "-producer.log")); return root;
    }
    @Test void actualCoreOpenRetainsLegacySeedAcrossIndependentJavaProcesses() throws Exception {
        Path root = produced("cold-legacy", true); assertEquals(0, process("cold", root, "cold-legacy-reader.log"));
    }
    @Test void actualCoreOpenRetainsUnknownClaimAcrossIndependentJavaProcessesWithoutRetry() throws Exception {
        Path root = produced("cold-claim", false);
        assertEquals(-33_554_431L, OrdinaryOnceClaims.decode(Files.readAllBytes(root.resolve("expected-state.json"))).claims().getFirst().claim().request().identity().actorId());
        assertEquals(0, process("cold", root, "cold-claim-reader.log"));
    }
    private static void replaceSameBytes(Path original) throws IOException {
        byte[] raw = Files.readAllBytes(original); Files.move(original, original.resolveSibling(original.getFileName() + ".retained-old")); Files.write(original, raw);
    }
    @Test void coldSameBytesClaimOriginalReplacementIsRefused() throws Exception {
        Path root = produced("claim-identity", false); var state = OrdinaryOnceClaims.decode(Files.readAllBytes(root.resolve("expected-state.json")));
        assertEquals(0, process("cold", root, "claim-identity-baseline.log"));
        replaceSameBytes(Path.of(state.claims().getFirst().original().path())); assertNotEquals(0, process("cold", root, "claim-identity-reader.log"));
    }
    @Test void coldSameBytesCanonicalBodyReplacementIsRefused() throws Exception {
        Path root = produced("body-identity", true); ExactRef body = ExactRef.fromJson(StrictJson.parse(Files.readAllBytes(root.resolve("expected-body-ref.json")), LIMIT));
        assertEquals(0, process("cold", root, "body-identity-baseline.log"));
        replaceSameBytes(Path.of(body.path())); assertNotEquals(0, process("cold", root, "body-identity-reader.log"));
    }
    @Test void currentProducerSelectionChangeRetainsUnknownKnowledgeWithoutRetry() throws Exception {
        Path root = produced("current-source-selection", false);
        assertEquals(0, process("cold-current-producer", root, "current-source-selection-reader.log"), Files.readString(temporary.resolve("current-source-selection-reader.log")));
    }
    @Test void coldChangedSelectedProducerIsRefused() throws Exception {
        Path root = produced("source-drift", false); assertEquals(0, process("cold", root, "source-drift-baseline.log"));
        Files.writeString(root.resolve("reviewed-producer.txt"), "different source closure");
        assertNotEquals(0, process("cold", root, "source-drift-reader.log"));
    }
    @Test void actualCoreOpenCannotTurnUncommittedCensusJsonIntoALiveSeed() throws Exception {
        Fixture fixture = initialize(temporary.resolve("uncommitted-seed"));
        var prepared = new RootOrdinaryClaimRuntime.Prepared(fixture.configuration().ledger().lock(), sources(fixture.producer()));
        var storage = StorageWriteGuardTestSupport.create(fixture.configuration().ledger());
        var core = RootApplicationAssembly.open(fixture.configuration(), Clock.systemUTC(), prepared.domainRegistrations(), Optional.empty(), storage); prepared.bindCore(core);
        byte[] before = Files.readAllBytes(fixture.configuration().ledger().snapshot());
        core.writer().locked(same -> {
            var archive = core.archive().withSession(same); ExactRef manifest = archive.preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("schema", RootOrdinaryClaimRuntime.MANIFEST_SCHEMA))));
            ExactRef empty = archive.preserveMaterial(new RawJson(OrdinaryOnceClaims.encode(new OrdinaryOnceClaims.State(fixture.configuration().machineId(), List.of(), List.of(), List.of()))));
            var request = new DomainBodies.ImportRequest(DomainBodies.Slot.ORDINARY_ONCE_CLAIM, OrdinaryOnceClaims.SCHEMA, empty,
                    input("LEGACY_SEED", null, null, manifest), List.of(manifest), "no-source-capture-ticket");
            assertThrows(IllegalArgumentException.class, () -> same.previewImport(request));
            assertThrows(IllegalArgumentException.class, () -> prepared.requireRetainedOriginal(same)); return null;
        });
        assertArrayEquals(before, Files.readAllBytes(fixture.configuration().ledger().snapshot()));
    }
}

