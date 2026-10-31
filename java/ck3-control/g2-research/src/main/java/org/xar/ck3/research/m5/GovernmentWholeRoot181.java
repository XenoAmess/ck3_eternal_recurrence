package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173Api;
import org.xar.ck3.research.m5.GovernmentWholeNormalized175;
import org.xar.ck3.research.m5.GovernmentWholeRoot181Api;
import org.xar.ck3.research.m5.GovernmentRoot178Calls;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Calls;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/**
 * Thin assembly for GovernmentWholeRoot181.
 * Wraps the existing normalized whole175 by injecting the 178 root and 176 helper
 * into the ordinary calls port before delegating to 175.
 */
public final class GovernmentWholeRoot181 {
    private GovernmentWholeRoot181() { }

    public static GovernmentWhole4798Api.Result execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentWholeRoot181Api.Memory memory,
            GovernmentWhole4798Api.Calls calls,
            GovernmentWhole4798Api.Budgets budgets,
            GovernmentLookupLoop580Api.Cpu cpu,
            GovernmentWhole4798Api.MxcsrBoundary mxcsrBoundary,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs,
            GovernmentLookupHelper176Api.LoopBudget helperBudget) {

        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(budgets);
        Objects.requireNonNull(cpu);
        Objects.requireNonNull(mxcsrBoundary);
        Objects.requireNonNull(deepInputs);
        Objects.requireNonNull(helperBudget);

        // 1. Bind the 178 root into the ordinary calls port.
        //    GovernmentRoot178Calls.bind returns GovernmentLookupHelper176Api.Calls.
        GovernmentLookupHelper176Api.Calls rootCalls = GovernmentRoot178Calls.bind(
                entry.imageBaseBits(),
                memory,
                calls.ordinary()
        );

        // 2. Bind the 176 helper into the normalizer calls port.
        //    GovernmentLookupHelper176Calls.bind returns GovernmentNormalizeFull174Api.Calls.
        //    It takes the rootCalls as the fallback for non-helper calls.
        GovernmentNormalizeFull174Api.Calls helperCalls = GovernmentLookupHelper176Calls.bind(
                entry.imageBaseBits(),
                memory,
                rootCalls,
                helperBudget
        );

        // 3. Construct the new Calls record for the whole assembly.
        //    Replace ONLY ordinary() with helperCalls. Preserve all other ports.
        GovernmentWhole4798Api.Calls newCalls = new GovernmentWhole4798Api.Calls(
                calls.initial(),
                calls.lookup(),
                helperCalls,
                calls.lookup155(),
                calls.prefix153(),
                calls.post153()
        );

        // 4. Delegate to the existing 175 normalized assembly.
        //    175 will internally bind the 174 normalizer using the provided helperCalls.
        return GovernmentWholeNormalized175.execute(
                entry,
                memory,
                newCalls,
                budgets,
                cpu,
                mxcsrBoundary,
                deepInputs
        );
    }
}
