package org.xar.ck3.control.contracts.index;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Finite executable regression; no game, files, process lookup or action authority. */
public final class OrderedCandidateIndexTestMain {
    private OrderedCandidateIndexTestMain() { }
    private record Scope(String sourceSha256, BigInteger frame, BigInteger ownerVersion) { }
    private static final class CyclicCandidate {
        private final String name;
        private final Object opaque;
        private CyclicCandidate self;
        private CyclicCandidate(String name, Object opaque) { this.name = name; this.opaque = opaque; self = this; }
        @Override public boolean equals(Object other) { throw new AssertionError("source candidate equals must never run"); }
        @Override public int hashCode() { throw new AssertionError("source candidate hashCode must never run"); }
    }
    private static void check(boolean value, String reason) { if (!value) { throw new AssertionError(reason); } }
    private static void rejected(Runnable operation, String reason) {
        try { operation.run(); } catch (IllegalStateException expected) { return; }
        throw new AssertionError(reason);
    }
    private static void immutable(Runnable operation) {
        try { operation.run(); } catch (UnsupportedOperationException expected) { return; }
        throw new AssertionError("exposed collection is mutable");
    }
    public static void main(String[] arguments) {
        if (arguments.length != 0) { throw new IllegalArgumentException("no test arguments"); }
        var scope = new Scope("a".repeat(64), BigInteger.ONE.shiftLeft(80), BigInteger.ONE);
        var active = new AtomicBoolean(true);
        var current = new java.util.concurrent.atomic.AtomicReference<>(scope);
        OrderedCandidateIndex.ScopeGuard<Scope> guard = expected -> {
            if (!active.get() || !current.get().equals(expected)) { throw new IllegalStateException("revoked source/frame/owner token"); }
        };
        var first = new CyclicCandidate("same", Double.longBitsToDouble(Long.MIN_VALUE));
        var second = new CyclicCandidate("same", Double.valueOf(0.0));
        var values = new ArrayList<CyclicCandidate>();
        values.add(first); values.add(second); values.add(first); values.add(null);
        var extracted = new AtomicInteger();
        var index = OrderedCandidateIndex.<Scope, String, CyclicCandidate>build(scope, guard, values, value -> {
            extracted.incrementAndGet();
            return value == null ? new OrderedCandidateIndex.NullValue<>() : new OrderedCandidateIndex.Present<>(value.name);
        });
        check(extracted.get() == 4, "complete producer sequence visited exactly once");
        values.clear();
        check(index.slots().size() == 4, "all slots survive source-list mutation");
        check(index.matching(new OrderedCandidateIndex.Present<>("same")).stream().map(OrderedCandidateIndex.Slot::position).toList()
                .equals(List.of(0, 1, 2)), "duplicate names retain all original positions");
        check(index.sameObject(first).stream().map(OrderedCandidateIndex.Slot::position).toList().equals(List.of(0, 2)),
                "repeated physical references are not collapsed");
        check(index.sameObject(null).getFirst().position() == 3, "explicit source null retained");
        check(first.self == first && index.slots().getFirst().value() == first, "cycle and identity retained");
        check(Double.doubleToRawLongBits((Double) first.opaque) == Long.MIN_VALUE, "negative zero bits retained");
        check(Double.doubleToRawLongBits((Double) second.opaque) == 0L, "positive zero bits retained");
        check(index.ordered((left, right) -> 0).stream().map(OrderedCandidateIndex.Slot::position).toList()
                .equals(List.of(0, 1, 2, 3)), "stable ties retain source order");
        check(index.slots().get(1).value() == second, "derived ordering cannot mutate base slots");
        check(extracted.get() == 4, "repeated lookup never reruns the producer projection");
        immutable(() -> index.slots().clear());
        immutable(() -> index.matching(new OrderedCandidateIndex.Present<>("same")).clear());
        var presentNullMissing = OrderedCandidateIndex.<Scope, String, Integer>build(scope, guard, List.of(0, 1, 2),
                value -> value == 0 ? new OrderedCandidateIndex.Missing<>() : value == 1
                        ? new OrderedCandidateIndex.NullValue<>() : new OrderedCandidateIndex.Present<>(""));
        check(presentNullMissing.matching(new OrderedCandidateIndex.Missing<>()).getFirst().position() == 0, "missing key retained");
        check(presentNullMissing.matching(new OrderedCandidateIndex.NullValue<>()).getFirst().position() == 1, "null key retained");
        check(presentNullMissing.matching(new OrderedCandidateIndex.Present<>("")).getFirst().position() == 2, "empty name distinct");
        current.set(new Scope("b".repeat(64), scope.frame(), scope.ownerVersion()));
        rejected(index::slots, "source drift must reject old index");
        current.set(new Scope(scope.sourceSha256(), scope.frame().add(BigInteger.ONE), scope.ownerVersion()));
        rejected(() -> index.sameObject(first), "frame drift must reject old index");
        current.set(new Scope(scope.sourceSha256(), scope.frame(), scope.ownerVersion().add(BigInteger.ONE)));
        rejected(() -> index.first(new OrderedCandidateIndex.Present<>("same")), "writer version must reject old index");
        current.set(scope); active.set(false);
        rejected(() -> index.matching(new OrderedCandidateIndex.Present<>("same")), "UNKNOWN token cannot be reused");
        rejected(() -> OrderedCandidateIndex.build(scope, guard, List.of(first), value -> new OrderedCandidateIndex.Present<>(value.name)),
                "UNKNOWN cannot build another index");
        active.set(true);
        rejected(() -> index.ordered((left, right) -> { active.set(false); return 0; }), "post-operation revocation must be detected");
        active.set(true);
        var huge = new CyclicCandidate("large", "x".repeat(8 * 1024 * 1024 + 1));
        var uncapped = OrderedCandidateIndex.<Scope, String, CyclicCandidate>build(scope, guard, List.of(huge),
                value -> new OrderedCandidateIndex.Present<>(value.name));
        check(uncapped.slots().getFirst().value().opaque == huge.opaque, "legal source above former8MiB remains complete by reference");
        System.out.println("ORDERED_CANDIDATE_INDEX_PASS producer_projection_calls=" + extracted.get());
    }
}
