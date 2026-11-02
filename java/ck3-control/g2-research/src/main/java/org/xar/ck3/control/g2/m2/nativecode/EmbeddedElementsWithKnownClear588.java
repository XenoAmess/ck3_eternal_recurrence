package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElements578Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedClear587Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsFullState37282B0;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedClearFullState889780;

/**
 * Thin binding for the 322-byte function at RVA 0x37282B0.
 * Intercepts the direct call to 0x889780 (site 0x37282E1) and routes it to the
 * known clear implementation (EmbeddedClearFullState889780), while leaving
 * all other calls opaque via the provided fallback.
 */
public final class EmbeddedElementsWithKnownClear588 {
    private EmbeddedElementsWithKnownClear588() { }

    /**
     * Required LIVE package-private static bindClear method.
     * Returns an EmbeddedElements578Api.Calls closure that intercepts the specific call site.
     */
    static EmbeddedElements578Api.Calls bindClear(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            EmbeddedElements578Api.Calls fallback,
            EmbeddedClear587Api.Calls clear) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(clear);

        return new EmbeddedElements578Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(EmbeddedElements578Api.CallFrame frame) {
                // Check if this is the specific direct call to 0x889780 at site 0x37282E1
                GovernmentCrtBoundary185Api.Call call = frame.call();
                if (call.callSiteRva() == 0x37282E1L &&
                    call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    call.targetBits() == 0x889780L) {

                    // Intercept: Execute the known clear implementation (93-byte function)
                    // using the child entry from the outer frame, the original budget,
                    // the same memory, and the provided clear port.
                    FullCopy437Api.Input clearInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        input.budget()
                    );

                    FullCopy437Api.CallResult actualResult = EmbeddedClearFullState889780.execute(
                        clearInput,
                        memory,
                        clear
                    );

                    // Validate the result against the outer frame's expectations
                    frame.checkNormalReturn(actualResult);

                    // Return the exact actual CallResult unchanged
                    return actualResult;
                }

                // For all other frames, pass through to the original fallback unchanged
                return fallback.invoke(frame);
            }
        };
    }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            EmbeddedElements578Api.Calls fallback,
            EmbeddedClear587Api.Calls clear) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(clear);

        // Create the live closure using the required static method
        EmbeddedElements578Api.Calls bindClearClosure = bindClear(input, memory, fallback, clear);

        // Execute the full 322-byte state machine once with the bound clear interceptor
        return EmbeddedElementsFullState37282B0.execute(input, memory, bindClearClosure);
    }
}