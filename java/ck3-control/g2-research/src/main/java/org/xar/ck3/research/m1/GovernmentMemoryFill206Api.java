package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/** Additional instruction effects of only the captured 4226F10 normal body. */
public final class GovernmentMemoryFill206Api {
    private GovernmentMemoryFill206Api() { }

    /** All methods address the same owned storage as the inherited memory view. */
    public interface Memory extends GovernmentCrtBoundary185Api.Memory {
        /** One source MOV WORD store; only the low sixteen input bits are stored. */
        void writeWord(long addressBits, int valueBits);
        /** One source MOVNTPS store, distinct from an ordinary 128-bit store. */
        void write128NonTemporal(long addressBits, Bits128 valueBits);
        /** The source SFENCE effect, distinct from an absent operation. */
        void sfence();
    }
}
