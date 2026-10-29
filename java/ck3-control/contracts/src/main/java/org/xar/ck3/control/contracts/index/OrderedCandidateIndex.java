package org.xar.ck3.control.contracts.index;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;

/**
 * A complete source sequence and reusable lookup tables, with no admission or selection policy.
 * Membership and lookup keys are immutable. Source values are retained by reference, including
 * null, repeated references, aliases and cycles; this class never compares or serializes them.
 * The owner must supply equality-safe immutable keys and a live scope guard. Resource admission
 * belongs to that owner: no native-frame or fixed JSON byte limit is a candidate count limit.
 */
public final class OrderedCandidateIndex<S, K, T> {
    /** Implemented by the original owner; a source/frame change or UNKNOWN must revoke the scope. */
    @FunctionalInterface
    public interface ScopeGuard<S> {
        void requireCurrent(S scope);
    }

    /** Missing, explicit null and a present lookup value are separate keys. */
    public sealed interface Key<K> permits Missing, NullValue, Present { }
    public record Missing<K>() implements Key<K> { }
    public record NullValue<K>() implements Key<K> { }
    public record Present<K>(K value) implements Key<K> {
        public Present { Objects.requireNonNull(value, "lookup value"); }
    }

    /** Position is the original zero-based sequence position; value may be null source content. */
    public record Slot<K, T>(int position, Key<K> key, T value) {
        public Slot {
            if (position < 0) { throw new IllegalArgumentException("negative source position"); }
            Objects.requireNonNull(key, "lookup key");
        }
    }

    private final S scope;
    private final ScopeGuard<? super S> guard;
    private final List<Slot<K, T>> slots;
    private final Map<Key<K>, List<Slot<K, T>>> keyed;
    private final IdentityHashMap<T, List<Slot<K, T>>> identities;

    private OrderedCandidateIndex(S scope, ScopeGuard<? super S> guard,
            List<Slot<K, T>> slots, Map<Key<K>, List<Slot<K, T>>> keyed,
            IdentityHashMap<T, List<Slot<K, T>>> identities) {
        this.scope = scope;
        this.guard = guard;
        this.slots = List.copyOf(slots);
        this.keyed = Collections.unmodifiableMap(keyed);
        this.identities = identities;
    }

    /** Visit every supplied slot once; the extractor is never a filter or a ranking function. */
    public static <S, K, T> OrderedCandidateIndex<S, K, T> build(S scope,
            ScopeGuard<? super S> guard, List<? extends T> values,
            Function<? super T, ? extends Key<K>> keyExtractor) {
        Objects.requireNonNull(scope, "scope");
        Objects.requireNonNull(guard, "scope guard");
        Objects.requireNonNull(values, "complete source sequence");
        Objects.requireNonNull(keyExtractor, "lookup key extractor");
        guard.requireCurrent(scope);
        var slots = new ArrayList<Slot<K, T>>(values.size());
        Map<Key<K>, List<Slot<K, T>>> keyed = new LinkedHashMap<>();
        var identities = new IdentityHashMap<T, List<Slot<K, T>>>();
        int position = 0;
        for (T value : values) {
            Key<K> key = Objects.requireNonNull(keyExtractor.apply(value), "lookup key");
            var slot = new Slot<K, T>(position++, key, value);
            slots.add(slot);
            keyed.computeIfAbsent(key, ignored -> new ArrayList<>()).add(slot);
            identities.computeIfAbsent(value, ignored -> new ArrayList<>()).add(slot);
        }
        keyed.replaceAll((key, members) -> List.copyOf(members));
        identities.replaceAll((value, members) -> List.copyOf(members));
        guard.requireCurrent(scope);
        return new OrderedCandidateIndex<>(scope, guard, slots, keyed, identities);
    }

    /** The original list order, including repeated keys and repeated physical objects. */
    public List<Slot<K, T>> slots() { return checked(slots); }

    public List<Slot<K, T>> matching(Key<K> key) {
        Objects.requireNonNull(key, "lookup key");
        guard.requireCurrent(scope);
        return checked(keyed.getOrDefault(key, List.of()));
    }

    /** Identity lookup deliberately avoids equals/hashCode on possibly cyclic source values. */
    public List<Slot<K, T>> sameObject(T original) {
        guard.requireCurrent(scope);
        return checked(identities.getOrDefault(original, List.of()));
    }

    public Optional<Slot<K, T>> first(Key<K> key) {
        List<Slot<K, T>> matching = matching(key);
        return checked(matching.isEmpty() ? Optional.empty() : Optional.of(matching.getFirst()));
    }

    /** A derived complete view. Equal ranks retain source position; base slots are never changed. */
    public List<Slot<K, T>> ordered(Comparator<? super T> comparator) {
        Objects.requireNonNull(comparator, "domain ordering");
        guard.requireCurrent(scope);
        var ordered = new ArrayList<>(slots);
        ordered.sort((left, right) -> {
            int compared = comparator.compare(left.value(), right.value());
            return compared != 0 ? compared : Integer.compare(left.position(), right.position());
        });
        return checked(List.copyOf(ordered));
    }

    /** Keep the owner's current-scope check around a whole pure consumer operation. */
    public <R> R use(Function<? super OrderedCandidateIndex<S, K, T>, ? extends R> consumer) {
        Objects.requireNonNull(consumer, "pure index consumer");
        guard.requireCurrent(scope);
        try {
            return consumer.apply(this);
        } finally {
            guard.requireCurrent(scope);
        }
    }

    private <R> R checked(R value) {
        guard.requireCurrent(scope);
        return value;
    }
}
