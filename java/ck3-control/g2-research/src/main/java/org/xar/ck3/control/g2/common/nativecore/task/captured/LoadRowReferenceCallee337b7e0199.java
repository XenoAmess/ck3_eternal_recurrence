package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

public final class LoadRowReferenceCallee337b7e0199 {
    private LoadRowReferenceCallee337b7e0199() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        State s = new State(entry, memory, calls, budget, floating);
        while (true) {
            if (s.pc == 0x337B7E0L) {
                prologue(s);
            } else if (s.pc >= 0x337B873L && s.pc < 0x337B9B4L) {
                LoadRowReferenceCallee337b7e0199Normal.run(s);
            } else if (s.pc >= 0x337B9B4L && s.pc < 0x337BB75L) {
                LoadRowReferenceCallee337b7e0199Displace.run(s);
            } else if (s.pc == 0x337BB75L) {
                growthFatal(s);
            } else if (s.pc == 0x337BBABL) {
                epilogue(s);
                return finish(s);
            } else {
                throw new IllegalStateException("Unknown pc: " + Long.toHexString(s.pc));
            }
        }
    }

    static final class State {
        final long image;
        long rsp, rax, rcx, rdx, r8, r9, r10, r11, rbx, rbp, rsi, rdi, r12, r13, r14, r15, pc;
        GovernmentPrimaryTail155Api.Bits128 x0, x1, x2, x3, x4, x5, x6;
        final GovernmentCrtBoundary185Api.Memory m;
        final GovernmentCrtBoundary185Api.Calls calls;
        final GovernmentCrtBoundary185Api.LoopBudget budget;
        final LoadRowReferenceCallee337b7e0199Api.Float32 floating;

        State(GovernmentCrtBoundary185Api.Entry e, GovernmentCrtBoundary185Api.Memory mem,
              GovernmentCrtBoundary185Api.Calls c, GovernmentCrtBoundary185Api.LoopBudget b,
              LoadRowReferenceCallee337b7e0199Api.Float32 f) {
            this.image = e.imageBaseBits();
            this.rsp = e.rspBits();
            this.m = mem;
            this.calls = c;
            this.budget = b;
            this.floating = f;
            this.pc = 0x337B7E0L;

            GovernmentPrimaryTail155Api.VolatileBits v = e.volatileBits();
            this.rax = v.raxBits(); this.rcx = v.rcxBits(); this.rdx = v.rdxBits();
            this.r8 = v.r8Bits(); this.r9 = v.r9Bits(); this.r10 = v.r10Bits(); this.r11 = v.r11Bits();
            this.x0 = v.xmm0(); this.x1 = v.xmm1(); this.x2 = v.xmm2();
            this.x3 = v.xmm3(); this.x4 = v.xmm4(); this.x5 = v.xmm5();

            GovernmentPrimaryTail155Api.NonvolatileBits n = e.nonvolatileBits();
            this.rbx = n.rbxBits(); this.rbp = n.rbpBits(); this.rsi = n.rsiBits(); this.rdi = n.rdiBits();
            this.r12 = n.r12Bits(); this.r13 = n.r13Bits(); this.r14 = n.r14Bits(); this.r15 = n.r15Bits();
            this.x6 = n.xmm6();
        }

        GovernmentPrimaryTail155Api.VolatileBits v() {
            return new GovernmentPrimaryTail155Api.VolatileBits(rax, rcx, rdx, r8, r9, r10, r11, x0, x1, x2, x3, x4, x5);
        }

        GovernmentPrimaryTail155Api.NonvolatileBits nv() {
            return new GovernmentPrimaryTail155Api.NonvolatileBits(rbx, rbp, rsi, rdi, r12, r13, r14, r15, x6);
        }

        void apply(GovernmentPrimaryTail155Api.VolatileBits v) {
            rax = v.raxBits(); rcx = v.rcxBits(); rdx = v.rdxBits();
            r8 = v.r8Bits(); r9 = v.r9Bits(); r10 = v.r10Bits(); r11 = v.r11Bits();
            x0 = v.xmm0(); x1 = v.xmm1(); x2 = v.xmm2(); x3 = v.xmm3(); x4 = v.xmm4(); x5 = v.xmm5();
        }

        void call(long siteRva, GovernmentCrtBoundary185Api.TargetKind kind, long targetBits, int length) {
            long nextRip = image + siteRva + length;
            m.writeQword(rsp - 8, nextRip);
            GovernmentPrimaryTail155Api.VolatileBits res = calls.invoke(new GovernmentCrtBoundary185Api.Call(
                siteRva, kind, targetBits, rsp, v(), nv()));
            apply(res);
        }
    }

    static void prologue(State s) {
        long S = s.rsp;
        s.m.writeQword(S + 0x10, s.rbx);
        s.m.writeQword(S + 0x20, s.r9);
        s.m.writeDword(S + 0x18, (int) s.r8);

        s.m.writeQword(S - 8, s.rbp); s.rsp = S - 8;
        s.m.writeQword(s.rsp - 8, s.rsi); s.rsp -= 8;
        s.m.writeQword(s.rsp - 8, s.rdi); s.rsp -= 8;
        s.m.writeQword(s.rsp - 8, s.r12); s.rsp -= 8;
        s.m.writeQword(s.rsp - 8, s.r13); s.rsp -= 8;
        s.m.writeQword(s.rsp - 8, s.r14); s.rsp -= 8;
        s.m.writeQword(s.rsp - 8, s.r15); s.rsp -= 8;

        s.rbp = s.rsp - 0x17;
        s.rsp -= 0xE0;

        s.r12 = s.r9;
        s.rdi = s.rdx;
        s.rsi = s.rcx;

        // MOV ECX zero-extends; CDQE subsequently sign-extends the masked EAX.
        s.rcx = Integer.toUnsignedLong(s.m.readDword(s.rcx + 0x14));
        s.rax = (int) (s.rcx & s.r8);
        s.rbx = (s.rax + 4 * s.rax) << 4;
        s.rbx += s.m.readQword(s.rsi + 0x8);
        s.r14 = (s.r14 & ~0xFFL) | 1L;
        if (s.m.readUnsignedByte(s.rbx + 4) >= 1) {
            // The key is loaded once before this source loop, not once per iteration.
            s.rax = s.m.readQword(s.r9);
            while (true) {
                s.budget.beforeStep(0x337B831L, s.rbx);
                if (s.rax == s.m.readQword(s.rbx + 8)) {
                    s.pc = 0x337B8C4L;
                    return;
                }
                s.r14 = (s.r14 & ~0xFFL) | ((s.r14 + 1) & 0xFFL);
                s.rbx += 0x50;
                if ((s.r14 & 0xFFL) > s.m.readUnsignedByte(s.rbx + 4)) {
                    break;
                }
            }
        }
        if ((s.r14 & 0xFFL) > s.m.readUnsignedByte(s.rsi + 0x18)) {
            s.pc = 0x337BB75L;
            return;
        }
        s.rax = Integer.toUnsignedLong(s.m.readDword(s.rsi + 0x10) + 1);
        // MOVD clears the upper 96 bits. Conversion of those exact zero lanes stays +0.
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(s.rax, 0);
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(
                Integer.toUnsignedLong(s.floating.convertSignedDwordToFloatBits((int) s.rax)), 0);
        s.x0 = new GovernmentPrimaryTail155Api.Bits128(s.rcx, 0);
        s.x0 = new GovernmentPrimaryTail155Api.Bits128(
                Integer.toUnsignedLong(s.floating.convertSignedDwordToFloatBits((int) s.rcx)), 0);
        int quotient = s.floating.divideScalarFloatBits((int) s.x1.lowBits(), (int) s.x0.lowBits());
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(
                (s.x1.lowBits() & 0xFFFFFFFF00000000L) | Integer.toUnsignedLong(quotient), s.x1.highBits());
        s.pc = s.floating.orderedAbove((int) s.x1.lowBits(), s.m.readDword(s.rsi + 0x1C))
                ? 0x337BB75L : 0x337B873L;
    }

    static void growthFatal(State s) {
        s.rcx = (s.rcx + 1) & 0xFFFFFFFFL;
        s.rdx = 1;

        s.call(0x337BB7CL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x86E160L, 5);

        int eax = (int) s.rax;
        if (eax >= 31) {
            s.rdx = s.rsi;
            s.rcx = s.rbp + 0x57;
            s.call(0x337BBD0L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x86F210L, 5);
            s.call(0x337BBD5L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4232CF4L, 5);
            throw new UnsupportedOperationException("Fatal growth path");
        }

        s.rdx = Integer.toUnsignedLong((int) s.rax);
        s.rcx = s.rsi;
        s.call(0x337BB8BL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x337C0C0L, 5);

        s.rax = s.m.readQword(s.rbp + 0x7F);
        s.m.writeQword(s.rsp + 0x28, s.rax);
        s.r9 = s.r12;
        s.r8 = Integer.toUnsignedLong(s.m.readDword(s.rbp + 0x67));
        s.rdx = s.rdi;
        s.rcx = s.rsi;
        s.call(0x337BBA6L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x337C200L, 5);

        s.pc = 0x337BBABL;
    }

    static void epilogue(State s) {
        s.rax = s.rdi;
        s.rbx = s.m.readQword(s.rsp + 0x128);
        s.rsp += 0xE0;

        s.r15 = s.m.readQword(s.rsp); s.rsp += 8;
        s.r14 = s.m.readQword(s.rsp); s.rsp += 8;
        s.r13 = s.m.readQword(s.rsp); s.rsp += 8;
        s.r12 = s.m.readQword(s.rsp); s.rsp += 8;
        s.rdi = s.m.readQword(s.rsp); s.rsp += 8;
        s.rsi = s.m.readQword(s.rsp); s.rsp += 8;
        s.rbp = s.m.readQword(s.rsp); s.rsp += 8;

        s.pc = 0x337BBC9L;
    }

    static GovernmentCrtBoundary185Api.NormalReturn finish(State s) {
        long returnRip = s.m.readQword(s.rsp);
        long callerRsp = s.rsp + 8;
        return new GovernmentCrtBoundary185Api.NormalReturn(s.v(), returnRip, callerRsp, s.nv());
    }
}
