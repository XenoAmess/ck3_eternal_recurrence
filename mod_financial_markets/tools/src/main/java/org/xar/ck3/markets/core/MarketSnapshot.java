package org.xar.ck3.markets.core;

import java.util.List;

public record MarketSnapshot(long day, long nextOrderSequence, long nextTradeSequence,
                             long importedCashCents, long feeTreasuryCents,
                             List<AccountView> accounts, List<CoinView> coins,
                             List<OrderView> orders, List<Trade> trades) {
    public MarketSnapshot {
        accounts = List.copyOf(accounts);
        coins = List.copyOf(coins);
        orders = List.copyOf(orders);
        trades = List.copyOf(trades);
    }

    public long totalCashCents() {
        long total = feeTreasuryCents;
        for (AccountView account : accounts) {
            total = Math.addExact(total, account.totalCashCents());
        }
        return total;
    }

    public long totalCoins(CoinId coinId) {
        long total = 0;
        for (AccountView account : accounts) {
            total = Math.addExact(total, account.balance(coinId).totalCoins());
        }
        return total;
    }
}
