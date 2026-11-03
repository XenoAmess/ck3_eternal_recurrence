package org.xar.ck3.research.m3.add4range262;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.Add4Fp639Api;
import org.xar.ck3.control.g2.m2.nativecode.Add4FullState639;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.copy437259.Add4Copy259;
import org.xar.ck3.research.m3.rangereverse261.RangeReverse261;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Same-RAM binding of the actual Add4 range call to the existing range/reverse composition. */
public final class Add4Range262 {
    private Add4Range262() { }

    /** One owned storage view for Add4, COPY, range and reverse effects. */
    public interface Memory extends Add4Fp639Api.Memory, RangeReverse261.Memory { }

    /** Selects only ADD219; all other legal Add4 frames retain their foreign handler. */
    public static Add4Fp639Api.Calls bind(Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget, Add4Fp639Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(foreign);

        return frame -> {
            Objects.requireNonNull(frame);
            GovernmentCrtBoundary185Api.Call call = frame.call();
            if (call.callSiteRva() == 0xADD219L
                    && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x9D0950L
                    && frame.instructionLength() == 5) {
                QueueFp604Api.Input input = new QueueFp604Api.Input(
                    new FullCopy437Api.Input(frame.childEntry(), frame.directionFlagSet(), budget),
                    frame.preMxcsr());
                QueueFp604Api.Outcome outcome = Objects.requireNonNull(
                    RangeReverse261.execute(input, memory));
                if (outcome instanceof QueueFp604Api.Normal normal) {
                    frame.checkNormalReturn(normal);
                }
                return outcome;
            }
            return Objects.requireNonNull(foreign.invoke(frame));
        };
    }

    /** Reuses the four COPY routes around the narrow range binding. */
    public static Add4Fp639Api.Calls withCopy(Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            FullCopyWithFp613.TailCalls unknownCopyTails, Add4Fp639Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(unknownCopyTails);
        Objects.requireNonNull(foreign);
        return Add4Copy259.bind(memory, budget, unknownCopyTails, bind(memory, budget, foreign));
    }

    /** Runs the existing complete Add4 protocol with the composed COPY/range handlers. */
    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input, Memory memory,
            FullCopyWithFp613.TailCalls unknownCopyTails, Add4Fp639Api.Calls foreign,
            long originCallSiteRva) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        return Add4FullState639.execute(input, memory,
            withCopy(memory, input.base().budget(), unknownCopyTails, foreign), originCallSiteRva);
    }
}
