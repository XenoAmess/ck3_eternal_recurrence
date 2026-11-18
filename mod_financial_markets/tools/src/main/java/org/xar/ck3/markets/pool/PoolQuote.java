package org.xar.ck3.markets.pool;

import java.math.BigInteger;
import org.xar.ck3.markets.core.TradingFees;

/** Independent exact rational oracle for the temporary A0 funded pool, not its CK3 implementation. */
public record PoolQuote(long traderCashDeltaCents, long poolCashDeltaCents,
                        long feeTreasuryDeltaCents, long traderCoinDelta,
                        long poolCoinDelta, long principalCents, long feePerSideCents) {
    private static final long LOT = 100;

    public static PoolQuote buy(long poolGoldCents, long inventoryCoins) {
        inputs(poolGoldCents, inventoryCoins);
        if (inventoryCoins <= LOT) throw new IllegalArgumentException("insufficient pool inventory");
        long principal = divide(poolGoldCents, LOT, inventoryCoins - LOT, true);
        long fee = TradingFees.cumulativeCents(principal);
        return new PoolQuote(-Math.addExact(principal, fee), principal - fee,
                Math.multiplyExact(2, fee), LOT, -LOT, principal, fee);
    }

    public static PoolQuote sell(long poolGoldCents, long inventoryCoins) {
        inputs(poolGoldCents, inventoryCoins);
        long principal = divide(poolGoldCents, LOT, Math.addExact(inventoryCoins, LOT), false);
        long fee = TradingFees.cumulativeCents(principal);
        long proceeds = principal - fee;
        if (proceeds <= 0) throw new IllegalArgumentException("sell below minimum executable proceeds");
        long cost = Math.addExact(principal, fee);
        if (cost > poolGoldCents) throw new IllegalArgumentException("pool cannot fund proceeds and its fee");
        return new PoolQuote(proceeds, -cost, Math.multiplyExact(2, fee), -LOT, LOT, principal, fee);
    }

    private static void inputs(long cash, long inventory) {
        if (cash <= 0 || inventory < 0) throw new IllegalArgumentException("positive real pool cash and nonnegative inventory required");
    }

    private static long divide(long left, long right, long denominator, boolean roundUp) {
        BigInteger[] result = BigInteger.valueOf(left).multiply(BigInteger.valueOf(right))
                .divideAndRemainder(BigInteger.valueOf(denominator));
        return (roundUp && result[1].signum() != 0 ? result[0].add(BigInteger.ONE) : result[0]).longValueExact();
    }
}
