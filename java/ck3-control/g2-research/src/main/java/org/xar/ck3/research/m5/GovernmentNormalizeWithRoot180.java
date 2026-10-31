package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Entry;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentNormalizeWithRoot180Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.LoopBudget;

public final class GovernmentNormalizeWithRoot180 {
    private GovernmentNormalizeWithRoot180() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls fallback, LoopBudget budget) {
        GovernmentLookupHelper176Api.Calls rootCalls = GovernmentRoot178Calls.bind(entry.imageBaseBits(), memory, fallback);
        return GovernmentNormalizeWithHelper177.execute(entry, memory, rootCalls, budget);
    }
}
