package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Captured748B normal CFG with explicit opaque calls, loop budgets and supplied Float32 ports. */
public final class LoadRowReferenceCallee337c5d0203 {
    private LoadRowReferenceCallee337c5d0203() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls, GovernmentCrtBoundary185Api.LoopBudget budget,
            LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        State s = new State(entry,memory,calls,budget,floating);
        enter(s);
        while (true) {
            switch (s.pc) {
                case 0x337C65B,0x337C690,0x337C696,0x337C69B -> insertFront(s);
                case 0x337C740 -> displaceLoop(s);
                case 0x337C6A3,0x337C86C -> { return growthExit(s); }
                default -> throw new IllegalStateException("Unclosed source pc " + Integer.toHexString(s.pc));
            }
        }
    }

    private static void enter(State s) {
        s.push(s.rbp); s.push(s.rbx); s.push(s.rsi); s.push(s.rdi); s.push(s.r13); s.push(s.r14); s.push(s.r15);
        s.rbp = s.rsp - 0x1f;
        s.rsp -= 0x90;
        s.rsi = s.rcx;
        s.r13 = (long)(int)s.r8;
        s.rcx = (long)s.m.readDword(s.rcx + 0x14);
        s.rdi = low8(s.rdi, 1);
        s.r10 = s.rcx;
        s.r15 = s.r9;
        s.r10 &= s.r13;
        s.r14 = s.rdx;
        s.rbx = s.r10 * 5;
        s.rbx <<= 4;
        s.rbx += s.m.readQword(s.rsi + 8);
        if (s.m.readUnsignedByte(s.rbx + 4) >= 1) {
            s.rax = s.m.readQword(s.r9);
            while (true) {
                s.budget.beforeStep(0x337C615, s.rbx);
                if (s.rax == s.m.readQword(s.rbx + 8)) {
                    s.m.writeQword(s.rdx, s.rbx);
                    s.m.writeByte(s.rdx + 8, 0);
                    s.pc = 0x337C6A3;
                    return;
                }
                s.rbx += 0x50;
                s.rdi = low8(s.rdi, (int)(s.rdi + 1));
                if ((s.rdi & 0xFFL) > s.m.readUnsignedByte(s.rbx + 4)) break;
            }
        }
        if ((s.rdi & 0xFFL) > s.m.readUnsignedByte(s.rsi + 0x18)) {
            s.pc = 0x337C86C;
            return;
        }
        s.rax = z32(s.m.readDword(s.rsi + 0x10));
        s.rax = z32((int)s.rax + 1);
        s.x0 = new GovernmentPrimaryTail155Api.Bits128(z32((int)s.rcx), 0);
        s.x0 = new GovernmentPrimaryTail155Api.Bits128(z32(s.floating.convertSignedDwordToFloatBits((int)s.x0.lowBits())), 0);
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(z32((int)s.rax), 0);
        s.x1 = new GovernmentPrimaryTail155Api.Bits128(z32(s.floating.convertSignedDwordToFloatBits((int)s.x1.lowBits())), 0);
        int quotient = s.floating.divideScalarFloatBits((int)s.x1.lowBits(), (int)s.x0.lowBits());
        s.x1 = new GovernmentPrimaryTail155Api.Bits128((s.x1.lowBits() & 0xFFFFFFFF00000000L) | z32(quotient), s.x1.highBits());
        if (s.floating.orderedAbove((int)s.x1.lowBits(), s.m.readDword(s.rsi + 0x1C))) {
            s.pc = 0x337C86C;
            return;
        }
        s.rax = z32(s.m.readUnsignedByte(s.rbx + 4));
        s.pc = 0x337C65B;
    }


    private static void insertFront(State s) {
        while (true) {
            if (s.pc == 0x337C65B) {
                s.m.writeQword(s.rsp + 0xD8, s.r12);
                s.r12 = s.rbx + 0x8;
                if ((s.rax & 0xFF) != 0) {
                    s.pc = 0x337C6C1;
                } else {
                    s.m.writeDword(s.rbx, (int)s.r13);
                    s.rdx = s.r9 + 0x8;
                    s.m.writeByte(s.rbx + 0x4, (int)s.rdi);
                    s.rcx = s.r12 + 0x8;
                    s.rax = s.m.readQword(s.r9);
                    s.m.writeQword(s.r12, s.rax);
                    s.m.writeQword(s.r12 + 0x40, 0L);
                    s.direct(0x337C68B, 0x87C9B0);
                    s.pc = 0x337C690;
                }
            } else if (s.pc == 0x337C690) {
                s.m.writeDword(s.rsi + 0x10, s.m.readDword(s.rsi + 0x10) + 1);
                s.m.writeQword(s.r14, s.rbx);
                s.m.writeByte(s.r14 + 0x8, 1);
                s.r12 = s.m.readQword(s.rsp + 0xD8);
                s.pc = 0x337C6A3;
            } else if (s.pc == 0x337C696) {
                s.m.writeByte(s.r14 + 0x8, 1);
                s.r12 = s.m.readQword(s.rsp + 0xD8);
                s.pc = 0x337C6A3;
            } else if (s.pc == 0x337C69B) {
                s.r12 = s.m.readQword(s.rsp + 0xD8);
                s.pc = 0x337C6A3;
            } else if (s.pc == 0x337C6C1) {
                s.rcx = z32(s.m.readDword(s.rbx));
                s.rdx = s.r12 + 0x8;
                s.rax = low8(s.rax, (int)(s.rax + 1));
                if (s.m.readUnsignedByte(s.rbx + 0x54) != 0) {
                    s.pc = 0x337C703;
                } else {
                    s.m.writeDword(s.rbx + 0x50, (int)s.rcx);
                    s.rcx = s.rbx + 0x60;
                    s.m.writeByte(s.rbx + 0x54, (int)s.rax);
                    s.rax = s.m.readQword(s.r12);
                    s.m.writeQword(s.rbx + 0x58, s.rax);
                    s.m.writeQword(s.rcx + 0x38, 0L);
                    s.direct(0x337C6EA, 0x87C9B0);
                    s.rdx = s.r15;
                    s.m.writeDword(s.rbx, (int)s.r13);
                    s.rcx = s.r12;
                    s.m.writeByte(s.rbx + 0x4, (int)s.rdi);
                    s.direct(0x337C6FC, 0xE23EA0);
                    s.pc = 0x337C690;
                }
            } else if (s.pc == 0x337C703) {
                s.m.writeDword(s.rbp - 0x31, (int)s.rcx);
                s.rcx = s.rbp - 0x21;
                s.m.writeByte(s.rbp - 0x2D, (int)s.rax);
                s.rax = s.m.readQword(s.r12);
                s.m.writeQword(s.rbp - 0x29, s.rax);
                s.m.writeQword(s.rbp + 0x17, 0L);
                s.direct(0x337C71D, 0x87C9B0);
                s.rdx = s.r15;
                s.m.writeDword(s.rbx, (int)s.r13);
                s.rcx = s.r12;
                s.m.writeByte(s.rbx + 0x4, (int)s.rdi);
                s.direct(0x337C72F, 0xE23EA0);
                s.rcx = z32(s.m.readUnsignedByte(s.rbp - 0x2D));
                s.rdi = s.rbx;
                s.pc = 0x337C740;
            }
            else { throw new IllegalStateException("Invalid insert pc " + Integer.toHexString(s.pc)); }
            if (s.pc == 0x337C740 || s.pc == 0x337C6A3) return;
        }
    }

    private static void displaceLoop(State s) {
        while (true) {
            s.budget.beforeStep(0x337C740L, s.rbx);
            s.rax = Integer.toUnsignedLong(s.m.readUnsignedByte(s.rbx + 0x54));
            s.rbx += 0x50;
            if (s.rax == 0) {
                s.rax = z32(s.m.readDword(s.rbp - 0x31));
                s.rdx = s.rbp - 0x21;
                s.m.writeDword(s.rbx, (int)s.rax);
                s.m.writeByte(s.rbx + 0x4, (int)s.rcx);
                s.rcx = s.rbx + 0x10;
                s.rax = s.m.readQword(s.rbp - 0x29);
                s.m.writeQword(s.rbx + 0x8, s.rax);
                s.m.writeQword(s.rcx + 0x38, 0L);
                s.direct(0x337C843L, 0x87C9B0L);
                s.rcx = s.m.readQword(s.rbp + 0x17);
                if (s.rcx != 0) {
                    s.rax = s.m.readQword(s.rcx);
                    s.rdx = s.rbp - 0x21;
                    s.rdx = low8(s.rdx, (s.rcx != s.rdx) ? 1 : 0);
                    s.indirect(0x337C85EL, s.m.readQword(s.rax + 0x20));
                }
                s.m.writeDword(s.rsi + 0x10, s.m.readDword(s.rsi + 0x10) + 1);
                s.m.writeQword(s.r14, s.rdi);
                s.pc = 0x337C696;
                return;
            }
            if ((s.rax & 0xFFL) >= (s.rcx & 0xFFL)) {
                s.rcx = low8(s.rcx, (int)(s.rcx + 1));
                s.m.writeByte(s.rbp - 0x2d, (int)s.rcx);
                int limit = s.m.readUnsignedByte(s.rsi + 0x18);
                if ((s.rcx & 0xFFL) <= limit) {
                    continue;
                }
                s.rcx = z32(s.m.readDword(s.rbp - 0x31));
                s.rdx = s.r12 + 0x8;
                s.rax = z32(s.m.readDword(s.rdi));
                s.m.writeDword(s.rbp - 0x31, (int)s.rax);
                s.rax = Integer.toUnsignedLong(s.m.readUnsignedByte(s.rdi + 0x4));
                s.m.writeDword(s.rdi, (int)s.rcx);
                s.rcx = Integer.toUnsignedLong(s.m.readUnsignedByte(s.rbp - 0x2d));
                s.m.writeByte(s.rbp - 0x2d, (int)s.rax);
                s.rax = s.m.readQword(s.rdi + 0x8);
                s.m.writeByte(s.rdi + 0x4, (int)s.rcx);
                s.rcx = s.m.readQword(s.rbp - 0x29);
                s.m.writeQword(s.rbp - 0x29, s.rax);
                s.m.writeQword(s.rdi + 0x8, s.rcx);
                s.rcx = s.rbp - 0x21;
                s.direct(0x337C7CFL, 0xA636F0L);
                s.rcx = s.rsi;
                s.direct(0x337C7D7L, 0x337C040L);
                s.r8 = z32(s.m.readDword(s.rbp - 0x31));
                s.rax = s.rbp + 0x6f;
                s.r9 = s.rbp - 0x29;
                s.m.writeQword(s.rsp + 0x20, s.rax);
                s.rdx = s.rbp - 0x41;
                s.m.writeByte(s.rbp + 0x6f, 0);
                s.rcx = s.rsi;
                s.direct(0x337C7F8L, 0x337C5D0L);
                s.rcx = s.m.readQword(s.rbp + 0x17);
                if (s.rcx != 0) {
                    s.rax = s.m.readQword(s.rcx);
                    s.rdx = s.rbp - 0x21;
                    s.rdx = low8(s.rdx, (s.rcx != s.rdx) ? 1 : 0);
                    s.indirect(0x337C813L, s.m.readQword(s.rax + 0x20));
                }
                s.x0 = s.m.read128(s.rbp - 0x41);
                s.m.write128(s.r14, s.x0);
                s.pc = 0x337C69B;
                return;
            }
            s.rcx = z32(s.m.readDword(s.rbp - 0x31));
            s.rdx = s.rbx + 0x10;
            s.rax = z32(s.m.readDword(s.rbx));
            s.m.writeDword(s.rbp - 0x31, (int)s.rax);
            s.rax = Integer.toUnsignedLong(s.m.readUnsignedByte(s.rbx + 0x4));
            s.m.writeDword(s.rbx, (int)s.rcx);
            s.rcx = Integer.toUnsignedLong(s.m.readUnsignedByte(s.rbp - 0x2d));
            s.m.writeByte(s.rbp - 0x2d, (int)s.rax);
            s.rax = s.m.readQword(s.rbx + 0x8);
            s.m.writeByte(s.rbx + 0x4, (int)s.rcx);
            s.rcx = s.m.readQword(s.rbp - 0x29);
            s.m.writeQword(s.rbp - 0x29, s.rax);
            s.m.writeQword(s.rbx + 0x8, s.rcx);
            s.rcx = s.rbp - 0x21;
            s.direct(0x337C784L, 0xA636F0L);
            s.rcx = Integer.toUnsignedLong(s.m.readUnsignedByte(s.rbp - 0x2d));
            s.rcx = low8(s.rcx, (int)(s.rcx + 1));
            s.m.writeByte(s.rbp - 0x2d, (int)s.rcx);
        }
    }

    private static GovernmentCrtBoundary185Api.NormalReturn growthExit(State s) {
        if (s.pc == 0x337C6A3) {
            s.rax = s.r14;
            s.rsp += 0x90;
            s.r15 = s.pop();
            s.r14 = s.pop();
            s.r13 = s.pop();
            s.rdi = s.pop();
            s.rsi = s.pop();
            s.rbx = s.pop();
            s.rbp = s.pop();
            return s.ret();
        }
        if (s.pc != 0x337C86C) {
            throw new UnsupportedOperationException("Invalid entry point");
        }
        s.rcx = z32((int)s.rcx + 1);
        s.rdx = 1;
        s.call(0x337C873, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x86E160, 5);
        if ((int)s.rax >= 31) {
            s.rdx = s.rsi;
            s.rcx = s.rbp + 0x5F;
            s.call(0x337C8B1, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x86F210, 5);
            s.call(0x337C8B6, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4232CF4, 5);
            throw new UnsupportedOperationException("INT3 reached");
        }
        s.rdx = z32((int)s.rax);
        s.rcx = s.rsi;
        s.call(0x337C882, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x337C0C0, 5);
        s.rax = s.rbp + 0x6F;
        s.m.writeByte(s.rbp + 0x6F, 0);
        s.r9 = s.r15;
        s.m.writeQword(s.rsp + 0x20, s.rax);
        s.r8 = z32((int)s.r13);
        s.rdx = s.r14;
        s.rcx = s.rsi;
        s.direct(0x337C8A0, 0x337C5D0);
        s.pc = 0x337C6A3;
        return growthExit(s);
    }

    private static long z32(int bits) { return Integer.toUnsignedLong(bits); }
    private static long low8(long original,int bits) { return (original & ~0xFFL) | (bits & 0xFFL); }

    private static final class State {
        final long image;
        long rsp,rax,rcx,rdx,r8,r9,r10,r11,rbx,rbp,rsi,rdi,r12,r13,r14,r15;
        int pc;
        GovernmentPrimaryTail155Api.Bits128 x0,x1,x2,x3,x4,x5,x6;
        final GovernmentCrtBoundary185Api.Memory m;
        final GovernmentCrtBoundary185Api.Calls calls;
        final GovernmentCrtBoundary185Api.LoopBudget budget;
        final LoadRowReferenceCallee337b7e0199Api.Float32 floating;
        State(GovernmentCrtBoundary185Api.Entry e,GovernmentCrtBoundary185Api.Memory memory,
                GovernmentCrtBoundary185Api.Calls ports,GovernmentCrtBoundary185Api.LoopBudget b,
                LoadRowReferenceCallee337b7e0199Api.Float32 f) {
            image=e.imageBaseBits();rsp=e.rspBits();m=memory;calls=ports;budget=b;floating=f;
            GovernmentPrimaryTail155Api.VolatileBits v=e.volatileBits();
            rax=v.raxBits();rcx=v.rcxBits();rdx=v.rdxBits();r8=v.r8Bits();r9=v.r9Bits();r10=v.r10Bits();r11=v.r11Bits();
            x0=v.xmm0();x1=v.xmm1();x2=v.xmm2();x3=v.xmm3();x4=v.xmm4();x5=v.xmm5();
            GovernmentPrimaryTail155Api.NonvolatileBits n=e.nonvolatileBits();
            rbx=n.rbxBits();rbp=n.rbpBits();rsi=n.rsiBits();rdi=n.rdiBits();r12=n.r12Bits();r13=n.r13Bits();r14=n.r14Bits();r15=n.r15Bits();x6=n.xmm6();
        }
        GovernmentPrimaryTail155Api.VolatileBits v() {
            return new GovernmentPrimaryTail155Api.VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5);
        }
        GovernmentPrimaryTail155Api.NonvolatileBits nv() {
            return new GovernmentPrimaryTail155Api.NonvolatileBits(rbx,rbp,rsi,rdi,r12,r13,r14,r15,x6);
        }
        void apply(GovernmentPrimaryTail155Api.VolatileBits v) {
            rax=v.raxBits();rcx=v.rcxBits();rdx=v.rdxBits();r8=v.r8Bits();r9=v.r9Bits();r10=v.r10Bits();r11=v.r11Bits();
            x0=v.xmm0();x1=v.xmm1();x2=v.xmm2();x3=v.xmm3();x4=v.xmm4();x5=v.xmm5();
        }
        void call(long site,GovernmentCrtBoundary185Api.TargetKind kind,long target,int length) {
            m.writeQword(rsp-8,image+site+length);
            apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(site,kind,target,rsp,v(),nv())));
        }
        void direct(long site,long target) { call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,5); }
        void indirect(long site,long target) { call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,3); }
        void push(long bits) { rsp-=8;m.writeQword(rsp,bits); }
        long pop() { long bits=m.readQword(rsp);rsp+=8;return bits; }
        GovernmentCrtBoundary185Api.NormalReturn ret() {
            long rip=m.readQword(rsp);rsp+=8;
            return new GovernmentCrtBoundary185Api.NormalReturn(v(),rip,rsp,nv());
        }
    }
}
