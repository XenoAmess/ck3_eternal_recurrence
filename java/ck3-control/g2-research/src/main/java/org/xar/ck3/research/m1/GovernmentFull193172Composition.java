package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentRowResolve164Api;
import org.xar.ck3.research.m1.GovernmentLookup167Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m5.GovernmentResult168Api;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api;

/**
 * Typed consumer assembly for GovernmentRowResolve164 (parent 2D1B7F0).
 * Binds the actual shared manager (3F8A7E0), lookup (3F8A6D0), ABF (ABF7E0),
 * and hash (3F7E220) callees.
 */
public final class GovernmentFull193172Composition {

    private GovernmentFull193172Composition() { }

    public static GovernmentRowResolve164Api.Result execute(
            GovernmentRowResolve164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            Calls delegate,
            GovernmentLookup167Api.SpinBudget lookupBudget,
            GovernmentResult168Api.WorkBudget resolveBudget,
            GovernmentByteUpdate169Api.LoopBudget hashBudget,
            GovernmentLookupLoop580Api.Mxcsr32 ownedMxcsrAtHash) {

        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(lookupBudget);
        Objects.requireNonNull(resolveBudget);
        Objects.requireNonNull(hashBudget);
        Objects.requireNonNull(ownedMxcsrAtHash);

        // 1. Bind the hash (3F7E220) adapter.
        Calls hashBound = GovernmentFull193172HashCalls.bind(
                entry.imageBaseBits(),
                memory,
                delegate,
                hashBudget,
                ownedMxcsrAtHash);

        // 2. Execute the existing ABF composition with the bound hash delegate.
        //    This reuses the frozen ABF path (manager/lookup/ABF) and injects the hash binding.
        return GovernmentAbf170Composition.execute(
                entry,
                memory,
                hashBound,
                lookupBudget,
                resolveBudget);
    }
}