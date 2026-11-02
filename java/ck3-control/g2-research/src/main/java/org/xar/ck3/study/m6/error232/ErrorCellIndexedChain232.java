package org.xar.ck3.study.m6.error232;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;
import org.xar.ck3.study.m6.indexed230.Indexed448FullCalls230;
import org.xar.ck3.study.m6.e900227.E900Calls227;
import org.xar.ck3.study.m6.fc226.Fc74Calls226;
import org.xar.ck3.research.m5.GovernmentErrorCell204;

public final class ErrorCellIndexedChain232 {
    private ErrorCellIndexedChain232() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            AtomicIndexedMemory229 memory,
            GovernmentCrtBoundary185Api.Calls originalFallback,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(originalFallback);
        Objects.requireNonNull(budget);

        long image = entry.imageBaseBits();

        // 1. Deepest Indexed binder (captures opaque calls for 424E448)
        GovernmentCrtBoundary185Api.Calls indexedBinder = Indexed448FullCalls230.bind(image, memory, originalFallback, budget);

        // 2. E900 binder (captures indexedBinder for 424E900)
        GovernmentCrtBoundary185Api.Calls e900Binder = E900Calls227.bind(image, memory, indexedBinder);

        // 3. FC74 binder (captures e900Binder for 424FC74)
        GovernmentCrtBoundary185Api.Calls fc74Binder = Fc74Calls226.bind(image, memory, e900Binder);

        // 4. Execute the root Error32 cell (423B18C) using the fully bound chain
        return GovernmentErrorCell204.execute(entry, memory, fc74Binder);
    }
}