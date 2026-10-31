package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentWholeCrt189Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtLeaf205Calls;
import org.xar.ck3.research.m5.GovernmentErrorCell204Calls;
import org.xar.ck3.research.m1.GovernmentResizeBase203Calls;
import org.xar.ck3.research.m4.Callee4259250FullState203Calls;
import org.xar.ck3.research.m5.GovernmentWholeResizeFree202;

/** Thin assembly for GovernmentWholeLeaf205. */
public final class GovernmentWholeLeaf205 {
    private GovernmentWholeLeaf205() { }

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

        long image = entry.imageBaseBits();

        GovernmentCrtBoundary185Api.Calls leaf = GovernmentCrtLeaf205Calls.bind(
                image,
                memory,
                crtPorts
        );

        GovernmentCrtBoundary185Api.Calls error = GovernmentErrorCell204Calls.bind(
                image,
                memory,
                leaf
        );

        GovernmentCrtBoundary185Api.Calls base = GovernmentResizeBase203Calls.bind(
                image,
                memory,
                error,
                crtBudget
        );

        GovernmentCrtBoundary185Api.Calls size = Callee4259250FullState203Calls.bind(
                image,
                memory,
                base
        );

        return GovernmentWholeResizeFree202.execute(
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
                size,
                crtBudget
        );
    }
}
