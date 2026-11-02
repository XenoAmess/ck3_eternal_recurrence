package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueue591Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppend597Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppendNonGrowthEntry599;

/**
 * Binding class for the known non-growth path of the embedded queue append.
 * It orchestrates the 103-byte function (3727EC0) using the actual producer,
 * but intercepts the specific call to 880340 to use the non-growth entry point.
 * All other calls are delegated to the provided opaque Calls interface.
 */
public final class EmbeddedQueueWithKnownNonGrowth600 {
    private EmbeddedQueueWithKnownNonGrowth600() { }

    /**
     * Nested public Memory extends BOTH EmbeddedQueue591Api.Memory and QueueAppend597Api.Memory.
     * These interfaces are nominal siblings; no wrapper or default implementation is provided.
     */
    public interface Memory extends EmbeddedQueue591Api.Memory, QueueAppend597Api.Memory {
    }

    /**
     * Executes the 103-byte function logic, routing the call to 0x880340 to the non-growth entry.
     */
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            Memory memory, EmbeddedQueue591Api.Calls otherCalls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(otherCalls);

        // Create an adapter that implements EmbeddedQueue591Api.Calls
        // It delegates to otherCalls for all sites EXCEPT 0x3727F0D (target 0x880340)
        EmbeddedQueue591Api.Calls adapter = new EmbeddedQueue591Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(EmbeddedQueue591Api.CallFrame frame) {
                // Check if this is the specific call site we want to intercept
                // The frame contains the call site RVA in frame.call().callSiteRva()
                if (frame.call().callSiteRva() == 0x3727F0DL) {
                    // Verify target is 0x880340 as per contract
                    if (frame.call().targetBits() != 0x880340L) {
                        throw new IllegalArgumentException("Unexpected target for intercepted call site");
                    }

                    // Build the Input for QueueAppendNonGrowthEntry599.execute
                    // We use the childEntry from the frame, the directionFlagSet from the frame,
                    // and the budget from the original input.
                    // The Memory object is the same one passed to this method.

                    // Construct FullCopy437Api.Input for the non-growth entry
                    // Note: QueueAppendNonGrowthEntry599.execute expects FullCopy437Api.Input
                    // and QueueAppend597Api.Memory.
                    // Our Memory interface extends QueueAppend597Api.Memory, so it is compatible.

                    FullCopy437Api.Input appendInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Execute the non-growth entry
                    // This may throw UnsupportedOperationException if growth is detected
                    return QueueAppendNonGrowthEntry599.execute(appendInput, memory);
                } else {
                    // Delegate all other calls to the provided otherCalls
                    return otherCalls.invoke(frame);
                }
            }
        };

        // Use the actual producer EmbeddedQueueFullState3727EC0.execute
        // It expects FullCopy437Api.Input, EmbeddedQueue591Api.Memory, and EmbeddedQueue591Api.Calls
        // Our Memory interface extends EmbeddedQueue591Api.Memory, so it is compatible.
        return EmbeddedQueueFullState3727EC0.execute(input, memory, adapter);
    }
}