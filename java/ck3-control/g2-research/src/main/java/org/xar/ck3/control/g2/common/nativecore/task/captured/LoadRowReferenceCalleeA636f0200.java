package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Projection of the complete held A636F0 normal CFG into owned Memory and opaque calls. */
public final class LoadRowReferenceCalleeA636f0200 {
    private LoadRowReferenceCalleeA636f0200() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Registers s = new Registers(entry, memory, calls);
        int pc = 0xA636F0;
        while (true) {
            switch (pc) {
                case 0xA636F0 -> {
                    memory.writeQword(s.rsp + 0x10, s.rbx);
                    s.rsp -= 8;
                    memory.writeQword(s.rsp, s.rdi);
                    s.rsp -= 0x60;
                    s.rdi = s.rcx;
                    s.rbx = s.rdx;
                    s.rcx = memory.readQword(s.rcx + 0x38);
                    pc = s.rcx == s.rdi ? 0xA63725 : 0xA63709;
                }
                case 0xA63709 -> {
                    s.rax = memory.readQword(s.rdx + 0x38);
                    pc = s.rax == s.rdx ? 0xA63725 : 0xA63712;
                }
                case 0xA63712 -> {
                    memory.writeQword(s.rdi + 0x38, s.rax);
                    memory.writeQword(s.rdx + 0x38, s.rcx);
                    return finish(s);
                }
                case 0xA63725 -> {
                    memory.writeQword(s.rsp + 0x70, s.rsi);
                    s.rsi = 0;
                    memory.writeQword(s.rsp + 0x58, s.rsi);
                    s.r8 = Integer.toUnsignedLong((int) s.rsi);
                    pc = s.rcx == 0 ? 0xA63779 : 0xA63739;
                }
                case 0xA63739 -> pc = s.rcx != s.rdi ? 0xA6376D : 0xA6373E;
                case 0xA6373E -> {
                    s.rax = memory.readQword(s.rcx);
                    s.rdx = s.rsp + 0x20;
                    s.call(0xA63746L, 0x08);
                    s.rcx = memory.readQword(s.rdi + 0x38);
                    s.r8 = s.rax;
                    memory.writeQword(s.rsp + 0x58, s.rax);
                    pc = s.rcx == 0 ? 0xA63779 : 0xA6375A;
                }
                case 0xA6375A -> {
                    s.rax = memory.readQword(s.rcx);
                    s.rdx = (s.rdx & ~0xFFL) | (s.rcx != s.rdi ? 1L : 0L);
                    s.call(0xA63763L, 0x20);
                    s.r8 = memory.readQword(s.rsp + 0x58);
                    pc = 0xA63775;
                }
                case 0xA6376D -> {
                    s.r8 = s.rcx;
                    memory.writeQword(s.rsp + 0x58, s.rcx);
                    pc = 0xA63775;
                }
                case 0xA63775 -> {
                    memory.writeQword(s.rdi + 0x38, s.rsi);
                    pc = 0xA63779;
                }
                case 0xA63779 -> {
                    s.rcx = memory.readQword(s.rbx + 0x38);
                    pc = s.rcx == 0 ? 0xA637BF : 0xA63782;
                }
                case 0xA63782 -> pc = s.rcx != s.rbx ? 0xA637B7 : 0xA63787;
                case 0xA63787 -> {
                    s.rax = memory.readQword(s.rcx);
                    s.rdx = s.rdi;
                    s.call(0xA6378DL, 0x08);
                    memory.writeQword(s.rdi + 0x38, s.rax);
                    s.rcx = memory.readQword(s.rbx + 0x38);
                    pc = s.rcx == 0 ? 0xA637B0 : 0xA6379D;
                }
                case 0xA6379D -> {
                    s.rax = memory.readQword(s.rcx);
                    s.rdx = (s.rdx & ~0xFFL) | (s.rcx != s.rbx ? 1L : 0L);
                    s.call(0xA637A6L, 0x20);
                    s.r8 = memory.readQword(s.rsp + 0x58);
                    pc = 0xA637BB;
                }
                case 0xA637B0 -> {
                    s.r8 = memory.readQword(s.rsp + 0x58);
                    pc = 0xA637BF;
                }
                case 0xA637B7 -> {
                    memory.writeQword(s.rdi + 0x38, s.rcx);
                    pc = 0xA637BB;
                }
                case 0xA637BB -> {
                    memory.writeQword(s.rbx + 0x38, s.rsi);
                    pc = 0xA637BF;
                }
                case 0xA637BF -> {
                    s.rsi = memory.readQword(s.rsp + 0x70);
                    pc = s.r8 == 0 ? 0xA6380D : 0xA637C9;
                }
                case 0xA637C9 -> {
                    s.rax = s.rsp + 0x20;
                    pc = s.r8 != s.rax ? 0xA63809 : 0xA637D3;
                }
                case 0xA637D3 -> {
                    s.rax = memory.readQword(s.r8);
                    s.rdx = s.rbx;
                    s.rcx = s.r8;
                    s.call(0xA637DCL, 0x08);
                    s.rcx = memory.readQword(s.rsp + 0x58);
                    memory.writeQword(s.rbx + 0x38, s.rax);
                    pc = s.rcx == 0 ? 0xA6380D : 0xA637ED;
                }
                case 0xA637ED -> {
                    s.rax = memory.readQword(s.rcx);
                    s.rdx = s.rsp + 0x20;
                    s.rdx = (s.rdx & ~0xFFL) | (s.rcx != s.rdx ? 1L : 0L);
                    s.call(0xA637FBL, 0x20);
                    return finish(s);
                }
                case 0xA63809 -> {
                    memory.writeQword(s.rbx + 0x38, s.r8);
                    pc = 0xA6380D;
                }
                case 0xA6380D -> { return finish(s); }
                default -> throw new IllegalStateException("Unsupported source block: " + Integer.toHexString(pc));
            }
        }
    }

    private static GovernmentCrtBoundary185Api.NormalReturn finish(Registers s) {
        s.rbx = s.memory.readQword(s.rsp + 0x78);
        s.rsp += 0x60;
        s.rdi = s.memory.readQword(s.rsp);
        s.rsp += 8;
        long returnRip = s.memory.readQword(s.rsp);
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
