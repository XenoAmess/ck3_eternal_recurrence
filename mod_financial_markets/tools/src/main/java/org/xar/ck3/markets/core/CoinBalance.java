package org.xar.ck3.markets.core;

public record CoinBalance(long availableCoins, long reservedCoins) {
    public long totalCoins() {
        return Math.addExact(availableCoins, reservedCoins);
    }
}
