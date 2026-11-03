package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageAllocateFp622;
import org.xar.ck3.control.g2.m2.nativecode.KnownHeapAllocateFp623;

public final class RetryKnownAllocate650 {
    private RetryKnownAllocate650() { }

    public static KnownPageAllocateFp622.RetryCalls bind(
            GovernmentCrtBoundary185Api.Memory memory,
            KnownHeapAllocateFp623.AllocateCalls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            KnownPageAllocateFp622.RetryCalls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(foreign);

        return new KnownPageAllocateFp622.RetryCalls() {
            @Override
            public QueueFp604Api.Outcome invoke(KnownPageAllocateFp622.RetryCall frame) {
                Objects.requireNonNull(frame);

                GovernmentCrtBoundary185Api.Call original = frame.original();
                long site = original.callSiteRva();
                GovernmentCrtBoundary185Api.TargetKind kind = original.kind();
                long target = original.targetBits();

                if (site == 0x4223BAEL
                        && kind == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && target == 0x42420B8L) {

                    DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            frame.preMxcsr());

                    QueueFp604Api.Outcome outcome = AllocateJump5EntryFp650.execute(
                            input, memory, calls, budget);

                    Objects.requireNonNull(outcome);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        frame.checkNormalReturn(normal.base());
                    }

                    return outcome;
                }

                QueueFp604Api.Outcome outcome = foreign.invoke(frame);
                Objects.requireNonNull(outcome);
                return outcome;
            }
        };
    }
}