package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.IntNode;
import java.math.BigInteger;

/** Complete native FactionID: public signed int32, with only all-ones reserved for absence.
 * Identity representation grants no faction membership, action or storage-instance authority. */
public record NativeFactionId(int value) {
    private static final BigInteger MINIMUM = BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger MAXIMUM = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger RAW_SENTINEL = new BigInteger("4294967295");

    public NativeFactionId {
        StrictJson.require(value != -1, "native faction identity -1 is the absent-faction sentinel");
    }
    public static NativeFactionId of(long value) { return of(BigInteger.valueOf(value)); }
    public static NativeFactionId of(BigInteger value) {
        StrictJson.require(value != null && value.compareTo(MINIMUM) >= 0 && value.compareTo(MAXIMUM) <= 0,
                "native faction identity requires an exact signed int32");
        return new NativeFactionId(value.intValueExact());
    }
    public static NativeFactionId fromJson(JsonNode value) {
        return of(StrictJson.integer(value, MINIMUM, MAXIMUM));
    }
    /** Private Native fields have one unsigned representation; signed aliases are rejected. */
    public static NativeFactionId fromRawUInt32(BigInteger value) {
        StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(RAW_SENTINEL) < 0,
                "raw native faction identity requires uint32 except the all-ones sentinel");
        return new NativeFactionId(value.intValue());
    }
    public BigInteger asRawUInt32() { return BigInteger.valueOf(Integer.toUnsignedLong(value)); }
    public BigInteger asBigInteger() { return BigInteger.valueOf(value); }
    public IntNode toJson() { return IntNode.valueOf(value); }
}
