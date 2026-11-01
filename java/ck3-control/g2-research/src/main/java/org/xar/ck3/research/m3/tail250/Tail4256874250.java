package org.xar.ck3.research.m3.tail250;

import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;

public final class Tail4256874250 {
    private Tail4256874250() { }

    public static long execute(Callee68d4Memory246 memory, long moduleBase, long entryRcx) {
        if (entryRcx == 0L) {
            return 0x000000007FFFFFFFL;
        }

        long sentinel = moduleBase + 0x44271D0L;
        if (entryRcx == sentinel) {
            return 0x000000007FFFFFFFL;
        }

        int oldBits = memory.exchangeAddInt32(entryRcx + 0x15CL, 1);
        int resultInt = oldBits + 1;
        return resultInt & 0xFFFFFFFFL;
    }
}