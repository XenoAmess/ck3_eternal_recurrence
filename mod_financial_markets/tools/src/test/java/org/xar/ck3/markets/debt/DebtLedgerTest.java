package org.xar.ck3.markets.debt;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.core.AccountId;
import org.xar.ck3.markets.debt.DebtLedger.*;

final class DebtLedgerTest {
    private final AccountId debtor = new AccountId("debtor");
    private final AccountId winner = new AccountId("winner");
    private final AccountId fund = new AccountId("fund");
    private final AccountId donor = new AccountId("relative");
    private final SettlementKey key = new SettlementKey("position-12", 40, SettlementKind.LIQUIDATION);

    @Test void finiteFundCreatesRecourseAndOnlyUnpaidRemainderIsWinnerClaim() {
        var ledger = new DebtLedger();
        var plan = ledger.prepareCover(key, debtor, winner, fund, 1_000, 300);
        assertEquals(List.of(new Payment(fund, winner, 300)), plan.transfers());
        assertThrows(IllegalArgumentException.class, () -> ledger.debt(key));
        ledger.commitCover(plan);
        assertEquals(700, ledger.debt(key).winnerUnpaidCents());
        assertEquals(300, ledger.debt(key).fundRecourseCents());
        assertEquals(1_000, ledger.debt(key).outstandingCents());
    }

    @Test void emptyFundDoesNotCreateMoneyAndTwoPreparedClaimsCannotOverdrawFund() {
        var ledger = new DebtLedger();
        var first = ledger.prepareCover(key, debtor, winner, fund, 1_000, 300);
        var secondKey = new SettlementKey("position-13", 40, SettlementKind.LIQUIDATION);
        var second = ledger.prepareCover(secondKey, debtor, winner, fund, 1_000, 300);
        assertTrue(second.transfers().isEmpty());
        assertEquals(1_000, second.debt().winnerUnpaidCents());
        ledger.abortCover(first); ledger.abortCover(second);
        assertTrue(ledger.snapshot().debts().isEmpty());
    }

    @Test void exactRetryPaysNothingAndConflictingIdentityFails() {
        var ledger = fundedLedger();
        var replay = ledger.prepareCover(key, debtor, winner, fund, 1_000, 99_999);
        assertTrue(replay.replay()); assertTrue(replay.transfers().isEmpty());
        ledger.commitCover(replay);
        assertThrows(IllegalArgumentException.class, () -> ledger.prepareCover(key, debtor, winner, fund, 1_001, 300));
        assertEquals(1, ledger.snapshot().debts().size());
    }

    @Test void realAidPaysWinnerBeforeFundAndUnusedDonationRemainsWithPayer() {
        var ledger = fundedLedger();
        var plan = ledger.prepareRepayment("aid-1", key, donor, 2_000, 1_000);
        assertEquals(List.of(new Payment(donor, winner, 700), new Payment(donor, fund, 300)), plan.transfers());
        assertEquals(1_000, plan.paidCents());
        ledger.commitRepayment(plan);
        assertEquals(0, ledger.debt(key).outstandingCents());
        assertTrue(ledger.prepareRepayment("aid-1", key, donor, 2_000, 0).transfers().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> ledger.prepareRepayment("aid-1", key, donor, 999, 999));
    }

    @Test void insufficientPayerMoneyAndUnconsentedWriteDownNeverChangeClaims() {
        var ledger = fundedLedger();
        assertThrows(IllegalArgumentException.class, () -> ledger.prepareRepayment("poor", key, donor, 500, 499));
        assertThrows(IllegalArgumentException.class, () -> ledger.writeDown("bad", key, 1, 0, false, false));
        assertEquals(1_000, ledger.debt(key).outstandingCents());
        ledger.writeDown("agreement", key, 100, 0, true, false);
        assertEquals(900, ledger.debt(key).outstandingCents());
        assertEquals(100, ledger.debt(key).writtenOffCents());
        assertEquals(300, ledger.debt(key).fundRecourseCents());
    }

    @Test void inheritanceKeepsStableDebtorAccountAndSnapshotKeepsRetryProtection() {
        var ledger = fundedLedger();
        var aid = ledger.prepareRepayment("aid-1", key, donor, 100, 100);
        ledger.commitRepayment(aid);
        var restored = DebtLedger.restore(ledger.snapshot());
        assertEquals(debtor, restored.debt(key).debtor());
        assertEquals(900, restored.debt(key).outstandingCents());
        assertTrue(restored.prepareRepayment("aid-1", key, donor, 100, 0).replay());
        assertTrue(restored.prepareCover(key, debtor, winner, fund, 1_000, 0).transfers().isEmpty());
    }

    @Test void uncommittedCashPlansCannotBeSavedOrWrittenDown() {
        var ledger = fundedLedger();
        var plan = ledger.prepareRepayment("aid", key, donor, 200, 200);
        assertThrows(IllegalStateException.class, ledger::snapshot);
        assertThrows(IllegalStateException.class, () -> ledger.writeDown("haircut", key, 1, 0, true, false));
        ledger.abortRepayment(plan);
        assertEquals(1_000, ledger.debt(key).outstandingCents());
    }

    @Test void invalidFinancialInputsAndDuplicateSaveRecordsAreRejected() {
        var ledger = new DebtLedger();
        assertThrows(IllegalArgumentException.class, () -> ledger.prepareCover(key, debtor, winner, fund, -1, 10));
        assertThrows(IllegalArgumentException.class, () -> ledger.prepareCover(key, debtor, debtor, fund, 1, 0));
        var funded = fundedLedger().snapshot();
        assertThrows(IllegalArgumentException.class, () -> DebtLedger.restore(new Snapshot(
                List.of(funded.debts().getFirst(), funded.debts().getFirst()), funded.covers(), List.of(), List.of())));
    }

    @Test void fundingClaimsRemainRealButCannotDrainDefaultFund() {
        var ledger = new DebtLedger();
        var funded = ledger.prepareCover(key, debtor, winner, fund, 1_000, 300);
        var fundingKey = new SettlementKey("perpetual-1", 40, SettlementKind.FUNDING);
        var funding = ledger.prepareCover(fundingKey, debtor, winner, fund, 100, 0);
        assertFalse(funding.insured()); assertTrue(funding.transfers().isEmpty());
        ledger.commitCover(funded); ledger.commitCover(funding);
        assertEquals(100, ledger.debt(fundingKey).winnerUnpaidCents());
        assertEquals(0, ledger.debt(fundingKey).fundRecourseCents());
        var uninsuredKey = new SettlementKey("uninsured-1", 40, SettlementKind.LIQUIDATION);
        var uninsured = ledger.prepareCover(uninsuredKey, debtor, winner, fund, 100, 9_000, false);
        assertTrue(uninsured.transfers().isEmpty()); ledger.commitCover(uninsured);
        assertThrows(IllegalArgumentException.class,
                () -> ledger.prepareCover(uninsuredKey, debtor, winner, fund, 100, 9_000, true));
    }

    @Test void operationIdentityCannotBeReservedForTwoClaims() {
        var ledger = fundedLedger();
        var otherKey = new SettlementKey("other", 40, SettlementKind.LIQUIDATION);
        ledger.commitCover(ledger.prepareCover(otherKey, debtor, winner, fund, 100, 0));
        var repayment = ledger.prepareRepayment("same-operation", key, donor, 10, 10);
        assertThrows(IllegalArgumentException.class,
                () -> ledger.prepareRepayment("same-operation", otherKey, donor, 10, 10));
        assertThrows(IllegalStateException.class,
                () -> ledger.writeDown("same-operation", otherKey, 1, 0, true, false));
        ledger.abortRepayment(repayment);
    }

    @Test void snapshotsMustReconcileActualPaymentHistoryRatherThanOnlyCurrentTotals() {
        var ledger = fundedLedger();
        var repayment = ledger.prepareRepayment("aid", key, donor, 100, 100);
        ledger.commitRepayment(repayment);
        ledger.writeDown("agreement", key, 100, 0, true, false);
        assertEquals(800, DebtLedger.restore(ledger.snapshot()).debt(key).outstandingCents());
        Snapshot saved = ledger.snapshot();
        assertThrows(IllegalArgumentException.class,
                () -> DebtLedger.restore(new Snapshot(saved.debts(), saved.covers(), List.of(), saved.writeDowns())));
    }

    @Test void largeGapRemainsWholeDebtWhileSingleFundPaymentIsBounded() {
        var ledger = new DebtLedger();
        var plan = ledger.prepareCover(key, debtor, winner, fund, 2_000_000_000L, 500_000_000L);
        assertEquals(100_000_000L, plan.debt().fundPaidCents());
        assertEquals(1_900_000_000L, plan.debt().winnerUnpaidCents());
        assertEquals(2_000_000_000L, plan.debt().outstandingCents());
        ledger.commitCover(plan);
        assertEquals(plan.debt(), DebtLedger.restore(ledger.snapshot()).debt(key));
    }

    @Test void monetaryClaimAndOperationIdentitySurviveJsonRoundTrip() throws Exception {
        var ledger = fundedLedger();
        var repayment = ledger.prepareRepayment("paid", key, donor, 100, 100);
        ledger.commitRepayment(repayment);
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        Snapshot snapshot = mapper.readValue(mapper.writeValueAsBytes(ledger.snapshot()), Snapshot.class);
        var restored = DebtLedger.restore(snapshot);
        assertEquals(900, restored.debt(key).outstandingCents());
        assertTrue(restored.prepareRepayment("paid", key, donor, 100, 0).replay());
    }

    private DebtLedger fundedLedger() {
        var ledger = new DebtLedger();
        ledger.commitCover(ledger.prepareCover(key, debtor, winner, fund, 1_000, 300));
        return ledger;
    }
}
