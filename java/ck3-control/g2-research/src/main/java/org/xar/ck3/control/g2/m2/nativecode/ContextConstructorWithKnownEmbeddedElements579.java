package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructorFullState373ACF0;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsFullState37282B0;

/**
 * Narrow known-callee consumer for the exact direct call site 0x373ADA1 -> 0x37282B0.
 * Binds only this specific frame to the actual EmbeddedElementsFullState37282B0 producer.
 * All other frames are forwarded unchanged to the foreignCalls provider.
 */
public final class ContextConstructorWithKnownEmbeddedElements579 {
    private ContextConstructorWithKnownEmbeddedElements579() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory,
            ContextConstructor543Api.Calls foreignCalls,
            EmbeddedElements578Api.Calls elementCalls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(foreignCalls);
        Objects.requireNonNull(elementCalls);

        // Create a Calls implementation that intercepts the specific known frame
        ContextConstructor543Api.Calls hybridCalls = new ContextConstructor543Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(ContextConstructor543Api.CallFrame frame) {
                // Check if this is the exact known call site: 0x373ADA1 -> 0x37282B0
                GovernmentCrtBoundary185Api.Call call = frame.call();
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
                        elementCalls
                    );

                    // Validate the result against the outer frame's expectations
                    frame.checkNormalReturn(result);

                    // Return the actual inner CallResult object unchanged
                    return result;
                }

                // Forward all other frames unchanged to the foreignCalls provider
                return foreignCalls.invoke(frame);
            }
        };

        // Execute the complete 233-byte ContextConstructor using the hybrid calls
        return ContextConstructorFullState373ACF0.execute(input, memory, hybridCalls);
    }
}