package org.xar.ck3.markets.oracle;

/** A settlement reference is not an offer to buy assets or finance a liquidation. */
@FunctionalInterface
public interface PriceOracle {
    PriceQuote quote(String assetId, long day);
}
