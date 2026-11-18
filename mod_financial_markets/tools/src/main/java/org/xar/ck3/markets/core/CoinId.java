package org.xar.ck3.markets.core;

public record CoinId(String value) implements Comparable<CoinId> {
    public CoinId {
        IdentifierRules.validate(value, "coin ID");
    }

    @Override
    public int compareTo(CoinId other) {
        return value.compareTo(other.value);
    }
}
