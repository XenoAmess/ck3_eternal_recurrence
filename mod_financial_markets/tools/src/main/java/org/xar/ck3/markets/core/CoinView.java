package org.xar.ck3.markets.core;

public record CoinView(CoinId id, AccountId issuerId, long issuedCoins, long maxSupplyCoins) {
}
