package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.FullPage495Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Real new root CALL2 consumer edge for PendingSlotProducerWithKnownPageContextAndInit528.
 * Installs the exact full Page2A321F0 implementation on the existing Context/Init composition.
 * Does not implement Page/Context/Init algorithms or duplicate caller logic.
 */
public final class PendingSlotProducerWithKnownPageContextAndInit528 {
    private PendingSlotProducerWithKnownPageContextAndInit528() { }

    public interface Memory extends PendingSlotProducerWithKnownContextAndInit521.Memory, FullPage495Api.Memory { }

    public interface PageCalls {
        FullCopy437Api.CallResult invoke(
            Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            FullPage495Api.CallFrame frame
        );
    }

    public static FullCopy437Api.CallResult execute(
            FullSlotProducer479Api.Input input,
            Memory memory,
            FullSlotProducer479Api.Calls fallback,
            PendingSlotProducerWithKnownContextAndInit521.ContextCalls contextCalls,
            PageCalls pageCalls) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(contextCalls);
        Objects.requireNonNull(pageCalls);

        // Create invocation-local Calls bound to the exact same memory and budget.
        FullSlotProducer479Api.Calls combinedCalls = new FullSlotProducer479Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(FullSlotProducer479Api.CallFrame frame) {
                // Select only the exact Page call site.
                if (frame.call().callSiteRva() == 0x2A327E7L &&
                    frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    frame.call().targetBits() == 0x2A321F0L) {

                    // Construct the Input for the nested Page execution using the child entry
                    // and the current direction flag from the frame.
                    FullPage495Api.Input pageInput = new FullPage495Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Create nested Calls that delegate to the provided PageCalls.
                    FullPage495Api.Calls nestedPageCalls = new FullPage495Api.Calls() {
                        @Override
                        public FullCopy437Api.CallResult invoke(FullPage495Api.CallFrame innerFrame) {
                            return pageCalls.invoke(memory, input.budget(), innerFrame);
                        }
                    };

                    // Execute the existing full-state Page exactly once with the SAME memory.
                    FullCopy437Api.CallResult result = PendingPageReserveFullState2A321F0.execute(
                        pageInput,
                        memory,
                        nestedPageCalls
                    );

                    // Validate the result against the frame expectations.
                    frame.checkNormalReturn(result);

                    return result;
                }

                // All other invokes go to the fallback.
                return fallback.invoke(frame);
            }
        };

        // Execute the full-state producer with known context/init exactly once with combined Calls.
        FullCopy437Api.CallResult result = PendingSlotProducerWithKnownContextAndInit521.execute(
            input,
            memory,
            combinedCalls,
            contextCalls
        );

        return result;
    }
}