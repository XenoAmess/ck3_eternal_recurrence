package org.xar.ck3.research.m3;

/** Source379078B..37907ED, finite captured-end domain; no added validity guards. */
public final class RegistryCandidateSelect178 {
    private RegistryCandidateSelect178() { }

    public static long select(RegistryConsumerApi176.Memory memory, long begin, long end) {
        long bestPointer = 0L;
        int bestScore = -1;
        long row = begin;
        while (row != end) {
            int score = (memory.readUnsigned8(row + 0x22L) & 0xff) == 0 ? 1 : 0;
            int at21 = memory.readUnsigned8(row + 0x21L) & 0xff;
            if (at21 == 0) {
                score += 2;
            }
            int at20 = memory.readUnsigned8(row + 0x20L) & 0xff;
            if (at20 == 2) {
                score += 4;
            }
            if (score > bestScore) {
                bestScore = score;
                bestPointer = row;
            }
            row += 0x28L;
        }
        return bestPointer;
    }
}
