package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.CommandOriginCodec;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.PhysicalStatusIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.service.root.RootStatusCapabilityFailureAssertions;

/** Controlled native packet DATA -> production refusal -> actual public consumers.
 * Replay dispatch is controlled protocol coverage; no Managed Game, qualified source, lease or stock Status business result is claimed. */
final class PublicStatusCapabilityFailureTest {
    @org.junit.jupiter.api.io.TempDir java.nio.file.Path temporary;
    private static final String MACHINE = "controlled-public-status-data";
    private static final BigInteger GENERATION = StrictJson.UINT64_MAX;
    private static final Instant OBSERVED = Instant.parse("2026-10-25T15:38:00Z");

    @Test void missingStatusSupportSurvivesColdOriginAndEveryOriginalPublicConsumer() throws Exception {
        for (var consumer : PublicPlanningRpcAssertions.Consumer.values()) {
            byte[] packet = hello();
            var hello = reference("hello.packet", packet);
            var source = new G2Source(MACHINE, OBSERVED.toString(), "controlled-packet-DATA", data("source"));
            var transport = new NativeObservationPort.TransportSession(MACHINE,
                    new GameGeneration(42, new PythonOnlyUInt64(GENERATION)), GENERATION, "controlled-status-session");
            var identity = new PhysicalStatusIdentity(transport, "native:7", BigInteger.valueOf(7), source,
                    data("snapshot"), hello, data("heartbeat"), data("qualification"), data("epoch"), OBSERVED);
            var origin = new CommandOrigin.PhysicalStatusOnly(identity);

            // Use the actual durable codecs; full-width fields must survive the JSON boundary exactly.
            byte[] encoded = StrictJson.canonical(CommandOriginCodec.origin(origin));
            var restored = CommandOriginCodec.origin(StrictJson.parse(encoded));
            assertEquals(origin, restored);
            assertEquals(GENERATION, restored.requirePhysicalStatusOnly().connectionGeneration());
            assertEquals(GENERATION, restored.game().creationFiletime().value());
            var restoredHello = ExactRef.fromJson(StrictJson.parse(StrictJson.canonical(hello.toJson())));
            assertEquals(hello, restoredHello);
            var decoded = assertInstanceOf(NativeWire.Hello.class, NativeWire.decode(packet.clone()));
            assertEquals(GENERATION, decoded.connectionGeneration());
            assertFalse(decoded.capabilities().contains(PhysicalStatusIdentity.CAPABILITY));

            var failure = RootStatusCapabilityFailureAssertions.fromOriginalHello(restored,
                    restored.requirePhysicalStatusOnly().source(), restoredHello, packet.clone());
            assertEquals("native DLL does not advertise required capability " + PhysicalStatusIdentity.CAPABILITY,
                    failure.getMessage());
            PublicStatusCapabilityRpcAssertions.assertOriginal(consumer, failure);
        }
    }

    /** Protocol mapping only: this does not assert that the stock Status handler can emit false ACK. */
    @Test void originalFramingFalseAckKeepsActualCustodyArchiveAndAllPublicErrors()throws Exception {
        var original=RootStatusCapabilityFailureAssertions.fromOriginalRejectedStatus(temporary);
        assertEquals(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,original.kind());
        assertTrue(original.originalCandidate().isPresent());
        assertTrue(original.getMessage().startsWith("native gameplay step failed: "));
        for(var consumer:PublicPlanningRpcAssertions.Consumer.values())
            PublicSourceFailureRpcAssertions.assertOriginal(consumer,PublicStatusCapabilityRpcAssertions.TOOL,"{}",original,
                    java.util.Optional.empty());
    }
    private static byte[] hello() throws java.io.IOException {
        var row = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", 42)
                .put("connection_generation", GENERATION).put("bridge_version", "controlled-data")
                .put("expected_ck3_sha256", "0".repeat(64)).put("game_adapter_id", "controlled-data")
                .put("game_adapter_status", "ready").put("ck3_build_match", true);
        row.putArray("capabilities").add("game.state.snapshot");
        return NativeWire.packet(StrictJson.canonical(row));
    }
    private static ExactRef data(String role) {
        return reference(role + ".data", role.getBytes(StandardCharsets.UTF_8));
    }
    private static ExactRef reference(String role, byte[] original) {
        return new ExactRef("D:/controlled-public-status-data/" + role, original.length, ActionCodec.sha256(original));
    }
}
