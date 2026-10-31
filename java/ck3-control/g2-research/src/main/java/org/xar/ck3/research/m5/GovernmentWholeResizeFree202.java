package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentWholeCrt189Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtResize202Calls;
import org.xar.ck3.research.m4.Free61FullState201Calls;
import org.xar.ck3.research.m5.GovernmentWholeGrowth200;

/** Thin assembly for GovernmentWholeResizeFree202. */
public final class GovernmentWholeResizeFree202 {
    private GovernmentWholeResizeFree202() { }

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

        GovernmentCrtBoundary185Api.Calls resizePorts = GovernmentCrtResize202Calls.bind(
                entry.imageBaseBits(),
                memory,
                crtPorts
        );

        GovernmentCrtBoundary185Api.Calls freePorts = Free61FullState201Calls.bind(
                entry.imageBaseBits(),
                memory,
                resizePorts
        );

        return GovernmentWholeGrowth200.execute(
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
                freePorts,
                crtBudget
        );
    }
}
