package com.xenoamess.kaishek.diff;

import java.util.*;

public record StateDelta(String scenarioId, String beforeHash, String afterHash, long revisionBefore,
                         long revisionAfter, List<DeltaChange> changes, List<String> unsupported, List<String> diagnostics) {
    public StateDelta {
        if (scenarioId == null || scenarioId.isBlank()) throw new IllegalArgumentException("scenarioId is blank");
        beforeHash = hash(beforeHash, "beforeHash"); afterHash = hash(afterHash, "afterHash");
        if (revisionBefore < 0 || revisionAfter < revisionBefore) throw new IllegalArgumentException("invalid revisions");
        changes = List.copyOf(Objects.requireNonNull(changes, "changes"));
        unsupported = nonBlankList(unsupported, "unsupported");
        diagnostics = List.copyOf(Objects.requireNonNull(diagnostics, "diagnostics"));
    }
    private static String hash(String s, String n) { if (s == null || !s.matches("[0-9a-fA-F]{64}")) throw new IllegalArgumentException(n + " must be SHA-256 hex"); return s.toLowerCase(Locale.ROOT); }
    private static List<String> nonBlankList(List<String> values, String name) {
        Objects.requireNonNull(values, name);
        if (values.stream().anyMatch(v -> v == null || v.isBlank()))
            throw new IllegalArgumentException(name + " contains blank value");
        return List.copyOf(values);
    }
}
