package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Source-scoped thin carrier/binding for the complete 133 PendingSlotArrayReserveFullState1ACE4B0.
 * Reuses the exact existing producer; no copying or reimplementing its GPR/stack/CALL/RET algorithm.
 * Scoped ONLY to actual complete133. No claim runtime loading, unknownallocator/freebody/currentNativeMXCSR/CPUOS/Native172samecall16+4/Game/performance.
 */
public final class SlotReserveWithFp615 {
    private SlotReserveWithFp615() { }

    /**
     * Union of memory interfaces required for the full state execution.
     * Ensures all operations address the same shared byte storage.
     */
    public interface Memory extends PendingSlotCapacityFullState412Api.Memory, FullCopy437Api.Memory {
    }

    /**
     * Input wrapper carrying base 412 Input and explicit MXCSR.
     */
    public record Input(PendingSlotCapacityFullState412Api.Input base, QueueFp604Api.Mxcsr mxcsr) {
        public Input {
            Objects.requireNonNull(base);
            Objects.requireNonNull(mxcsr);
        }
    }

    /**
     * Call frame wrapper carrying original 412 CallFrame and pre-call MXCSR state.
     */
    public record CallFrame(PendingSlotCapacityFullState412Api.CallFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public CallFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Functional interface for handling calls in the 133 context.
     */
    @FunctionalInterface
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }

    /**
     * Private exception used to propagate the Stopped outcome from a callback back to execute.
     * This allows the bridge to intercept the stop and return the Outcome directly without
     * manufacturing a legacy normal return or processing continuation.
     */
    private static final class StoppedOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;

        StoppedOutcomeException(QueueFp604Api.Stopped outcome) {
            this.outcome = outcome;
        }
    }

    /**
     * Executes the 133 logic with FP awareness.
     * @param input The FP input containing the base PendingSlotCapacityFullState412Api.Input and MXCSR state.
     * @param memory The owned memory view.
     * @param otherCalls The handler for non-COPY calls (allocator/free).
     * @param copyTails The handler for COPY tails (FullCopyWithFp613.TailCalls).
     * @return The Outcome (Normal or Stopped) resulting from the execution.
     */
    public static QueueFp604Api.Outcome execute(Input input, Memory memory, Calls otherCalls, FullCopyWithFp613.TailCalls copyTails) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(otherCalls);
        Objects.requireNonNull(copyTails);

        // Isolated local MXCSR holder for EACH execute, initialized to the SAME input.mxcsr object.
        // Never global/shared across executions and never widen unknown bits or fill default1F80.
        final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
        currentMxcsrHolder[0] = input.mxcsr();

        // Narrow 412.Calls implementation that handles the specific COPY edge and delegates others.
        PendingSlotCapacityFullState412Api.Calls narrowCalls = new PendingSlotCapacityFullState412Api.Calls() {
            @Override
            public PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotCapacityFullState412Api.CallFrame frame) {
                // Only original.call.callSiteRva 1ACE4FC / kind DIRECT_RVA / target 4226860 selects supplied actual FullCopyWithFp613.execute ONCE.
                if (frame.call().callSiteRva() == 0x1ACE4FCL
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x4226860L) {

                    // Build its 604.Input with 437.Input(original.childEntry, original.directionFlagSet, ORIGINAL input.base.budget) and the CURRENT localMxcsr.
                    FullCopy437Api.Input copyInput = new FullCopy437Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            input.base().budget()
                    );
                    QueueFp604Api.Input fpInput = new QueueFp604Api.Input(copyInput, currentMxcsrHolder[0]);

                    // Pass the SAME Memory and supplied copyTails.
                    QueueFp604Api.Outcome outcome = FullCopyWithFp613.execute(fpInput, memory, copyTails);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        // Store its SAME postMxcsr object as localcurrentstate.
                        currentMxcsrHolder[0] = normal.postMxcsr();
                        // Convert only its structural CallResult to a new 412.CallResult using the SAME 185.NormalReturn object and offered postDF.
                        return new PendingSlotCapacityFullState412Api.CallResult(
                                normal.base().normalReturn(),
                                normal.base().postDirectionFlagSet()
                        );
                    } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                        // Abort immediately to execute's outer boundary.
                        throw new StoppedOutcomeException(stopped);
                    } else {
                        throw new NullPointerException("Null callback outcome");
                    }
                }

                // All other actual 133 calls go once to otherCalls.invoke(new CallFrame(the EXACT original 412frame, SAME currentMxcsr)).
                CallFrame wrappedFrame = new CallFrame(frame, currentMxcsrHolder[0]);
                QueueFp604Api.Outcome outcome = otherCalls.invoke(wrappedFrame);

                if (outcome instanceof QueueFp604Api.Normal normal) {
                        // Store its SAME postMxcsr object as localcurrentstate.
                        currentMxcsrHolder[0] = normal.postMxcsr();
                    // Convert only its structural CallResult to a new 412.CallResult using the SAME 185.NormalReturn object and offered postDF.
                    return new PendingSlotCapacityFullState412Api.CallResult(
                            normal.base().normalReturn(),
                            normal.base().postDirectionFlagSet()
                    );
                } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                    // Abort immediately to execute's outer boundary.
                    throw new StoppedOutcomeException(stopped);
                } else {
                    throw new NullPointerException("Null callback outcome");
                }
            }

            @Override
            public PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotCapacityFullState412Api.TailFrame frame) {
                // Unused 412.tail port explicitly throws if unexpectedly reached: complete 133 has neither.
                throw new UnsupportedOperationException("Tail not expected in complete 133");
            }

            @Override
            public long readGsQword58() {
                // Unused 412.readGsQword58 port explicitly throws if unexpectedly reached: complete 133 has neither.
                throw new UnsupportedOperationException("GS read not expected in complete 133");
            }
        };

        try {
            // Run PendingSlotArrayReserveFullState1ACE4B0.execute(input.base(), SAME memory, a narrow 412.Calls).
            PendingSlotCapacityFullState412Api.CallResult result = PendingSlotArrayReserveFullState1ACE4B0.execute(
                    input.base(),
                    memory,
                    narrowCalls
            );

            // On known normal whole completion, wrap its exact 133 NormalReturn/postDF into 437.CallResult and 604.Normal with the current postMxcsr object.
            FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                    result.normalReturn(),
                    result.postDirectionFlagSet()
            );
            return new QueueFp604Api.Normal(baseResult, currentMxcsrHolder[0]);
        } catch (StoppedOutcomeException e) {
            // Return the EXACT same Stopped object, without manufacturing a legacy normal, processing old 133 continuation/free/header publish/epilogue, restoring any register/Memory, or resetting FP.
            return e.outcome;
        }
    }
}