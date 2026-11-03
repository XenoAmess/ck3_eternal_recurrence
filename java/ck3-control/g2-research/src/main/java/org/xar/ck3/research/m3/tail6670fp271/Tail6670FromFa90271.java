package org.xar.ck3.research.m3.tail6670fp271;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m3.fa90fp267.Fa90Fp267Api;
import org.xar.ck3.research.m3.tail6670fp271.Tail6670Fp271Api;

/**
 * Binding for the FA90 context to route the 4256670 tail through the new whole.
 */
public final class Tail6670FromFa90271 {
    private Tail6670FromFa90271() { }

    public static Fa90Fp267Api.Calls bind(FullCopy437Api.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget, Tail6670Fp271Api.Calls calls, Fa90Fp267Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(foreign);

        return new Fa90Fp267Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(Fa90Fp267Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                GovernmentCrtBoundary185Api.Call original = frame.original();
                long site = original.callSiteRva();
                GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
                long target = original.targetBits();

                if (site == 0x424FAE7L && kind == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && target == 0x4256670L) {
                    // Select new whole for 4256670
                    GovernmentCrtBoundary185Api.Entry childEntry = frame.childEntry();
                    boolean directionFlagSet = frame.directionFlagSet();
                    QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();

                    // Form QueueFp604Api.Input
                    FullCopy437Api.Input baseInput = new FullCopy437Api.Input(childEntry, directionFlagSet, budget);
                    QueueFp604Api.Input input = new QueueFp604Api.Input(baseInput, preMxcsr);

                    // Call new whole exactly once on same memory
                    QueueFp604Api.Outcome outcome = Tail6670FullState271.execute(input, memory, calls);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        // Check normal return before returning same outcome
                        frame.checkNormalReturn(normal);
                    }

                    return outcome;
                } else {
                    // Pass all other legal frames to foreign exactly once
                    QueueFp604Api.Outcome outcome = foreign.invoke(frame);
                    Objects.requireNonNull(outcome);
                    return outcome;
                }
            }
        };
    }
}