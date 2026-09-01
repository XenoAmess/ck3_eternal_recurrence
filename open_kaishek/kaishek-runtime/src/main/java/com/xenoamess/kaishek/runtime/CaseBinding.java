package com.xenoamess.kaishek.runtime;

import java.util.Objects;

/** Identity tuple used by serial/owner/subject stale guards. */
public record CaseBinding(String caseId, long serial, ScopeRef owner, ScopeRef subject, long revision) {
    public CaseBinding {
        if (caseId == null || caseId.isBlank() || serial < 0 || revision < 0) throw new IllegalArgumentException("invalid case binding");
        Objects.requireNonNull(owner); Objects.requireNonNull(subject);
    }
    public CaseBinding nextRevision() { return new CaseBinding(caseId, serial, owner, subject, revision + 1); }
    public CaseSerial caseSerial() { return new CaseSerial(caseId, serial); }
}
