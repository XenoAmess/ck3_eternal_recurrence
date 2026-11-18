package org.xar.ck3.markets.oracle;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

final class WindowPriceOracleTest {
    @Test void fewerThanSevenCompletedDaysDoNotAuthorizeFutures() {
        WindowPriceOracle oracle = oracle();
        for (int day = 0; day < 6; day++) day(oracle, day, 1_000);
        PriceQuote pending = oracle.quote("coin", 6);
        assertEquals(Quality.PENDING, pending.quality());
        assertEquals(0, pending.maxLeverage());
        assertFalse(pending.terminationEligible());
    }

    @Test void incompleteDayAndSingleLargestAndSmallestDaysCannotSetMark() {
        WindowPriceOracle oracle = oracle();
        long[] prices = {100, 1_000, 2_000, 3_000, 4_000, 5_000, 1_000_000};
        for (int day = 0; day < prices.length; day++) day(oracle, day, prices[day]);
        day(oracle, 7, 8_000_000);
        PriceQuote quote = oracle.quote("coin", 7);
        assertEquals(3_000, quote.indexCents());
        assertEquals(quote.indexCents(), quote.markCents());
        assertEquals(3, quote.maxLeverage());
        assertEquals(Quality.SINGLE_VENUE, quote.quality());
        assertEquals(6, quote.lastObservationDay());
        assertEquals(WindowPriceOracle.SOURCE_ID, quote.sourceId());
    }

    @Test void economicBeneficiaryReuseIsRejectedAcrossDifferentTrades() {
        WindowPriceOracle oracle = oracle();
        assertTrue(oracle.record(trade(0, "b", "s", 1_000, 10, false)));
        assertFalse(oracle.record(trade(0, "b", "other", 9_000, 10, false)));
        assertFalse(oracle.record(trade(0, "other", "s", 9_000, 10, false)));
        assertFalse(oracle.record(trade(0, "same", "same", 9_000, 10, false)));
        assertFalse(oracle.record(trade(0, "controller", "new", 9_000, 10, true)));
    }

    @Test void tinyAndUnfundedSizeCannotCreateQualifiedDay() {
        WindowPriceOracle oracle = oracle();
        for (int day = 0; day < 14; day++) {
            for (int i = 0; i < 8; i++) assertFalse(oracle.record(trade(day, "b" + i, "s" + i, 1, 1, false)));
        }
        assertEquals(Quality.PENDING, oracle.quote("coin", 14).quality());
        assertThrows(IllegalArgumentException.class, () -> trade(14, "b", "s", 100, 0, false));
    }

    @Test void eightSampleBoundRejectsLateSamplesWithoutChangingPrice() {
        WindowPriceOracle oracle = oracle();
        for (int day = 0; day < 7; day++) {
            for (int i = 0; i < 8; i++) assertTrue(oracle.record(trade(day, "b" + i, "s" + i, 1_000, 10, false)));
            assertFalse(oracle.record(trade(day, "lateB", "lateS", 900_000, 100, false)));
        }
        assertEquals(1_000, oracle.quote("coin", 7).indexCents());
    }

    @Test void matureThirtyDayCoinCanReachTenTimesButNeverTwenty() {
        WindowPriceOracle oracle = oracle();
        for (int day = 16; day < 30; day++) day(oracle, day, 2_500);
        PriceQuote quote = oracle.quote("coin", 30);
        assertEquals(10, quote.maxLeverage());
        assertEquals(Quality.SINGLE_VENUE, quote.quality());
    }

    @Test void fullWindowBeforeThirtyDaysRemainsThreeTimes() {
        WindowPriceOracle oracle = oracle();
        for (int day = 0; day < 14; day++) day(oracle, day, 1_000);
        assertEquals(3, oracle.quote("coin", 14).maxLeverage());
    }

    @Test void staleReferencePreservesHistoricalPriceWithoutAuthorizingZeroSettlement() {
        WindowPriceOracle oracle = oracle();
        for (int day = 0; day < 10; day++) day(oracle, day, 1_234);
        assertEquals(1_234, oracle.quote("coin", 10).markCents());
        PriceQuote stale = oracle.quote("coin", 12);
        assertEquals(Quality.PENDING, stale.quality());
        assertEquals(1_234, stale.markCents());
        assertEquals(0, stale.maxLeverage());
        assertFalse(stale.terminationEligible());
        assertEquals("stale_reference", stale.reason());
    }

    @Test void realIndependentMultiDayRepricingMovesTheReference() {
        WindowPriceOracle oracle = oracle();
        for (int day = 0; day < 14; day++) day(oracle, day, 1_000);
        assertEquals(1_000, oracle.quote("coin", 14).indexCents());
        for (int day = 14; day < 28; day++) day(oracle, day, 2_000);
        assertEquals(2_000, oracle.quote("coin", 28).indexCents());
    }

    @Test void boundedLotsWeightAndIntegerDivisionMatchNativeSpecification() {
        WindowPriceOracle oracle = oracle();
        for (int day = 0; day < 7; day++) {
            assertTrue(oracle.record(trade(day, "a", "b", 100, 10_000, false)));
            assertTrue(oracle.record(trade(day, "c", "d", 200, 1, false)));
            assertTrue(oracle.record(trade(day, "e", "f", 200, 1, false)));
            assertTrue(oracle.record(trade(day, "g", "h", 200, 1, false)));
        }
        assertEquals(100, oracle.quote("coin", 7).indexCents());
    }

    @Test void capacityAndClockDoNotSilentlyEvictOrReplay() {
        WindowPriceOracle oracle = new WindowPriceOracle(1);
        oracle.register("coin", 0);
        assertThrows(IllegalStateException.class, () -> oracle.register("second", 0));
        assertThrows(IllegalArgumentException.class, () -> oracle.register("coin", 1));
        oracle.quote("coin", 5);
        assertThrows(IllegalArgumentException.class, () -> oracle.quote("coin", 4));
        assertThrows(IllegalArgumentException.class, () -> oracle.record(trade(4, "b", "s", 100, 1, false)));
    }

    private static WindowPriceOracle oracle() {
        WindowPriceOracle oracle = new WindowPriceOracle(4_096);
        oracle.register("coin", 0);
        return oracle;
    }

    private static void day(WindowPriceOracle oracle, int day, long price) {
        for (int i = 0; i < 4; i++) assertTrue(oracle.record(trade(day, "b" + i, "s" + i, price, 10, false)));
    }

    private static QualifiedTrade trade(long day, String buyer, String seller, long price, long lots, boolean related) {
        return new QualifiedTrade("coin", buyer, seller, day, price, lots, related);
    }
}
