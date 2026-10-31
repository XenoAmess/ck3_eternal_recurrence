package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api;

/**
 * Owned normal-body translation for GovernmentThreadWait179 (0x4223B30).
 * Uses exact supplied APIs and original ASM semantics. No Game memory, no Windows API implementation.
 */
public final class GovernmentThreadWait179 {
    private GovernmentThreadWait179() { }

    public static GovernmentCallee164Api.NormalReturn execute(
            GovernmentCallee164Api.Entry entry,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentThreadHeader178Api.Ports ports) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(ports);

        // Initialize registers from the callee entry using the supplied helper.
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(entry);
        long imageBase = entry.imageBaseBits();
        long rsp = entry.frameRspBits();

        // 04223B30: push rbx
        memory.writeQword(rsp - 8, r.rbx);
        rsp -= 8;

        // 04223B32: sub rsp, 0x20
        rsp -= 0x20;

        // 04223B36: mov rax, qword ptr [rip + 0x1a39003] -> 0x5c5cb40
        r.rax = memory.readQword(imageBase + 0x5c5cb40);

        // 04223B3D: mov ebx, ecx
        // ECX is 32-bit, zero-extended to 64-bit for EBX.
        r.rbx = Integer.toUnsignedLong((int) r.rcx);

        // 04223B3F: test rax, rax
        // 04223B42: je 0x4223b61
        if (r.rax == 0) {
            // Slow path: RAX is zero.
            // 04223B61: lea rcx, [rip + 0x1a38fb0] -> 0x5c5cb18
            r.rcx = imageBase + 0x5c5cb18;

            // 04223B68: call qword ptr [rip + 0x1b6982] -> 0x43da4f0
            long callSiteRsp = rsp;
            memory.writeQword(rsp - 8, imageBase + 0x4223B6E);
            rsp -= 8;

            GovernmentThreadHeader178Api.IatCall iatCall1 = new GovernmentThreadHeader178Api.IatCall(
                    0x4223B68,
                    0x43da4f0,
                    callSiteRsp,
                    false,
                    r.volatileBits(),
                    r.nonvolatileBits()
            );
            GovernmentPrimaryTail155Api.VolatileBits vPost1 = ports.invokeIat(iatCall1);
            r.apply(vPost1);

            rsp += 8;

            // 04223B6E: mov rcx, qword ptr [rip + 0x1a38f9b] -> 0x5c5cb10
            r.rcx = memory.readQword(imageBase + 0x5c5cb10);

            // 04223B75: xor r8d, r8d
            r.r8 = 0;

            // 04223B78: mov edx, ebx
            r.rdx = Integer.toUnsignedLong((int) r.rbx);

            // 04223B7A: call qword ptr [rip + 0x1b6998] -> 0x43da518
            long callSiteRsp2 = rsp;
            memory.writeQword(rsp - 8, imageBase + 0x4223B80);
            rsp -= 8;

            GovernmentThreadHeader178Api.IatCall iatCall2 = new GovernmentThreadHeader178Api.IatCall(
                    0x4223B7A,
                    0x43da518,
                    callSiteRsp2,
                    false,
                    r.volatileBits(),
                    r.nonvolatileBits()
            );
            GovernmentPrimaryTail155Api.VolatileBits vPost2 = ports.invokeIat(iatCall2);
            r.apply(vPost2);

            rsp += 8;

            // 04223B80: lea rcx, [rip + 0x1a38f91] -> 0x5c5cb18
            r.rcx = imageBase + 0x5c5cb18;

            // 04223B87: add rsp, 0x20
            rsp += 0x20;

            // 04223B8B: pop rbx
            r.rbx = memory.readQword(rsp);
            rsp += 8;

            // 04223B8C: jmp qword ptr [rip + 0x1b696d] -> 0x43da500
            GovernmentThreadHeader178Api.IatCall tailCall = new GovernmentThreadHeader178Api.IatCall(
                    0x4223B8C,
                    0x43da500,
                    rsp,
                    true,
                    r.volatileBits(),
                    r.nonvolatileBits()
            );
            GovernmentPrimaryTail155Api.VolatileBits vTail = ports.invokeIat(tailCall);
            r.apply(vTail);

            long retRip = memory.readQword(rsp);
            return new GovernmentCallee164Api.NormalReturn(
                    r.volatileBits(),
                    r.nonvolatileBits(),
                    retRip,
                    rsp + 8
            );
        } else {
            // Fast path: RAX is non-zero.
            // 04223B44: mov r8d, ecx
            r.r8 = Integer.toUnsignedLong((int) r.rcx);

            // 04223B47: lea rdx, [rip + 0x1a38fca] -> 0x5c5cb18
            r.rdx = imageBase + 0x5c5cb18;

            // 04223B4E: lea rcx, [rip + 0x1a38fb3] -> 0x5c5cb08
            r.rcx = imageBase + 0x5c5cb08;

            // 04223B55: add rsp, 0x20
            rsp += 0x20;

            // 04223B59: pop rbx
            r.rbx = memory.readQword(rsp);
            rsp += 8;

            // 04223B5A: jmp qword ptr [rip + 0x1b8047] -> 0x43dbba8
            GovernmentThreadHeader178Api.IatCall tailCall = new GovernmentThreadHeader178Api.IatCall(
                    0x4223B5A,
                    0x43dbba8,
                    rsp,
                    true,
                    r.volatileBits(),
                    r.nonvolatileBits()
            );
            GovernmentPrimaryTail155Api.VolatileBits vTail = ports.invokeIat(tailCall);
            r.apply(vTail);

            long retRip = memory.readQword(rsp);
            return new GovernmentCallee164Api.NormalReturn(
                    r.volatileBits(),
                    r.nonvolatileBits(),
                    retRip,
                    rsp + 8
            );
        }
    }
}