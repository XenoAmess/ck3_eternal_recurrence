package org.xar.ck3.research.m1;

import org.xar.ck3.research.m1.GovernmentRowResolve164Api;
import org.xar.ck3.research.m1.GovernmentLookup167Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m1.GovernmentLookup167Adapter;
import org.xar.ck3.research.m1.GovernmentLookup167;

/**
 * Typed consumer assembly for GovernmentRowResolve164 (parent 2D1B7F0).
 * Binds the actual shared manager (3F8A7E0) and lookup (3F8A6D0) callees
 * using their existing adapters, preserving full volatile/nonvolatile state
 * and CALL/RET semantics.
 */
public final class GovernmentSharedComposition168 {

    private GovernmentSharedComposition168() { }

    public static GovernmentRowResolve164Api.Result execute(
            GovernmentRowResolve164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            Calls delegate,
            GovernmentLookup167Api.SpinBudget spinBudget) {

        // 1. Bind the Shared Manager (3F8A7E0) adapter.
        //    This adapter intercepts calls to 3F8A7E0 and executes GovernmentSharedManager167.execute.
        //    It requires the image base from the entry and the shared memory object.
        Calls managerBound = GovernmentSharedManager167Calls.bind(
                entry.imageBaseBits(),
                memory,
                delegate);

        // 2. Bind the Lookup (3F8A6D0) adapter.
        //    This adapter intercepts calls to 3F8A6D0 and executes GovernmentLookup167.execute.
        //    It wraps the managerBound calls so that nested calls to 3F8A7E0 from within the lookup
        //    are also handled correctly by the manager adapter.
        Calls lookupBound = new GovernmentLookup167Adapter(
                entry.imageBaseBits(),
                memory,
                managerBound,
                GovernmentLookup167::execute,
                spinBudget);

        // 3. Execute the parent (2D1B7F0) using the fully bound call chain.
        //    The parent will invoke callees via 'lookupBound', which routes to the appropriate
        //    adapter based on the target RVA.
        return GovernmentRowResolve164.execute(
                entry,
                memory,
                lookupBound);
    }
}