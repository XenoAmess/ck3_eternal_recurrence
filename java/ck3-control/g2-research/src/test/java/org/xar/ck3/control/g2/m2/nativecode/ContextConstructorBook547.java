package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import static org.xar.ck3.control.g2.m2.nativecode.ContextConstructorData547.*;
import org.xar.ck3.control.g2.m2.nativecode.ContextConstructor543Api.CallFrame;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.CallResult;

/** Two independent original-source normal/alias witnesses. */
public final class ContextConstructorBook547 {
 private ContextConstructorBook547() { }
public static ContextConstructorData547.Scene normalScene() {
    long M = ContextConstructorData547.M;
    long E = ContextConstructorData547.E;
    long D = ContextConstructorData547.D;
    long S = ContextConstructorData547.S;
    long RET = ContextConstructorData547.RET;
    long bodySP = E - 0x38;
    long childSP = E - 0x40;

    List<ContextConstructorData547.Cell> initialMemory = List.of(
        ContextConstructorData547.c(8, E, RET),
        ContextConstructorData547.c128(S, 0x8877665544332211L, 0xFFEEDDCCBBAA9988L),
        ContextConstructorData547.c(4, S + 0x10, 0xFFABCDE0L)
    );

    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
        M, E, ContextConstructorData547.v0(S), ContextConstructorData547.n0()
    );
    boolean initialDF = false;

    List<ContextConstructorData547.Step> steps = new ArrayList<>();

    steps.add(ContextConstructorData547.w(8, E + 0x10, 0x2001L));
    steps.add(ContextConstructorData547.w(8, E + 0x18, 0x2002L));
    steps.add(ContextConstructorData547.w(8, E + 0x08, D));
    steps.add(ContextConstructorData547.w(8, E - 0x08, 0x2003L));
    steps.add(ContextConstructorData547.w(8, E - 0x10, 0x2004L));
    steps.add(ContextConstructorData547.w(8, E - 0x18, 0x2007L));

    steps.add(ContextConstructorData547.w(4, D, 0L));
    steps.add(ContextConstructorData547.w(8, D + 0x08, 0L));
    steps.add(ContextConstructorData547.w(4, D + 0x10, 0xFFFFFFFFL));

    VolatileBits v1_pre = new VolatileBits(0x8877665544332211L,0x8100000000020018L,0x8100000000030000L,0x0000000000001008L,0x0000000000001009L,0x000000000000100AL,0x000000000000100BL,new Bits128(0x0000000000001010L,0xFFFFFFFFFFFFEFEFL),new Bits128(0x0000000000001020L,0xFFFFFFFFFFFFEFDFL),new Bits128(0x0000000000001030L,0xFFFFFFFFFFFFEFCFL),new Bits128(0x0000000000001040L,0xFFFFFFFFFFFFEFBFL),new Bits128(0x0000000000001050L,0xFFFFFFFFFFFFEFAFL),new Bits128(0x0000000000001060L,0xFFFFFFFFFFFFEF9FL));
    NonvolatileBits n1_pre = ContextConstructorData547.n(0x0000000000002001L,0x0000000000000000L,0x8100000000030000L,0x0000000000002004L,0x0000000000002005L,0x0000000000002006L,0x8100000000020000L,0x0000000000002008L);
    NonvolatileBits nHeld = ContextConstructorData547.n(0x8100000000020118L,0x0000000000000000L,0x8100000000030000L,0x0000000000002004L,0x0000000000002005L,0x0000000000002006L,0x8100000000020000L,0x0000000000002008L);
    boolean df1_pre = false;

    ContextConstructor543Api.CallFrame frame1 = ContextConstructorData547.cf(0x373AD20L, 0x8895D0L, v1_pre, n1_pre, df1_pre);

    VolatileBits v1_post = ContextConstructorData547.v(0xA000L, 0xA100000000000001L, 0xA200000000000002L, 0xA300000000000003L);

    FullCopy437Api.CallResult res1 = ContextConstructorData547.result(v1_post, n1_pre, M + 0x373AD25L, bodySP, true);

    List<ContextConstructorData547.Write> effects1 = List.of(
        ContextConstructorData547.w128(S, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L),
        ContextConstructorData547.w(4, S + 0x10, 0x80000001L)
    );

    steps.add(ContextConstructorData547.w(8, childSP, M + 0x373AD25L));
    steps.add(new ContextConstructorData547.Invoke(frame1, res1, effects1));
    steps.addAll(effects1);

    steps.add(ContextConstructorData547.w(8, D + 0x100, 0L));
    steps.add(ContextConstructorData547.w(8, D + 0x108, 0L));
    steps.add(ContextConstructorData547.w(8, D + 0x110, M + 0x54DE270L));

    steps.add(ContextConstructorData547.w(8, D + 0x118, M + 0x448D1F8L));

    steps.add(ContextConstructorData547.w(8, D + 0x120, M + 0x448D268L));

    steps.add(ContextConstructorData547.w(8, D + 0x128, 0L));
    steps.add(ContextConstructorData547.w(8, D + 0x130, 0L));

    steps.add(ContextConstructorData547.w(8, D + 0x138, M + 0x54DE278L));

    steps.add(ContextConstructorData547.w(4, D + 0x140, 0L));
    steps.add(ContextConstructorData547.w(8, D + 0x148, 0L));
    steps.add(ContextConstructorData547.w(8, D + 0x150, 0L));

    steps.add(ContextConstructorData547.w(8, D + 0x158, M + 0x54DE270L));

    steps.add(ContextConstructorData547.w(4, D + 0x160, 0xFFFFFFFFL));

    steps.add(ContextConstructorData547.w(2, D + 0x164, 0L));

    steps.add(ContextConstructorData547.w(1, D + 0x166, 0L));

    steps.add(ContextConstructorData547.r128(S, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));
    steps.add(ContextConstructorData547.w128(D, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L));

    steps.add(ContextConstructorData547.r(4, S + 0x10, 0x80000001L));
    steps.add(ContextConstructorData547.w(4, D + 0x10, 0x80000001L));

    VolatileBits v2_pre = new VolatileBits(0x0000000080000001L,0x8100000000020100L,0x8100000000030100L,0x000000000000A008L,0x000000000000A009L,0x000000000000A00AL,0x000000000000A00BL,new Bits128(0x0706050403020100L,0x0F0E0D0C0B0A0908L),new Bits128(0x000000000000A020L,0xFFFFFFFFFFFF5FDFL),new Bits128(0x000000000000A030L,0xFFFFFFFFFFFF5FCFL),new Bits128(0x000000000000A040L,0xFFFFFFFFFFFF5FBFL),new Bits128(0x000000000000A050L,0xFFFFFFFFFFFF5FAFL),new Bits128(0x000000000000A060L,0xFFFFFFFFFFFF5F9FL));
    ContextConstructor543Api.CallFrame frame2 = ContextConstructorData547.cf(0x373ADA1L, 0x37282B0L, v2_pre, nHeld, true);

    VolatileBits v2_post = ContextConstructorData547.v(0xB000L, 0xB100000000000001L, 0xB200000000000002L, 0xB300000000000003L);
    FullCopy437Api.CallResult res2 = ContextConstructorData547.result(v2_post, nHeld, M + 0x373ADA6L, bodySP, false);

    steps.add(ContextConstructorData547.w(8, childSP, M + 0x373ADA6L));
    steps.add(new ContextConstructorData547.Invoke(frame2, res2, List.of()));

    VolatileBits v3_pre = new VolatileBits(0xB100000000000001L,0x8100000000020018L,0x8100000000030018L,0x000000000000B008L,0x000000000000B009L,0x000000000000B00AL,0x000000000000B00BL,new Bits128(0x000000000000B010L,0xFFFFFFFFFFFF4FEFL),new Bits128(0x000000000000B020L,0xFFFFFFFFFFFF4FDFL),new Bits128(0x000000000000B030L,0xFFFFFFFFFFFF4FCFL),new Bits128(0x000000000000B040L,0xFFFFFFFFFFFF4FBFL),new Bits128(0x000000000000B050L,0xFFFFFFFFFFFF4FAFL),new Bits128(0x000000000000B060L,0xFFFFFFFFFFFF4F9FL));
    ContextConstructor543Api.CallFrame frame3 = ContextConstructorData547.cf(0x373ADAEL, 0x260E040L, v3_pre, nHeld, false);

    VolatileBits v3_post = ContextConstructorData547.v(0xC000L, 0xC100000000000001L, 0xC200000000000002L, 0xC300000000000003L);
    FullCopy437Api.CallResult res3 = ContextConstructorData547.result(v3_post, nHeld, M + 0x373ADB3L, bodySP, true);

    steps.add(ContextConstructorData547.w(8, childSP, M + 0x373ADB3L));
    steps.add(new ContextConstructorData547.Invoke(frame3, res3, List.of()));

    VolatileBits v4_pre = new VolatileBits(0xC100000000000001L,0x8100000000020118L,0x8100000000030118L,0x000000000000C008L,0x000000000000C009L,0x000000000000C00AL,0x000000000000C00BL,new Bits128(0x000000000000C010L,0xFFFFFFFFFFFF3FEFL),new Bits128(0x000000000000C020L,0xFFFFFFFFFFFF3FDFL),new Bits128(0x000000000000C030L,0xFFFFFFFFFFFF3FCFL),new Bits128(0x000000000000C040L,0xFFFFFFFFFFFF3FBFL),new Bits128(0x000000000000C050L,0xFFFFFFFFFFFF3FAFL),new Bits128(0x000000000000C060L,0xFFFFFFFFFFFF3F9FL));
    ContextConstructor543Api.CallFrame frame4 = ContextConstructorData547.cf(0x373ADBDL, 0x3727180L, v4_pre, nHeld, true);

    VolatileBits v4_post = ContextConstructorData547.v(0xD000L, 0xD100000000000001L, 0xD200000000000002L, 0xD300000000000003L);
    FullCopy437Api.CallResult res4 = ContextConstructorData547.result(v4_post, nHeld, M + 0x373ADC2L, bodySP, false);

    steps.add(ContextConstructorData547.w(8, childSP, M + 0x373ADC2L));
    steps.add(new ContextConstructorData547.Invoke(frame4, res4, List.of()));
    steps.add(ContextConstructorData547.r(8, E + 0x10, 0x2001L));
    steps.add(ContextConstructorData547.r(8, E + 0x18, 0x2002L));
    steps.add(ContextConstructorData547.r(8, E - 0x18, 0x2007L));
    steps.add(ContextConstructorData547.r(8, E - 0x10, 0x2004L));
    steps.add(ContextConstructorData547.r(8, E - 0x08, 0x2003L));
    steps.add(ContextConstructorData547.r(8, E, RET));


    VolatileBits finalV = new VolatileBits(
        D, v4_post.rcxBits(), v4_post.rdxBits(), v4_post.r8Bits(), v4_post.r9Bits(), v4_post.r10Bits(), v4_post.r11Bits(),
        v4_post.xmm0(), v4_post.xmm1(), v4_post.xmm2(), v4_post.xmm3(), v4_post.xmm4(), v4_post.xmm5()
    );

    NonvolatileBits finalN = new NonvolatileBits(
        0x2001L, 0x2002L, 0x2003L, 0x2004L, n1_pre.r12Bits(), n1_pre.r13Bits(), 0x2007L, n1_pre.r15Bits(), n1_pre.xmm6()
    );

    FullCopy437Api.CallResult finalResult = new FullCopy437Api.CallResult(
        new GovernmentCrtBoundary185Api.NormalReturn(finalV, RET, E + 8, finalN),
        false
    );

    List<ContextConstructorData547.Cell> finalMemory = List.of(
        ContextConstructorData547.c(8, E, RET),

        ContextConstructorData547.c(8, E + 0x10, 0x2001L),
        ContextConstructorData547.c(8, E + 0x18, 0x2002L),
        ContextConstructorData547.c(8, E + 0x08, D),
        ContextConstructorData547.c(8, E - 0x08, 0x2003L),
        ContextConstructorData547.c(8, E - 0x10, 0x2004L),
        ContextConstructorData547.c(8, E - 0x18, 0x2007L),

        ContextConstructorData547.c128(D, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L),
        ContextConstructorData547.c(4, D + 0x10, 0x80000001L),
        ContextConstructorData547.c(8, D + 0x100, 0L),
        ContextConstructorData547.c(8, D + 0x108, 0L),
        ContextConstructorData547.c(8, D + 0x110, M + 0x54DE270L),
        ContextConstructorData547.c(8, D + 0x118, M + 0x448D1F8L),
        ContextConstructorData547.c(8, D + 0x120, M + 0x448D268L),
        ContextConstructorData547.c(8, D + 0x128, 0L),
        ContextConstructorData547.c(8, D + 0x130, 0L),
        ContextConstructorData547.c(8, D + 0x138, M + 0x54DE278L),
        ContextConstructorData547.c(4, D + 0x140, 0L),
        ContextConstructorData547.c(8, D + 0x148, 0L),
        ContextConstructorData547.c(8, D + 0x150, 0L),
        ContextConstructorData547.c(8, D + 0x158, M + 0x54DE270L),
        ContextConstructorData547.c(4, D + 0x160, 0xFFFFFFFFL),
        ContextConstructorData547.c(2, D + 0x164, 0L),
        ContextConstructorData547.c(1, D + 0x166, 0L),

        ContextConstructorData547.c128(S, 0x0706050403020100L, 0x0F0E0D0C0B0A0908L),
        ContextConstructorData547.c(4, S + 0x10, 0x80000001L)
    );

    return new ContextConstructorData547.Scene(
        "normal",
        entry,
        initialDF,
        initialMemory,
        steps,
        finalResult,
        finalMemory
    );
}


public static ContextConstructorData547.Scene aliasScene() {
    long M = ContextConstructorData547.M;
    long E = ContextConstructorData547.E;
    long D = ContextConstructorData547.D;
    long RET = ContextConstructorData547.RET;
    long RET2 = ContextConstructorData547.RET2;
    long RESTORED_BX = ContextConstructorData547.RESTORED_BX;

    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(M, E, v0(D), n0());
    boolean df = false;

    List<Cell> initialMemory = List.of(
        c(8, E, RET),
        c128(D, 0x8877665544332211L, 0xFFEEDDCCBBAA9988L),
        c(4, D + 0x10, 0xFFABCDE0L)
    );

    List<Step> steps = new ArrayList<>();

    // Prologue writes
    steps.add(w(8, E + 0x10, 0x2001L));
    steps.add(w(8, E + 0x18, 0x2002L));
    steps.add(w(8, E + 0x8, D));
    steps.add(w(8, E - 0x8, 0x2003L));
    steps.add(w(8, E - 0x10, 0x2004L));
    steps.add(w(8, E - 0x18, 0x2007L));

    // Before Call 1
    steps.add(w(4, D, 0L));
    steps.add(w(8, D + 0x8, 0L));
    steps.add(w(4, D + 0x10, 0xFFFFFFFFL));
    steps.add(w(8, E - 0x40, M + 0x373AD25L));

    // Invoke 1
    NonvolatileBits N1 = n(0x2001L, 0L, D, 0x2004L, 0x2005L, 0x2006L, D, 0x2008L);
    VolatileBits beforeV1 = v(0x1000L, 0x8877665544332211L, D + 0x18L, D);
    VolatileBits postV1 = v(0xA000L, 0xA100000000000001L, 0xA200000000000002L, 0xA300000000000003L);
    CallFrame frame1 = cf(0x373AD20L, 0x8895D0L, beforeV1, N1, false);
    CallResult result1 = result(postV1, N1, M + 0x373AD25L, E - 0x38L, true);
    steps.add(new Invoke(frame1, result1, List.of()));

    // After Call 1 / Before Call 2
    steps.add(w(8, D + 0x100, 0L));
    steps.add(w(8, D + 0x108, 0L));
    steps.add(w(8, D + 0x110, M + 0x54DE270L));
    steps.add(w(8, D + 0x118, M + 0x448D1F8L));
    steps.add(w(8, D + 0x120, M + 0x448D268L));
    steps.add(w(8, D + 0x128, 0L));
    steps.add(w(8, D + 0x130, 0L));
    steps.add(w(8, D + 0x138, M + 0x54DE278L));
    steps.add(w(4, D + 0x140, 0L));
    steps.add(w(8, D + 0x148, 0L));
    steps.add(w(8, D + 0x150, 0L));
    steps.add(w(8, D + 0x158, M + 0x54DE270L));
    steps.add(w(4, D + 0x160, 0xFFFFFFFFL));
    steps.add(w(2, D + 0x164, 0L));
    steps.add(w(1, D + 0x166, 0L));

    steps.add(r128(D, 0x8877665500000000L, 0L));
    steps.add(w128(D, 0x8877665500000000L, 0L));
    steps.add(r(4, D + 0x10, 0xFFFFFFFFL));
    steps.add(w(4, D + 0x10, 0xFFFFFFFFL));
    steps.add(w(8, E - 0x40, M + 0x373ADA6L));

    // Invoke 2
    NonvolatileBits NN = n(D + 0x118L, 0L, D, 0x2004L, 0x2005L, 0x2006L, D, 0x2008L);
    VolatileBits beforeV2 = new VolatileBits(0xFFFFFFFFL, D + 0x100L, D + 0x100L, 0xA008L, 0xA009L, 0xA00AL, 0xA00BL, new Bits128(0x8877665500000000L, 0L), x(0xA020L), x(0xA030L), x(0xA040L), x(0xA050L), x(0xA060L));
    VolatileBits postV2 = v(0xB000L, 0xB100000000000001L, 0xB200000000000002L, 0xB300000000000003L);
    CallFrame frame2 = cf(0x373ADA1L, 0x37282B0L, beforeV2, NN, true);
    CallResult result2 = result(postV2, NN, M + 0x373ADA6L, E - 0x38L, false);
    steps.add(new Invoke(frame2, result2, List.of()));

    // Before Call 3
    steps.add(w(8, E - 0x40, M + 0x373ADB3L));

    // Invoke 3
    VolatileBits beforeV3 = v(0xB000L, 0xB100000000000001L, D + 0x18L, D + 0x18L);
    VolatileBits postV3 = v(0xC000L, 0xC100000000000001L, 0xC200000000000002L, 0xC300000000000003L);
    CallFrame frame3 = cf(0x373ADAEL, 0x260E040L, beforeV3, NN, false);
    CallResult result3 = result(postV3, NN, M + 0x373ADB3L, E - 0x38L, true);
    steps.add(new Invoke(frame3, result3, List.of()));

    // Before Call 4
    steps.add(w(8, E - 0x40, M + 0x373ADC2L));

    // Invoke 4
    VolatileBits beforeV4 = v(0xC000L, 0xC100000000000001L, D + 0x118L, D + 0x118L);
    VolatileBits postV4 = v(0xD000L, 0xD100000000000001L, 0xD200000000000002L, 0xD300000000000003L);
    CallFrame frame4 = cf(0x373ADBDL, 0x3727180L, beforeV4, NN, true);
    CallResult result4 = result(postV4, NN, M + 0x373ADC2L, E - 0x38L, false);
    List<Write> effects4 = List.of(w(8, E + 0x10, RESTORED_BX), w(8, E, RET2));
    steps.add(new Invoke(frame4, result4, effects4));

    // Epilogue / Tail
    steps.add(w(8, E + 0x10, RESTORED_BX));
    steps.add(w(8, E, RET2));
    steps.add(r(8, E + 0x10, RESTORED_BX));
    steps.add(r(8, E + 0x18, 0x2002L));
    steps.add(r(8, E - 0x18, 0x2007L));
    steps.add(r(8, E - 0x10, 0x2004L));
    steps.add(r(8, E - 0x8, 0x2003L));
    steps.add(r(8, E, RET2));

    VolatileBits finalV = v(0xD000L, D, 0xD200000000000002L, 0xD300000000000003L);
    NonvolatileBits finalN = n(RESTORED_BX, 0x2002L, 0x2003L, 0x2004L, 0x2005L, 0x2006L, 0x2007L, 0x2008L);
    CallResult expectedResult = result(finalV, finalN, RET2, E + 0x8L, false);

    List<Cell> finalMemory = List.of(
        c128(D, 0x8877665500000000L, 0L),
        c(4, D + 0x10, 0xFFFFFFFFL),
        c(8, D + 0x100, 0L),
        c(8, D + 0x108, 0L),
        c(8, D + 0x110, M + 0x54DE270L),
        c(8, D + 0x118, M + 0x448D1F8L),
        c(8, D + 0x120, M + 0x448D268L),
        c(8, D + 0x128, 0L),
        c(8, D + 0x130, 0L),
        c(8, D + 0x138, M + 0x54DE278L),
        c(4, D + 0x140, 0L),
        c(8, D + 0x148, 0L),
        c(8, D + 0x150, 0L),
        c(8, D + 0x158, M + 0x54DE270L),
        c(4, D + 0x160, 0xFFFFFFFFL),
        c(2, D + 0x164, 0L),
        c(1, D + 0x166, 0L),
        c(8, E + 0x10, RESTORED_BX),
        c(8, E + 0x18, 0x2002L),
        c(8, E + 0x8, D),
        c(8, E - 0x8, 0x2003L),
        c(8, E - 0x10, 0x2004L),
        c(8, E - 0x18, 0x2007L),
        c(8, E - 0x40, M + 0x373ADC2L),
        c(8, E, RET2)
    );

    return new Scene("ALIAS_RET", entry, df, initialMemory, steps, expectedResult, finalMemory);
}

 public static List<ContextConstructorData547.Scene> scenes() { return List.of(normalScene(),aliasScene()); }
 public static int verify() { List<ContextConstructorData547.Scene> scenes=scenes(); for(ContextConstructorData547.Scene scene:scenes) ContextConstructorHost547.verify(scene); return scenes.size(); }
 public static void main(String[] args) { System.out.println(verify()); }
}
