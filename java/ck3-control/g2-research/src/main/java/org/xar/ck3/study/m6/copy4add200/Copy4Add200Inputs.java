package org.xar.ck3.study.m6.copy4add200;

public final class Copy4Add200Inputs {
    private Copy4Add200Inputs() { }
    public record Input(long headerRaw64, long indexRaw64, long beginRaw64, long endRaw64) { }
    public interface Calls {
        long virtual8(long targetRaw64, long rcxRaw64, long bytesRaw64, long alignmentRaw64, long entryEndR9Raw64);
        void virtual16(long targetRaw64, long rcxRaw64, long oldBaseRaw64, long alignmentRaw64);
        void copy4226860(long destinationRaw64, long sourceRaw64, long bytesRaw64);
        void range9d0950(long beginRaw64, long middleRaw64, long endRaw64, long baseR9Raw64);
    }
}
