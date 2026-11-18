package org.xar.ck3.markets.pool;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

final class PoolQuoteTest {
    @Test void initialTwoGoldPoolQuotesThreeCentPrincipalAndOneCentEachFee() {
        var buy = PoolQuote.buy(200, 10_000);
        assertEquals(3, buy.principalCents());
        assertEquals(1, buy.feePerSideCents());
        assertEquals(-4, buy.traderCashDeltaCents());
        assertEquals(2, buy.poolCashDeltaCents());
        assertEquals(2, buy.feeTreasuryDeltaCents());
        assertConserved(buy);
    }
    @Test void roundTripAccountsForBothPoolAndTraderFeesWithoutCreatingCash() {
        var buy = PoolQuote.buy(200, 10_000);
        var sell = PoolQuote.sell(200 + buy.poolCashDeltaCents(), 10_000 + buy.poolCoinDelta());
        assertEquals(1, sell.traderCashDeltaCents());
        assertEquals(-3, sell.poolCashDeltaCents());
        assertEquals(-3, buy.traderCashDeltaCents() + sell.traderCashDeltaCents());
        assertEquals(-1, buy.poolCashDeltaCents() + sell.poolCashDeltaCents());
        assertEquals(4, buy.feeTreasuryDeltaCents() + sell.feeTreasuryDeltaCents());
        assertConserved(sell);
    }
    @Test void unsellableDustAndExhaustedInventoryAreRefused() {
        assertThrows(IllegalArgumentException.class, () -> PoolQuote.sell(1, 10_000));
        assertThrows(IllegalArgumentException.class, () -> PoolQuote.sell(200, 0));
        assertThrows(IllegalArgumentException.class, () -> PoolQuote.buy(200, 100));
        assertThrows(IllegalArgumentException.class, () -> PoolQuote.buy(0, 10_000));
        assertThrows(IllegalArgumentException.class, () -> PoolQuote.buy(200, -1));
    }
    @Test void referenceArithmeticAvoidsIntermediateOverflowAndRejectsUnrepresentableTotal() {
        assertConserved(PoolQuote.buy(Long.MAX_VALUE / 2, 10_000));
        assertThrows(ArithmeticException.class, () -> PoolQuote.buy(Long.MAX_VALUE, 101));
    }
    @Test void wideInventoryAndCapitalVectorsKeepRealCashAndCoinDeltasBalanced() {
        for (long cash : new long[]{200, 2_000, 100_000, 1_000_000_000}) {
            for (long inventory : new long[]{200, 1_000, 10_000}) {
                var buy = PoolQuote.buy(cash, inventory);
                assertConserved(buy);
                assertTrue(buy.poolCashDeltaCents() >= 0);
                var sell = PoolQuote.sell(cash + buy.poolCashDeltaCents(), inventory - 100);
                assertConserved(sell);
                assertTrue(-sell.poolCashDeltaCents() <= cash + buy.poolCashDeltaCents());
            }
        }
    }
    private static void assertConserved(PoolQuote quote) {
        assertEquals(0, quote.traderCashDeltaCents() + quote.poolCashDeltaCents() + quote.feeTreasuryDeltaCents());
        assertEquals(0, quote.traderCoinDelta() + quote.poolCoinDelta());
    }
}
