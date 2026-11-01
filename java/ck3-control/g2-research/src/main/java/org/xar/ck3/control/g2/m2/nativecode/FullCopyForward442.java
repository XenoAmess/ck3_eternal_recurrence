package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import java.util.Objects;

public final class FullCopyForward442 {
    private FullCopyForward442() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input, FullCopy437Api.Memory memory, FullCopy437Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        boolean directionFlagSet = input.directionFlagSet();
        GovernmentCrtBoundary185Api.LoopBudget budget = input.budget();

        GovernmentPrimaryTail155Api.VolatileBits v = entry.volatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits n = entry.nonvolatileBits();
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();

        long rax = v.raxBits();
        long rdx = v.rdxBits();
        long r8 = v.r8Bits();
        long r10 = v.r10Bits();
        long rcx = v.rcxBits(), r9 = v.r9Bits();


        int cpuVal = memory.readDword(imageBase + 0x542F098L);
        if (Integer.compareUnsigned(cpuVal, 3) < 0) {
            FullCopy437Api.Input sseInput = new FullCopy437Api.Input(entry, directionFlagSet, budget);
            return FullCopySse445.execute(sseInput, memory, calls);
        }

        if (Long.compareUnsigned(r8, 0x2000L) <= 0) {
        } else {
            if (Long.compareUnsigned(r8, 0x180000L) > 0) {
            } else {
                int flagVal = memory.readUnsignedByte(imageBase + 0x5C5CBB0L);
                if ((flagVal & ~255) != 0) throw new IllegalArgumentException("actual BYTE required");
                if ((flagVal & 2) != 0) {
                    FullCopy437Api.Input repInput = new FullCopy437Api.Input(entry, directionFlagSet, budget);
                    return FullCopyRep4226840.execute(repInput, memory);
                }
            }
        }

        FullCopy437Api.Bits256 headSnapshot = memory.read256(rdx);
        FullCopy437Api.Bits256 tailSnapshot = memory.read256(rdx + r8 - 32);


        boolean initialBulk = true;
        if (Long.compareUnsigned(r8, 0x100L) <= 0) {
            initialBulk = false;
        } else {
            r9 = rcx;
            r9 = r9 & 0x1FL;
            r9 = r9 - 32;
            rcx = rcx - r9;
            rdx = rdx - r9;
            r8 = r8 + r9;
            if (Long.compareUnsigned(r8, 0x100L) <= 0) {
                initialBulk = false;
            } else {
                if (Long.compareUnsigned(r8, 0x180000L) > 0) {
                } else {
                }
            }
        }

        GovernmentPrimaryTail155Api.NonvolatileBits currentN = n;
        GovernmentPrimaryTail155Api.VolatileBits currentV = new GovernmentPrimaryTail155Api.VolatileBits(
            rax, rcx, rdx, r8, r9, r10, v.r11Bits(),
            headSnapshot.low(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), tailSnapshot.low()
        );

        GovernmentCrtBoundary185Api.Entry currentEntry = new GovernmentCrtBoundary185Api.Entry(
            imageBase, rsp, currentV, currentN
        );
        FullCopy437Api.Input currentInput = new FullCopy437Api.Input(currentEntry, directionFlagSet, budget);
        FullCopyCaptured442 captured = new FullCopyCaptured442(currentInput, headSnapshot, tailSnapshot, initialBulk);

        if (Long.compareUnsigned(r8, 0x180000L) > 0) {
            return FullCopyStreamingAvx444.execute(captured, memory, calls);
        } else {
            return FullCopyCachedAvx443.execute(captured, memory, calls);
        }
    }
}
