package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Entry;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentNormalizeWithToken183Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.Pause;

public final class GovernmentNormalizeWithToken183 {
    private GovernmentNormalizeWithToken183() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls fallback, LoopBudget helperBudget, Pause pause, GovernmentTokenLookup182Api.LoopBudget tokenBudget) {
        GovernmentNormalizeFull174Api.Calls tokenCalls = GovernmentTokenLookup182Calls.bind(entry.imageBaseBits(), memory, fallback, pause, tokenBudget);
        return GovernmentNormalizeWithRoot180.execute(entry, memory, tokenCalls, helperBudget);
    }
}
