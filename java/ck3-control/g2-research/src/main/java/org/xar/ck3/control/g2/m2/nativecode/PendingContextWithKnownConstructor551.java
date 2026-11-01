package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullContext493Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorFullState373ACF0;
import java.util.Objects;

/**
 * Thin composition class for the 262-byte context copy 3076B60.
 * Handles the two specific calls to 373ACF0 by delegating to ContextConstructorFullState373ACF0,
 * while passing all other calls to the fallback.
 */
public final class PendingContextWithKnownConstructor551 {
    private PendingContextWithKnownConstructor551() { }

    public interface ConstructorCalls {
        FullCopy437Api.CallResult invoke(FullContext493Api.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget, ContextConstructor543Api.CallFrame frame);
    }

    public static FullCopy437Api.CallResult execute(FullContext493Api.Input input, FullContext493Api.Memory memory, FullContext493Api.Calls fallback, ConstructorCalls constructors) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(constructors);

        // Create a combined Calls implementation that routes the two specific sites to the constructor
        // and all other sites to the fallback.
        FullContext493Api.Calls combinedCalls = new FullContext493Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(FullContext493Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                long site = frame.call().callSiteRva();

                // Check if this is one of the two known constructor call sites
                if ((site == 0x3076B8CL || site == 0x3076BA0L)
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x373ACF0L) {
                    // Construct the Input for the child constructor execution
                    // Input437 requires: Entry, boolean directionFlagSet, LoopBudget
                    // We use the frame's childEntry, directionFlagSet, and the original input's budget
                    FullCopy437Api.Input childInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Create the Calls closure for the constructor
                    // It must bind the original memory and budget to the constructors.invoke
                    ContextConstructor543Api.Calls constructorCalls = new ContextConstructor543Api.Calls() {
                        @Override
                        public FullCopy437Api.CallResult invoke(ContextConstructor543Api.CallFrame innerFrame) {
                            Objects.requireNonNull(innerFrame);
                            // Delegate to the provided constructors interface with the original memory and budget
                            return constructors.invoke(memory, input.budget(), innerFrame);
                        }
                    };

                    // Execute the constructor logic
                    FullCopy437Api.CallResult result = ContextConstructorFullState373ACF0.execute(childInput, memory, constructorCalls);

                    // Validate the result against the outer frame expectations
                    frame.checkNormalReturn(result);

                    return result;
                } else {
                    // For all other call sites, use the fallback
                    return fallback.invoke(frame);
                }
            }
        };

        // Run the existing mature context copy implementation exactly once
        return PendingContextCopyFullState3076B60.execute(input, memory, combinedCalls);
    }
}