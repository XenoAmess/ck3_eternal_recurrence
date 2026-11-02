package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownEmbeddedInit560;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownInitElementsVector580;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElements578Api;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Copy581Api;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32FullState3727180;

/**
 * Production composition combining known init, known elements, known vector, and known copy32.
 * Delegates to ContextConstructorWithKnownInitElementsVector580 for init/elements/vector handling,
 * while injecting the known copy32 handler for site 373ADBD.
 */
public final class ContextConstructorWithKnownFourEmbedded583 {
    private ContextConstructorWithKnownFourEmbedded583() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            ContextConstructor543Api.Calls fallback,
            ContextConstructorWithKnownEmbeddedInit560.EmbeddedCalls embedded,
            ContextConstructorWithKnownEmbeddedVector574.VectorCalls vector,
            EmbeddedElements578Api.Calls elements,
            Embedded32Copy581Api.Calls copy32) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(embedded);
        Objects.requireNonNull(vector);
        Objects.requireNonNull(elements);
        Objects.requireNonNull(copy32);

        // Create the hybrid calls that handles the specific copy32 site
        ContextConstructor543Api.Calls hybridCalls = bindCopy32(input, memory, fallback, copy32);

        // Execute the mature 580 composition (which handles init, elements, and vector) using the hybrid calls
        return ContextConstructorWithKnownInitElementsVector580.execute(input, memory, hybridCalls, embedded, vector, elements);
    }

    /**
     * Internal factoring to create the ContextConstructor543Api.Calls closure
     * that intercepts the specific copy32 call site.
     */
    static ContextConstructor543Api.Calls bindCopy32(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            ContextConstructor543Api.Calls fallback,
            Embedded32Copy581Api.Calls copy32) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(copy32);

        return new ContextConstructor543Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(ContextConstructor543Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call call = frame.call();

                // Check if this is the exact known call site: 0x373ADBD -> 0x3727180
                if (call.callSiteRva() == 0x373ADBDL &&
                    call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    call.targetBits() == 0x3727180L) {

                    // Invoke the known actual producer with the outer frame's child entry
                    // and direction flag, using the same memory and budget.
                    FullCopy437Api.CallResult result = Embedded32FullState3727180.execute(
                        new FullCopy437Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            input.budget()
                        ),
                        memory,
                        copy32
                    );

                    // Validate the result against the outer frame's expectations
                    frame.checkNormalReturn(result);

                    // Return the actual inner CallResult object unchanged
                    return result;
                }

                // Forward all other frames unchanged to the fallback provider
                return fallback.invoke(frame);
            }
        };
    }
}