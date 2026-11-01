package org.xar.ck3.study.m6.range9d201;

import org.xar.ck3.study.m6.copy4add200.Copy4Add200Candidate;
import org.xar.ck3.study.m6.copy4add200.Copy4Add200Inputs;
import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.range9d201.Range9d201Candidate;
import org.xar.ck3.study.m6.range9d201.Range9d201Inputs;

public final class Copy4AddWithKnownRange9d201 {
    private Copy4AddWithKnownRange9d201() { }

    public static void apply(Copy4Add200Inputs.Input input, Element172Inputs.Memory memory,
                             Copy4Add200Inputs.Calls passthrough, Range9d201Inputs.Calls rangeCalls) {
        Copy4Add200Candidate.apply(input, memory, new Copy4Add200Inputs.Calls() {
            @Override
            public long virtual8(long targetRaw64, long rcxRaw64, long bytesRaw64, long alignmentRaw64, long entryEndR9Raw64) {
                return passthrough.virtual8(targetRaw64, rcxRaw64, bytesRaw64, alignmentRaw64, entryEndR9Raw64);
            }

            @Override
            public void virtual16(long targetRaw64, long rcxRaw64, long oldBaseRaw64, long alignmentRaw64) {
                passthrough.virtual16(targetRaw64, rcxRaw64, oldBaseRaw64, alignmentRaw64);
            }

            @Override
            public void copy4226860(long destinationRaw64, long sourceRaw64, long bytesRaw64) {
                passthrough.copy4226860(destinationRaw64, sourceRaw64, bytesRaw64);
            }

            @Override
            public void range9d0950(long beginRaw64, long middleRaw64, long endRaw64, long baseR9Raw64) {
                Range9d201Candidate.apply(
                    new Range9d201Inputs.Input(beginRaw64, middleRaw64, endRaw64, baseR9Raw64),
                    rangeCalls
                );
            }
        });
    }
}