package com.xenoamess.kaishek.runtime;

import java.util.Objects;

/** Stable, typed reference; arbitrary map keys are deliberately not accepted. */
public record ScopeRef(com.xenoamess.kaishek.profile.ScopeType type, String id) {
    public ScopeRef {
        Objects.requireNonNull(type, "type");
        if (id == null || id.isBlank()) throw new IllegalArgumentException("scope id is blank");
    }
    /** Compatibility bridge for early runtime clients; profile ScopeType is canonical. */
    public ScopeRef(com.xenoamess.kaishek.runtime.ScopeType type, String id) {
        this(toProfileType(type), id);
    }

    /**
     * Keep the compatibility constructor lossless. The two enums intentionally
     * share their common names; silently rewriting PERFORMANCE_DOMAIN/CASE/SAVED
     * to another kind would change scope semantics at runtime.
     */
    private static com.xenoamess.kaishek.profile.ScopeType toProfileType(
            com.xenoamess.kaishek.runtime.ScopeType type) {
        Objects.requireNonNull(type, "type");
        return com.xenoamess.kaishek.profile.ScopeType.valueOf(type.name());
    }
}
