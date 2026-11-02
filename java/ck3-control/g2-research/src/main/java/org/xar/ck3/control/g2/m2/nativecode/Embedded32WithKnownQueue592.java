package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner thin caller scaffold with narrow model dispatch for the actual394-to103 route. */
public final class Embedded32WithKnownQueue592 {
    private Embedded32WithKnownQueue592() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory,Embedded32Copy581Api.Calls fallback,
            EmbeddedQueue591Api.Calls queueCalls) {
        var bound=bindQueue(input,memory,fallback,queueCalls);
        return Embedded32FullState3727180.execute(input,memory,bound);
    }
    static Embedded32Copy581Api.Calls bindQueue(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory,Embedded32Copy581Api.Calls fallback,
            EmbeddedQueue591Api.Calls queueCalls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(fallback);Objects.requireNonNull(queueCalls);
        return frame->dispatch(frame,input.budget(),memory,fallback,queueCalls);
    }
    private static FullCopy437Api.CallResult dispatch(Embedded32Copy581Api.CallFrame frame,
            GovernmentCrtBoundary185Api.LoopBudget budget,EmbeddedQueue591Api.Memory memory,
            Embedded32Copy581Api.Calls fallback,EmbeddedQueue591Api.Calls queueCalls) {
        if (frame.call().callSiteRva() == 0x37272F8L && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && frame.call().targetBits() == 0x3727EC0L) {
            FullCopy437Api.Input innerInput = new FullCopy437Api.Input(frame.childEntry(), frame.directionFlagSet(), budget);
            FullCopy437Api.CallResult result = EmbeddedQueueFullState3727EC0.execute(innerInput, memory, queueCalls);
            frame.checkNormalReturn(result);
            return result;
        }
        FullCopy437Api.CallResult result = fallback.invoke(frame);
        return result;
    }
}
