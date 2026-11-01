package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Typed adapter for the 133 CALL 1ACE4FC direct 4226860 edge.
 * Bridges FullCopy437Api.Calls to PendingSlotCapacityFullState412Api.Calls.
 * Does not implement the copy algorithm or native execution.
 */
public final class PendingSlotCapacityKnownCopyFullState456 {
    private PendingSlotCapacityKnownCopyFullState456() { }

    /**
     * Strong nested Memory union of 412 and 437 views.
     * Ensures all operations address the same shared byte storage.
     */
    public interface Memory extends PendingSlotCapacityFullState412Api.Memory, FullCopy437Api.Memory {
    }

    /**
     * Binds the adapter to the provided memory, budget, and fallback calls.
     * Returns a Calls instance that handles the specific 4226860 edge.
     */
    public static PendingSlotCapacityFullState412Api.Calls bind(
            Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            PendingSlotCapacityFullState412Api.Calls fallback
    ) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(fallback);

        return new PendingSlotCapacityFullState412Api.Calls() {
            @Override
            public PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotCapacityFullState412Api.CallFrame frame) {
                if (frame.call().callSiteRva() == 0x1ACE4FCL
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x4226860L) {

                    FullCopy437Api.Input input = new FullCopy437Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            budget
                    );

                    FullCopy437Api.Calls calls437 = new FullCopy437Api.Calls() {
                        @Override
                        public FullCopy437Api.CallResult invoke(FullCopy437Api.CallFrame innerFrame) {
                            throw new UnsupportedOperationException("Source 4226860 has no CALL instructions");
                        }

                        @Override
                        public FullCopy437Api.CallResult tail(FullCopy437Api.TailFrame innerFrame) {
                            PendingSlotCapacityFullState412Api.TailFrame outerTailFrame = new PendingSlotCapacityFullState412Api.TailFrame(
                                    innerFrame.transfer(),
                                    innerFrame.directionFlagSet()
                            );

                            PendingSlotCapacityFullState412Api.CallResult outerResult = fallback.tail(outerTailFrame);

                            return new FullCopy437Api.CallResult(
                                    outerResult.normalReturn(),
                                    outerResult.postDirectionFlagSet()
                            );
                        }

                        @Override
                        public long readGsQword58() {
                            return fallback.readGsQword58();
                        }
                    };


                    FullCopy437Api.CallResult result437 = FullCopy4226860.execute(input, memory, calls437);

                    PendingSlotCapacityFullState412Api.CallResult convertedResult = new PendingSlotCapacityFullState412Api.CallResult(
                            result437.normalReturn(),
                            result437.postDirectionFlagSet()
                    );

                    frame.checkNormalReturn(convertedResult);

                    return convertedResult;
                }

                return fallback.invoke(frame);
            }

            @Override
            public PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotCapacityFullState412Api.TailFrame frame) {
                return fallback.tail(frame);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}