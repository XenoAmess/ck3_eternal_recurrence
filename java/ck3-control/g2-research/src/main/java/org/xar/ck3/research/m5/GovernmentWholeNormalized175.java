package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentWhole4798Api;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173Api;
import org.xar.ck3.research.m5.GovernmentWholeNormalized175Api;
import org.xar.ck3.research.m5.GovernmentInitialFrame162Api;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Calls;

/**
 * Thin assembly for GovernmentWholeNormalized175.
 * Wraps the ordinary calls port with the 174 normalizer bridge before delegating to 173.
 */
public final class GovernmentWholeNormalized175 {
    private GovernmentWholeNormalized175() { }

    public static GovernmentWhole4798Api.Result execute(GovernmentInitialFrame162Api.Entry entry,
            GovernmentWholeNormalized175Api.Memory memory,
            GovernmentWhole4798Api.Calls calls,
            GovernmentWhole4798Api.Budgets budgets,
            GovernmentLookupLoop580Api.Cpu cpu,
            GovernmentWhole4798Api.MxcsrBoundary mxcsrBoundary,
            GovernmentWholeConcrete173Api.DeepInputs deepInputs) {

        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(budgets);
        Objects.requireNonNull(cpu);
        Objects.requireNonNull(mxcsrBoundary);
        Objects.requireNonNull(deepInputs);

        // Bind the ordinary calls using the 174 normalizer bridge
        GovernmentPrimaryTail155Api.Calls normalizedOrdinary = GovernmentNormalizeFull174Calls.bind(
                entry.imageBaseBits(),
                memory,
                calls.ordinary()
        );

        // Construct the new Calls record preserving other ports
        GovernmentWhole4798Api.Calls newCalls = new GovernmentWhole4798Api.Calls(
                calls.initial(),
                calls.lookup(),
                normalizedOrdinary,
                calls.lookup155(),
                calls.prefix153(),
                calls.post153()
        );

        // Delegate to the existing 173 concrete assembly
        return GovernmentWholeConcrete173.execute(
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
