package com.xenoamess.kaishek.profile;

import java.util.Set;

/** Static validator shape for one script opcode. */
public record OpcodeSpec(String name, Kind kind, int minParameters, int maxParameters,
                         Set<String> allowedScopes, String introducedIn) {
    public OpcodeSpec {
        if (name == null || name.isBlank()) throw new IllegalArgumentException("opcode name is blank");
        kind = java.util.Objects.requireNonNull(kind, "kind");
        if (minParameters < 0 || maxParameters < minParameters) throw new IllegalArgumentException("parameter range");
        allowedScopes = allowedScopes == null ? Set.of() : Set.copyOf(allowedScopes);
        introducedIn = introducedIn == null ? "1.0" : introducedIn;
    }
    public enum Kind { TRIGGER, EFFECT, VALUE, INTERFACE, STRUCTURAL }
}
