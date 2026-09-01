package com.xenoamess.kaishek.diff;

import java.util.Objects;

public record DeltaChange(String path, String before, String after) {
    public DeltaChange {
        if (path == null || path.isBlank()) throw new IllegalArgumentException("path is blank");
        if (Objects.equals(before, after)) throw new IllegalArgumentException("delta change must change value");
    }
}
