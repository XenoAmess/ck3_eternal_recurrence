package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentWholeCrt189Api;
import org.xar.ck3.research.m5.GovernmentFill207Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentWholeFill207;
import org.xar.ck3.research.m1.GovernmentMemoryFillRep207Calls;

/** Thin assembly for GovernmentWholeRep208. */
public final class GovernmentWholeRep208 {
    private GovernmentWholeRep208() { }

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
            GovernmentCrtBoundary185Api.LoopBudget crtBudget,
            boolean ownedDirectionFlagSet) {

        if (ownedDirectionFlagSet) {
            throw new UnsupportedOperationException("whole208 DF-set is outside Growth199 normal DF=0 domain");
        }

        GovernmentCrtBoundary185Api.Calls repPorts = GovernmentMemoryFillRep207Calls.bind(
                memory,
                crtPorts,
                ownedDirectionFlagSet,
                crtBudget
        );

        return GovernmentWholeFill207.execute(
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
                repPorts,
                crtBudget
        );
    }
}
