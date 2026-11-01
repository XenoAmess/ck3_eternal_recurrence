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
public final class LoadRowReferencePopulatedGrowth246WitnessTest {
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
 @Test void whole199MigratesOneOwnedRowThenInsertsThrough246() {
  final long I=0x140000000L,E=0x800008L,P=E-0x118L,S=P-8L,W=S-0x58L,T=W-8L,U=T-0xC8L,Z=U-8L;
  final long M=0x210000L,O=0x220000L,K=0x230000L,C=0x240000L,A=0x250000L,VT=0x260000L;
  final long OLD=0x300000L,NEW=0x400000L,SENT=I+0x5C673E0L,GS=0x610000L,TLS=0x620000L;
  final long AT=0x123456789ABCDE00L,FT=0x23456789ABCDEF00L,OK=0x8A7B6C5D4E3F2011L,NK=0x9A8B7C6D5E4F3022L;
  final long RET=0x7FFF880012345678L,LEFT=0x8142434445464748L,RIGHT=0x9192939495969798L;
  Bytes m=new Bytes();NonvolatileBits en=n(0x6200000000000100L);
  VolatileBits b=v(0x5100000000000000L),ar=v(0x7300000000000200L),fr=v(0x8400000000000300L);
  VolatileBits ev=q(b,0xA100000000000123L,M,O,0x7777000000000001L,K,b.r10Bits(),b.r11Bits());
  VolatileBits av=q(ar,NEW,ar.rcxBits(),ar.rdxBits(),ar.r8Bits(),ar.r9Bits(),ar.r10Bits(),ar.r11Bits());
  for(int j=0;j<0xF0;j++)m.putB(OLD+j,0xA6);
  m.putD(OLD,0);m.putB(OLD+4,1);m.putQ(OLD+8,OK);m.putQ(OLD+0x48,0);m.putB(OLD+0x54,0);m.putB(OLD+0xA4,255);
  for(int j=0;j<0x460;j++)m.putB(NEW+j,0x6B);
  m.putQ(OLD-8,LEFT);m.putQ(OLD+0xF0,RIGHT);m.putQ(NEW-8,RIGHT);m.putQ(NEW+0x460,LEFT);
  m.putQ(M+8,OLD);m.putD(M+0x10,1);m.putD(M+0x14,0);m.putQ(M+0x18,0x3F80000044332201L);m.putQ(M+0x20,A);
  m.putQ(A,VT);m.putQ(VT+8,AT);m.putQ(VT+0x10,FT);m.putQ(K,NK);m.putQ(C+0x38,0);
  m.putQ(O,0x8172635445362718L);m.putQ(O+8,0x88776655443322A5L);
  m.putQ(GS,TLS);m.putD(TLS+0x10,0x80000001);m.putD(I+0x5C673D0L,0x80000000);
  m.putQ(E,RET);m.putQ(E+0x18,0xCAFEBABE90909090L);m.putQ(E+0x30,C);
  byte[] oldBytes=new byte[0xF0];for(int j=0;j<oldBytes.length;j++)oldBytes[j]=(byte)m.rawB(OLD+j);
  long r14=(en.r14Bits()&~0xFFL)|2L;
  NonvolatileBits active=new NonvolatileBits(OLD+0x50,E-0x4F,M,O,K,en.r13Bits(),r14,en.r15Bits(),en.xmm6());
  NonvolatileBits allocN=new NonvolatileBits(8,OLD,M,1,K,en.r13Bits(),0,en.r15Bits(),en.xmm6());
  NonvolatileBits freeN=new NonvolatileBits(OLD+0x50,OLD,M,O,K,en.r13Bits(),r14,en.r15Bits(),en.xmm6());
  List<Call> rootExpected=List.of(
   new Call(0x337BB7CL,TargetKind.DIRECT_RVA,0x86E160L,P,q(ev,NK,1,1,ev.r8Bits(),K,ev.r10Bits(),ev.r11Bits()),active),
   new Call(0x337BB8BL,TargetKind.DIRECT_RVA,0x337C0C0L,P,q(ev,3,M,3,0,1,ev.r10Bits(),ev.r11Bits()),active),
   new Call(0x337BBA6L,TargetKind.DIRECT_RVA,0x337C200L,P,q(fr,C,M,O,1,K,fr.r10Bits(),fr.r11Bits()),active));
  Call allocExpected=new Call(0x337C12EL,TargetKind.INDIRECT_ABSOLUTE,AT,W,q(ev,14,A,0x460,8,AT,ev.r10Bits(),ev.r11Bits()),allocN);
  VolatileBits freeInput=new VolatileBits(VT,A,OLD,8,OLD+8,0,av.r11Bits(),new Bits128(0x40E00000L,0),new Bits128(0x3E124925L,0),av.xmm2(),av.xmm3(),av.xmm4(),av.xmm5());
  Call freeExpected=new Call(0x337C1ECL,TargetKind.INDIRECT_ABSOLUTE,FT,W,freeInput,freeN);
  List<Op> expected=new ArrayList<>(List.of(
   o("wq",E+0x10,en.rbxBits()),o("wq",E+0x20,K),o("wd",E+0x18,1),
   o("wq",E-8,en.rbpBits()),o("wq",E-0x10,en.rsiBits()),o("wq",E-0x18,en.rdiBits()),o("wq",E-0x20,en.r12Bits()),
   o("wq",E-0x28,en.r13Bits()),o("wq",E-0x30,en.r14Bits()),o("wq",E-0x38,en.r15Bits()),
   o("rd",M+0x14,0),o("rq",M+8,OLD),o("rb",OLD+4,1),o("rq",K,NK),o("rq",OLD+8,OK),o("rb",OLD+0x54,0),o("rb",M+0x18,1),
   o("wq",P-8,I+0x337BB81L),o("rq",P-8,I+0x337BB81L),o("wq",P-8,I+0x337BB90L),
   o("wq",S-8,M),o("wq",W+0x60,OLD+0x50),o("wq",W+0x70,E-0x4F),o("rq",M+8,OLD),
   o("wb",M+0x18,5),o("rq",M+0x20,A),o("wq",W+0x48,O),o("rd",M+0x10,1),o("wq",W+0x40,r14),
   o("wd",M+0x14,7),o("wd",M+0x10,0),o("rq",A,VT),o("rq",VT+8,AT),o("wq",W-8,I+0x337C131L),o("rb",M+0x18,5),o("wq",M+8,NEW)));
  List<Op> budgetExpected=new ArrayList<>(List.of(o("budget",0x337B831L,OLD)));
  for(int j=0;j<13;j++){expected.add(o("wb",NEW+j*0x50L+4,0));budgetExpected.add(o("budget",0x337C150L,NEW+j*0x50L));}
  budgetExpected.add(o("budget",0x337C173L,OLD+0x48));
  expected.addAll(List.of(
   o("wb",NEW+0x414,255),o("wq",W-8,I+0x337C166L),o("rq",GS,TLS),o("rd",TLS+0x10,0x80000001L),o("rd",I+0x5C673D0L,0x80000000L),o("rq",W-8,I+0x337C166L),
   o("rb",OLD+4,1),o("rd",OLD,0),o("wq",W+0x20,W+0x68),o("wb",W+0x68,0),o("wq",W-8,I+0x337C19DL),
   o("wq",T-8,OLD),o("wq",T-0x10,OLD+0x48),o("wq",T-0x18,M),o("wq",T-0x20,1),o("wq",T-0x28,en.r13Bits()),o("wq",T-0x30,0),o("wq",T-0x38,en.r15Bits()),
   o("rd",M+0x14,7),o("rq",M+8,NEW),o("rb",NEW+4,0),o("rb",M+0x18,5),o("rd",M+0x10,0),o("rd",M+0x1C,0x3F800000),o("rb",NEW+4,0),
   o("wq",U+0xD8,K),o("wd",NEW,0),o("wb",NEW+4,1),o("rq",OLD+8,OK),o("wq",NEW+8,OK),o("wq",NEW+0x48,0),o("wq",U-8,I+0x337C690L),
   o("wq",Z+8,NEW),o("wq",Z-8,1),o("rq",OLD+0x48,0),o("rq",Z+8,NEW),o("rq",Z-8,1),o("rq",Z,I+0x337C690L),
   o("rd",M+0x10,0),o("wd",M+0x10,1),o("wq",W+0x30,NEW),o("wb",W+0x38,1),o("rq",U+0xD8,K),
   o("rq",T-0x38,en.r15Bits()),o("rq",T-0x30,0),o("rq",T-0x28,en.r13Bits()),o("rq",T-0x20,1),o("rq",T-0x18,M),o("rq",T-0x10,OLD+0x48),o("rq",T-8,OLD),o("rq",T,I+0x337C19DL),
   o("rq",OLD+0x48,0),o("wq",W-8,I+0x337C1C8L),o("rq",GS,TLS),o("rd",TLS+0x10,0x80000001L),o("rd",I+0x5C673D0L,0x80000000L),o("rq",W-8,I+0x337C1C8L),
   o("rq",W+0x40,r14),o("rq",W+0x48,O),o("rq",W+0x60,OLD+0x50),o("rq",M+0x20,A),o("rq",A,VT),o("rq",VT+0x10,FT),o("wq",W-8,I+0x337C1EFL),
   o("rq",W+0x70,E-0x4F),o("rq",S-8,M),o("rq",S,I+0x337BB90L),
   o("rq",E+0x30,C),o("wq",P+0x28,C),o("rd",E+0x18,1),o("wq",P-8,I+0x337BBABL),
   o("wq",S+0x10,OLD+0x50),o("wd",S+0x18,1),o("wq",S-8,E-0x4F),o("wq",S-0x10,M),o("wq",S-0x18,O),o("wq",S-0x20,K),
   o("wq",S-0x28,en.r13Bits()),o("wq",S-0x30,r14),o("wq",S-0x38,en.r15Bits()),
   o("rd",M+0x14,7),o("rq",M+8,NEW),o("rb",NEW+0x54,0),o("rb",M+0x18,5),o("rd",M+0x10,1),o("rd",M+0x1C,0x3F800000),o("rb",NEW+0x54,0),
   o("wd",NEW+0x50,1),o("wb",NEW+0x54,1),o("rq",K,NK),o("wq",NEW+0x58,NK),o("wq",S+8,NEW+0x60),o("wq",NEW+0x98,0),
   o("rq",S+0x30,C),o("rq",C+0x38,0),o("rd",M+0x10,1),o("wd",M+0x10,2),o("wq",O,NEW+0x50),o("wb",O+8,1),
   o("rq",S+0x10,OLD+0x50),o("rq",S-0x38,en.r15Bits()),o("rq",S-0x30,r14),o("rq",S-0x28,en.r13Bits()),o("rq",S-0x20,K),o("rq",S-0x18,O),o("rq",S-0x10,M),o("rq",S-8,E-0x4F),o("rq",S,I+0x337BBABL),
   o("rq",E+0x10,en.rbxBits()),o("rq",E-0x38,en.r15Bits()),o("rq",E-0x30,en.r14Bits()),o("rq",E-0x28,en.r13Bits()),o("rq",E-0x20,en.r12Bits()),o("rq",E-0x18,en.rdiBits()),o("rq",E-0x10,en.rsiBits()),o("rq",E-8,en.rbpBits()),o("rq",E,RET)));
  assertEquals(166,expected.size());assertEquals(15,budgetExpected.size());assertEquals(3,rootExpected.size());assertTrue(m.ops.isEmpty());
  List<Call> rootSeen=new ArrayList<>(),opaqueSeen=new ArrayList<>();List<Op> budgets=new ArrayList<>();List<String> fp=new ArrayList<>();int[] gsCount={0};
  Ports original=new Ports();original.invoke=c->{
   int ix=opaqueSeen.size();assertTrue(ix<2);assertEquals(ix==0?allocExpected:freeExpected,c);assertEquals(ix==0?34:113,m.ops.size());
   assertEquals(I+(ix==0?0x337C131L:0x337C1EFL),m.rawQ(W-8));opaqueSeen.add(c);return ix==0?av:fr;
  };
  original.gs=()->{assertTrue(gsCount[0]<2);assertEquals(gsCount[0]++==0?51:102,m.ops.size());return GS;};
  LoopBudget budget=(header,cursor)->{Op got=o("budget",header,cursor);assertEquals(budgetExpected.get(budgets.size()),got);budgets.add(got);};
  LoadRowReferenceCallee337b7e0199Api.Float32 floating=new LoadRowReferenceCallee337b7e0199Api.Float32(){
   public int convertSignedDwordToFloatBits(int a){int ix=fp.size();assertTrue(ix==0||ix==1||ix==4||ix==5);assertEquals(ix<4?72:134,m.ops.size());int want=ix==0||ix==5?7:ix==1?1:2;assertEquals(want,a);fp.add("c:"+a);return a==7?0x40E00000:a==1?0x3F800000:0x40000000;}
   public int divideScalarFloatBits(int a,int b){int ix=fp.size();assertTrue(ix==2||ix==6);assertEquals(ix==2?72:134,m.ops.size());assertEquals(ix==2?0x3F800000:0x40000000,a);assertEquals(0x40E00000,b);fp.add("div");return ix==2?0x3E124925:0x3E924925;}
   public boolean orderedAbove(int a,int b){int ix=fp.size();assertTrue(ix==3||ix==7);assertEquals(ix==3?73:135,m.ops.size());assertEquals(ix==3?0x3E124925:0x3E924925,a);assertEquals(0x3F800000,b);fp.add("above");return false;}
  };
  Calls graph=LoadRowReferenceMigration246Calls.bind(I,m,original,budget,floating);
  Ports observedRoot=new Ports();observedRoot.invoke=c->{assertEquals(rootExpected.get(rootSeen.size()),c);rootSeen.add(c);return graph.invoke(c);};
  NormalReturn result=LoadRowReferenceCallee337b7e0199.execute(new Entry(I,E,ev,en),m,observedRoot,budget,floating);
  VolatileBits fv=new VolatileBits(O,0,O,1,K,fr.r10Bits(),fr.r11Bits(),new Bits128(0x40E00000L,0),new Bits128(0x3E924925L,0),fr.xmm2(),fr.xmm3(),fr.xmm4(),fr.xmm5());
  assertEquals(new NormalReturn(fv,RET,E+8,en),result);assertEquals(expected,m.ops);assertEquals(rootExpected,rootSeen);assertEquals(List.of(allocExpected,freeExpected),opaqueSeen);
  assertEquals(budgetExpected,budgets);assertEquals(List.of("c:7","c:1","div","above","c:2","c:7","div","above"),fp);assertEquals(2,gsCount[0]);
  assertEquals(NEW,m.rawQ(M+8));assertEquals(2,m.rawD(M+0x10));assertEquals(7,m.rawD(M+0x14));assertEquals(0x3F80000044332205L,m.rawQ(M+0x18));assertEquals(A,m.rawQ(M+0x20));
  assertEquals(NEW+0x50,m.rawQ(O));assertEquals(0x8877665544332201L,m.rawQ(O+8));assertEquals(0xCAFEBABE00000001L,m.rawQ(E+0x18));assertEquals(K,m.rawQ(E+0x20));assertEquals(C,m.rawQ(E+0x30));
  assertEquals(LEFT,m.rawQ(OLD-8));assertEquals(RIGHT,m.rawQ(OLD+0xF0));assertEquals(RIGHT,m.rawQ(NEW-8));assertEquals(LEFT,m.rawQ(NEW+0x460));
  for(int j=0;j<oldBytes.length;j++)assertEquals(Byte.toUnsignedInt(oldBytes[j]),m.rawB(OLD+j));
  for(int j=0;j<0x460;j++){
   int want=0x6B;
   if(j<4)want=0;
   else if(j==4||j==0x54)want=1;
   else if(j>=8&&j<16)want=(int)(OK>>>(8*(j-8)))&255;
   else if(j>=0x48&&j<0x50||j>=0x98&&j<0xA0)want=0;
   else if(j>=0x50&&j<0x54)want=j==0x50?1:0;
   else if(j>=0x58&&j<0x60)want=(int)(NK>>>(8*(j-0x58)))&255;
   else if(j%0x50==4)want=j/0x50==13?255:0;
   assertEquals(want,m.rawB(NEW+j),"owned new byte "+j);
  }
 }
}
