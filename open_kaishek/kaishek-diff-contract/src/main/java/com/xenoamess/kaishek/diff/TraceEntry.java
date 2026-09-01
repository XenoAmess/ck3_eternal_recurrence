package com.xenoamess.kaishek.diff;

import com.xenoamess.kaishek.ir.SourceSpan;
import java.util.*;

public record TraceEntry(long sequence, String opcodeId, SourceSpan sourceSpan, TraceStatus status,
                         String branch, Set<String> reads, Set<String> writes, List<String> draws, String message) {
    public TraceEntry(long sequence, String opcodeId, com.xenoamess.kaishek.syntax.SourceSpan sourceSpan, TraceStatus status,
                      String branch, Set<String> reads, Set<String> writes, List<String> draws, String message) {
        this(sequence, opcodeId, new SourceSpan("<input>", sourceSpan.start(), sourceSpan.end(), 1, 1, 1, 1), status, branch, reads, writes, draws, message);
    }
    public TraceEntry {
        if (sequence < 0 || opcodeId == null || opcodeId.isBlank()) throw new IllegalArgumentException("invalid trace entry");
        sourceSpan = Objects.requireNonNull(sourceSpan, "sourceSpan"); status = Objects.requireNonNull(status, "status");
        branch = branch == null ? "" : branch; reads = nonBlankSet(reads, "reads"); writes = nonBlankSet(writes, "writes");
        draws = List.copyOf(Objects.requireNonNull(draws, "draws")); message = message == null ? "" : message;
    }

    private static Set<String> nonBlankSet(Set<String> values, String name) {
        Objects.requireNonNull(values, name);
        if (values.stream().anyMatch(v -> v == null || v.isBlank()))
            throw new IllegalArgumentException(name + " contains blank value");
        return Set.copyOf(values);
    }
}
