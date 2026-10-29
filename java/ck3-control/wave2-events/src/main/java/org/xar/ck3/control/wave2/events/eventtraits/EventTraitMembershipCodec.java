package org.xar.ck3.control.wave2.events.eventtraits;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativePlayerEventTraitMembership;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Available;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Frame;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Observation;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Traits;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership.Unavailable;

/** Existing bounded business projection delegates the one lower semantic wire producer/codec. */
public final class EventTraitMembershipCodec {
    public static final int MAXIMUM_BYTES = 8192;
    private EventTraitMembershipCodec() { }

    public static Observation decode(byte[] raw, Frame expected) {
        return decodeLeaf(StrictJson.parse(raw, MAXIMUM_BYTES), expected);
    }

    public static Observation decodeLeaf(JsonNode raw, Frame expected) {
        Objects.requireNonNull(expected, "expected");
        var original = NativePlayerEventTraitMembership.read(raw, BigInteger.valueOf(expected.playedCharacterId()),
                expected.nativeRevision(), com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(BigInteger.valueOf(expected.dateRaw())));
        var frame = new Frame(original.frame().nativeRevision(), original.frame().dateRaw().intValueExact(),
                original.frame().playedCharacterId().intValueExact());
        if (original instanceof NativePlayerEventTraitMembership.Available available)
            return new Available(frame, new Traits(available.traits().lifestylePoet(), available.traits().journaller()));
        var unavailable = (NativePlayerEventTraitMembership.Unavailable) original;
        // The historical qualified business type retains its narrower bounded reason contract.
        return new Unavailable(frame, unavailable.reason());
    }

    public static byte[] encode(Observation observed) {
        Objects.requireNonNull(observed, "observed");
        var frame = new NativePlayerEventTraitMembership.Frame(observed.frame().nativeRevision(),
                BigInteger.valueOf(observed.frame().dateRaw()), BigInteger.valueOf(observed.frame().playedCharacterId()));
        NativePlayerEventTraitMembership.Observation original;
        if (observed instanceof Available available)
            original = new NativePlayerEventTraitMembership.Available(frame,
                    new NativePlayerEventTraitMembership.Traits(available.traits().lifestylePoet(), available.traits().journaller()));
        else {
            var unavailable = (Unavailable) observed;
            original = new NativePlayerEventTraitMembership.Unavailable(frame, unavailable.reason());
        }
        return StrictJson.canonical(NativePlayerEventTraitMembership.toJson(original), MAXIMUM_BYTES);
    }
}
