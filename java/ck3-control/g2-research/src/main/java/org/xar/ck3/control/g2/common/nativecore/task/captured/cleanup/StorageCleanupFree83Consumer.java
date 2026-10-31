package org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup;

import java.util.Objects;
import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Candidate;

/** Source-bound Java consumer of held856050 and the free83 port. No Native memory or Game API. */
public final class StorageCleanupFree83Consumer {
    public enum Completion {
        RESET_INLINE,
        RESET_AFTER_CALLEE_RETURN,
        NEEDS_POINTER,
        NEEDS_BACK_REFERENCE,
        REJECTED_HEADER_UNEXECUTED
    }

    /** One owned callback for each literal normal-path store relative to D=C+98. */
    @FunctionalInterface
    public interface ResetSink {
        void store(int offsetFromD, int byteWidth, long valueBits);
    }

    /** Completion describes this owned Java port execution; it does not claim heap ownership/free success. */
    public record Outcome(Completion completion, InlineStorageCleanupPlan.Plan plan) {
        public Outcome {
            Objects.requireNonNull(completion, "completion");
            Objects.requireNonNull(plan, "plan");
        }
    }

    private StorageCleanupFree83Consumer() { }

    /**
     * Compose the existing cleanup plan and free83 port. First derive exactly one Plan using the existing plan method.
     * Inputs are explicit raw observations, with heapHandleRaw the externally supplied QWORD[5C5DE30].
     * No read, alias ownership, original heap availability, exception/EH or current Game claim is made.
     *
     * INLINE calls no free port, ignores the observations as the plan dictates, then emits the existing
     * three normalResetValues() in list order and returns RESET_INLINE with the original Plan.
     * NEEDS_POINTER / NEEDS_BACK_REFERENCE return their corresponding Completion and original Plan;
     * they make zero free calls and zero reset stores. calls/resetSink may be null on these paths.
     * REJECTED_HEADER returns REJECTED_HEADER_UNEXECUTED with no free/reset call: the actual separate
     * 4232A70+INT3 branch is deliberately outside this component, not implemented as normal completion.
     *
     * DIRECT_CALL and ADJUSTED_CALL call M4 Free83Candidate.release exactly once with the Plan's
     * present RCX bits as blockRaw, heapHandleRaw and calls. Do not pass original RDX/R8/size as flags
     * or block: 424E364 overwrites EDX=0 and sets R8=entry RCX. M4 alone owns free83 algorithm.
     * After release returns normally, emit the same three existing reset descriptors, then return
     * RESET_AFTER_CALLEE_RETURN with the original Plan. A failed HeapFree can still return normally
     * after mapper/captured-cell effects: never gate the resets on success. A known blockRaw==0 may
     * use calls==null; release makes no callbacks and the three resets still occur.
     *
     * resetSink is nonnull on paths that emit stores. Calls obey the frozen M4 protocol: ordinary
     * callbacks and nonnull failure Cell32. Do not catch/suppress exceptions or perform reset in a
     * finally block; this preserves Java port sequencing and grants no original Native EH contract.
     * No added capacity/null-pointer/heap/overflow/ownership guard; unknown observations stay unknown.
     */
    public static Outcome cleanup(long capacityBits, OptionalLong heapPointerBits,
            OptionalLong backReferenceBits, long heapHandleRaw, Calls calls, ResetSink resetSink) {
        InlineStorageCleanupPlan.Plan plan = InlineStorageCleanupPlan.plan(capacityBits, heapPointerBits, backReferenceBits);

        switch (plan.path()) {
            case InlineStorageCleanupPlan.Path.INLINE:
                emitResets(resetSink);
                return new Outcome(Completion.RESET_INLINE, plan);

            case InlineStorageCleanupPlan.Path.NEEDS_POINTER:
                return new Outcome(Completion.NEEDS_POINTER, plan);

            case InlineStorageCleanupPlan.Path.NEEDS_BACK_REFERENCE:
                return new Outcome(Completion.NEEDS_BACK_REFERENCE, plan);

            case InlineStorageCleanupPlan.Path.REJECTED_HEADER:
                return new Outcome(Completion.REJECTED_HEADER_UNEXECUTED, plan);

            case InlineStorageCleanupPlan.Path.DIRECT_CALL:
            case InlineStorageCleanupPlan.Path.ADJUSTED_CALL:
                long blockRaw = plan.rcxBits().getAsLong();
                Free83Candidate.release(blockRaw, heapHandleRaw, calls);
                emitResets(resetSink);
                return new Outcome(Completion.RESET_AFTER_CALLEE_RETURN, plan);

            default:
                throw new IllegalStateException("unhandled plan path");
        }
    }

    private static void emitResets(ResetSink resetSink) {
        for (InlineStorageCleanupPlan.RelativeReset r : InlineStorageCleanupPlan.normalResetValues()) {
            resetSink.store(r.offsetFromD(), r.byteWidth(), r.valueBits());
        }
    }
}