package org.xar.ck3.control.wave2.finance.feastcounters;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;

/** The four native actor counters and their pure before/after observation subtree. */
public record OutcomeCounterValues(Optional<Long> prestigeRaw, Optional<Integer> stressPoints,
                                   Presence revelerPresent, Optional<Long> revelerXpRaw) {
    public OutcomeCounterValues {
        Objects.requireNonNull(prestigeRaw, "prestigeRaw"); Objects.requireNonNull(stressPoints, "stressPoints");
        Objects.requireNonNull(revelerPresent, "revelerPresent"); Objects.requireNonNull(revelerXpRaw, "revelerXpRaw");
    }
    public enum Presence { UNKNOWN, ABSENT, PRESENT }
    public record Delta(Optional<BigInteger> prestigeRaw, Optional<BigInteger> stressPoints, Optional<BigInteger> revelerXpRaw) {
        public Delta { Objects.requireNonNull(prestigeRaw); Objects.requireNonNull(stressPoints); Objects.requireNonNull(revelerXpRaw); }
    }
    public record PresenceTransition(boolean before, boolean after) { }
    public record Observed(boolean prestigeRaw, boolean stressPoints, boolean revelerPresent, boolean revelerXpRaw) { }

    /** The source consumer normalizes an absent/null counter group to four unknown observations. */
    public static OutcomeCounterValues unknown() {
        return new OutcomeCounterValues(Optional.empty(), Optional.empty(), Presence.UNKNOWN, Optional.empty());
    }

    public record Projection(Optional<OutcomeCounterValues> before, Optional<OutcomeCounterValues> after) {
        public Projection { Objects.requireNonNull(before); Objects.requireNonNull(after); }
        public Projection(OutcomeCounterValues before, OutcomeCounterValues after) { this(Optional.of(before), Optional.of(after)); }
        public OutcomeCounterValues beforeValues() { return before.orElseGet(OutcomeCounterValues::unknown); }
        public OutcomeCounterValues afterValues() { return after.orElseGet(OutcomeCounterValues::unknown); }
        public Delta changes() {
            OutcomeCounterValues previous = beforeValues(); OutcomeCounterValues current = afterValues();
            return new Delta(difference(previous.prestigeRaw(), current.prestigeRaw()),
                    integerDifference(previous.stressPoints(), current.stressPoints()), difference(previous.revelerXpRaw(), current.revelerXpRaw()));
        }
        public Optional<PresenceTransition> presenceTransition() {
            Presence previous = beforeValues().revelerPresent(); Presence current = afterValues().revelerPresent();
            if (previous == Presence.UNKNOWN || current == Presence.UNKNOWN) return Optional.empty();
            return Optional.of(new PresenceTransition(previous == Presence.PRESENT, current == Presence.PRESENT));
        }
        public Observed observed() {
            OutcomeCounterValues current = afterValues();
            return new Observed(current.prestigeRaw().isPresent(), current.stressPoints().isPresent(),
                    current.revelerPresent() != Presence.UNKNOWN, current.revelerXpRaw().isPresent());
        }
    }

    private static Optional<BigInteger> difference(Optional<Long> before, Optional<Long> after) {
        if (before.isEmpty() || after.isEmpty()) return Optional.empty();
        return Optional.of(BigInteger.valueOf(after.orElseThrow()).subtract(BigInteger.valueOf(before.orElseThrow())));
    }
    private static Optional<BigInteger> integerDifference(Optional<Integer> before, Optional<Integer> after) {
        if (before.isEmpty() || after.isEmpty()) return Optional.empty();
        return Optional.of(BigInteger.valueOf(after.orElseThrow()).subtract(BigInteger.valueOf(before.orElseThrow())));
    }
}
