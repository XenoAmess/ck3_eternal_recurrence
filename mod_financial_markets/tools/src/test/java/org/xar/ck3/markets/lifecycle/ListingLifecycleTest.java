package org.xar.ck3.markets.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.lifecycle.ListingLifecycle.DerivativeDisposition;
import org.xar.ck3.markets.lifecycle.ListingLifecycle.State;

final class ListingLifecycleTest {
    @Test void thirtyDayExitKeepsSpotBothDirectionsWhileStoppingNewLeverage() {
        var listing = new ListingLifecycle("coin:1", "venue:1"); listing.announce(100);
        assertTrue(listing.snapshot().spotTrading()); assertFalse(listing.snapshot().newDerivativeRisk());
        for (long day = 101; day <= 120; day++) listing.advance(day, OptionalLong.of(1_400));
        assertEquals(DerivativeDisposition.REDUCE_ONLY, listing.snapshot().derivatives());
        listing.advance(121, OptionalLong.empty());
        assertEquals(1_400, listing.snapshot().settlementPriceCents().orElseThrow());
        assertEquals(DerivativeDisposition.SETTLEMENT_DUE, listing.snapshot().derivatives());
        listing.confirmDerivativeTermination(); listing.advance(129, OptionalLong.empty());
        assertTrue(listing.snapshot().spotTrading()); listing.advance(130, OptionalLong.empty());
        assertFalse(listing.snapshot().spotTrading()); assertTrue(listing.snapshot().otcTransfer());
    }
    @Test void missingOracleNeverInventsZeroOrWritesOffCollateral() {
        var listing = new ListingLifecycle("coin:1", "venue:1"); listing.announce(0);
        listing.advance(21, OptionalLong.empty()); listing.advance(30, OptionalLong.empty());
        assertEquals(State.DELISTED, listing.snapshot().state());
        assertEquals(DerivativeDisposition.PRICE_PENDING, listing.snapshot().derivatives());
        assertTrue(listing.snapshot().settlementPriceCents().isEmpty());
        assertThrows(IllegalStateException.class, listing::confirmDerivativeTermination);
        assertThrows(IllegalStateException.class, () -> listing.resolvePricePending(0));
        listing.resolvePricePending(44); listing.confirmDerivativeTermination();
        assertEquals(DerivativeDisposition.TERMINATED, listing.snapshot().derivatives());
    }
    @Test void duplicateDayDoesNotAddSecondPriceSample() {
        var listing = new ListingLifecycle("coin", "venue"); listing.announce(0);
        listing.advance(15, OptionalLong.of(100)); listing.advance(15, OptionalLong.of(100));
        listing.advance(16, OptionalLong.of(100)); listing.advance(21, OptionalLong.empty());
        assertEquals(DerivativeDisposition.PRICE_PENDING, listing.snapshot().derivatives());
        assertThrows(IllegalArgumentException.class, () -> listing.advance(20, OptionalLong.empty()));
    }
    @Test void otherVenueContractsAndOrdersContinue() {
        var closing = new ListingLifecycle("same-coin", "closed"); var healthy = new ListingLifecycle("same-coin", "healthy");
        closing.announce(0); closing.advance(30, OptionalLong.empty());
        assertTrue(healthy.snapshot().spotTrading()); assertTrue(healthy.snapshot().newDerivativeRisk());
        assertEquals(DerivativeDisposition.LIVE, healthy.snapshot().derivatives());
    }
    @Test void oneResidualRightForbidsArchiveAndCoinIdSurvivesRelisting() {
        var listing = new ListingLifecycle("permanent:1", "venue:1"); listing.recordDefault(); listing.announce(0);
        listing.advance(15, OptionalLong.of(100)); listing.advance(16, OptionalLong.of(110)); listing.advance(17, OptionalLong.of(120));
        listing.advance(21, OptionalLong.empty()); listing.confirmDerivativeTermination(); listing.advance(30, OptionalLong.empty());
        assertThrows(IllegalStateException.class, () -> listing.archive(new ListingLifecycle.Rights(0, 0, 0, 0, 0, 1, 0)));
        listing.requestRelist(40, true, true, true); listing.advance(69, OptionalLong.empty());
        assertFalse(listing.snapshot().spotTrading()); listing.advance(70, OptionalLong.empty());
        assertTrue(listing.snapshot().spotTrading()); assertEquals("permanent:1", listing.snapshot().permanentCoinId());
        assertEquals(1, listing.snapshot().defaultHistoryCount());
    }
    @Test void archiveRequiresEveryCounterZero() {
        var listing = new ListingLifecycle("coin", "venue"); listing.announce(0); listing.advance(30, OptionalLong.empty());
        assertThrows(IllegalStateException.class, () -> listing.archive(new ListingLifecycle.Rights(1, 0, 0, 0, 0, 0, 0)));
        listing.archive(new ListingLifecycle.Rights(0, 0, 0, 0, 0, 0, 0));
        assertFalse(listing.snapshot().otcTransfer()); assertEquals(State.ARCHIVED, listing.snapshot().state());
    }
    @Test void emergencyReviewHasThreeThenSevenDayDeadlines() {
        var listing = new ListingLifecycle("coin", "venue"); listing.suspend(10);
        assertEquals(13, listing.snapshot().nextReviewDay()); assertFalse(listing.snapshot().spotTrading());
        assertThrows(IllegalStateException.class, () -> listing.reviewSuspension(12, true));
        listing.reviewSuspension(13, false); assertEquals(20, listing.snapshot().nextReviewDay());
        listing.reviewSuspension(20, true); assertTrue(listing.snapshot().spotTrading());
    }
}
