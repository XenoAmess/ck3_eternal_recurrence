package org.xar.ck3.markets.issuance;

import java.util.LinkedHashMap;
import java.util.Collections;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.markets.listing.ListingFunding;
import org.xar.ck3.markets.listing.ListingFunding.Tier;

/** Pure offering-state calculator, never a wallet API. Use OfferingWallet for actual cash settlement. */
public final class Offering {
    public enum State { SUBSCRIBING, LISTED, REFUNDING, REFUNDED }
    public record Subscription(String buyerId, long cents, long lots) { }
    public record Closing(long proceedsCents, long freeProjectCashCents,
                          ListingFunding.Allocation allocation, Map<String, Subscription> allotments) {
        public Closing { allotments = Collections.unmodifiableMap(new LinkedHashMap<>(allotments)); }
    }
    private final Tier tier;
    private final long centsPerLot;
    private final long minimumProceedsCents;
    private final long offeredLots;
    private final Map<String, Subscription> subscriptions = new LinkedHashMap<>();
    private final Map<String, Long> refunds = new LinkedHashMap<>();
    private long paidCents;
    private long soldLots;
    private long revision;
    private State state = State.SUBSCRIBING;

    public Offering(Tier tier, long centsPerLot, long minimumProceedsCents, long offeredLots) {
        this.tier = Objects.requireNonNull(tier, "tier");
        if (centsPerLot <= 0 || minimumProceedsCents < 0 || offeredLots <= 0) throw new IllegalArgumentException("invalid offer");
        this.centsPerLot = centsPerLot; this.minimumProceedsCents = minimumProceedsCents; this.offeredLots = offeredLots;
        Math.multiplyExact(centsPerLot, offeredLots);
    }
    record SubscriptionPlan(long revision, Subscription subscription, long totalLots, long totalCents) { }
    record RefundPlan(long revision, String buyerId, long cents) { }
    record ClosingPlan(long revision, Closing closing) { }

    SubscriptionPlan prepareSubscription(String buyerId, long actualPaidCents) {
        requireState(State.SUBSCRIBING);
        if (buyerId == null || buyerId.isBlank() || actualPaidCents <= 0 || actualPaidCents % centsPerLot != 0)
            throw new IllegalArgumentException("paid whole lots and buyer required");
        long lots = actualPaidCents / centsPerLot;
        long updatedLots = Math.addExact(soldLots, lots);
        long updatedPaid = Math.addExact(paidCents, actualPaidCents);
        if (updatedLots > offeredLots || (tier == Tier.MICRO && updatedPaid > 5_000))
            throw new IllegalArgumentException("offering capacity exceeded");
        Subscription old = subscriptions.getOrDefault(buyerId, new Subscription(buyerId, 0, 0));
        Subscription next = new Subscription(buyerId, Math.addExact(old.cents(), actualPaidCents), Math.addExact(old.lots(), lots));
        return new SubscriptionPlan(revision, next, updatedLots, updatedPaid);
    }
    void commitSubscription(SubscriptionPlan plan) {
        requireRevision(plan.revision());
        subscriptions.put(plan.subscription().buyerId(), plan.subscription());
        soldLots = plan.totalLots(); paidCents = plan.totalCents(); revision++;
    }
    /** Pure model convenience only; it does not debit or represent a real-world wallet. */
    public Subscription subscribe(String buyerId, long actualPaidCents) {
        SubscriptionPlan plan = prepareSubscription(buyerId, actualPaidCents);
        commitSubscription(plan); return plan.subscription();
    }
    ClosingPlan prepareClosing(long existingProjectCashCents) {
        requireState(State.SUBSCRIBING);
        if (paidCents < minimumProceedsCents) throw new IllegalStateException("minimum actual subscription not met");
        ListingFunding.Funding funding = ListingFunding.fund(tier, existingProjectCashCents, paidCents);
        return new ClosingPlan(revision, new Closing(paidCents, funding.freeProjectCashCents(), funding.allocation(), subscriptions));
    }
    void commitClosing(ClosingPlan plan) {
        requireRevision(plan.revision()); state = State.LISTED; revision++;
    }
    public Closing close(long existingProjectCashCents) {
        ClosingPlan plan = prepareClosing(existingProjectCashCents); commitClosing(plan); return plan.closing();
    }
    public void abort() {
        requireState(State.SUBSCRIBING);
        for (Subscription subscription : subscriptions.values()) refunds.put(subscription.buyerId(), subscription.cents());
        state = refunds.isEmpty() ? State.REFUNDED : State.REFUNDING;
        revision++;
    }
    RefundPlan prepareRefund(String buyerId) {
        if (state != State.REFUNDING && state != State.REFUNDED) throw new IllegalStateException("not refunding");
        return new RefundPlan(revision, buyerId, refunds.getOrDefault(buyerId, 0L));
    }
    void commitRefund(RefundPlan plan) {
        requireRevision(plan.revision());
        if (plan.cents() == 0) return;
        refunds.remove(plan.buyerId());
        paidCents = Math.subtractExact(paidCents, plan.cents());
        if (refunds.isEmpty()) state = State.REFUNDED;
        revision++;
    }
    /** Pure model convenience. A real refund commits through OfferingWallet after the transfer. */
    public long claimRefund(String buyerId) {
        RefundPlan plan = prepareRefund(buyerId); commitRefund(plan); return plan.cents();
    }
    public State state() { return state; }
    public long escrowCents() { return state == State.LISTED ? 0 : paidCents; }
    public long soldLots() { return soldLots; }
    private void requireState(State required) {
        if (state != required) throw new IllegalStateException("offering is " + state);
    }
    private void requireRevision(long expected) {
        if (revision != expected) throw new IllegalStateException("stale prepared offering transition");
    }
}
