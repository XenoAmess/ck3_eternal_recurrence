package com.xenoamess.kaishek.runtime;

import java.util.Objects;

public record Receipt(String transactionId, String account, String resource, long charged, long refunded) {
    public Receipt {
        Objects.requireNonNull(transactionId); Objects.requireNonNull(account); Objects.requireNonNull(resource);
        if (transactionId.isBlank() || account.isBlank() || resource.isBlank() || charged < 0 || refunded < 0 || refunded > charged)
            throw new IllegalArgumentException("invalid receipt");
    }
    public long net() { return charged - refunded; }
}
