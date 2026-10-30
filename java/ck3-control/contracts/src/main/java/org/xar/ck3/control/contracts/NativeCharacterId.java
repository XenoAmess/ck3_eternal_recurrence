package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.IntNode;
import java.math.BigInteger;

/** Native public character identity: signed int32, with only -1 reserved for absence.
 * This preserves the full native ID, including its sign; it grants no character-specific action eligibility.
 */
public record NativeCharacterId(int value) {
    private static final BigInteger MINIMUM=BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger MAXIMUM=BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger RAW_SENTINEL=new BigInteger("4294967295");

    public NativeCharacterId {
        StrictJson.require(value!=-1,"native character identity -1 is the absent-character sentinel");
    }

    /** Preserve the original signed value, refusing any narrowing or unsigned reinterpretation. */
    public static NativeCharacterId of(long value) {
        return of(BigInteger.valueOf(value));
    }

    public static NativeCharacterId of(BigInteger value) {
        StrictJson.require(value!=null&&value.compareTo(MINIMUM)>=0&&value.compareTo(MAXIMUM)<=0,
                "native character identity requires an exact signed int32");
        return new NativeCharacterId(value.intValueExact());
    }

    /** JSON strings, booleans, null and floating-point tokens never alias native integer identities. */
    public static NativeCharacterId fromJson(JsonNode value) {
        return of(StrictJson.integer(value,MINIMUM,MAXIMUM));
    }

    /** Explicit raw uint32 boundary used by private Native character fields.
     * Signed aliases and the all-ones absence sentinel are rejected before preserving the bits. */
    public static NativeCharacterId fromRawUInt32(BigInteger value) {
        StrictJson.require(value!=null&&value.signum()>=0&&value.compareTo(RAW_SENTINEL)<0,
                "raw native character identity requires uint32 except the all-ones sentinel");
        return new NativeCharacterId(value.intValue());
    }

    /** Convert this validated public signed identity to the private raw uint32 representation. */
    public BigInteger asRawUInt32() { return BigInteger.valueOf(Integer.toUnsignedLong(value)); }

    public IntNode toJson() { return IntNode.valueOf(value); }
    public BigInteger asBigInteger() { return BigInteger.valueOf(value); }
}
