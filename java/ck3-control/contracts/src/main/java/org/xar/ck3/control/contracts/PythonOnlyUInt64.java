package org.xar.ck3.control.contracts;

import java.math.BigInteger;

/** Opaque Python/Java integer JSON lane. Never transport through JavaScript Number. */
public record PythonOnlyUInt64(BigInteger value) {
    public PythonOnlyUInt64 {
        StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0,
                "exact uint64 integer required");
    }
}
