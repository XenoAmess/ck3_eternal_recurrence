package org.xar.ck3.markets.core;

public record OrderId(long value) {
    public OrderId {
        if (value <= 0) {
            throw new IllegalArgumentException("order ID must be positive");
        }
    }
}
