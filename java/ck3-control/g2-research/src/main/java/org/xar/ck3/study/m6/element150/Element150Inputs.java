package org.xar.ck3.study.m6.element150;

public final class Element150Inputs {
    private Element150Inputs() { }
    public record Input(long destinationRaw64,long sourceRaw64,long imageBaseRaw64) { }
    public interface Memory {
        int read32(long address);long read64(long address);int read8(long address);
        void write32(long address,int value);void write64(long address,long value);void write8(long address,int value);
    }
    public interface Calls {
        void copy16_21a5050(long destinationHeader,long sourceHeader);
        void copy4_b2eee0(long destinationHeader,long sourceHeader);
    }
}
