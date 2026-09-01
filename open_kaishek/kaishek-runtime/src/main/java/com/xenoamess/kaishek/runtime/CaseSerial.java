package com.xenoamess.kaishek.runtime;

/** Monotonic identity component for a case; a reopened case always gets a new serial. */
public record CaseSerial(String caseId, long value) {
    public CaseSerial { if (caseId == null || caseId.isBlank() || value < 0) throw new IllegalArgumentException("invalid case serial"); }
}
