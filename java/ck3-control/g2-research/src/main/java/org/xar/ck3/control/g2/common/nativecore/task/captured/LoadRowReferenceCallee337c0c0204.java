package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Complete held 314B normal CFG; all external calls remain opaque owned ports. */
public final class LoadRowReferenceCallee337c0c0204 {
    private LoadRowReferenceCallee337c0c0204() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        State s = new State(entry, memory, calls, budget);
        int pc = 0x337C0C0;
        while (true) {
            switch (pc) {
                case 0x337C0C0 -> {
                    s.push(s.rsi);
                    s.rsp -= 0x50;
                    s.rax = u32((int) (s.rdx - 1));
                    s.rsi = s.rcx;
                    pc = s.rax > 0x1DL ? 0x337C1F4 : 0x337C0D5;
                }
                case 0x337C0D5 -> {
                    s.rcx = u32((int) s.rdx);
                    memory.writeQword(s.rsp + 0x60, s.rbx);
                    s.rdx = (s.rdx & ~0xFFL) | ((s.rdx + 2) & 0xFFL);
                    memory.writeQword(s.rsp + 0x70, s.rbp);
                    s.rbp = memory.readQword(s.rsi + 0x08);
                    s.rbx = 1;
                    s.rdx &= 0xFFL;
                    memory.writeByte(s.rsi + 0x18, (int) s.rdx);
                    s.rbx = u32((int) s.rbx << ((int) s.rcx & 31));
                    s.rcx = memory.readQword(s.rsi + 0x20);
                    memory.writeQword(s.rsp + 0x48, s.rdi);
                    s.rdi = u32(memory.readDword(s.rsi + 0x10));
                    s.rax = u32((int) (s.rbx - 1));
                    memory.writeQword(s.rsp + 0x40, s.r14);
                    memory.writeDword(s.rsi + 0x14, (int) s.rax);
                    s.r14 = 0;
                    memory.writeDword(s.rsi + 0x10, (int) s.r14);
                    s.rax = memory.readQword(s.rcx);
                    s.r8 = u32((int) (s.r14 + 0x08));
                    s.r9 = memory.readQword(s.rax + 0x08);
                    s.rax = u32((int) (s.rdx + 1));
                    s.rax = u32((int) s.rax + (int) s.rbx);
                    s.rdx = (int) s.rax;
                    s.rdx += s.rdx * 4;
                    s.rdx <<= 4;
                    s.call(0x337C12EL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, s.r9, 3);
                    s.rcx = u32(memory.readUnsignedByte(s.rsi + 0x18));
                    s.rdx = (int) s.rbx;
                    s.rdx += s.rcx;
                    memory.writeQword(s.rsi + 0x08, s.rax);
                    s.rcx = s.rdx + s.rdx * 4;
                    s.rcx <<= 4;
                    s.rcx += s.rax;
                    pc = s.rax == s.rcx ? 0x337C15D : 0x337C14F;
                }
                case 0x337C14F -> pc = 0x337C150;
                case 0x337C150 -> {
                    budget.beforeStep(0x337C150L, s.rax);
                    memory.writeByte(s.rax + 0x04, (int) s.r14);
                    s.rax += 0x50;
                    pc = s.rax != s.rcx ? 0x337C150 : 0x337C15D;
                }
                case 0x337C15D -> {
                    memory.writeByte(s.rcx + 0x04, 0xFF);
                    s.call(0x337C161L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x8CEEB0L, 5);
                    pc = s.rbp == s.rax ? 0x337C1C3 : 0x337C16B;
                }
                case 0x337C16B -> pc = (int) s.rdi <= 0 ? 0x337C1C3 : 0x337C16F;
                case 0x337C16F -> {
                    s.rbx = s.rbp + 0x48;
                    pc = 0x337C173;
                }
                case 0x337C173 -> {
                    budget.beforeStep(0x337C173L, s.rbx);
                    pc = memory.readUnsignedByte(s.rbx - 0x44) == (s.r14 & 0xFFL)
                            ? 0x337C1BB : 0x337C179;
                }
                case 0x337C179 -> {
                    s.r8 = u32(memory.readDword(s.rbx - 0x48));
                    s.rax = s.rsp + 0x68;
                    s.r9 = s.rbx - 0x40;
                    memory.writeQword(s.rsp + 0x20, s.rax);
                    s.rdx = s.rsp + 0x30;
                    memory.writeByte(s.rsp + 0x68, (int) s.r14);
                    s.rcx = s.rsi;
                    s.call(0x337C198L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x337C5D0L, 5);
                    s.rcx = memory.readQword(s.rbx);
                    pc = s.rcx == 0 ? 0x337C1B9 : 0x337C1A5;
                }
                case 0x337C1A5 -> {
                    s.r8 = memory.readQword(s.rcx);
                    s.rax = s.rbx - 0x38;
                    s.rdx = (s.rdx & ~0xFFL) | (s.rcx != s.rax ? 1L : 0L);
                    s.call(0x337C1B2L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                            memory.readQword(s.r8 + 0x20), 4);
                    memory.writeQword(s.rbx, s.r14);
                    pc = 0x337C1B9;
                }
                case 0x337C1B9 -> {
                    s.rdi = u32((int) s.rdi - 1);
                    pc = 0x337C1BB;
                }
                case 0x337C1BB -> {
                    s.rbx += 0x50;
                    pc = (int) s.rdi > 0 ? 0x337C173 : 0x337C1C3;
                }
                case 0x337C1C3 -> {
                    s.call(0x337C1C3L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x8CEEB0L, 5);
                    s.r14 = memory.readQword(s.rsp + 0x40);
                    s.rdi = memory.readQword(s.rsp + 0x48);
                    s.rbx = memory.readQword(s.rsp + 0x60);
                    pc = s.rbp == s.rax ? 0x337C1EF : 0x337C1DC;
                }
                case 0x337C1DC -> {
                    s.rcx = memory.readQword(s.rsi + 0x20);
                    s.r8 = 0x08;
                    s.rdx = s.rbp;
                    s.rax = memory.readQword(s.rcx);
                    s.call(0x337C1ECL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                            memory.readQword(s.rax + 0x10), 3);
                    pc = 0x337C1EF;
                }
                case 0x337C1EF -> {
                    s.rbp = memory.readQword(s.rsp + 0x70);
                    pc = 0x337C1F4;
                }
                case 0x337C1F4 -> {
                    s.rsp += 0x50;
                    s.rsi = s.pop();
                    return s.ret();
                }
                default -> throw new IllegalStateException("Unsupported source block: " + Integer.toHexString(pc));
            }
        }
    }

    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }

    private static final class State {
        final long image;
        final GovernmentCrtBoundary185Api.Memory memory;
        final GovernmentCrtBoundary185Api.Calls calls;
        final GovernmentCrtBoundary185Api.LoopBudget budget;
        long rsp, rax, rcx, rdx, r8, r9, r10, r11;
        long rbx, rbp, rsi, rdi, r12, r13, r14, r15;
        GovernmentPrimaryTail155Api.Bits128 x0, x1, x2, x3, x4, x5, x6;

        State(GovernmentCrtBoundary185Api.Entry entry,
                GovernmentCrtBoundary185Api.Memory memory,
                GovernmentCrtBoundary185Api.Calls calls,
                GovernmentCrtBoundary185Api.LoopBudget budget) {
            image = entry.imageBaseBits();
            rsp = entry.rspBits();
            this.memory = memory;
            this.calls = calls;
            this.budget = budget;
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

        void call(long siteRva, GovernmentCrtBoundary185Api.TargetKind kind, long targetBits, int length) {
            memory.writeQword(rsp - 8, image + siteRva + length);
            apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(
                    siteRva, kind, targetBits, rsp, v(), nv())));
        }

        void push(long bits) {
            rsp -= 8;
            memory.writeQword(rsp, bits);
        }

        long pop() {
            long bits = memory.readQword(rsp);
            rsp += 8;
            return bits;
        }

        GovernmentCrtBoundary185Api.NormalReturn ret() {
            long rip = memory.readQword(rsp);
            rsp += 8;
            return new GovernmentCrtBoundary185Api.NormalReturn(v(), rip, rsp, nv());
        }
    }
}
