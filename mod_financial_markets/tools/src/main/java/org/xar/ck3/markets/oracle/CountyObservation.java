package org.xar.ck3.markets.oracle;

import java.util.Objects;

/** A current real county observation from the fixed, disclosed model basket. */
public record CountyObservation(String countyId, int prosperity, int control, boolean holderAtWar) {
    public CountyObservation {
        Objects.requireNonNull(countyId, "countyId");
        if (countyId.isBlank() || prosperity < 0 || prosperity > 100 || control < 0 || control > 100) {
            throw new IllegalArgumentException("invalid normalized county observation");
        }
    }
}
