package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;

public final class GovernmentMemoryFillRep207 {
    private GovernmentMemoryFillRep207() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentMemoryFill206Api.Memory memory,
            boolean directionFlagSet,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));

        // PUSH RDI
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.rdi);

        // MOV EAX, EDX (zero-extend low DWORD into RAX, RDX unchanged)
        r.rax = Integer.toUnsignedLong((int) r.rdx);

        // MOV RDI, RCX
        r.rdi = r.rcx;

        // MOV RCX, R8
        r.rcx = r.r8;

        // REP STOSB at 0x4226EF9
        // Loop while RCX != 0 (full 64-bit count)
        while (r.rcx != 0) {
            budget.beforeStep(0x4226EF9L, r.rdi);
            // Write AL (low byte of RAX) at current RDI
            memory.writeByte(r.rdi, (int) r.rax);
            // Update RDI by direction
            r.rdi += directionFlagSet ? -1 : 1;
            // Decrement RCX modulo 64-bit
            r.rcx--;
        }

        // MOV RAX, R11
        r.rax = r.r11;

        // POP RDI
        r.rdi = memory.readQword(r.rsp);
        r.rsp += 8;

        // RET
        long returnRip = memory.readQword(r.rsp);
        r.rsp += 8;

        return new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),
            returnRip,
            r.rsp,
            r.nonvolatileBits());
    }
}
