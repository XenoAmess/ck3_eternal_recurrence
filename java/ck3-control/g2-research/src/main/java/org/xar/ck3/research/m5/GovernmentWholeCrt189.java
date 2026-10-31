package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentCrtRegistry188Bridge;

/** Thin assembly for GovernmentWholeCrt189. */
public final class GovernmentWholeCrt189 {
    private GovernmentWholeCrt189() { }

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

        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(budgets);
        Objects.requireNonNull(cpu);
        Objects.requireNonNull(mxcsrBoundary);
        Objects.requireNonNull(deepInputs);
        Objects.requireNonNull(helperBudget);
        Objects.requireNonNull(pause);
        Objects.requireNonNull(tokenBudget);
        Objects.requireNonNull(crtPorts);
        Objects.requireNonNull(crtBudget);

        // 1. Bind the M1 registry bridge into the CRT boundary calls port.
        GovernmentCrtBoundary185Api.Calls registryCalls = GovernmentCrtRegistry188Bridge.bind(
                entry.imageBaseBits(),
                memory,
                crtPorts
        );

        // 2. Bind the M4 callee bridge into the registry calls port.
        GovernmentCrtBoundary185Api.Calls calleeCalls = GovernmentCrtCallee186Calls.bind(
                entry.imageBaseBits(),
                memory,
                registryCalls
        );

        // 3. Bind the CRT boundary calls into the ordinary calls port.
        GovernmentCrtBoundary185BridgeApi.Calls crtCalls = GovernmentCrtBoundary185Calls.bind(
                entry.imageBaseBits(),
                memory,
                calls.ordinary(),
                calleeCalls,
                crtBudget
        );

        // 4. Construct the new Calls record for the whole assembly.
        //    Replace ONLY ordinary() with crtCalls. Preserve all other ports.
        GovernmentWhole4798Api.Calls newCalls = new GovernmentWhole4798Api.Calls(
                calls.initial(),
                calls.lookup(),
                crtCalls,
                calls.lookup155(),
                calls.prefix153(),
                calls.post153()
        );

        // 5. Delegate to the existing 184 token assembly.
        return GovernmentWholeToken184.execute(
                entry,
                memory,
                newCalls,
                budgets,
                cpu,
                mxcsrBoundary,
                deepInputs,
                helperBudget,
                pause,
                tokenBudget
        );
    }
}
