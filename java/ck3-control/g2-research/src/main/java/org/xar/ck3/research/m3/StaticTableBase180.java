package org.xar.ck3.research.m3;
import org.xar.ck3.research.m3.C3e150Api180.Memory;
import org.xar.ck3.research.m3.C3e150Api180.Ports;

public final class StaticTableBase180 {
    private StaticTableBase180() { }

    public static long get(Memory memory, Ports ports, long moduleBase) {
        // 1. GS58 observation
        long gs58 = ports.gs58(memory);

        // 2. Pointer read from gs58
        long tlsModule = memory.readPointer(gs58);

        // 3. DWORD read from tlsModule + 10h
        long tlsEpochAddr = tlsModule + 0x10L;
        int tlsEpoch = memory.readInt32(tlsEpochAddr);

        // 4. Guard address calculation (moduleBase + 5D1F630)
        long guardAddr = moduleBase + 0x5D1F630L;

        // 5. Read guard DWORD
        int guardBefore = memory.readInt32(guardAddr);

        // 6. Branch: CMP guard, EAX; JG header block if signed guard > signed tlsEpoch
        //    If guard <= tlsEpoch, jump to C3E170 (LEA return path)
        if (guardBefore <= tlsEpoch) {
            // Normal return path: LEA moduleBase+5D1F5E0, RET
            long returnAddr = moduleBase + 0x5D1F5E0L;
            return returnAddr;
        }

        // Header block (C3E17C onwards)
        // 7. LEA RCX = guard address (moduleBase + 5D1F630)
        //    This is the address, not the value.
        long rcx = guardAddr;

        // 8. Call header port: call4223a84(Memory, long guard)
        //    The guard argument is the address (rcx)
        ports.call4223a84(memory, rcx);

        // 9. Fresh read of guard DWORD after header call
        int guardAfterHeader = memory.readInt32(guardAddr);

        // 10. CMP guard, FFFFFFFFh; JNE C3E170 if not equal to -1
        if (guardAfterHeader != -1) {
            // Return normally via LEA path
            long returnAddr = moduleBase + 0x5D1F5E0L;
            return returnAddr;
        }

        // 11. Byte stores when guard == -1
        //    mov byte ptr [0000000005D1F5E4h], 0
        long byteStoreAddr1 = moduleBase + 0x5D1F5E4L;
        memory.write8(byteStoreAddr1, 0);

        //    mov byte ptr [0000000005D1F60Ch], 0FFh
        long byteStoreAddr2 = moduleBase + 0x5D1F60CL;
        memory.write8(byteStoreAddr2, 0xFF);

        // 12. Call footer port: call4223a24(Memory, long guard)
        //    The guard argument is the same address (rcx)
        ports.call4223a24(memory, rcx);

        // 13. JMP C3E170 (LEA return path)
        long returnAddr = moduleBase + 0x5D1F5E0L;
        return returnAddr;
    }
}
