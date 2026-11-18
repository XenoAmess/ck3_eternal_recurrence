package org.xar.ck3.markets.core;

public record AccountId(String value) implements Comparable<AccountId> {
    public AccountId {
        IdentifierRules.validate(value, "account ID");
    }

    @Override
    public int compareTo(AccountId other) {
        return value.compareTo(other.value);
    }
}
