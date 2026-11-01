package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownEmbeddedInit560;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedVector565Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedVectorFullState260E040;
import java.util.Objects;

/** Composition of the actual 373ADAE call with the full-state 260E040 implementation. */
public final class ContextConstructorWithKnownEmbeddedVector574 {
    private ContextConstructorWithKnownEmbeddedVector574() { }

    @FunctionalInterface
    public interface VectorCalls {
        FullCopy437Api.CallResult invoke(FullCopy437Api.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget, EmbeddedVector565Api.CallFrame frame);
    }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input, FullCopy437Api.Memory memory, ContextConstructor543Api.Calls fallback, ContextConstructorWithKnownEmbeddedInit560.EmbeddedCalls embedded, VectorCalls vector) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(embedded);
        Objects.requireNonNull(vector);

        // Create a combined Calls implementation that routes the specific site to the embedded vector
        // and all other sites to the fallback.
        ContextConstructor543Api.Calls combinedCalls = new ContextConstructor543Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(ContextConstructor543Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                long site = frame.call().callSiteRva();

                // Check if this is the known embedded vector call site
                if (site == 0x373ADAE
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x260E040L) {

                    // Construct the Input for the child embedded vector execution
                    // Input437 requires: Entry, boolean directionFlagSet, LoopBudget
                    // We use the frame's childEntry, directionFlagSet, and the original input's budget
                    FullCopy437Api.Input childInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Create the Calls closure for the embedded vector
                    // It must bind the original memory and budget to the vector.invoke
                    EmbeddedVector565Api.Calls vectorCalls = new EmbeddedVector565Api.Calls() {
                        @Override
                        public FullCopy437Api.CallResult invoke(EmbeddedVector565Api.CallFrame innerFrame) {
                            Objects.requireNonNull(innerFrame);
                            // Delegate to the provided vector interface with the original memory and budget
                            return vector.invoke(memory, input.budget(), innerFrame);
                        }
                    };

                    // Execute the embedded vector logic
                    FullCopy437Api.CallResult result = EmbeddedVectorFullState260E040.execute(childInput, memory, vectorCalls);

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
        return ContextConstructorWithKnownEmbeddedInit560.execute(input, memory, combinedCalls, embedded);
    }
}