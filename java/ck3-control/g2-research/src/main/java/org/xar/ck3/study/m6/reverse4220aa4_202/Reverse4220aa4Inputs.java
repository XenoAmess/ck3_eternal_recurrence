package org.xar.ck3.study.m6.reverse4220aa4_202;

public final class Reverse4220aa4Inputs {
    private Reverse4220aa4Inputs() { }
    public record Input(long beginRaw64,long endRaw64,long imageBaseRaw64) { }
    public record Word32(long q0Raw64,long q1Raw64,long q2Raw64,long q3Raw64) { }
    public interface Memory extends org.xar.ck3.study.m6.range8c194.Range8c194Inputs.Memory {
        Word32 read32Bytes(long address);
        void write32Bytes(long address,Word32 value);
    }
    public interface Effects { void vzeroUpper(); }
}
