package org.xar.ck3.research.m3.e900239;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.e900239.E900Api239.Input;
import org.xar.ck3.research.m3.e900239.E900Api239.Ports;

/** Normal supplied-storage tail projection of exact70B424E900; no physical CPU/EH state. */
public final class E900Target424E900 {
    private E900Target424E900() { }

    public static long execute(NativeTaskMemory memory, Ports ports, Input input) {
        long base = input.moduleBase();
        int entryEcxBits = input.entryEcxBits();

        // LEA addresses (RIP-relative, not reads)
        long r9 = base + 0x4426F30L;
        long r8 = base + 0x4426F28L;
        long rdx = base + 0x4420C50L;

        // Direct call to 424E448
        long rax = ports.call424e448(memory, 0x424E922L, 5, rdx, r8, r9);

        // Branch on full 64-bit RAX
        if (rax != 0L) {
            // Fresh single readPointer for slot 43DBBA8
            long actualTarget = memory.readPointer(base + 0x43DBBA8L);
            // Actual tail call 43dbba8
            return ports.tail43dbba8(memory, 0x424E933L, actualTarget, rax, entryEcxBits);
        } else {
            // Fresh single readPointer for slot 43DA460
            long actualTarget = memory.readPointer(base + 0x43DA460L);
            // Actual tail call 43da460
            return ports.tail43da460(memory, 0x424E93FL, actualTarget, 0L, entryEcxBits);
        }
    }
}