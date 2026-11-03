package org.xar.ck3.research.m3.f8a8fp263;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.Fc74Fp626Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Only the actual FD10 edge selects the represented205 child on the same storage. */
public final class F8a8FromFc74263 {
    private F8a8FromFc74263() { }

    public static Fc74Fp626Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget, F8a8Fp263Api.Calls calls,
            Fc74Fp626Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(foreign);
        return frame -> {
            Objects.requireNonNull(frame);
            GovernmentCrtBoundary185Api.Call original = frame.original();
            if (original.callSiteRva() == 0x424FD10L
                    && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && original.targetBits() == 0x424F8A8L) {
                QueueFp604Api.Input input = new QueueFp604Api.Input(
                    new FullCopy437Api.Input(frame.childEntry(), frame.directionFlagSet(), budget),
                    frame.preMxcsr());
                QueueFp604Api.Outcome outcome = F8a8FullState263.execute(input, memory, calls);
                if (outcome instanceof QueueFp604Api.Normal normal) {
                    frame.checkNormalReturn(normal.base());
                }
                return outcome;
            }
            return Objects.requireNonNull(foreign.invoke(frame));
        };
    }
}
