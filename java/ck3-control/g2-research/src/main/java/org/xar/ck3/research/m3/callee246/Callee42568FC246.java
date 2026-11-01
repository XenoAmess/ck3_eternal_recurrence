package org.xar.ck3.research.m3.callee246;

import org.xar.ck3.research.m3.callee246.Callee68fcApi246.Memory;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246.Ports;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246.Input;

/** Supplied-storage business effects of 42568FC; physical CPU and EH excluded. */
public final class Callee42568FC246 {
    private Callee42568FC246() { }

    public static void execute(Memory memory, Ports ports, Input input) {
        long moduleBase = input.moduleBase();
        long entryRcx = input.entryRcx();

        // 6900: TEST rcx, rcx; JE 6903
        if (entryRcx == 0) {
            return;
        }

        // 6909: OR r9d, 0xffffffff -> R9 = 0x00000000FFFFFFFF
        long r9 = 0x00000000FFFFFFFFL;

        // 690D: LOCK ADD DWORD[rcx+0x10], r9d
        memory.atomicAddInt32(entryRcx + 0x10L, -1);

        // 6912: MOV rax, QWORD[rcx+0xE0]
        long rax = memory.readPointer(entryRcx + 0xE0L);
        // 6919: TEST rax, rax; JE 6922
        if (rax != 0) {
            // 691E: LOCK ADD DWORD[rax], r9d
            memory.atomicAddInt32(rax, -1);
        }

        // 6922: MOV rax, QWORD[rcx+0xF0]
        rax = memory.readPointer(entryRcx + 0xF0L);
        // 6929: TEST rax, rax; JE 6932
        if (rax != 0) {
            // 692E: LOCK ADD DWORD[rax], r9d
            memory.atomicAddInt32(rax, -1);
        }

        // 6932: MOV rax, QWORD[rcx+0xE8]
        rax = memory.readPointer(entryRcx + 0xE8L);
        // 6939: TEST rax, rax; JE 6942
        if (rax != 0) {
            // 693E: LOCK ADD DWORD[rax], r9d
            memory.atomicAddInt32(rax, -1);
        }

        // 6942: MOV rax, QWORD[rcx+0x100]
        rax = memory.readPointer(entryRcx + 0x100L);
        // 6949: TEST rax, rax; JE 6952
        if (rax != 0) {
            // 694E: LOCK ADD DWORD[rax], r9d
            memory.atomicAddInt32(rax, -1);
        }

        // 6952: LEA rax, [rcx+0x38] -> cursorRAX
        long cursorRax = entryRcx + 0x38L;
        // 6956: MOV r8d, 6 -> R8 = 6
        long r8 = 6L;

        // Loop: 6 iterations
        // 695C: LEA rdx, [rip+0x11d8b35] -> sentinelRVA = moduleBase + 0x542F498
        long sentinelRva = moduleBase + 0x542F498L;
        long liveRdx = 0L;

        while (r8 != 0) {
            // 695C: LEA rdx, [rip+0x11d8b35] -> RDX = sentinelRVA
            liveRdx = sentinelRva;

            // 6963: CMP QWORD[cursor-0x10], rdx
            long val1 = memory.readPointer(cursorRax - 0x10L);
            if (val1 != liveRdx) {
                // 6969: MOV rdx, QWORD[cursor]
                liveRdx = memory.readPointer(cursorRax);
                // 696C: TEST rdx, rdx; JE 6975
                if (liveRdx != 0) {
                    // 6971: LOCK ADD DWORD[rdx], r9d
                    memory.atomicAddInt32(liveRdx, -1);
                }
            }

            // 6975: CMP QWORD[cursor-0x18], 0
            long val2 = memory.readPointer(cursorRax - 0x18L);
            if (val2 != 0) {
                // 697C: MOV rdx, QWORD[cursor-8]
                liveRdx = memory.readPointer(cursorRax - 8L);
                // 6980: TEST rdx, rdx; JE 6989
                if (liveRdx != 0) {
                    // 6985: LOCK ADD DWORD[rdx], r9d
                    memory.atomicAddInt32(liveRdx, -1);
                }
            }

            // 6989: ADD rax, 0x20
            cursorRax += 0x20L;
            // 698D: SUB r8, 1
            r8 -= 1L;
            // 6991: JNE 695C
        }

        // 6993: MOV rcx, QWORD[rcx+0x120]
        long finalRcx = memory.readPointer(entryRcx + 0x120L);

        // 699A: CALL 42568D4
        // Pass: knownRcx=finalRcx, knownRdx=liveRdx, liveRax=cursorRax, knownR8=0, knownR9=0x00000000FFFFFFFF
        ports.call42568d4(memory, 0x425699AL, finalRcx, liveRdx, cursorRax, 0L, 0x00000000FFFFFFFFL);
    }
}