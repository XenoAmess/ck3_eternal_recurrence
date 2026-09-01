package com.xenoamess.kaishek.profile;

import java.util.Objects;

public record Unsupported(UnsupportedReason reason, String detail) {
    public Unsupported { reason = Objects.requireNonNull(reason, "reason"); if (detail == null || detail.isBlank()) throw new IllegalArgumentException("detail is blank"); }
}
