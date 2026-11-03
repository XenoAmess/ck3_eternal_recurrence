package org.xar.ck3.study.m6.activity265;

import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Exact owned-memory effects of [23FD63A,23FD64F); no CALL, RET or whole-state result. */
public final class ActivityWordBlock265 {
    private ActivityWordBlock265() { }

    /**
     * Uses the same Memory object for all four source operations. The caller supplies its
     * actual image/RBP and applies only the returned final RAX on successful continuation.
     * Ordinary Memory errors escape unchanged with the effects already performed.
     */
    public static long execute(long imageBaseBits, long rbpBits,
            GovernmentCrtBoundary185Api.Memory sameMemory) {
        if (!(sameMemory instanceof FullCopy437Api.Memory words)) {
            throw new UnsupportedOperationException("Activity word block requires exact word-capable Memory");
        }
        int wordBits = words.readUnsignedWord(imageBaseBits + 0x4439524L) & 0xFFFF;
        words.writeWord(rbpBits - 0x20L, wordBits);
        int eaxBits = sameMemory.readUnsignedByte(imageBaseBits + 0x4439526L) & 0xFF;
        sameMemory.writeByte(rbpBits - 0x1EL, eaxBits);
        return Integer.toUnsignedLong(eaxBits);
    }
}
