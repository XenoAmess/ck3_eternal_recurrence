package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Owner thin caller scaffold with narrow model dispatch for the actual394-to103 route.
 * Connects actual394 tailCALL37272F8->full103 and that queue's exactCALL3727ECF->full81.
 * All other 394 calls and foreign queue F0D remain supplied fallbacks.
 */
public final class Embedded32WithKnownClassifiedQueue596 {
    private Embedded32WithKnownClassifiedQueue596() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory, Embedded32Copy581Api.Calls fallback,
            EmbeddedQueue591Api.Calls queueFallback) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(queueFallback);
        var bound = bindKnown(input, memory, fallback, queueFallback);
        return Embedded32FullState3727180.execute(input, memory, bound);
    }

    static Embedded32Copy581Api.Calls bindKnown(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory, Embedded32Copy581Api.Calls fallback,
            EmbeddedQueue591Api.Calls queueFallback) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(queueFallback);
        return frame -> dispatch(frame, input.budget(), memory, fallback, queueFallback);
    }

    private static FullCopy437Api.CallResult dispatch(Embedded32Copy581Api.CallFrame frame,
            GovernmentCrtBoundary185Api.LoopBudget budget, EmbeddedQueue591Api.Memory memory,
            Embedded32Copy581Api.Calls fallback, EmbeddedQueue591Api.Calls queueFallback) {
        if (frame.call().callSiteRva() == 0x37272F8L && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && frame.call().targetBits() == 0x3727EC0L) {
            FullCopy437Api.Input innerInput = new FullCopy437Api.Input(frame.childEntry(), frame.directionFlagSet(), budget);
            FullCopy437Api.CallResult result = EmbeddedQueueWithKnownClassifier595.execute(innerInput, memory, queueFallback);
            frame.checkNormalReturn(result);
            return result;
        }
        FullCopy437Api.CallResult result = fallback.invoke(frame);
        return result;
    }
}