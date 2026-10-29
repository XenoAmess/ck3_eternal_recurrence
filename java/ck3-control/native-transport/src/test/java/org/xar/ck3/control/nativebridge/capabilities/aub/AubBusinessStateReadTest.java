package org.xar.ck3.control.nativebridge.capabilities.aub;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Consumes the existing native fixture's real production serializer, never a replacement DTO producer. */
final class AubBusinessStateReadTest {
    @TempDir Path temporary;
    private int sequence;
    private static ObservationIdentity before() {
        return new ObservationIdentity("fixture-machine", new GameGeneration(12700, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31254), BigInteger.valueOf(7), BigInteger.valueOf(1234)),
                        "aub-fixture-snapshot", BigInteger.valueOf(9), "aub-fixture-episode"), 1);
    }
    private RawJson actualProducer() throws Exception {
        String executable = System.getProperty("xar.aub.native.producer");
        String sha256 = System.getProperty("xar.aub.native.producer.sha256");
        if (executable == null || executable.isBlank() || !Path.of(executable).isAbsolute())
            throw new IllegalStateException("NOT EXECUTED: required absolute xar.aub.native.producer target xar_ck3_aub_business_state_v1_test missing");
        if (sha256 == null || !sha256.matches("[a-f0-9]{64}"))
            throw new IllegalStateException("NOT EXECUTED: exact xar.aub.native.producer.sha256 from actual native build required");
        var witness = org.xar.ck3.control.build.SharedSourceFiles.observe(Path.of(executable));
        assertEquals(sha256, witness.source().sha256(), "actual native AUB fixture executable drift");
        Path output = temporary.resolve("aub-producer-" + (++sequence) + ".json");
        Path error = temporary.resolve("aub-producer-" + sequence + ".stderr");
        Process process = new ProcessBuilder(executable, "serialization").redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if (!process.waitFor(20, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("actual native AUB producer timeout"); }
        if (process.exitValue() != 0) throw new IOException("actual native AUB producer failed: " + Files.readString(error, StandardCharsets.UTF_8));
        org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(witness);
        return new RawJson(Files.readAllBytes(output));
    }
    @Test void actualNativeFlagProducerDecodesAndFormatsTheOriginalPublicReadWithoutProductCredit() throws Exception {
        RawJson raw = actualProducer();
        var state = AubBusinessStateRead.decodeMaterial(raw, before(), BigInteger.ONE);
        assertEquals(4, state.flags().size()); assertTrue(state.flags().get(0).present());
        assertFalse(state.flags().get(1).present()); assertFalse(state.detail().effectivelyVisible());
        ObjectNode publicResult = NativeWire.object(NativeWire.parse(AubBusinessStateRead.normalizedForPublic(state).bytes()));
        assertEquals("aub-fixture-episode", publicResult.get("episode_run_id").textValue());
        assertEquals("9", publicResult.get("queried_revision").textValue());
        assertEquals("7", publicResult.get("native_revision").textValue());
        assertEquals("1", publicResult.get("connection_generation").textValue());
        for (String key : List.of("uses_mouse", "uses_keyboard", "uses_ocr", "full_product_acceptance_credit", "product_acceptance_proven"))
            assertFalse(publicResult.get(key).booleanValue());
        assertEquals(NativeWire.parse(raw.bytes()).get("flags"), publicResult.get("flags"));
        var roundtrip = AubBusinessStateRead.decodeMaterial(new RawJson(NativeWire.parse(raw.bytes()).toString().getBytes(StandardCharsets.UTF_8)), before(), BigInteger.ONE);
        assertEquals(state.flags(), roundtrip.flags()); assertEquals(state.detail(), roundtrip.detail());
        ObjectNode large = NativeWire.object(NativeWire.parse(raw.bytes()));
        BigInteger largeGeneration = new BigInteger("9007199254740992"); large.put("connection_generation", largeGeneration);
        var exactInternal = AubBusinessStateRead.decodeMaterial(new RawJson(large.toString().getBytes(StandardCharsets.UTF_8)), before(), largeGeneration);
        assertEquals(largeGeneration, exactInternal.connectionGeneration());
        RawJson exactPublic=AubBusinessStateRead.normalizedForPublic(exactInternal);
        assertEquals(largeGeneration.toString(),NativeWire.parse(exactPublic.bytes()).get("connection_generation").textValue());
        assertEquals(NativeWire.parse(exactPublic.bytes()),NativeWire.parse(AubPublicCodec.readPublic(AubPublicCodec.Operation.BUSINESS,exactPublic).bytes()));
        assertTrue(NativeWire.parse(exactInternal.original().bytes()).get("connection_generation").isIntegralNumber(),"original native token remains numeric");
    }
    @Test void actualProducerRejectsWrongMissingExtraAndBooleanNumericTokensAndUnavailableFlags() throws Exception {
        ObjectNode actual = NativeWire.object(NativeWire.parse(actualProducer().bytes()));
        for (String key : List.of("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw")) {
            ObjectNode wrongBoolean = actual.deepCopy(); wrongBoolean.put(key, true); reject(wrongBoolean);
            ObjectNode wrongFloat = actual.deepCopy(); wrongFloat.put(key, 1.0); reject(wrongFloat);
            ObjectNode missing = actual.deepCopy(); missing.remove(key); reject(missing);
        }
        ObjectNode extra = actual.deepCopy(); extra.put("accepted", true); reject(extra);
        ObjectNode wrongBuild = actual.deepCopy(); wrongBuild.put("game_version", "1.20.0.4"); reject(wrongBuild);
        ObjectNode incomplete = actual.deepCopy(); incomplete.withArray("flags").remove(0); reject(incomplete);
        ObjectNode nullFlag = actual.deepCopy(); ((ObjectNode) nullFlag.withArray("flags").get(0)).putNull("present"); reject(nullFlag);
        ObjectNode unregistered = actual.deepCopy(); ((ObjectNode) unregistered.withArray("flags").get(0)).put("atom_registered", false); reject(unregistered);
        ObjectNode reordered = actual.deepCopy(); ((ObjectNode) reordered.withArray("flags").get(0)).put("key", "aub_funding_personal_only"); reject(reordered);
        ObjectNode product = actual.deepCopy(); product.put("product_acceptance_proven", true); reject(product);
    }
    @Test void originalHelloAndSnapshotBindingRequiresExactBuildAndExplicitAbsentModalFields() throws Exception {
        String hello = "{\"type\":\"hello\",\"protocol_version\":1,\"pid\":12700,\"connection_generation\":1,\"bridge_version\":\"fixture\","
                + "\"expected_ck3_sha256\":\"" + AubBusinessStateRead.GAME_SHA256 + "\",\"expected_ck3_version\":\"1.20.0.3\","
                + "\"game_adapter_id\":\"ck3-1.20.0.3-msvc-x64\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,"
                + "\"capabilities\":[\"" + AubBusinessStateRead.CAPABILITY + "\"]}";
        var originalHello = (NativeWire.Hello) NativeWire.decode(NativeWire.packet(hello.getBytes(StandardCharsets.UTF_8)));
        String frame = "{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"aub-fixture-snapshot\",\"revision\":7,\"state\":{"
                + "\"date_raw\":1234,\"paused\":true,\"map_ready\":true,\"active_event\":null,\"pending_character_interaction\":null,"
                + "\"played_character\":{\"character_id\":31254,\"alive\":true}}}";
        var originalSnapshot = (NativeWire.Snapshot) NativeWire.decode(NativeWire.packet(frame.getBytes(StandardCharsets.UTF_8)));
        AubBusinessStateRead.validateFrame(before(), BigInteger.ONE, originalSnapshot, originalHello);
        for (String modal : List.of("active_event", "pending_character_interaction")) {
            ObjectNode changed = NativeWire.object(NativeWire.parse(frame.getBytes(StandardCharsets.UTF_8)));
            ((ObjectNode) changed.get("state")).remove(modal);
            var missing = (NativeWire.Snapshot) NativeWire.decode(NativeWire.packet(changed.toString().getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> AubBusinessStateRead.validateFrame(before(), BigInteger.ONE, missing, originalHello));
            ((ObjectNode) changed.get("state")).putObject(modal);
            var active = (NativeWire.Snapshot) NativeWire.decode(NativeWire.packet(changed.toString().getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> AubBusinessStateRead.validateFrame(before(), BigInteger.ONE, active, originalHello));
        }
        assertThrows(IllegalArgumentException.class, () -> AubBusinessStateRead.validateFrame(before(), BigInteger.TWO, originalSnapshot, originalHello));
    }
    private static void reject(ObjectNode row) {
        Exception rejected = assertThrows(Exception.class, () -> AubBusinessStateRead.decodeMaterial(new RawJson(row.toString().getBytes(StandardCharsets.UTF_8)), before(), BigInteger.ONE));
        assertTrue(rejected instanceof IllegalArgumentException || rejected instanceof IOException, "unexpected decoder failure: " + rejected.getClass());
    }
}
