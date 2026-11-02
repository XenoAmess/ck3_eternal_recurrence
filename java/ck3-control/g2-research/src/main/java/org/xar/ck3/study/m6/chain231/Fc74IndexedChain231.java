package org.xar.ck3.study.m6.chain231;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.e900227.E900Calls227;
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;
import org.xar.ck3.study.m6.indexed230.Indexed448FullCalls230;
import org.xar.ck3.study.m6.fc226.Fc74FullState226;

public final class Fc74IndexedChain231 {
    private Fc74IndexedChain231() { }

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

        // 1. Bind the deepest opaque provider (originalFallback) to the indexed helper (E448).
        //    This adapter intercepts calls to 0x424E448 and delegates to Indexed448FullState230.
        GovernmentCrtBoundary185Api.Calls indexedBinder = Indexed448FullCalls230.bind(
                image, memory, originalFallback, budget);

        // 2. Bind the indexed binder to the E900 helper (E900).
        //    This adapter intercepts calls to 0x424E900 and delegates to E900FullState227,
        //    passing the indexedBinder as the fallback for deeper calls (like 0x424E448).
        GovernmentCrtBoundary185Api.Calls e900Binder = E900Calls227.bind(
                image, memory, indexedBinder);

        // 3. Execute the root FC74 logic using the e900Binder as the Calls provider.
        //    Fc74FullState226 owns the root frame and calls lower.invoke for child boundaries.
        return Fc74FullState226.execute(entry, memory, e900Binder);
    }
}