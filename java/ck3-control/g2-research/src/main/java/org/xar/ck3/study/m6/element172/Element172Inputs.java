package org.xar.ck3.study.m6.element172;

public final class Element172Inputs {
    private Element172Inputs() { }
    public record Input(long destinationRaw64,long sourceRaw64,long imageBaseRaw64) { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        int read8(long address);
        void write32(long address,int value);
        void write64(long address,long value);
        void write8(long address,int value);
    }
    public interface Calls {
        void copy16_8c70b0(long destinationHeader,long rdxZero,long begin,long end);
        void copy4_add0d0(long destinationHeader,long rdxZero,long begin,long end);
    }
}
