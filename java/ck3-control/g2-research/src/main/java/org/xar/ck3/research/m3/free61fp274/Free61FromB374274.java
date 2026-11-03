package org.xar.ck3.research.m3.free61fp274;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m3.b374fp270.B374Fp270Api;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;

/** B374's eleven E364 CALLs and final E364 tail use the bare-entry implementation. */
public final class Free61FromB374274 {
    private Free61FromB374274() { }

    public static B374Fp270Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget, FreePostState251Api.Children children,
            B374Fp270Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(children);
        Objects.requireNonNull(foreign);
        return new B374Fp270Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(B374Fp270Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call call=frame.original();
                if (call.kind()!=GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        || call.targetBits()!=0x424E364L) {
                    return Objects.requireNonNull(foreign.invoke(frame));
                }
                QueueFp604Api.Input input=new QueueFp604Api.Input(new FullCopy437Api.Input(
                        frame.childEntry(),frame.directionFlagSet(),budget),frame.preMxcsr());
                QueueFp604Api.Outcome actual=Free61EntryFp274.execute(input,memory,children);
                if (actual instanceof QueueFp604Api.Normal normal) frame.checkNormalReturn(normal);
                return actual;
            }

            @Override public QueueFp604Api.Outcome tail(B374Fp270Api.TailFrame frame) {
                Objects.requireNonNull(frame);
                // The current TailFrame constructor admits only 425686D DIRECT424E364.
                QueueFp604Api.Input input=new QueueFp604Api.Input(new FullCopy437Api.Input(
                        frame.original().entry(),frame.directionFlagSet(),budget),frame.preMxcsr());
                QueueFp604Api.Outcome actual=Free61EntryFp274.execute(input,memory,children);
                if (actual instanceof QueueFp604Api.Normal normal) frame.checkNormalReturn(normal);
                return actual;
            }
        };
    }
}
