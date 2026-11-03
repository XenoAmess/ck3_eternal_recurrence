package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m3.copy437259.Add4Copy259;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner composition of the actual parent150 port, existing642 routing and sole M3 COPY259 binding. */
public final class EmbeddedElementsKnownConstruct644 {
    private EmbeddedElementsKnownConstruct644() { }

    public interface Memory extends EmbeddedElementsKnownLower642.Memory, Element150Fp643Api.Memory {
    }

    /** Use the same owned Memory and LoopBudget as the full parent Input. */
    public static EmbeddedElementsFp637.Calls bind(
            Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Range16Fp638Api.Calls rangeCalls,
            FullCopyWithFp613.TailCalls unknownCopyTails,
            Add4Fp639Api.Calls foreignAddCalls,
            Element150Fp643Api.Calls construct150Calls,
            EmbeddedElementsFp637.Calls foreignParentCalls) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(rangeCalls);
        Objects.requireNonNull(unknownCopyTails);
        Objects.requireNonNull(foreignAddCalls);
        Objects.requireNonNull(construct150Calls);
        Objects.requireNonNull(foreignParentCalls);

        Add4Fp639Api.Calls knownCopyCalls =
                Add4Copy259.bind(memory, budget, unknownCopyTails, foreignAddCalls);
        EmbeddedElementsFp637.Calls remaining = EmbeddedElementsKnownLower642.bind(
                memory, budget, rangeCalls, knownCopyCalls, foreignParentCalls);
        return frame -> {
            Objects.requireNonNull(frame);
            EmbeddedElements578Api.CallFrame original = frame.original();
            GovernmentCrtBoundary185Api.Call call = original.call();
            if (call.callSiteRva() == 0x372833BL
                    && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x37295B0L
                    && original.instructionLength() == 5) {
                Element150Fp643Api.Input input = new Element150Fp643Api.Input(
                        original.childEntry(), original.directionFlagSet(), frame.preMxcsr());
                QueueFp604Api.Outcome offered = Objects.requireNonNull(
                        Element150FullState643.execute(input, memory, construct150Calls));
                if (offered instanceof QueueFp604Api.Normal normal)
                    original.checkNormalReturn(normal.base());
                return offered;
            }
            return Objects.requireNonNull(remaining.invoke(frame));
        };
    }
}
