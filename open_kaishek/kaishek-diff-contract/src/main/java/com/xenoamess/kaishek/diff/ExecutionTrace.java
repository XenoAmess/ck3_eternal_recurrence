package com.xenoamess.kaishek.diff;

import com.xenoamess.kaishek.profile.BuildFingerprint;
import java.util.*;

public record ExecutionTrace(String scenarioId, BuildFingerprint fingerprint, List<TraceEntry> entries,
                             Set<String> readSet, Set<String> writeSet, TraceStatus status, List<String> diagnostics) {
    public ExecutionTrace {
        if (scenarioId == null || scenarioId.isBlank()) throw new IllegalArgumentException("scenarioId is blank");
        fingerprint = Objects.requireNonNull(fingerprint, "fingerprint"); entries = List.copyOf(Objects.requireNonNull(entries, "entries"));
        readSet = nonBlankSet(readSet, "readSet"); writeSet = nonBlankSet(writeSet, "writeSet");
        status = Objects.requireNonNull(status, "status"); diagnostics = List.copyOf(Objects.requireNonNull(diagnostics, "diagnostics"));
    }

    private static Set<String> nonBlankSet(Set<String> values, String name) {
        Objects.requireNonNull(values, name);
        if (values.stream().anyMatch(v -> v == null || v.isBlank()))
            throw new IllegalArgumentException(name + " contains blank value");
        return Set.copyOf(values);
    }
}
