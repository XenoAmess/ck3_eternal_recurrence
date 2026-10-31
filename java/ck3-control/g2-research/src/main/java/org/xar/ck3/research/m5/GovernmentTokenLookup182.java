package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.Calls;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.Entry;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.Memory;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentTokenLookup182Api.Pause;

/** Full represented normal state for held292B; owned ports and preserved-NV preconditions. */
public final class GovernmentTokenLookup182 {
    private GovernmentTokenLookup182() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls calls,
            Pause pause, LoopBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(pause);
        Objects.requireNonNull(budget);
        Registers r = new Registers(entry);
        long image = entry.imageBaseBits();
        long frameRsp = entry.rspBits() - 0x28L;

        r.r9 = (int) r.rcx;
        r.rax = memory.readQword(image + 0x5cbede8L);
        r.rdx = 2L;
        r.rdx = u32(memory.lockedXaddDword(r.rax, (int) r.rdx));
        r.r8 = 0xfffffffeL;

        boolean acquired = (r.rdx & 1L) == 0;
        while (!acquired) {
            r.rcx = u32((int) r.r8);
            r.rcx = u32(memory.lockedXaddDword(r.rax, (int) r.rcx));
            for (;;) {
                budget.beforeStep(0x3f4f910L, r.rax);
                r.rcx = u32(memory.readDword(r.rax));
                if ((r.rcx & 1L) == 0) {
                    break;
                }
                pause.at(0x3f4f917L);
            }
            r.rcx = 2L;
            r.rcx = u32(memory.lockedXaddDword(r.rax, (int) r.rcx));
            acquired = (r.rcx & 1L) == 0;
        }

        // The negative-key edge bypasses the bound read; both acquired routes release once.
        boolean slotRead = (int) r.r9 >= 0
                && (int) r.r9 <= memory.readDword(r.rax + 0x54L);
        if (slotRead) {
            r.rcx = memory.readQword(r.rax + 0x48L);
            r.r9 = memory.readQword(r.rcx + r.r9 * 8L);
        }
        r.r8 = u32(memory.lockedXaddDword(r.rax, (int) r.r8));
        if (slotRead && r.r9 != 0L) {
            r.rax = r.r9;
            return normalReturn(r, memory, frameRsp);
        }

        r.rdx = 0x10L;
        r.rax = calls.readGsQword58();
        r.rcx = memory.readQword(r.rax);
        r.rax = u32(memory.readDword(r.rdx + r.rcx));
        long guard = image + 0x5dc1124L;
        long fallback = image + 0x5dc1128L;
        if (memory.readDword(guard) > (int) r.rax) {
            r.rcx = guard;
            invoke(r, memory, calls, image, frameRsp, 0x3f4f982L, 0x4223a84L);
            if (memory.readDword(guard) == -1) {
                memory.writeQword(fallback, 0L);
                memory.writeQword(image + 0x5dc1140L, 15L);
                memory.writeQword(image + 0x5dc1138L, 7L);
                r.rax = u32(memory.readDword(image + 0x472c488L));
                memory.writeDword(fallback, (int) r.rax);
                r.rax = memory.readUnsignedWord(image + 0x472c48cL) & 0xffffL;
                memory.writeWord(fallback + 4L, (int) r.rax);
                r.rax = memory.readUnsignedByte(image + 0x472c48eL) & 0xffL;
                memory.writeByte(fallback + 6L, (int) r.rax);
                memory.writeByte(fallback + 7L, 0);
                r.rcx = image + 0x43d7570L;
                invoke(r, memory, calls, image, frameRsp, 0x3f4f9e6L, 0x4223f24L);
                r.rcx = guard;
                invoke(r, memory, calls, image, frameRsp, 0x3f4f9f3L, 0x4223a24L);
            }
        }
        r.rax = fallback;
        return normalReturn(r, memory, frameRsp);
    }

    private static long u32(int bits) {
        return Integer.toUnsignedLong(bits);
    }

    private static void invoke(Registers r, Memory memory, Calls calls, long image,
            long frameRsp, long callSiteRva, long targetRva) {
        memory.writeQword(frameRsp - 8L, image + callSiteRva + 5L);
        r.apply(calls.invoke(new OpaqueCall(callSiteRva, targetRva, frameRsp,
                r.volatileBits(), r.nonvolatileBits)));
    }

    private static NormalReturn normalReturn(Registers r, Memory memory, long frameRsp) {
        long restoredRsp = frameRsp + 0x28L;
        long returnRip = memory.readQword(restoredRsp);
        return new NormalReturn(r.volatileBits(), returnRip, restoredRsp + 8L,
                r.nonvolatileBits);
    }

    private static final class Registers {
        private long rax, rcx, rdx, r8, r9, r10, r11;
        private Bits128 x0, x1, x2, x3, x4, x5;
        private final NonvolatileBits nonvolatileBits;

        private Registers(Entry entry) {
            nonvolatileBits = entry.nonvolatileBits();
            apply(entry.volatileBits());
        }

        private void apply(VolatileBits bits) {
            Objects.requireNonNull(bits);
            rax = bits.raxBits();
            rcx = bits.rcxBits();
            rdx = bits.rdxBits();
            r8 = bits.r8Bits();
            r9 = bits.r9Bits();
            r10 = bits.r10Bits();
            r11 = bits.r11Bits();
            x0 = bits.xmm0();
            x1 = bits.xmm1();
            x2 = bits.xmm2();
            x3 = bits.xmm3();
            x4 = bits.xmm4();
            x5 = bits.xmm5();
        }

        private VolatileBits volatileBits() {
            return new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11,
                    x0, x1, x2, x3, x4, x5);
        }
    }
}
