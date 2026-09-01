package com.xenoamess.kaishek.runtime;

import java.util.*;

/** Immutable ROOT/THIS/PREV context and explicitly saved scopes. */
public final class ScopeContext {
    private final ScopeRef root, current, previous;
    private final Map<String, ScopeRef> saved;

    public ScopeContext(ScopeRef root, ScopeRef current, ScopeRef previous) {
        this(root, current, previous, Map.of());
    }
    public ScopeContext(ScopeRef root, ScopeRef current, ScopeRef previous, Map<String, ScopeRef> saved) {
        this.root = Objects.requireNonNull(root); this.current = Objects.requireNonNull(current);
        this.previous = previous;
        this.saved = Map.copyOf(saved == null ? Map.of() : saved);
    }
    public ScopeRef root() { return root; }
    public ScopeRef current() { return current; }
    public ScopeRef previous() { return previous; }
    public Map<String, ScopeRef> saved() { return saved; }
    public ScopeRef resolve(String token) {
        if (token == null) return null;
        return switch (token) { case "ROOT" -> root; case "THIS" -> current; case "PREV" -> previous;
            default -> saved.get(token); };
    }
    public ScopeContext withCurrent(ScopeRef next) { return new ScopeContext(root, next, current, saved); }
    public ScopeContext save(String name, ScopeRef ref) {
        if (name == null || name.isBlank() || ref == null) throw new IllegalArgumentException("invalid saved scope");
        Map<String, ScopeRef> m = new LinkedHashMap<>(saved); m.put(name, ref);
        return new ScopeContext(root, current, previous, m);
    }
}
