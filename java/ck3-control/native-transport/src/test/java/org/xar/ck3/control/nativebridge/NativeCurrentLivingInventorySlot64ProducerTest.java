package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.NativeCurrentLivingInventory26785313ProducerTest.result;
import static org.xar.ck3.control.nativebridge.NativeCurrentLivingInventory26785313ProducerTest.responseIdentity;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/** New original C++ serializer software responses. No live inventory or original8 business claim. */
final class NativeCurrentLivingInventorySlot64ProducerTest {
    private static byte[] original(String name, int bytes, String sha256) throws Exception {
        try (var in = NativeCurrentLivingInventorySlot64ProducerTest.class.getResourceAsStream(
                "/current267-living-slot64-cpp-a1458/" + name)) {
            if (in == null) throw new IOException("Actual slot64 Cpp original absent: " + name);
            var raw = in.readAllBytes();
            assertEquals(bytes, raw.length);
            assertEquals(sha256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            return raw;
        }
    }

    private static void actualCompleteResponse(int count, int length, String bodyHash, String packetHash) throws Exception {
        var body = original("native-slot" + count + ".response.body.json", length, bodyHash);
        var packet = original("native-slot" + count + ".response.packet.bin", length + 4, packetHash);
        assertEquals(length, ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        assertArrayEquals(body, Arrays.copyOfRange(packet, 4, packet.length));
        assertArrayEquals(packet, NativeWire.packet(body));
        var frame = CurrentLivingInventoryQueryResult.decode(result(body));
        assertEquals(frame, CurrentLivingInventoryQueryResult.decode(frame.encode()));
        responseIdentity(body, frame.encode(), frame.successful());
        assertEquals(CurrentLivingInventoryQueryResult.Status.AVAILABLE, frame.status());
        assertFalse(frame.effectAttempted()); assertFalse(frame.nativeReturned());
        assertEquals(BigInteger.ZERO, frame.claimSequence());
        var source = frame.source().orElseThrow();
        assertEquals(36423L, source.actorFullId()); assertTrue(source.completeInventory()); assertTrue(source.sampledTwice());
        assertTrue(source.artifacts().isEmpty()); assertEquals(6, source.fixedReferences().size());
        assertEquals(count, source.slots().size()); assertEquals(Optional.of(count - 1), source.weaponSlot());
        for (int i = 0; i < count; i++) {
            assertEquals(i == count - 1 ? "weapon" : "fixture_slot_" + String.format(java.util.Locale.ROOT, "%02d", i),
                    source.slots().get(i).key());
            assertTrue(source.slots().get(i).artifactFullId().isEmpty());
        }
        assertTrue(body.length < NativeWire.MAXIMUM_FRAME_BYTES);
    }

    @Test void actualCpp36CompleteSlotsAndWeapon35RoundTrip() throws Exception {
        actualCompleteResponse(36, 3528,
                "6a223c575f7f897891dcc80ee4e6ddae7867df5a4e41512910a45653ef9dc5b2",
                "0234e4271f0db150ff435bdc5834945931b4b555b1f6013e07be34f2fc14e032");
    }

    @Test void actualCpp64CompleteSlotsAndWeapon63RoundTrip() throws Exception {
        actualCompleteResponse(64, 4928,
                "ee1a284a6e1008271532d81abe9d015ba59ed676fe4b9ffba39cce3d974eb6b7",
                "f2682a54d5dad96294373c87320f24509ae9f29ede8fa3e302bae1785ac01d71");
    }
}
