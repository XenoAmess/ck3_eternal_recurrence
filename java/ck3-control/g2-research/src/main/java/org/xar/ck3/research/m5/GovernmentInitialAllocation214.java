package org.xar.ck3.research.m5;

import org.xar.ck3.research.m4.StackProbe78FullState290;
import org.xar.ck3.research.m4.Wrapper19Initial162Calls285;
import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

public final class GovernmentInitialAllocation214 {
    private GovernmentInitialAllocation214() { }

    public static GovernmentInitialFrame162Api.Join execute(
            GovernmentInitialFrame162Api.Entry entry,
            GovernmentInitialFrame162Api.Memory memory,
            GovernmentInitialFrame162Api.Calls outer,
            GovernmentInitialFrame162Api.LoopBudget initialBudget,
            StackProbe78FullState290.Gs10 gs10,
            GovernmentCrtBoundary185Api.LoopBudget probeBudget,
            GovernmentCrtBoundary185Api.Calls allocationPorts,
            GovernmentCrtBoundary185Api.LoopBudget allocationBudget) {
        if (entry == null) throw new NullPointerException("entry");
        if (memory == null) throw new NullPointerException("memory");
        if (outer == null) throw new NullPointerException("outer");
        if (initialBudget == null) throw new NullPointerException("initialBudget");
        if (gs10 == null) throw new NullPointerException("gs10");
        if (probeBudget == null) throw new NullPointerException("probeBudget");
        if (allocationPorts == null) throw new NullPointerException("allocationPorts");
        if (allocationBudget == null) throw new NullPointerException("allocationBudget");

        GovernmentInitialFrame162Api.Calls allocation = Wrapper19Initial162Calls285.bind(
                entry.imageBaseBits(), memory, outer, allocationPorts, allocationBudget);

        return GovernmentInitialStack213.execute(
                entry, memory, allocation, initialBudget, gs10, probeBudget);
    }
}
