package org.xar.ck3.study.m6.full224;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/**
 * Real new224 scope: existing185 REPRESENTED normal state, not full hardwareABI.
 * Actual GovernmentCrtBoundary185Api.Entry supplies image, actual postCALL entrySP, all7V-GPR/XMM0..5 and8N-GPR/XMM6.
 * No missing fields may be fabricated/defaulted. DF/RFLAGS/XMM7..15/EH/hardware stackfault are NOT in this API.
 */
public final class DefaultObject185Wrappers224 {
    private DefaultObject185Wrappers224() { }

    /**
     * Actual 18B8571D0: startSP=s, SUB RSP0x28=>pre=s-0x28; MOV RCX,RDX only;
     * ownedCALL at0x8571D7 writes memory.writeQword(pre-0x8,image+0x8571DC) exactlyonce,
     * then calls.invoke(new185.Call(0x8571D7,DIRECT_RVA,0x4223B94,pre,currentV,currentN)).
     * TargetBits is RVA forDIRECT_RVA, not image+RVA.
     * Call.rsp is PRE-CALL; port owns calleeRET and returns all represented actualV, while normalport preserves providedN.
     * Apply all returnedV. Source then ADD RSP0x28 and RET: freshreadQword at original s, callerSP=s+0x8, preserve all actual representedN.
     * No guessed childreturnV or extra stackpush/pop.
     */
    public static NormalReturn fromSlot08(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // SUB RSP, 0x28
        long pre = s - 0x28L;

        // MOV RCX, RDX (mechanical register update, no external effect)
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, pre, currentV, currentN));
        r.rcx = r.rdx;

        // CALL at 0x8571D7: write return address to memory at pre-0x8
        long callSiteRva = 0x8571D7L;
        long targetRva = 0x4223B94L;
        long retAddr = image + callSiteRva + 5L; // 0x8571DC
        memory.writeQword(pre - 0x8L, retAddr);

        // Invoke the owned call
        Call call = new Call(callSiteRva, TargetKind.DIRECT_RVA, targetRva, pre, r.volatileBits(), r.nonvolatileBits());
        VolatileBits returnedV = calls.invoke(call);

        // Apply all returned volatile bits
        r.apply(returnedV);

        // ADD RSP, 0x28
        r.rsp = s;

        // RET: fresh readQword at original s
        long rip = memory.readQword(s);
        long callerSP = s + 0x8L;

        // Preserve all actual represented nonvolatile bits
        return new NormalReturn(r.volatileBits(), rip, callerSP, r.nonvolatileBits());
    }

    /**
     * Actual 14B8571C0: TEST entryRDX; if0, do actualRET fresh readQword(s), callerSP=s+0x8, entireentryV/N unchanged (including highbitRAX).
     * No port call. Else MOV RCX,RDX only and return actual calls.tail(new185.Tail(0x8571C8,DIRECT_RVA,0x40EC530,new185.Entry(image,s,currentV,currentN))).
     * No new CALLpush and NO ownRET afterTAIL. No eagerCalls nullvalidation on zero branch, no RET value cached from input, no exception swallowing.
     * Owned normal-port exceptions are software outcomes, not NativeEH.
     */
    public static NormalReturn fromSlot10(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // TEST RDX, RDX
        if (currentV.rdxBits() == 0L) {
            // Zero branch: actual RET, no port call
            long rip = memory.readQword(s);
            long callerSP = s + 0x8L;
            // Entire entry V/N unchanged (including highbitRAX)
            return new NormalReturn(currentV, rip, callerSP, currentN);
        }

        // Non-zero branch: MOV RCX, RDX only
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, s, currentV, currentN));
        r.rcx = r.rdx;

        // Tail JMP to 0x40EC530
        long jumpSiteRva = 0x8571C8L;
        long targetRva = 0x40EC530L;
        Entry tailEntry = new Entry(image, s, r.volatileBits(), r.nonvolatileBits());
        Tail tail = new Tail(jumpSiteRva, TargetKind.DIRECT_RVA, targetRva, tailEntry);

        // No new CALLpush and NO ownRET afterTAIL
        return calls.tail(tail);
    }
}