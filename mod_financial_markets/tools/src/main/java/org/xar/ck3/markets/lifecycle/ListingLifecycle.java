package org.xar.ck3.markets.lifecycle;

import java.util.Objects;
import java.util.OptionalLong;

/** One venue pair. Coin ownership and contracts on other reliable venues survive its closure. */
public final class ListingLifecycle {
    public enum State { NORMAL, WARNING, SUSPENDED, DELISTING, DELISTED, RELIST_REVIEW, ARCHIVED }
    public enum DerivativeDisposition { LIVE, REDUCE_ONLY, SETTLEMENT_DUE, PRICE_PENDING, TERMINATED }
    public record Rights(long holders, long orders, long collateralCents, long openContracts,
                         long redemptionCents, long debtCents, long unclaimedCents) {
        public Rights {
            if (holders < 0 || orders < 0 || collateralCents < 0 || openContracts < 0
                    || redemptionCents < 0 || debtCents < 0 || unclaimedCents < 0)
                throw new IllegalArgumentException("negative residual right");
        }
        public boolean empty() {
            return holders == 0 && orders == 0 && collateralCents == 0 && openContracts == 0
                    && redemptionCents == 0 && debtCents == 0 && unclaimedCents == 0;
        }
    }
    public record Snapshot(String permanentCoinId, String venueId, State state, long noticeDay,
                           boolean spotTrading, boolean newDerivativeRisk, boolean otcTransfer,
                           DerivativeDisposition derivatives, OptionalLong settlementPriceCents,
                           long nextReviewDay, int defaultHistoryCount) { }
    private final String coinId;
    private final String venueId;
    private State state = State.NORMAL;
    private DerivativeDisposition derivatives = DerivativeDisposition.LIVE;
    private long lastProcessedDay = -1;
    private long noticeDay = -1;
    private long nextReviewDay = -1;
    private long sumPriceCents;
    private int qualifiedSamples;
    private OptionalLong settlementPrice = OptionalLong.empty();
    private int defaults;
    public ListingLifecycle(String coinId, String venueId) {
        if (coinId == null || coinId.isBlank() || venueId == null || venueId.isBlank()) throw new IllegalArgumentException("identities required");
        this.coinId = coinId; this.venueId = venueId;
    }
    public void warn() {
        if (state == State.NORMAL) state = State.WARNING;
    }
    public void announce(long day) {
        nonnegative(day);
        if (state != State.NORMAL && state != State.WARNING && state != State.SUSPENDED)
            throw new IllegalStateException("cannot announce in " + state);
        state = State.DELISTING; noticeDay = day; derivatives = DerivativeDisposition.REDUCE_ONLY;
        qualifiedSamples = 0; sumPriceCents = 0; settlementPrice = OptionalLong.empty(); nextReviewDay = day + 30;
    }
    public void suspend(long day) {
        nonnegative(day);
        if (state != State.NORMAL && state != State.WARNING) throw new IllegalStateException("cannot suspend in " + state);
        state = State.SUSPENDED; derivatives = DerivativeDisposition.REDUCE_ONLY; nextReviewDay = Math.addExact(day, 3);
    }
    public void reviewSuspension(long day, boolean resume) {
        if (state != State.SUSPENDED || day < nextReviewDay) throw new IllegalStateException("review not due");
        if (resume) { state = State.WARNING; derivatives = DerivativeDisposition.LIVE; nextReviewDay = -1; }
        else nextReviewDay = Math.addExact(day, 7);
    }
    /** An eligible sample must already exclude issuer/self/wash trades and stale or unreliable prices. */
    public void advance(long day, OptionalLong eligiblePriceCents) {
        nonnegative(day); Objects.requireNonNull(eligiblePriceCents, "price");
        if (eligiblePriceCents.isPresent() && eligiblePriceCents.getAsLong() <= 0) throw new IllegalArgumentException("positive qualified price required");
        if (day < lastProcessedDay) throw new IllegalArgumentException("day moved backwards");
        if (day == lastProcessedDay) return;
        lastProcessedDay = day;
        if (state == State.RELIST_REVIEW && day >= nextReviewDay) { state = State.WARNING; derivatives = DerivativeDisposition.LIVE; return; }
        if (state != State.DELISTING) return;
        long elapsed = day - noticeDay;
        if (elapsed >= 15 && elapsed <= 20 && eligiblePriceCents.isPresent()) {
            sumPriceCents = Math.addExact(sumPriceCents, eligiblePriceCents.getAsLong()); qualifiedSamples++;
        }
        if (elapsed >= 21 && derivatives == DerivativeDisposition.REDUCE_ONLY) {
            if (qualifiedSamples >= 3) {
                settlementPrice = OptionalLong.of(sumPriceCents / qualifiedSamples);
                derivatives = DerivativeDisposition.SETTLEMENT_DUE;
            } else derivatives = DerivativeDisposition.PRICE_PENDING;
        }
        if (elapsed >= 30) state = State.DELISTED;
    }
    /** Caller confirms the exact contract transfers/debt claims have been recorded before terminalizing. */
    public void confirmDerivativeTermination() {
        if (derivatives != DerivativeDisposition.SETTLEMENT_DUE) throw new IllegalStateException("no qualified settlement due");
        derivatives = DerivativeDisposition.TERMINATED;
    }
    public void resolvePricePending(long contractAuthorizedPriceCents) {
        if (derivatives != DerivativeDisposition.PRICE_PENDING || contractAuthorizedPriceCents <= 0)
            throw new IllegalStateException("positive contract-authorized replacement required");
        settlementPrice = OptionalLong.of(contractAuthorizedPriceCents); derivatives = DerivativeDisposition.SETTLEMENT_DUE;
    }
    public void recordDefault() { defaults = Math.addExact(defaults, 1); }
    public void requestRelist(long day, boolean maintenancePaid, boolean makerFunded, boolean responsibilityHandled) {
        nonnegative(day);
        if (state != State.DELISTED || !maintenancePaid || !makerFunded || !responsibilityHandled
                || derivatives == DerivativeDisposition.PRICE_PENDING || derivatives == DerivativeDisposition.SETTLEMENT_DUE)
            throw new IllegalStateException("relisting requirements not met");
        state = State.RELIST_REVIEW; nextReviewDay = Math.addExact(day, 30);
    }
    public void archive(Rights rights) {
        Objects.requireNonNull(rights, "rights");
        if (state != State.DELISTED || !rights.empty()) throw new IllegalStateException("remaining rights forbid archive");
        state = State.ARCHIVED;
    }
    public Snapshot snapshot() {
        boolean trading = state == State.NORMAL || state == State.WARNING || state == State.DELISTING;
        return new Snapshot(coinId, venueId, state, noticeDay, trading,
                state == State.NORMAL || state == State.WARNING, state != State.ARCHIVED, derivatives,
                settlementPrice, nextReviewDay, defaults);
    }
    private static void nonnegative(long day) { if (day < 0) throw new IllegalArgumentException("negative day"); }
}
