package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Tiny package-private final class implementing ONLY the sourcebasicblock8897CB..8897DC
 * selected by owner caller after full93prologue and TEST EDI signed<=0.
 * This is one basic block, not the whole 93 producer claim.
 */
final class EmbeddedClearNonPositive587 {
    private EmbeddedClearNonPositive587() { }

    /**
     * Translates exact held instructions in order:
     * 1. 8897CB MOV RSI, QWORD[RSP+38hex] FIRST
     * 2. 8897D0 MOV DWORD[RCX+C], 0 SECOND
     * 3. 8897D7 ADD RSP, 20hex
     * 4. 8897DB POP RDI from actualMemory/advance8
     * 5. 8897DC RET from actualfreshMemory/advance8
     *
     * Supplied registers are actual CURRENT body state with RSP=entryE-28hex,
     * RSI=RCX receiver and EDI from MOV DWORD zeroextended.
     * Do not redo prologue, readcount, branch, CALL, budget, create default registers
     * or perform opaque algorithm.
     *
     * Return actual current full V/N via 185.NormalReturn(actualV, actualfreshRIP, actualpostRETSP, actualN),
     * same incoming DF via 437.CallResult.
     * Keep source aliasing/readwrite widths/order, all remaining GPR/XMM bits pass through.
     * No sourceEntryN/RET repair or use of old scalar clear helper.
     */
    static FullCopy437Api.CallResult finish(GovernmentPrimaryTail155Api.Registers r, boolean directionFlagSet, FullCopy437Api.Memory memory) {
        // 1. 8897CB: MOV RSI, QWORD PTR [RSP+0x38]
        // Read QWORD at RSP + 0x38 and assign to RSI
        long rspPlus38 = r.rsp + 0x38L;
        long newRsi = memory.readQword(rspPlus38);
        r.rsi = newRsi;

        // 2. 8897D0: MOV DWORD PTR [RCX+0xC], 0
        // Write DWORD 0 at RCX + 0xC
        long rcxPlusC = r.rcx + 0xC;
        memory.writeDword(rcxPlusC, 0);

        // 3. 8897D7: ADD RSP, 0x20
        r.rsp += 0x20L;

        // 4. 8897DB: POP RDI
        // Read QWORD at current RSP, assign to RDI, then advance RSP by 8
        long popAddr = r.rsp;
        long poppedRdi = memory.readQword(popAddr);
        r.rdi = poppedRdi;
        r.rsp += 8L;

        // 5. 8897DC: RET
        // Read QWORD at current RSP (return address), assign to RIP, then advance RSP by 8
        long retAddr = r.rsp;
        long returnRip = memory.readQword(retAddr);
        r.rsp += 8L;

        // Capture actual current full V/N
        GovernmentPrimaryTail155Api.VolatileBits actualV = r.volatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits actualN = r.nonvolatileBits();

        // Construct NormalReturn with actual fresh RIP and post-RET SP
        GovernmentCrtBoundary185Api.NormalReturn normalReturn = new GovernmentCrtBoundary185Api.NormalReturn(
            actualV,
            returnRip,
            r.rsp,
            actualN
        );

        // Return CallResult with same incoming directionFlagSet
        return new FullCopy437Api.CallResult(normalReturn, directionFlagSet);
    }
}