package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownHeapAllocateFp623;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

public final class AllocateJump5EntryFp650 {
    private AllocateJump5EntryFp650() { }

    public static QueueFp604Api.Outcome execute(
            DefaultStaticFp648Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory,
            KnownHeapAllocateFp623.AllocateCalls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        return Allocate94EntryFp650.execute(input, memory, calls, budget);
    }
}