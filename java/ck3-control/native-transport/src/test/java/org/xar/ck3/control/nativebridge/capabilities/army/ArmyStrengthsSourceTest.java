package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPublicNumbers.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Controlled raw packet/source tests; these packets do not grant a live read permit or Game acceptance. */
public final class ArmyStrengthsSourceTest {
    public static final String VERSION = "1.20.0.4";
    public static final String SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    @Test void actualHelloAndOriginalQueryEvidenceAreRequiredBeforeExactBuild() throws Exception {
        var input = input(ArmyJson.empty(), projectedHello());
        assertTrue(input.exactNativeBuild(VERSION, SHA));
        assertFalse(new ArmyStrengthsPipeline.Input(input.snapshot(), input.original(), input.query(), input.selected()).exactNativeBuild(VERSION, SHA));
        var receipt = input.original().original();
        var guard = receipt.before(); var binding = guard.binding();
        var wrong = new ExactRef("controlled-wrong-hello", 1, "a".repeat(64));
        var crossed = new PlanningReadGuard(new GuardEvidence(binding.observed(), binding.source(), binding.sessionId(),
                binding.connectionGeneration(), binding.operation(), binding.nativeEvidence(), wrong, binding.authorityId(),
                binding.observedAt(), binding.validUntil()), guard.paused(), guard.mapReady(), guard.playerAlive(), guard.originalBindingSha256());
        var changed = new PlanningReadReceipt(receipt.request(), receipt.contractId(), receipt.requestId(), crossed, receipt.after(), receipt.original());
        var read = input.original();
        var crossedRead = new Read(read.profile(), read.status(), read.sequence(), read.backendId(), read.rows(), read.timing(), read.publishedScopeStatus(), changed);
        var crossedInput = new ArmyStrengthsPipeline.Input(input.snapshot(), crossedRead, input.query(), input.selected(), input.originalHello());
        assertThrows(IllegalArgumentException.class, crossedInput::actualNativeSource);
    }
    @Test void sourceKeyPresenceKeepsNullAndWrongDigestFromFallingBack() throws Exception {
        var result = ArmyJson.empty();
        result.putObject("source").putNull("game_version").put("executable_sha256", SHA);
        assertFalse(input(result, projectedHello()).exactNativeBuild(VERSION, SHA));
        result = ArmyJson.empty();
        result.putObject("source").put("game_version", VERSION).put("executable_sha256", "a".repeat(64));
        assertFalse(input(result, projectedHello()).exactNativeBuild(VERSION, SHA));
        var hello = projectedHello().putNull("expected_ck3_version").put("game_version", VERSION);
        assertFalse(input(ArmyJson.empty(), hello).exactNativeBuild(VERSION, SHA));
        var legacy = ArmyJson.empty().put("game_version", VERSION).put("executable_sha256", SHA);
        assertTrue(input(ArmyJson.empty(), legacy).exactNativeBuild(VERSION, SHA));
        var sourcePreferred = ArmyJson.empty();
        sourcePreferred.putObject("source").put("game_version", VERSION).put("executable_sha256", SHA);
        assertTrue(input(sourcePreferred, projectedHello().put("expected_ck3_version", "wrong")).exactNativeBuild(VERSION, SHA));
    }
    @Test void explicitlyDeclaredObjectUnionPreservesScalarBranchesWithoutRelaxingWildcardsOrIntegerTypes() {
        var rule = new Rule("/missing_inputs/*/physical_slot_i64", Domain.SIGNED_64, Traversal.OBJECT_BRANCHES).prefixed("/projection");
        var original = raw("{\"projection\":{\"missing_inputs\":[\"missing table\",{\"physical_slot_i64\":9223372036854775807},null]}}");
        var projected = ArmyStrengthsCodec.parseValue(encode(original, List.of(rule)));
        assertEquals("missing table", projected.at("/projection/missing_inputs/0").textValue());
        assertEquals("9223372036854775807", projected.at("/projection/missing_inputs/1/physical_slot_i64").textValue());
        assertTrue(ArmyStrengthsCodec.parseValue(original).at("/projection/missing_inputs/1/physical_slot_i64").isIntegralNumber());
        assertThrows(IllegalArgumentException.class, () -> encode(original, List.of(new Rule(rule.exactPath(), rule.domain()))));
        assertThrows(IllegalArgumentException.class, () -> encode(raw("{\"projection\":{\"missing_inputs\":{}}}"), List.of(rule)));
        assertThrows(IllegalArgumentException.class, () -> encode(raw("{\"projection\":{\"missing_inputs\":[[]]}}"), List.of(rule)));
        assertThrows(IllegalArgumentException.class, () -> encode(raw("{\"projection\":{\"missing_inputs\":[{\"physical_slot_i64\":true}]}}"), List.of(rule)));
    }
    @Test void installFromRealTempJarPreservesTraceAndRejectsInvalidRegistry() throws Exception {
        var dir = java.nio.file.Files.createTempDirectory("army-install");
        var file = dir.resolve("carrier.jar");
        java.nio.file.Files.write(file, new byte[]{1, 2, 3});
        var ref = new ExactRef(file.toString(), 3, ActionCodec.sha256(java.nio.file.Files.readAllBytes(file)));
        java.nio.file.Files.deleteIfExists(file);
        java.nio.file.Files.deleteIfExists(dir);
        var nf = new ArmyStrengthsNativeFields.Sources(ref, ref, ref);
        var ef = new ArmyStrengthsExistingFamilies.Sources(ref, ref, ref, ref, ref, ref, ref, ref);
        var src = new ArmyStrengthsInstallation.Sources(nf, ef, ref, ref, ref, ref, ref, ref, ref, ref, ref, ref, ref, ref);
        var inst = ArmyStrengthsInstallation.install(src);
        assertTrue(inst.families().coverage().complete());
        assertTrue(inst.pipeline().coverage().complete());
        var normalized = inst.families().normalize(ArmyStrengthsFamilies.Key.NATIVE_OWNER_RECALL_INPUTS_V1, new NullValue<>(), new RowContext(new Core(Status.AVAILABLE, new PublicUnitId(0), new Present<>(new FullId(0)), Role.PLAYER, List.of(), new Present<>(0), new Present<>(0), new Present<>(0), new Present<>(0L), new NullValue<>()), new Missing<>()));
        assertInstanceOf(NullValue.class, normalized.value());
        assertEquals(54, inst.pipeline().project(input(ArmyJson.empty(), projectedHello())).values().size());
        assertThrows(IllegalArgumentException.class, () -> inst.families().register(ArmyStrengthsFamilies.Key.NATIVE_OWNER_RECALL_INPUTS_V1, String.class, (v, r) -> new NullValue<>(), v -> raw("null"), ref));
    }
    public static ObjectNode projectedHello() { return ArmyJson.empty().put("expected_ck3_version", VERSION).put("expected_ck3_sha256", SHA); }
    /** Reusable test boundary for the same-query stage; caller supplies the exact controlled native result. */
    public static ArmyStrengthsPipeline.Input input(ObjectNode result, ObjectNode projectedHello) throws IOException {
        Instant now = Instant.now();
        ObjectNode helloBody = ArmyJson.empty().put("type", "hello").put("protocol_version", 1).put("pid", 42)
                .put("connection_generation", 5).put("bridge_version", "controlled").put("expected_ck3_version", VERSION)
                .put("expected_ck3_sha256", SHA).put("game_adapter_id", "ck3-1.20.0.4-msvc-x64")
                .put("game_adapter_status", "ready").put("ck3_build_match", true);
        helloBody.putArray("capabilities").add("game.state.snapshot").add(ArmyStrengths.CAPABILITY);
        byte[] helloPacket = NativeWire.packet(ArmyJson.bytes(helloBody));
        var hello = (NativeWire.Hello) NativeWire.decode(helloPacket);
        ExactRef cap = new ExactRef("controlled-original-hello-packet", helloPacket.length, ActionCodec.sha256(helloPacket));
        G2Source source = new G2Source("fixture-machine", now.toString(), "controlled", cap);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ZERO, BigInteger.valueOf(11), BigInteger.valueOf(53238336)), "native:11", BigInteger.valueOf(7), "fixture-episode");
        Context context = new Context(new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "fixture-session", now.plusSeconds(60));
        ObjectNode snapshotRaw = ArmyJson.empty().put("snapshot_id", "native:11").put("revision", 7).put("native_revision", 11).put("date_raw", 53238336).put("episode_run_id", "fixture-episode").put("paused", true).put("map_ready", true);
        snapshotRaw.putObject("played_character").put("character_id", 0).put("alive", true);
        snapshotRaw.putObject("diagnostics").put("connection_generation", 5).set("hello", projectedHello);
        snapshotRaw.putArray("player_armies").addObject().put("army_id", 0); snapshotRaw.putArray("active_wars");
        Snapshot snapshot = ArmyStrengthsCodec.snapshot(context, new RawJson(ArmyJson.bytes(snapshotRaw)));
        OperationKey operation = new OperationKey(STEP);
        var request = new PlanningReadRequest(context.before(), source, context.sessionId(), operation, new OpportunityJson.Obj(Map.of()), context.deadline());
        var guard = new PlanningReadGuard(new GuardEvidence(context.before(), source, context.sessionId(), BigInteger.valueOf(5), operation, cap, cap, "controlled", now, context.deadline()), true, true, true, "b".repeat(64));
        ObjectNode body = ArmyJson.empty().put("type", "command_result").put("protocol_version", 1).put("request_id", "controlled-source-read").put("ok", true);
        body.set("result", result);
        byte[] originalBody = ArmyJson.bytes(body);
        var ack = new NativeActionPort.AckReceived("controlled-source-read", true, Optional.of(new RawJson(ArmyJson.bytes(result))), new RawJson(originalBody), NativeWire.packet(originalBody));
        var receipt = new PlanningReadReceipt(request, "controlled-source-read", "controlled-source-read", guard, guard, ack);
        var read = new Read(Profile.ORDINARY_CORE_V1, Status.AVAILABLE, BigInteger.ONE, "controlled", List.of(), new Missing<>(), new Missing<>(), receipt);
        var query = new Query(Profile.ORDINARY_CORE_V1, Mode.EXPLICIT_RICH, new Present<>(List.of(new PublicUnitId(0))), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED);
        return new ArmyStrengthsPipeline.Input(snapshot, read, query, List.of(), Optional.of(hello));
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
}

