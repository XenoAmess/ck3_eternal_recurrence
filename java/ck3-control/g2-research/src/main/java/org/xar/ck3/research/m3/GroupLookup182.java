package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.GroupLookupApi182.Memory;
import org.xar.ck3.research.m3.GroupLookupApi182.Ports;

/** Direct-entry normal data effects of held 314B3793900; supplied finite observations. */
public final class GroupLookup182 {
    private GroupLookup182() { }

    public static long find(Memory memory, Ports ports, long moduleBase, long receiver, int hash32) {
        boolean shared = memory.readUnsigned8(receiver + 0xEE0L) == 0;
        long lockAddress = receiver + 0xEA0L;
        if (shared) {
            int old = ports.atomicXadd32(memory, lockAddress, 2);
            while ((old & 1) != 0) {
                ports.atomicXadd32(memory, lockAddress, -2);
                while ((memory.readInt32(lockAddress) & 1) != 0) {
                    ports.pause(memory);
                }
                old = ports.atomicXadd32(memory, lockAddress, 2);
            }
        }

        int mask = memory.readInt32(receiver + 0x18CL);
        long table = memory.readPointer(receiver + 0x180L);
        long row = table + (((long) mask & (long) hash32) * 3L) * 8L;
        int distance = 1;
        boolean fallback = memory.readUnsigned8(row + 4L) < distance;
        if (!fallback) {
            while (memory.readInt32(row + 8L) != hash32) {
                row += 0x18L;
                distance = (distance + 1) & 0xFF;
                if (distance > memory.readUnsigned8(row + 4L)) {
                    fallback = true;
                    break;
                }
            }
        }
        if (fallback) {
            int index = memory.readUnsigned8(receiver + 0x190L);
            index = index + 1 + mask;
            row = table + ((long) index * 3L) * 8L;
        }

        long result = memory.readUnsigned8(row + 4L) == 0xFF
                ? memory.readPointer(moduleBase + 0x5D37D78L)
                : memory.readPointer(row + 0x10L);
        if (shared) {
            ports.atomicXadd32(memory, lockAddress, -2);
        }
        return result;
    }
}
