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
public final class LoadRowReferenceWhole199Witness242Test {
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
 @Test
 void whole199DisplacesOneOccupiedRowThroughFourRealOuterCalls() {
  long image=0x140000000L, e=0x70000008L, w=e-0x118, bp=e-0x4f;
  long map=0x51000000L, table=0x52000000L, r0=table, r1=table+0x50, r2=table+0xa0, r3=table+0xf0;
  long out=0x53000000L, key=0x54000000L, descriptor=0x55000000L, ret=0x7ff600123456L;
  long k0=0x1111222233334444L, k1=0x2222333344445555L, k2=0x3333444455556666L, fresh=0xdeadbeef12345678L;
  int h0=0x11110011, h1=0x22220022, h2=0x33330033;
  NonvolatileBits entryN=n(0x2000000000000000L);
  VolatileBits seed=v(0x1000000000000000L);
  VolatileBits entryV=q(seed,0xa000000000000007L,map,out,0xcafebabe00000000L,key,seed.r10Bits(),seed.r11Bits());
  Bytes m=new Bytes();
  for(int i=0;i<4*0x50;i++)m.putB(table+i,0xa5);
  m.putQ(map+8,table);m.putD(map+0x10,1);m.putD(map+0x14,3);m.putB(map+0x18,3);m.putD(map+0x1c,0x3f800000);
  m.putD(r0,h0);m.putB(r0+4,1);m.putQ(r0+8,k0);m.putQ(r0+0x48,0);
  m.putD(r1,h1);m.putB(r1+4,1);m.putQ(r1+8,k1);m.putQ(r1+0x48,0);
  m.putD(r2,h2);m.putB(r2+4,1);m.putQ(r2+8,k2);m.putQ(r2+0x48,0);m.putB(r3+4,0);
  m.putQ(key,fresh);m.putQ(descriptor+0x38,0);m.putQ(e,ret);m.putQ(e+0x30,descriptor);
  m.putQ(e+0x18,0x7e7d7c7b12345678L);m.putQ(out,0x123456789abcdef0L);m.putQ(out+8,0x88776655443322eeL);
  assertTrue(m.ops.isEmpty());assertEquals(3,m.rawD(map+0x14));assertEquals(1,m.rawD(map+0x10));
  assertEquals(0,(int)entryV.r8Bits());assertEquals(1,m.rawB(r0+4));assertEquals(1,m.rawB(r1+4));
  assertEquals(1,m.rawB(r2+4));assertEquals(0,m.rawB(r3+4));assertEquals(k0,m.rawQ(r0+8));
  assertEquals(k1,m.rawQ(r1+8));assertEquals(k2,m.rawQ(r2+8));assertEquals(fresh,m.rawQ(key));

  VolatileBits fv=new VolatileBits(entryV.raxBits(),entryV.rcxBits(),entryV.rdxBits(),entryV.r8Bits(),entryV.r9Bits(),entryV.r10Bits(),entryV.r11Bits(),
    new Bits128(0x40400000L,0),new Bits128(0x3f2aaaabL,0),entryV.xmm2(),entryV.xmm3(),entryV.xmm4(),entryV.xmm5());
  long t10=entryV.r10Bits(),t11=entryV.r11Bits();
  NonvolatileBits n1=new NonvolatileBits(r1,bp,map,out,0,r1+0x10,(entryN.r14Bits()&~0xffL)|2,entryN.r15Bits(),entryN.xmm6());
  NonvolatileBits n2=new NonvolatileBits(r2,bp,map,out,0,r1+0x10,r1,entryN.r15Bits(),entryN.xmm6());
  NonvolatileBits n3=new NonvolatileBits(r3,bp,map,out,0,r1+0x10,r1,entryN.r15Bits(),entryN.xmm6());
  List<Call> expectedCalls=List.of(
    new Call(0x337b9ceL,TargetKind.DIRECT_RVA,0x87c9b0L,w,q(fv,k1,w+0x40,r1+0x10,entryV.r8Bits(),key,t10,t11),n1),
    new Call(0x337ba17L,TargetKind.DIRECT_RVA,0xe23ea0L,w,q(fv,descriptor,r1+8,w+0x80,0,key,t10,t11),n1),
    new Call(0x337ba8bL,TargetKind.DIRECT_RVA,0xa636f0L,w,q(fv,k2,w+0x40,r2+0x10,0,key,t10,t11),n2),
    new Call(0x337bb4aL,TargetKind.DIRECT_RVA,0x87c9b0L,w,q(fv,k2,r3+0x10,w+0x40,0,key,t10,t11),n3));
  List<Op> expected=List.of(
    new Op("wq",e+0x10,entryN.rbxBits()),new Op("wq",e+0x20,key),new Op("wd",e+0x18,0),
    new Op("wq",e-8,entryN.rbpBits()),new Op("wq",e-0x10,entryN.rsiBits()),new Op("wq",e-0x18,entryN.rdiBits()),
    new Op("wq",e-0x20,entryN.r12Bits()),new Op("wq",e-0x28,entryN.r13Bits()),new Op("wq",e-0x30,entryN.r14Bits()),new Op("wq",e-0x38,entryN.r15Bits()),
    new Op("rd",map+0x14,3),new Op("rq",map+8,table),new Op("rb",r0+4,1),new Op("rq",key,fresh),new Op("rq",r0+8,k0),
    new Op("rb",r1+4,1),new Op("rb",map+0x18,3),new Op("rd",map+0x10,1),new Op("rd",map+0x1c,0x3f800000),new Op("rb",r1+4,1),
    new Op("rd",r1,h1),new Op("rb",r2+4,1),new Op("wd",w+0x30,h1),new Op("wb",w+0x34,2),new Op("rq",r1+8,k1),new Op("wq",w+0x38,k1),
    new Op("wq",w+0x78,0),new Op("wq",w-8,image+0x337b9d3L),
    new Op("wq",w,r1),new Op("wq",w-0x10,out),new Op("rq",r1+0x48,0),new Op("rq",w,r1),new Op("rq",w-0x10,out),new Op("rq",w-8,image+0x337b9d3L),
    new Op("rd",e+0x18,0),new Op("wd",r1,0),new Op("wb",r1+4,2),new Op("rq",e+0x20,key),new Op("rq",key,fresh),new Op("wq",w+0x80,fresh),
    new Op("wq",e+8,w+0x88),new Op("wq",w+0xc0,0),new Op("rq",e+0x30,descriptor),new Op("rq",descriptor+0x38,0),new Op("wq",w-8,image+0x337ba1cL),
    new Op("wq",w,r1),new Op("wq",w+8,map),new Op("wq",w-0x10,out),new Op("rq",w+0x80,fresh),new Op("wq",r1+8,fresh),
    new Op("rq",r1+0x48,0),new Op("rq",w+0xc0,0),new Op("rq",w+8,map),new Op("rq",w,r1),new Op("rq",w-0x10,out),new Op("rq",w-8,image+0x337ba1cL),
    new Op("rq",w+0xc0,0),new Op("rb",w+0x34,2),new Op("rb",r2+4,1),new Op("rd",w+0x30,h1),new Op("rd",r2,h2),
    new Op("wd",w+0x30,h2),new Op("wd",r2,h1),new Op("rb",w+0x34,2),new Op("rb",r2+4,1),new Op("wb",w+0x34,1),new Op("wb",r2+4,2),
    new Op("rq",w+0x38,k1),new Op("rq",r2+8,k2),new Op("wq",w+0x38,k2),new Op("wq",r2+8,k1),new Op("wq",w-8,image+0x337ba90L),
    new Op("wq",w+8,r2),new Op("wq",w-0x10,out),new Op("rq",w+0x78,0),new Op("rq",r2+0x48,0),new Op("wq",w+0x78,0),new Op("wq",r2+0x48,0),
    new Op("rq",w+8,r2),new Op("rq",w-0x10,out),new Op("rq",w-8,image+0x337ba90L),
    new Op("rb",w+0x34,1),new Op("wb",w+0x34,2),new Op("rb",r3+4,0),new Op("rd",w+0x30,h2),new Op("wd",r3,h2),new Op("wb",r3+4,2),
    new Op("rq",w+0x38,k2),new Op("wq",r3+8,k2),new Op("wq",r3+0x48,0),new Op("wq",w-8,image+0x337bb4fL),
    new Op("wq",w,r3),new Op("wq",w-0x10,out),new Op("rq",w+0x78,0),new Op("rq",w,r3),new Op("rq",w-0x10,out),new Op("rq",w-8,image+0x337bb4fL),
    new Op("rq",w+0x78,0),new Op("rd",map+0x10,1),new Op("wd",map+0x10,2),new Op("wq",out,r1),new Op("wb",out+8,1),
    new Op("rq",e+0x10,entryN.rbxBits()),new Op("rq",e-0x38,entryN.r15Bits()),new Op("rq",e-0x30,entryN.r14Bits()),new Op("rq",e-0x28,entryN.r13Bits()),
    new Op("rq",e-0x20,entryN.r12Bits()),new Op("rq",e-0x18,entryN.rdiBits()),new Op("rq",e-0x10,entryN.rsiBits()),new Op("rq",e-8,entryN.rbpBits()),new Op("rq",e,ret));
  assertEquals(111,expected.size());assertEquals(4,expectedCalls.size());
  List<List<Integer>> fp=new ArrayList<>();
  LoadRowReferenceCallee337b7e0199Api.Float32 floating=new LoadRowReferenceCallee337b7e0199Api.Float32(){
   public int convertSignedDwordToFloatBits(int value){fp.add(List.of(0,value));if(value==2)return 0x40000000;if(value==3)return 0x40400000;throw new AssertionError(value);}
   public int divideScalarFloatBits(int dividend,int divisor){fp.add(List.of(1,dividend,divisor));assertEquals(0x40000000,dividend);assertEquals(0x40400000,divisor);return 0x3f2aaaab;}
   public boolean orderedAbove(int left,int right){fp.add(List.of(2,left,right));assertEquals(0x3f2aaaab,left);assertEquals(0x3f800000,right);return false;}
  };
  List<Op> budgets=new ArrayList<>();
  LoopBudget budget=(site,cursor)->{if(budgets.size()>=3)throw new AssertionError("unbounded walk");budgets.add(new Op("budget",site,cursor));};
  int[] opaque={0,0,0};Ports fallback=new Ports();
  fallback.invoke=c->{opaque[0]++;throw new AssertionError(c);};fallback.tail=t->{opaque[1]++;throw new AssertionError(t);};fallback.gs=()->{opaque[2]++;throw new AssertionError("GS58");};
  Calls bound=LoadRowReferenceOuter240Calls.bind(image,m,fallback,budget,floating);
  List<Call> seen=new ArrayList<>();Ports observed=new Ports();
  observed.invoke=c->{seen.add(c);return bound.invoke(c);};observed.tail=bound::tail;observed.gs=bound::readGsQword58;
  NormalReturn result=LoadRowReferenceCallee337b7e0199.execute(new Entry(image,e,entryV,entryN),m,observed,budget,floating);
  assertEquals(expectedCalls,seen);assertEquals(expected,m.ops);
  assertEquals(List.of(new Op("budget",0x337b831L,r0),new Op("budget",0x337ba40L,r1),new Op("budget",0x337ba40L,r2)),budgets);
  assertEquals(List.of(List.of(0,2),List.of(0,3),List.of(1,0x40000000,0x40400000),List.of(2,0x3f2aaaab,0x3f800000)),fp);
  assertArrayEquals(new int[]{0,0,0},opaque);
  assertEquals(new NormalReturn(q(fv,out,0,w+0x40,0,key,t10,t11),ret,e+8,entryN),result);
  assertEquals(r1,m.rawQ(out));assertEquals(0x8877665544332201L,m.rawQ(out+8));assertEquals(2,m.rawD(map+0x10));
  assertEquals(h0,m.rawD(r0));assertEquals(1,m.rawB(r0+4));assertEquals(k0,m.rawQ(r0+8));
  assertEquals(0,m.rawD(r1));assertEquals(fresh,m.rawQ(r1+8));assertEquals(h1,m.rawD(r2));assertEquals(k1,m.rawQ(r2+8));
  assertEquals(h2,m.rawD(r3));assertEquals(k2,m.rawQ(r3+8));
  for(long row:new long[]{r1,r2,r3}){assertEquals(0xa5a5a502,m.rawD(row+4));assertEquals(0L,m.rawQ(row+0x48));}
  assertEquals(0x7e7d7c7b,m.rawD(e+0x1c));assertEquals(w+0x88,m.rawQ(e+8));assertEquals(image+0x337bb4fL,m.rawQ(w-8));
 }

}
