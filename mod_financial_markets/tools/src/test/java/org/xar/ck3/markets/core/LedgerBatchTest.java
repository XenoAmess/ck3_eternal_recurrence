package org.xar.ck3.markets.core;

import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class LedgerBatchTest {
    private static final AccountId A = new AccountId("a");
    private static final AccountId B = new AccountId("b");
    private static final AccountId E = new AccountId("xfm.escrow.test.margin");
    @Test void emptyEscrowAtomicMovesFeesAndReplayConserve() {
        FinancialMarket market = new FinancialMarket();
        market.createAccount(A, new BeneficiaryId("a"), 1_000);
        market.createAccount(B, new BeneficiaryId("b"), 0);
        LedgerBatch batch = new LedgerBatch("margin.1", List.of(new LedgerBatch.CreateEscrow(E, A)),
                List.of(new LedgerBatch.Transfer(A, E, 100), new LedgerBatch.Transfer(E, B, 30)),
                List.of(new LedgerBatch.Fee(E, 1)));
        assertTrue(market.applyBatch(batch).applied());
        assertEquals(900, market.account(A).availableCashCents());
        assertEquals(69, market.account(E).availableCashCents());
        assertEquals(30, market.account(B).availableCashCents());
        assertEquals(1_000, market.snapshot().totalCashCents());
        var before = market.snapshot();
        assertFalse(market.applyBatch(batch).applied());
        assertEquals(before, market.snapshot());
        assertThrows(MarketException.class, () -> market.transferCash(E, A, 1));
        assertThrows(MarketException.class, () -> market.createAccount(new AccountId("xfm.escrow.forged"), new BeneficiaryId("x"), 100));
    }
    @Test void failedLatePaymentRollsBackEscrowAndEarlierTransfer() {
        FinancialMarket market = new FinancialMarket();
        market.createAccount(A, new BeneficiaryId("a"), 100);
        market.createAccount(B, new BeneficiaryId("b"), 0);
        var before = market.snapshot();
        LedgerBatch batch = new LedgerBatch("bad.1", List.of(new LedgerBatch.CreateEscrow(E, A)),
                List.of(new LedgerBatch.Transfer(A, E, 60), new LedgerBatch.Transfer(A, B, 50)), List.of());
        assertThrows(MarketException.class, () -> market.applyBatch(batch));
        assertEquals(before, market.snapshot());
    }
    @Test void conflictingIdCannotChangeAnAppliedBatch() {
        FinancialMarket market = new FinancialMarket();
        market.createAccount(A, new BeneficiaryId("a"), 100);
        market.createAccount(B, new BeneficiaryId("b"), 0);
        market.applyBatch(new LedgerBatch("once", List.of(), List.of(new LedgerBatch.Transfer(A, B, 10)), List.of()));
        var before = market.snapshot();
        assertThrows(MarketException.class, () -> market.applyBatch(new LedgerBatch("once", List.of(),
                List.of(new LedgerBatch.Transfer(A, B, 11)), List.of())));
        assertEquals(before, market.snapshot());
    }
    @Test void finiteIssuanceCoinDeliveryCashAndFeeCommitTogether() {
        FinancialMarket market = new FinancialMarket();
        market.createAccount(A, new BeneficiaryId("a"), 0);
        market.createAccount(B, new BeneficiaryId("b"), 100);
        CoinId coin = new CoinId("offering");
        LedgerBatch batch = new LedgerBatch("close", List.of(), List.of(new LedgerBatch.Transfer(B, A, 50)),
                List.of(new LedgerBatch.Fee(A, 1)), List.of(new LedgerBatch.CoinTransfer(A, B, coin, 100)),
                List.of(new LedgerBatch.CoinIssue(coin, A, 200, 200)));
        market.applyBatch(batch);
        assertEquals(49, market.account(A).availableCashCents());
        assertEquals(100, market.account(B).balance(coin).availableCoins());
        assertEquals(200, market.snapshot().totalCoins(coin));
        assertEquals(100, market.snapshot().totalCashCents());
        assertFalse(market.applyBatch(batch).applied());
    }
    @Test void failedCoinDeliveryRollsBackCashIssuanceAndFee() {
        FinancialMarket market = new FinancialMarket();
        market.createAccount(A, new BeneficiaryId("a"), 0);
        market.createAccount(B, new BeneficiaryId("b"), 100);
        var before = market.snapshot(); CoinId coin = new CoinId("offering");
        assertThrows(MarketException.class, () -> market.applyBatch(new LedgerBatch("close", List.of(),
                List.of(new LedgerBatch.Transfer(B, A, 50)), List.of(new LedgerBatch.Fee(A, 1)),
                List.of(new LedgerBatch.CoinTransfer(A, B, coin, 300)),
                List.of(new LedgerBatch.CoinIssue(coin, A, 200, 200)))));
        assertEquals(before, market.snapshot());
    }
}
