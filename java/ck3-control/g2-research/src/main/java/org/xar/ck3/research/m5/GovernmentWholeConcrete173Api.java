package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentLookup167Api;

/** Mechanical contract for new thin owned-memory assembly; no live Native/Game claim. */
public final class GovernmentWholeConcrete173Api {
    private GovernmentWholeConcrete173Api() { }

    /** One object: Whole phases, M0 full193 and M1 full193 share all byte/atomic effects. */
    public interface Memory extends GovernmentWhole4798Api.Memory,
            GovernmentFull193Composition168Api.Memory { }

    /**
     * The two MXCSR observations name the actual INNER hash input points, not callee entry,
     * afterInitial, lookup output or final Whole state. They are owned software inputs;
     * this assembly does not claim a Native observation producer. A supplied observation
     * must apply to every corresponding dynamic invocation in this execution.
     * Unavailable stops before that outer concrete call's push or execution. No default
     * is inferred, and no effects of the unexecuted concrete call are claimed.
     * Primary lookup's hash already receives actual CallFrame.mxcsr via the existing binder.
     */
    public record DeepInputs(
            GovernmentWhole4798Api.MxcsrObservation m0HashMxcsrAt2D0B4FE,
            GovernmentWhole4798Api.MxcsrObservation m1HashMxcsrAt2D1B85E,
            GovernmentByteUpdate169Api.LoopBudget m0HashBudget,
            GovernmentLookup167Api.SpinBudget m0LookupBudget,
            GovernmentResult168Api.WorkBudget m0ResultBudget,
            GovernmentByteUpdate169Api.LoopBudget m1HashBudget,
            GovernmentLookup167Api.SpinBudget m1LookupBudget,
            GovernmentResult168Api.WorkBudget m1ResultBudget,
            GovernmentByteUpdate169Api.LoopBudget primaryHashBudget) {
        public DeepInputs {
            Objects.requireNonNull(m0HashMxcsrAt2D0B4FE);
            Objects.requireNonNull(m1HashMxcsrAt2D1B85E);
            Objects.requireNonNull(m0HashBudget); Objects.requireNonNull(m0LookupBudget);
            Objects.requireNonNull(m0ResultBudget); Objects.requireNonNull(m1HashBudget);
            Objects.requireNonNull(m1LookupBudget); Objects.requireNonNull(m1ResultBudget);
            Objects.requireNonNull(primaryHashBudget);
        }
    }
}
