package org.xar.ck3.research.m3.callee246;

import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;

/** Normal-CFG-closed 37B entry 42568D4; physical CPU/EH/unwind excluded. */
public final class Callee42568D4247 {
    private Callee42568D4247() { }

    public static long execute(Callee68d4Memory246 memory, long moduleBase, long entryRcx) {
        // 42568D4: TEST rcx, rcx; JE 42568F3
        if (entryRcx == 0) {
            // 42568F3: MOV eax, 0x7fffffff; RET
            return 0x000000007FFFFFFFL;
        }

        // 42568D9: LEA rax, [rip + 0x1d08f0] -> sentinel address
        long sentinelRva = moduleBase + 0x44271D0L;

        // 42568E0: CMP rcx, rax; JE 42568F3
        if (entryRcx == sentinelRva) {
            // 42568F3: MOV eax, 0x7fffffff; RET
            return 0x000000007FFFFFFFL;
        }

        // 42568E5: OR eax, 0xffffffff -> deltaBits = -1
        // 42568E8: LOCK XADD DWORD[rcx + 0x15c], eax
        // Returns old int32 bits, updates memory with wrapping add.
        int oldBits = memory.exchangeAddInt32(entryRcx + 0x15CL, -1);

        // 42568F0: DEC eax -> oldBits - 1 (32-bit wrapping)
        int resultInt = oldBits - 1;

        // 42568F2: RET -> full64 zeroextended result
        return resultInt & 0xFFFFFFFFL;
    }
}