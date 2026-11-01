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
public final class LoadRowReferenceSelf337c5d0234WitnessTest {
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

 @Test void bothSelfPairsUseOwnedChildFrameAndPreserveForeign234() {
  long[] sites={0x337C7F8L,0x337C8A0L};
  for(int k=0;k<2;k++) {
   long image=0xF000000010000000L,e=0xE000000020000008L+k*0x10000L,pre=e+8L,ret=image+sites[k]+5L;
   long map=0x5100000000000000L,out=0x5200000000000000L,keyp=0x5300000000000000L;
   long table=0x7000000000000000L,row=table-171798691120L,key=0xC700000000000101L;
   long rawHash=0xE100000080000009L,maskSigned=-2147483633L,index=-2147483639L;
   VolatileBits seed=v(0xA000000000000100L);
   VolatileBits in=q(seed,seed.raxBits(),map,out,rawHash,keyp,seed.r10Bits(),seed.r11Bits());
   NonvolatileBits n=n(0xB000000000000100L);
   VolatileBits expected=q(in,out,maskSigned,out,rawHash,keyp,index,in.r11Bits());
   Bytes m=new Bytes();m.putD(map+0x14L,0x8000000F);m.putQ(map+8L,table);
   m.putB(row+4L,1);m.putQ(keyp,key);m.putQ(row+8L,key);
   m.putQ(out,0x1111111111111111L);m.putQ(out+8L,0x1122334455667788L);
   List<Op> ops=new ArrayList<>();ops.add(new Op("wq",e,ret));saves(ops,e,n);
   ops.addAll(List.of(new Op("rd",map+0x14L,0x8000000FL),new Op("rq",map+8L,table),
    new Op("rb",row+4L,1),new Op("rq",keyp,key),new Op("rq",row+8L,key),
    new Op("wq",out,row),new Op("wb",out+8L,0)));
   restores(ops,e,n,ret);assertEquals(23,ops.size());assertTrue(m.ops.isEmpty());
   int[] budgetCalls={0};LoopBudget budget=(pc,address)->{assertEquals(0,budgetCalls[0]++);assertEquals(0x337C615L,pc);assertEquals(row,address);};
   Ports fallback=new Ports();Calls bound=LoadRowReferenceSelf337c5d0234Calls.bind(image,m,fallback,budget,NO_FP);
   // The real parent owns the single CALL push before entering the new adapter.
   m.writeQword(e,ret);
   VolatileBits actual=bound.invoke(new Call(sites[k],TargetKind.DIRECT_RVA,0x337C5D0L,pre,in,n));
   assertEquals(expected,actual);assertEquals(ops,m.ops);assertEquals(1,budgetCalls[0]);
   assertEquals(row,m.rawQ(out));assertEquals(0x1122334455667700L,m.rawQ(out+8L));assertEquals(ret,m.rawQ(e));
   if(k==0) {
    VolatileBits foreignV=v(0xCC00000000001000L);
    Call[] foreign={new Call(sites[k]+1L,TargetKind.DIRECT_RVA,0x337C5D0L,pre,in,n),
     new Call(sites[k],TargetKind.DIRECT_RVA,0x337C5D1L,pre,in,n),
     new Call(sites[k],TargetKind.INDIRECT_ABSOLUTE,0x337C5D0L,pre,in,n)};
    int[] seen={0};fallback.invoke=c->{assertSame(foreign[seen[0]++],c);return foreignV;};
    for(Call c:foreign)assertSame(foreignV,bound.invoke(c));assertEquals(3,seen[0]);
    Entry tailEntry=new Entry(image,e,in,n);Tail tail=new Tail(0x337C7F8L,TargetKind.DIRECT_RVA,0x337C5D0L,tailEntry);
    NormalReturn foreignNR=new NormalReturn(foreignV,0xDD00000000001234L,0xEE00000000005678L,n);
    fallback.tail=t->{assertSame(tail,t);assertSame(tailEntry,t.entry());return foreignNR;};
    fallback.gs=()->0xABCD00000000FEDCL;
    assertSame(foreignNR,bound.tail(tail));assertEquals(0xABCD00000000FEDCL,bound.readGsQword58());
    assertEquals(ops,m.ops);assertEquals(1,budgetCalls[0]);
   }
  }
 }

 @Test void actualGrowthReentersC5At8A0AndChildKeyMatches234() {
  long image=0xF100000010000000L,e=0xE200000020000008L,w=e-0xC8L,bp=e-0x57L,childE=w-8L;
  long map=0x5100000001000000L,out=0x5200000001000000L,keyp=0x5300000001000000L;
  long table1=0x5400000001000000L,row1=table1+80L,table2=0x5500000001000000L,key=0x9A00000000123456L;
  long rawHash=0xA555000080000003L,lowHash=0x80000003L,signedHash=-2147483645L;
  long originalRet=0xFA00000000000123L,freshRet=0xFB00000000000456L;
  VolatileBits seed=v(0xA200000000000100L);
  VolatileBits in=q(seed,seed.raxBits(),map,out,rawHash,keyp,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits n=n(0xB200000000000100L);
  NonvolatileBits active=new NonvolatileBits(row1,bp,map,(n.rdiBits()&~0xFFL)|1L,n.r12Bits(),signedHash,out,keyp,n.xmm6());
  VolatileBits capIncoming=q(in,in.raxBits(),2L,1L,rawHash,keyp,1L,in.r11Bits());
  VolatileBits capSeed=v(0xC200000000000100L);
  VolatileBits cap=q(capSeed,0xCC00000000000003L,capSeed.rcxBits(),capSeed.rdxBits(),capSeed.r8Bits(),capSeed.r9Bits(),capSeed.r10Bits(),capSeed.r11Bits());
  VolatileBits growIncoming=q(cap,cap.raxBits(),map,3L,cap.r8Bits(),cap.r9Bits(),cap.r10Bits(),cap.r11Bits());
  VolatileBits grow=v(0xD200000000000100L);
  VolatileBits selfIncoming=q(grow,e+0x18L,map,out,lowHash,keyp,grow.r10Bits(),grow.r11Bits());
  VolatileBits childPost=q(selfIncoming,out,0L,out,lowHash,keyp,0L,grow.r11Bits());
  NormalReturn expected=new NormalReturn(childPost,freshRet,e+8L,n);
  Bytes m=new Bytes();m.putD(map+0x14L,1);m.putQ(map+8L,table1);m.putB(row1+4L,0);m.putB(map+0x18L,0);
  m.putQ(keyp,key);m.putQ(out,0x1111111111111111L);m.putQ(out+8L,0x1122334455667788L);m.putQ(e,originalRet);
  List<Op> ops=new ArrayList<>();saves(ops,e,n);
  ops.addAll(List.of(new Op("rd",map+0x14L,1),new Op("rq",map+8L,table1),new Op("rb",row1+4L,0),new Op("rb",map+0x18L,0),
   new Op("wq",w-8L,image+0x337C878L),new Op("wq",w-8L,image+0x337C887L),
   new Op("wb",e+0x18L,0),new Op("wq",w+0x20L,e+0x18L),new Op("wq",w-8L,image+0x337C8A5L)));
  saves(ops,childE,active);
  ops.addAll(List.of(new Op("rd",map+0x14L,0),new Op("rq",map+8L,table2),new Op("rb",table2+4L,1),
   new Op("rq",keyp,key),new Op("rq",table2+8L,key),new Op("wq",out,table2),new Op("wb",out+8L,0)));
  restores(ops,childE,active,image+0x337C8A5L);restores(ops,e,n,freshRet);
  assertEquals(46,ops.size());assertTrue(m.ops.isEmpty());
  int[] budgetCalls={0},opaqueCalls={0},matched={0};
  LoopBudget budget=(pc,address)->{assertEquals(0,budgetCalls[0]++);assertEquals(0x337C615L,pc);assertEquals(table2,address);};
  Ports fallback=new Ports();fallback.invoke=c->{
   int ordinal=opaqueCalls[0]++;
   if(ordinal==0) {
    assertEquals(new Call(0x337C873L,TargetKind.DIRECT_RVA,0x86E160L,w,capIncoming,active),c);
    assertEquals(image+0x337C878L,m.rawQ(w-8L));return cap;
   }
   assertEquals(1,ordinal);
   assertEquals(new Call(0x337C882L,TargetKind.DIRECT_RVA,0x337C0C0L,w,growIncoming,active),c);
   assertEquals(image+0x337C887L,m.rawQ(w-8L));
   m.putD(map+0x14L,0);m.putQ(map+8L,table2);m.putB(table2+4L,1);m.putQ(table2+8L,key);m.putQ(e,freshRet);
   return grow;
  };
  Calls bound=LoadRowReferenceSelf337c5d0234Calls.bind(image,m,fallback,budget,NO_FP);
  Ports observed=new Ports();observed.invoke=c->{
   if(c.callSiteRva()==0x337C8A0L) {
    assertEquals(0,matched[0]++);
    assertEquals(new Call(0x337C8A0L,TargetKind.DIRECT_RVA,0x337C5D0L,w,selfIncoming,active),c);
    assertEquals(image+0x337C8A5L,m.rawQ(childE));assertEquals(e+0x18L,m.rawQ(w+0x20L));
    VolatileBits actual=bound.invoke(c);assertEquals(childPost,actual);return actual;
   }
   return bound.invoke(c);
  };
  observed.tail=bound::tail;observed.gs=bound::readGsQword58;
  assertEquals(0,opaqueCalls[0]);assertEquals(0,matched[0]);assertEquals(0,budgetCalls[0]);
  NormalReturn actual=LoadRowReferenceCallee337c5d0203.execute(new Entry(image,e,in,n),m,observed,budget,NO_FP);
  assertEquals(expected,actual);assertEquals(ops,m.ops);assertEquals(2,opaqueCalls[0]);assertEquals(1,matched[0]);assertEquals(1,budgetCalls[0]);
  assertEquals(table2,m.rawQ(out));assertEquals(0x1122334455667700L,m.rawQ(out+8L));
  assertEquals(e+0x18L,m.rawQ(w+0x20L));assertEquals(0,m.rawB(e+0x18L));assertEquals(freshRet,m.rawQ(e));
 }

}
