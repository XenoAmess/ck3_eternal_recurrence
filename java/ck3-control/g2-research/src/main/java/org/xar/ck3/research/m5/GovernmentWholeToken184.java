package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173Api;
import org.xar.ck3.research.m5.GovernmentWholeToken184Api;
import org.xar.ck3.research.m5.GovernmentWholeRoot181;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Calls;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api;

/**
 * Thin assembly for GovernmentWholeToken184.
 * Wraps the existing root181 assembly by injecting the 182 token lookup bridge
 * into the ordinary calls port before delegating to 181.
 */
public final class GovernmentWholeToken184 {
    private GovernmentWholeToken184() { }

    public static GovernmentWhole4798Api.Result execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentWholeToken184Api.Memory memory,
            GovernmentWhole4798Api.Calls calls,
            GovernmentWhole4798Api.Budgets budgets,
            GovernmentLookupLoop580Api.Cpu cpu,
            GovernmentWhole4798Api.MxcsrBoundary mxcsrBoundary,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs,
            GovernmentLookupHelper176Api.LoopBudget helperBudget,
            GovernmentTokenLookup182Api.Pause pause,
            GovernmentTokenLookup182Api.LoopBudget tokenBudget) {

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

        // 1. Bind the 182 token lookup bridge into the ordinary calls port.
        //    GovernmentTokenLookup182Calls.bind returns GovernmentNormalizeFull174Api.Calls.
        //    It takes the original calls.ordinary() as the fallback for non-token calls.
        GovernmentNormalizeFull174Api.Calls tokenCalls = GovernmentTokenLookup182Calls.bind(
                entry.imageBaseBits(),
                memory,
                calls.ordinary(),
                pause,
                tokenBudget
        );

        // 2. Construct the new Calls record for the whole assembly.
        //    Replace ONLY ordinary() with tokenCalls. Preserve all other ports.
        GovernmentWhole4798Api.Calls newCalls = new GovernmentWhole4798Api.Calls(
                calls.initial(),
                calls.lookup(),
                tokenCalls,
                calls.lookup155(),
                calls.prefix153(),
                calls.post153()
        );

        // 3. Delegate to the existing 181 root assembly.
        //    181 will internally bind the 178 root and 176 helper using the provided newCalls.
        return GovernmentWholeRoot181.execute(
                entry,
                memory,
                newCalls,
                budgets,
                cpu,
                mxcsrBoundary,
                deepInputs,
                helperBudget
        );
    }
}
