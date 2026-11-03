package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;
import org.xar.ck3.study.m6.range8c194.Element172WithKnownRange194;
import org.xar.ck3.study.m6.copy4add200.Copy4Add200Inputs;
import org.xar.ck3.study.m6.copy4add200.Copy4Add200Candidate;

public final class Element172BothGrowth634 {
    private Element172BothGrowth634() { }

    public static long assign(Element172Inputs.Input input, Range8c194Inputs.Memory memory, Range8c194Inputs.Calls range16Foreign, Copy4Add200Inputs.Calls range4Foreign) {
        if (input == null) throw new NullPointerException("input");
        if (memory == null) throw new NullPointerException("memory");
        if (range16Foreign == null) throw new NullPointerException("range16Foreign");
        if (range4Foreign == null) throw new NullPointerException("range4Foreign");

        Element172WithKnownRange194.Calls adapter = new Element172WithKnownRange194.Calls() {
            @Override
            public long virtual8(long targetRaw64, long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) {
                return range16Foreign.virtual8(targetRaw64, rcxRaw64, rdxRaw64, r8Raw64, r9Raw64);
            }

            @Override
            public void virtual16(long targetRaw64, long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) {
                range16Foreign.virtual16(targetRaw64, rcxRaw64, rdxRaw64, r8Raw64, r9Raw64);
            }

            @Override
            public void direct8f8550(long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64) {
                range16Foreign.direct8f8550(rcxRaw64, rdxRaw64, r8Raw64, r9Raw64);
            }

            @Override
            public void copy4_add0d0(long destinationHeader, long rdxZero, long begin, long end) {
                Copy4Add200Inputs.Input copy4Input = new Copy4Add200Inputs.Input(
                    destinationHeader,
                    rdxZero,
                    begin,
                    end
                );
                Copy4Add200Candidate.apply(copy4Input, memory, range4Foreign);
            }
        };

        return Element172WithKnownRange194.assign(input, memory, adapter);
    }
}