package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import java.util.ArrayList;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.ContextKnownData553.*;
/** Mechanically assembled complete separately source-frozen methods; parent owns assembly only. */
public final class ContextKnownBook553 {
 private ContextKnownBook553() { }
public static ContextKnownData553.Scene wholeContextScene() {
    List<Cell> initial = List.of(
        c(8, E, RET),
        c(8, S, 0xA1B2C3D4E5F6071L),
        c128(S+8, 0x1122334455667788L, 0x99AABBCCDDEEFF00L),
        c(4, S+0x18L, 0xFFABCDE0L),
        c128(S+0x170L, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L),
        c(4, S+0x180L, 0x80000001L),
        c(4, S+0x2E8L, 0xFFFFFFFFL)
    );
    NonvolatileBits held = n(0xFFFFFFFFFFFFFFFEL,0x0000000000002002L,0x0000000000002003L,0x8100000000060000L,0x0000000000002005L,0x0000000000002006L,0x8100000000050000L,0x8100000000040000L);
    VolatileBits offered1 = new VolatileBits(0x00000000FEEDC0DEL,0x8100000000040300L,0xFF00000000000003L,0x000000000000B008L,0x000000000000B009L,0x000000000000B00AL,0x000000000000B00BL,new Bits128(0x0011223344556677L,0x8899AABBCCDDEEFFL),new Bits128(0x000000000000B020L,0xFFFFFFFFFFFF4FDFL),new Bits128(0x000000000000B030L,0xFFFFFFFFFFFF4FCFL),new Bits128(0x000000000000B040L,0xFFFFFFFFFFFF4FBFL),new Bits128(0x000000000000B050L,0xFFFFFFFFFFFF4FAFL),new Bits128(0x000000000000B060L,0xFFFFFFFFFFFF4F9FL));
    FullContext493Api.CallFrame frame1 = contextFrame(0x0000000003076C1FL,0x000000000105D2D0L,offered1,held,false);
    FullCopy437Api.CallResult post1 = result(new VolatileBits(0x1100000000000001L,0x2200000000000002L,0x3300000000000003L,0x000000000000C008L,0x000000000000C009L,0x000000000000C00AL,0x000000000000C00BL,new Bits128(0x000000000000C010L,0xFFFFFFFFFFFF3FEFL),new Bits128(0x000000000000C020L,0xFFFFFFFFFFFF3FDFL),new Bits128(0x000000000000C030L,0xFFFFFFFFFFFF3FCFL),new Bits128(0x000000000000C040L,0xFFFFFFFFFFFF3FBFL),new Bits128(0x000000000000C050L,0xFFFFFFFFFFFF3FAFL),new Bits128(0x000000000000C060L,0xFFFFFFFFFFFF3F9FL)),held,0x0000003303076C24L,0x810000000000AFD0L,true);
    List<Write> effects1 = List.of(w(4,0x810000000004030CL,0x0000000080000001L),w(8,0x8100000000050300L,0x8100000000061000L),w(4,0x810000000005030CL,0x0000000000000007L));
    VolatileBits offered2 = new VolatileBits(0x1100000000000001L,0x8100000000040300L,0x0000000080000001L,0x8100000000060000L,0x810000000005FFFEL,0x000000000000C00AL,0x000000000000C00BL,new Bits128(0x000000000000C010L,0xFFFFFFFFFFFF3FEFL),new Bits128(0x000000000000C020L,0xFFFFFFFFFFFF3FDFL),new Bits128(0x000000000000C030L,0xFFFFFFFFFFFF3FCFL),new Bits128(0x000000000000C040L,0xFFFFFFFFFFFF3FBFL),new Bits128(0x000000000000C050L,0xFFFFFFFFFFFF3FAFL),new Bits128(0x000000000000C060L,0xFFFFFFFFFFFF3F9FL));
    FullContext493Api.CallFrame frame2 = contextFrame(0x0000000003076C39L,0x0000000000BCB7C0L,offered2,held,true);
    FullCopy437Api.CallResult post2 = result(new VolatileBits(0x4400000000000001L,0x5500000000000002L,0x6600000000000003L,0x000000000000D008L,0x000000000000D009L,0x000000000000D00AL,0x000000000000D00BL,new Bits128(0x000000000000D010L,0xFFFFFFFFFFFF2FEFL),new Bits128(0x000000000000D020L,0xFFFFFFFFFFFF2FDFL),new Bits128(0x000000000000D030L,0xFFFFFFFFFFFF2FCFL),new Bits128(0x000000000000D040L,0xFFFFFFFFFFFF2FBFL),new Bits128(0x000000000000D050L,0xFFFFFFFFFFFF2FAFL),new Bits128(0x000000000000D060L,0xFFFFFFFFFFFF2F9FL)),held,0x0000003303076C3EL,0x810000000000AFD0L,false);
    List<Write> effects2 = List.of();
    VolatileBits offered3 = new VolatileBits(0x4400000000000001L,0x8100000000040330L,0x8100000000050000L,0x000000000000D008L,0x000000000000D009L,0x000000000000D00AL,0x000000000000D00BL,new Bits128(0x000000000000D010L,0xFFFFFFFFFFFF2FEFL),new Bits128(0x000000000000D020L,0xFFFFFFFFFFFF2FDFL),new Bits128(0x000000000000D030L,0xFFFFFFFFFFFF2FCFL),new Bits128(0x000000000000D040L,0xFFFFFFFFFFFF2FBFL),new Bits128(0x000000000000D050L,0xFFFFFFFFFFFF2FAFL),new Bits128(0x000000000000D060L,0xFFFFFFFFFFFF2F9FL));
    FullContext493Api.CallFrame frame3 = contextFrame(0x0000000003076C49L,0x0000000002503880L,offered3,held,false);
    FullCopy437Api.CallResult post3 = result(new VolatileBits(0x7700000000000001L,0x8800000000000002L,0x9900000000000003L,0x000000000000E008L,0x000000000000E009L,0x000000000000E00AL,0x000000000000E00BL,new Bits128(0x000000000000E010L,0xFFFFFFFFFFFF1FEFL),new Bits128(0x000000000000E020L,0xFFFFFFFFFFFF1FDFL),new Bits128(0x000000000000E030L,0xFFFFFFFFFFFF1FCFL),new Bits128(0x000000000000E040L,0xFFFFFFFFFFFF1FBFL),new Bits128(0x000000000000E050L,0xFFFFFFFFFFFF1FAFL),new Bits128(0x000000000000E060L,0xFFFFFFFFFFFF1F9FL)),held,0x0000003303076C4EL,0x810000000000AFD0L,true);
    List<Write> effects3 = List.of(w(4,0x81000000000502E8L,0x0000000000000000L));
    List<Step> steps = new ArrayList<>();
    steps.add(w(8,0x810000000000B018L,0x0000000000002001L));
    steps.add(w(8,0x810000000000B020L,0x0000000000002003L));
    steps.add(w(8,0x810000000000B010L,0x8100000000040000L));
    steps.add(w(8,0x810000000000B000L,0x0000000000002004L));
    steps.add(w(8,0x810000000000AFF8L,0x0000000000002007L));
    steps.add(w(8,0x810000000000AFF0L,0x0000000000002008L));
    steps.add(r(8,0x8100000000050000L,0x0A1B2C3D4E5F6071L));
    steps.add(w(8,0x8100000000040000L,0x0A1B2C3D4E5F6071L));
    steps.add(w(8,0x810000000000AFC8L,0x0000003303076B91L));
    appendFirstConstructorScript(steps);
    steps.add(w(8,0x810000000000AFC8L,0x0000003303076BA5L));
    appendSecondConstructorScript(steps);
    steps.add(r(4,0x81000000000502D8L,0x0000000080000001L));
    steps.add(w(4,0x81000000000402D8L,0x0000000080000001L));
    steps.add(r(4,0x81000000000502DCL,0x00000000FFFFFFFFL));
    steps.add(w(4,0x81000000000402DCL,0x00000000FFFFFFFFL));
    steps.add(r(4,0x81000000000502E0L,0x00000000AABBCCDDL));
    steps.add(w(4,0x81000000000402E0L,0x00000000AABBCCDDL));
    steps.add(r(4,0x81000000000502E4L,0x0000000001234567L));
    steps.add(w(4,0x81000000000402E4L,0x0000000001234567L));
    steps.add(r(4,0x81000000000502E8L,0x0000000089ABCDEFL));
    steps.add(w(4,0x81000000000402E8L,0x0000000089ABCDEFL));
    steps.add(r(4,0x81000000000502ECL,0x00000000FEEDC0DEL));
    steps.add(w(4,0x81000000000402ECL,0x00000000FEEDC0DEL));
    steps.add(r128(0x81000000000502F0L,0x0011223344556677L,0x8899AABBCCDDEEFFL));
    steps.add(w128(0x81000000000402F0L,0x0011223344556677L,0x8899AABBCCDDEEFFL));
    steps.add(r(4,0x810000000005030CL,0x00000000FFFFFFFEL));
    steps.add(r(8,0x8100000000050300L,0x8100000000060000L));
    steps.add(w(8,0x810000000000AFC8L,0x0000003303076C24L));
    steps.add(new ContextInvoke(frame1,post1,effects1));
    steps.add(w(4,0x810000000004030CL,0x0000000080000001L));
    steps.add(w(8,0x8100000000050300L,0x8100000000061000L));
    steps.add(w(4,0x810000000005030CL,0x0000000000000007L));
    steps.add(r(4,0x810000000004030CL,0x0000000080000001L));
    steps.add(w(8,0x810000000000AFC8L,0x0000003303076C3EL));
    steps.add(new ContextInvoke(frame2,post2,effects2));
    steps.add(w(8,0x810000000000AFC8L,0x0000003303076C4EL));
    steps.add(new ContextInvoke(frame3,post3,effects3));
    steps.add(w(4,0x81000000000502E8L,0x0000000000000000L));
    steps.add(r(8, E+0x10, 0x2001L));
    steps.add(r(8, E+0x18, 0x2003L));
    steps.add(r(8, E-0x18, 0x2008L));
    steps.add(r(8, E-0x10, 0x2007L));
    steps.add(r(8, E-0x08, 0x2004L));
    steps.add(r(8, E, RET));
    List<Cell> finalMemory = List.of(
        c(8,0x8100000000040000L,0x0A1B2C3D4E5F6071L),
        c128(0x8100000000040008L,0x1122334455667788L,0x99AABBCCDDEEFF00L),
        c(4,0x8100000000040018L,0x00000000FFABCDE0L),
        c128(0x8100000000040170L,0x0123456789ABCDEFL,0xFEDCBA9876543210L),
        c(4,0x8100000000040180L,0x0000000080000001L),
        c(4,0x81000000000402D8L,0x0000000080000001L),
        c(4,0x81000000000402DCL,0x00000000FFFFFFFFL),
        c(4,0x81000000000402E0L,0x00000000AABBCCDDL),
        c(4,0x81000000000402E4L,0x0000000001234567L),
        c(4,0x81000000000402E8L,0x0000000089ABCDEFL),
        c(4,0x81000000000402ECL,0x00000000FEEDC0DEL),
        c128(0x81000000000402F0L,0x0011223344556677L,0x8899AABBCCDDEEFFL),
        c(4,0x810000000004030CL,0x0000000080000001L),
        c(8,0x8100000000050300L,0x8100000000061000L),
        c(4,0x810000000005030CL,0x0000000000000007L),
        c(4,0x81000000000502E8L,0x0000000000000000L),
        c(8,0x810000000000B018L,0x0000000000002001L),
        c(8,0x810000000000B020L,0x0000000000002003L),
        c(8,0x810000000000B010L,0x8100000000040000L),
        c(8,0x810000000000B008L,0xAABBCCDD11223344L),
        c(8,0x8100000000040108L,0x0000000000000000L),
        c(8,0x8100000000040110L,0x0000000000000000L),
        c(8,0x8100000000040118L,0x00000033054DE270L),
        c(8,0x8100000000040120L,0x000000330448D1F8L),
        c(8,0x8100000000040128L,0x000000330448D268L),
        c(8,0x8100000000040130L,0x0000000000000000L),
        c(8,0x8100000000040138L,0x0000000000000000L),
        c(8,0x8100000000040140L,0x00000033054DE278L),
        c(4,0x8100000000040148L,0x0000000000000000L),
        c(8,0x8100000000040150L,0x0000000000000000L),
        c(8,0x8100000000040158L,0x0000000000000000L),
        c(8,0x8100000000040160L,0x00000033054DE270L),
        c(4,0x8100000000040168L,0x00000000FFFFFFFFL),
        c(2,0x810000000004016CL,0x0000000000000000L),
        c(1,0x810000000004016EL,0x0000000000000000L),
        c(8,0x8100000000040270L,0x0000000000000000L),
        c(8,0x8100000000040278L,0x0000000000000000L),
        c(8,0x8100000000040280L,0x00000033054DE270L),
        c(8,0x8100000000040288L,0x000000330448D1F8L),
        c(8,0x8100000000040290L,0x000000330448D268L),
        c(8,0x8100000000040298L,0x0000000000000000L),
        c(8,0x81000000000402A0L,0x0000000000000000L),
        c(8,0x81000000000402A8L,0x00000033054DE278L),
        c(4,0x81000000000402B0L,0x0000000000000000L),
        c(8,0x81000000000402B8L,0x0000000000000000L),
        c(8,0x81000000000402C0L,0x0000000000000000L),
        c(8,0x81000000000402C8L,0x00000033054DE270L),
        c(4,0x81000000000402D0L,0x00000000FFFFFFFFL),
        c(2,0x81000000000402D4L,0x0000000000000000L),
        c(1,0x81000000000402D6L,0x0000000000000000L)
    );
    FullCopy437Api.CallResult expected = result(new VolatileBits(0x8100000000040000L,0x8800000000000002L,0x9900000000000003L,0x000000000000E008L,0x000000000000E009L,0x000000000000E00AL,0x000000000000E00BL,new Bits128(0x000000000000E010L,0xFFFFFFFFFFFF1FEFL),new Bits128(0x000000000000E020L,0xFFFFFFFFFFFF1FDFL),new Bits128(0x000000000000E030L,0xFFFFFFFFFFFF1FCFL),new Bits128(0x000000000000E040L,0xFFFFFFFFFFFF1FBFL),new Bits128(0x000000000000E050L,0xFFFFFFFFFFFF1FAFL),new Bits128(0x000000000000E060L,0xFFFFFFFFFFFF1F9FL)),n0(),RET,E+8,true);
    return new Scene("wholeContext",new Entry(M,E,v0(),n0()),false,initial,steps,expected,finalMemory);
}

public static void appendFirstConstructorScript(java.util.List<ContextKnownData553.Step> steps) {
    long E = 0x810000000000B008L;
    long childE = E - 0x40L;
    long bodySP = 0x810000000000AF90L;
    long childSP = 0x810000000000AF88L;
    long D = 0x8100000000040000L;
    long S = 0x8100000000050000L;
    long M = 0x3300000000L;

    // Prologue: Save registers and push
    steps.add(w(8, childE + 0x10, 0x2001L)); // 373ACF0 save RBX
    steps.add(w(8, childE + 0x18, 0x2002L)); // 373ACF5 save RBP
    steps.add(w(8, childE + 0x08, D + 0x08)); // 373ACFA save RCX (D+8)
    steps.add(w(8, childE - 0x08, 0x2003L)); // 373ACFF PUSH RSI
    steps.add(w(8, childE - 0x10, 0x2004L)); // 373AD00 PUSH RDI
    steps.add(w(8, childE - 0x18, S)); // 373AD01 PUSH R14 (parent S)

    // Init: Set RSI=S, R14=D, EBP=0
    // Source writes to D (destination object)
    steps.add(w(4, D + 0x08, 0x00000000L)); // 373AD0F W32[D]=0
    steps.add(w(8, D + 0x10, 0x00000000L)); // 373AD11 W64[D+8]=0
    steps.add(w(4, D + 0x18, 0xFFFFFFFFL)); // 373AD15 W32[D+10]=FFFFFFFF

    // Call 1: 373AD20 -> 8895D0
    steps.add(w(8, childSP, M + 0x373AD25L)); // 373AD20 physical CALL push
    VolatileBits v1 = new VolatileBits(0x0A1B2C3D4E5F6071L, D + 0x20, S + 0x08, 0x1008L, 0x1009L, 0x100AL, 0x100BL, x(0x1010L), x(0x1020L), x(0x1030L), x(0x1040L), x(0x1050L), x(0x1060L));
    NonvolatileBits n1 = new NonvolatileBits(0x2001L, 0x00000000L, S + 0x08, 0x2004L, 0x2005L, 0x2006L, D + 0x08, D, x(0x2060L));
    ContextConstructor543Api.CallFrame f1 = ctorFrame(0x373AD20L, 0x8895D0L, v1, n1, false);
    VolatileBits rv1 = new VolatileBits(0x5100000000000001L, 0x5100000000000002L, 0x5100000000000003L, 0x5108L, 0x5109L, 0x510AL, 0x510BL, x(0x5110L), x(0x5120L), x(0x5130L), x(0x5140L), x(0x5150L), x(0x5160L));
    FullCopy437Api.CallResult res1 = result(rv1, n1, M + 0x373AD25L, bodySP, true);
    steps.add(new ContextKnownData553.ConstructorInvoke(f1, res1, List.of()));

    // Post Call 1: Write to D+100 (RCX was D+18, now D+100? No, RCX=D+18 in source, but contract says RCX=D+100 after call1? Contract: "After call1: RCX=D+100". Wait, source 373AD26 lea rcx,[r14+0x100]. R14 is D. So RCX=D+100.)
    steps.add(w(8, D + 0x108, 0x00000000L)); // 373AD2D W64[RCX]=0 (RCX=D+100)
    steps.add(w(8, D + 0x110, 0x00000000L)); // 373AD30 W64[RCX+8]=0
    steps.add(w(8, D + 0x118, M + 0x54DE270L)); // 373AD3B W64[RCX+10]=RDX (RDX=I+54DE270)

    // RBX = D+118
    steps.add(w(8, D + 0x120, M + 0x448D1F8L)); // 373AD4D W64[RBX]=RAX
    steps.add(w(8, D + 0x128, M + 0x448D268L)); // 373AD57 W64[RBX+8]=RAX
    steps.add(w(8, D + 0x130, 0x00000000L)); // 373AD5B W64[RBX+10]=0
    steps.add(w(8, D + 0x138, 0x00000000L)); // 373AD5F W64[RBX+18]=0
    steps.add(w(8, D + 0x140, M + 0x54DE278L)); // 373AD6A W64[RBX+20]=RAX
    steps.add(w(4, D + 0x148, 0x00000000L)); // 373AD6E W32[RBX+28]=0
    steps.add(w(8, D + 0x150, 0x00000000L)); // 373AD71 W64[RBX+30]=0
    steps.add(w(8, D + 0x158, 0x00000000L)); // 373AD75 W64[RBX+38]=0
    steps.add(w(8, D + 0x160, M + 0x54DE270L)); // 373AD79 W64[RBX+40]=RDX
    steps.add(w(4, D + 0x168, 0xFFFFFFFFL)); // 373AD7D W32[RBX+48]=FFFFFFFF
    steps.add(w(2, D + 0x16C, 0x0000L)); // 373AD84 W16[RBX+4C]=0
    steps.add(w(1, D + 0x16E, 0x00L)); // 373AD88 W8[RBX+4E]=0

    // Snapshot S to D
    steps.add(r128(S + 0x08, 0x1122334455667788L, 0x99AABBCCDDEEFF00L)); // 373AD8C read S+8
    steps.add(w128(D + 0x08, 0x1122334455667788L, 0x99AABBCCDDEEFF00L)); // 373AD8F write D+8
    steps.add(r(4, S + 0x18, 0xFFABCDE0L)); // 373AD93 read S+10 (DWORD)
    steps.add(w(4, D + 0x18, 0xFFABCDE0L)); // 373AD96 write D+10

    // Call 2: 373ADA1 -> 37282B0
    steps.add(w(8, childSP, M + 0x373ADA6L)); // 373ADA1 physical CALL push
    VolatileBits v2 = new VolatileBits(0xFFABCDE0L, D + 0x108, S + 0x108, 0x5108L, 0x5109L, 0x510AL, 0x510BL, new Bits128(0x1122334455667788L, 0x99AABBCCDDEEFF00L), x(0x5120L), x(0x5130L), x(0x5140L), x(0x5150L), x(0x5160L));
    // Note: XMM0 in v2 comes from snapshot. RAX is EAX from read.
    NonvolatileBits n2 = new NonvolatileBits(D + 0x120, 0x00000000L, S + 0x08, 0x2004L, 0x2005L, 0x2006L, D + 0x08, D, x(0x2060L));
    ContextConstructor543Api.CallFrame f2 = ctorFrame(0x373ADA1L, 0x37282B0L, v2, n2, true);
    VolatileBits rv2 = new VolatileBits(0x5200000000000001L, 0x5200000000000002L, 0x5200000000000003L, 0x5208L, 0x5209L, 0x520AL, 0x520BL, x(0x5210L), x(0x5220L), x(0x5230L), x(0x5240L), x(0x5250L), x(0x5260L));
    FullCopy437Api.CallResult res2 = result(rv2, n2, M + 0x373ADA6L, bodySP, false);
    steps.add(new ContextKnownData553.ConstructorInvoke(f2, res2, List.of()));

    // Call 3: 373ADAE -> 260E040
    steps.add(w(8, childSP, M + 0x373ADB3L)); // 373ADAE physical CALL push
    VolatileBits v3 = new VolatileBits(0x5200000000000001L, D + 0x20, S + 0x20, 0x5208L, 0x5209L, 0x520AL, 0x520BL, x(0x5210L), x(0x5220L), x(0x5230L), x(0x5240L), x(0x5250L), x(0x5260L));
    NonvolatileBits n3 = new NonvolatileBits(D + 0x120, 0x00000000L, S + 0x08, 0x2004L, 0x2005L, 0x2006L, D + 0x08, D, x(0x2060L));
    ContextConstructor543Api.CallFrame f3 = ctorFrame(0x373ADAEL, 0x260E040L, v3, n3, false);
    VolatileBits rv3 = new VolatileBits(0x5300000000000001L, 0x5300000000000002L, 0x5300000000000003L, 0x5308L, 0x5309L, 0x530AL, 0x530BL, x(0x5310L), x(0x5320L), x(0x5330L), x(0x5340L), x(0x5350L), x(0x5360L));
    FullCopy437Api.CallResult res3 = result(rv3, n3, M + 0x373ADB3L, bodySP, true);
    steps.add(new ContextKnownData553.ConstructorInvoke(f3, res3, List.of()));

    // Call 4: 373ADBD -> 3727180
    steps.add(w(8, childSP, M + 0x373ADC2L)); // 373ADBD physical CALL push
    VolatileBits v4 = new VolatileBits(0x5300000000000001L, D + 0x120, S + 0x120, 0x5308L, 0x5309L, 0x530AL, 0x530BL, x(0x5310L), x(0x5320L), x(0x5330L), x(0x5340L), x(0x5350L), x(0x5360L));
    NonvolatileBits n4 = new NonvolatileBits(D + 0x120, 0x00000000L, S + 0x08, 0x2004L, 0x2005L, 0x2006L, D + 0x08, D, x(0x2060L));
    ContextConstructor543Api.CallFrame f4 = ctorFrame(0x373ADBDL, 0x3727180L, v4, n4, true);
    VolatileBits rv4 = new VolatileBits(0xAA00000000000001L, 0xBB00000000000002L, 0xCC00000000000003L, 0xA008L, 0xA009L, 0xA00AL, 0xA00BL, x(0xA010L), x(0xA020L), x(0xA030L), x(0xA040L), x(0xA050L), x(0xA060L));
    FullCopy437Api.CallResult res4 = result(rv4, n4, M + 0x373ADC2L, bodySP, true);
    steps.add(new ContextKnownData553.ConstructorInvoke(f4, res4, List.of()));

    // Epilogue: Fresh restores and RET
    steps.add(r(8, childE + 0x10, 0x2001L)); // 373ADC6 fresh RBX
    steps.add(r(8, childE + 0x18, 0x2002L)); // 373ADCB fresh RBP
    steps.add(r(8, childE - 0x18, S)); // 373ADD4 fresh POP R14
    steps.add(r(8, childE - 0x10, 0x2004L)); // 373ADD6 fresh POP RDI
    steps.add(r(8, childE - 0x08, 0x2003L)); // 373ADD7 fresh POP RSI
    steps.add(r(8, childE, M + 0x3076B91L)); // 373ADD8 RET read
  }
public static void appendSecondConstructorScript(java.util.List<ContextKnownData553.Step> steps) {
    long M = 0x3300000000L;
    long E = 0x810000000000B008L;
    long childE = E - 0x40L;
    long D = 0x8100000000040000L;
    long S = 0x8100000000050000L;
    long bodySP = 0x810000000000AF90L;
    long childSP = 0x810000000000AF88L;
    long dest2 = 0x8100000000040170L;
    long src2 = 0x8100000000050170L;

    // Prologue writes
    steps.add(w(8, childE + 0x10, 0x2001L));
    steps.add(w(8, childE + 0x18, 0x2002L));
    steps.add(w(8, childE + 0x08, D + 0x170));
    steps.add(w(8, childE - 0x08, 0x2003L));
    steps.add(w(8, childE - 0x10, 0x2004L));
    steps.add(w(8, childE - 0x18, S));

    // Initial destination setup
    steps.add(w(4, D + 0x170, 0L));
    steps.add(w(8, D + 0x178, 0L));
    steps.add(w(4, D + 0x180, 0xFFFFFFFFL));

    // Call 1: 373AD20 -> 8895D0
    steps.add(w(8, childSP, M + 0x373AD25L));
    {
        VolatileBits v1 = new VolatileBits(
            D + 0x8, D + 0x188, S + 0x170,
            0xA008L, 0xA009L, 0xA00AL, 0xA00BL,
            new Bits128(0xA010L, 0xFFFFFFFFFFFF5FEFL), new Bits128(0xA020L, 0xFFFFFFFFFFFF5FDFL),
            new Bits128(0xA030L, 0xFFFFFFFFFFFF5FCFL), new Bits128(0xA040L, 0xFFFFFFFFFFFF5FBFL),
            new Bits128(0xA050L, 0xFFFFFFFFFFFF5FAFL), new Bits128(0xA060L, 0xFFFFFFFFFFFF5F9FL)
        );
        NonvolatileBits n1 = new NonvolatileBits(
            0x2001L, 0L, S + 0x170, 0x2004L, 0x2005L, 0x2006L, D + 0x170, D,
            new Bits128(0x2060L, 0xFFFFFFFFFFFFDF9FL)
        );
        ContextConstructor543Api.CallFrame f1 = ctorFrame(0x373AD20L, 0x8895D0L, v1, n1, true);
        VolatileBits rv1 = new VolatileBits(
            0x6100000000000001L, 0x6100000000000002L, 0x6100000000000003L,
            0x6108L, 0x6109L, 0x610AL, 0x610BL,
            new Bits128(0x6110L, 0xFFFFFFFFFFFF9EEFL), new Bits128(0x6120L, 0xFFFFFFFFFFFF9EDFL),
            new Bits128(0x6130L, 0xFFFFFFFFFFFF9ECFL), new Bits128(0x6140L, 0xFFFFFFFFFFFF9EBFL),
            new Bits128(0x6150L, 0xFFFFFFFFFFFF9EAFL), new Bits128(0x6160L, 0xFFFFFFFFFFFF9E9FL)
        );
        FullCopy437Api.CallResult r1 = result(rv1, n1, M + 0x373AD25L, bodySP, false);
        steps.add(new ConstructorInvoke(f1, r1, List.of()));
    }

    // Post-call 1 writes
    steps.add(w(8, D + 0x270, 0L));
    steps.add(w(8, D + 0x278, 0L));
    steps.add(w(8, D + 0x280, M + 0x54DE270L));
    steps.add(w(8, D + 0x288, M + 0x448D1F8L));
    steps.add(w(8, D + 0x290, M + 0x448D268L));
    steps.add(w(8, D + 0x298, 0L));
    steps.add(w(8, D + 0x2A0, 0L));
    steps.add(w(8, D + 0x2A8, M + 0x54DE278L));
    steps.add(w(4, D + 0x2B0, 0L));
    steps.add(w(8, D + 0x2B8, 0L));
    steps.add(w(8, D + 0x2C0, 0L));
    steps.add(w(8, D + 0x2C8, M + 0x54DE270L));
    steps.add(w(4, D + 0x2D0, 0xFFFFFFFFL));
    steps.add(w(2, D + 0x2D4, 0L));
    steps.add(w(1, D + 0x2D6, 0L));

    // Snapshot copy
    steps.add(r128(S + 0x170, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L));
    steps.add(w128(D + 0x170, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L));
    steps.add(r(4, S + 0x180, 0x80000001L));
    steps.add(w(4, D + 0x180, 0x80000001L));

    // Call 2: 373ADA1 -> 37282B0
    steps.add(w(8, childSP, M + 0x373ADA6L));
    {
        VolatileBits v2 = new VolatileBits(
            0x80000001L, D + 0x270, S + 0x270,
            0x6108L, 0x6109L, 0x610AL, 0x610BL,
            new Bits128(0x0123456789ABCDEFL, 0xFEDCBA9876543210L), new Bits128(0x6120L, 0xFFFFFFFFFFFF9EDFL),
            new Bits128(0x6130L, 0xFFFFFFFFFFFF9ECFL), new Bits128(0x6140L, 0xFFFFFFFFFFFF9EBFL),
            new Bits128(0x6150L, 0xFFFFFFFFFFFF9EAFL), new Bits128(0x6160L, 0xFFFFFFFFFFFF9E9FL)
        );
        NonvolatileBits n2 = new NonvolatileBits(
            D + 0x288, 0L, S + 0x170, 0x2004L, 0x2005L, 0x2006L, D + 0x170, D,
            new Bits128(0x2060L, 0xFFFFFFFFFFFFDF9FL)
        );
        ContextConstructor543Api.CallFrame f2 = ctorFrame(0x373ADA1L, 0x37282B0L, v2, n2, false);
        VolatileBits rv2 = new VolatileBits(
            0x6200000000000001L, 0x6200000000000002L, 0x6200000000000003L,
            0x6208L, 0x6209L, 0x620AL, 0x620BL,
            new Bits128(0x6210L, 0xFFFFFFFFFFFF9DEFL), new Bits128(0x6220L, 0xFFFFFFFFFFFF9DDFL),
            new Bits128(0x6230L, 0xFFFFFFFFFFFF9DCFL), new Bits128(0x6240L, 0xFFFFFFFFFFFF9DBFL),
            new Bits128(0x6250L, 0xFFFFFFFFFFFF9DAFL), new Bits128(0x6260L, 0xFFFFFFFFFFFF9D9FL)
        );
        FullCopy437Api.CallResult r2 = result(rv2, n2, M + 0x373ADA6L, bodySP, true);
        steps.add(new ConstructorInvoke(f2, r2, List.of()));
    }

    // Call 3: 373ADAE -> 260E040
    steps.add(w(8, childSP, M + 0x373ADB3L));
    {
        VolatileBits v3 = new VolatileBits(
            0x6200000000000001L, D + 0x188, S + 0x188,
            0x6208L, 0x6209L, 0x620AL, 0x620BL,
            new Bits128(0x6210L, 0xFFFFFFFFFFFF9DEFL), new Bits128(0x6220L, 0xFFFFFFFFFFFF9DDFL),
            new Bits128(0x6230L, 0xFFFFFFFFFFFF9DCFL), new Bits128(0x6240L, 0xFFFFFFFFFFFF9DBFL),
            new Bits128(0x6250L, 0xFFFFFFFFFFFF9DAFL), new Bits128(0x6260L, 0xFFFFFFFFFFFF9D9FL)
        );
        NonvolatileBits n3 = new NonvolatileBits(
            D + 0x288, 0L, S + 0x170, 0x2004L, 0x2005L, 0x2006L, D + 0x170, D,
            new Bits128(0x2060L, 0xFFFFFFFFFFFFDF9FL)
        );
        ContextConstructor543Api.CallFrame f3 = ctorFrame(0x373ADAEL, 0x260E040L, v3, n3, true);
        VolatileBits rv3 = new VolatileBits(
            0x6300000000000001L, 0x6300000000000002L, 0x6300000000000003L,
            0x6308L, 0x6309L, 0x630AL, 0x630BL,
            new Bits128(0x6310L, 0xFFFFFFFFFFFF9CEFL), new Bits128(0x6320L, 0xFFFFFFFFFFFF9CDFL),
            new Bits128(0x6330L, 0xFFFFFFFFFFFF9CCFL), new Bits128(0x6340L, 0xFFFFFFFFFFFF9CBFL),
            new Bits128(0x6350L, 0xFFFFFFFFFFFF9CAFL), new Bits128(0x6360L, 0xFFFFFFFFFFFF9C9FL)
        );
        FullCopy437Api.CallResult r3 = result(rv3, n3, M + 0x373ADB3L, bodySP, true);
        steps.add(new ConstructorInvoke(f3, r3, List.of()));
    }

    // Call 4: 373ADBD -> 3727180
    steps.add(w(8, childSP, M + 0x373ADC2L));
    {
        VolatileBits v4 = new VolatileBits(
            0x6300000000000001L, D + 0x288, S + 0x288,
            0x6308L, 0x6309L, 0x630AL, 0x630BL,
            new Bits128(0x6310L, 0xFFFFFFFFFFFF9CEFL), new Bits128(0x6320L, 0xFFFFFFFFFFFF9CDFL),
            new Bits128(0x6330L, 0xFFFFFFFFFFFF9CCFL), new Bits128(0x6340L, 0xFFFFFFFFFFFF9CBFL),
            new Bits128(0x6350L, 0xFFFFFFFFFFFF9CAFL), new Bits128(0x6360L, 0xFFFFFFFFFFFF9C9FL)
        );
        NonvolatileBits n4 = new NonvolatileBits(
            D + 0x288, 0L, S + 0x170, 0x2004L, 0x2005L, 0x2006L, D + 0x170, D,
            new Bits128(0x2060L, 0xFFFFFFFFFFFFDF9FL)
        );
        ContextConstructor543Api.CallFrame f4 = ctorFrame(0x373ADBDL, 0x3727180L, v4, n4, true);
        VolatileBits rv4 = new VolatileBits(
            0xDD00000000000001L, 0xEE00000000000002L, 0xFF00000000000003L,
            0xB008L, 0xB009L, 0xB00AL, 0xB00BL,
            new Bits128(0xB010L, 0xFFFFFFFFFFFF4FEFL), new Bits128(0xB020L, 0xFFFFFFFFFFFF4FDFL),
            new Bits128(0xB030L, 0xFFFFFFFFFFFF4FCFL), new Bits128(0xB040L, 0xFFFFFFFFFFFF4FBFL),
            new Bits128(0xB050L, 0xFFFFFFFFFFFF4FAFL), new Bits128(0xB060L, 0xFFFFFFFFFFFF4F9FL)
        );
        List<Write> eff4 = List.of(
            w(4, S + 0x2D8, 0x80000001L),
            w(4, S + 0x2DC, 0xFFFFFFFFL),
            w(4, S + 0x2E0, 0xAABBCCDDL),
            w(4, S + 0x2E4, 0x01234567L),
            w(4, S + 0x2E8, 0x89ABCDEFL),
            w(4, S + 0x2EC, 0xFEEDC0DEL),
            w128(S + 0x2F0, 0x0011223344556677L, 0x8899AABBCCDDEEFFL),
            w(8, S + 0x300, 0x8100000000060000L),
            w(4, S + 0x30C, 0xFFFFFFFEL)
        );
        FullCopy437Api.CallResult r4 = result(rv4, n4, M + 0x373ADC2L, bodySP, false);
        steps.add(new ConstructorInvoke(f4, r4, eff4));
        steps.addAll(eff4);
    }

    // Epilogue reads
    steps.add(r(8, childE + 0x10, 0x2001L));
    steps.add(r(8, childE + 0x18, 0x2002L));
    steps.add(r(8, childE - 0x18, S));
    steps.add(r(8, childE - 0x10, 0x2004L));
    steps.add(r(8, childE - 0x08, 0x2003L));
    steps.add(r(8, childE, M + 0x3076BA5L));
}
 public static int verify() {
  Scene scene=wholeContextScene();
  if(scene.steps().size()!=136)throw new AssertionError("source-declared total trace");
  ContextKnownHost553.verify(scene);
  return 1;
 }
 public static void main(String[] args) { System.out.println(verify()); }
}
