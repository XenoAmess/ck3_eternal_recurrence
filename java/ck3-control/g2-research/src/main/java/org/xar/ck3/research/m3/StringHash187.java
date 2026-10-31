package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.StringHashApi187.Memory;
import org.xar.ck3.research.m3.StringHashApi187.Scratch;

/** Normal data effects of held135B wrapper and320B helper; excludes unused ABI homes. */
public final class StringHash187 {
    private StringHash187() { }

    public static int hash(Memory memory, long data, int lengthBits, Scratch scratch) {
        long stateAddress = scratch.sourceEntryRsp() + 8L;
        long pendingAddress = scratch.sourceEntryRsp() + 0x18L;
        memory.writeInt32(stateAddress, 0);
        memory.writeInt32(pendingAddress, 0);
        accumulate(memory, stateAddress, pendingAddress, data, lengthBits);

        int pending = memory.readInt32(pendingAddress);
        int state = memory.readInt32(stateAddress);
        int pendingCount = pending & 3;
        if (pendingCount != 0) {
            int residual = pending >>> ((4 - pendingCount) * 8);
            state ^= mixKey(residual);
        }
        int result = state ^ lengthBits;
        result ^= result >>> 16;
        result *= 0x85EBCA6B;
        result ^= result >>> 13;
        result *= 0xC2B2AE35;
        return result ^ (result >>> 16);
    }

    private static void accumulate(Memory memory, long stateAddress, long pendingAddress,
            long data, int remaining) {
        int pending = memory.readInt32(pendingAddress);
        int state = memory.readInt32(stateAddress);
        int pendingCount = pending & 3;
        int prefix = (-pendingCount) & 3;
        if (prefix != 0 && prefix <= remaining) {
            remaining -= prefix;
            do {
                pending = (memory.readUnsigned8(data) << 24) | (pending >>> 8);
                data++;
                prefix--;
                pendingCount++;
                if (pendingCount == 4) {
                    pending = mixKey(pending);
                    state = mixState(state, pending);
                    pendingCount = 0;
                }
            } while (prefix != 0);
        }

        int rounded = (remaining + ((remaining >> 31) & 3)) & ~3;
        long end = data + (long) rounded;
        while (Long.compareUnsigned(data, end) < 0) {
            int word = memory.readInt32(data);
            data += 4L;
            state = mixState(state, mixKey(word));
        }
        remaining -= rounded;
        if (remaining != 0) {
            do {
                pending = (memory.readUnsigned8(data) << 24) | (pending >>> 8);
                data++;
                remaining--;
                pendingCount++;
                if (pendingCount == 4) {
                    pending = mixKey(pending);
                    state = mixState(state, pending);
                    pendingCount = 0;
                }
            } while (remaining != 0);
        }
        memory.writeInt32(stateAddress, state);
        memory.writeInt32(pendingAddress, (pending & 0xFFFFFF00) | pendingCount);
    }

    private static int mixKey(int value) {
        return Integer.rotateLeft(value * 0xCC9E2D51, 15) * 0x1B873593;
    }

    private static int mixState(int state, int mixedKey) {
        return (Integer.rotateLeft(state ^ mixedKey, 13) + 0xFADDAF14) * 5;
    }
}
