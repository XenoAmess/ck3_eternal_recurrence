package org.xar.ck3.research.m5;

import org.xar.ck3.research.m4.StackProbe78FullState290;
import org.xar.ck3.research.m4.StackProbe78Initial162Calls290;
import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

public final class GovernmentInitialStack213 {
    private GovernmentInitialStack213() { }

    public static GovernmentInitialFrame162Api.Join execute(
            GovernmentInitialFrame162Api.Entry entry,
            GovernmentInitialFrame162Api.Memory memory,
            GovernmentInitialFrame162Api.Calls outer,
            GovernmentInitialFrame162Api.LoopBudget initialBudget,
            StackProbe78FullState290.Gs10 gs10,
            GovernmentCrtBoundary185Api.LoopBudget probeBudget) {
        if (entry == null) throw new NullPointerException("entry");
        if (memory == null) throw new NullPointerException("memory");
        if (outer == null) throw new NullPointerException("outer");
        if (initialBudget == null) throw new NullPointerException("initialBudget");
        if (gs10 == null) throw new NullPointerException("gs10");
        if (probeBudget == null) throw new NullPointerException("probeBudget");

        GovernmentInitialFrame162Api.Calls bound = StackProbe78Initial162Calls290.bind(
                entry.imageBaseBits(), memory, outer, gs10, probeBudget);

        return GovernmentInitialFrame162.execute(entry, memory, bound, initialBudget);
    }
}