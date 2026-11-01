package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.CallResult;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Memory;
import java.util.Objects;

public final class FullCopyRep4226840 {
    private FullCopyRep4226840() { }

    public static CallResult execute(Input input, Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Entry entry = input.entry();
        boolean df = input.directionFlagSet();
        LoopBudget budget = input.budget();

        long rsp = entry.rspBits();
        NonvolatileBits n = entry.nonvolatileBits();
        VolatileBits v = entry.volatileBits();

        // 1. PUSH RDI (SP-8)
        memory.writeQword(rsp - 8, n.rdiBits());
        rsp -= 8;

        // 2. PUSH RSI (SP-16)
        memory.writeQword(rsp - 8, n.rsiBits());
        rsp -= 8;

        // 3. MOV RDI, RCX
        long rdi = v.rcxBits();

        // 4. MOV RSI, RDX
        long rsi = v.rdxBits();

        // 5. MOV RCX, R8
        long rcx = v.r8Bits();

        // 6. REP MOVSB loop
        while (rcx != 0) {
            budget.beforeStep(0x422684BL, rdi);
            int byteVal = memory.readUnsignedByte(rsi);
            if (byteVal < 0 || byteVal > 255) {
                throw new IllegalArgumentException("Invalid byte value");
            }
            memory.writeByte(rdi, byteVal);
            if (df) {
                rdi--;
                rsi--;
            } else {
                rdi++;
                rsi++;
            }
            rcx--;
        }

        // 7. POP RSI
        long poppedRsi = memory.readQword(rsp);
        rsp += 8;

        // 8. POP RDI
        long poppedRdi = memory.readQword(rsp);
        rsp += 8;

        // 9. RET
        long retAddr = memory.readQword(rsp);
        rsp += 8;

        // Construct NormalReturn
        // V: RCX is 0 (loop termination), others pass-through
        VolatileBits updatedV = new VolatileBits(
            v.raxBits(), 0L, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
            v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5()
        );

        // N: RSI/RDI from fresh POPs, others pass-through
        NonvolatileBits updatedN = new NonvolatileBits(
            n.rbxBits(), n.rbpBits(), poppedRsi, poppedRdi,
            n.r12Bits(), n.r13Bits(), n.r14Bits(), n.r15Bits(), n.xmm6()
        );

        NormalReturn nr = new NormalReturn(updatedV, retAddr, rsp, updatedN);
        return new CallResult(nr, df);
    }
}