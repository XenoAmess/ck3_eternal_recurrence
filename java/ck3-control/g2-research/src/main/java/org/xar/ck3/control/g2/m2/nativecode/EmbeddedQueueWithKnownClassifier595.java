package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner thin queuecaller scaffold; only exact classify binding is new. */
public final class EmbeddedQueueWithKnownClassifier595 {
    private EmbeddedQueueWithKnownClassifier595() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory,EmbeddedQueue591Api.Calls fallback) {
        return EmbeddedQueueFullState3727EC0.execute(input,memory,bindClassifier(input,memory,fallback));
    }
    static EmbeddedQueue591Api.Calls bindClassifier(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory,EmbeddedQueue591Api.Calls fallback) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(fallback);
        return frame->dispatch(frame,input.budget(),memory,fallback);
    }
    private static FullCopy437Api.CallResult dispatch(EmbeddedQueue591Api.CallFrame frame,
            GovernmentCrtBoundary185Api.LoopBudget budget,EmbeddedQueue591Api.Memory memory,
            EmbeddedQueue591Api.Calls fallback) {
        if (frame.call().callSiteRva() == 0x3727ECFL) {
            FullCopy437Api.Input input = new FullCopy437Api.Input(frame.childEntry(), frame.directionFlagSet(), budget);
            FullCopy437Api.CallResult actualResult = EmbeddedClassifyFullState3727580.execute(input, memory);
            frame.checkNormalReturn(actualResult);
            return actualResult;
        } else {
            return fallback.invoke(frame);
        }
    }
}
