package org.xar.ck3.markets.issuance;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.core.AccountId;
import org.xar.ck3.markets.core.BeneficiaryId;
import org.xar.ck3.markets.core.CoinId;
import org.xar.ck3.markets.core.FinancialMarket;
import org.xar.ck3.markets.core.LedgerBatch;
import org.xar.ck3.markets.core.MarketException;
import org.xar.ck3.markets.listing.ListingFunding.Tier;

final class OfferingWalletTest {
    private static final AccountId PROJECT = new AccountId("project");
    private static final AccountId BUYER = new AccountId("buyer");
    private static final CoinId COIN = new CoinId("coin");
    private static FinancialMarket ledger(long projectCash, long buyerCash, long supply) {
        var market = new FinancialMarket();
        market.createAccount(PROJECT, new BeneficiaryId("issuer-beneficiary"), projectCash);
        market.createAccount(BUYER, new BeneficiaryId("buyer-beneficiary"), buyerCash);
        market.issueCoin(COIN, PROJECT, supply, 30_000, 0);
        return market;
    }
    private static OfferingWallet micro(FinancialMarket market) {
        return new OfferingWallet(market, "micro1", PROJECT, COIN, Tier.MICRO, 20, 2_000, 100);
    }
    @Test void actualWalletSubscriptionAndClosingConserveGoldAndCoins() {
        var market = ledger(10_000, 2_000, 15_000); var offer = micro(market);
        assertEquals(100, market.feeTreasuryCents());
        assertEquals(9_900, market.account(PROJECT).availableCashCents());
        offer.subscribe("paid", BUYER, 2_000);
        assertEquals(0, market.account(BUYER).availableCashCents());
        assertEquals(2_000, market.account(offer.subscriptionEscrow()).availableCashCents());
        var closing = offer.close("close");
        assertEquals(11_400, closing.closing().freeProjectCashCents());
        assertEquals(11_400, market.account(PROJECT).availableCashCents());
        assertEquals(240, market.feeTreasuryCents());
        assertEquals(60, market.account(offer.maintenanceEscrow()).availableCashCents());
        assertEquals(100, market.account(offer.bondEscrow()).availableCashCents());
        assertEquals(200, market.account(offer.makerEscrow()).availableCashCents());
        assertEquals(0, market.account(offer.subscriptionEscrow()).availableCashCents());
        assertEquals(10_000, market.account(BUYER).balance(COIN).availableCoins());
        assertEquals(12_000, market.snapshot().totalCashCents());
        assertEquals(15_000, market.snapshot().totalCoins(COIN));
        assertFalse(offer.close("close").applied());
    }
    @Test void invalidOrUnfundedSubscriptionNeverDebitsAndRetryCanSucceed() {
        var market = ledger(100, 100, 15_000); var offer = micro(market);
        var before = market.snapshot();
        assertThrows(IllegalArgumentException.class, () -> offer.subscribe("bad-lot", BUYER, 21));
        assertEquals(before, market.snapshot());
        assertThrows(MarketException.class, () -> offer.subscribe("paid", BUYER, 200));
        assertEquals(before, market.snapshot()); assertEquals(0, offer.outstandingSubscriptionCents());
        market.transferCash(BUYER, PROJECT, 20);
        assertTrue(offer.subscribe("paid", BUYER, 80).applied());
        assertFalse(offer.subscribe("paid", BUYER, 80).applied());
        assertThrows(IllegalStateException.class, () -> offer.subscribe("paid", BUYER, 60));
        assertEquals(80, offer.outstandingSubscriptionCents());
    }
    @Test void failedRefundRetainsClaimAndSuccessfulRetryPaysExactlyOnce() {
        var market = ledger(1_000, 1_000, 15_000); var offer = micro(market);
        offer.subscribe("paid", BUYER, 1_000); offer.abort();
        // Simulate an independently detected custody deficit; the business claim must survive.
        market.applyBatch(new LedgerBatch("custody-deficit", List.of(), List.of(new LedgerBatch.Transfer(offer.subscriptionEscrow(), PROJECT, 1_000)), List.of()));
        var deficit = market.snapshot();
        assertThrows(MarketException.class, () -> offer.refund("refund", BUYER));
        assertEquals(deficit, market.snapshot()); assertEquals(1_000, offer.outstandingSubscriptionCents());
        market.transferCash(PROJECT, offer.subscriptionEscrow(), 1_000);
        assertEquals(1_000, offer.refund("refund", BUYER).cents());
        assertEquals(1_000, market.account(BUYER).availableCashCents());
        assertFalse(offer.refund("refund", BUYER).applied());
        assertEquals(0, offer.refund("different-refund", BUYER).cents());
        assertEquals(Offering.State.REFUNDED, offer.state());
    }
    @Test void coinDeliveryFailureRollsBackAllCashFeesAndClaims() {
        var market = ledger(100, 2_000, 100); var offer = micro(market);
        offer.subscribe("paid", BUYER, 2_000); var before = market.snapshot();
        assertThrows(MarketException.class, () -> offer.close("close"));
        assertEquals(before, market.snapshot());
        assertEquals(Offering.State.SUBSCRIBING, offer.state()); assertEquals(2_000, offer.outstandingSubscriptionCents());
        market.mint(COIN, PROJECT, 9_900, 0);
        assertTrue(offer.close("close").applied());
        assertEquals(10_000, market.account(BUYER).balance(COIN).availableCoins());
    }
    @Test void selfOwnedFundingDoesNotCountAsIndependentDemand() {
        var market = ledger(3_000, 0, 15_000); var offer = micro(market);
        offer.subscribe("self-funded", PROJECT, 2_000);
        var before = market.snapshot();
        assertThrows(IllegalStateException.class, () -> offer.close("close"));
        assertEquals(before, market.snapshot());
    }
    @Test void openingModelOnExistingCustodyRequiresRestoreRatherThanResettingClaims() {
        var market = ledger(1_000, 1_000, 15_000); var offer = micro(market);
        offer.subscribe("paid", BUYER, 400); var before = market.snapshot();
        assertThrows(IllegalStateException.class, () -> micro(market));
        assertEquals(before, market.snapshot()); assertEquals(400, offer.outstandingSubscriptionCents());
    }
}
