package com.xenoamess.kaishek.diff;

import com.xenoamess.kaishek.ir.IrProgram;
import java.util.*;

public record DifferentialScenario(String id, WorldSnapshot preSnapshot, IrProgram program,
                                    List<Long> drawTape, Map<String, String> metadata) {
    public DifferentialScenario {
        if (id == null || id.isBlank()) throw new IllegalArgumentException("id is blank");
        preSnapshot = Objects.requireNonNull(preSnapshot, "preSnapshot"); program = Objects.requireNonNull(program, "program");
        if (!program.fingerprint().equals(preSnapshot.fingerprint())) throw new IllegalArgumentException("profile fingerprint mismatch");
        drawTape = List.copyOf(Objects.requireNonNull(drawTape, "drawTape")); if (drawTape.stream().anyMatch(Objects::isNull)) throw new IllegalArgumentException("drawTape contains null");
        metadata = immutableMetadata(metadata);
    }

    private static Map<String, String> immutableMetadata(Map<String, String> metadata) {
        Objects.requireNonNull(metadata, "metadata");
        if (metadata.entrySet().stream().anyMatch(e -> e.getKey() == null || e.getKey().isBlank()
                || e.getValue() == null))
            throw new IllegalArgumentException("metadata contains invalid entry");
        return Collections.unmodifiableMap(new TreeMap<>(metadata));
    }
}
