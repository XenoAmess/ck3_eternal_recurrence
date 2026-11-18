package org.xar.ck3.markets.issuance;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.markets.core.AccountId;
import org.xar.ck3.markets.core.CoinId;
import org.xar.ck3.markets.core.FinancialMarket;
import org.xar.ck3.markets.core.LedgerBatch;
import org.xar.ck3.markets.listing.ListingFunding;
import org.xar.ck3.markets.listing.ListingFunding.Tier;

/** Reference coordinator over the actual common ledger; not a CK3 runtime adapter.
 * Every operation prepares all domain checks, atomically settles a typed ledger batch,
 * then commits the prepared domain state. Failed transfers never consume claims.
 */
public final class OfferingWallet {
    public record SubscriptionReceipt(String requestId, AccountId buyer, long cents, long lots, boolean applied) { }
    public record RefundReceipt(String requestId, AccountId buyer, long cents, boolean applied) { }
    public record ClosingReceipt(String requestId, Offering.Closing closing, boolean applied) { }
    private sealed interface JournalEntry permits Paid, Refunded, Closed { }
    private record Paid(AccountId buyer, long cents, SubscriptionReceipt receipt) implements JournalEntry { }
    private record Refunded(AccountId buyer, RefundReceipt receipt) implements JournalEntry { }
    private record Closed(ClosingReceipt receipt) implements JournalEntry { }
    private final FinancialMarket market;
    private final Offering offering;
    private final String offeringId;
    private final AccountId project;
    private final CoinId coin;
    private final AccountId subscriptionEscrow;
    private final AccountId maintenanceEscrow;
    private final AccountId bondEscrow;
    private final AccountId makerEscrow;
    private final long paidRegistrationCents;
    private final long priceCentsPerLot;
    private final long minimumProceedsCents;
    private long independentPaidCents;
    private final Map<String, JournalEntry> journal = new LinkedHashMap<>();

    public OfferingWallet(FinancialMarket market, String offeringId, AccountId project, CoinId coin,
                          Tier tier, long centsPerLot, long minimumProceedsCents, long offeredLots) {
        this.market = Objects.requireNonNull(market, "market");
        this.project = Objects.requireNonNull(project, "project"); this.coin = Objects.requireNonNull(coin, "coin");
        if (offeringId == null || !offeringId.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,31}")) throw new IllegalArgumentException("bounded stable offering ID required");
        this.offeringId = offeringId;
        offering = new Offering(tier, centsPerLot, minimumProceedsCents, offeredLots);
        priceCentsPerLot = centsPerLot; this.minimumProceedsCents = minimumProceedsCents;
        subscriptionEscrow = escrow("subscriptions"); maintenanceEscrow = escrow("maintenance");
        bondEscrow = escrow("bond"); makerEscrow = escrow("maker");
        paidRegistrationCents = ListingFunding.quote(tier, 0).registrationFeeCents();
        var initial = new LedgerBatch(batchId("register"), List.of(
                new LedgerBatch.CreateEscrow(subscriptionEscrow, project), new LedgerBatch.CreateEscrow(maintenanceEscrow, project),
                new LedgerBatch.CreateEscrow(bondEscrow, project), new LedgerBatch.CreateEscrow(makerEscrow, project)),
                List.of(), List.of(new LedgerBatch.Fee(project, paidRegistrationCents)));
        if (!market.applyBatch(initial).applied()) throw new IllegalStateException("existing offering requires qualified state restoration, not a new empty model");
    }
    public synchronized SubscriptionReceipt subscribe(String requestId, AccountId buyer, long cents) {
        validateRequest(requestId); Objects.requireNonNull(buyer, "buyer");
        JournalEntry previous = journal.get(requestId);
        if (previous != null) {
            if (!(previous instanceof Paid paid) || !paid.buyer().equals(buyer) || paid.cents() != cents)
                throw new IllegalStateException("request ID reused with conflicting subscription");
            var receipt = paid.receipt();
            return new SubscriptionReceipt(requestId, buyer, receipt.cents(), receipt.lots(), false);
        }
        Offering.SubscriptionPlan prepared = offering.prepareSubscription(buyer.value(), cents);
        var batch = new LedgerBatch(batchId(requestId), List.of(),
                List.of(new LedgerBatch.Transfer(buyer, subscriptionEscrow, cents)), List.of());
        market.applyBatch(batch);
        offering.commitSubscription(prepared);
        if (!market.account(buyer).beneficiaryId().equals(market.account(project).beneficiaryId())) independentPaidCents = Math.addExact(independentPaidCents, cents);
        var receipt = new SubscriptionReceipt(requestId, buyer, cents, cents / priceCentsPerLot, true);
        journal.put(requestId, new Paid(buyer, cents, receipt)); return receipt;
    }
    public synchronized void abort() { offering.abort(); }
    public synchronized RefundReceipt refund(String requestId, AccountId buyer) {
        validateRequest(requestId); Objects.requireNonNull(buyer, "buyer");
        JournalEntry previous = journal.get(requestId);
        if (previous != null) {
            if (!(previous instanceof Refunded refunded) || !refunded.buyer().equals(buyer)) throw new IllegalStateException("request ID reused with conflicting refund");
            return new RefundReceipt(requestId, buyer, refunded.receipt().cents(), false);
        }
        Offering.RefundPlan prepared = offering.prepareRefund(buyer.value());
        List<LedgerBatch.Transfer> transfers = prepared.cents() == 0 ? List.of() : List.of(new LedgerBatch.Transfer(subscriptionEscrow, buyer, prepared.cents()));
        market.applyBatch(new LedgerBatch(batchId(requestId), List.of(), transfers, List.of()));
        offering.commitRefund(prepared);
        var receipt = new RefundReceipt(requestId, buyer, prepared.cents(), true);
        journal.put(requestId, new Refunded(buyer, receipt)); return receipt;
    }
    public synchronized ClosingReceipt close(String requestId) {
        validateRequest(requestId);
        JournalEntry previous = journal.get(requestId);
        if (previous != null) {
            if (!(previous instanceof Closed closed)) throw new IllegalStateException("request ID reused with conflicting close");
            return new ClosingReceipt(requestId, closed.receipt().closing(), false);
        }
        synchronized (market) {
            long minimumIndependent = minimumProceedsCents / 5 + (minimumProceedsCents % 5 == 0 ? 0 : 1);
            if (independentPaidCents < minimumIndependent) throw new IllegalStateException("minimum independent subscription not met");
            long existingBeforePaidRegistration = Math.addExact(market.account(project).availableCashCents(), paidRegistrationCents);
            Offering.ClosingPlan prepared = offering.prepareClosing(existingBeforePaidRegistration);
            Offering.Closing closing = prepared.closing();
            ListingFunding.Allocation costs = closing.allocation();
            long costAfterRegistration = costs.requiredCashCents() - paidRegistrationCents;
            long freeFromProceeds = closing.proceedsCents() - costAfterRegistration;
            if (freeFromProceeds < 0) throw new IllegalStateException("proceeds do not cover disclosed listing restrictions");
            var transfers = new ArrayList<LedgerBatch.Transfer>();
            if (freeFromProceeds > 0) transfers.add(new LedgerBatch.Transfer(subscriptionEscrow, project, freeFromProceeds));
            transfers.add(new LedgerBatch.Transfer(subscriptionEscrow, maintenanceEscrow, costs.prepaidMaintenanceCents()));
            transfers.add(new LedgerBatch.Transfer(subscriptionEscrow, bondEscrow, costs.performanceBondCents()));
            transfers.add(new LedgerBatch.Transfer(subscriptionEscrow, makerEscrow, costs.makerCashCents()));
            var coins = new ArrayList<LedgerBatch.CoinTransfer>();
            for (Offering.Subscription subscription : closing.allotments().values()) {
                coins.add(new LedgerBatch.CoinTransfer(project, new AccountId(subscription.buyerId()), coin,
                        Math.multiplyExact(subscription.lots(), FinancialMarket.COINS_PER_LOT)));
            }
            market.applyBatch(new LedgerBatch(batchId(requestId), List.of(), transfers,
                    List.of(new LedgerBatch.Fee(subscriptionEscrow, costs.listingFeeCents())), coins));
            offering.commitClosing(prepared);
            var receipt = new ClosingReceipt(requestId, closing, true);
            journal.put(requestId, new Closed(receipt)); return receipt;
        }
    }
    public synchronized Offering.State state() { return offering.state(); }
    public synchronized long outstandingSubscriptionCents() { return offering.escrowCents(); }
    public AccountId subscriptionEscrow() { return subscriptionEscrow; }
    public AccountId maintenanceEscrow() { return maintenanceEscrow; }
    public AccountId bondEscrow() { return bondEscrow; }
    public AccountId makerEscrow() { return makerEscrow; }
    private AccountId escrow(String suffix) { return new AccountId("xfm.escrow.offer." + offeringId + "." + suffix); }
    private String batchId(String suffix) { return "offer." + offeringId + "." + suffix; }
    private static void validateRequest(String request) {
        if (request == null || request.equals("register") || !request.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,31}")) throw new IllegalArgumentException("bounded stable non-registration request ID required");
    }
}
