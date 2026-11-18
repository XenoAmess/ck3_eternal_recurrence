package org.xar.ck3.markets.core;

/** Cumulative per-original-order fees: 0.3%, rounded up to cents, minimum one cent if filled. */
public final class TradingFees {
    private TradingFees() {
    }

    public static long cumulativeCents(long filledGrossCents) {
        if (filledGrossCents < 0) {
            throw new MarketException(MarketException.Code.INVALID_ARGUMENT, "gross cannot be negative");
        }
        if (filledGrossCents == 0) {
            return 0;
        }
        // Divide first without losing the remainder, avoiding 3 * gross overflow.
        long whole = Math.multiplyExact(filledGrossCents / 1_000, 3);
        long remainder = ((filledGrossCents % 1_000) * 3 + 999) / 1_000;
        return Math.max(1, Math.addExact(whole, remainder));
    }
}
