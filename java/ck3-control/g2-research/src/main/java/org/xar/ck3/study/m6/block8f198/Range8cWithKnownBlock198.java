package org.xar.ck3.study.m6.block8f198;

import org.xar.ck3.study.m6.range8c194.Range8c194Candidate;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;

public final class Range8cWithKnownBlock198 {
    private Range8cWithKnownBlock198() { }

    public interface Calls {
        long virtual8(long targetRaw64, long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64);
        void virtual16(long targetRaw64, long rcxRaw64, long rdxRaw64, long r8Raw64, long r9Raw64);
    }

    public static void apply(Range8c194Inputs.Input input, Range8c194Inputs.Memory memory, Calls calls) {
        Range8c194Candidate.apply(input, memory, new Range8c194Inputs.Calls() {
            @Override public long virtual8(long target, long rcx, long rdx, long r8, long r9) {
                return calls.virtual8(target, rcx, rdx, r8, r9);
            }
            @Override public void virtual16(long target, long rcx, long rdx, long r8, long r9) {
                calls.virtual16(target, rcx, rdx, r8, r9);
            }
            @Override public void direct8f8550(long rcx, long rdx, long r8, long r9) {
                BlockRange8f198Candidate.apply(new BlockRange8f198Inputs.Input(rcx, rdx, r8, r9), memory);
            }
        });
    }
}
