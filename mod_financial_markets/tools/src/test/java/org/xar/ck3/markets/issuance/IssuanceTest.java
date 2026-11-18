package org.xar.ck3.markets.issuance;

import static org.junit.jupiter.api.Assertions.*;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.listing.ListingFunding.Tier;

final class IssuanceTest {
    @Test void paidMicroSubscriptionsAllocateRealCoinsAndExactCents() {
        Offering offer = new Offering(Tier.MICRO, 20, 2_000, 100);
        offer.subscribe("unlanded", 1_000); offer.subscribe("baron", 1_000);
        var closing = offer.close(0);
        assertEquals(1_400, closing.freeProjectCashCents());
        assertEquals(100, closing.allotments().values().stream().mapToLong(Offering.Subscription::lots).sum());
        assertEquals(2_000, closing.freeProjectCashCents() + closing.allocation().requiredCashCents());
        assertEquals(0, offer.escrowCents());
        assertThrows(IllegalStateException.class, () -> offer.subscribe("late", 20));
        assertThrows(IllegalStateException.class, offer::abort);
    }
    @Test void standardInitialCashIsNotLostAndFeesAreNotDoubleCharged() {
        Offering offer = new Offering(Tier.STANDARD, 200, 20_000, 100);
        offer.subscribe("real-buyer", 20_000);
        var closing = offer.close(10_000);
        assertEquals(24_500, closing.freeProjectCashCents());
        assertEquals(30_000, closing.freeProjectCashCents() + closing.allocation().requiredCashCents());
    }
    @Test void failureRefundsEachOriginalBuyerExactlyOnce() {
        Offering offer = new Offering(Tier.MICRO, 20, 2_000, 100);
        offer.subscribe("a", 400); offer.subscribe("a", 200); offer.subscribe("b", 200);
        assertThrows(IllegalStateException.class, () -> offer.close(100_000));
        offer.abort(); assertEquals(800, offer.escrowCents());
        assertEquals(600, offer.claimRefund("a")); assertEquals(0, offer.claimRefund("a"));
        assertEquals(200, offer.claimRefund("b")); assertEquals(0, offer.escrowCents());
        assertEquals(Offering.State.REFUNDED, offer.state());
    }
    @Test void badSubscriptionsCannotPartlyMutateEscrow() {
        Offering offer = new Offering(Tier.MICRO, 20, 0, 100);
        assertThrows(IllegalArgumentException.class, () -> offer.subscribe("buyer", 21));
        assertThrows(IllegalArgumentException.class, () -> offer.subscribe("buyer", 2_020));
        assertEquals(0, offer.escrowCents()); assertEquals(0, offer.soldLots());
    }
    @Test void supplyCannotBurnHoldersOrUnlockTwice() {
        SupplyCharter supply = new SupplyCharter(125, 250, 25, 365, true);
        supply.allot(100); assertThrows(IllegalArgumentException.class, () -> supply.burnTreasury(1));
        assertEquals(0, supply.unlock(364)); assertEquals(25, supply.unlock(365)); assertEquals(0, supply.unlock(366));
        supply.mint(10, false); supply.burnTreasury(5);
        var snapshot = supply.snapshot();
        assertEquals(130, snapshot.totalLots()); assertEquals(10, snapshot.undisclosedMintLots());
        assertEquals(snapshot.totalLots(), snapshot.circulationLots() + snapshot.treasuryLots() + snapshot.founderLockedLots() + snapshot.founderReleasedLots());
    }
    @Test void fixedSupplyAndCapAreReal() {
        var fixed = new SupplyCharter(100, 100, 10, 30, false);
        assertThrows(IllegalStateException.class, () -> fixed.mint(1, true));
        var capped = new SupplyCharter(100, 120, 0, 0, true);
        assertThrows(IllegalArgumentException.class, () -> capped.mint(21, true));
        assertEquals(100, capped.snapshot().totalLots());
    }
    @Test void successionPreservesDebtDefaultsAndCooldown() {
        var identity = new IssuerIdentity("dynasty:42:coin:7", IssuerIdentity.Kind.DYNASTY, "dynasty:42", "old", "old", 730, 500, Set.of("default-1"));
        var successor = identity.succession("new");
        assertEquals(identity.permanentId(), successor.permanentId()); assertEquals(500, successor.unpaidDebtCents());
        assertEquals(identity.disclosedDefaults(), successor.disclosedDefaults()); assertFalse(successor.mayIssue(729, 0, 0));
        assertTrue(successor.mayAct("new", Set.of("dynasty:42"))); assertFalse(successor.mayAct("new", Set.of("other")));
    }
    @Test void personalConcurrentAndPendingLimitsHaveNoRankGate() {
        var identity = new IssuerIdentity("p:1", IssuerIdentity.Kind.PERSONAL, "unlanded", "unlanded", "unlanded", 0, 0, Set.of());
        assertTrue(identity.mayIssue(0, 0, 0)); assertFalse(identity.mayIssue(0, 1, 0)); assertFalse(identity.mayIssue(0, 0, 1));
    }
    @Test void maintenanceAppliesExistingCreditOnlyOnceBeforeEscrow() {
        var charge = Maintenance.charge(100, 40, 600);
        assertEquals(40, charge.creditUsedCents()); assertEquals(60, charge.prepaidUsedCents());
        assertEquals(0, charge.arrearsAddedCents()); assertEquals(540, charge.prepaidRemainingCents());
        assertEquals(0, charge.creditRemainingCents());
        var shortfall = Maintenance.charge(100, 200, 50);
        assertEquals(100, shortfall.creditRemainingCents()); assertEquals(50, shortfall.prepaidRemainingCents());
        assertEquals(30, Maintenance.charge(100, 20, 50).arrearsAddedCents());
    }
}
