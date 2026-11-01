package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceCalleesWithSwap238Calls {
    private LoadRowReferenceCalleesWithSwap238Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls originalFallback, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        GovernmentCrtBoundary185Api.Calls inner = LoadRowReferenceSwap238Calls.bind(image, memory, originalFallback);
        return LoadRowReferenceCalleesWithTransfer237Calls.bind(image, memory, inner, budget, floating);
    }
}