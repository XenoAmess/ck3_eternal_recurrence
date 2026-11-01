package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorFullState373ACF0;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInit550Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInitFullState8895D0;
import java.util.Objects;

/**
 * Thin composition class for the 233-byte context constructor 373ACF0.
 * Handles the specific call to 8895D0 by delegating to EmbeddedInitFullState8895D0,
 * while passing all other calls to the fallback.
 */
public final class ContextConstructorWithKnownEmbeddedInit560 {
    private ContextConstructorWithKnownEmbeddedInit560() { }

    @FunctionalInterface
    public interface EmbeddedCalls {
        FullCopy437Api.CallResult invoke(FullCopy437Api.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget, EmbeddedInit550Api.CallFrame frame);
    }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input, FullCopy437Api.Memory memory, ContextConstructor543Api.Calls fallback, EmbeddedCalls embedded) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(embedded);

        // Create a combined Calls implementation that routes the specific site to the embedded init
        // and all other sites to the fallback.
        ContextConstructor543Api.Calls combinedCalls = new ContextConstructor543Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(ContextConstructor543Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                long site = frame.call().callSiteRva();

                // Check if this is the known embedded init call site
                if (site == 0x373AD20L
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x8895D0L) {

                    // Construct the Input for the child embedded init execution
                    // Input437 requires: Entry, boolean directionFlagSet, LoopBudget
                    // We use the frame's childEntry, directionFlagSet, and the original input's budget
                    FullCopy437Api.Input childInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Create the Calls closure for the embedded init
                    // It must bind the original memory and budget to the embedded.invoke
                    EmbeddedInit550Api.Calls embeddedCalls = new EmbeddedInit550Api.Calls() {
                        @Override
                        public FullCopy437Api.CallResult invoke(EmbeddedInit550Api.CallFrame innerFrame) {
                            Objects.requireNonNull(innerFrame);
                            // Delegate to the provided embedded interface with the original memory and budget
                            return embedded.invoke(memory, input.budget(), innerFrame);
                        }
                    };

                    // Execute the embedded init logic
                    FullCopy437Api.CallResult result = EmbeddedInitFullState8895D0.execute(childInput, memory, embeddedCalls);

                    // Validate the result against the outer frame expectations
                    frame.checkNormalReturn(result);

                    return result;
                } else {
                    // For all other call sites, use the fallback
                    return fallback.invoke(frame);
                }
            }
        };

        // Run the existing mature context constructor implementation exactly once
        return ContextConstructorFullState373ACF0.execute(input, memory, combinedCalls);
    }
}