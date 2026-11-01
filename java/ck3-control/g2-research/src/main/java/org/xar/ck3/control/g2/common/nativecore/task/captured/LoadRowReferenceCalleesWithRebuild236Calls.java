package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class LoadRowReferenceCalleesWithRebuild236Calls {
    private LoadRowReferenceCalleesWithRebuild236Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls originalFallback, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        GovernmentCrtBoundary185Api.Calls newRebuild = LoadRowReferenceRebuild236Calls.bind(imageBaseBits, memory, originalFallback, budget, floating);
        return LoadRowReferenceCallees337c203Calls.bind(imageBaseBits, memory, newRebuild, budget, floating);
    }
}