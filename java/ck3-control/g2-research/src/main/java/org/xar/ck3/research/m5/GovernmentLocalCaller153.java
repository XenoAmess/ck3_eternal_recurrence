package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCaller153Api.Calls;
import org.xar.ck3.research.m5.GovernmentCaller153Api.DiagnosticCall;
import org.xar.ck3.research.m5.GovernmentCaller153Api.Entry;
import org.xar.ck3.research.m5.GovernmentCaller153Api.Memory;
import org.xar.ck3.research.m5.GovernmentCaller153Api.Outcome;
import org.xar.ck3.research.m5.GovernmentTierLookupKey150.LookupKey32;
import org.xar.ck3.research.m5.GovernmentTierLookupKey150.RawTier32;

/**
 * Pending method; must reuse the already implemented conversion, not reimplement it.
 */
public final class GovernmentLocalCaller153 {
    private GovernmentLocalCaller153() { }

    public static Outcome execute(Entry entry, Memory memory, Calls calls) {
        // 1. Signed guard: CMP DWORD[G+4D0], 2; JGE skips all later local operations including fieldstore.
        int guardVal = memory.readDword(entry.governmentBits() + 0x4D0L);
        if (guardVal >= 2) {
            return Outcome.SKIPPED_SIGNED_GUARD;
        }

        // 2. Fresh read of the DWORD at G+4D0 for the adapter.
        //    "Adapter must read it again and invoke existing GovernmentTierLookupKey150.convert(new RawTier32(fresh)); first guard read cannot substitute."
        int freshVal = memory.readDword(entry.governmentBits() + 0x4D0L);
        RawTier32 rawTier = new RawTier32(freshVal);
        LookupKey32 lookupKey = GovernmentTierLookupKey150.convert(rawTier);

        // 3. Call 3F4F8E0 with the LookupKey32. Capture full RAX to R14.
        //    "call3F4F8E0 is an opaque exact typed port returning raw64, including zero/high-bit values."
        long r14Bits = calls.call3F4F8E0(lookupKey);

        // 4. Read QWORD GS:[58] as a Calls port, then Memory QWORD at that returned RCX.
        //    "Read QWORD GS:[58] as a Calls port, then Memory QWORD at that returned RCX; read unsigned byte at returnedRDX + zeroextend32(savedTlsOffset)."
        //    Actual assembly: 30A3ED6 MOV RCX, GS:[58]; 30A3EDF MOV RDX, [RCX]; 30A3EE2 CMP BYTE[R12+RDX], 0
        //    This means: readGsQword58() returns the value of GS:[58] (which is RCX).
        //    Then readQword(RCX) returns the value at [RCX] (which is RDX).
        //    Then readUnsignedByte(RDX + zeroextend32(R12)) checks the byte.
        long gs58Val = calls.readGsQword58();
        long rdxVal = memory.readQword(gs58Val);
        long byteAddr = rdxVal + (entry.savedTlsOffsetDwordBits() & 0xFFFFFFFFL);
        int byteVal = memory.readUnsignedByte(byteAddr);

        if (byteVal != 0) {
            // "Any nonzero byte JNE30A3F43 skips counter/helper/diagnostic/atomic, still writes7."
            memory.writeDword(entry.governmentBits() + 0x4D0L, 7);
            return Outcome.NORMALIZED_TLS_FLAG;
        }

        // 5. Read signed DWORD at imageBase+5C6A9DC. If >=0x186A0, skip helper/diagnostic/atomic, still write7.
        //    The address is derived from imageBase. In the Entry, imageBaseBits is provided.
        //    0x5C6A9DC is the offset from imageBase.
        long counterAddr = entry.imageBaseBits() + 0x5C6A9DCL;
        int counterVal = memory.readDword(counterAddr);
        if (counterVal >= 0x186A0) {
            // "If >=0x186A0, skip helper/diagnostic/atomic, still write7."
            memory.writeDword(entry.governmentBits() + 0x4D0L, 7);
            return Outcome.NORMALIZED_COUNTER_LIMIT;
        }

        // 6. CALL 3F5F970 ECX=0x10000; zero returnedRAX skips diagnostic/atomic, still writes7.
        //    "CALL3F5F970 ECX=0x10000; zero returnedRAX skips diagnostic/atomic, still writes7."
        long helperRax = calls.call3F5F970(0x10000);
        if (helperRax == 0L) {
            // "zero returnedRAX skips diagnostic/atomic, still writes7."
            memory.writeDword(entry.governmentBits() + 0x4D0L, 7);
            return Outcome.NORMALIZED_NULL_HELPER;
        }

        // 7. Nonzero helperRAX calls ABBAF0 with specific arguments.
        //    "Nonzero helperRAX callsABBAF0 with RCX=helperRAX, RDX=imageBase+48B7A48, R8D=1A8, R9D=4, stack20=imageBase+48B75E0, stack28=earlier lookupRAX (captured R14), stack30=entryRSI."
        long rcxArg = helperRax;
        long rdxArg = entry.imageBaseBits() + 0x48B7A48L;
        int r8dArg = 0x1A8;
        int r9dArg = 4;
        long stack20Arg = entry.imageBaseBits() + 0x48B75E0L;
        long stack28Arg = r14Bits; // captured R14 from step 3
        long stack30Arg = entry.savedRsiBits();

        DiagnosticCall diagCall = new DiagnosticCall(
            rcxArg,
            rdxArg,
            r8dArg,
            r9dArg,
            stack20Arg,
            stack28Arg,
            stack30Arg
        );
        calls.callABBAF0(diagCall);

        // 8. After ABBAF0 normal return only, LOCK XADD DWORD[imageBase+5C6A9DC], entryR15D.
        //    "After ABBAF0 normal return only, LOCK XADD DWORD[imageBase+5C6A9DC],entryR15D. Its captured oldDWORD return is ignored by this local consumer."
        long xaddAddr = entry.imageBaseBits() + 0x5C6A9DCL;
        int xaddAddend = entry.savedR15dBits();
        memory.lockedXaddDword(xaddAddr, xaddAddend);

        // 9. Then MOV DWORD[G+4D0], 7.
        //    "Then MOV DWORD[G+4D0],7."
        memory.writeDword(entry.governmentBits() + 0x4D0L, 7);

        return Outcome.NORMALIZED_DIAGNOSTIC;
    }
}
