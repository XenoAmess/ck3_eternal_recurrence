package org.xar.ck3.markets.core;

public record Trade(long sequence, long day, CoinId coinId, OrderId buyOrderId, OrderId sellOrderId,
                    AccountId buyerId, AccountId sellerId, long lots, long priceCentsPerLot,
                    long grossCents, long buyerFeeCents, long sellerFeeCents) {
}
