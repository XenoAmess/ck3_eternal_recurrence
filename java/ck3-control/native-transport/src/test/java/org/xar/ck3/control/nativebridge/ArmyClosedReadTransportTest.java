package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyClosedReadContracts;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyClosedReadService;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatFrames;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Original C++ producer fixture -> actual NativeGameTransport -> actual read coordinator -> public binding.
 * Offline packet replay proves software routing only; no native process, original writer or Game acceptance is claimed.
 */
final class ArmyClosedReadTransportTest {
    @TempDir Path temporary;
    private int sequence;
    private static final String SHA3 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    @Test void actualHeldTransportAndCoordinatorConsumeTheOriginalProducerWithoutWorldIntent() throws Exception { chain(false); }
    @Test void rejectedNativeResultProducesNoFallbackQueryOrWorldIntent() throws Exception { chain(true); }
    private void chain(boolean reject) throws Exception {
        byte[] originalHello = packet(StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", 42)
                .put("connection_generation", new BigInteger("18446744073709551615")).put("bridge_version", "fixture").put("expected_ck3_sha256", SHA3)
                .put("game_adapter_id", "ck3-1.20.0.3-fixture").put("game_adapter_status", "ready").put("ck3_build_match", true)
                .set("capabilities", StrictJson.parse("[\"game.state.snapshot\",\"game.command.query-player-default-raise-v1\",\"game.command.query-raiktor-actual-truce-expiry-v1-N\",\"game.command.query-army-strengths-v1\"]".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        ObjectNode state = StrictJson.object().put("date_raw", 53238336).put("paused", true).put("map_ready", true);
        state.set("played_character", StrictJson.object().put("character_id", 29829).put("alive", true));
        ObjectNode snapshot = StrictJson.object().put("type", "state_snapshot").put("protocol_version", 1).put("snapshot_id", "native:11").put("revision", 11); snapshot.set("state", state);
        byte[] originalSnapshot = packet(snapshot); Replay port = new Replay(originalHello, originalSnapshot);
        ObjectNode producer = originalFixture();
        port.react = requestPacket -> {
            ObjectNode request = StrictJson.object(StrictJson.parse(Arrays.copyOfRange(requestPacket, 4, requestPacket.length)), Set.of("type", "protocol_version", "request_id", "step", "expected_revision"));
            assertEquals("execute_step", request.get("type").textValue()); assertEquals("query-player-default-raise-v1", request.get("step").textValue());
            assertEquals(BigInteger.valueOf(11), request.get("expected_revision").bigIntegerValue(), "native and public revisions must remain distinct");
            ObjectNode result = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", request.get("request_id").textValue()).put("ok", !reject);
            if (reject) result.put("error", "fixture native rejection"); else result.set("result", producer);
            port.frames.addLast(packet(result));
        };
        var config = new NativePipeEndpoint.Config("\\\\.\\pipe\\army-closed-read-fixture", "fixture-machine", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), "fixture-session", "fixture", SHA3, "ck3-1.20.0.3-fixture");
        try (NativeGameTransport transport = new NativeGameTransport(port, config, 16, 16)) {
            var observed = transport.observe(Instant.now().plusSeconds(20));
            ExactRef nativeRef = preserve("original-snapshot", observed.originalPacket()), helloRef = preserve("original-hello", originalHello);
            Instant now = Instant.now(); var source = new G2Source("fixture-machine", now.toString(), "1.20.0.3", nativeRef);
            var before = new ProposalLifecycle.ObservationIdentity(source.machineId(), config.game(), new JointBudgetSelector.ProposalFrame(
                    new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(11), BigInteger.valueOf(53238336)), "native:11", BigInteger.valueOf(7), "fixture-episode"), 1);
            var context = new ArmyTypes.Context(before, source, config.sessionId(), now.plusSeconds(20));
            var definitions = new ArmyClosedReadContracts(nativeRef, helloRef);
            var catalog = new RootReadContractCatalog(List.of(), definitions.families());
            ReadJournal journal = new ReadJournal(); ReadArchive archive = new ReadArchive();
            PlanningReadCoordinator coordinator = new PlanningReadCoordinator(catalog, journal, (head, request, contract) ->
                    new PlanningReadGuard(new GuardEvidence(before, source, config.sessionId(), observed.session().connectionGeneration(), request.operation(), nativeRef, helloRef,
                            "fixture-authority", now, context.deadline()), true, true, true, "b".repeat(64)), transport, archive, Clock.systemUTC());
            // Explicit fixture Driver facts joined to the actual observed Native state; this fixture grants no real Driver/Game credit.
            ObjectNode semantic = ((ObjectNode)StrictJson.parse(observed.state().bytes())).deepCopy();
            semantic.put("snapshot_id", before.frame().snapshotId()).put("revision", before.frame().revision()).put("native_revision", observed.nativeRevision()).put("episode_run_id", before.frame().episodeRunId());
            semantic.putObject("diagnostics").put("connection_generation", observed.session().connectionGeneration()).put("bridge_pid", config.game().pid());
            var semanticValue = DriverJson.object(StrictJson.canonical(semantic), DriverJson.MAX_NATIVE_BYTES);
            var complete = new DriverObservationAssembler.Complete(before, source, config.sessionId(), observed.session().connectionGeneration(), semanticValue, nativeRef, observed.observedAt(), DriverObservationAssembler.bindingSha256(semanticValue));
            var current = new ArmyRetreatFrames.Current(complete, context.deadline());
            var service = new ArmyClosedReadService(() -> current, coordinator, catalog, definitions);
            PublicBindings bindings = new PublicBindings(); service.install(bindings, nativeRef); bindings.freeze(ArmyClosedReadContracts.METHODS);
            assertEquals(3, bindings.coverage().installed().size());
            var binding = bindings.lookup(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1).orElseThrow();
            for (String bad : List.of("{\"expected_revision\":true}", "{\"expected_revision\":7.0}", "{\"expected_revision\":8}", "{\"expected_revision\":7,\"extra\":true}"))
                assertThrows(RuntimeException.class, () -> binding.invoke(PublicBindings.present(raw(bad))));
            assertEquals(0, port.writes);
            if (reject) {
                assertThrows(IllegalStateException.class, () -> binding.invoke(PublicBindings.present(raw("{\"expected_revision\":7}"))));
                assertTrue(archive.reads.isEmpty());
            } else {
                var result = StrictJson.parse(binding.invoke(PublicBindings.present(raw("{\"expected_revision\":7}"))).bytes());
                assertFalse(result.has("public_wire_schema")); assertFalse(result.has("integer_paths")); assertTrue(result.get("player_default_raise").get("unraised_troops_scale").isIntegralNumber());
                assertEquals("11", result.get("snapshot_revision").textValue()); assertEquals("7", result.get("queried_revision").textValue());
                assertEquals("fixture-episode", result.get("queried_episode_run_id").textValue()); assertEquals(observed.session().connectionGeneration().toString(), result.get("queried_connection_generation").textValue());
                assertEquals(42, result.get("queried_bridge_pid").intValue()); assertTrue(result.get("queried_bridge_pid").isIntegralNumber());
                assertTrue(result.get("player_default_raise").get("native_default_raise_legal").booleanValue());
                assertEquals(1, archive.reads.size());
                var receipt = archive.reads.values().iterator().next();
                assertEquals(producer, StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()));
                assertArrayEquals(receipt.original().originalPacket(), Files.readAllBytes(Path.of(archive.readReferenceOf(receipt).path())));
            }
            assertEquals(1, port.writes); assertEquals(0, journal.worldAppends); assertEquals(1, journal.locks);
        }
    }
    private static RawJson raw(String json) { return new RawJson(json.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
    private static byte[] packet(com.fasterxml.jackson.databind.JsonNode json) throws IOException { return NativeWire.packet(StrictJson.canonical(json)); }
    private ObjectNode originalFixture() throws Exception {
        String file = required("xar.army.defaultRaise.fixture"), hash = required("xar.army.defaultRaise.sha256"); byte[] original = Files.readAllBytes(Path.of(file));
        assertEquals(hash, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        return (ObjectNode) StrictJson.parse(original).get("legal");
    }
    private static String required(String key) { String value = System.getProperty(key); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: missing original fixture property " + key); return value; }
    private ExactRef preserve(String name, byte[] original) throws Exception { Path path = temporary.resolve(name + "-" + ++sequence + ".bin"); Files.write(path, original); return new ExactRef(path.toString(), original.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original))); }
    private static final class ReadJournal implements ActionJournal, ActionJournal.LockedJournal {
        int locks, worldAppends;
        @Override public <T> T locked(Function<ActionJournal.LockedJournal,T> work) { locks++; return work.apply(this); }
        @Override public org.xar.ck3.control.continuity.writer.WriterContracts.Head head() { return null; }
        @Override public Optional<ActionReceipt> find(String id) { return Optional.empty(); }
        @Override public List<ActionReceipt> unresolved() { return List.of(); }
        @Override public ActionReceipt append(ActionCommand command, String digest, ActionState state) { worldAppends++; throw new AssertionError("read appended a world intent"); }
    }
    private final class ReadArchive implements ActionPorts.OutcomeArchive {
        final Map<ExactRef,PlanningReadReceipt> reads = new HashMap<>();
        @Override public ExactRef preserveRead(PlanningReadReceipt receipt) { try { ExactRef ref = ArmyClosedReadTransportTest.this.preserve("read", receipt.original().originalPacket()); reads.put(ref, receipt); return ref; } catch (Exception failure) { throw new IllegalStateException(failure); } }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { return Optional.ofNullable(reads.get(ref)).orElseThrow(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt receipt) { return reads.entrySet().stream().filter(entry -> entry.getValue() == receipt).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        private UnsupportedOperationException unsupported() { return new UnsupportedOperationException("read-only fixture archive"); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { throw unsupported(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { throw unsupported(); }
        @Override public ExactRef preserveRequest(NativeRequest value) { throw unsupported(); }
        @Override public NativeRequest loadRequest(ExactRef ref) { throw unsupported(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { throw unsupported(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { throw unsupported(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw unsupported(); }
        @Override public ActionRecord loadRecord(ExactRef ref) { throw unsupported(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw unsupported(); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { throw unsupported(); }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { throw unsupported(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { throw unsupported(); }
        @Override public ExactRef preserveMaterial(RawJson value) { throw unsupported(); }
        @Override public RawJson loadMaterial(ExactRef ref) { throw unsupported(); }
        @Override public ExactRef materialReferenceOf(RawJson value) { throw unsupported(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw unsupported(); }
        @Override public byte[] loadNativeFrame(ExactRef ref) { throw unsupported(); }
    }
    @FunctionalInterface private interface React { void apply(byte[] packet) throws Exception; }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> frames = new ArrayDeque<>(); int writes; React react = packet -> { };
        Replay(byte[]... initial) { frames.addAll(Arrays.asList(initial)); }
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException { if (frames.isEmpty()) throw new IOException("fixture exhausted"); return frames.removeFirst().clone(); }
        @Override public void writePacket(byte[] packet, Instant deadline) throws IOException { writes++; try { react.apply(packet.clone()); } catch (Exception failure) { throw new IOException(failure); } }
        @Override public void close() { }
    }
}
