package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Owned normal projection of the complete held E23EA0 body. */
public final class LoadRowReferenceCalleeE23ea0202 {
    private LoadRowReferenceCalleeE23ea0202() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Registers s = new Registers(entry, memory, calls);
        memory.writeQword(s.rsp + 0x08, s.rbx);
        memory.writeQword(s.rsp + 0x10, s.rsi);
        s.rsp -= 8;
        memory.writeQword(s.rsp, s.rdi);
        s.rsp -= 0x20;

        s.rax = memory.readQword(s.rdx);
        s.rdi = s.rdx + 0x08;
        s.rsi = s.rcx + 0x08;
        memory.writeQword(s.rcx, s.rax);
        s.rbx = s.rcx;

        if (s.rsi != s.rdi) {
            s.rcx = memory.readQword(s.rsi + 0x38);
            if (s.rcx != 0) {
                s.rax = memory.readQword(s.rcx);
                s.rdx = (s.rdx & ~0xFFL) | (s.rcx != s.rsi ? 1L : 0L);
                s.call(0xE23ED7L, 0x20);
                memory.writeQword(s.rsi + 0x38, 0);
            }

            s.rcx = memory.readQword(s.rdi + 0x38);
            if (s.rcx != 0) {
                if (s.rcx != s.rdi) {
                    memory.writeQword(s.rsi + 0x38, s.rcx);
                    memory.writeQword(s.rdi + 0x38, 0);
                } else {
                    s.rax = memory.readQword(s.rcx);
                    s.rdx = s.rsi;
                    s.call(0xE23EF6L, 0x08);
                    memory.writeQword(s.rsi + 0x38, s.rax);
                    s.rcx = memory.readQword(s.rdi + 0x38);
                    if (s.rcx != 0) {
                        s.rax = memory.readQword(s.rcx);
                        s.rdx = (s.rdx & ~0xFFL) | (s.rcx != s.rdi ? 1L : 0L);
                        s.call(0xE23F0FL, 0x20);
                        memory.writeQword(s.rdi + 0x38, 0);
                    }
                }
            }
        }

        s.rsi = memory.readQword(s.rsp + 0x38);
        s.rax = s.rbx;
        s.rbx = memory.readQword(s.rsp + 0x30);
        s.rsp += 0x20;
        s.rdi = memory.readQword(s.rsp);
        s.rsp += 8;
        long returnRip = memory.readQword(s.rsp);
        return new GovernmentCrtBoundary185Api.NormalReturn(
                s.v(), returnRip, s.rsp + 8, s.nv());
    }

    private static final class Registers {
        final long imageBase;
        final GovernmentCrtBoundary185Api.Memory memory;
        final GovernmentCrtBoundary185Api.Calls calls;
        long rsp, rax, rcx, rdx, r8, r9, r10, r11;
        long rbx, rbp, rsi, rdi, r12, r13, r14, r15;
        GovernmentPrimaryTail155Api.Bits128 x0, x1, x2, x3, x4, x5, x6;

        Registers(GovernmentCrtBoundary185Api.Entry entry,
                GovernmentCrtBoundary185Api.Memory memory,
                GovernmentCrtBoundary185Api.Calls calls) {
            imageBase = entry.imageBaseBits();
            rsp = entry.rspBits();
            this.memory = memory;
            this.calls = calls;
            apply(entry.volatileBits());
            GovernmentPrimaryTail155Api.NonvolatileBits n = entry.nonvolatileBits();
            rbx = n.rbxBits(); rbp = n.rbpBits(); rsi = n.rsiBits(); rdi = n.rdiBits();
            r12 = n.r12Bits(); r13 = n.r13Bits(); r14 = n.r14Bits(); r15 = n.r15Bits();
            x6 = n.xmm6();
        }

        GovernmentPrimaryTail155Api.VolatileBits v() {
            return new GovernmentPrimaryTail155Api.VolatileBits(
                    rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
        }

        GovernmentPrimaryTail155Api.NonvolatileBits nv() {
            return new GovernmentPrimaryTail155Api.NonvolatileBits(
                    rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
        }

        void apply(GovernmentPrimaryTail155Api.VolatileBits v) {
            rax = v.raxBits(); rcx = v.rcxBits(); rdx = v.rdxBits();
            r8 = v.r8Bits(); r9 = v.r9Bits(); r10 = v.r10Bits(); r11 = v.r11Bits();
            x0 = v.xmm0(); x1 = v.xmm1(); x2 = v.xmm2();
            x3 = v.xmm3(); x4 = v.xmm4(); x5 = v.xmm5();
        }

        void call(long callSiteRva, long virtualSlotOffset) {
            long target = memory.readQword(rax + virtualSlotOffset);
            memory.writeQword(rsp - 8, imageBase + callSiteRva + 3);
            apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(
                    callSiteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                    target, rsp, v(), nv())));
        }
    }
}
