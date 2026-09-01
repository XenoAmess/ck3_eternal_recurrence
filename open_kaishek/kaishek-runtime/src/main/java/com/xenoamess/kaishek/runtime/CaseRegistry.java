package com.xenoamess.kaishek.runtime;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/** Registry that rejects stale serials and owner/subject rebinding. */
public final class CaseRegistry {
    private final Map<String, CaseBinding> cases = new ConcurrentHashMap<>();
    public CaseBinding open(String id, ScopeRef owner, ScopeRef subject) {
        Objects.requireNonNull(id); Objects.requireNonNull(owner); Objects.requireNonNull(subject);
        return cases.compute(id, (k, old) -> new CaseBinding(k, old == null ? 0 : old.serial() + 1, owner, subject, 0));
    }
    public Optional<CaseBinding> get(String id) { return Optional.ofNullable(cases.get(id)); }
    public CaseBinding revise(String id) {
        return cases.computeIfPresent(id, (k, old) -> old.nextRevision());
    }
    public boolean matches(CaseBinding expected) {
        CaseBinding actual = cases.get(expected.caseId());
        return expected.equals(actual);
    }
    public boolean matches(String id, long serial, ScopeRef owner, ScopeRef subject, long revision) {
        CaseBinding c = cases.get(id);
        return c != null && c.serial() == serial && c.revision() == revision && c.owner().equals(owner) && c.subject().equals(subject);
    }
}
