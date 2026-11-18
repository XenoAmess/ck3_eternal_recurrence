package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pinned actual C++ Full002 plus software HELLO/public frame DATA. No private Received, Live, Driver or Game is created. */
final class PersonalCashFullProjectionTest {
    private static final String MACHINE = "cash-projection-data", SESSION = "cash-projection-data-session";
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_1210;
    private static final String ADAPTER = "ck3-1.21.0-msvc-x64";
    private static final BigInteger CONNECTION = BigInteger.valueOf(3);
    private static final GameGeneration GAME = new GameGeneration(42,
            new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final Instant OBSERVED = Instant.parse("2026-11-18T00:00:00Z");

    @Test
    void originalCppFullStateProducesOnlyPacketDerivedCashInputDataAndLeavesOriginalsUnchanged() throws Exception {
        var frame = frame(); var hello = hello(helloData());
        byte[] originalState = frame.state().bytes(), originalFrame = frame.originalPacket(), originalHello = hello.packet().value();
        var state = DriverObservationAssembler.originalNativeState(frame);
        var projected = data(PersonalCashFullProjection.snapshotData(frame, hello));
        var expectedKeys = new HashSet<>(state.members().keySet()); expectedKeys.addAll(List.of("native_revision", "diagnostics"));
        assertEquals(expectedKeys, projected.members().keySet());
        for (var field : state.members().entrySet()) assertEquals(field.getValue(), projected.get(field.getKey()), field.getKey());
        assertEquals(new IntegerValue(frame.nativeRevision()), projected.get("native_revision"));
        assertEquals(BigInteger.TEN, integer(projected.get("native_revision"), "Native revision"));
        assertEquals(state.get("played_character"), projected.get("played_character"));
        assertEquals(state.get("date_raw"), projected.get("date_raw"));
        assertEquals(helloPayload(hello), object(projected.get("diagnostics"), "diagnostics").get("hello"));
        assertFalse(projected.members().containsKey("revision"), "no Driver public revision is invented");
        assertFalse(projected.members().containsKey("java_driver_facts_evidence"));
        assertFalse(projected.members().containsKey("episode_run_id"));
        assertFalse(projected.members().containsKey("same_frame_ready"));
        assertArrayEquals(originalState, frame.state().bytes()); assertArrayEquals(originalFrame, frame.originalPacket());
        assertArrayEquals(originalHello, hello.packet().value());
    }

    @Test
    void matchingExistingFieldsAreRetainedAndConflictingTypesOrValuesAreNeverOverwritten() throws Exception {
        var frame = frame(); var hello = hello(helloData());
        var original = DriverObservationAssembler.originalNativeState(frame);
        var diagnostics = new Obj(Map.of("hello", helloPayload(hello), "original_note", new Text("retained DATA")));
        var matching = original.with("native_revision", new IntegerValue(frame.nativeRevision())).with("diagnostics", diagnostics);
        assertEquals(matching, data(PersonalCashFullProjection.snapshotData(withState(frame, matching), hello)));
        for (var invalid : List.<Value>of(new IntegerValue(frame.nativeRevision().add(BigInteger.ONE)),
                new DecimalValue("10.0"), new Text("10"), Nil.INSTANCE)) {
            var changed = withState(frame, original.with("native_revision", invalid));
            assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(changed, hello));
        }
        var foreignHello = helloPayload(hello).with("expected_ck3_version", new Text("1.20.0.4"));
        var conflict = withState(frame, original.with("diagnostics", new Obj(Map.of("hello", foreignHello))));
        assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(conflict, hello));
        var nullDiagnostics = withState(frame, original.with("diagnostics", Nil.INSTANCE));
        assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(nullDiagnostics, hello));
    }

    @Test
    void helloPacketTypedFieldsAndFramePidConnectionAndFlorinTupleMustAgree() throws Exception {
        var frame = frame();
        for (String mismatch : List.of("pid", "connection", "version", "hash", "adapter", "status", "build-match")) {
            var source = helloData();
            switch (mismatch) {
                case "pid" -> source.put("pid", GAME.pid() + 1);
                case "connection" -> source.put("connection_generation", CONNECTION.add(BigInteger.ONE));
                case "version" -> source.put("expected_ck3_version", "1.21.0.0");
                case "hash" -> source.put("expected_ck3_sha256", ExactCk3Build.CK3_12004.executableSha256());
                case "adapter" -> source.put("game_adapter_id", "ck3-1.20.0.4-msvc-x64");
                case "status" -> source.put("game_adapter_status", "unavailable");
                case "build-match" -> source.put("ck3_build_match", false);
                default -> throw new AssertionError(mismatch);
            }
            var invalid = hello(source);
            assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(frame, invalid), mismatch);
        }
        var source = hello(helloData());
        var typedMismatch = new NativeWire.Hello(source.pid() + 1, source.connectionGeneration(), source.bridgeVersion(),
                source.gameSha256(), source.adapterId(), source.adapterStatus(), source.buildMatch(), source.capabilities(), source.packet());
        assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(frame, typedMismatch));
        var wrongPacket = new NativeWire.Hello(source.pid(), source.connectionGeneration(), source.bridgeVersion(), source.gameSha256(),
                source.adapterId(), source.adapterStatus(), source.buildMatch(), source.capabilities(), new NativeWire.Bytes(frame.originalPacket()));
        assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(frame, wrongPacket));
    }

    @Test
    void inconsistentFramePacketOrStateAndMixedFullSourceAreRefusedBeforeDataProjection() throws Exception {
        var frame = frame(); var hello = hello(helloData());
        var wrongId = new ObservedFrame(frame.session(), "native:11", frame.nativeRevision(), frame.state(), frame.originalPacket(), frame.observedAt());
        assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(wrongId, hello));
        var original = DriverObservationAssembler.originalNativeState(frame);
        var wrongState = original.with("date_raw", new IntegerValue(BigInteger.valueOf(123457)));
        var inconsistent = new ObservedFrame(frame.session(), frame.snapshotId(), frame.nativeRevision(),
                new RawJson(DriverJson.encode(wrongState)), frame.originalPacket(), frame.observedAt());
        assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(inconsistent, hello));
        for (String field : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend")) {
            var mixed = withState(frame, original.with(field, new Text("unqualified-DATA")));
            assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(mixed, hello), field);
        }
        var foreignSession = new TransportSession(MACHINE, new GameGeneration(43, GAME.creationFiletime()), CONNECTION, SESSION);
        var foreign = new ObservedFrame(foreignSession, frame.snapshotId(), frame.nativeRevision(), frame.state(), frame.originalPacket(), frame.observedAt());
        assertThrows(IllegalArgumentException.class, () -> PersonalCashFullProjection.snapshotData(foreign, hello));
    }

    private static Obj data(RawJson value) { return DriverJson.object(value.bytes(), DriverJson.MAX_NATIVE_BYTES); }
    private static Obj helloPayload(NativeWire.Hello hello) {
        byte[] packet = hello.packet().value(); return DriverJson.object(Arrays.copyOfRange(packet, 4, packet.length), DriverJson.MAX_NATIVE_BYTES);
    }
    private static NativeWire.Hello hello(ObjectNode source) throws Exception {
        return assertInstanceOf(NativeWire.Hello.class, NativeWire.decode(NativeWire.packet(StrictJson.canonical(source))));
    }
    private static ObjectNode helloData() {
        var source = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", GAME.pid())
                .put("connection_generation", CONNECTION).put("bridge_version", "software-personal-cash-projection")
                .put("expected_ck3_version", BUILD.version()).put("expected_ck3_sha256", BUILD.executableSha256())
                .put("game_adapter_id", ADAPTER).put("game_adapter_status", "ready").put("ck3_build_match", true);
        source.putArray("capabilities").add("game.state.snapshot"); return source;
    }
    private static ObservedFrame frame() throws Exception {
        String name = "full-snapshot-producer-002.json", root = System.getProperty("xar.native.full1210.fixtures");
        byte[] original;
        if (root == null || root.isBlank()) {
            try (var stream = PersonalCashFullProjectionTest.class.getResourceAsStream("/newnative/full1210/" + name)) {
                if (stream == null) throw new java.io.IOException("exact C++ Full002 resource missing");
                original = stream.readNBytes(1172);
            }
        } else {
            var directory = Path.of(root);
            if (!directory.isAbsolute()) throw new java.io.IOException("absolute actual Full1210 fixture directory required");
            try (var stream = Files.newInputStream(directory.resolve(name))) { original = stream.readNBytes(1172); }
        }
        assertEquals(1171, original.length);
        assertEquals("5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        var packet = NativeWire.packet(original);
        var snapshot = assertInstanceOf(NativeWire.Snapshot.class, NativeWire.decode(packet));
        return new ObservedFrame(new TransportSession(MACHINE, GAME, CONNECTION, SESSION), snapshot.snapshotId(), snapshot.revision(),
                new RawJson(snapshot.state().value()), packet, OBSERVED);
    }
    /** Explicit modified public packet DATA for negative/matching-field cases; never an original C++ or private receipt. */
    private static ObservedFrame withState(ObservedFrame original, Obj state) throws Exception {
        byte[] packet = original.originalPacket();
        var envelope = DriverJson.object(Arrays.copyOfRange(packet, 4, packet.length), DriverJson.MAX_NATIVE_BYTES);
        byte[] modified = NativeWire.packet(DriverJson.encode(envelope.with("state", state)));
        return new ObservedFrame(original.session(), original.snapshotId(), original.nativeRevision(),
                new RawJson(DriverJson.encode(state)), modified, original.observedAt());
    }
}
