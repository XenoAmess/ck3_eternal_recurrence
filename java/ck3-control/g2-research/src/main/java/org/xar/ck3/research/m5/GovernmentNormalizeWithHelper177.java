package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Entry;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentNormalizeWithHelper177Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.LoopBudget;

public final class GovernmentNormalizeWithHelper177 {
    private GovernmentNormalizeWithHelper177() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls fallback, LoopBudget budget) {
        GovernmentNormalizeFull174Api.Calls calls = GovernmentLookupHelper176Calls.bind(entry.imageBaseBits(), memory, fallback, budget);
        return GovernmentNormalizeFull174.execute(entry, memory, calls);
    }
}
