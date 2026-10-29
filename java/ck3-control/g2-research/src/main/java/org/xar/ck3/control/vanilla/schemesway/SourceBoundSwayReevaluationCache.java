package org.xar.ck3.control.vanilla.schemesway;

import java.util.Objects;
import java.util.Optional;

/** Bounded per-owner cache of pure nomination. Native terms and submission are always outside it. */
public final class SourceBoundSwayReevaluationCache {
    public enum Disposition { COMPUTED, REUSED_EXACT_INPUT }
    public record Lookup(OrdinarySwaySchedule.Decision decision, Disposition disposition,
            long computations, long exactReuses) {
        public Lookup { Objects.requireNonNull(decision); Objects.requireNonNull(disposition); }
    }
    private record Entry(OrdinarySwaySchedule.Request request, OrdinarySwaySchedule.Decision decision) { }
    private Optional<Entry> last = Optional.empty();
    private long computations;
    private long exactReuses;

    public synchronized Lookup evaluate(OrdinarySwaySchedule.Request request) {
        Objects.requireNonNull(request);
        if (last.isPresent() && last.orElseThrow().request().equals(request)) {
            exactReuses = Math.addExact(exactReuses, 1);
            return new Lookup(last.orElseThrow().decision(), Disposition.REUSED_EXACT_INPUT, computations, exactReuses);
        }
        OrdinarySwaySchedule.Decision decision = OrdinarySwaySchedule.plan(request);
        computations = Math.addExact(computations, 1);
        last = Optional.of(new Entry(request, decision));
        return new Lookup(decision, Disposition.COMPUTED, computations, exactReuses);
    }

    public synchronized void clear() { last = Optional.empty(); }
}
