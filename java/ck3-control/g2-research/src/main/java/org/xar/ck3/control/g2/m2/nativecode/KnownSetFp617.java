package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.SlotReserveWithFp615;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Narrowly scoped actual SET FP factory for the 1ACE015/4226F10 edge.
 * Reuses supplied PendingSlotCapacityKnownSet412 and SlotReserveWithFp615 contracts.
 */
public final class KnownSetFp617 {
    private KnownSetFp617() { }

    /**
     * Wrapper for a tail call frame carrying the original 412 TailFrame and pre-call MXCSR state.
     */
    public record TailCall(PendingSlotCapacityFullState412Api.TailFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public TailCall {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Functional interface for handling unknown SET tails in the FP context.
     */
    @FunctionalInterface
    public interface TailCalls {
        QueueFp604Api.Outcome tail(TailCall frame);
    }

    /**
     * Private exception used to propagate the Outcome from a tail call back to the invoke handler.
     */
    private static final class TailOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Outcome outcome;

        TailOutcomeException(QueueFp604Api.Outcome outcome) {
            this.outcome = outcome;
        }
    }

    /**
     * Binds a SlotReserveWithFp615.Calls handler that routes the specific SET edge to the known binder
     * and delegates all other calls to the foreign handler.
     */
    public static SlotReserveWithFp615.Calls bind(
            SlotReserveWithFp615.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            TailCalls unknownSetTails,
            SlotReserveWithFp615.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(unknownSetTails);
        Objects.requireNonNull(foreign);

        return new SlotReserveWithFp615.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(SlotReserveWithFp615.CallFrame fpFrame) {
                Objects.requireNonNull(fpFrame);
                PendingSlotCapacityFullState412Api.CallFrame original = fpFrame.original();
                QueueFp604Api.Mxcsr preMxcsr = fpFrame.preMxcsr();

                // Match ONLY original 412 call site 1ACE015 / kind DIRECT_RVA / target 4226F10
                if (original.call().callSiteRva() == 0x1ACE015L
                        && original.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.call().targetBits() == 0x4226F10L) {

                    // Reuse supplied exact PendingSlotCapacityKnownSet412.bind
                    PendingSlotCapacityFullState412Api.Calls knownSetCalls = PendingSlotCapacityKnownSet412.bind(
                            memory, budget, new PendingSlotCapacityFullState412Api.Calls() {
                                @Override
                                public PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotCapacityFullState412Api.CallFrame frame) {
                                    throw new UnsupportedOperationException("206 has no CALL instructions");
                                }

                                @Override
                                public PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotCapacityFullState412Api.TailFrame frame) {
                                    // Reached only for UNKNOWN 206 tail
                                    QueueFp604Api.Outcome outcome = unknownSetTails.tail(new TailCall(frame, preMxcsr));
                                    if (outcome == null) {
                                        throw new NullPointerException("Null outcome from unknownSetTails");
                                    }
                                    throw new TailOutcomeException(outcome);
                                }

                                @Override
                                public long readGsQword58() {
                                    throw new UnsupportedOperationException("GS read not expected in 206");
                                }
                            });

                    try {
                        // Execute the known binder once
                        PendingSlotCapacityFullState412Api.CallResult result = knownSetCalls.invoke(original);

                        // Validate against the original frame
                        original.checkNormalReturn(result);

                        // Wrap in Normal with SAME preMxcsr
                        return new QueueFp604Api.Normal(
                                new FullCopy437Api.CallResult(result.normalReturn(), result.postDirectionFlagSet()),
                                preMxcsr);
                    } catch (TailOutcomeException e) {
                        // Return the exact Outcome from the tail call unchanged
                        QueueFp604Api.Outcome outcome = e.outcome;
                        if (outcome instanceof QueueFp604Api.Normal normal) {
                            // Preserve original CALL guard for unknown-tail Normal
                            original.checkNormalReturn(new PendingSlotCapacityFullState412Api.CallResult(
                                    normal.base().normalReturn(),
                                    normal.base().postDirectionFlagSet()));
                        }
                        return outcome;
                    }
                }

                // Nonmatches go ONCE to foreign.invoke(the EXACT SAME 615.CallFrame)
                QueueFp604Api.Outcome outcome = foreign.invoke(fpFrame);
                if (outcome == null) {
                    throw new NullPointerException("Null outcome from foreign");
                }
                return outcome;
            }
        };
    }
}