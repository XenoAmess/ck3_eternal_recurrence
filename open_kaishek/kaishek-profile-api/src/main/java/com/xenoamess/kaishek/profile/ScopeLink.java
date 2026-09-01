package com.xenoamess.kaishek.profile;

import java.util.Objects;

/** A typed transition from one scope to another. */
public record ScopeLink(ScopeType from, ScopeType to, String operation) {
    public ScopeLink {
        from = Objects.requireNonNull(from, "from");
        to = Objects.requireNonNull(to, "to");
        operation = operation == null || operation.isBlank() ? "identity" : operation;
    }
}
