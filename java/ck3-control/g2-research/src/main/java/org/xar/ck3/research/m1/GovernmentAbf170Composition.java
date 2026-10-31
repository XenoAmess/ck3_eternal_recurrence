package org.xar.ck3.research.m1;

import org.xar.ck3.research.m1.GovernmentRowResolve164Api;
import org.xar.ck3.research.m1.GovernmentLookup167Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentResult168Api;

/**
 * Typed consumer assembly for GovernmentRowResolve164 (parent 2D1B7F0).
 * Binds the actual shared manager (3F8A7E0), lookup (3F8A6D0), and ABF (ABF7E0) callees.
 */
public final class GovernmentAbf170Composition {

    private GovernmentAbf170Composition() { }

    public static GovernmentRowResolve164Api.Result execute(
            GovernmentRowResolve164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            Calls delegate,
            GovernmentLookup167Api.SpinBudget lookupBudget,
            GovernmentResult168Api.WorkBudget resolveBudget) {

        // 1. Bind the ABF (ABF7E0) adapter.
        //    This adapter intercepts calls to ABF7E0 and executes GovernmentResult168.execute.
        Calls abfBound = GovernmentAbf170Calls.bind(
                entry.imageBaseBits(),
                memory,
                delegate,
                resolveBudget);

        // 2. Execute the parent (2D1B7F0) using the fully bound call chain.
        //    The existing GovernmentSharedComposition168 already binds manager and lookup.
        //    We pass abfBound as the delegate to it, so that when the parent calls ABF7E0,
        //    it is handled by our new binding.
        return GovernmentSharedComposition168.execute(
                entry,
                memory,
                abfBound,
                lookupBudget);
    }
}