package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import java.util.Objects;

public final class GovernmentRegistryTable186 {
    public static GovernmentCallee164Api.NormalReturn execute(
            GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(entry);
        long rsp = entry.frameRspBits();
        long imageBase = entry.imageBaseBits();

        // 0424DEEC: mov qword ptr [rsp + 0x10], rdx
        memory.writeQword(rsp + 0x10, r.rdx);
        // 0424DEF1: mov qword ptr [rsp + 8], rcx
        memory.writeQword(rsp + 8, r.rcx);
        // 0424DEF6: push rbp
        rsp -= 8;
        memory.writeQword(rsp, r.rbp);
        // 0424DEF7: mov rbp, rsp
        r.rbp = rsp;
        // 0424DEFA: sub rsp, 0x40
        rsp -= 0x40;

        // 0424DEFE: lea rax, [rbp + 0x10]
        r.rax = r.rbp + 0x10;
        // 0424DF02: mov qword ptr [rbp - 0x18], rax
        memory.writeQword(r.rbp - 0x18, r.rax);
        // 0424DF06: lea r9, [rbp + 0x28]
        r.r9 = r.rbp + 0x28;
        // 0424DF0A: lea rax, [rbp + 0x18]
        r.rax = r.rbp + 0x18;
        // 0424DF0E: mov qword ptr [rbp - 0x10], rax
        memory.writeQword(r.rbp - 0x10, r.rax);
        // 0424DF12: lea r8, [rbp - 0x18]
        r.r8 = r.rbp - 0x18;
        // 0424DF16: mov eax, 2
        r.rax = 2;
        // 0424DF1B: lea rdx, [rbp - 0x20]
        r.rdx = r.rbp - 0x20;
        // 0424DF1F: lea rcx, [rbp + 0x20]
        r.rcx = r.rbp + 0x20;
        // 0424DF23: mov dword ptr [rbp + 0x28], eax
        memory.writeDword(r.rbp + 0x28, (int)r.rax);
        // 0424DF26: mov dword ptr [rbp - 0x20], eax
        memory.writeDword(r.rbp - 0x20, (int)r.rax);

        // 0424DF29: call 0x424db38
        // Write return address at rsp-8 (pre-CALL site RSP W, push continuation)
        memory.writeQword(rsp - 8, imageBase + 0x424DF2E);

        GovernmentPrimaryTail155Api.OpaqueCall opaqueCall = new GovernmentPrimaryTail155Api.OpaqueCall(
                0x424DF29L, 0x424DB38L, rsp, r.volatileBits(), r.nonvolatileBits());
        GovernmentPrimaryTail155Api.VolatileBits postV = calls.invoke(opaqueCall);
        r.apply(postV);

        // 0424DF2E: add rsp, 0x40
        rsp += 0x40;
        // 0424DF32: pop rbp
        r.rbp = memory.readQword(rsp);
        rsp += 8;
        // 0424DF33: ret
        long returnRipBits = memory.readQword(rsp);
        rsp += 8;

        return new GovernmentCallee164Api.NormalReturn(
                r.volatileBits(), r.nonvolatileBits(), returnRipBits, rsp);
    }
}
