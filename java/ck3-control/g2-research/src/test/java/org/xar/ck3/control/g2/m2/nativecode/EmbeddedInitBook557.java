package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.EmbeddedInitData557.*;
/** Complete separately source-frozen methods joined without changing expectations. */
public final class EmbeddedInitBook557 {
 private EmbeddedInitBook557() { }
public static EmbeddedInitData557.Scene normalScene() {
    long M = EmbeddedInitData557.M;
    long E = EmbeddedInitData557.E;
    long D = EmbeddedInitData557.D;
    long VT2 = EmbeddedInitData557.VT2;
    long TARGET1 = EmbeddedInitData557.TARGET1;
    long TARGET2 = EmbeddedInitData557.TARGET2;
    long RET = EmbeddedInitData557.RET;

    List<EmbeddedInitData557.Cell> initialMemory = new ArrayList<>();
    initialMemory.add(EmbeddedInitData557.c(8, E, RET));
    initialMemory.add(EmbeddedInitData557.c(8, M + 0x448D2A0L + 0x10L, TARGET1));
    initialMemory.add(EmbeddedInitData557.c(8, VT2 + 0x20L, TARGET2));

    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
        M, E, EmbeddedInitData557.v0(), EmbeddedInitData557.n0()
    );
    boolean initialDF = true;

    List<EmbeddedInitData557.Step> steps = new ArrayList<>();

    steps.add(EmbeddedInitData557.w(8, E + 8, EmbeddedInitData557.n0().rbxBits()));

    steps.add(EmbeddedInitData557.w(8, E + 0x10, EmbeddedInitData557.n0().rbpBits()));

    steps.add(EmbeddedInitData557.w(8, E + 0x18, EmbeddedInitData557.n0().rsiBits()));

    steps.add(EmbeddedInitData557.w(8, E - 8, EmbeddedInitData557.n0().rdiBits()));

    steps.add(EmbeddedInitData557.w(8, D, 0L));

    steps.add(EmbeddedInitData557.w(4, D + 8, 0));

    steps.add(EmbeddedInitData557.w(8, D + 0x10, D + 0x18));

    steps.add(EmbeddedInitData557.w(8, D + 0x18, M + 0x448D2A0L));

    steps.add(EmbeddedInitData557.w(8, D + 0x18 + 0xc8, M + 0x54DE2E0L));

    steps.add(EmbeddedInitData557.r(8, D, 0L));

    steps.add(EmbeddedInitData557.w(4, D + 0xc, 0));

    steps.add(EmbeddedInitData557.r(8, D + 0x10, D + 0x18));

    steps.add(EmbeddedInitData557.r(8, D + 0x18, M + 0x448D2A0L));

    steps.add(EmbeddedInitData557.r(8, M + 0x448D2A0L + 0x10L, TARGET1));

    VolatileBits v1 = new VolatileBits(
        M + 0x448D2A0L, D + 0x18, 0L, 8L,
        EmbeddedInitData557.v0().r9Bits(), EmbeddedInitData557.v0().r10Bits(), EmbeddedInitData557.v0().r11Bits(),
        EmbeddedInitData557.v0().xmm0(), EmbeddedInitData557.v0().xmm1(), EmbeddedInitData557.v0().xmm2(),
        EmbeddedInitData557.v0().xmm3(), EmbeddedInitData557.v0().xmm4(), EmbeddedInitData557.v0().xmm5()
    );
    NonvolatileBits n1 = new NonvolatileBits(
        D + 0x18, 0L, D, EmbeddedInitData557.n0().rdiBits(),
        EmbeddedInitData557.n0().r12Bits(), EmbeddedInitData557.n0().r13Bits(), EmbeddedInitData557.n0().r14Bits(), EmbeddedInitData557.n0().r15Bits(),
        EmbeddedInitData557.n0().xmm6()
    );

    EmbeddedInit550Api.CallFrame frame1 = EmbeddedInitData557.cf(0x889620L, TARGET1, v1, n1, true);

    steps.add(EmbeddedInitData557.w(8, E - 0x30, M + 0x889623L));
    VolatileBits postV1 = EmbeddedInitData557.v(0x5000, 0x5100000000000001L, 0x5200000000000002L, 0x5300000000000003L);
    FullCopy437Api.CallResult res1 = EmbeddedInitData557.result(postV1, n1, M + 0x889623L, E - 0x28L, false);

    steps.add(new EmbeddedInitData557.Invoke(frame1, res1, List.of(EmbeddedInitData557.w(8, D + 0x18, VT2))));

    steps.add(EmbeddedInitData557.w(8, D + 0x18, VT2));

    steps.add(EmbeddedInitData557.r(8, D + 0x18, VT2));

    steps.add(EmbeddedInitData557.w(8, D, 0L));

    steps.add(EmbeddedInitData557.w(8, D + 8, 0L));

    steps.add(EmbeddedInitData557.r(8, VT2 + 0x20L, TARGET2));

    VolatileBits v2 = new VolatileBits(
        VT2, D + 0x18, D, D + 8,
        postV1.r9Bits(), postV1.r10Bits(), postV1.r11Bits(),
        postV1.xmm0(), postV1.xmm1(), postV1.xmm2(),
        postV1.xmm3(), postV1.xmm4(), postV1.xmm5()
    );

    NonvolatileBits n2 = new NonvolatileBits(
        D + 0x18, 0L, D, EmbeddedInitData557.n0().rdiBits(),
        EmbeddedInitData557.n0().r12Bits(), EmbeddedInitData557.n0().r13Bits(), EmbeddedInitData557.n0().r14Bits(), EmbeddedInitData557.n0().r15Bits(),
        EmbeddedInitData557.n0().xmm6()
    );

    EmbeddedInit550Api.CallFrame frame2 = EmbeddedInitData557.cf(0x889637L, TARGET2, v2, n2, false);

    steps.add(EmbeddedInitData557.w(8, E - 0x30, M + 0x88963AL));
    VolatileBits postV2 = EmbeddedInitData557.v(0x6000, 0x6100000000000001L, 0x6200000000000002L, 0x6300000000000003L);
    FullCopy437Api.CallResult res2 = EmbeddedInitData557.result(postV2, n2, M + 0x88963AL, E - 0x28L, true);

    steps.add(new EmbeddedInitData557.Invoke(frame2, res2, List.of()));

    steps.add(EmbeddedInitData557.r(8, E + 8, EmbeddedInitData557.n0().rbxBits()));

    steps.add(EmbeddedInitData557.r(8, E + 0x18, EmbeddedInitData557.n0().rsiBits()));

    steps.add(EmbeddedInitData557.r(8, E + 0x10, EmbeddedInitData557.n0().rbpBits()));

    steps.add(EmbeddedInitData557.r(8, E - 8, EmbeddedInitData557.n0().rdiBits()));

    steps.add(EmbeddedInitData557.r(8, E, RET));

    List<EmbeddedInitData557.Cell> finalMemory = new ArrayList<>();
    finalMemory.add(EmbeddedInitData557.c(8, E, RET));
    finalMemory.add(EmbeddedInitData557.c(8, D, 0L));
    finalMemory.add(EmbeddedInitData557.c(8, D + 8, 0L));
    finalMemory.add(EmbeddedInitData557.c(8, D + 0x10, D + 0x18));
    finalMemory.add(EmbeddedInitData557.c(8, D + 0x18, VT2));
    finalMemory.add(EmbeddedInitData557.c(8, D + 0x18 + 0xc8, M + 0x54DE2E0L));
    finalMemory.add(EmbeddedInitData557.c(8, E + 8, EmbeddedInitData557.n0().rbxBits()));
    finalMemory.add(EmbeddedInitData557.c(8, E + 0x10, EmbeddedInitData557.n0().rbpBits()));
    finalMemory.add(EmbeddedInitData557.c(8, E + 0x18, EmbeddedInitData557.n0().rsiBits()));
    finalMemory.add(EmbeddedInitData557.c(8, E - 8, EmbeddedInitData557.n0().rdiBits()));

    VolatileBits finalV = new VolatileBits(
        D, postV2.rcxBits(), postV2.rdxBits(), postV2.r8Bits(),
        postV2.r9Bits(), postV2.r10Bits(), postV2.r11Bits(),
        postV2.xmm0(), postV2.xmm1(), postV2.xmm2(),
        postV2.xmm3(), postV2.xmm4(), postV2.xmm5()
    );
    NonvolatileBits finalN = new NonvolatileBits(
        EmbeddedInitData557.n0().rbxBits(), EmbeddedInitData557.n0().rbpBits(), EmbeddedInitData557.n0().rsiBits(), EmbeddedInitData557.n0().rdiBits(),
        EmbeddedInitData557.n0().r12Bits(), EmbeddedInitData557.n0().r13Bits(), EmbeddedInitData557.n0().r14Bits(), EmbeddedInitData557.n0().r15Bits(),
        EmbeddedInitData557.n0().xmm6()
    );

    FullCopy437Api.CallResult expectedResult = EmbeddedInitData557.result(finalV, finalN, RET, E + 8, true);

    return new EmbeddedInitData557.Scene(
        "normal",
        entry,
        initialDF,
        initialMemory,
        steps,
        expectedResult,
        finalMemory
    );
}

public static EmbeddedInitData557.Scene aliasScene() {
    long M = EmbeddedInitData557.M;
    long E = EmbeddedInitData557.E;
    long D = EmbeddedInitData557.D;
    long RET = EmbeddedInitData557.RET;
    long RET2 = EmbeddedInitData557.RET2;
    long RESTORED_RSI = EmbeddedInitData557.RESTORED_RSI;
    long TARGET1 = EmbeddedInitData557.TARGET1;
    long ALIAS_VT = EmbeddedInitData557.ALIAS_VT;
    long ALIAS_VAL = 0x7FFF9999A1B2C3D4L;
    long CLEAR_VAL = 0x99AABBCCDDEEFF00L;
    long TARGET2 = 0x00000000A1B2C3D4L;

    List<Cell> initialMemory = new ArrayList<Cell>();
    initialMemory.add(c(8, E, RET));
    initialMemory.add(c(8, M + 0x448D2A0L + 0x10L, TARGET1));
    initialMemory.add(c(8, D - 4L, ALIAS_VAL));

    List<Step> steps = new ArrayList<Step>();

    steps.add(w(8, E + 8L, 0x2001L));
    steps.add(w(8, E + 0x10L, 0x2002L));
    steps.add(w(8, E + 0x18L, 0x2003L));
    steps.add(w(8, E - 8L, 0x2004L));
    steps.add(w(8, D, 0L));
    steps.add(w(4, D + 8L, 0L));
    steps.add(w(8, D + 0x10L, D + 0x18L));
    steps.add(w(8, D + 0x18L, M + 0x448D2A0L));
    steps.add(w(8, D + 0x18L + 0xC8L, M + 0x54DE2E0L));
    steps.add(r(8, D, 0L));
    steps.add(w(4, D + 0xC, 0L));
    steps.add(r(8, D + 0x10L, D + 0x18L));
    steps.add(r(8, D + 0x18L, M + 0x448D2A0L));
    steps.add(r(8, M + 0x448D2A0L + 0x10L, TARGET1));
    steps.add(w(8, E - 0x30L, M + 0x889623L));

    long body_rsp = E - 0x28L;
    long call_rsp = body_rsp - 8L;

    VolatileBits v1 = new VolatileBits(M + 0x448D2A0L, D + 0x18L, 0L, 8L, 0x1009L, 0x100AL, 0x100BL, x(0x1010L), x(0x1020L), x(0x1030L), x(0x1040L), x(0x1050L), x(0x1060L));
    NonvolatileBits n1 = n(D + 0x18L, 0L, D, 0x2004L, 0x2005L, 0x2006L, 0x2007L, 0x2008L);
    EmbeddedInit550Api.CallFrame f1 = new EmbeddedInit550Api.CallFrame(new GovernmentCrtBoundary185Api.Call(0x889620L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, TARGET1, body_rsp, v1, n1), new GovernmentCrtBoundary185Api.Entry(M, call_rsp, v1, n1), false, 3, M + 0x889623L);

    VolatileBits postV1 = new VolatileBits(0x5100000000000001L, 0x5200000000000002L, 0x5300000000000003L, 0x5008L, 0x5009L, 0x500AL, 0x500BL, x(0x5010L), x(0x5020L), x(0x5030L), x(0x5040L), x(0x5050L), x(0x5060L));
    FullCopy437Api.CallResult res1 = new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(postV1, M + 0x889623L, body_rsp, n1), true);

    List<Write> eff1 = new ArrayList<Write>();
    eff1.add(w(8, D + 0x18L, ALIAS_VT));
    eff1.add(w(8, D, CLEAR_VAL));
    steps.add(new Invoke(f1, res1, eff1));
    steps.add(w(8, D + 0x18L, ALIAS_VT));
    steps.add(w(8, D, CLEAR_VAL));

    steps.add(r(8, D + 0x18L, ALIAS_VT));
    steps.add(w(8, D, 0L));
    steps.add(w(8, D + 8L, 0L));
    steps.add(r(8, ALIAS_VT + 0x20L, TARGET2));
    steps.add(w(8, E - 0x30L, M + 0x88963AL));

    VolatileBits v2 = new VolatileBits(ALIAS_VT, D + 0x18L, D, D + 8L, 0x5009L, 0x500AL, 0x500BL, x(0x5010L), x(0x5020L), x(0x5030L), x(0x5040L), x(0x5050L), x(0x5060L));
    NonvolatileBits n2 = n(D + 0x18L, 0L, D, 0x2004L, 0x2005L, 0x2006L, 0x2007L, 0x2008L);
    EmbeddedInit550Api.CallFrame f2 = new EmbeddedInit550Api.CallFrame(new GovernmentCrtBoundary185Api.Call(0x889637L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, TARGET2, body_rsp, v2, n2), new GovernmentCrtBoundary185Api.Entry(M, call_rsp, v2, n2), true, 3, M + 0x88963AL);

    VolatileBits postV2 = new VolatileBits(0x6100000000000001L, 0x6200000000000002L, 0x6300000000000003L, 0x6008L, 0x6009L, 0x600AL, 0x600BL, x(0x6010L), x(0x6020L), x(0x6030L), x(0x6040L), x(0x6050L), x(0x6060L));
    FullCopy437Api.CallResult res2 = new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(postV2, M + 0x88963AL, body_rsp, n2), false);

    List<Write> eff2 = new ArrayList<Write>();
    eff2.add(w(8, E + 0x18L, RESTORED_RSI));
    eff2.add(w(8, E, RET2));
    steps.add(new Invoke(f2, res2, eff2));
    steps.add(w(8, E + 0x18L, RESTORED_RSI));
    steps.add(w(8, E, RET2));

    steps.add(r(8, E + 8L, 0x2001L));
    steps.add(r(8, E + 0x18L, RESTORED_RSI));
    steps.add(r(8, E + 0x10L, 0x2002L));
    steps.add(r(8, E - 8L, 0x2004L));
    steps.add(r(8, E, RET2));

    List<Cell> finalMemory = new ArrayList<Cell>();
    finalMemory.add(c(8, E, RET2));
    finalMemory.add(c(8, E + 8L, 0x2001L));
    finalMemory.add(c(8, E + 0x10L, 0x2002L));
    finalMemory.add(c(8, E + 0x18L, RESTORED_RSI));
    finalMemory.add(c(8, E - 8L, 0x2004L));
    finalMemory.add(c(8, E - 0x30L, M + 0x88963AL));
    finalMemory.add(c(8, M + 0x448D2A0L + 0x10L, TARGET1));
    finalMemory.add(c(8, D - 4L, TARGET2));
    finalMemory.add(c(8, D, 0L));
    finalMemory.add(c(8, D + 8L, 0L));
    finalMemory.add(c(8, D + 0x10L, D + 0x18L));
    finalMemory.add(c(8, D + 0x18L, ALIAS_VT));
    finalMemory.add(c(8, D + 0x18L + 0xC8L, M + 0x54DE2E0L));

    GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(M, E, v0(), n0());
    return new Scene("ALIAS_TARGET_RET", entry, false, initialMemory, steps, result(v(0x6000L, D, 0x6200000000000002L, 0x6300000000000003L), n(0x2001L, 0x2002L, RESTORED_RSI, 0x2004L, 0x2005L, 0x2006L, 0x2007L, 0x2008L), RET2, E + 8L, false), finalMemory);
}
 public static List<Scene> scenes() { return List.of(normalScene(),aliasScene()); }
 public static int verify() {
  List<Scene> cases=scenes();
  if(cases.get(0).steps().size()!=28||cases.get(1).steps().size()!=31)throw new AssertionError("source trace counts");
  for(Scene scene:cases)EmbeddedInitHost557.verify(scene);
  return cases.size();
 }
 public static void main(String[] args) { System.out.println(verify()); }
}
