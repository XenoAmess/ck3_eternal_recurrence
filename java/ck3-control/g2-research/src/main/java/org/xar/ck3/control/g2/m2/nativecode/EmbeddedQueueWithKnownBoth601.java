package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueue591Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueWithKnownNonGrowth600;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueWithKnownClassifier595;

/**
 * Composes the known non-growth append (600) and the known classifier (595) into a single
 * execution path for the 103-byte function. It does not run both full functions sequentially;
 * instead, it uses the 600 orchestration which intercepts the append call, and provides the
 * 595 classifier binding as the fallback for other calls (specifically the classify call).
 */
public final class EmbeddedQueueWithKnownBoth601 {
    private EmbeddedQueueWithKnownBoth601() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            EmbeddedQueueWithKnownNonGrowth600.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);

        // Create the fallback Calls interface that delegates to the 595 classifier binding
        // for the classify call site (0x3727ECF), and throws for any other unexpected site.
        EmbeddedQueue591Api.Calls fallback = new EmbeddedQueue591Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(EmbeddedQueue591Api.CallFrame frame) {
                if (frame.call().callSiteRva() == 0x3727ECFL) {
                    // Use the existing 595 factory to bind the classifier
                    // This handles the call to 0x3727580 using EmbeddedClassifyFullState3727580
                    EmbeddedQueue591Api.Calls classifierCalls = EmbeddedQueueWithKnownClassifier595.bindClassifier(
                        input, memory, this
                    );
                    return classifierCalls.invoke(frame);
                } else {
                    // Any other call site reaching this fallback is unrepresented in this composition
                    throw new UnsupportedOperationException("Unrepresented call site in Both601 fallback");
                }
            }
        };

        // Execute the 600 orchestration, which handles the append call (0x3727F0D) internally
        // and delegates other calls (like 0x3727ECF) to the provided fallback.
        return EmbeddedQueueWithKnownNonGrowth600.execute(input, memory, fallback);
    }
}