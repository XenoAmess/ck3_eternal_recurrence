package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.FullSlotProducer479Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Thin composition consumer for the 2A328D0 initializer edge.
 * Installs the mature full-state initializer on the same strong Memory and budget,
 * then executes the full-state producer with combined Calls.
 */
public final class PendingSlotProducerWithKnownInit497 {
    private PendingSlotProducerWithKnownInit497() { }

    public static FullCopy437Api.CallResult execute(
            FullSlotProducer479Api.Input input,
            FullSlotProducer479Api.Memory memory,
            FullSlotProducer479Api.Calls fallback) {

        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);

        // Create invocation-local Calls bound to the exact same memory and budget.
        FullSlotProducer479Api.Calls combinedCalls = new FullSlotProducer479Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(FullSlotProducer479Api.CallFrame frame) {
                // Select only the exact initializer call site.
                if (frame.call().callSiteRva() == 0x2A328D0L &&
                    frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    frame.call().targetBits() == 0x2756120L) {

                    // Construct the Input for the nested initializer execution using the child entry
                    // and the current direction flag from the frame.
                    FullCopy437Api.Input initInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Execute the existing full-state initializer exactly once with the SAME memory.
                    FullCopy437Api.CallResult result = PendingComponentInitFullState2756120.execute(
                        initInput,
                        memory
                    );

                    // Validate the result against the frame expectations.
                    frame.checkNormalReturn(result);

                    return result;
                }

                // All other invokes go to the fallback.
                return fallback.invoke(frame);
            }
        };

        // Execute the full-state producer exactly once with combined Calls.
        FullCopy437Api.CallResult result = PendingSlotProducerFullState2A32770.execute(
            input,
            memory,
            combinedCalls
        );

        return result;
    }
}