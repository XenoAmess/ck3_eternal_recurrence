package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

public final class PendingMemoryCopy4226860 {
    private PendingMemoryCopy4226860() { }

    public static long copy(Copy4226860Api.Memory memory, long destination, long source, long bytes, long moduleBase) {
        if (Long.compareUnsigned(bytes, 15L) <= 0) {
            PendingCopySmall4226860.copy(memory, destination, source, bytes, moduleBase);
            return destination;
        }

        if (Long.compareUnsigned(bytes, 32) <= 0) {
            Bits128 first = memory.read128(source);
            Bits128 last = memory.read128(source + bytes - 16);
            memory.write128(destination, first);
            memory.write128(destination + bytes - 16, last);
            return destination;
        }

        if (Long.compareUnsigned(source, destination) < 0 && Long.compareUnsigned(destination, source + bytes) < 0) {
            PendingCopyBackward4226860.copy(memory, destination, source, bytes);
            return destination;
        }

        int cpuFeature = memory.read32(moduleBase + 0x542f098L);
        if (Integer.compareUnsigned(cpuFeature, 3) >= 0) {
            if (Long.compareUnsigned(bytes, 0x2000L) > 0 && Long.compareUnsigned(bytes, 0x180000L) <= 0) {
                int flag = memory.read8(moduleBase + 0x5c5cbb0L);
                if ((flag & 0x2) != 0) {
                    PendingCopyRep4226840.copy(memory, destination, source, bytes);
                    return destination;
                }
            }
            PendingCopyAvx4226860.copy(memory, destination, source, bytes, moduleBase);
            return destination;
        } else {
            if (Long.compareUnsigned(bytes, 0x800L) > 0) {
                int flag = memory.read8(moduleBase + 0x5c5cbb0L);
                if ((flag & 0x2) != 0) {
                    PendingCopyRep4226840.copy(memory, destination, source, bytes);
                    return destination;
                }
            }
            PendingCopySse4226860.copy(memory, destination, source, bytes, moduleBase);
            return destination;
        }
    }
}