package org.xar.ck3.control.g2.m2.nativecode;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.CallResult;
import org.xar.ck3.control.g2.m2.nativecode.FullContext493Api.CallFrame;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextFullData507.*;
/** Recipe input constants and mechanical constructors only; new source scene model-derived and source-reviewed with bounded repairs. */
public final class PendingContextFullBook507 {
 private PendingContextFullBook507() { }
 private static final long M=0x3300000000L,E=0x820000000000D008L,D=0x8200000000004000L,S=0x8200000000010000L,B=0x8200000000020000L,RET=0xAABBCCDD11223344L;
 private static Bits128 x(long seed){return new Bits128(seed,~seed);}
 private static VolatileBits v(long seed,long ax,long cx,long dx){return new VolatileBits(ax,cx,dx,seed+8,seed+9,seed+0xA,seed+0xB,x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60));}
 private static NonvolatileBits n(long bx,long bp,long si,long di,long a12,long a13,long a14,long a15){return new NonvolatileBits(bx,bp,si,di,a12,a13,a14,a15,x(0x2060));}
 private static NonvolatileBits n0(){return n(0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008);}
 private static VolatileBits v0(){return v(0x1000,0x8877665544332211L,D,S);}
 private static Cell c(int width,long address,long bits){return new Cell(width,address,new Bits128(bits,0));}
 private static Read r(int width,long address,long bits){return new Read(width,address,new Bits128(bits,0));}
 private static Write w(int width,long address,long bits){return new Write(width,address,new Bits128(bits,0));}
 private static Cell c128(long address,Bits128 bits){return new Cell(16,address,bits);}
 private static Read r128(long address,Bits128 bits){return new Read(16,address,bits);}
 private static Write w128(long address,Bits128 bits){return new Write(16,address,bits);}
 private static CallResult result(VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df){return new CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df);}
 private static CallFrame frame(long site,long target,long preSP,long childSP,VolatileBits v,NonvolatileBits n,boolean df,int length,long rip){return new CallFrame(new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,preSP,v,n),new Entry(M,childSP,v,n),df,length,rip);}
 private static Scene scene() {
    List<Cell> initialMemory = List.of(
        c(8, E, RET),
        c(8, S, 0xA1B2C3D4E5F6071L)
    );

    List<Step> steps = new ArrayList<>();

    // Prologue: Save RBX, RSI, RCX
    steps.add(w(8, E + 0x10, 0x2001L));
    steps.add(w(8, E + 0x18, 0x2003L));
    steps.add(w(8, E + 0x08, D));

    // Push RDI, R14, R15
    steps.add(w(8, E - 0x08, 0x2004L));
    steps.add(w(8, E - 0x10, 0x2007L));
    steps.add(w(8, E - 0x18, 0x2008L));

    // SUB RSP, 20 (No memory effect)

    // MOV R14, RDX (S)
    // MOV R15, RCX (D)

    // MOV RAX, QWORD PTR [RDX] -> q[S]
    steps.add(r(8, S, 0xA1B2C3D4E5F6071L));

    // MOV QWORD PTR [RCX], RAX -> [D] = q[S]
    steps.add(w(8, D, 0xA1B2C3D4E5F6071L));

    // ADD RCX, 8
    // ADD RDX, 8

    // CALL 1: 3076B8C -> 373ACF0
    // Pre-push continuation
    steps.add(w(8, E - 0x40, M + 0x3076B91L));

    // Frame 1 V/N/DF
    // V: RAX=q[S], RCX=D+8, RDX=S+8, R8..R11/XMM0..5 incoming
    // N: RBX=0x2001, RBP=0x2002, RSI=0x2003, RDI=0x2004, R12=0x2005, R13=0x2006, R14=S, R15=D, XMM6=x(0x2060)
    // DF: false
    VolatileBits v1 = new VolatileBits(0xA1B2C3D4E5F6071L, D + 8, S + 8, 0x1008, 0x1009, 0x100A, 0x100B, x(0x1010), x(0x1020), x(0x1030), x(0x1040), x(0x1050), x(0x1060));
    NonvolatileBits n1 = n(0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, S, D);
    CallFrame f1 = frame(0x3076B8CL, 0x373ACF0L, E - 0x38, E - 0x40, v1, n1, false, 5, M + 0x3076B91L);

    // Result 1: v(0x3000, 0x3031323334353637, 0x4041424344454647, 0x5051525354555657), DF true, no effects
    CallResult r1 = result(v(0x3000, 0x3031323334353637L, 0x4041424344454647L, 0x5051525354555657L), n1, M + 0x3076B91L, E - 0x38, true);
    steps.add(new Invoke(f1, r1, List.of()));

    // LEA RCX, [R15 + 0x170] -> D + 0x170
    // LEA RDX, [R14 + 0x170] -> S + 0x170

    // CALL 2: 3076BA0 -> 373ACF0
    steps.add(w(8, E - 0x40, M + 0x3076BA5L));

    // Frame 2 V/N/DF
    // V: RAX=Q1.RAX, RCX=D+0x170, RDX=S+0x170, R8..R11/XMM0..5 Q1
    // N: same as n1
    // DF: true
    VolatileBits v2 = new VolatileBits(0x3031323334353637L, D + 0x170, S + 0x170, 0x3008, 0x3009, 0x300A, 0x300B, x(0x3010), x(0x3020), x(0x3030), x(0x3040), x(0x3050), x(0x3060));
    CallFrame f2 = frame(0x3076BA0L, 0x373ACF0L, E - 0x38, E - 0x40, v2, n1, true, 5, M + 0x3076BA5L);

    // Result 2: v(0x4000, 0x6061626364656667, 0x7071727374757677, 0x8000000000004003), DF false
    // Effects: W32[S+2D8]=80000001; W32[S+2DC]=FFFFFFFF; W32[S+2E0]=AABBCCDD; W32[S+2E4]=01234567; W32[S+2E8]=89ABCDEF; W32[S+2EC]=FEEDC0DE; W128[S+2F0]=(0011223344556677,8899AABBCCDDEEFF); W64[S+300]=B; W32[S+30C]=FFFFFFFE
    List<Write> eff2 = List.of(
        w(4, S + 0x2D8, 0x80000001L),
        w(4, S + 0x2DC, 0xFFFFFFFFL),
        w(4, S + 0x2E0, 0xAABBCCDDL),
        w(4, S + 0x2E4, 0x01234567L),
        w(4, S + 0x2E8, 0x89ABCDEFL),
        w(4, S + 0x2EC, 0xFEEDC0DEL),
        w128(S + 0x2F0, new Bits128(0x0011223344556677L, 0x8899AABBCCDDEEFFL)),
        w(8, S + 0x300, B),
        w(4, S + 0x30C, 0xFFFFFFFEL)
    );
    CallResult r2 = result(v(0x4000, 0x6061626364656667L, 0x7071727374757677L, 0x8000000000004003L), n1, M + 0x3076BA5L, E - 0x38, false);
    steps.add(new Invoke(f2, r2, eff2));
    steps.addAll(eff2);

    // MOV EAX, DWORD PTR [R14 + 0x2D8] -> q[S+2D8]
    steps.add(r(4, S + 0x2D8, 0x80000001L));
    // MOV DWORD PTR [R15 + 0x2D8], EAX -> [D+2D8]
    steps.add(w(4, D + 0x2D8, 0x80000001L));

    // MOV EAX, DWORD PTR [R14 + 0x2DC] -> q[S+2DC]
    steps.add(r(4, S + 0x2DC, 0xFFFFFFFFL));
    // MOV DWORD PTR [R15 + 0x2DC], EAX -> [D+2DC]
    steps.add(w(4, D + 0x2DC, 0xFFFFFFFFL));

    // MOV EAX, DWORD PTR [R14 + 0x2E0] -> q[S+2E0]
    steps.add(r(4, S + 0x2E0, 0xAABBCCDDL));
    // MOV DWORD PTR [R15 + 0x2E0], EAX -> [D+2E0]
    steps.add(w(4, D + 0x2E0, 0xAABBCCDDL));

    // MOV EAX, DWORD PTR [R14 + 0x2E4] -> q[S+2E4]
    steps.add(r(4, S + 0x2E4, 0x01234567L));
    // MOV DWORD PTR [R15 + 0x2E4], EAX -> [D+2E4]
    steps.add(w(4, D + 0x2E4, 0x01234567L));

    // MOV EAX, DWORD PTR [R14 + 0x2E8] -> q[S+2E8]
    steps.add(r(4, S + 0x2E8, 0x89ABCDEFL));
    // MOV DWORD PTR [R15 + 0x2E8], EAX -> [D+2E8]
    steps.add(w(4, D + 0x2E8, 0x89ABCDEFL));

    // MOV EAX, DWORD PTR [R14 + 0x2EC] -> q[S+2EC]
    steps.add(r(4, S + 0x2EC, 0xFEEDC0DEL));
    // MOV DWORD PTR [R15 + 0x2EC], EAX -> [D+2EC]
    steps.add(w(4, D + 0x2EC, 0xFEEDC0DEL));

    // MOVUPS XMM0, [R14 + 0x2F0] -> [S+2F0]
    steps.add(r128(S + 0x2F0, new Bits128(0x0011223344556677L, 0x8899AABBCCDDEEFFL)));
    // MOVUPS [R15 + 0x2F0], XMM0 -> [D+2F0]
    steps.add(w128(D + 0x2F0, new Bits128(0x0011223344556677L, 0x8899AABBCCDDEEFFL)));

    // MOVSXD RBX, DWORD PTR [R14 + 0x30C] -> q[S+30C] (Signed)
    steps.add(r(4, S + 0x30C, 0xFFFFFFFEL));
    // MOV RDI, QWORD PTR [R14 + 0x300] -> q[S+300]
    steps.add(r(8, S + 0x300, B));
    // LEA RCX, [R15 + 0x300] -> D + 0x300

    // CALL 3: 3076C1F -> 105D2D0
    steps.add(w(8, E - 0x40, M + 0x3076C24L));

    // Frame 3 V/N/DF
    // V: RAX=u32(q[S+2EC]), RCX=D+0x300, RDX=Q2.RDX, R8..R11/XMM0..5 Q2
    // N: RBX=sign64(q[S+30C]), RBP=0x2002, RSI=0x2003, RDI=q[S+300], R12=0x2005, R13=0x2006, R14=S, R15=D, XMM6=x(0x2060)
    // DF: false
    VolatileBits v3 = new VolatileBits(0xFEEDC0DEL, D + 0x300, 0x8000000000004003L, 0x4008, 0x4009, 0x400A, 0x400B, new Bits128(0x0011223344556677L, 0x8899AABBCCDDEEFFL), x(0x4020), x(0x4030), x(0x4040), x(0x4050), x(0x4060));
    NonvolatileBits n3 = n(0xFFFFFFFFFFFFFFFEL, 0x2002, 0x2003, B, 0x2005, 0x2006, S, D);
    CallFrame f3 = frame(0x3076C1FL, 0x105D2D0L, E - 0x38, E - 0x40, v3, n3, false, 5, M + 0x3076C24L);

    // Result 3: v(0x5000, 0x8182838485868788, 0x9192939495969798, 0xA1A2A3A4A5A6A7A8), DF true
    // Effects: W32[D+30C]=80000001; W64[S+300]=B+1000; W32[S+30C]=7
    List<Write> eff3 = List.of(
        w(4, D + 0x30C, 0x80000001L),
        w(8, S + 0x300, B + 0x1000),
        w(4, S + 0x30C, 0x7L)
    );
    CallResult r3 = result(v(0x5000, 0x8182838485868788L, 0x9192939495969798L, 0xA1A2A3A4A5A6A7A8L), n3, M + 0x3076C24L, E - 0x38, true);
    steps.add(new Invoke(f3, r3, eff3));
    steps.addAll(eff3);

    // LEA R9, [RDI + RBX] -> B + 0xFFFFFFFFFFFFFFFEL
    // MOV R8, RDI -> B
    // MOV EDX, DWORD PTR [R15 + 0x30C] -> q[D+30C]
    steps.add(r(4, D + 0x30C, 0x80000001L));
    // LEA RCX, [R15 + 0x300] -> D + 0x300

    // CALL 4: 3076C39 -> BCB7C0
    steps.add(w(8, E - 0x40, M + 0x3076C3EL));

    // Frame 4 V/N/DF
    // V: RAX=Q3.RAX, RCX=D+0x300, RDX=u32(q[D+30C]), R8=B, R9=B+0xFFFFFFFFFFFFFFFEL, R10/R11/XMM0..5 Q3
    // N: same as n3
    // DF: true
    VolatileBits v4 = new VolatileBits(0x8182838485868788L, D + 0x300, 0x80000001L, B, B + 0xFFFFFFFFFFFFFFFEL, 0x500A, 0x500B, x(0x5010), x(0x5020), x(0x5030), x(0x5040), x(0x5050), x(0x5060));
    CallFrame f4 = frame(0x3076C39L, 0xBCB7C0L, E - 0x38, E - 0x40, v4, n3, true, 5, M + 0x3076C3EL);

    // Result 4: v(0x6000, 0xB1B2B3B4B5B6B7B8, 0xC1C2C3C4C5C6C7C8, 0xD1D2D3D4D5D6D7D8), DF false, no effects
    CallResult r4 = result(v(0x6000, 0xB1B2B3B4B5B6B7B8L, 0xC1C2C3C4C5C6C7C8L, 0xD1D2D3D4D5D6D7D8L), n3, M + 0x3076C3EL, E - 0x38, false);
    steps.add(new Invoke(f4, r4, List.of()));

    // LEA RCX, [R15 + 0x330] -> D + 0x330
    // MOV RDX, R14 -> S

    // CALL 5: 3076C49 -> 2503880
    steps.add(w(8, E - 0x40, M + 0x3076C4EL));

    // Frame 5 V/N/DF
    // V: RAX=Q4.RAX, RCX=D+0x330, RDX=S, R8..R11/XMM0..5 Q4
    // N: same as n3
    // DF: false
    VolatileBits v5 = new VolatileBits(0xB1B2B3B4B5B6B7B8L, D + 0x330, S, 0x6008, 0x6009, 0x600A, 0x600B, x(0x6010), x(0x6020), x(0x6030), x(0x6040), x(0x6050), x(0x6060));
    CallFrame f5 = frame(0x3076C49L, 0x2503880L, E - 0x38, E - 0x40, v5, n3, false, 5, M + 0x3076C4EL);

    // Result 5: v(0x7000, 0xE1E2E3E4E5E6E7E8, 0xF1F2F3F4F5F6F7F8, 0x0102030405060708), DF true
    // Effects: W64[E+10]=A11AA11AA11AA11A; W64[E+18]=B22BB22BB22BB22B; W64[E-18]=C33CC33CC33CC33C; W64[E-10]=D44DD44DD44DD44D; W64[E-8]=E55EE55EE55EE55E; W64[E]=F66FF66FF66FF66F
    List<Write> eff5 = List.of(
        w(8, E + 0x10, 0xA11AA11AA11AA11AL),
        w(8, E + 0x18, 0xB22BB22BB22BB22BL),
        w(8, E - 0x18, 0xC33CC33CC33CC33CL),
        w(8, E - 0x10, 0xD44DD44DD44DD44DL),
        w(8, E - 0x08, 0xE55EE55EE55EE55EL),
        w(8, E, 0xF66FF66FF66FF66FL)
    );
    CallResult r5 = result(v(0x7000, 0xE1E2E3E4E5E6E7E8L, 0xF1F2F3F4F5F6F7F8L, 0x0102030405060708L), n3, M + 0x3076C4EL, E - 0x38, true);
    steps.add(new Invoke(f5, r5, eff5));
    steps.addAll(eff5);

    // MOV RAX, R15 -> D
    // MOV RBX, QWORD PTR [RSP + 0x48] -> q[E+10]
    steps.add(r(8, E + 0x10, 0xA11AA11AA11AA11AL));
    // MOV RSI, QWORD PTR [RSP + 0x50] -> q[E+18]
    steps.add(r(8, E + 0x18, 0xB22BB22BB22BB22BL));
    // ADD RSP, 20
    // POP R15 -> q[E-18]
    steps.add(r(8, E - 0x18, 0xC33CC33CC33CC33CL));
    // POP R14 -> q[E-10]
    steps.add(r(8, E - 0x10, 0xD44DD44DD44DD44DL));
    // POP RDI -> q[E-8]
    steps.add(r(8, E - 0x08, 0xE55EE55EE55EE55EL));
    // RET -> q[E]
    steps.add(r(8, E, 0xF66FF66FF66FF66FL));

    // Final Expected Result
    // V: RAX=D, RCX=Q5.RCX, RDX=Q5.RDX, R8..R11/XMM0..5 Q5
    // N: RBX=q[E+10], RBP=0x2002, RSI=q[E+18], RDI=q[E-8], R12=0x2005, R13=0x2006, R14=q[E-10], R15=q[E-18], XMM6=x(0x2060)
    // RIP: q[E], SP: E+8, DF: true
    VolatileBits vFinal = new VolatileBits(D, 0xF1F2F3F4F5F6F7F8L, 0x0102030405060708L, 0x7008, 0x7009, 0x700A, 0x700B, x(0x7010), x(0x7020), x(0x7030), x(0x7040), x(0x7050), x(0x7060));
    NonvolatileBits nFinal = n(0xA11AA11AA11AA11AL, 0x2002, 0xB22BB22BB22BB22BL, 0xE55EE55EE55EE55EL, 0x2005, 0x2006, 0xD44DD44DD44DD44DL, 0xC33CC33CC33CC33CL);
    CallResult expectedResult = result(vFinal, nFinal, 0xF66FF66FF66FF66FL, E + 8, true);

    // Final Memory Cells
    List<Cell> finalMemory = List.of(
        c(8, D, 0xA1B2C3D4E5F6071L),
        c(4, D + 0x2D8, 0x80000001L),
        c(4, D + 0x2DC, 0xFFFFFFFFL),
        c(4, D + 0x2E0, 0xAABBCCDDL),
        c(4, D + 0x2E4, 0x01234567L),
        c(4, D + 0x2E8, 0x89ABCDEFL),
        c(4, D + 0x2EC, 0xFEEDC0DEL),
        c128(D + 0x2F0, new Bits128(0x0011223344556677L, 0x8899AABBCCDDEEFFL)),
        c(4, D + 0x30C, 0x80000001L),
        c(8, S + 0x300, B + 0x1000),
        c(4, S + 0x30C, 0x7L),
        c(8, E + 0x10, 0xA11AA11AA11AA11AL),
        c(8, E + 0x18, 0xB22BB22BB22BB22BL),
        c(8, E - 0x18, 0xC33CC33CC33CC33CL),
        c(8, E - 0x10, 0xD44DD44DD44DD44DL),
        c(8, E - 0x08, 0xE55EE55EE55EE55EL),
        c(8, E, 0xF66FF66FF66FF66FL)
    );

    return new Scene("FULL_CONTEXT", new Entry(M, E, v0(), n0()), false, initialMemory, steps, expectedResult, finalMemory);
}
 public static List<Scene> scenes(){return List.of(scene());}
 public static int verify(){List<Scene> s=scenes();for(Scene x:s)PendingContextFullHost507.verify(x);return s.size();}
 public static void main(String[] args){System.out.println(verify());}
}
