package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.FullContext493Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Thin composition consumer for the 2A328C4 context-copy edge.
 * Installs the mature full-state context copy on the same strong Memory and budget,
 * then executes the full-state producer with combined Calls.
 */
public final class PendingSlotProducerWithKnownContextAndInit521 {
    private PendingSlotProducerWithKnownContextAndInit521() { }

    public interface Memory extends FullSlotProducer479Api.Memory, FullContext493Api.Memory { }

    public interface ContextCalls {
        FullCopy437Api.CallResult invoke(Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget, FullContext493Api.CallFrame frame);
    }

    public static FullCopy437Api.CallResult execute(
            FullSlotProducer479Api.Input input,
            Memory memory,
            FullSlotProducer479Api.Calls fallback,
            ContextCalls contextCalls) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(contextCalls);

        // Create invocation-local Calls bound to the exact same memory and budget.
        FullSlotProducer479Api.Calls combinedCalls = new FullSlotProducer479Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(FullSlotProducer479Api.CallFrame frame) {
                // Select only the exact context-copy call site.
                if (frame.call().callSiteRva() == 0x2A328C4L &&
                    frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    frame.call().targetBits() == 0x3076B60L) {

                    // Construct the Input for the nested context execution using the child entry
                    // and the current direction flag from the frame.
                    FullContext493Api.Input contextInput = new FullContext493Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Create nested Calls that delegate to the provided ContextCalls.
                    FullContext493Api.Calls nestedCalls = new FullContext493Api.Calls() {
                        @Override
                        public FullCopy437Api.CallResult invoke(FullContext493Api.CallFrame innerFrame) {
                            return contextCalls.invoke(memory, input.budget(), innerFrame);
                        }
                    };

                    // Execute the existing full-state context copy exactly once with the SAME memory.
                    FullCopy437Api.CallResult result = PendingContextCopyFullState3076B60.execute(
                        contextInput,
                        memory,
                        nestedCalls
                    );

                    // Validate the result against the frame expectations.
                    frame.checkNormalReturn(result);

                    return result;
                }

                // All other invokes go to the fallback.
                return fallback.invoke(frame);
            }
        };

        // Execute the full-state producer with known init exactly once with combined Calls.
        FullCopy437Api.CallResult result = PendingSlotProducerWithKnownInit497.execute(
            input,
            memory,
            combinedCalls
        );

        return result;
    }
}