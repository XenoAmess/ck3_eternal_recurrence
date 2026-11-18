package org.xar.ck3.markets.listing;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.listing.ListingFunding.Tier;

final class ListingFundingTest {
    @Test void standard200GoldPreservesFeeCapitalDistinctionAndInitialCash() {
        var funded = ListingFunding.fund(Tier.STANDARD, 10_000, 20_000);
        assertEquals(24_500, funded.freeProjectCashCents());
        var allocation = funded.allocation();
        assertEquals(1_900, allocation.earnedFeesCents());
        assertEquals(600, allocation.prepaidMaintenanceCents());
        assertEquals(1_000, allocation.performanceBondCents());
        assertEquals(2_000, allocation.makerCashCents());
        assertEquals(30_000, funded.freeProjectCashCents() + allocation.earnedFeesCents() + allocation.restrictedCashCents());
    }
    @Test void micro20GoldLeaves14GoldFree() {
        var funded = ListingFunding.fund(Tier.MICRO, 0, 2_000);
        assertEquals(1_400, funded.freeProjectCashCents());
        assertEquals(240, funded.allocation().earnedFeesCents());
        assertEquals(360, funded.allocation().restrictedCashCents());
        assertEquals(600, funded.allocation().requiredCashCents());
    }
    @Test void noProceedsRequireFivePointSixRealGoldForMicroListing() {
        assertEquals(560, ListingFunding.quote(Tier.MICRO, 0).requiredCashCents());
        assertThrows(IllegalArgumentException.class, () -> ListingFunding.fund(Tier.MICRO, 559, 0));
        assertEquals(0, ListingFunding.fund(Tier.MICRO, 560, 0).freeProjectCashCents());
    }
    @Test void admissionAndRoundingRejectFreeOrUnboundedMicroOffers() {
        assertThrows(IllegalArgumentException.class, () -> ListingFunding.quote(Tier.MICRO, 5_001));
        assertThrows(IllegalArgumentException.class, () -> ListingFunding.quote(Tier.STANDARD, -1));
        assertThrows(IllegalArgumentException.class, () -> ListingFunding.fund(Tier.STANDARD, -1, 0));
        assertThrows(ArithmeticException.class, () -> ListingFunding.fund(Tier.STANDARD, Long.MAX_VALUE, 1));
        assertEquals(1_001, ListingFunding.quote(Tier.STANDARD, 1).listingFeeCents());
    }
}
