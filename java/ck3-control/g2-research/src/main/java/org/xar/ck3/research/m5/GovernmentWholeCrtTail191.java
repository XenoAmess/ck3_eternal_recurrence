package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentWholeCrt189Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtNative192Calls;

/** Thin assembly for GovernmentWholeCrtTail191. */
public final class GovernmentWholeCrtTail191 {
    private GovernmentWholeCrtTail191() { }

    public static GovernmentWhole4798Api.Result execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentWholeCrt189Api.Memory memory,
            GovernmentWhole4798Api.Calls calls,
            GovernmentWhole4798Api.Budgets budgets,
            GovernmentLookupLoop580Api.Cpu cpu,
            GovernmentWhole4798Api.MxcsrBoundary mxcsrBoundary,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs,
            GovernmentLookupHelper176Api.LoopBudget helperBudget,
            GovernmentTokenLookup182Api.Pause pause,
            GovernmentTokenLookup182Api.LoopBudget tokenBudget,
            GovernmentCrtBoundary185Api.Calls crtPorts,
            GovernmentCrtBoundary185Api.LoopBudget crtBudget) {

        GovernmentCrtBoundary185Api.Calls newCrtPorts = GovernmentCrtNative192Calls.bind(
                entry.imageBaseBits(),
                memory,
                crtPorts
        );

        return GovernmentWholeCrt189.execute(
                entry,
                memory,
                calls,
                budgets,
                cpu,
                mxcsrBoundary,
                deepInputs,
                helperBudget,
                pause,
                tokenBudget,
                newCrtPorts,
                crtBudget
        );
    }
}
