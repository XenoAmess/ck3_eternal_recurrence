package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;

public final class PendingRangeOrder9CF240 {
    private PendingRangeOrder9CF240() { }

    public static long apply(RangeOrder410Api.Memory memory, RangeOrder410Api.LoopBudget budget, RangeOrder410Api.Input input) {
        long first = input.first();
        long middle = input.middle();
        long last = input.last();
        long moduleBase = input.moduleBase();

        if (first == middle) {
            return last;
        }
        if (middle == last) {
            return first;
        }

        PendingByteReverse42208E8.reverse(memory, budget, first, middle, moduleBase);
        PendingByteReverse42208E8.reverse(memory, budget, middle, last, moduleBase);
        PendingByteReverse42208E8.reverse(memory, budget, first, last, moduleBase);

        return last + (first - middle);
    }
}