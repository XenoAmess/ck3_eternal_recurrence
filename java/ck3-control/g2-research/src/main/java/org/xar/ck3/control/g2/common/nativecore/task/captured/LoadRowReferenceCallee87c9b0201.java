package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class LoadRowReferenceCallee87c9b0201 {
    private LoadRowReferenceCallee87c9b0201() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        long S = entry.rspBits();
        long W = S - 0x28;

        // Prologue: save RBX, push RDI, sub rsp
        memory.writeQword(S + 0x8, entry.nonvolatileBits().rbxBits());
        memory.writeQword(S - 0x8, entry.nonvolatileBits().rdiBits());

        // Initialize registers from entry
        long rax = entry.volatileBits().raxBits();
        long rcx = entry.volatileBits().rcxBits();
        long rdx = entry.volatileBits().rdxBits();
        long r8 = entry.volatileBits().r8Bits();
        long r9 = entry.volatileBits().r9Bits();
        long r10 = entry.volatileBits().r10Bits();
        long r11 = entry.volatileBits().r11Bits();
        Bits128 x0 = entry.volatileBits().xmm0();
        Bits128 x1 = entry.volatileBits().xmm1();
        Bits128 x2 = entry.volatileBits().xmm2();
        Bits128 x3 = entry.volatileBits().xmm3();
        Bits128 x4 = entry.volatileBits().xmm4();
        Bits128 x5 = entry.volatileBits().xmm5();

        long rbx = entry.nonvolatileBits().rbxBits();
        long rbp = entry.nonvolatileBits().rbpBits();
        long rsi = entry.nonvolatileBits().rsiBits();
        long rdi = entry.nonvolatileBits().rdiBits();
        long r12 = entry.nonvolatileBits().r12Bits();
        long r13 = entry.nonvolatileBits().r13Bits();
        long r14 = entry.nonvolatileBits().r14Bits();
        long r15 = entry.nonvolatileBits().r15Bits();
        Bits128 x6 = entry.nonvolatileBits().xmm6();

        // 87c9ba: mov rdi, rcx
        rdi = rcx;
        // 87c9bd: mov rbx, rdx
        rbx = rdx;
        // 87c9c0: mov rcx, [rdx+0x38]
        rcx = memory.readQword(rdx + 0x38);
        // 87c9c4: test rcx, rcx
        // 87c9c7: je 0x87ca0f (if rcx == 0)
        if (rcx == 0) {
            // Jump to epilogue at 87ca0f
            // 87ca0f: mov rbx, [rsp+0x30] -> W+0x30 = S-0x28+0x30 = S+8
            rbx = memory.readQword(W + 0x30);
            // 87ca14: add rsp, 0x20
            // 87ca18: pop rdi
            rdi = memory.readQword(S - 0x8);
            // 87ca19: ret
            long returnRip = memory.readQword(S);
            long callerRsp = S + 0x8;
            VolatileBits finalV = new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
            NonvolatileBits finalNV = new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
            return new GovernmentCrtBoundary185Api.NormalReturn(finalV, returnRip, callerRsp, finalNV);
        }
        // 87c9c9: cmp rcx, rdx
        // 87c9cc: jne 0x87ca03 (if rcx != rdx)
        if (rcx != rdx) {
            // Jump to 87ca03
            // 87ca03: mov [rdi+0x38], rcx
            memory.writeQword(rdi + 0x38, rcx);
            // 87ca07: mov [rdx+0x38], 0
            memory.writeQword(rdx + 0x38, 0);
            // 87ca0f: mov rbx, [rsp+0x30]
            rbx = memory.readQword(W + 0x30);
            // 87ca14: add rsp, 0x20
            // 87ca18: pop rdi
            rdi = memory.readQword(S - 0x8);
            // 87ca19: ret
            long returnRip = memory.readQword(S);
            long callerRsp = S + 0x8;
            VolatileBits finalV = new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
            NonvolatileBits finalNV = new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
            return new GovernmentCrtBoundary185Api.NormalReturn(finalV, returnRip, callerRsp, finalNV);
        }

        // 87c9ce: mov rax, [rcx]
        rax = memory.readQword(rcx);
        // 87c9d1: mov rdx, rdi
        rdx = rdi;
        // 87c9d4: call [rax+0x8] (INDIRECT_ABSOLUTE, site 0x87C9D4, slot 8)
        long target1 = memory.readQword(rax + 0x8);
        long callSite1 = 0x87C9D4L;
        memory.writeQword(W - 0x8, entry.imageBaseBits() + callSite1 + 3);
        GovernmentCrtBoundary185Api.Call call1 = new GovernmentCrtBoundary185Api.Call(
                callSite1, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target1, W,
                new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5),
                new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6));
        VolatileBits retV1 = calls.invoke(call1);
        rax = retV1.raxBits(); rcx = retV1.rcxBits(); rdx = retV1.rdxBits();
        r8 = retV1.r8Bits(); r9 = retV1.r9Bits(); r10 = retV1.r10Bits(); r11 = retV1.r11Bits();
        x0 = retV1.xmm0(); x1 = retV1.xmm1(); x2 = retV1.xmm2(); x3 = retV1.xmm3(); x4 = retV1.xmm4(); x5 = retV1.xmm5();

        // 87c9d7: mov [rdi+0x38], rax
        memory.writeQword(rdi + 0x38, rax);
        // 87c9db: mov rcx, [rbx+0x38]
        rcx = memory.readQword(rbx + 0x38);
        // 87c9df: test rcx, rcx
        // 87c9e2: je 0x87ca0f (if rcx == 0)
        if (rcx == 0) {
            // Jump to epilogue at 87ca0f
            rbx = memory.readQword(W + 0x30);
            rdi = memory.readQword(S - 0x8);
            long returnRip = memory.readQword(S);
            long callerRsp = S + 0x8;
            VolatileBits finalV = new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
            NonvolatileBits finalNV = new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
            return new GovernmentCrtBoundary185Api.NormalReturn(finalV, returnRip, callerRsp, finalNV);
        }

        // 87c9e4: mov rax, [rcx]
        rax = memory.readQword(rcx);
        // 87c9e7: cmp rcx, rbx
        // 87c9ea: setne dl (RDX low 8 bits = (rcx != rbx) ? 1 : 0)
        long dl = (rcx != rbx) ? 1 : 0;
        rdx = (rdx & 0xFFFFFFFFFFFFFF00L) | dl;
        // 87c9ed: call [rax+0x20] (INDIRECT_ABSOLUTE, site 0x87C9ED, slot 20)
        long target2 = memory.readQword(rax + 0x20);
        long callSite2 = 0x87C9EDL;
        memory.writeQword(W - 0x8, entry.imageBaseBits() + callSite2 + 3);
        GovernmentCrtBoundary185Api.Call call2 = new GovernmentCrtBoundary185Api.Call(
                callSite2, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target2, W,
                new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5),
                new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6));
        VolatileBits retV2 = calls.invoke(call2);
        rax = retV2.raxBits(); rcx = retV2.rcxBits(); rdx = retV2.rdxBits();
        r8 = retV2.r8Bits(); r9 = retV2.r9Bits(); r10 = retV2.r10Bits(); r11 = retV2.r11Bits();
        x0 = retV2.xmm0(); x1 = retV2.xmm1(); x2 = retV2.xmm2(); x3 = retV2.xmm3(); x4 = retV2.xmm4(); x5 = retV2.xmm5();

        // 87c9f0: mov [rbx+0x38], 0
        memory.writeQword(rbx + 0x38, 0);
        // 87c9f8: mov rbx, [rsp+0x30]
        rbx = memory.readQword(W + 0x30);
        // 87c9fd: add rsp, 0x20
        // 87ca01: pop rdi
        rdi = memory.readQword(S - 0x8);
        // 87ca02: ret
        long returnRip = memory.readQword(S);
        long callerRsp = S + 0x8;
        VolatileBits finalV = new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
        NonvolatileBits finalNV = new NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
        return new GovernmentCrtBoundary185Api.NormalReturn(finalV, returnRip, callerRsp, finalNV);
    }
}
