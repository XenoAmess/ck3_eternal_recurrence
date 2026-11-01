package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.VectorFullData570.*;
/** Four complete source-frozen Scene methods, parent assembly only. */
public final class VectorFullBook570 {
 private VectorFullBook570() { }
public static VectorFullData570.Scene selfScene() {
    long E = VectorFullData570.E;
    long M = VectorFullData570.M;
    long RET = VectorFullData570.RET;
    long D = E - 8;
    long S = E - 8;

    // Entry: D=S=E-8, RSI=0x2003 (from n0), RAX=0x8877... (from v0)
    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
        M, E, VectorFullData570.v0(D, S), VectorFullData570.n0()
    );

    // Initial Memory: Only Q[E] = RET is seeded.
    List<VectorFullData570.Cell> initialMemory = new ArrayList<VectorFullData570.Cell>();
    initialMemory.add(VectorFullData570.c(8, E, RET));

    List<VectorFullData570.Step> steps = new ArrayList<VectorFullData570.Step>();

    // 1. PUSH RSI (260E040): Write Q[E-8] = RSI (which is 0x2003 from n0)
    steps.add(VectorFullData570.w(8, E - 8, 0x2003L));

    // 2. SUB RSP, 0x20 (260E042): RSP becomes E - 0x28. No memory effect.

    // 3. MOV RSI, RCX (260E046): RSI = D. No memory effect.

    // 4. CMP RCX, RDX (260E049): D == S. Branch taken.

    // 5. JE 0x260E132 (260E04C): Jump to self epilogue.

    // 6. MOV RAX, RSI (260E132): RAX = D. No memory effect.

    // 7. ADD RSP, 0x20 (260E135): RSP becomes E. No memory effect.

    // 8. POP RSI (260E139): Read Q[E-8] -> RSI.
    // The value at Q[E-8] was written by step 1 as 0x2003. So RSI becomes 0x2003.
    steps.add(VectorFullData570.r(8, E - 8, 0x2003L));

    // 9. RET (260E13A): Read Q[E] -> RIP. Value is RET.
    steps.add(VectorFullData570.r(8, E, RET));

    // Final Memory State:
    // Q[E] = RET (unchanged)
    // Q[E-8] = 0x2003 (written by PUSH, read by POP)
    List<VectorFullData570.Cell> finalMemory = new ArrayList<VectorFullData570.Cell>();
    finalMemory.add(VectorFullData570.c(8, E, RET));
    finalMemory.add(VectorFullData570.c(8, E - 8, 0x2003L));

    // Expected Result:
    // NormalReturn:
    //   VolatileBits: RAX=D, RCX=D, RDX=S, R8/R9/R10/R11/XMM0..5 from entry v0.
    //   NonvolatileBits: RBX/RBP/RSI/RDI/R12..15/XMM6 from entry n0.
    //   returnRipBits: RET
    //   callerRspBits: E + 8 (after POP and RET)
    //   DF: true (input DF is true, no flags changed)

    GovernmentCrtBoundary185Api.NormalReturn normalReturn = new GovernmentCrtBoundary185Api.NormalReturn(
        VectorFullData570.v(0x1000L, D, D, S), // VolatileBits: RAX=D, RCX=D, RDX=S, rest from v0
        RET, // returnRipBits
        E + 8, // callerRspBits
        VectorFullData570.n0() // NonvolatileBits: unchanged from entry
    );

    FullCopy437Api.CallResult expectedResult = new FullCopy437Api.CallResult(normalReturn, true);

    return new VectorFullData570.Scene(
        "selfScene",
        entry,
        true, // directionFlagSet (input DF)
        initialMemory,
        steps,
        expectedResult,
        finalMemory
    );
}
public static VectorFullData570.Scene negativeScene() {
    long m = 0x3300000000L;
    long e = 0x810000000000C008L;
    long d = 0x8100000000020000L;
    long s = 0x8100000000030000L;
    long p = 0x8100000000040000L;
    long ret = 0xAABBCCDD11223344L;
    long count = 0x80000001L;

    VolatileBits v = v0(d, s);
    NonvolatileBits n = n0();
    boolean df = false;

    List<Cell> initialMemory = new ArrayList<>();
    initialMemory.add(c(8, e, ret));
    initialMemory.add(c(8, s, p));
    initialMemory.add(c(4, s + 0xC, count));

    List<Step> steps = new ArrayList<>();
    steps.add(w(8, e - 8, n.rsiBits()));
    steps.add(w(8, e + 0x8, n.rbxBits()));
    steps.add(r(4, s + 0xC, count));
    steps.add(w(8, e + 0x18, n.rdiBits()));
    steps.add(r(8, s, p));
    steps.add(w(4, d + 0xC, 0));
    steps.add(w(4, d + 0xC, count));
    steps.add(r(8, e + 0x8, n.rbxBits()));
    steps.add(r(8, e + 0x18, n.rdiBits()));
    steps.add(r(8, e - 8, n.rsiBits()));
    steps.add(r(8, e, ret));

    VolatileBits finalV = new VolatileBits(d, d, s, v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(), v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
    NonvolatileBits finalN = new NonvolatileBits(n.rbxBits(), n.rbpBits(), n.rsiBits(), n.rdiBits(), n.r12Bits(), n.r13Bits(), n.r14Bits(), n.r15Bits(), n.xmm6());

    FullCopy437Api.CallResult expectedResult = new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(finalV, ret, e + 8, finalN), df);

    List<Cell> finalMemory = new ArrayList<>();
    finalMemory.add(c(8, e, ret));
    finalMemory.add(c(8, s, p));
    finalMemory.add(c(4, s + 0xC, count));
    finalMemory.add(c(8, e - 8, n.rsiBits()));
    finalMemory.add(c(8, e + 0x8, n.rbxBits()));
    finalMemory.add(c(8, e + 0x18, n.rdiBits()));
    finalMemory.add(c(4, d + 0xC, count));

    return new Scene("negative", new GovernmentCrtBoundary185Api.Entry(m, e, v, n), false, initialMemory, steps, expectedResult, finalMemory);
}
public static VectorFullData570.Scene nonGrowthAliasScene() {
    long M = VectorFullData570.M;
    long E = VectorFullData570.E;
    long D = VectorFullData570.D;
    long S = VectorFullData570.S;
    long P = VectorFullData570.P;
    long RET = VectorFullData570.RET;
    long W = E - 0x28L;
    long J = E - 0x30L;

    // Entry Construction
    VolatileBits v0 = VectorFullData570.v0(D, S);
    NonvolatileBits n0 = VectorFullData570.n0();
    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(M, E, v0, n0);

    // Initial Memory
    List<VectorFullData570.Cell> initialMemory = new ArrayList<VectorFullData570.Cell>();
    initialMemory.add(VectorFullData570.c(8, E, RET));
    initialMemory.add(VectorFullData570.c(8, S, P));
    initialMemory.add(VectorFullData570.c(4, S + 0xC, 2L));
    initialMemory.add(VectorFullData570.c(8, D, P + 8));
    initialMemory.add(VectorFullData570.c(4, D + 8, 2L));
    initialMemory.add(VectorFullData570.c(4, D + 0xC, 99L));
    initialMemory.add(VectorFullData570.c128(P, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));
    initialMemory.add(VectorFullData570.c(8, P + 0x10, 0x1716151413121110L));
    initialMemory.add(VectorFullData570.c128(P + 0x18, 0x1F1E1D1C1B1A1918L, 0x2726252423222120L));
    initialMemory.add(VectorFullData570.c(8, P + 0x28, 0x2F2E2D2C2B2A2928L));

    // Steps
    List<VectorFullData570.Step> steps = new ArrayList<VectorFullData570.Step>();

    // 1. PUSH RSI (260E040)
    steps.add(new VectorFullData570.Write(8, E - 8, n0.rsiBits(), 0L));

    // 2. MOV RBX to stack (260E052)
    steps.add(new VectorFullData570.Write(8, W + 0x30, n0.rbxBits(), 0L));

    // 3. Read Source Count (260E057)
    steps.add(new VectorFullData570.Read(4, S + 0xC, 2L, 0L));

    // 4. MOV RDI to stack (260E05A)
    steps.add(new VectorFullData570.Write(8, W + 0x40, n0.rdiBits(), 0L));

    // 5. Read Source Base (260E05F)
    steps.add(new VectorFullData570.Read(8, S, P, 0L));

    // 6. Clear Dest Count (260E062)
    steps.add(new VectorFullData570.Write(4, D + 0xC, 0L, 0L));

    // 7. Read Capacity (260E071)
    steps.add(new VectorFullData570.Read(4, D + 8, 2L, 0L));

    // 8. Write Dest Count (260E0F4)
    steps.add(new VectorFullData570.Write(4, D + 0xC, 2L, 0L));

    // 9. Read Dest Base (260E0FB)
    steps.add(new VectorFullData570.Read(8, D, P + 8, 0L));

    // 10. Budget Iter 1 (260E100)
    steps.add(new VectorFullData570.Budget(0x260E100L, P));

    // 11. Read 128 Src (260E100)
    steps.add(new VectorFullData570.Read(16, P, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));

    // 12. Write 128 Dest (260E10D)
    steps.add(new VectorFullData570.Write(16, P + 8, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));

    // 13. Read 64 Src (260E111) - Alias effect: sees overwritten bytes
    steps.add(new VectorFullData570.Read(8, P + 0x10, 0x0F0E0D0C0B0A0908L, 0L));

    // 14. Write 64 Dest (260E116)
    steps.add(new VectorFullData570.Write(8, P + 0x18, 0x0F0E0D0C0B0A0908L, 0L));

    // 15. Budget Iter 2 (260E100)
    steps.add(new VectorFullData570.Budget(0x260E100L, P + 0x18));

    // 16. Read 128 Src (260E100) - Alias effect: sees overwritten bytes
    steps.add(new VectorFullData570.Read(16, P + 0x18, 0x0F0E0D0C0B0A0908L, 0x2726252423222120L));

    // 17. Write 128 Dest (260E10D)
    steps.add(new VectorFullData570.Write(16, P + 0x20, 0x0F0E0D0C0B0A0908L, 0x2726252423222120L));

    // 18. Read 64 Src (260E111) - Alias effect: sees overwritten bytes
    steps.add(new VectorFullData570.Read(8, P + 0x28, 0x2726252423222120L, 0L));

    // 19. Write 64 Dest (260E116)
    steps.add(new VectorFullData570.Write(8, P + 0x30, 0x2726252423222120L, 0L));

    // 20. Read RBX Home (260E11F)
    steps.add(new VectorFullData570.Read(8, W + 0x30, n0.rbxBits(), 0L));

    // 21. Read RDI Home (260E127)
    steps.add(new VectorFullData570.Read(8, W + 0x40, n0.rdiBits(), 0L));

    // 22. Read RSI Home (260E130)
    steps.add(new VectorFullData570.Read(8, E - 8, n0.rsiBits(), 0L));

    // 23. Read RET (260E131)
    steps.add(new VectorFullData570.Read(8, E, RET, 0L));

    // Final Memory
    List<VectorFullData570.Cell> finalMemory = new ArrayList<VectorFullData570.Cell>();
    finalMemory.add(VectorFullData570.c(8, E, RET));
    finalMemory.add(VectorFullData570.c(8, E - 8, n0.rsiBits()));
    finalMemory.add(VectorFullData570.c(8, W + 0x30, n0.rbxBits()));
    finalMemory.add(VectorFullData570.c(8, W + 0x40, n0.rdiBits()));
    finalMemory.add(VectorFullData570.c(8, S, P));
    finalMemory.add(VectorFullData570.c(4, S + 0xC, 2L));
    finalMemory.add(VectorFullData570.c(8, D, P + 8));
    finalMemory.add(VectorFullData570.c(4, D + 8, 2L));
    finalMemory.add(VectorFullData570.c(4, D + 0xC, 2L));
    finalMemory.add(VectorFullData570.c(8, P, 0x0706050403020100L));
    finalMemory.add(VectorFullData570.c(8, P + 8, 0x0706050403020100L));
    finalMemory.add(VectorFullData570.c(8, P + 0x10, 0x0F0E0D0C0B0A0908L));
    finalMemory.add(VectorFullData570.c(8, P + 0x18, 0x0F0E0D0C0B0A0908L));
    finalMemory.add(VectorFullData570.c(8, P + 0x20, 0x0F0E0D0C0B0A0908L));
    finalMemory.add(VectorFullData570.c(8, P + 0x28, 0x2726252423222120L));
    finalMemory.add(VectorFullData570.c(8, P + 0x30, 0x2726252423222120L));

    // Expected Result
    // Final V: RAX=D, RCX=D, RDX=S, R8/R9/R10/R11 preserved, XMM0/1 updated, XMM2..5 preserved
    VolatileBits finalV = new VolatileBits(
        D, D, S,
        v0.r8Bits(), v0.r9Bits(), v0.r10Bits(), v0.r11Bits(),
        new Bits128(0x0F0E0D0C0B0A0908L, 0x2726252423222120L),
        new Bits128(0x2726252423222120L, 0L),
        v0.xmm2(), v0.xmm3(), v0.xmm4(), v0.xmm5()
    );
    // Final N: RBX/RBP/RSI/RDI/R12..15/XMM6 preserved from n0 (fresh restores match initial values in this scene)
    NonvolatileBits finalN = n0;

    GovernmentCrtBoundary185Api.NormalReturn normalReturn = new GovernmentCrtBoundary185Api.NormalReturn(finalV, RET, E + 8, finalN);
    FullCopy437Api.CallResult expectedResult = new FullCopy437Api.CallResult(normalReturn, true);

    return new VectorFullData570.Scene("nonGrowthAlias", entry, true, initialMemory, steps, expectedResult, finalMemory);
}
public static VectorFullData570.Scene growthScene() {
    long M = VectorFullData570.M;
    long E = VectorFullData570.E;
    long D = VectorFullData570.D;
    long S = VectorFullData570.S;
    long P = VectorFullData570.P;
    long OLD = VectorFullData570.OLD;
    long NEW = OLD + 8;
    long TO = P + 8;
    long ALT = VectorFullData570.ALT;
    long A1 = VectorFullData570.A1;
    long A2 = VectorFullData570.A2;
    long VT1 = VectorFullData570.VT1;
    long VT2 = VectorFullData570.VT2;
    long TARGET1 = VectorFullData570.TARGET1;
    long TARGET2 = VectorFullData570.TARGET2;
    long RET = VectorFullData570.RET;
    long RESTORED_BP = VectorFullData570.RESTORED_BP;

    VolatileBits v0 = VectorFullData570.v0(D, S);
    NonvolatileBits n0 = VectorFullData570.n0();
    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(M, E, v0, n0);
    boolean directionFlagSet = false;

    List<Cell> initialMemory = new ArrayList<>();
    initialMemory.add(VectorFullData570.c(8, E, RET));
    initialMemory.add(VectorFullData570.c(8, S, P));
    initialMemory.add(VectorFullData570.c(4, S + 0xC, 1));
    initialMemory.add(VectorFullData570.c(8, D, OLD));
    initialMemory.add(VectorFullData570.c(4, D + 8, 0));
    initialMemory.add(VectorFullData570.c(4, D + 0xC, 0));
    initialMemory.add(VectorFullData570.c(8, D + 0x10, A1));
    initialMemory.add(VectorFullData570.c(8, A1, VT1));
    initialMemory.add(VectorFullData570.c(8, VT1 + 8, TARGET1));
    initialMemory.add(VectorFullData570.c(8, A2, VT2));
    initialMemory.add(VectorFullData570.c(8, VT2 + 0x10, TARGET2));
    initialMemory.add(VectorFullData570.c128(OLD, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));
    initialMemory.add(VectorFullData570.c(8, OLD + 0x10, 0x1716151413121110L));
    initialMemory.add(VectorFullData570.c128(P, 0x1111222233334444L, 0x5555666677778888L));
    initialMemory.add(VectorFullData570.c(8, P + 0x10, 0x9999AAAABBBBCCCCL));

    List<Step> steps = new ArrayList<>();

    steps.add(VectorFullData570.w(8, E - 8, 0x2003L));





    steps.add(VectorFullData570.w(8, E + 8, 0x2001L));

    steps.add(VectorFullData570.r(4, S + 0xC, 1));

    steps.add(VectorFullData570.w(8, E + 0x18, 0x2004L));

    steps.add(VectorFullData570.r(8, S, P));

    steps.add(VectorFullData570.w(4, D + 0xC, 0));



    steps.add(VectorFullData570.r(4, D + 8, 0));


    steps.add(VectorFullData570.r(8, D + 0x10, A1));




    steps.add(VectorFullData570.w(8, E + 0x10, 0x2002L));

    steps.add(VectorFullData570.r(8, A1, VT1));

    steps.add(VectorFullData570.r(8, VT1 + 8, TARGET1));
    steps.add(VectorFullData570.w(8, E - 0x30, M + 0x260E09BL));

    VolatileBits vCall1 = VectorFullData570.v(0x5000, NEW, 0x5100000000000002L, 0x5300000000000003L);
    NonvolatileBits nCall1 = VectorFullData570.n(1, 0x2002, D, P, 0x2005, 0x2006, 0x2007, 0x2008);
    VolatileBits frame1V = new VolatileBits(0x8100000000070000L, 0x8100000000060000L, 0x0000000000000018L, 0x0000000000000008L, 0x7FFF111122223333L, 0x000000000000100AL, 0x000000000000100BL, new Bits128(0x0000000000001010L, 0xFFFFFFFFFFFFEFEFL), new Bits128(0x0000000000001020L, 0xFFFFFFFFFFFFEFDFL), new Bits128(0x0000000000001030L, 0xFFFFFFFFFFFFEFCFL), new Bits128(0x0000000000001040L, 0xFFFFFFFFFFFFEFBFL), new Bits128(0x0000000000001050L, 0xFFFFFFFFFFFFEFAFL), new Bits128(0x0000000000001060L, 0xFFFFFFFFFFFFEF9FL));
    GovernmentCrtBoundary185Api.Call call1 = new GovernmentCrtBoundary185Api.Call(0x260E098L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, TARGET1, E - 0x28, frame1V, nCall1);
    GovernmentCrtBoundary185Api.Entry childEntry1 = new GovernmentCrtBoundary185Api.Entry(M, E - 0x30, frame1V, nCall1);
    EmbeddedVector565Api.CallFrame frame1 = new EmbeddedVector565Api.CallFrame(call1, childEntry1, false, 3, M + 0x260E09BL);
    FullCopy437Api.CallResult result1 = VectorFullData570.result(vCall1, nCall1, M + 0x260E09BL, E - 0x28, true);
    List<Write> effects1 = new ArrayList<>();
    effects1.add(VectorFullData570.w(4, D + 0xC, 1));
    effects1.add(VectorFullData570.w(8, D + 0x10, A2));
    steps.add(new Invoke(frame1, result1, effects1));
    steps.addAll(effects1);

    steps.add(VectorFullData570.r(4, D + 0xC, 1));




    steps.add(VectorFullData570.r(8, D, OLD));



    steps.add(new Budget(0x260E0B0L, OLD));

    steps.add(VectorFullData570.r128(OLD, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));




    steps.add(VectorFullData570.w128(NEW, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));

    steps.add(VectorFullData570.r(8, OLD + 0x10, 0x0F0E0D0C0B0A0908L));

    steps.add(VectorFullData570.w(8, NEW + 0x10, 0x0F0E0D0C0B0A0908L));



    steps.add(VectorFullData570.r(8, D + 0x10, A2));


    steps.add(VectorFullData570.r(8, D, OLD));

    steps.add(VectorFullData570.r(8, A2, VT2));
    steps.add(VectorFullData570.r(8, VT2 + 0x10, TARGET2));

    VolatileBits vCall2 = VectorFullData570.v(0x6000, 0x6100000000000001L, 0x6200000000000002L, 0x6300000000000003L);
    NonvolatileBits nCall2 = VectorFullData570.n(1, NEW, D, P, 0x2005, 0x2006, 0x2007, 0x2008);
    VolatileBits frame2V = new VolatileBits(0x8100000000071000L, 0x8100000000061000L, 0x8100000000050000L, 0x0000000000000008L, 0x0000000000000000L, 0x000000000000500AL, 0x000000000000500BL, new Bits128(0x0706050403020100L, 0x0F0E0D0C0B0A0908L), new Bits128(0x0F0E0D0C0B0A0908L, 0x0000000000000000L), new Bits128(0x0000000000005030L, 0xFFFFFFFFFFFFAFCFL), new Bits128(0x0000000000005040L, 0xFFFFFFFFFFFFAFBFL), new Bits128(0x0000000000005050L, 0xFFFFFFFFFFFFAFAFL), new Bits128(0x0000000000005060L, 0xFFFFFFFFFFFFAF9FL));
    GovernmentCrtBoundary185Api.Call call2 = new GovernmentCrtBoundary185Api.Call(0x260E0E1L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, TARGET2, E - 0x28, frame2V, nCall2);
    GovernmentCrtBoundary185Api.Entry childEntry2 = new GovernmentCrtBoundary185Api.Entry(M, E - 0x30, frame2V, nCall2);
    EmbeddedVector565Api.CallFrame frame2 = new EmbeddedVector565Api.CallFrame(call2, childEntry2, true, 3, M + 0x260E0E4L);
    FullCopy437Api.CallResult result2 = VectorFullData570.result(vCall2, nCall2, M + 0x260E0E4L, E - 0x28, false);
    List<Write> effects2 = new ArrayList<>();
    effects2.add(VectorFullData570.w(8, S, ALT));
    effects2.add(VectorFullData570.w128(P, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L));
    effects2.add(VectorFullData570.w(8, P + 0x10, 0x1122334455667788L));
    effects2.add(VectorFullData570.w(8, E + 0x10, RESTORED_BP));
    steps.add(VectorFullData570.w(8, E - 0x30, M + 0x260E0E4L));
    steps.add(new Invoke(frame2, result2, effects2));
    steps.addAll(effects2);

    steps.add(VectorFullData570.w(8, D, NEW));

    steps.add(VectorFullData570.r(8, E + 0x10, RESTORED_BP));

    steps.add(VectorFullData570.w(4, D + 8, 1));

    steps.add(VectorFullData570.w(4, D + 0xC, 1));


    steps.add(VectorFullData570.r(8, D, NEW));


    steps.add(new Budget(0x260E100L, P));

    steps.add(VectorFullData570.r128(P, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L));




    steps.add(VectorFullData570.w128(NEW, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L));

    steps.add(VectorFullData570.r(8, P + 0x10, 0x1122334455667788L));

    steps.add(VectorFullData570.w(8, NEW + 0x10, 0x1122334455667788L));



    steps.add(VectorFullData570.r(8, E + 8, 0x2001L));


    steps.add(VectorFullData570.r(8, E + 0x18, 0x2004L));


    steps.add(VectorFullData570.r(8, E - 8, 0x2003L));

    steps.add(VectorFullData570.r(8, E, RET));

    List<Cell> finalMemory = new ArrayList<>();
    finalMemory.add(VectorFullData570.c(8, E, RET));
    finalMemory.add(VectorFullData570.c(8, E - 8, 0x2003L));
    finalMemory.add(VectorFullData570.c(8, E + 8, 0x2001L));
    finalMemory.add(VectorFullData570.c(8, E + 0x10, RESTORED_BP));
    finalMemory.add(VectorFullData570.c(8, E + 0x18, 0x2004L));
    finalMemory.add(VectorFullData570.c(8, S, ALT));
    finalMemory.add(VectorFullData570.c(8, D, NEW));
    finalMemory.add(VectorFullData570.c(4, D + 8, 1));
    finalMemory.add(VectorFullData570.c(4, D + 0xC, 1));
    finalMemory.add(VectorFullData570.c(8, D + 0x10, A2));
    finalMemory.add(VectorFullData570.c128(NEW, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L));
    finalMemory.add(VectorFullData570.c(8, NEW + 0x10, 0x1122334455667788L));
    finalMemory.add(VectorFullData570.c128(P, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L));
    finalMemory.add(VectorFullData570.c(8, P + 0x10, 0x1122334455667788L));
    finalMemory.add(VectorFullData570.c(4, S + 0xC, 1));
    finalMemory.add(VectorFullData570.c(8, OLD, 0x0706050403020100L));
    finalMemory.add(VectorFullData570.c(8, E - 0x30, M + 0x260E0E4L));

    VolatileBits vFinal = new VolatileBits(0x8100000000020000L, 0x6200000000000002L, 0x6300000000000003L, 0x0000000000006008L, 0x0000000000006009L, 0x000000000000600AL, 0x000000000000600BL, new Bits128(0x0123456789ABCDEFL, 0xFEDCBA9876543210L), new Bits128(0x1122334455667788L, 0x0000000000000000L), new Bits128(0x0000000000006030L, 0xFFFFFFFFFFFF9FCFL), new Bits128(0x0000000000006040L, 0xFFFFFFFFFFFF9FBFL), new Bits128(0x0000000000006050L, 0xFFFFFFFFFFFF9FAFL), new Bits128(0x0000000000006060L, 0xFFFFFFFFFFFF9F9FL));
    NonvolatileBits nFinal = VectorFullData570.n(0x2001, RESTORED_BP, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008);
    FullCopy437Api.CallResult expectedResult = VectorFullData570.result(vFinal, nFinal, RET, E + 8, false);

    return new VectorFullData570.Scene("growth", entry, directionFlagSet, initialMemory, steps, expectedResult, finalMemory);
}

 public static List<VectorFullData570.Scene> scenes() {
  return List.of(selfScene(), negativeScene(), nonGrowthAliasScene(), growthScene());
 }
 public static int verify() {
  List<VectorFullData570.Scene> all = scenes();
  int[] expected = {3, 11, 23, 46};
  int reads = 0, writes = 0, invokes = 0, budgets = 0;
  for (int i = 0; i < all.size(); i++) {
   VectorFullData570.Scene scene = all.get(i);
   if (scene.steps().size() != expected[i]) throw new AssertionError("Source trace count");
   for (VectorFullData570.Step step : scene.steps()) {
    if (step instanceof VectorFullData570.Read) reads++;
    else if (step instanceof VectorFullData570.Write) writes++;
    else if (step instanceof VectorFullData570.Invoke) invokes++;
    else if (step instanceof VectorFullData570.Budget) budgets++;
   }
   VectorFullHost570.verify(scene);
  }
  if (reads != 42 || writes != 35 || invokes != 2 || budgets != 4) {
   throw new AssertionError("Source event categories");
  }
  return all.size();
 }
 public static void main(String[] args) { System.out.println(verify()); }
}
