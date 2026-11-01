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
public final class LoadRowReferenceGrowth244WitnessTest {
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
 @Test void whole199GrowsThroughRealCapacityGettersAndEmptyChild() {
  final long I=0x140000000L,E=0x800008L,P=E-0x118L,S=P-8L,W=S-0x58L,CW=S-0x118L;
  final long M=0x210000L,O=0x220000L,K=0x230000L,C=0x240000L,A=0x250000L,VT=0x260000L;
  final long OLD=I+0x5C673E0L,NEW=0x400000L,GS=0x610000L,TLS=0x620000L;
  final long TARGET=0x123456789ABCDE00L,KEY=0x8A7B6C5D4E3F2011L,RET=0x7FFF880012345678L;
  final long PAD=0x88776655443322A5L,LEFT=0x8142434445464748L,RIGHT=0x9192939495969798L;
  Bytes m=new Bytes();
  NonvolatileBits en=n(0x6200000000000100L);
  VolatileBits ev0=v(0x5100000000000000L);
  VolatileBits ev=q(ev0,0xA100000000000123L,M,O,0x7777000000000000L,K,ev0.r10Bits(),ev0.r11Bits());
  VolatileBits av0=v(0x7300000000000200L);
  VolatileBits av=q(av0,NEW,av0.rcxBits(),av0.rdxBits(),av0.r8Bits(),av0.r9Bits(),av0.r10Bits(),av0.r11Bits());
  for(int j=0;j<80;j++)m.putB(OLD+j,0xA6);
  m.putB(OLD+4,0);
  for(int j=0;j<0x460;j++)m.putB(NEW+j,0x6B);
  m.putQ(NEW-8,LEFT);m.putQ(NEW+0x460,RIGHT);
  m.putQ(M+8,OLD);m.putD(M+0x10,0);m.putD(M+0x14,0);
  m.putQ(M+0x18,0x3F80000044332200L);m.putQ(M+0x20,A);
  m.putQ(A,VT);m.putQ(VT+8,TARGET);m.putQ(K,KEY);m.putQ(C+0x38,0);
  m.putQ(O,0x8172635445362718L);m.putQ(O+8,PAD);
  m.putQ(GS,TLS);m.putD(TLS+0x10,0x80000001);m.putD(I+0x5C673D0L,0x80000000);
  m.putQ(E,RET);m.putQ(E+0x18,0xCAFEBABE90909090L);m.putQ(E+0x30,C);
  byte[] oldBytes=new byte[80];for(int j=0;j<80;j++)oldBytes[j]=(byte)m.rawB(OLD+j);
  long r14=(en.r14Bits()&~0xFFL)|1L;
  NonvolatileBits active=new NonvolatileBits(OLD,E-0x4F,M,O,K,en.r13Bits(),r14,en.r15Bits(),en.xmm6());
  NonvolatileBits allocN=new NonvolatileBits(8,OLD,M,0,K,en.r13Bits(),0,en.r15Bits(),en.xmm6());
  List<Call> rootExpected=List.of(
   new Call(0x337BB7CL,TargetKind.DIRECT_RVA,0x86E160L,P,q(ev,0,1,1,ev.r8Bits(),K,ev.r10Bits(),ev.r11Bits()),active),
   new Call(0x337BB8BL,TargetKind.DIRECT_RVA,0x337C0C0L,P,q(ev,3,M,3,0,1,ev.r10Bits(),ev.r11Bits()),active),
   new Call(0x337BBA6L,TargetKind.DIRECT_RVA,0x337C200L,P,q(av,C,M,O,0,K,av.r10Bits(),av.r11Bits()),active));
  Call allocExpected=new Call(0x337C12EL,TargetKind.INDIRECT_ABSOLUTE,TARGET,W,q(ev,14,A,0x460,8,TARGET,ev.r10Bits(),ev.r11Bits()),allocN);
  List<Op> expected=new ArrayList<>(List.of(
   o("wq",E+0x10,en.rbxBits()),o("wq",E+0x20,K),o("wd",E+0x18,0),
   o("wq",E-8,en.rbpBits()),o("wq",E-0x10,en.rsiBits()),o("wq",E-0x18,en.rdiBits()),
   o("wq",E-0x20,en.r12Bits()),o("wq",E-0x28,en.r13Bits()),o("wq",E-0x30,en.r14Bits()),o("wq",E-0x38,en.r15Bits()),
   o("rd",M+0x14,0),o("rq",M+8,OLD),o("rb",OLD+4,0),o("rb",M+0x18,0),
   o("wq",P-8,I+0x337BB81L),o("rq",P-8,I+0x337BB81L),
   o("wq",P-8,I+0x337BB90L),o("wq",S-8,M),o("wq",W+0x60,OLD),o("wq",W+0x70,E-0x4F),o("rq",M+8,OLD),
   o("wb",M+0x18,5),o("rq",M+0x20,A),o("wq",W+0x48,O),o("rd",M+0x10,0),o("wq",W+0x40,r14),
   o("wd",M+0x14,7),o("wd",M+0x10,0),o("rq",A,VT),o("rq",VT+8,TARGET),o("wq",W-8,I+0x337C131L),
   o("rb",M+0x18,5),o("wq",M+8,NEW)));
  List<Op> budgetExpected=new ArrayList<>();
  for(int j=0;j<13;j++){
   expected.add(o("wb",NEW+j*0x50L+4,0));
   budgetExpected.add(o("budget",0x337C150L,NEW+j*0x50L));
  }
  expected.addAll(List.of(
   o("wb",NEW+0x410+4,0xFF),
   o("wq",W-8,I+0x337C166L),o("rq",GS,TLS),o("rd",TLS+0x10,0x80000001L),o("rd",I+0x5C673D0L,0x80000000L),o("rq",W-8,I+0x337C166L),
   o("wq",W-8,I+0x337C1C8L),o("rq",GS,TLS),o("rd",TLS+0x10,0x80000001L),o("rd",I+0x5C673D0L,0x80000000L),o("rq",W-8,I+0x337C1C8L),
   o("rq",W+0x40,r14),o("rq",W+0x48,O),o("rq",W+0x60,OLD),o("rq",W+0x70,E-0x4F),o("rq",S-8,M),o("rq",S,I+0x337BB90L),
   o("rq",E+0x30,C),o("wq",P+0x28,C),o("rd",E+0x18,0),o("wq",P-8,I+0x337BBABL),
   o("wq",S+0x10,OLD),o("wd",S+0x18,0),
   o("wq",S-8,E-0x4F),o("wq",S-0x10,M),o("wq",S-0x18,O),o("wq",S-0x20,K),o("wq",S-0x28,en.r13Bits()),o("wq",S-0x30,r14),o("wq",S-0x38,en.r15Bits()),
   o("rd",M+0x14,7),o("rq",M+8,NEW),o("rb",NEW+4,0),o("rb",M+0x18,5),o("rd",M+0x10,0),o("rd",M+0x1C,0x3F800000),o("rb",NEW+4,0),
   o("wd",NEW,0),o("wb",NEW+4,1),o("rq",K,KEY),o("wq",NEW+8,KEY),o("wq",S+8,NEW+0x10),o("wq",NEW+0x48,0),
   o("rq",S+0x30,C),o("rq",C+0x38,0),o("rd",M+0x10,0),o("wd",M+0x10,1),o("wq",O,NEW),o("wb",O+8,1),
   o("rq",S+0x10,OLD),o("rq",S-0x38,en.r15Bits()),o("rq",S-0x30,r14),o("rq",S-0x28,en.r13Bits()),o("rq",S-0x20,K),
   o("rq",S-0x18,O),o("rq",S-0x10,M),o("rq",S-8,E-0x4F),o("rq",S,I+0x337BBABL),
   o("rq",E+0x10,en.rbxBits()),o("rq",E-0x38,en.r15Bits()),o("rq",E-0x30,en.r14Bits()),o("rq",E-0x28,en.r13Bits()),o("rq",E-0x20,en.r12Bits()),
   o("rq",E-0x18,en.rdiBits()),o("rq",E-0x10,en.rsiBits()),o("rq",E-8,en.rbpBits()),o("rq",E,RET)));
  assertEquals(113,expected.size());assertEquals(3,rootExpected.size());assertEquals(13,budgetExpected.size());assertTrue(m.ops.isEmpty());
  List<Call> rootSeen=new ArrayList<>();List<Op> budgets=new ArrayList<>();List<String> fp=new ArrayList<>();
  int[] allocCount={0},gsCount={0};
  Ports original=new Ports();
  original.invoke=c->{assertEquals(0,allocCount[0]++);assertEquals(allocExpected,c);assertEquals(I+0x337C131L,m.rawQ(W-8));return av;};
  original.gs=()->{assertTrue(gsCount[0]<2);assertEquals(gsCount[0]++==0?48:53,m.ops.size());return GS;};
  LoopBudget budget=(header,cursor)->{Op got=o("budget",header,cursor);assertEquals(budgetExpected.get(budgets.size()),got);budgets.add(got);};
  LoadRowReferenceCallee337b7e0199Api.Float32 floating=new LoadRowReferenceCallee337b7e0199Api.Float32(){
   public int convertSignedDwordToFloatBits(int a){int i=fp.size();assertTrue(i==0||i==1);assertEquals(81,m.ops.size());assertEquals(i==0?1:7,a);fp.add("c:"+a);return i==0?0x3F800000:0x40E00000;}
   public int divideScalarFloatBits(int a,int b){assertEquals(2,fp.size());assertEquals(81,m.ops.size());assertEquals(0x3F800000,a);assertEquals(0x40E00000,b);fp.add("div");return 0x3E124925;}
   public boolean orderedAbove(int a,int b){assertEquals(3,fp.size());assertEquals(82,m.ops.size());assertEquals(0x3E124925,a);assertEquals(0x3F800000,b);fp.add("above");return false;}
  };
  Calls graph=LoadRowReferenceGrowth244Calls.bind(I,m,original,budget,floating);
  Ports rootCalls=new Ports();rootCalls.invoke=c->{assertEquals(rootExpected.get(rootSeen.size()),c);rootSeen.add(c);return graph.invoke(c);};
  NormalReturn result=LoadRowReferenceCallee337b7e0199.execute(new Entry(I,E,ev,en),m,rootCalls,budget,floating);
  VolatileBits fv=new VolatileBits(O,0,O,0,K,av.r10Bits(),av.r11Bits(),new Bits128(0x40E00000L,0),new Bits128(0x3E124925L,0),av.xmm2(),av.xmm3(),av.xmm4(),av.xmm5());
  assertEquals(new NormalReturn(fv,RET,E+8,en),result);assertEquals(expected,m.ops);assertEquals(rootExpected,rootSeen);
  assertEquals(budgetExpected,budgets);assertEquals(List.of("c:1","c:7","div","above"),fp);assertEquals(1,allocCount[0]);assertEquals(2,gsCount[0]);
  assertEquals(NEW,m.rawQ(M+8));assertEquals(1,m.rawD(M+0x10));assertEquals(7,m.rawD(M+0x14));assertEquals(0x3F80000044332205L,m.rawQ(M+0x18));
  assertEquals(A,m.rawQ(M+0x20));assertEquals(NEW,m.rawQ(O));assertEquals(0x8877665544332201L,m.rawQ(O+8));
  assertEquals(0xCAFEBABE00000000L,m.rawQ(E+0x18));assertEquals(K,m.rawQ(E+0x20));assertEquals(C,m.rawQ(E+0x30));
  assertEquals(LEFT,m.rawQ(NEW-8));assertEquals(RIGHT,m.rawQ(NEW+0x460));
  for(int j=0;j<80;j++)assertEquals(Byte.toUnsignedInt(oldBytes[j]),m.rawB(OLD+j));
  for(int j=0;j<0x460;j++){
   int want=0x6B;
   if(j<4)want=0;
   else if(j==4)want=1;
   else if(j>=8&&j<16)want=(int)(KEY>>>(8*(j-8)))&255;
   else if(j>=0x48&&j<0x50)want=0;
   else if(j%0x50==4)want=j/0x50==13?255:0;
   assertEquals(want,m.rawB(NEW+j),"owned new byte "+j);
  }
 }
}
