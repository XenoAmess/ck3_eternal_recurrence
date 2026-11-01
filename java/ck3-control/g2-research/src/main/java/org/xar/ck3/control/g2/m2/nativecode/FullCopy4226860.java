package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held normal COPY entry, within the explicit 185 register and owned DF projection. */
public final class FullCopy4226860 {
    private FullCopy4226860() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory, FullCopy437Api.Calls calls) {
        Objects.requireNonNull(input); Objects.requireNonNull(memory); Objects.requireNonNull(calls);
        var entry = input.entry();
        long image = entry.imageBaseBits();
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        r.rax = r.rcx;
        r.r10 = image;
        if (Long.compareUnsigned(r.r8, 0xFL) <= 0) {
            r.r9 = Integer.toUnsignedLong(memory.readDword(r.r10 + r.r8 * 4 + 0x6090000L));
            r.r9 += r.r10;
            long label = r.r9 - image;
            if (label == 0x422688EL) {
                // The zero-length family handler is an immediate RET.
            } else if (label == 0x4226890L) {
                r.r8 = memory.readQword(r.rdx);
                r.rcx = dword(memory, r.rdx + 8);
                r.r9 = word(memory, r.rdx + 0xC);
                r.r10 = octet(memory, r.rdx + 0xE);
                memory.writeQword(r.rax, r.r8);
                memory.writeDword(r.rax + 8, (int) r.rcx);
                memory.writeWord(r.rax + 0xC, (int) r.r9);
                memory.writeByte(r.rax + 0xE, (int) r.r10);
            } else if (label == 0x42268B0L) {
                r.r8 = memory.readQword(r.rdx);
                r.rcx = word(memory, r.rdx + 8);
                r.r9 = octet(memory, r.rdx + 0xA);
                memory.writeQword(r.rax, r.r8);
                memory.writeWord(r.rax + 8, (int) r.rcx);
                memory.writeByte(r.rax + 0xA, (int) r.r9);
            } else if (label == 0x42268C8L) {
                r.rcx = word(memory, r.rdx);
                memory.writeWord(r.rax, (int) r.rcx);
            } else if (label == 0x42268D0L) {
                r.rcx = dword(memory, r.rdx);
                r.r8 = word(memory, r.rdx + 4);
                r.r9 = octet(memory, r.rdx + 6);
                memory.writeDword(r.rax, (int) r.rcx);
                memory.writeWord(r.rax + 4, (int) r.r8);
                memory.writeByte(r.rax + 6, (int) r.r9);
            } else if (label == 0x42268E8L) {
                r.r8 = memory.readQword(r.rdx);
                r.rcx = dword(memory, r.rdx + 8);
                r.r9 = word(memory, r.rdx + 0xC);
                memory.writeQword(r.rax, r.r8);
                memory.writeDword(r.rax + 8, (int) r.rcx);
                memory.writeWord(r.rax + 0xC, (int) r.r9);
            } else if (label == 0x42268FFL) {
                r.rcx = word(memory, r.rdx);
                r.r8 = octet(memory, r.rdx + 2);
                memory.writeWord(r.rax, (int) r.rcx);
                memory.writeByte(r.rax + 2, (int) r.r8);
            } else if (label == 0x4226910L) {
                r.r8 = memory.readQword(r.rdx);
                r.rcx = dword(memory, r.rdx + 8);
                r.r9 = octet(memory, r.rdx + 0xC);
                memory.writeQword(r.rax, r.r8);
                memory.writeDword(r.rax + 8, (int) r.rcx);
                memory.writeByte(r.rax + 0xC, (int) r.r9);
            } else if (label == 0x4226926L) {
                r.r8 = memory.readQword(r.rdx);
                r.rcx = word(memory, r.rdx + 8);
                memory.writeQword(r.rax, r.r8);
                memory.writeWord(r.rax + 8, (int) r.rcx);
            } else if (label == 0x4226935L) {
                r.r8 = memory.readQword(r.rdx);
                r.rcx = octet(memory, r.rdx + 8);
                memory.writeQword(r.rax, r.r8);
                memory.writeByte(r.rax + 8, (int) r.rcx);
            } else if (label == 0x4226943L) {
                r.r8 = memory.readQword(r.rdx);
                r.rcx = dword(memory, r.rdx + 8);
                memory.writeQword(r.rax, r.r8);
                memory.writeDword(r.rax + 8, (int) r.rcx);
            } else if (label == 0x4226950L) {
                r.rcx = dword(memory, r.rdx);
                r.r8 = word(memory, r.rdx + 4);
                memory.writeDword(r.rax, (int) r.rcx);
                memory.writeWord(r.rax + 4, (int) r.r8);
            } else if (label == 0x422695FL) {
                r.rcx = dword(memory, r.rdx);
                r.r8 = octet(memory, r.rdx + 4);
                memory.writeDword(r.rax, (int) r.rcx);
                memory.writeByte(r.rax + 4, (int) r.r8);
            } else if (label == 0x422696DL) {
                r.rcx = memory.readQword(r.rdx);
                memory.writeQword(r.rax, r.rcx);
            } else if (label == 0x4226974L) {
                r.rcx = octet(memory, r.rdx);
                memory.writeByte(r.rax, (int) r.rcx);
            } else if (label == 0x422697AL) {
                r.rcx = dword(memory, r.rdx);
                memory.writeDword(r.rax, (int) r.rcx);
            } else {
                var current = snapshot(input, r);
                var tail = new GovernmentCrtBoundary185Api.Tail(0x422688BL,
                        GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, r.r9, current.entry());
                return calls.tail(new FullCopy437Api.TailFrame(tail, input.directionFlagSet()));
            }
            return finish(input, memory, r);
        }
        if (Long.compareUnsigned(r.r8, 0x20L) <= 0) {
            r.x1 = Objects.requireNonNull(memory.read128(r.rdx));
            r.x2 = Objects.requireNonNull(memory.read128(r.rdx + r.r8 - 0x10));
            memory.write128(r.rcx, r.x1);
            memory.write128(r.rcx + r.r8 - 0x10, r.x2);
            return finish(input, memory, r);
        }
        if (Long.compareUnsigned(r.rdx, r.rcx) < 0) {
            r.r9 = r.rdx + r.r8;
            if (Long.compareUnsigned(r.rcx, r.r9) < 0)
                return FullCopyBackward446.execute(snapshot(input, r), memory);
        }
        return FullCopyForward442.execute(snapshot(input, r), memory, calls);
    }

    private static FullCopy437Api.Input snapshot(FullCopy437Api.Input input, Registers r) {
        return new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(
                input.entry().imageBaseBits(), r.rsp, r.volatileBits(), r.nonvolatileBits()),
                input.directionFlagSet(), input.budget());
    }

    private static FullCopy437Api.CallResult finish(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory, Registers r) {
        long returned = memory.readQword(r.rsp);
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(), returned, r.rsp + 8, r.nonvolatileBits()), input.directionFlagSet());
    }

    private static long dword(FullCopy437Api.Memory memory, long address) {
        return Integer.toUnsignedLong(memory.readDword(address));
    }
    private static long word(FullCopy437Api.Memory memory, long address) {
        int value = memory.readUnsignedWord(address);
        if ((value & ~0xFFFF) != 0) throw new IllegalArgumentException("actual unsigned WORD required");
        return value;
    }
    private static long octet(FullCopy437Api.Memory memory, long address) {
        int value = memory.readUnsignedByte(address);
        if ((value & ~0xFF) != 0) throw new IllegalArgumentException("actual unsigned BYTE required");
        return value;
    }
}
