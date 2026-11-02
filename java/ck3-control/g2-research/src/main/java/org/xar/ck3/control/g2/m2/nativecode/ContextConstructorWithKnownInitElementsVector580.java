package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownEmbeddedInit560;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorWithKnownEmbeddedVector574;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElements578Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsFullState37282B0;

/**
 * Production composition combining known init, known vector, and known elements.
 * Delegates to ContextConstructorWithKnownEmbeddedVector574 for init/vector handling,
 * while injecting the known elements handler for site 373ADA1.
 */
public final class ContextConstructorWithKnownInitElementsVector580 {
    private ContextConstructorWithKnownInitElementsVector580() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            ContextConstructor543Api.Calls fallback,
            ContextConstructorWithKnownEmbeddedInit560.EmbeddedCalls embedded,
            ContextConstructorWithKnownEmbeddedVector574.VectorCalls vector,
            EmbeddedElements578Api.Calls elements) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(embedded);
        Objects.requireNonNull(vector);
        Objects.requireNonNull(elements);

        // Create the hybrid calls that handles the specific elements site
        ContextConstructor543Api.Calls hybridCalls = bindElements(input, memory, fallback, elements);

        // Execute the mature 574 composition (which handles init and vector) using the hybrid calls
        return ContextConstructorWithKnownEmbeddedVector574.execute(input, memory, hybridCalls, embedded, vector);
    }

    /**
     * Internal factoring to create the ContextConstructor543Api.Calls closure
     * that intercepts the specific elements call site.
     */
    static ContextConstructor543Api.Calls bindElements(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            ContextConstructor543Api.Calls fallback,
            EmbeddedElements578Api.Calls elements) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(elements);

        return new ContextConstructor543Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(ContextConstructor543Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call call = frame.call();

                // Check if this is the exact known call site: 0x373ADA1 -> 0x37282B0
                if (call.callSiteRva() == 0x373ADA1L &&
                    call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    call.targetBits() == 0x37282B0L) {

                    // Invoke the known actual producer with the outer frame's child entry
                    // and direction flag, using the same memory and budget.
                    FullCopy437Api.CallResult result = EmbeddedElementsFullState37282B0.execute(
                        new FullCopy437Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            input.budget()
                        ),
                        memory,
                        elements
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