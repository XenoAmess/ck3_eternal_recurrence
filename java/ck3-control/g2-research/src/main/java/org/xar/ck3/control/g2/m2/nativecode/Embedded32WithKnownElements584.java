package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Copy581Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElements578Api;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32FullState3727180;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsFullState37282B0;

/**
 * Thin known-callee consumer for the 394-byte function at RVA 0x3727180.
 * Intercepts only the internal call to 0x37282B0 (site 0x37272F0) and delegates
 * to the known 322-byte implementation, leaving all other calls opaque.
 */
public final class Embedded32WithKnownElements584 {
    private Embedded32WithKnownElements584() { }

    /**
     * Package-private static bindElements: creates the live closure that intercepts ONLY site 0x37272F0
     * (target 0x37282B0) and delegates to EmbeddedElementsFullState37282B0.execute for that specific frame.
     * All other frames are passed unchanged to the original fallback.
     */
    static Embedded32Copy581Api.Calls bindElements(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            Embedded32Copy581Api.Calls fallback,
            EmbeddedElements578Api.Calls elements) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(elements);

        return new Embedded32Copy581Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(Embedded32Copy581Api.CallFrame frame) {
                // Check if this is the specific internal call to 0x37282B0
                // Site 0x37272F0, Direct, Target 0x37282B0
                if (frame.call().callSiteRva() == 0x37272F0L &&
                    frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    frame.call().targetBits() == 0x37282B0L) {

                    // Construct the input for the known 322-byte implementation
                    // using the childEntry from the frame, the direction flag, budget, memory, and elements
                    FullCopy437Api.Input innerInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    // Execute the known 322-byte implementation
                    FullCopy437Api.CallResult actualResult = EmbeddedElementsFullState37282B0.execute(
                        innerInput,
                        memory,
                        elements
                    );

                    // Validate the result against the outer frame expectations
                    frame.checkNormalReturn(actualResult);

                    // Return the exact result unchanged
                    return actualResult;
                }

                // For all other frames, delegate to the original fallback
                return fallback.invoke(frame);
            }
        };
    }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            Embedded32Copy581Api.Calls fallback,
            EmbeddedElements578Api.Calls elements) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(elements);

        // Create a live closure that intercepts ONLY site 0x37272F0 (target 0x37282B0)
        // and delegates to EmbeddedElementsFullState37282B0.execute for that specific frame.
        // All other frames are passed unchanged to the original fallback.
        Embedded32Copy581Api.Calls boundCalls = bindElements(input, memory, fallback, elements);

        // Run the actual 394-byte implementation exactly once using the bound calls
        return Embedded32FullState3727180.execute(input, memory, boundCalls);
    }
}