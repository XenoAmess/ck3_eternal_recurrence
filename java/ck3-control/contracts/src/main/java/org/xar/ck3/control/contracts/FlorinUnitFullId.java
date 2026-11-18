package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;

/** Florin observed CUnit full identity, distinct from legacy public ArmyTypes.UnitId.
 * Validation preserves signed generation bits and grants no cash scope or army action eligibility.
 */
public record FlorinUnitFullId(int value) {
    private static final BigInteger MINIMUM = BigInteger.valueOf(Integer.MIN_VALUE);
    private static final BigInteger MAXIMUM = BigInteger.valueOf(Integer.MAX_VALUE);

    public FlorinUnitFullId {
        StrictJson.require(value != -1, "Florin CUnit -1 is the absent-unit sentinel");
    }

    public static FlorinUnitFullId fromJson(JsonNode value) {
        return new FlorinUnitFullId(StrictJson.integer(value, MINIMUM, MAXIMUM).intValueExact());
    }

    public BigInteger asBigInteger() { return BigInteger.valueOf(value); }
}
