package org.xar.ck3.study.m6.reverse4220aa4_202;

import org.xar.ck3.study.m6.range9d201.Range9d201Candidate;
import org.xar.ck3.study.m6.range9d201.Range9d201Inputs;
import org.xar.ck3.study.m6.reverse4220aa4_202.Reverse4220aa4Inputs;

public final class Range9dWithKnown4220aa4_202 {
    public static long apply(Range9d201Inputs.Input input, Reverse4220aa4Inputs.Memory memory, long imageBaseRaw64, Reverse4220aa4Inputs.Effects effects) {
        // Delegate to the mature Range9d201Candidate logic exactly once.
        // The Calls interface implementation adapts the actual RCX/RDX values from the 201 source
        // to the new core's Input signature, using the provided imageBaseRaw64.
        // Incoming R8/R9 are ignored as per the contract (new core does not require them).
        // The return value of the core is ignored; the outer 201 return value is preserved.

        Range9d201Inputs.Calls calls = new Range9d201Inputs.Calls() {
            @Override
            public void first4220aa4(long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) {
                // Construct Input for the new core using actual RCX/RDX and separate imageBase
                Reverse4220aa4Inputs.Input coreInput = new Reverse4220aa4Inputs.Input(rcxRaw64, rdxRaw64, imageBaseRaw64);
                // Call the new core. Return value is ignored as per contract.
                Reverse4220aa4Candidate.apply(coreInput, memory, effects);
            }

            @Override
            public void later4220aa4(long rcxRaw64, long rdxRaw64) {
                // Construct Input for the new core using actual RCX/RDX and separate imageBase
                Reverse4220aa4Inputs.Input coreInput = new Reverse4220aa4Inputs.Input(rcxRaw64, rdxRaw64, imageBaseRaw64);
                // Call the new core. Return value is ignored as per contract.
                Reverse4220aa4Candidate.apply(coreInput, memory, effects);
            }
        };

        // Execute the mature 201 algorithm with the adapted calls
        return Range9d201Candidate.apply(input, calls);
    }
}