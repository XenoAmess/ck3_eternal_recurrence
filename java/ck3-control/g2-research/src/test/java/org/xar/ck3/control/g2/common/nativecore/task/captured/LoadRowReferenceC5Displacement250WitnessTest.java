package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class LoadRowReferenceC5Displacement250WitnessTest {
 static Op o(String kind,long address,long value) {return new Op(kind,address,value);}
 static Bits128 x(long b) {return new Bits128(b,b+1L);}
 static VolatileBits v(long b) {return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60));}
 static NonvolatileBits n(long b) {return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80));}
 static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) {return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());}
 static final class Ports implements Calls {
  java.util.function.Function<Call,VolatileBits> invoke=c->{throw new AssertionError(c);};
  java.util.function.Function<Tail,NormalReturn> tail=t->{throw new AssertionError(t);};
  java.util.function.LongSupplier gs=()->{throw new AssertionError("GS58");};
  public VolatileBits invoke(Call c) {return invoke.apply(c);}
  public NormalReturn tail(Tail t) {return tail.apply(t);}
  public long readGsQword58() {return gs.getAsLong();}
 }

 static void expectCall(Call actual,long site,TargetKind kind,long target,long sp,VolatileBits expectedV,NonvolatileBits expectedN) {
  assertEquals(new Call(site,kind,target,sp,expectedV,expectedN),actual);
 }
 @Test void whole199MigrationDisplacesAdjacentRow250() {
  final long I=0x0000000140000000L,E=0x0000000360000000L,O=0x0000000220000000L,T=0x0000000221000000L,NT=0x0000000222000000L;
  final long OUT=0x0000000223000000L,K=0x0000000224000000L,DESC=0x0000000225000000L,OBJ=0x0000000226000000L,VT=0x0000000227000000L;
  final long AT=I+0x100001L,FT=I+0x100002L,GSL=0x0000000228000000L,TLS=0x0000000229000000L,P=0x0000000230000000L,RET=I+0x123456L;
  final long KA=0xA123456700000001L,KB=0xB234567800000002L,KC=0xC345678900000003L,KD=0xD456789A00000004L;
  final long B=E-0x4F,W=E-0x118,Z=W-0x8,U=Z-0x58,C=U-0x8,CW=C-0xC8,M=CW-0x8,J=W-0x8;
  final Bytes m=new Bytes(),oldImage=new Bytes(),newImage=new Bytes();
  for(int j=-0x400;j<0x80;j++)m.putB(E+j,0xA5);
  for(int j=-0x1;j<=0x460;j++){m.putB(T+j,0xA5);oldImage.putB(T+j,0xA5);}
  for(int j=-0x1;j<=0x730;j++){m.putB(NT+j,0xA5);newImage.putB(NT+j,0xA5);}
  for(int j=-0x1;j<=0x10;j++)m.putB(OUT+j,0xA5);
  for(int j=0;j<0xE;j++){m.putB(T+j*0x50+0x4,j==0xD?0xFF:0x0);oldImage.putB(T+j*0x50+0x4,j==0xD?0xFF:0x0);}
  final int[] oldRows={0x0,0x7,0x8},hashes={0x8,0x7,0x17},markers={0x1,0x1,0x2};final long[] keys={KA,KB,KC},payloads={P,0x0,0x0};
  for(int j=0;j<0x3;j++){long a=T+oldRows[j]*0x50L;m.putD(a,hashes[j]);m.putB(a+0x4,markers[j]);m.putQ(a+0x8,keys[j]);m.putQ(a+0x48,payloads[j]);oldImage.putD(a,hashes[j]);oldImage.putB(a+0x4,markers[j]);oldImage.putQ(a+0x8,keys[j]);oldImage.putQ(a+0x48,payloads[j]);}
  m.putQ(O+0x8,T);m.putD(O+0x10,0x3);m.putD(O+0x14,0x7);m.putB(O+0x18,0x5);m.putD(O+0x1C,0x3F000000);m.putQ(O+0x20,OBJ);
  m.putQ(OBJ,VT);m.putQ(VT+0x8,AT);m.putQ(VT+0x10,FT);m.putQ(GSL,TLS);m.putD(TLS+0x10,0x7);m.putD(I+0x5C673D0L,0xFFFFFFFF);
  m.putQ(K,KD);m.putQ(DESC+0x38,0x0);m.putQ(E,RET);m.putQ(E+0x18,0x7F6E5D4C12345678L);m.putQ(E+0x30,DESC);m.putQ(P,0xF123456789ABCDEFL);m.putQ(P+0x8,0xE23456789ABCDEF1L);
  final NonvolatileBits en=n(0x9182736400001000L);final long r14=(en.r14Bits()&~0xFFL)|0x3;
  final VolatileBits seed=v(0xA1B2C3D400002000L),iv=q(seed,seed.raxBits(),O,OUT,0xFEDCBA980000000FL,K,seed.r10Bits(),seed.r11Bits());
  final VolatileBits av0=v(0xB2C3D4E500003000L),av=q(av0,NT,av0.rcxBits(),av0.rdxBits(),av0.r8Bits(),av0.r9Bits(),av0.r10Bits(),av0.r11Bits()),fv=v(0xC3D4E5F600004000L);
  final NonvolatileBits rootN=new NonvolatileBits(T+0x2D0,B,O,OUT,K,en.r13Bits(),r14,en.r15Bits(),en.xmm6());
  final VolatileBits rootFp=new VolatileBits(iv.raxBits(),iv.rcxBits(),iv.rdxBits(),iv.r8Bits(),iv.r9Bits(),iv.r10Bits(),iv.r11Bits(),new Bits128(0x40E00000L,0x0),new Bits128(0x3F124925L,0x0),iv.xmm2(),iv.xmm3(),iv.xmm4(),iv.xmm5());
  final VolatileBits capIn=q(rootFp,0x4,0x8,0x1,iv.r8Bits(),K,iv.r10Bits(),iv.r11Bits()),capOut=q(rootFp,0x4,0x4,0x1D,0x3,0x1,iv.r10Bits(),iv.r11Bits());
  final VolatileBits c0In=q(capOut,0x4,O,0x4,0x3,0x1,iv.r10Bits(),iv.r11Bits()),allocIn=q(rootFp,0x17,OBJ,0x730,0x8,AT,iv.r10Bits(),iv.r11Bits());
  final NonvolatileBits allocN=new NonvolatileBits(0x10,T,O,0x3,K,en.r13Bits(),0x0,en.r15Bits(),en.xmm6());
  final VolatileBits freeFp=new VolatileBits(av.raxBits(),av.rcxBits(),av.rdxBits(),av.r8Bits(),av.r9Bits(),av.r10Bits(),av.r11Bits(),new Bits128(0x41700000L,0x0),new Bits128(0x3E4CCCCDL,0x0),av.xmm2(),av.xmm3(),av.xmm4(),av.xmm5());
  final VolatileBits freeIn=q(freeFp,VT,OBJ,T,0x8,T+0x288,0x7,av.r11Bits());final NonvolatileBits freeN=new NonvolatileBits(T+0x2D0,T,O,OUT,K,en.r13Bits(),r14,en.r15Bits(),en.xmm6());
  final VolatileBits childIn=q(fv,DESC,O,OUT,0xF,K,fv.r10Bits(),fv.r11Bits());
  record F(int kind,int a,int b,int result,int at){}record L(long pc,long row,int at){}
  final List<Op> expected=new ArrayList<>();
  // Literal source block: whole199-lookup-two-comparisons-and-growth
  expected.add(o("wq",E+0x10,en.rbxBits()));
  expected.add(o("wq",E+0x20,K));
  expected.add(o("wd",E+0x18,0xF));
  expected.add(o("wq",E-0x8,en.rbpBits()));
  expected.add(o("wq",E-0x10,en.rsiBits()));
  expected.add(o("wq",E-0x18,en.rdiBits()));
  expected.add(o("wq",E-0x20,en.r12Bits()));
  expected.add(o("wq",E-0x28,en.r13Bits()));
  expected.add(o("wq",E-0x30,en.r14Bits()));
  expected.add(o("wq",E-0x38,en.r15Bits()));
  expected.add(o("rd",O+0x14,0x7));
  expected.add(o("rq",O+0x8,T));
  expected.add(o("rb",T+0x234,0x1));
  expected.add(o("rq",K,KD));
  expected.add(o("rq",T+0x238,KB));
  expected.add(o("rb",T+0x284,0x2));
  expected.add(o("rq",T+0x288,KC));
  expected.add(o("rb",T+0x2D4,0x0));
  expected.add(o("rb",O+0x18,0x5));
  expected.add(o("rd",O+0x10,0x3));
  expected.add(o("rd",O+0x1C,0x3F000000L));
  expected.add(o("wq",W-0x8,I+0x337BB81L));
  expected.add(o("rq",W-0x8,I+0x337BB81L));
  expected.add(o("wq",W-0x8,I+0x337BB90L));
  // Literal source block: C0-allocate22clear-sentinel-firstgetter
  expected.add(o("wq",Z-0x8,O));
  expected.add(o("wq",U+0x60,T+0x2D0));
  expected.add(o("wq",U+0x70,B));
  expected.add(o("rq",O+0x8,T));
  expected.add(o("wb",O+0x18,0x6));
  expected.add(o("rq",O+0x20,OBJ));
  expected.add(o("wq",U+0x48,OUT));
  expected.add(o("rd",O+0x10,0x3));
  expected.add(o("wq",U+0x40,r14));
  expected.add(o("wd",O+0x14,0xF));
  expected.add(o("wd",O+0x10,0x0));
  expected.add(o("rq",OBJ,VT));
  expected.add(o("rq",VT+0x8,AT));
  expected.add(o("wq",U-0x8,I+0x337C131L));
  expected.add(o("rb",O+0x18,0x6));
  expected.add(o("wq",O+0x8,NT));
  expected.add(o("wb",NT+0x4,0x0));
  expected.add(o("wb",NT+0x54,0x0));
  expected.add(o("wb",NT+0xA4,0x0));
  expected.add(o("wb",NT+0xF4,0x0));
  expected.add(o("wb",NT+0x144,0x0));
  expected.add(o("wb",NT+0x194,0x0));
  expected.add(o("wb",NT+0x1E4,0x0));
  expected.add(o("wb",NT+0x234,0x0));
  expected.add(o("wb",NT+0x284,0x0));
  expected.add(o("wb",NT+0x2D4,0x0));
  expected.add(o("wb",NT+0x324,0x0));
  expected.add(o("wb",NT+0x374,0x0));
  expected.add(o("wb",NT+0x3C4,0x0));
  expected.add(o("wb",NT+0x414,0x0));
  expected.add(o("wb",NT+0x464,0x0));
  expected.add(o("wb",NT+0x4B4,0x0));
  expected.add(o("wb",NT+0x504,0x0));
  expected.add(o("wb",NT+0x554,0x0));
  expected.add(o("wb",NT+0x5A4,0x0));
  expected.add(o("wb",NT+0x5F4,0x0));
  expected.add(o("wb",NT+0x644,0x0));
  expected.add(o("wb",NT+0x694,0x0));
  expected.add(o("wb",NT+0x6E4,0xFF));
  expected.add(o("wq",U-0x8,I+0x337C166L));
  expected.add(o("rq",GSL,TLS));
  expected.add(o("rd",TLS+0x10,0x7));
  expected.add(o("rd",I+0x5C673D0L,0xFFFFFFFFL));
  expected.add(o("rq",U-0x8,I+0x337C166L));
  // Literal source block: fixed-migration-0-actual201
  expected.add(o("rb",T+0x0+0x4,0x1));
  expected.add(o("rd",T+0x0,0x8));
  expected.add(o("wq",U+0x20,U+0x68));
  expected.add(o("wb",U+0x68,0x0));
  expected.add(o("wq",U-0x8,I+0x337C19DL));
  expected.add(o("wq",C-0x8,T));
  expected.add(o("wq",C-0x10,T+0x0+0x48));
  expected.add(o("wq",C-0x18,O));
  expected.add(o("wq",C-0x20,0x3));
  expected.add(o("wq",C-0x28,en.r13Bits()));
  expected.add(o("wq",C-0x30,0x0));
  expected.add(o("wq",C-0x38,en.r15Bits()));
  expected.add(o("rd",O+0x14,0xF));
  expected.add(o("rq",O+0x8,NT));
  expected.add(o("rb",NT+0x280+0x4,0x0));
  expected.add(o("rb",O+0x18,0x6));
  expected.add(o("rd",O+0x10,0x0));
  expected.add(o("rd",O+0x1C,0x3F000000L));
  expected.add(o("rb",NT+0x280+0x4,0x0));
  expected.add(o("wq",C+0x10,K));
  expected.add(o("wd",NT+0x280,0x8));
  expected.add(o("wb",NT+0x280+0x4,0x1));
  expected.add(o("rq",T+0x0+0x8,KA));
  expected.add(o("wq",NT+0x280+0x8,KA));
  expected.add(o("wq",NT+0x280+0x48,0x0));
  expected.add(o("wq",CW-0x8,I+0x337C690L));
  expected.add(o("wq",M+0x8,NT+0x280));
  expected.add(o("wq",M-0x8,0x1));
  expected.add(o("rq",T+0x0+0x48,P));
  expected.add(o("wq",NT+0x280+0x48,P));
  expected.add(o("wq",T+0x0+0x48,0x0));
  expected.add(o("rq",M+0x8,NT+0x280));
  expected.add(o("rq",M-0x8,0x1));
  expected.add(o("rq",M,I+0x337C690L));
  expected.add(o("rd",O+0x10,0x0));
  expected.add(o("wd",O+0x10,0x1));
  expected.add(o("wq",U+0x30,NT+0x280));
  expected.add(o("wb",U+0x38,0x1));
  expected.add(o("rq",C+0x10,K));
  expected.add(o("rq",C-0x38,en.r15Bits()));
  expected.add(o("rq",C-0x30,0x0));
  expected.add(o("rq",C-0x28,en.r13Bits()));
  expected.add(o("rq",C-0x20,0x3));
  expected.add(o("rq",C-0x18,O));
  expected.add(o("rq",C-0x10,T+0x0+0x48));
  expected.add(o("rq",C-0x8,T));
  expected.add(o("rq",C,I+0x337C19DL));
  expected.add(o("rq",T+0x0+0x48,0x0));
  // Literal source block: literal-six-empty-oldrows
  expected.add(o("rb",T+0x54,0x0));
  expected.add(o("rb",T+0xA4,0x0));
  expected.add(o("rb",T+0xF4,0x0));
  expected.add(o("rb",T+0x144,0x0));
  expected.add(o("rb",T+0x194,0x0));
  expected.add(o("rb",T+0x1E4,0x0));
  // Literal source block: fixed-migration-1-actual201
  expected.add(o("rb",T+0x230+0x4,0x1));
  expected.add(o("rd",T+0x230,0x7));
  expected.add(o("wq",U+0x20,U+0x68));
  expected.add(o("wb",U+0x68,0x0));
  expected.add(o("wq",U-0x8,I+0x337C19DL));
  expected.add(o("wq",C-0x8,T));
  expected.add(o("wq",C-0x10,T+0x230+0x48));
  expected.add(o("wq",C-0x18,O));
  expected.add(o("wq",C-0x20,0x2));
  expected.add(o("wq",C-0x28,en.r13Bits()));
  expected.add(o("wq",C-0x30,0x0));
  expected.add(o("wq",C-0x38,en.r15Bits()));
  expected.add(o("rd",O+0x14,0xF));
  expected.add(o("rq",O+0x8,NT));
  expected.add(o("rb",NT+0x230+0x4,0x0));
  expected.add(o("rb",O+0x18,0x6));
  expected.add(o("rd",O+0x10,0x1));
  expected.add(o("rd",O+0x1C,0x3F000000L));
  expected.add(o("rb",NT+0x230+0x4,0x0));
  expected.add(o("wq",C+0x10,K));
  expected.add(o("wd",NT+0x230,0x7));
  expected.add(o("wb",NT+0x230+0x4,0x1));
  expected.add(o("rq",T+0x230+0x8,KB));
  expected.add(o("wq",NT+0x230+0x8,KB));
  expected.add(o("wq",NT+0x230+0x48,0x0));
  expected.add(o("wq",CW-0x8,I+0x337C690L));
  expected.add(o("wq",M+0x8,NT+0x230));
  expected.add(o("wq",M-0x8,0x1));
  expected.add(o("rq",T+0x230+0x48,0x0));
  expected.add(o("rq",M+0x8,NT+0x230));
  expected.add(o("rq",M-0x8,0x1));
  expected.add(o("rq",M,I+0x337C690L));
  expected.add(o("rd",O+0x10,0x1));
  expected.add(o("wd",O+0x10,0x2));
  expected.add(o("wq",U+0x30,NT+0x230));
  expected.add(o("wb",U+0x38,0x1));
  expected.add(o("rq",C+0x10,K));
  expected.add(o("rq",C-0x38,en.r15Bits()));
  expected.add(o("rq",C-0x30,0x0));
  expected.add(o("rq",C-0x28,en.r13Bits()));
  expected.add(o("rq",C-0x20,0x2));
  expected.add(o("rq",C-0x18,O));
  expected.add(o("rq",C-0x10,T+0x230+0x48));
  expected.add(o("rq",C-0x8,T));
  expected.add(o("rq",C,I+0x337C19DL));
  expected.add(o("rq",T+0x230+0x48,0x0));
  // Literal source block: fixed-migration-2-actual201-and202adjacent
  expected.add(o("rb",T+0x280+0x4,0x2));
  expected.add(o("rd",T+0x280,0x17));
  expected.add(o("wq",U+0x20,U+0x68));
  expected.add(o("wb",U+0x68,0x0));
  expected.add(o("wq",U-0x8,I+0x337C19DL));
  expected.add(o("wq",C-0x8,T));
  expected.add(o("wq",C-0x10,T+0x280+0x48));
  expected.add(o("wq",C-0x18,O));
  expected.add(o("wq",C-0x20,0x1));
  expected.add(o("wq",C-0x28,en.r13Bits()));
  expected.add(o("wq",C-0x30,0x0));
  expected.add(o("wq",C-0x38,en.r15Bits()));
  expected.add(o("rd",O+0x14,0xF));
  expected.add(o("rq",O+0x8,NT));
  expected.add(o("rb",NT+0x230+0x4,0x1));
  expected.add(o("rq",T+0x288,KC));
  expected.add(o("rq",NT+0x238,KB));
  expected.add(o("rb",NT+0x284,0x1));
  expected.add(o("rb",O+0x18,0x6));
  expected.add(o("rd",O+0x10,0x2));
  expected.add(o("rd",O+0x1C,0x3F000000L));
  expected.add(o("rb",NT+0x280+0x4,0x1));
  expected.add(o("wq",C+0x10,K));
  expected.add(o("rd",NT+0x280,0x8));
  expected.add(o("rb",NT+0x2D4,0x0));
  expected.add(o("wd",NT+0x2D0,0x8));
  expected.add(o("wb",NT+0x2D4,0x2));
  expected.add(o("rq",NT+0x288,KA));
  expected.add(o("wq",NT+0x2D8,KA));
  expected.add(o("wq",NT+0x318,0x0));
  expected.add(o("wq",CW-0x8,I+0x337C6EFL));
  expected.add(o("wq",M+0x8,NT+0x280));
  expected.add(o("wq",M-0x8,0x2));
  expected.add(o("rq",NT+0x280+0x48,P));
  expected.add(o("wq",NT+0x2D0+0x48,P));
  expected.add(o("wq",NT+0x280+0x48,0x0));
  expected.add(o("rq",M+0x8,NT+0x280));
  expected.add(o("rq",M-0x8,0x2));
  expected.add(o("rq",M,I+0x337C6EFL));
  expected.add(o("wd",NT+0x280,0x17));
  expected.add(o("wb",NT+0x284,0x2));
  expected.add(o("wq",CW-0x8,I+0x337C701L));
  expected.add(o("wq",M+0x8,NT+0x280));
  expected.add(o("wq",M+0x10,O));
  expected.add(o("wq",M-0x8,0x2));
  expected.add(o("rq",T+0x288,KC));
  expected.add(o("wq",NT+0x288,KC));
  expected.add(o("rq",NT+0x2C8,0x0));
  expected.add(o("rq",T+0x2C8,0x0));
  expected.add(o("rq",M+0x10,O));
  expected.add(o("rq",M+0x8,NT+0x280));
  expected.add(o("rq",M-0x8,0x2));
  expected.add(o("rq",M,I+0x337C701L));
  expected.add(o("rd",O+0x10,0x2));
  expected.add(o("wd",O+0x10,0x3));
  expected.add(o("wq",U+0x30,NT+0x280));
  expected.add(o("wb",U+0x38,0x1));
  expected.add(o("rq",C+0x10,K));
  expected.add(o("rq",C-0x38,en.r15Bits()));
  expected.add(o("rq",C-0x30,0x0));
  expected.add(o("rq",C-0x28,en.r13Bits()));
  expected.add(o("rq",C-0x20,0x1));
  expected.add(o("rq",C-0x18,O));
  expected.add(o("rq",C-0x10,T+0x280+0x48));
  expected.add(o("rq",C-0x8,T));
  expected.add(o("rq",C,I+0x337C19DL));
  expected.add(o("rq",T+0x280+0x48,0x0));
  // Literal source block: secondgetter-free-C0return-and-root207
  expected.add(o("wq",U-0x8,I+0x337C1C8L));
  expected.add(o("rq",GSL,TLS));
  expected.add(o("rd",TLS+0x10,0x7));
  expected.add(o("rd",I+0x5C673D0L,0xFFFFFFFFL));
  expected.add(o("rq",U-0x8,I+0x337C1C8L));
  expected.add(o("rq",U+0x40,r14));
  expected.add(o("rq",U+0x48,OUT));
  expected.add(o("rq",U+0x60,T+0x2D0));
  expected.add(o("rq",O+0x20,OBJ));
  expected.add(o("rq",OBJ,VT));
  expected.add(o("rq",VT+0x10,FT));
  expected.add(o("wq",U-0x8,I+0x337C1EFL));
  expected.add(o("rq",U+0x70,B));
  expected.add(o("rq",Z-0x8,O));
  expected.add(o("rq",Z,I+0x337BB90L));
  expected.add(o("rq",E+0x30,DESC));
  expected.add(o("wq",W+0x28,DESC));
  expected.add(o("rd",E+0x18,0xF));
  expected.add(o("wq",W-0x8,I+0x337BBABL));
  // Literal source block: 207-empty-newhash15-normalreturn
  expected.add(o("wq",J+0x10,T+0x2D0));
  expected.add(o("wd",J+0x18,0xF));
  expected.add(o("wq",J-0x8,B));
  expected.add(o("wq",J-0x10,O));
  expected.add(o("wq",J-0x18,OUT));
  expected.add(o("wq",J-0x20,K));
  expected.add(o("wq",J-0x28,en.r13Bits()));
  expected.add(o("wq",J-0x30,r14));
  expected.add(o("wq",J-0x38,en.r15Bits()));
  expected.add(o("rd",O+0x14,0xF));
  expected.add(o("rq",O+0x8,NT));
  expected.add(o("rb",NT+0x4B4,0x0));
  expected.add(o("rb",O+0x18,0x6));
  expected.add(o("rd",O+0x10,0x3));
  expected.add(o("rd",O+0x1C,0x3F000000L));
  expected.add(o("rb",NT+0x4B4,0x0));
  expected.add(o("wd",NT+0x4B0,0xF));
  expected.add(o("wb",NT+0x4B4,0x1));
  expected.add(o("rq",K,KD));
  expected.add(o("wq",NT+0x4B8,KD));
  expected.add(o("wq",J+0x8,NT+0x4C0));
  expected.add(o("wq",NT+0x4F8,0x0));
  expected.add(o("rq",J+0x30,DESC));
  expected.add(o("rq",DESC+0x38,0x0));
  expected.add(o("rd",O+0x10,0x3));
  expected.add(o("wd",O+0x10,0x4));
  expected.add(o("wq",OUT,NT+0x4B0));
  expected.add(o("wb",OUT+0x8,0x1));
  expected.add(o("rq",J+0x10,T+0x2D0));
  expected.add(o("rq",J-0x38,en.r15Bits()));
  expected.add(o("rq",J-0x30,r14));
  expected.add(o("rq",J-0x28,en.r13Bits()));
  expected.add(o("rq",J-0x20,K));
  expected.add(o("rq",J-0x18,OUT));
  expected.add(o("rq",J-0x10,O));
  expected.add(o("rq",J-0x8,B));
  expected.add(o("rq",J,I+0x337BBABL));
  // Literal source block: whole199-freshNV-andRET
  expected.add(o("rq",E+0x10,en.rbxBits()));
  expected.add(o("rq",E-0x38,en.r15Bits()));
  expected.add(o("rq",E-0x30,en.r14Bits()));
  expected.add(o("rq",E-0x28,en.r13Bits()));
  expected.add(o("rq",E-0x20,en.r12Bits()));
  expected.add(o("rq",E-0x18,en.rdiBits()));
  expected.add(o("rq",E-0x10,en.rsiBits()));
  expected.add(o("rq",E-0x8,en.rbpBits()));
  expected.add(o("rq",E,RET));
  final List<F> fpExpected=List.of(
   new F(0,4,0,0x40800000,20),
   new F(0,7,0,0x40E00000,20),
   new F(1,0x40800000,0x40E00000,0x3F124925,20),
   new F(2,0x3F124925,0x3F000000,1,21),
   new F(0,15,0,0x41700000,85),
   new F(0,1,0,0x3F800000,85),
   new F(1,0x3F800000,0x41700000,0x3D888889,85),
   new F(2,0x3D888889,0x3F000000,0,86),
   new F(0,15,0,0x41700000,139),
   new F(0,2,0,0x40000000,139),
   new F(1,0x40000000,0x41700000,0x3E088889,139),
   new F(2,0x3E088889,0x3F000000,0,140),
   new F(0,15,0,0x41700000,188),
   new F(0,3,0,0x40400000,188),
   new F(1,0x40400000,0x41700000,0x3E4CCCCD,188),
   new F(2,0x3E4CCCCD,0x3F000000,0,189),
   new F(0,4,0,0x40800000,268),
   new F(0,15,0,0x41700000,268),
   new F(1,0x40800000,0x41700000,0x3E888889,268),
   new F(2,0x3E888889,0x3F000000,0,269)
  );
  final List<L> loops=List.of(
   new L(0x337B831L,T+0x230,14),
   new L(0x337B831L,T+0x280,16),
   new L(0x337C150L,NT+0x0,40),
   new L(0x337C150L,NT+0x50,41),
   new L(0x337C150L,NT+0xA0,42),
   new L(0x337C150L,NT+0xF0,43),
   new L(0x337C150L,NT+0x140,44),
   new L(0x337C150L,NT+0x190,45),
   new L(0x337C150L,NT+0x1E0,46),
   new L(0x337C150L,NT+0x230,47),
   new L(0x337C150L,NT+0x280,48),
   new L(0x337C150L,NT+0x2D0,49),
   new L(0x337C150L,NT+0x320,50),
   new L(0x337C150L,NT+0x370,51),
   new L(0x337C150L,NT+0x3C0,52),
   new L(0x337C150L,NT+0x410,53),
   new L(0x337C150L,NT+0x460,54),
   new L(0x337C150L,NT+0x4B0,55),
   new L(0x337C150L,NT+0x500,56),
   new L(0x337C150L,NT+0x550,57),
   new L(0x337C150L,NT+0x5A0,58),
   new L(0x337C150L,NT+0x5F0,59),
   new L(0x337C150L,NT+0x640,60),
   new L(0x337C150L,NT+0x690,61),
   new L(0x337C173L,T+0x0+0x48,68),
   new L(0x337C173L,T+0x98,116),
   new L(0x337C173L,T+0xE8,117),
   new L(0x337C173L,T+0x138,118),
   new L(0x337C173L,T+0x188,119),
   new L(0x337C173L,T+0x1D8,120),
   new L(0x337C173L,T+0x228,121),
   new L(0x337C173L,T+0x230+0x48,122),
   new L(0x337C173L,T+0x280+0x48,168),
   new L(0x337C615L,NT+0x230,184)
  );
  final int[] rootAt={22,24,254},opaqueAt={38,247},gsAt={64,236};
  final List<Call> rootExpected=List.of(new Call(0x337BB7CL,TargetKind.DIRECT_RVA,0x86E160L,W,capIn,rootN),new Call(0x337BB8BL,TargetKind.DIRECT_RVA,0x337C0C0L,W,c0In,rootN),new Call(0x337BBA6L,TargetKind.DIRECT_RVA,0x337C200L,W,childIn,rootN));
  final List<Call> opaqueExpected=List.of(new Call(0x337C12EL,TargetKind.INDIRECT_ABSOLUTE,AT,U,allocIn,allocN),new Call(0x337C1ECL,TargetKind.INDIRECT_ABSOLUTE,FT,U,freeIn,freeN));
  assertEquals(300,expected.size());assertEquals(34,loops.size());assertEquals(20,fpExpected.size());assertEquals(3,rootExpected.size());assertEquals(2,opaqueExpected.size());assertEquals(2,gsAt.length);
  final int[] counts=new int[5];
  final LoopBudget budget=(pc,row)->{int i=counts[0]++;assertTrue(i<loops.size(),"extra loop");assertEquals(loops.get(i),new L(pc,row,m.ops.size()));};
  final LoadRowReferenceCallee337b7e0199Api.Float32 fp=new LoadRowReferenceCallee337b7e0199Api.Float32(){
   private int take(int kind,int a,int b){int i=counts[1]++;assertTrue(i<fpExpected.size(),"extra FP");F f=fpExpected.get(i);assertEquals(new F(kind,a,b,f.result(),m.ops.size()),f);return f.result();}
   public int convertSignedDwordToFloatBits(int a){return take(0,a,0);}public int divideScalarFloatBits(int a,int b){return take(1,a,b);}public boolean orderedAbove(int a,int b){return take(2,a,b)!=0;}
  };
  final Ports ports=new Ports();ports.invoke=c->{int i=counts[2]++;assertTrue(i<opaqueExpected.size(),"extra opaque");assertEquals(opaqueExpected.get(i),c);assertEquals(opaqueAt[i],m.ops.size());return i==0?av:fv;};
  ports.gs=()->{int i=counts[3]++;assertTrue(i<gsAt.length,"extra GS");assertEquals(gsAt[i],m.ops.size());return GSL;};
  final Calls bound=LoadRowReferenceMigration246Calls.bind(I,m,ports,budget,fp);
  final Calls observeRoot=new Calls(){public VolatileBits invoke(Call c){int i=counts[4]++;assertTrue(i<rootExpected.size(),"extra rootCall");assertEquals(rootExpected.get(i),c);assertEquals(rootAt[i],m.ops.size());return bound.invoke(c);}public NormalReturn tail(Tail t){throw new AssertionError(t);}public long readGsQword58(){throw new AssertionError("root GS");}};
  m.ops.clear();final NormalReturn result=LoadRowReferenceCallee337b7e0199.execute(new Entry(I,E,iv,en),m,observeRoot,budget,fp);
  assertEquals(expected,m.ops);assertArrayEquals(new int[]{34,20,2,2,3},counts);
  final VolatileBits endV=new VolatileBits(OUT,0x0,OUT,0xF,K,fv.r10Bits(),fv.r11Bits(),new Bits128(0x41700000L,0x0),new Bits128(0x3E888889L,0x0),fv.xmm2(),fv.xmm3(),fv.xmm4(),fv.xmm5());assertEquals(new NormalReturn(endV,RET,E+0x8,en),result);
  oldImage.putQ(T+0x48,0x0);for(int j=0;j<0x16;j++)newImage.putB(NT+j*0x50+0x4,0x0);newImage.putB(NT+0x6E4,0xFF);
  final int[] finalRows={0x7,0x8,0x9,0xF},finalHashes={0x7,0x17,0x8,0xF},finalMarkers={0x1,0x2,0x2,0x1};final long[] finalKeys={KB,KC,KA,KD},finalPayloads={0x0,0x0,P,0x0};
  for(int j=0;j<0x4;j++){long a=NT+finalRows[j]*0x50L;newImage.putD(a,finalHashes[j]);newImage.putB(a+0x4,finalMarkers[j]);newImage.putQ(a+0x8,finalKeys[j]);newImage.putQ(a+0x48,finalPayloads[j]);}
  for(int j=-0x1;j<=0x730;j++)assertEquals(newImage.rawB(NT+j),m.rawB(NT+j),"new byte "+j);for(int j=-0x1;j<=0x460;j++)assertEquals(oldImage.rawB(T+j),m.rawB(T+j),"old byte "+j);
  assertEquals(NT,m.rawQ(O+0x8));assertEquals(4,m.rawD(O+0x10));assertEquals(15,m.rawD(O+0x14));assertEquals(6,m.rawB(O+0x18));assertEquals(0x3F000000,m.rawD(O+0x1C));assertEquals(OBJ,m.rawQ(O+0x20));
  assertEquals(NT+0x4B0,m.rawQ(OUT));assertEquals(1,m.rawB(OUT+0x8));for(int j=0x9;j<=0x10;j++)assertEquals(0xA5,m.rawB(OUT+j));assertEquals(0xA5,m.rawB(OUT-0x1));
  assertEquals(0x7F6E5D4C0000000FL,m.rawQ(E+0x18));assertEquals(K,m.rawQ(E+0x20));assertEquals((B&0xFFFFFFFF00000000L)|0xF,m.rawQ(J+0x18));assertEquals(RET,m.rawQ(E));assertEquals(0xF123456789ABCDEFL,m.rawQ(P));assertEquals(0xE23456789ABCDEF1L,m.rawQ(P+0x8));
 }
}
