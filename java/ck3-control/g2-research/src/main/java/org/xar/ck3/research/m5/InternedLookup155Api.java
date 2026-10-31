package org.xar.ck3.research.m5;
import org.xar.ck3.research.m5.GovernmentTierLookupKey150.LookupKey32;
/** Actual3F4F8E0 owned-memory normal-path ports. No native pointer or availability is minted. */
public final class InternedLookup155Api {
    private InternedLookup155Api() { }
    public record Entry(long imageBaseBits, LookupKey32 nativeStringKey) { }
    /** Missing/invalid owned memory must throw at its actual read; never invent zero or fallback. */
    public interface Memory extends GovernmentCaller153Api.Memory {
        int readUnsignedWord(long addressBits);
        void writeQword(long addressBits, long valueBits);
        void writeWord(long addressBits, int unsigned16Bits);
        void writeByte(long addressBits, int unsigned8Bits);
    }
    /** Each method is one exact externally supplied effect; normal return is not assumed in advance. */
    public interface Calls {
        long readGsQword58();
        void pauseSpin();
        void call4223A84(long guardAddressBits);
        void call4223F24(long callbackAddressBits);
        void call4223A24(long guardAddressBits);
    }
}
