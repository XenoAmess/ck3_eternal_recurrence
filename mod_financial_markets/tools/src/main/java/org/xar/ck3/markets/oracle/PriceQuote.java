package org.xar.ck3.markets.oracle;

import java.util.Objects;

/** day is publication day; lastObservationDay is the last complete qualified observation. */
public record PriceQuote(String assetId, long day, long indexCents, long markCents,
                         int maxLeverage, Quality quality, boolean terminationEligible,
                         String reason, long lastObservationDay, String sourceId) {
    public PriceQuote {
        Objects.requireNonNull(assetId, "assetId");
        Objects.requireNonNull(quality, "quality");
        Objects.requireNonNull(reason, "reason");
        Objects.requireNonNull(sourceId, "sourceId");
        if (assetId.isBlank() || sourceId.isBlank() || reason.isBlank() || day < 0 || indexCents < 0 || markCents < 0
                || maxLeverage < 0 || maxLeverage > 20 || lastObservationDay < -1 || lastObservationDay > day) {
            throw new IllegalArgumentException("invalid price quote");
        }
        if (quality == Quality.PENDING) {
            if (maxLeverage != 0 || terminationEligible) {
                throw new IllegalArgumentException("pending references cannot authorize risk or termination");
            }
        } else if (indexCents == 0 || markCents == 0 || maxLeverage == 0
                || lastObservationDay < 0) {
            throw new IllegalArgumentException("qualified reference requires positive price and observations");
        }
        if (quality != Quality.MULTI_VENUE && maxLeverage > 10) {
            throw new IllegalArgumentException("leverage above 10 requires actual independent venues");
        }
        if (quality == Quality.MODEL_INDEX && maxLeverage > 5) {
            throw new IllegalArgumentException("model indexes permit at most five times leverage");
        }
    }

    public boolean qualified() {
        return quality != Quality.PENDING;
    }
}
