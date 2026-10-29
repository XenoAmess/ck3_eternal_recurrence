package org.xar.ck3.control.nativebridge.capabilities.religion;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventmaterial.RiteGrowthMaterial;

/** Actual pinned C++ mailbox fixtures enter the production Java decoder. No Game or qualification is claimed. */
final class PlayerReligionContextReadTest {
    @TempDir Path temporary;
    private JsonNode sourceMap;

    @Test void sixActualNativeProducerPacketsRoundTripEveryBaseField() throws Exception {
        for (String name : List.of("current-zero", "signed-values", "native-default", "legal-absent",
                "faith-unavailable", "fervor-unavailable")) {
            ObjectNode frame = fixture(name);
            PlayerReligionContextRead.Observation observation = PlayerReligionContextRead.decode(receipt(frame));
            assertEquals(frame.get("result").get("player_religion_context"), observation.context().encode(), name);
            assertEquals(observation.context(), PlayerReligionContext.decode(observation.context().encode()), name);
            assertNotEquals(observation.context().captureEpoch(), observation.metadata().queriedNativeRevision(), name);
            assertEquals(frame.get("result").get("status").textValue(), observation.metadata().status());
            assertEquals(observation.context().encode().size() + 12, PlayerReligionContextRead.flattened(observation).size());
        }
        var zero = PlayerReligionContextRead.decode(receipt(fixture("current-zero"))).context();
        assertEquals(BigInteger.ZERO, zero.riteId());
        assertEquals(new BigInteger("2197815299"), zero.faithId());
        assertEquals(BigInteger.ZERO, zero.faithFervorRaw());
        assertEquals(BigInteger.ZERO, zero.spiritualFulfillmentRaw());
        assertNull(PlayerReligionContextRead.decode(receipt(fixture("legal-absent"))).context().riteId());
        assertEquals(new BigInteger("-123456"),
                PlayerReligionContextRead.decode(receipt(fixture("signed-values"))).context().faithFervorRaw());
    }
    @Test void seventeenFieldBoundaryRejectsMissingUnknownWrongTypesAndPreservesUint32AndInt64Edges() throws Exception {
        ObjectNode nativeValue = (ObjectNode) fixture("current-zero").get("result").get("player_religion_context");
        for (String key : List.of("capture_epoch", "date_raw", "played_character_id", "rite_id", "faith_id",
                "religion_id", "faith_main_rite_id", "faith_fervor_raw", "spiritual_fulfillment_raw", "raw_scale")) {
            ObjectNode wrongBool = nativeValue.deepCopy(); wrongBool.put(key, true);
            assertThrows(IllegalArgumentException.class, () -> PlayerReligionContext.decode(wrongBool), key);
            ObjectNode wrongFloat = nativeValue.deepCopy(); wrongFloat.put(key, 1.0);
            assertThrows(IllegalArgumentException.class, () -> PlayerReligionContext.decode(wrongFloat), key);
        }
        ObjectNode lowerSha = nativeValue.deepCopy();
        lowerSha.put("executable_sha256", PlayerReligionContext.Build.CROZIER2.sha256().toLowerCase(java.util.Locale.ROOT));
        var casePreserving = PlayerReligionContext.decode(lowerSha);
        var metadata = new PlayerReligionContextRead.Metadata("religion-native-fixture", BigInteger.valueOf(702),
                BigInteger.valueOf(701), 53175816, BigInteger.valueOf(50331652),
                "ck3-1.20.0.2-native-player-religion-context-v1", "observed");
        ObjectNode flattened = PlayerReligionContextRead.flattened(new PlayerReligionContextRead.Observation(casePreserving, metadata));
        assertEquals(lowerSha.get("executable_sha256"), flattened.get("executable_sha256"));
        assertEquals(PlayerReligionContext.Build.CROZIER2.sha256(), flattened.get("exe_sha256").textValue());
        ObjectNode missing = nativeValue.deepCopy(); missing.remove("rite_id");
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContext.decode(missing));
        ObjectNode unknown = nativeValue.deepCopy(); unknown.put("rite", 0);
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContext.decode(unknown));
        ObjectNode edge = nativeValue.deepCopy();
        edge.put("rite_id", new BigInteger("4294967295")).put("capture_epoch", new BigInteger("18446744073709551615"))
                .put("faith_fervor_raw", BigInteger.valueOf(Long.MIN_VALUE)).put("spiritual_fulfillment_raw", BigInteger.valueOf(Long.MAX_VALUE));
        assertEquals(edge, PlayerReligionContext.decode(edge).encode());
        edge.put("rite_id", new BigInteger("4294967296"));
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContext.decode(edge));
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContext.decode("{\"schema\":1,\"schema\":1}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void originalPacketTokenActorAndSourceEnvelopeAreActuallyBound() throws Exception {
        ObjectNode wrongActor = fixture("current-zero");
        ((ObjectNode) wrongActor.get("result").get("player_religion_context")).put("played_character_id", 50331653);
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContextRead.decode(receipt(wrongActor)));
        ObjectNode wrongRevision = fixture("current-zero");
        ((ObjectNode) wrongRevision.get("result")).put("snapshot_revision", 702);
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContextRead.decode(receipt(wrongRevision)));
        ObjectNode wrongStatus = fixture("current-zero");
        ((ObjectNode) wrongStatus.get("result")).put("status", "unavailable");
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContextRead.decode(receipt(wrongStatus)));
        ObjectNode wrongBackend = fixture("current-zero");
        ((ObjectNode) wrongBackend.get("result")).put("backend_id", "ck3-1.20.0.4-native-player-religion-context-v1");
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContextRead.decode(receipt(wrongBackend)));
        PlanningReadReceipt original = receipt(fixture("current-zero"));
        NativeActionPort.AckReceived changedToken = new NativeActionPort.AckReceived(original.requestId(), true,
                Optional.of(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))),
                original.original().originalFrame(), original.original().originalPacket());
        PlanningReadReceipt tampered = new PlanningReadReceipt(original.request(), original.contractId(), original.requestId(),
                original.before(), original.after(), changedToken);
        assertThrows(IllegalArgumentException.class, () -> PlayerReligionContextRead.decode(tampered));
    }
    @Test void controlledBuildRemapReachesActualRiteGrowthConsumerAndWrongMetadataFailsClosed() throws Exception {
        // Controlled schema/build remap of the pinned .2 fixture, explicitly not a new native .4 execution receipt.
        ObjectNode frame = fixture("current-zero"), result = (ObjectNode) frame.get("result");
        remapFour(result);
        ObjectNode context = (ObjectNode) result.get("player_religion_context");
        context.put("schema", PlayerReligionContext.Build.CROZIER4.schema()); remapFour(context);
        PlayerReligionContextRead.Observation typed = PlayerReligionContextRead.decode(receipt(frame));
        ObjectNode query = PlayerReligionContextRead.flattened(typed), snapshot = snapshot();
        RiteGrowthMaterial.Observation compact = RiteGrowthMaterial.observe(query, snapshot);
        assertEquals(RiteGrowthMaterial.Status.AVAILABLE, compact.status());
        assertEquals(compact, RiteGrowthMaterial.decodeObservation(NativeWire.parse(RiteGrowthMaterial.encode(compact))));
        snapshot.set(RiteGrowthMaterial.SNAPSHOT_FIELD, NativeWire.parse(RiteGrowthMaterial.encode(compact)));
        ObjectNode decision = JsonNodeFactory.instance.objectNode().put("status", "recommended")
                .put("event_definition_key", "rite_growth.0010").put("ck3_build", "1.20.0.4")
                .put("selected_native_option_index", 0).put("selected_option_number", 1);
        var plan = RiteGrowthMaterial.plan(decision, snapshot).orElseThrow();
        assertEquals(RiteGrowthMaterial.Status.READY, plan.status());
        assertEquals(plan, RiteGrowthMaterial.decodeExpectation(RiteGrowthMaterial.encode(plan)));
        ObjectNode drift = query.deepCopy(); drift.put("queried_revision", 703);
        assertEquals(RiteGrowthMaterial.Status.UNAVAILABLE, RiteGrowthMaterial.observe(drift, snapshot).status());
        drift = query.deepCopy(); drift.put("queried_snapshot_id", "another-frame");
        assertEquals(RiteGrowthMaterial.Status.UNAVAILABLE, RiteGrowthMaterial.observe(drift, snapshot).status());
    }
    @Test void exactRegisteredNativeReadUsesLiveAdmissionWithoutOpeningImplementationFiles() throws Exception {
        Capture port = new Capture();
        ExactRef unavailable = new ExactRef(temporary.resolve("unavailable-live-producer").toString(), 1, "0".repeat(64));
        var sources = new PlayerReligionContextRead.Sources(unavailable, unavailable, unavailable);
        int[] admissions = {0};
        PlayerReligionContextRead adapter = new PlayerReligionContextRead(port, sources, (pins, request) -> admissions[0]++);
        PlanningReadRequest request = request(unavailable);
        assertThrows(Captured.class, () -> adapter.query_player_religion_context_v1(request));
        assertSame(adapter.contract(), port.contract); assertSame(request, port.request);
        NativeRequest prepared = adapter.contract().prepare(request, "religion-request-fixture");
        assertEquals(1, admissions[0]);
        assertTrue(prepared.requiredCapability().isEmpty());
        byte[] packet = NativeWire.executePrivateQuery("religion-request-fixture", prepared.step(),
                request.before().frame().identity().nativeRevision(), prepared.additionalFields().bytes());
        JsonNode wire = NativeWire.parse(java.util.Arrays.copyOfRange(packet, 4, packet.length));
        assertEquals(6, wire.size());
        assertEquals(701, wire.get("expected_revision").intValue());
        assertEquals(701, wire.get("expected_snapshot_revision").intValue());
        assertFalse(wire.has("character_id"));
        assertEquals(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, adapter.contract().permissionMode());
        assertEquals(ReadContract.WireProfile.G2_PRIVATE_QUERY, adapter.contract().wireProfile());
        PlanningReadRequest wrong = new PlanningReadRequest(request.before(), request.source(), request.sessionId(),
                request.operation(), new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(BigInteger.ONE))), request.deadline());
        assertThrows(IllegalArgumentException.class, () -> adapter.contract().prepare(wrong, "fixture"));
        assertEquals(1, admissions[0]);
        var driftedSources = new PlayerReligionContextRead.Sources(sources.pythonProducer(), sources.nativeMailbox(),
                new ExactRef(sources.nativeContext().path(), sources.nativeContext().bytes(), "f".repeat(64)));
        var driftedAdapter = new PlayerReligionContextRead(port, driftedSources, (pins, actual) -> admissions[0]++);
        NativeRequest driftedPrepared = driftedAdapter.contract().prepare(request, "fixture");
        assertEquals(2, admissions[0]);
        assertEquals(prepared.step(), driftedPrepared.step());
        assertArrayEquals(prepared.additionalFields().bytes(), driftedPrepared.additionalFields().bytes());

        PlayerReligionContextRead liveDenied = new PlayerReligionContextRead(port, sources, (pins, actual) -> {
            throw new IllegalArgumentException("actual live admission denied");
        });
        assertThrows(IllegalArgumentException.class, () -> liveDenied.contract().prepare(request, "fixture"));
        assertEquals(2, admissions[0]);
    }

    @Test void installedPureReplayUsesTheSameOriginalParserWithoutPreparingOrReadingLiveSources() throws Exception {
        ExactRef unavailable = new ExactRef(temporary.resolve("unavailable-live-producer").toString(), 1, "0".repeat(64));
        var sources = new PlayerReligionContextRead.Sources(unavailable, unavailable, unavailable);
        int[] admissions = {0};
        var query = new PlayerReligionContextRead(new Capture(), sources, (pins, request) -> admissions[0]++);
        assertTrue(query.contract().hasPureReplay());
        assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, query.contract().guardMode());
        for (String name : List.of("current-zero", "signed-values", "native-default", "legal-absent",
                "faith-unavailable", "fervor-unavailable")) {
            PlanningReadReceipt archived = receipt(fixture(name));
            assertEquals(PlayerReligionContextRead.flattened(PlayerReligionContextRead.decode(archived)),
                    PlayerReligionContextRead.flattened(query.contract().replay(archived)), name);
        }
        PlanningReadReceipt archived = receipt(fixture("current-zero"));
        assertEquals(0, admissions[0], "archival interpretation never prepares a query or invokes live admission");
        PlanningReadRequest wrongArguments = new PlanningReadRequest(archived.request().before(), archived.request().source(),
                archived.request().sessionId(), archived.request().operation(),
                new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(BigInteger.ONE))), archived.request().deadline());
        PlanningReadReceipt changedRequest = new PlanningReadReceipt(wrongArguments, archived.contractId(), archived.requestId(),
                archived.before(), archived.after(), archived.original());
        assertThrows(IllegalArgumentException.class, () -> query.contract().replay(changedRequest));
        ObjectNode wrongActor = fixture("current-zero");
        ((ObjectNode) wrongActor.get("result").get("player_religion_context")).put("played_character_id", 50331653);
        assertThrows(IllegalArgumentException.class, () -> query.contract().replay(receipt(wrongActor)));
        ObjectNode wrongRevision = fixture("current-zero");
        ((ObjectNode) wrongRevision.get("result")).put("snapshot_revision", 702);
        assertThrows(IllegalArgumentException.class, () -> query.contract().replay(receipt(wrongRevision)));
    }

    static void remapFour(ObjectNode value) {
        value.put("game_version", PlayerReligionContext.Build.CROZIER4.version())
                .put("executable_sha256", PlayerReligionContext.Build.CROZIER4.sha256());
        if (value.has("backend_id")) value.put("backend_id", "ck3-1.20.0.4-native-player-religion-context-v1");
    }
    static PlayerReligionContextReadTest fixtureAt(Path temporary) {
        PlayerReligionContextReadTest fixture = new PlayerReligionContextReadTest();
        fixture.temporary = java.util.Objects.requireNonNull(temporary);
        return fixture;
    }
    ObjectNode fixture(String name) throws Exception {
        ExactRef ref = input("fixture_" + name);
        return (ObjectNode) NativeWire.parse(pinned(ref));
    }
    private ExactRef input(String key) throws Exception {
        if (sourceMap == null) {
            byte[] map = Files.readAllBytes(Path.of(required("xar.religionContext.sourceMap")));
            assertEquals(required("xar.religionContext.sourceMapSha256"), sha(map), "source map drift");
            sourceMap = NativeWire.parse(map);
        }
        JsonNode ref = sourceMap.get("input_refs").get(key);
        assertNotNull(ref, "explicit original producer/fixture input missing: " + key);
        return new ExactRef(ref.get("path").textValue(), ref.get("bytes").longValue(), ref.get("sha256").textValue());
    }
    private static byte[] pinned(ExactRef ref) throws Exception {
        byte[] bytes = Files.readAllBytes(Path.of(ref.path()));
        assertEquals(ref.bytes(), bytes.length); assertEquals(ref.sha256(), sha(bytes)); return bytes;
    }
    PlanningReadRequest request() throws Exception {
        return request(input("python_producer"));
    }
    PlanningReadRequest request(ExactRef implementation) throws Exception {
        Instant now = Instant.now();
        G2Source source = new G2Source("software-fixture-machine", now.toString(), "actual-native-religion-fixture", implementation);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(50331652),
                BigInteger.valueOf(701), BigInteger.valueOf(53175816)), "religion-native-fixture", BigInteger.valueOf(702), "fixture-episode");
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new PlanningReadRequest(before, source, "fixture-session", PlayerReligionContextRead.OPERATION,
                new OpportunityJson.Obj(Map.of()), now.plusSeconds(60));
    }
    PlanningReadReceipt receipt(ObjectNode frame) throws Exception {
        PlanningReadRequest request = request(); Instant now = Instant.now();
        String buildSha = frame.get("result").get("executable_sha256").textValue();
        ObjectNode hello = JsonNodeFactory.instance.objectNode().put("type", "hello").put("protocol_version", 1)
                .put("pid", 42).put("connection_generation", 11).put("bridge_version", "software-fixture")
                .put("expected_ck3_sha256", buildSha).put("game_adapter_id", "native-fixture")
                .put("game_adapter_status", "ready").put("ck3_build_match", true);
        hello.putArray("capabilities");
        ExactRef helloRef = store("hello-" + temporaryCounter() + ".packet", NativeWire.packet(hello.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        byte[] payload = frame.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8), packet = NativeWire.packet(payload);
        ExactRef nativeRef = store("result-" + temporaryCounter() + ".packet", packet);
        GuardEvidence binding = new GuardEvidence(request.before(), request.source(), request.sessionId(),
                BigInteger.valueOf(11), PlayerReligionContextRead.OPERATION, nativeRef, helloRef,
                "software-fixture-only", now, now.plusSeconds(60));
        PlanningReadGuard guard = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
        String requestId = frame.get("request_id").textValue();
        var ack = new NativeActionPort.AckReceived(requestId, true,
                Optional.of(new RawJson(frame.get("result").toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))), new RawJson(payload), packet);
        return new PlanningReadReceipt(request, PlayerReligionContextRead.CONTRACT_ID, requestId, guard, guard, ack);
    }
    private int counter;
    private int temporaryCounter() { return ++counter; }
    private ExactRef store(String name, byte[] bytes) throws Exception {
        Path path = temporary.resolve(name); Files.write(path, bytes);
        return new ExactRef(path.toString(), bytes.length, sha(bytes));
    }
    private static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    private static String required(String key) {
        String value = System.getProperty(key);
        if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: actual original religion input property missing: " + key);
        return value;
    }
    static ObjectNode snapshot() {
        ObjectNode snapshot = JsonNodeFactory.instance.objectNode().put("snapshot_id", "religion-native-fixture")
                .put("revision", 702).put("native_revision", 701).put("date_raw", 53175816).put("paused", true).put("map_ready", true);
        snapshot.putObject("played_character").put("character_id", 50331652).put("alive", true);
        snapshot.putObject("diagnostics").putObject("hello").put("game_version", PlayerReligionContext.Build.CROZIER4.version())
                .put("executable_sha256", PlayerReligionContext.Build.CROZIER4.sha256());
        return snapshot;
    }
    private static final class Captured extends RuntimeException { private static final long serialVersionUID = 1; }
    private static final class Capture implements PlanningReadPort {
        private ReadContract<?> contract;
        private PlanningReadRequest request;
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> actualContract, PlanningReadRequest actualRequest) {
            contract = actualContract; request = actualRequest; throw new Captured();
        }
    }
}
