package org.xar.ck3.research.m5;

import java.util.Objects;

/** Owned normal composition contract for held4798B; no live capture, Native ABI or Game claim. */
public final class GovernmentWhole4798Api {
    private GovernmentWhole4798Api() { }
    /** One byte-addressed object for all phases and concrete/opaque callee effects. */
    public interface Memory extends GovernmentInitialFrame162Api.Memory,
            GovernmentLookupLoop580Api.Memory, GovernmentPrimarySuffix155Api.Memory { }
    public sealed interface MxcsrObservation permits AvailableMxcsr, UnavailableMxcsr { }
    public record AvailableMxcsr(GovernmentLookupLoop580Api.Mxcsr32 bits) implements MxcsrObservation {
        public AvailableMxcsr { Objects.requireNonNull(bits); }
    }
    public record UnavailableMxcsr(String reason) implements MxcsrObservation {
        public UnavailableMxcsr { Objects.requireNonNull(reason); }
    }
    /**
     * Nonmutating owned software observations, not instructions or a proven capture producer.
     * afterInitial must observe the actual executed Join; unavailable stops before lookup.
     * afterNormalReturn independently observes the completed Middle result. Its unavailable value
     * remains explicit in Result. No default/entry/lookup MXCSR is an implicit final observation.
     */
    public interface MxcsrBoundary {
        MxcsrObservation afterInitial(GovernmentInitialFrame162Api.Join actualJoin);
        MxcsrObservation afterNormalReturn(GovernmentMiddle166Api.Result actualResult);
    }
    public static final class MxcsrUnavailableException extends UnsupportedOperationException {
        private static final long serialVersionUID=1L;
        public MxcsrUnavailableException(String reason) { super(reason); }
    }
    public record Calls(GovernmentInitialFrame162Api.Calls initial,
            GovernmentLookupLoop580Api.Calls lookup, GovernmentPrimaryTail155Api.Calls ordinary,
            InternedLookup155Api.Calls lookup155, GovernmentCaller153Api.Calls prefix153,
            GovernmentPrimarySuffix155Api.VolatileBoundary post153) {
        public Calls { Objects.requireNonNull(initial);Objects.requireNonNull(lookup);
            Objects.requireNonNull(ordinary);Objects.requireNonNull(lookup155);
            Objects.requireNonNull(prefix153);Objects.requireNonNull(post153); }
    }
    public record Budgets(GovernmentInitialFrame162Api.LoopBudget initial,
            GovernmentLookupLoop580Api.LoopBudget lookup, GovernmentEarlierRows161Api.LoopBudget earlier,
            GovernmentPrimaryTail155Api.LoopBudget rows, GovernmentCompaction160Api.Loops compaction,
            GovernmentPrimaryTail155Api.LoopBudget tail) {
        public Budgets { Objects.requireNonNull(initial);Objects.requireNonNull(lookup);
            Objects.requireNonNull(earlier);Objects.requireNonNull(rows);
            Objects.requireNonNull(compaction);Objects.requireNonNull(tail); }
    }
    /** Real executed component results. Middle normalReturn reports RAX/RIP/RSP/NV only, not full final V. */
    public record Result(GovernmentInitialFrame162Api.Join initialJoin, AvailableMxcsr afterInitialMxcsr,
            GovernmentLookupLoop580Api.Join lookupJoin, GovernmentEarlierRows161Api.Join earlierJoin,
            GovernmentRows461Api.Join rowsJoin, GovernmentMiddle166Api.Result middleResult,
            MxcsrObservation finalMxcsr) {
        public Result { Objects.requireNonNull(initialJoin);Objects.requireNonNull(afterInitialMxcsr);
            Objects.requireNonNull(lookupJoin);Objects.requireNonNull(earlierJoin);Objects.requireNonNull(rowsJoin);
            Objects.requireNonNull(middleResult);Objects.requireNonNull(finalMxcsr); }
    }
}
