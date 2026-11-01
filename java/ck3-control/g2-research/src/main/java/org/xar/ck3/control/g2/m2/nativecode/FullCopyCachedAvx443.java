package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Only cached AVX 4226A30..6B5D, within the owned low-128 register projection. */
public final class FullCopyCachedAvx443 {
    private FullCopyCachedAvx443() { }

    public static FullCopy437Api.CallResult execute(FullCopyCaptured442 captured,
            FullCopy437Api.Memory memory, FullCopy437Api.Calls calls) {
        Objects.requireNonNull(captured);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        FullCopy437Api.Input input = captured.input();
        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));

        if (captured.initialBulk()) {
            do {
                input.budget().beforeStep(0x4226A30L, r.rcx);
                FullCopy437Api.Bits256 y1 = memory.read256(r.rdx);
                r.x1 = y1.low();
                FullCopy437Api.Bits256 y2 = memory.read256(r.rdx + 0x20L);
                r.x2 = y2.low();
                FullCopy437Api.Bits256 y3 = memory.read256(r.rdx + 0x40L);
                r.x3 = y3.low();
                FullCopy437Api.Bits256 y4 = memory.read256(r.rdx + 0x60L);
                r.x4 = y4.low();
                memory.write256(r.rcx, y1);
                memory.write256(r.rcx + 0x20L, y2);
                memory.write256(r.rcx + 0x40L, y3);
                memory.write256(r.rcx + 0x60L, y4);
                y1 = memory.read256(r.rdx + 0x80L);
                r.x1 = y1.low();
                y2 = memory.read256(r.rdx + 0xA0L);
                r.x2 = y2.low();
                y3 = memory.read256(r.rdx + 0xC0L);
                r.x3 = y3.low();
                y4 = memory.read256(r.rdx + 0xE0L);
                r.x4 = y4.low();
                memory.write256(r.rcx + 0x80L, y1);
                memory.write256(r.rcx + 0xA0L, y2);
                memory.write256(r.rcx + 0xC0L, y3);
                memory.write256(r.rcx + 0xE0L, y4);
                r.rcx += 0x100L;
                r.rdx += 0x100L;
                r.r8 -= 0x100L;
            } while (Long.compareUnsigned(r.r8, 0x100L) >= 0);
        }

        r.r9 = (r.r8 + 0x1FL) & ~0x1FL;
        r.r11 = r.r9 >>> 5;
        r.r11 = Integer.toUnsignedLong(memory.readDword(r.r10 + r.r11 * 4L + 0x6090040L));
        r.r11 += r.r10;
        long image = entry.imageBaseBits();
        int start;
        if (r.r11 == image + 0x4226AD5L) start = 0;
        else if (r.r11 == image + 0x4226AE9L) start = 1;
        else if (r.r11 == image + 0x4226AFDL) start = 2;
        else if (r.r11 == image + 0x4226B11L) start = 3;
        else if (r.r11 == image + 0x4226B25L) start = 4;
        else if (r.r11 == image + 0x4226B33L) start = 5;
        else if (r.r11 == image + 0x4226B41L) start = 6;
        else if (r.r11 == image + 0x4226B4FL) start = 7;
        else if (r.r11 == image + 0x4226B56L) start = 8;
        else {
            VolatileBits current = new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11,
                    r.x0, r.x1, r.x2, r.x3, r.x4, r.x5);
            GovernmentCrtBoundary185Api.Entry targetEntry = new GovernmentCrtBoundary185Api.Entry(
                    image, r.rsp, current, r.nonvolatileBits());
            GovernmentCrtBoundary185Api.Tail transfer = new GovernmentCrtBoundary185Api.Tail(
                    0x4226AD2L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                    r.r11, targetEntry);
            return calls.tail(new FullCopy437Api.TailFrame(transfer, input.directionFlagSet()));
        }

        if (start <= 0) {
            FullCopy437Api.Bits256 y1 = memory.read256(r.rdx + r.r9 - 0x100L);
            r.x1 = y1.low();
            memory.write256(r.rcx + r.r9 - 0x100L, y1);
        }
        if (start <= 1) {
            FullCopy437Api.Bits256 y1 = memory.read256(r.rdx + r.r9 - 0xE0L);
            r.x1 = y1.low();
            memory.write256(r.rcx + r.r9 - 0xE0L, y1);
        }
        if (start <= 2) {
            FullCopy437Api.Bits256 y1 = memory.read256(r.rdx + r.r9 - 0xC0L);
            r.x1 = y1.low();
            memory.write256(r.rcx + r.r9 - 0xC0L, y1);
        }
        if (start <= 3) {
            FullCopy437Api.Bits256 y1 = memory.read256(r.rdx + r.r9 - 0xA0L);
            r.x1 = y1.low();
            memory.write256(r.rcx + r.r9 - 0xA0L, y1);
        }
        if (start <= 4) {
            FullCopy437Api.Bits256 y1 = memory.read256(r.rdx + r.r9 - 0x80L);
            r.x1 = y1.low();
            memory.write256(r.rcx + r.r9 - 0x80L, y1);
        }
        if (start <= 5) {
            FullCopy437Api.Bits256 y1 = memory.read256(r.rdx + r.r9 - 0x60L);
            r.x1 = y1.low();
            memory.write256(r.rcx + r.r9 - 0x60L, y1);
        }
        if (start <= 6) {
            FullCopy437Api.Bits256 y1 = memory.read256(r.rdx + r.r9 - 0x40L);
            r.x1 = y1.low();
            memory.write256(r.rcx + r.r9 - 0x40L, y1);
        }
        if (start <= 7) memory.write256(r.rcx + r.r8 - 0x20L, captured.tail());
        memory.write256(r.rax, captured.head());
        // VZEROUPPER at 4226B5A changes only state outside this declared projection.
        VolatileBits result = new VolatileBits(r.rax, r.rcx, r.rdx, r.r8, r.r9, r.r10, r.r11,
                r.x0, r.x1, r.x2, r.x3, r.x4, r.x5);
        GovernmentCrtBoundary185Api.NormalReturn returned = new GovernmentCrtBoundary185Api.NormalReturn(
                result, memory.readQword(r.rsp), r.rsp + 8L,
                r.nonvolatileBits());
        return new FullCopy437Api.CallResult(returned, input.directionFlagSet());
    }
}
