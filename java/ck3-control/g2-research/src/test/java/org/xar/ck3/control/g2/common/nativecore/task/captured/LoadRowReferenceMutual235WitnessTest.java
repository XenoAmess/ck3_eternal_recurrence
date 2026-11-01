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
public final class LoadRowReferenceMutual235WitnessTest {
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

 static final LoadRowReferenceCallee337b7e0199Api.Float32 NO_FP=new LoadRowReferenceCallee337b7e0199Api.Float32() {
  public int convertSignedDwordToFloatBits(int bits) {throw new AssertionError("CVTDQ2PS");}
  public int divideScalarFloatBits(int left,int right) {throw new AssertionError("DIVSS");}
  public boolean orderedAbove(int left,int right) {throw new AssertionError("COMISS");}
 };

 // Finite expected witnesses for the seven literal PUSH/POP instructions, not a business traversal.
 static void saves(List<Op> ops,long e,NonvolatileBits n) {
  long[] a={e-8,e-16,e-24,e-32,e-40,e-48,e-56};
  long[] z={n.rbpBits(),n.rbxBits(),n.rsiBits(),n.rdiBits(),n.r13Bits(),n.r14Bits(),n.r15Bits()};
  for(int k=0;k<7;k++)ops.add(new Op("wq",a[k],z[k]));
 }
 static void restores(List<Op> ops,long e,NonvolatileBits n,long ret) {
  long[] a={e-56,e-48,e-40,e-32,e-24,e-16,e-8};
  long[] z={n.r15Bits(),n.r14Bits(),n.r13Bits(),n.rdiBits(),n.rsiBits(),n.rbxBits(),n.rbpBits()};
  for(int k=0;k<7;k++)ops.add(new Op("rq",a[k],z[k]));
  ops.add(new Op("rq",e,ret));
 }

 @Test void actualC198RoutesC5GrowthThroughFastC0AndSelf235() {
  long image=0xF100000000000000L,pre=0xE100000020000000L,e=pre-8L,w=e-0xC8L,child=w-8L;
  long map=0x5100000002000000L,oldTable=0x5200000002000000L,oldRow=oldTable,keyp=oldRow+8L;
  long out=pre+0x30L,table1=0x5400000002000000L,row1=table1+80L,table2=0x5500000002000000L,key=0x9A00000000123456L;
  VolatileBits seed=v(0xA100000000000100L);
  VolatileBits in=q(seed,pre+0x68L,map,out,3L,keyp,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits ns=n(0xB100000000000100L);
  NonvolatileBits callerN=new NonvolatileBits(oldRow+0x48L,oldTable,map,1L,ns.r12Bits(),ns.r13Bits(),0L,ns.r15Bits(),ns.xmm6());
  NonvolatileBits active=new NonvolatileBits(row1,e-0x57L,map,1L,callerN.r12Bits(),3L,out,keyp,callerN.xmm6());
  VolatileBits capacityIncoming=q(in,in.raxBits(),2L,1L,3L,keyp,1L,in.r11Bits());
  VolatileBits cs=v(0xC100000000000100L);
  VolatileBits capacity=q(cs,0xCC00000000000000L,cs.rcxBits(),cs.rdxBits(),cs.r8Bits(),cs.r9Bits(),cs.r10Bits(),cs.r11Bits());
  VolatileBits expected=q(capacity,out,0L,out,3L,keyp,0L,capacity.r11Bits());
  Bytes m=new Bytes();m.putD(oldRow,3);m.putQ(keyp,key);
  m.putQ(pre+0x20L,pre+0x68L);m.putB(pre+0x68L,0);
  m.putD(map+0x14L,1);m.putQ(map+8L,table1);m.putB(row1+4L,0);m.putB(map+0x18L,0);
  m.putQ(out,0x1111111111111111L);m.putQ(out+8L,0x1122334455667788L);
  List<Op> ops=new ArrayList<>();ops.add(new Op("wq",e,image+0x337C19DL));saves(ops,e,callerN);
  ops.addAll(List.of(new Op("rd",map+0x14L,1),new Op("rq",map+8L,table1),new Op("rb",row1+4L,0),new Op("rb",map+0x18L,0),
   new Op("wq",w-8L,image+0x337C878L),new Op("wq",w-8L,image+0x337C887L),
   new Op("wq",child-8L,map),new Op("rq",child-8L,map),new Op("rq",child,image+0x337C887L),
   new Op("wb",e+0x18L,0),new Op("wq",w+0x20L,e+0x18L),new Op("wq",w-8L,image+0x337C8A5L)));
  saves(ops,child,active);
  ops.addAll(List.of(new Op("rd",map+0x14L,0),new Op("rq",map+8L,table2),new Op("rb",table2+4L,1),
   new Op("rq",keyp,key),new Op("rq",table2+8L,key),new Op("wq",out,table2),new Op("wb",out+8L,0)));
  restores(ops,child,active,image+0x337C8A5L);restores(ops,e,callerN,image+0x337C19DL);
  assertEquals(50,ops.size());assertTrue(m.ops.isEmpty());int[] capacityCalls={0},steps={0};
  LoopBudget budget=(pc,address)->{assertEquals(0,steps[0]++);assertEquals(0x337C615L,pc);assertEquals(table2,address);};
  Ports fallback=new Ports();fallback.invoke=c->{
   assertEquals(0,capacityCalls[0]++);
   assertEquals(new Call(0x337C873L,TargetKind.DIRECT_RVA,0x86E160L,w,capacityIncoming,active),c);
   assertEquals(image+0x337C878L,m.rawQ(w-8L));
   // Artificial supplied normal-port EAX0; this is not a result of the mature capacity algorithm.
   m.putD(map+0x14L,0);m.putQ(map+8L,table2);m.putB(table2+4L,1);m.putQ(table2+8L,key);
   return capacity;
  };
  Calls bound=LoadRowReferenceMutual235Calls.bind(image,m,fallback,budget,NO_FP);
  Call incoming=new Call(0x337C198L,TargetKind.DIRECT_RVA,0x337C5D0L,pre,in,callerN);
  assertEquals(0,capacityCalls[0]);assertEquals(0,steps[0]);m.writeQword(e,image+0x337C19DL);
  VolatileBits actual=bound.invoke(incoming);
  assertEquals(expected,actual);assertEquals(ops,m.ops);assertEquals(1,capacityCalls[0]);assertEquals(1,steps[0]);
  assertEquals(table2,m.rawQ(out));assertEquals(0x1122334455667700L,m.rawQ(out+8L));
  assertEquals(image+0x337C19DL,m.rawQ(e));assertEquals(image+0x337C8A5L,m.rawQ(child));
  assertEquals(e+0x18L,m.rawQ(w+0x20L));assertEquals(0,m.rawB(e+0x18L));
 }

 @Test void actualC064TailFastReturnAndForeignIdentity235() {
  long image=0xF200000000000000L,e=0xE200000020000008L,ret=0xD200000000001234L;
  VolatileBits seed=v(0xA200000000000100L);
  VolatileBits in=q(seed,seed.raxBits(),0x5200000000000000L,0L,seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
  NonvolatileBits n=n(0xB200000000000100L);Entry originalEntry=new Entry(image,e,in,n);
  Tail matching=new Tail(0x337C064L,TargetKind.DIRECT_RVA,0x337C0C0L,originalEntry);
  VolatileBits expectedV=q(in,0xFFFFFFFFL,in.rcxBits(),0L,in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits());
  NormalReturn expected=new NormalReturn(expectedV,ret,e+8L,n);
  Bytes m=new Bytes();m.putQ(e,ret);
  List<Op> ops=List.of(new Op("wq",e-8L,n.rsiBits()),new Op("rq",e-8L,n.rsiBits()),new Op("rq",e,ret));
  assertEquals(3,ops.size());assertTrue(m.ops.isEmpty());
  Ports fallback=new Ports();LoopBudget noLoop=(pc,address)->{throw new AssertionError("unexpected budget");};
  Calls bound=LoadRowReferenceMutual235Calls.bind(image,m,fallback,noLoop,NO_FP);
  NormalReturn actual=bound.tail(matching);assertEquals(expected,actual);assertEquals(ops,m.ops);
  VolatileBits foreignV=v(0xC200000000000100L);
  Call[] calls={new Call(0x337C199L,TargetKind.DIRECT_RVA,0x337C5D0L,e+8L,in,n),
   new Call(0x337C198L,TargetKind.DIRECT_RVA,0x337C5D1L,e+8L,in,n),
   new Call(0x337C198L,TargetKind.INDIRECT_ABSOLUTE,0x337C5D0L,e+8L,in,n)};
  int[] seenCalls={0},seenTails={0},seenGS={0};
  fallback.invoke=c->{assertSame(calls[seenCalls[0]++],c);return foreignV;};
  for(Call c:calls)assertSame(foreignV,bound.invoke(c));assertEquals(3,seenCalls[0]);
  Tail[] tails={new Tail(0x337C065L,TargetKind.DIRECT_RVA,0x337C0C0L,originalEntry),
   new Tail(0x337C064L,TargetKind.DIRECT_RVA,0x337C0C1L,originalEntry),
   new Tail(0x337C064L,TargetKind.INDIRECT_ABSOLUTE,0x337C0C0L,originalEntry)};
  NormalReturn foreignNR=new NormalReturn(foreignV,0xDD00000000000001L,0xEE00000000000002L,n);
  fallback.tail=t->{assertSame(tails[seenTails[0]++],t);assertSame(originalEntry,t.entry());return foreignNR;};
  for(Tail t:tails)assertSame(foreignNR,bound.tail(t));assertEquals(3,seenTails[0]);
  fallback.gs=()->{assertEquals(0,seenGS[0]++);return 0xABCD00000000FEDCL;};
  assertEquals(0xABCD00000000FEDCL,bound.readGsQword58());assertEquals(1,seenGS[0]);assertEquals(ops,m.ops);
 }

}
