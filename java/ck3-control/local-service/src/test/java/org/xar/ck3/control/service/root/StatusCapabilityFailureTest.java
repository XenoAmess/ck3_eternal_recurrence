package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.FrontendFrame;
import org.xar.ck3.control.application.action.FrontendIdentity;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.PhysicalStatusIdentity;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Complete controlled packet DATA reaches the production gate. No file/source scope, Managed Game or Ready is issued. */
final class StatusCapabilityFailureTest {
    private static final String MACHINE = "controlled-status-capability-data";
    private static final BigInteger GENERATION = StrictJson.UINT64_MAX;
    private static final Instant OBSERVED = Instant.parse("2026-10-25T15:38:00Z");
    private record Input(CommandOrigin origin, G2Source source, ExactRef hello, byte[] packet) { }

    @Test void onlyAMissingStatusCapabilityOfAValidBoundOriginalHasTheTypedFailure() throws Exception {
        Input absent = input(body(false));
        var failure = assertThrows(StatusCapabilityFailure.class, () -> check(absent));
        assertSame(absent.origin(), failure.origin()); assertSame(absent.source(), failure.source());
        assertSame(absent.hello(), failure.originalHello());
        assertEquals("native DLL does not advertise required capability " + PhysicalStatusIdentity.CAPABILITY, failure.getMessage());
        assertDoesNotThrow(() -> check(input(body(true))), "an advertised capability creates no failure or qualification");
    }

    @Test void wrongOriginalBytesAndShaCannotBeReclassifiedAsUnsupported() throws Exception {
        Input original = input(body(false));
        for (ExactRef wrong : List.of(new ExactRef(original.hello().path(), original.hello().bytes() + 1, original.hello().sha256()),
                new ExactRef(original.hello().path(), original.hello().bytes(), "f".repeat(64))))
            ordinaryRefusal(new Input(original.origin(), original.source(), wrong, original.packet()));
        byte[] changed = original.packet().clone(); changed[changed.length - 1] ^= 1;
        ordinaryRefusal(new Input(original.origin(), original.source(), original.hello(), changed));
    }

    @Test void anotherGameConnectionSourceAndPhaseCannotBorrowThePhysicalFailureKind() throws Exception {
        var wrongPid = body(false); wrongPid.put("pid", 43); ordinaryRefusal(input(wrongPid));
        var wrongGeneration = body(false); wrongGeneration.put("connection_generation", GENERATION.subtract(BigInteger.ONE));
        ordinaryRefusal(input(wrongGeneration));
        Input original = input(body(false));
        var foreignSource = new G2Source(MACHINE, OBSERVED.toString(), "another-source", data("another-source"));
        ordinaryRefusal(new Input(original.origin(), foreignSource, original.hello(), original.packet()));
        var physical = original.origin().requirePhysicalStatusOnly();
        var frontend = new FrontendIdentity(MACHINE, physical.game(), physical.sessionId(), GENERATION, 42,
                new FrontendFrame.Menu(BigInteger.ONE), data("frontend"), original.hello());
        ordinaryRefusal(new Input(new CommandOrigin.Frontend(frontend), original.source(), original.hello(), original.packet()));
    }

    @Test void booleanFloatingAndMissingGenerationAreInputFailuresEvenWhenStatusIsAbsent() throws Exception {
        List<Consumer<ObjectNode>> mutations = List.of(row -> row.put("connection_generation", true),
                row -> row.put("connection_generation", 7.0), row -> row.remove("connection_generation"));
        for (var mutation : mutations) {
            var row = body(false); mutation.accept(row); ordinaryRefusal(input(row));
        }
    }

    @Test void missingSnapshotSupportWrongBuildAndUnreadyAdapterRemainOrdinarySourceFailures() throws Exception {
        var snapshotAbsent = body(false); snapshotAbsent.putArray("capabilities"); ordinaryRefusal(input(snapshotAbsent));
        var build = body(false); build.put("ck3_build_match", false); ordinaryRefusal(input(build));
        var adapter = body(false); adapter.put("game_adapter_status", "unavailable"); ordinaryRefusal(input(adapter));
    }

    private static void check(Input input) throws IOException {
        StatusCapabilityFailure.requireAdvertised(input.origin(), input.source(), input.hello(), input.packet());
    }
    private static void ordinaryRefusal(Input input) {
        Exception failure = assertThrows(Exception.class, () -> check(input));
        assertFalse(failure instanceof StatusCapabilityFailure, "invalid original DATA cannot impersonate a supported source with missing Status");
        assertTrue(failure instanceof IOException || failure instanceof IllegalArgumentException);
    }
    private static ObjectNode body(boolean status) {
        var row = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", 42)
                .put("connection_generation", GENERATION).put("bridge_version", "controlled-data")
                .put("expected_ck3_sha256", "0".repeat(64)).put("game_adapter_id", "controlled-data")
                .put("game_adapter_status", "ready").put("ck3_build_match", true);
        var caps = row.putArray("capabilities"); caps.add("game.state.snapshot");
        if (status) caps.add(PhysicalStatusIdentity.CAPABILITY);
        return row;
    }
    private static Input input(ObjectNode body) throws IOException {
        byte[] packet = NativeWire.packet(body.toString().getBytes(StandardCharsets.UTF_8));
        ExactRef hello = reference("hello.packet", packet);
        var source = new G2Source(MACHINE, OBSERVED.toString(), "controlled-packet-DATA", data("source"));
        var game = new GameGeneration(42, new PythonOnlyUInt64(GENERATION));
        var transport = new TransportSession(MACHINE, game, GENERATION, "controlled-status-session");
        var identity = new PhysicalStatusIdentity(transport, "native:7", BigInteger.valueOf(7), source,
                data("snapshot"), hello, data("heartbeat"), data("qualification"), data("epoch"), OBSERVED);
        return new Input(new CommandOrigin.PhysicalStatusOnly(identity), source, hello, packet);
    }
    private static ExactRef data(String role) { return reference(role + ".data", role.getBytes(StandardCharsets.UTF_8)); }
    private static ExactRef reference(String role, byte[] bytes) {
        return new ExactRef("D:/controlled-status-capability-data/" + role, bytes.length, DriverJson.sha256(bytes));
    }
}
