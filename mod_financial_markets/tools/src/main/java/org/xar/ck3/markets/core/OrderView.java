package org.xar.ck3.markets.core;

public record OrderView(OrderId id, long submittedDay, AccountId ownerId, CoinId coinId, Side side,
                        long originalLots, long filledLots, long limitPriceCentsPerLot,
                        long filledGrossCents, long feePaidCents, long reservedCashCents,
                        OrderStatus status) {
    public long unfilledLots() {
        return originalLots - filledLots;
    }
}
