package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.Entry;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentNormalizeWithCrt187Api.Memory;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.Pause;

public final class GovernmentNormalizeWithCrt187 {
    private GovernmentNormalizeWithCrt187() { }

    public static GovernmentNormalizeFull174Api.NormalReturn execute(GovernmentNormalizeFull174Api.Entry entry, GovernmentNormalizeWithCrt187Api.Memory memory, GovernmentPrimaryTail155Api.Calls fallback, GovernmentLookupHelper176Api.LoopBudget helperBudget, GovernmentTokenLookup182Api.Pause pause, GovernmentTokenLookup182Api.LoopBudget tokenBudget, GovernmentCrtBoundary185Api.Calls crtPorts, GovernmentCrtBoundary185Api.LoopBudget crtBudget) {
        GovernmentCrtBoundary185BridgeApi.Calls crtCalls = GovernmentCrtBoundary185Calls.bind(entry.imageBaseBits(), memory, fallback, crtPorts, crtBudget);
        return GovernmentNormalizeWithToken183.execute(entry, memory, crtCalls, helperBudget, pause, tokenBudget);
    }
}
