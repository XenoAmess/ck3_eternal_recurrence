package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Thin composition consumer for the 2A327CE growth edge.
 * Installs the mature full-state growth chain (470) on the same strong Memory and budget,
 * then executes the full-state producer with combined Calls.
 */
public final class PendingSlotProducerWithKnownGrowthPageContextAndInit540 {
    private PendingSlotProducerWithKnownGrowthPageContextAndInit540() { }

    public interface GrowthCalls {
        PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotProducerWithKnownPageContextAndInit528.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget, PendingSlotCapacityFullState412Api.CallFrame frame);
        PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotProducerWithKnownPageContextAndInit528.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget, PendingSlotCapacityFullState412Api.TailFrame frame);
        long readGsQword58(PendingSlotProducerWithKnownPageContextAndInit528.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget);
    }

    public static FullCopy437Api.CallResult execute(
            FullSlotProducer479Api.Input input,
            PendingSlotProducerWithKnownPageContextAndInit528.Memory memory,
            FullSlotProducer479Api.Calls fallback,
            PendingSlotProducerWithKnownContextAndInit521.ContextCalls contextCalls,
            PendingSlotProducerWithKnownPageContextAndInit528.PageCalls pageCalls,
            GrowthCalls growthCalls) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(contextCalls);
        Objects.requireNonNull(pageCalls);
        Objects.requireNonNull(growthCalls);

        // Create invocation-local Calls bound to the exact same memory and budget.
        FullSlotProducer479Api.Calls combinedCalls = new FullSlotProducer479Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(FullSlotProducer479Api.CallFrame frame) {
                // Select only the exact growth call site.
                if (frame.call().callSiteRva() == 0x2A327CEL &&
                    frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    frame.call().targetBits() == 0x1ACDFB0L) {

                    // Construct the Input for the nested growth execution using the child entry
                    // and the current direction flag from the frame.
                    PendingSlotCapacityFullState412Api.Input growthInput = new PendingSlotCapacityFullState412Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Build invocation-local 412Api.Calls forwarding to growthCalls.
                    PendingSlotCapacityFullState412Api.Calls nestedGrowthCalls = new PendingSlotCapacityFullState412Api.Calls() {
                        @Override
                        public PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotCapacityFullState412Api.CallFrame innerFrame) {
                            return growthCalls.invoke(memory, input.budget(), innerFrame);
                        }

                        @Override
                        public PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotCapacityFullState412Api.TailFrame innerFrame) {
                            return growthCalls.tail(memory, input.budget(), innerFrame);
                        }

                        @Override
                        public long readGsQword58() {
                            return growthCalls.readGsQword58(memory, input.budget());
                        }
                    };

                    // Execute the existing full-state growth chain exactly once with the SAME memory.
                    PendingSlotCapacityFullState412Api.CallResult result412 = PendingSlotCapacityWithKnownMemoryFullState470.execute(
                        growthInput,
                        memory,
                        nestedGrowthCalls
                    );

                    // Convert nominal carrier: preserve identical actual NormalReturn and postDF.
                    FullCopy437Api.CallResult convertedResult = new FullCopy437Api.CallResult(
                        result412.normalReturn(),
                        result412.postDirectionFlagSet()
                    );

                    // Validate the result against the frame expectations.
                    frame.checkNormalReturn(convertedResult);

                    return convertedResult;
                }

                // All other invokes go to the fallback.
                return fallback.invoke(frame);
            }
        };

        // Execute the full-state producer with known page/context/init exactly once with combined Calls.
        FullCopy437Api.CallResult result = PendingSlotProducerWithKnownPageContextAndInit528.execute(
            input,
            memory,
            combinedCalls,
            contextCalls,
            pageCalls
        );

        return result;
    }
}