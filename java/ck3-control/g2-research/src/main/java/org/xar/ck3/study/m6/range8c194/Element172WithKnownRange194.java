package org.xar.ck3.study.m6.range8c194;

import org.xar.ck3.study.m6.element172.Element172Candidate;
import org.xar.ck3.study.m6.element172.Element172Inputs;

public final class Element172WithKnownRange194 {
    private Element172WithKnownRange194() { }

    public interface Calls extends Range8c194Inputs.Calls {
        void copy4_add0d0(long destinationHeader, long rdxZero, long begin, long end);
    }

    public static long assign(Element172Inputs.Input input, Range8c194Inputs.Memory memory, Calls calls) {
        // Adapter that routes copy16 to Range8c194Candidate and delegates copy4 to the provided Calls
        Element172Inputs.Calls adapter = new Element172Inputs.Calls() {
            @Override
            public void copy16_8c70b0(long destinationHeader, long rdxZero, long begin, long end) {
                // Construct the Range8c194Inputs.Input from the actual arguments
                Range8c194Inputs.Input rangeInput = new Range8c194Inputs.Input(
                    destinationHeader,
                    rdxZero,
                    begin,
                    end
                );
                // Invoke the frozen core target
                Range8c194Candidate.apply(rangeInput, memory, calls);
            }

            @Override
            public void copy4_add0d0(long destinationHeader, long rdxZero, long begin, long end) {
                // Delegate directly to the provided Calls interface
                calls.copy4_add0d0(destinationHeader, rdxZero, begin, end);
            }
        };

        // Invoke the existing mature upper component
        return Element172Candidate.assign(input, memory, adapter);
    }
}