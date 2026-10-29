package org.xar.ck3.control.contracts;

import java.math.BigInteger;
import java.util.Objects;

/** The public CUnit handle domain; private CArmy, Regiment and Province identities use different contracts. */
public record PublicCUnitId(BigInteger value) {
    public static final BigInteger MAXIMUM = BigInteger.valueOf(Integer.MAX_VALUE);
    public PublicCUnitId {
        Objects.requireNonNull(value);
        StrictJson.require(value.signum() >= 0 && value.compareTo(MAXIMUM) <= 0,
                "public CUnit identity must be an integer in 0..2147483647");
    }
}
