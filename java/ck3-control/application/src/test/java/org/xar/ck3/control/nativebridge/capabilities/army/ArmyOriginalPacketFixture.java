package org.xar.ck3.control.nativebridge.capabilities.army;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;

/** Test DATA framing only. This helper neither calls nor replaces any runtime transport/serializer,
 * does not mint an ACK source or private Known, and leaves all original JSON bytes unchanged. */
final class ArmyOriginalPacketFixture {
    private ArmyOriginalPacketFixture() { }
    static byte[] packet(RawJson originalFrame) {
        byte[] json=Objects.requireNonNull(originalFrame,"original test frame DATA required").bytes();
        return ByteBuffer.allocate(Math.addExact(Integer.BYTES,json.length)).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(json.length).put(json).array();
    }
}
