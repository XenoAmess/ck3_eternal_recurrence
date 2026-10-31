package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentFill207Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtFill207Calls;
import org.xar.ck3.research.m5.GovernmentWholeLeaf205;

/** Thin assembly for GovernmentWholeFill207. */
public final class GovernmentWholeFill207 {
    private GovernmentWholeFill207() { }

    public static GovernmentWhole4798Api.Result execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentFill207Api.Memory memory,
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

        GovernmentCrtBoundary185Api.Calls fillPorts = GovernmentCrtFill207Calls.bind(
                entry.imageBaseBits(),
                memory,
                crtPorts,
                crtBudget
        );

        return GovernmentWholeLeaf205.execute(
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
                fillPorts,
                crtBudget
        );
    }
}
