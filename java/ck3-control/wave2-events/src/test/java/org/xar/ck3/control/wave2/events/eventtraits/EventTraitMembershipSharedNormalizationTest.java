package org.xar.ck3.control.wave2.events.eventtraits;

import com.fasterxml.jackson.databind.node.BigIntegerNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePlayerEventTraitMembership;
import static org.junit.jupiter.api.Assertions.*;

/** The existing qualified consumers now share the same lower wire decoder and serializer. */
final class EventTraitMembershipSharedNormalizationTest {
    @Test void actualQualifiedCodecAndSharedReceiveContractRoundTripThroughTheIdenticalProducer() {
        var frame = new EventTraitMembership.Frame(BigInteger.valueOf(17), -1000, 73);
        var values = java.util.List.<EventTraitMembership.Observation>of(
                new EventTraitMembership.Available(frame, new EventTraitMembership.Traits(false, true)),
                new EventTraitMembership.Unavailable(frame, "not_available"));
        for (var value : values) {
            byte[] original = EventTraitMembershipCodec.encode(value);
            var raw = StrictJson.parse(original, EventTraitMembershipCodec.MAXIMUM_BYTES);
            var lower = NativePlayerEventTraitMembership.read(raw, BigInteger.valueOf(73), BigInteger.valueOf(17),
                    BigIntegerNode.valueOf(BigInteger.valueOf(-1000)));
            assertEquals(value, EventTraitMembershipCodec.decode(original, frame));
            assertEquals(raw, StrictJson.parse(NativePlayerEventTraitMembership.toJson(lower).toString().getBytes(StandardCharsets.UTF_8),
                    EventTraitMembershipCodec.MAXIMUM_BYTES));
        }
    }

    @Test void semanticAcceptanceDoesNotWidenTheExistingQualifiedBusinessRangesOrReasonBounds() {
        var frame = new NativePlayerEventTraitMembership.Frame(BigInteger.ONE.shiftLeft(100),
                BigInteger.ONE.shiftLeft(90), BigInteger.ONE.shiftLeft(80));
        var raw = NativePlayerEventTraitMembership.toJson(new NativePlayerEventTraitMembership.Unavailable(frame, "r".repeat(33000)));
        assertNotNull(NativePlayerEventTraitMembership.read(raw, frame.playedCharacterId(), frame.nativeRevision(),
                BigIntegerNode.valueOf(frame.dateRaw())));
        assertThrows(IllegalArgumentException.class, () -> new EventTraitMembership.Frame(frame.nativeRevision(), 1000, 73));
        var qualified = new EventTraitMembership.Frame(BigInteger.valueOf(17), 1000, 73);
        var longReason = NativePlayerEventTraitMembership.toJson(new NativePlayerEventTraitMembership.Unavailable(
                new NativePlayerEventTraitMembership.Frame(BigInteger.valueOf(17), BigInteger.valueOf(1000), BigInteger.valueOf(73)),
                "r".repeat(1025)));
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decodeLeaf(longReason, qualified));
        var wrongFrame = NativePlayerEventTraitMembership.toJson(new NativePlayerEventTraitMembership.Available(
                new NativePlayerEventTraitMembership.Frame(BigInteger.valueOf(18), BigInteger.valueOf(1000), BigInteger.valueOf(73)),
                new NativePlayerEventTraitMembership.Traits(false, false)));
        assertThrows(IllegalArgumentException.class, () -> EventTraitMembershipCodec.decodeLeaf(wrongFrame, qualified));
    }
}
