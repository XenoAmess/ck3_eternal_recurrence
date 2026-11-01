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
public final class LoadRowReferencePopulatedGrowth247WitnessTest {
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

 @Test void whole199MovesPayloadAcrossTwoOldRowsThenInserts247() {
  final long I=0x180000000L,E=0x1000000L,O=0x2000000L,T=0x3000000L,A=0x4000000L,Y=0x5000000L,K=0x6000000L,DESC=0x6100000L;
  final long OBJ=0x7000000L,VT=0x7100000L,GS=0x8000000L,TLS=0x8100000L;
  final long PAY=0x8A0000005010L,AT=0x8B0000006010L,FT=0x8C0000007010L,RET=0x8D0000008010L;
  final long K0=0x1020304050607080L,K1=0x8877665544332211L,KN=0x1718191A1B1C1D1EL,H=0xABCDEF0100000002L;
  final long W=E-0x118L,Z=W-8,U=Z-0x58L,C=U-8,CW=C-0xC8L,M=CW-8,BP=E-0x4FL,CBP=C-0x57L,J=W-8,JW=J-0x118L;
  final long CO=U+0x30L,FLAG=U+0x68L;
  final NonvolatileBits en=n(0xB100000000000100L);
  final long r14two=(en.r14Bits()&~255L)|2L;
  final VolatileBits iv=q(v(0xA100000000000100L),0xA111111111111111L,O,Y,H,K,0xA122222222222222L,0xA133333333333333L);
  final VolatileBits av=q(v(0xA200000000000100L),A,0xA244444444444444L,0xA255555555555555L,0xA266666666666666L,0xA277777777777777L,0xA288888888888888L,0xA299999999999999L);
  final VolatileBits fv=v(0xA300000000000100L);
  final NonvolatileBits rn=new NonvolatileBits(T+0x50,BP,O,Y,K,en.r13Bits(),r14two,en.r15Bits(),en.xmm6());
  final NonvolatileBits an=new NonvolatileBits(8,T,O,2,K,en.r13Bits(),0,en.r15Bits(),en.xmm6());
  final NonvolatileBits fn=new NonvolatileBits(T+0x50,T,O,Y,K,en.r13Bits(),r14two,en.r15Bits(),en.xmm6());
  final VolatileBits cap=q(iv,3,2,31,1,1,iv.r10Bits(),iv.r11Bits());
  final VolatileBits childIn=q(fv,DESC,O,Y,2,K,fv.r10Bits(),fv.r11Bits());
  final VolatileBits resultV=new VolatileBits(Y,0,Y,2,K,fv.r10Bits(),fv.r11Bits(),new Bits128(0x40E00000L,0),new Bits128(0x3EDB6DB7L,0),fv.xmm2(),fv.xmm3(),fv.xmm4(),fv.xmm5());
  Bytes m=new Bytes();
  m.putQ(E,RET);m.putQ(E+0x30,DESC);m.putD(E+0x1C,0xCAFEBABE);
  m.putQ(O+8,T);m.putD(O+0x10,2);m.putD(O+0x14,1);m.putB(O+0x18,1);m.putD(O+0x1C,0x3F800000);m.putQ(O+0x20,OBJ);
  m.putD(T,0);m.putB(T+4,1);m.putQ(T+8,K0);m.putQ(T+0x48,PAY);
  m.putD(T+0x50,1);m.putB(T+0x54,1);m.putQ(T+0x58,K1);m.putQ(T+0x98,0);m.putB(T+0xA4,0);
  m.putQ(K,KN);m.putQ(DESC+0x38,0);m.putQ(OBJ,VT);m.putQ(VT+8,AT);m.putQ(VT+0x10,FT);
  m.putQ(GS,TLS);m.putD(TLS+0x10,7);m.putD(I+0x5C673D0,-1);m.putQ(PAY,0xE123456789ABCDEFL);
  byte[] oldBefore=new byte[320];for(int i=0;i<320;i++)oldBefore[i]=(byte)m.rawB(T+i);
  List<Op> e=new ArrayList<>();
  // Whole199 prologue and the real mismatch/limit path to Capacity and C0.
  e.addAll(List.of(o("wq",E+0x10,en.rbxBits()),o("wq",E+0x20,K),o("wd",E+0x18,2),o("wq",E-8,en.rbpBits()),o("wq",E-0x10,en.rsiBits()),o("wq",E-0x18,en.rdiBits()),o("wq",E-0x20,en.r12Bits()),o("wq",E-0x28,en.r13Bits()),o("wq",E-0x30,en.r14Bits()),o("wq",E-0x38,en.r15Bits()),
   o("rd",O+0x14,1),o("rq",O+8,T),o("rb",T+4,1),o("rq",K,KN),o("rq",T+8,K0),o("rb",T+0x54,1),o("rb",O+0x18,1),o("wq",W-8,I+0x337BB81L),o("rq",W-8,I+0x337BB81L),o("wq",W-8,I+0x337BB90L)));
  // C0 owns its frame; allocator is opaque but the returned table is already owned RAM.
  e.addAll(List.of(o("wq",Z-8,O),o("wq",U+0x60,T+0x50),o("wq",U+0x70,BP),o("rq",O+8,T),o("wb",O+0x18,5),o("rq",O+0x20,OBJ),o("wq",U+0x48,Y),o("rd",O+0x10,2),o("wq",U+0x40,r14two),o("wd",O+0x14,7),o("wd",O+0x10,0),o("rq",OBJ,VT),o("rq",VT+8,AT),o("wq",U-8,I+0x337C131L),o("rb",O+0x18,5),o("wq",O+8,A)));
  for(int i=0;i<13;i++)e.add(o("wb",A+80L*i+4,0));
  e.addAll(List.of(o("wb",A+1044,255),o("wq",U-8,I+0x337C166L),o("rq",GS,TLS),o("rd",TLS+0x10,7),o("rd",I+0x5C673D0,0xFFFFFFFFL),o("rq",U-8,I+0x337C166L)));
  // First original occupied row -> actual C5 -> actual201 direct move, not a callback.
  e.addAll(List.of(o("rb",T+4,1),o("rd",T,0),o("wq",U+0x20,FLAG),o("wb",FLAG,0),o("wq",U-8,I+0x337C19DL),
   o("wq",C-8,T),o("wq",C-0x10,T+0x48),o("wq",C-0x18,O),o("wq",C-0x20,2),o("wq",C-0x28,en.r13Bits()),o("wq",C-0x30,0),o("wq",C-0x38,en.r15Bits()),
   o("rd",O+0x14,7),o("rq",O+8,A),o("rb",A+4,0),o("rb",O+0x18,5),o("rd",O+0x10,0),o("rd",O+0x1C,0x3F800000),o("rb",A+4,0),o("wq",CW+0xD8,K),
   o("wd",A,0),o("wb",A+4,1),o("rq",T+8,K0),o("wq",A+8,K0),o("wq",A+0x48,0),o("wq",CW-8,I+0x337C690L),
   o("wq",M+8,A),o("wq",M-8,1),o("rq",T+0x48,PAY),o("wq",A+0x48,PAY),o("wq",T+0x48,0),o("rq",M+8,A),o("rq",M-8,1),o("rq",M,I+0x337C690L),
   o("rd",O+0x10,0),o("wd",O+0x10,1),o("wq",CO,A),o("wb",CO+8,1),o("rq",CW+0xD8,K),o("rq",C-0x38,en.r15Bits()),o("rq",C-0x30,0),o("rq",C-0x28,en.r13Bits()),o("rq",C-0x20,2),o("rq",C-0x18,O),o("rq",C-0x10,T+0x48),o("rq",C-8,T),o("rq",C,I+0x337C19DL),o("rq",T+0x48,0)));
  // Second original occupied row -> separate actual C5 empty slot and actual201 null path.
  e.addAll(List.of(o("rb",T+0x54,1),o("rd",T+0x50,1),o("wq",U+0x20,FLAG),o("wb",FLAG,0),o("wq",U-8,I+0x337C19DL),
   o("wq",C-8,T),o("wq",C-0x10,T+0x98),o("wq",C-0x18,O),o("wq",C-0x20,1),o("wq",C-0x28,en.r13Bits()),o("wq",C-0x30,0),o("wq",C-0x38,en.r15Bits()),
   o("rd",O+0x14,7),o("rq",O+8,A),o("rb",A+0x54,0),o("rb",O+0x18,5),o("rd",O+0x10,1),o("rd",O+0x1C,0x3F800000),o("rb",A+0x54,0),o("wq",CW+0xD8,K),
   o("wd",A+0x50,1),o("wb",A+0x54,1),o("rq",T+0x58,K1),o("wq",A+0x58,K1),o("wq",A+0x98,0),o("wq",CW-8,I+0x337C690L),
   o("wq",M+8,A+0x50),o("wq",M-8,1),o("rq",T+0x98,0),o("rq",M+8,A+0x50),o("rq",M-8,1),o("rq",M,I+0x337C690L),
   o("rd",O+0x10,1),o("wd",O+0x10,2),o("wq",CO,A+0x50),o("wb",CO+8,1),o("rq",CW+0xD8,K),o("rq",C-0x38,en.r15Bits()),o("rq",C-0x30,0),o("rq",C-0x28,en.r13Bits()),o("rq",C-0x20,1),o("rq",C-0x18,O),o("rq",C-0x10,T+0x98),o("rq",C-8,T),o("rq",C,I+0x337C19DL),o("rq",T+0x98,0)));
  // Getter and actual old-table free; no payload destructor after201 cleared source.
  e.addAll(List.of(o("wq",U-8,I+0x337C1C8L),o("rq",GS,TLS),o("rd",TLS+0x10,7),o("rd",I+0x5C673D0,0xFFFFFFFFL),o("rq",U-8,I+0x337C1C8L),o("rq",U+0x40,r14two),o("rq",U+0x48,Y),o("rq",U+0x60,T+0x50),o("rq",O+0x20,OBJ),o("rq",OBJ,VT),o("rq",VT+0x10,FT),o("wq",U-8,I+0x337C1EFL),o("rq",U+0x70,BP),o("rq",Z-8,O),o("rq",Z,I+0x337BB90L),
   o("rq",E+0x30,DESC),o("wq",W+0x28,DESC),o("rd",E+0x18,2),o("wq",W-8,I+0x337BBABL)));
  // Real207 receives a fresh physical child frame and inserts the third distinct key.
  e.addAll(List.of(o("wq",J+0x10,T+0x50),o("wd",J+0x18,2),o("wq",J-8,BP),o("wq",J-0x10,O),o("wq",J-0x18,Y),o("wq",J-0x20,K),o("wq",J-0x28,en.r13Bits()),o("wq",J-0x30,r14two),o("wq",J-0x38,en.r15Bits()),
   o("rd",O+0x14,7),o("rq",O+8,A),o("rb",A+0xA4,0),o("rb",O+0x18,5),o("rd",O+0x10,2),o("rd",O+0x1C,0x3F800000),o("rb",A+0xA4,0),o("wd",A+0xA0,2),o("wb",A+0xA4,1),o("rq",K,KN),o("wq",A+0xA8,KN),o("wq",J+8,A+0xB0),o("wq",A+0xE8,0),o("rq",J+0x30,DESC),o("rq",DESC+0x38,0),o("rd",O+0x10,2),o("wd",O+0x10,3),o("wq",Y,A+0xA0),o("wb",Y+8,1),
   o("rq",J+0x10,T+0x50),o("rq",J-0x38,en.r15Bits()),o("rq",J-0x30,r14two),o("rq",J-0x28,en.r13Bits()),o("rq",J-0x20,K),o("rq",J-0x18,Y),o("rq",J-0x10,O),o("rq",J-8,BP),o("rq",J,I+0x337BBABL),
   o("rq",E+0x10,en.rbxBits()),o("rq",E-0x38,en.r15Bits()),o("rq",E-0x30,en.r14Bits()),o("rq",E-0x28,en.r13Bits()),o("rq",E-0x20,en.r12Bits()),o("rq",E-0x18,en.rdiBits()),o("rq",E-0x10,en.rsiBits()),o("rq",E-8,en.rbpBits()),o("rq",E,RET)));
  assertEquals(214,e.size(),"independent source operation count before execute");
  List<Op> expectedBudget=new ArrayList<>();expectedBudget.add(o("budget",0x337B831L,T));
  for(int i=0;i<13;i++)expectedBudget.add(o("budget",0x337C150L,A+80L*i));
  expectedBudget.add(o("budget",0x337C173L,T+0x48));expectedBudget.add(o("budget",0x337C173L,T+0x98));
  List<Op> budgets=new ArrayList<>();
  LoopBudget budget=(header,cursor)->{
   int at=budgets.size();assertTrue(at<16);assertEquals(expectedBudget.get(at),o("budget",header,cursor));
   int ramIndex=at==0?e.indexOf(o("rq",T+8,K0)):at<=13?e.indexOf(o("wb",A+80L*(at-1)+4,0)):e.lastIndexOf(o("rb",at==14?T+4:T+0x54,1));
   assertEquals(ramIndex,m.ops.size(),"budget must precede source RAM event");budgets.add(o("budget",header,cursor));
  };
  List<Integer> comparisonReads=new ArrayList<>();for(int i=0;i<e.size();i++)if(e.get(i).equals(o("rd",O+0x1C,0x3F800000)))comparisonReads.add(i);
  assertEquals(3,comparisonReads.size());final int[] fp={0};
  LoadRowReferenceCallee337b7e0199Api.Float32 floating=new LoadRowReferenceCallee337b7e0199Api.Float32(){
   public int convertSignedDwordToFloatBits(int value){int at=fp[0]++;int expected=switch(at){case 0,4,9->7;case 1->1;case 5->2;case 8->3;default->throw new AssertionError(at);};assertEquals(expected,value);assertEquals(comparisonReads.get(at/4).intValue(),m.ops.size());return switch(value){case 1->0x3F800000;case 2->0x40000000;case 3->0x40400000;case 7->0x40E00000;default->throw new AssertionError(value);};}
   public int divideScalarFloatBits(int left,int right){int at=fp[0]++;assertTrue(at==2||at==6||at==10);assertEquals(at==2?0x3F800000:at==6?0x40000000:0x40400000,left);assertEquals(0x40E00000,right);assertEquals(comparisonReads.get(at/4).intValue(),m.ops.size());return at==2?0x3E124925:at==6?0x3E924925:0x3EDB6DB7;}
   public boolean orderedAbove(int left,int right){int at=fp[0]++;assertTrue(at==3||at==7||at==11);assertEquals(at==3?0x3E124925:at==7?0x3E924925:0x3EDB6DB7,left);assertEquals(0x3F800000,right);assertEquals(comparisonReads.get(at/4)+1,m.ops.size());return false;}
  };
  final int[] opaque={0},gs={0},roots={0};Ports original=new Ports();
  original.gs=()->{assertTrue(gs[0]++<2);return GS;};
  original.invoke=c->{
   if(opaque[0]++==0){expectCall(c,0x337C12EL,TargetKind.INDIRECT_ABSOLUTE,AT,U,q(iv,14,OBJ,1120,8,AT,iv.r10Bits(),iv.r11Bits()),an);assertEquals(I+0x337C131L,m.rawQ(U-8));return av;}
   assertEquals(2,opaque[0]);
   VolatileBits freeV=new VolatileBits(VT,OBJ,T,8,T+0x58,1,av.r11Bits(),new Bits128(0x40E00000L,0),new Bits128(0x3E924925L,0),av.xmm2(),av.xmm3(),av.xmm4(),av.xmm5());
   expectCall(c,0x337C1ECL,TargetKind.INDIRECT_ABSOLUTE,FT,U,freeV,fn);assertEquals(I+0x337C1EFL,m.rawQ(U-8));return fv;
  };
  Calls actual=LoadRowReferenceMigration246Calls.bind(I,m,original,budget,floating);Ports root=new Ports();root.gs=actual::readGsQword58;root.tail=actual::tail;
  root.invoke=c->{int at=roots[0]++;assertTrue(at<3);if(at==0)expectCall(c,0x337BB7CL,TargetKind.DIRECT_RVA,0x86E160L,W,q(iv,KN,2,1,H,K,iv.r10Bits(),iv.r11Bits()),rn);else if(at==1)expectCall(c,0x337BB8BL,TargetKind.DIRECT_RVA,0x337C0C0L,W,q(cap,3,O,3,1,1,iv.r10Bits(),iv.r11Bits()),rn);else expectCall(c,0x337BBA6L,TargetKind.DIRECT_RVA,0x337C200L,W,childIn,rn);assertEquals(I+(at==0?0x337BB81L:at==1?0x337BB90L:0x337BBABL),m.rawQ(W-8));VolatileBits reply=actual.invoke(c);assertEquals(at==0?cap:at==1?fv:resultV,reply);return reply;};
  NormalReturn result=LoadRowReferenceCallee337b7e0199.execute(new Entry(I,E,iv,en),m,root,budget,floating);
  assertEquals(new NormalReturn(resultV,RET,E+8,en),result);assertEquals(e,m.ops);assertEquals(214,m.ops.size());assertEquals(expectedBudget,budgets);assertEquals(16,budgets.size());assertEquals(12,fp[0]);assertEquals(3,roots[0]);assertEquals(2,opaque[0]);assertEquals(2,gs[0]);
  assertEquals(A,m.rawQ(O+8));assertEquals(3,m.rawD(O+0x10));assertEquals(7,m.rawD(O+0x14));assertEquals(5,m.rawB(O+0x18));assertEquals(0xA5A5A5L,m.raw(O+0x19,3));assertEquals(0x3F800000,m.rawD(O+0x1C));assertEquals(OBJ,m.rawQ(O+0x20));
  Bytes expectedNew=new Bytes();for(int i=0;i<13;i++)expectedNew.putB(A+80L*i+4,0);expectedNew.putB(A+1044,255);
  expectedNew.putD(A,0);expectedNew.putB(A+4,1);expectedNew.putQ(A+8,K0);expectedNew.putQ(A+0x48,PAY);
  expectedNew.putD(A+0x50,1);expectedNew.putB(A+0x54,1);expectedNew.putQ(A+0x58,K1);expectedNew.putQ(A+0x98,0);
  expectedNew.putD(A+0xA0,2);expectedNew.putB(A+0xA4,1);expectedNew.putQ(A+0xA8,KN);expectedNew.putQ(A+0xE8,0);
  for(int i=0;i<1120;i++)assertEquals(expectedNew.rawB(A+i),m.rawB(A+i),"new byte "+i);
  for(int i=0;i<320;i++)assertEquals(i>=0x48&&i<0x50?0:Byte.toUnsignedInt(oldBefore[i]),m.rawB(T+i),"old byte "+i);
  assertEquals(0xA5,m.rawB(A-1));assertEquals(0xA5,m.rawB(A+1120));assertEquals(0xA5,m.rawB(T-1));assertEquals(0xA5,m.rawB(T+320));
  assertEquals(A+0xA0,m.rawQ(Y));assertEquals(1,m.rawB(Y+8));assertEquals(0xA5A5A5A5A5A5A5L,m.raw(Y+9,7));assertEquals(0xCAFEBABE,m.rawD(E+0x1C));assertEquals(H&0xFFFFFFFFL,m.raw(E+0x18,4));assertEquals(K,m.rawQ(E+0x20));assertEquals(DESC,m.rawQ(E+0x30));assertEquals(0xE123456789ABCDEFL,m.rawQ(PAY));
 }

}
