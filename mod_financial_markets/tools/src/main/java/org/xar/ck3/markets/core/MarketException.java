package org.xar.ck3.markets.core;

public final class MarketException extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;

    public enum Code {
        INVALID_ARGUMENT,
        ACCOUNT_EXISTS,
        ACCOUNT_NOT_FOUND,
        COIN_EXISTS,
        COIN_NOT_FOUND,
        ORDER_NOT_FOUND,
        NOT_OWNER,
        INSUFFICIENT_CASH,
        INSUFFICIENT_COINS,
        SUPPLY_LIMIT,
        SELF_TRADE,
        ORDER_NOT_OPEN,
        ARITHMETIC_OVERFLOW,
        DAY_REGRESSION
    }

    private final Code code;

    public MarketException(Code code, String message) {
        super(message);
        this.code = code;
    }

    public Code code() {
        return code;
    }
}
