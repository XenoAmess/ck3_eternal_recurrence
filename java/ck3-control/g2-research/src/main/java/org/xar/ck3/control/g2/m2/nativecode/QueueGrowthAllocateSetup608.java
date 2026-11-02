package org.xar.ck3.control.g2.m2.nativecode;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppend597Api.Memory;

public final class QueueGrowthAllocateSetup608 {
    private QueueGrowthAllocateSetup608() { }

    public static long prepare(Registers r, Memory memory) {
        // CMP ESI,EAX / CMOVL EBP,EAX (signed 32-bit comparison)
        int esi = (int)r.rsi;
        int eax = (int)r.rax;
        if (esi < eax) {
            r.rbp = Integer.toUnsignedLong(eax);
        }
        // MOV RAX, QWORD PTR [RCX]
        r.rax = memory.readQword(r.rcx);
        // MOV EDX, EBP
        r.rdx = r.rbp;
        // SHL RDX, 3
        r.rdx <<= 3;
        // Read target QWORD PTR [RAX+8]
        return memory.readQword(r.rax + 8);
    }
}