package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentLookupHelper176Api;
import org.xar.ck3.research.m5.GovernmentLookupWithRoot179Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentRoot178Calls;

public final class GovernmentLookupWithRoot179 {
    private GovernmentLookupWithRoot179() { }

    public static GovernmentLookupHelper176Api.NormalReturn execute(
            GovernmentLookupHelper176Api.Entry entry,
            GovernmentLookupWithRoot179Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls fallback,
            GovernmentLookupHelper176Api.LoopBudget budget) {
        GovernmentLookupHelper176Api.Calls calls = GovernmentRoot178Calls.bind(
                entry.imageBaseBits(),
                memory,
                fallback);
        return GovernmentLookupHelper176.execute(entry, memory, calls, budget);
    }
}
