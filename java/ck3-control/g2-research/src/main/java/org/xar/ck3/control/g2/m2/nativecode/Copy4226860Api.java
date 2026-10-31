package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
/** Frozen observable Memory API; register/flags/EH outside normal study profile. */
public final class Copy4226860Api {
    private Copy4226860Api() { }
    public record Bits256(Bits128 low128,Bits128 high128) { }
    public interface Memory {
        int read8(long address);
        int read16(long address);
        int read32(long address);
        long read64(long address);
        Bits128 read128(long address);
        Bits256 read256(long address);
        void write8(long address,int value);
        void write16(long address,int value);
        void write32(long address,int value);
        void write64(long address,long value);
        void write128(long address,Bits128 value);
        void write256(long address,Bits256 value);
        void storeFence();
    }
}
