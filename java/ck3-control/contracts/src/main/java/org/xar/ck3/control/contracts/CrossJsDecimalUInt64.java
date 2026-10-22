package org.xar.ck3.control.contracts;

import java.math.BigInteger;

/** Separate cross-JavaScript wire domain; not an alias accepted by the map producer. */
public record CrossJsDecimalUInt64(String decimal) {
    public CrossJsDecimalUInt64 {
        StrictJson.require(decimal != null && decimal.matches("0|[1-9][0-9]*") && decimal.length() <= 20,
                "canonical decimal uint64 string required");
        StrictJson.require(new BigInteger(decimal).compareTo(StrictJson.UINT64_MAX) <= 0, "decimal uint64 range");
    }
}
