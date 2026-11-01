package org.xar.ck3.study.m6.copy4add200;

import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;
import org.xar.ck3.study.m6.range8c194.Element172WithKnownRange194;

public final class Element172WithKnownCopy4Add200 {
    private Element172WithKnownCopy4Add200() { }

    public static long assign(Element172Inputs.Input input, Range8c194Inputs.Memory memory, Range8c194Inputs.Calls range16Calls, Copy4Add200Inputs.Calls copy4Calls) {
        Element172WithKnownRange194.Calls adapter = new Element172WithKnownRange194.Calls() {
            @Override
            public long virtual8(long targetRaw64, long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) {
                return range16Calls.virtual8(targetRaw64, rcxRaw64, rdxRaw64, r8Raw64, r9Raw64);
            }

            @Override
            public void virtual16(long targetRaw64, long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) {
                range16Calls.virtual16(targetRaw64, rcxRaw64, rdxRaw64, r8Raw64, r9Raw64);
            }

            @Override
            public void direct8f8550(long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) {
                range16Calls.direct8f8550(rcxRaw64, rdxRaw64, r8Raw64, r9Raw64);
            }

            @Override
            public void copy4_add0d0(long destinationHeader, long rdxZero, long begin, long end) {
                Copy4Add200Inputs.Input copy4Input = new Copy4Add200Inputs.Input(
                    destinationHeader,
                    rdxZero,
                    begin,
                    end
                );
                Copy4Add200Candidate.apply(copy4Input, memory, copy4Calls);
            }
        };

        return Element172WithKnownRange194.assign(input, memory, adapter);
    }
}