package org.xar.ck3.study.m6.range8c194;

public final class Range8c194Inputs {
    private Range8c194Inputs() { }
    public record Input(long destinationHeaderRaw64,long rdxRaw64,long beginRaw64,long endRaw64) { }
    public record Word16(long lowRaw64,long highRaw64) { }
    public interface Memory extends org.xar.ck3.study.m6.element172.Element172Inputs.Memory {
        Word16 read16(long address);
        void write16(long address,Word16 value);
    }
    public interface Calls {
        long virtual8(long targetRaw64,long rcxRaw64,long rdxRaw64,long r8Raw64,long r9Raw64);
        void virtual16(long targetRaw64,long rcxRaw64,long rdxRaw64,long r8Raw64,long r9Raw64);
        void direct8f8550(long rcxRaw64,long rdxRaw64,long r8Raw64,long r9Raw64);
    }
}
