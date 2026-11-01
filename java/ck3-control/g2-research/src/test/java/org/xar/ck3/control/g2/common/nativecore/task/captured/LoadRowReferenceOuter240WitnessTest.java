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
public final class LoadRowReferenceOuter240WitnessTest {
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

 static void expectCall(Call actual,long site,TargetKind kind,long target,long sp,VolatileBits expectedV,NonvolatileBits expectedN) {
  assertEquals(new Call(site,kind,target,sp,expectedV,expectedN),actual);
 }
 @Test
 public void actual195RegistrationReaches199And200ViaOuter240() {
  // One artificial normal whole195 input; the three unknown helpers remain software ports.
  long image=0x8800000100000000L,E=0x7000000000300000L;
  long object=0x8100000000010203L,Q=0x8200000000020000L,P=0x8300000000030000L;
  long table=P+0x18L,row=0x8400000000040000L;
  long bp=E-0x5fL,work=E-0xc8L,descriptor=bp-0x11L,key=bp-0x39L,out=bp-0x21L;
  long child=work-8L,childBp=child-0x4fL,childWork=child-0x118L;
  long swap=childWork-8L,temp=childBp-0x49L;
  long global=image+0x5d75f40L,hash=0x0bed4376L;
  long oldRip=0xe000000000123450L,freshRip=0xf000000000123450L;
  VolatileBits initial=q(v(0x1111000000000000L),0x1111000000000000L,object,Q,
    0x1111000000000003L,0x1111000000000004L,0x1111000000000005L,0x1111000000000006L);
  NonvolatileBits incoming=n(0x2222000000000000L),changed=n(0x6666000000000000L);
  VolatileBits first=v(0x3333000000000000L),g=v(0x4444000000000000L),last=v(0x5555000000000000L);
  VolatileBits guard=q(g,0xabcd000000000000L,g.rcxBits(),g.rdxBits(),g.r8Bits(),g.r9Bits(),g.r10Bits(),g.r11Bits());
  NonvolatileBits firstN=new NonvolatileBits(object,bp,Q,0,incoming.r12Bits(),incoming.r13Bits(),
    incoming.r14Bits(),incoming.r15Bits(),incoming.xmm6());
  NonvolatileBits registrationN=new NonvolatileBits(object,bp,Q,table,incoming.r12Bits(),incoming.r13Bits(),
    global,incoming.r15Bits(),incoming.xmm6());
  NonvolatileBits restored=new NonvolatileBits(changed.rbxBits(),changed.rbpBits(),changed.rsiBits(),changed.rdiBits(),
    incoming.r12Bits(),incoming.r13Bits(),changed.r14Bits(),incoming.r15Bits(),incoming.xmm6());
  Bytes mem=new Bytes();
  mem.putQ(E,oldRip);mem.putQ(Q,P);
  mem.putD(table+0x14L,0);mem.putQ(table+8L,row);
  mem.putB(row+4L,1);mem.putQ(row+8L,object);mem.putQ(row+0x48L,0);
  int[] opaque={0},budgets={0};
  Ports fallback=new Ports();
  fallback.invoke=c->switch(opaque[0]++) {
   case 0 -> {
    expectCall(c,0x34ef74eL,TargetKind.DIRECT_RVA,0x34f04d0L,work,
      q(initial,P,object,Q,initial.r8Bits(),initial.r9Bits(),initial.r10Bits(),initial.r11Bits()),firstN);
    yield first;
   }
   case 1 -> {
    expectCall(c,0x34ef83cL,TargetKind.DIRECT_RVA,0x42219e0L,work,
      q(first,descriptor,global,object+0x470L,28L,3L,15L,first.r11Bits()),registrationN);
    // Controlled guard effect, not an observed port read/write or a guessed native implementation.
    mem.putQ(bp+0x27L,0);
    yield guard;
   }
   case 2 -> {
    expectCall(c,0x34ef8ceL,TargetKind.DIRECT_RVA,0x4221a04L,work,
      q(guard,out,global,row+0x10L,hash,key,guard.r10Bits(),guard.r11Bits()),registrationN);
    // Both real inner NR gates have returned before outer-only saved homes are changed.
    mem.putQ(E-0x28L,changed.r14Bits());mem.putQ(E-0x20L,changed.rdiBits());
    mem.putQ(E-0x18L,changed.rsiBits());mem.putQ(E-0x10L,changed.rbxBits());
    mem.putQ(E-8L,changed.rbpBits());mem.putQ(E,freshRip);
    yield last;
   }
   default -> throw new AssertionError("unexpected opaque CALL "+c);
  };
  LoopBudget budget=(pc,address)->{
   assertEquals(0x337b831L,pc);assertEquals(row,address);assertEquals(1,++budgets[0]);
  };
  Calls bound=LoadRowReferenceOuter240Calls.bind(image,mem,fallback,budget,NO_FP);
  List<Op> expected=new ArrayList<>();
  // EXPECTED-TRACE-BEGIN: original195, actual199 and actual200, every typed RAM operation.
  expected.addAll(List.of(
   new Op("wq",E+0x10L,Q),new Op("wq",E+8L,object),
   new Op("wq",E-8L,incoming.rbpBits()),new Op("wq",E-0x10L,incoming.rbxBits()),
   new Op("wq",E-0x18L,incoming.rsiBits()),new Op("wq",E-0x20L,incoming.rdiBits()),
   new Op("wq",E-0x28L,incoming.r14Bits()),new Op("wd",object+8L,0),
   new Op("wq",object,image+0x48f8928L),new Op("rq",Q,P),
   new Op("wq",object+0x10L,P),new Op("wq",Q,0),new Op("wd",object+0x18L,0),
   new Op("wq",work-8L,image+0x34ef753L),new Op("wd",object+0x30L,0),
   new Op("wd",object+0x3cL,0x3f666666L),new Op("wq",object+0x40L,object+0x48L),
   new Op("wq",object+0x48L,image+0x48f8a18L),new Op("wq",object+0x4a0L,image+0x54de1e8L),
   new Op("wd",bp+0x77L,3),new Op("wd",bp+0x7fL,3),
   new Op("wq",object+0x28L,object+0x50L),new Op("wd",object+0x34L,15),
   new Op("wb",object+0x38L,6)));
  // Fixed22 literal metadata slots, no table traversal or target-derived expected state.
  for(int slot=0;slot<22;slot++)expected.add(new Op("wb",object+0x54L+0x30L*slot,0));
  expected.addAll(List.of(
   new Op("wb",object+0x474L,0xffL),new Op("rq",object+0x10L,P),
   new Op("wq",descriptor,image+0x48f8ad0L),new Op("wq",bp-9L,image+0x34f0000L),
   new Op("wq",bp-1L,object),new Op("wq",bp+0x27L,descriptor),
   new Op("wq",key,object),new Op("wq",bp-0x31L,global),new Op("wb",bp-0x29L,0),
   new Op("wq",work-8L,image+0x34ef841L),new Op("wb",bp-0x29L,1),
   new Op("rb",key,3),new Op("rb",key+1L,2),new Op("rb",key+2L,1),new Op("rb",key+3L,0),
   new Op("rb",key+4L,0),new Op("rb",key+5L,0),new Op("rb",key+6L,0),new Op("rb",key+7L,0x81L),
   new Op("wq",work+0x28L,descriptor),new Op("wq",work-8L,image+0x34ef8caL),
   new Op("wq",child+0x10L,object),new Op("wq",child+0x20L,key),new Op("wd",child+0x18L,hash),
   new Op("wq",child-8L,bp),new Op("wq",child-0x10L,Q),new Op("wq",child-0x18L,table),
   new Op("wq",child-0x20L,incoming.r12Bits()),new Op("wq",child-0x28L,incoming.r13Bits()),
   new Op("wq",child-0x30L,global),new Op("wq",child-0x38L,incoming.r15Bits()),
   new Op("rd",table+0x14L,0),new Op("rq",table+8L,row),new Op("rb",row+4L,1),
   new Op("rq",key,object),new Op("rq",row+8L,object),new Op("wq",childBp-0x11L,0),
   new Op("rq",childBp+0x7fL,descriptor),new Op("rq",descriptor+0x38L,0),
   new Op("wq",childWork-8L,image+0x337b8f2L),
   new Op("wq",swap+0x10L,row),new Op("wq",swap-8L,out),
   new Op("rq",temp+0x38L,0),new Op("rq",row+0x48L,0),
   new Op("wq",temp+0x38L,0),new Op("wq",row+0x48L,0),
   new Op("rq",swap+0x10L,row),new Op("rq",swap-8L,out),new Op("rq",swap,image+0x337b8f2L),
   new Op("rq",childBp-0x11L,0),new Op("wq",out,row),new Op("wb",out+8L,0),
   new Op("rq",child+0x10L,object),new Op("rq",child-0x38L,incoming.r15Bits()),
   new Op("rq",child-0x30L,global),new Op("rq",child-0x28L,incoming.r13Bits()),
   new Op("rq",child-0x20L,incoming.r12Bits()),new Op("rq",child-0x18L,table),
   new Op("rq",child-0x10L,Q),new Op("rq",child-8L,bp),new Op("rq",child,image+0x34ef8caL),
   new Op("wq",work-8L,image+0x34ef8d3L),new Op("rq",bp+0x27L,0),new Op("rq",Q,0),
   new Op("rq",E-0x28L,changed.r14Bits()),new Op("rq",E-0x20L,changed.rdiBits()),
   new Op("rq",E-0x18L,changed.rsiBits()),new Op("rq",E-0x10L,changed.rbxBits()),
   new Op("rq",E-8L,changed.rbpBits()),new Op("rq",E,freshRip)));
  // EXPECTED-TRACE-END
  assertEquals(116,expected.size());assertEquals(0,opaque[0]);assertEquals(0,budgets[0]);assertTrue(mem.ops.isEmpty());
  NormalReturn actual=LoadRowReference34ef710195.execute(new Entry(image,E,initial,incoming),mem,bound);
  assertEquals(new NormalReturn(q(last,object,0,last.rdxBits(),last.r8Bits(),last.r9Bits(),last.r10Bits(),last.r11Bits()),
    freshRip,E+8L,restored),actual);
  assertEquals(expected,mem.ops);assertEquals(3,opaque[0]);assertEquals(1,budgets[0]);
  assertEquals(row,mem.rawQ(out));assertEquals(0,mem.raw(out+8L,1));assertEquals(0,mem.rawQ(Q));
  assertEquals(0,mem.rawQ(row+0x48L));assertEquals(0,mem.rawQ(bp+0x27L));

  // Foreign identity only; no second normal entry, no extra RAM or matcher observer.
  VolatileBits foreignV=v(0x7777000000000000L);
  Call foreign=new Call(0x34ef8c6L,TargetKind.DIRECT_RVA,0x337b7e0L,E,initial,incoming);
  int[] foreignCalls={0},foreignTails={0},foreignGs={0};
  fallback.invoke=c->{assertSame(foreign,c);foreignCalls[0]++;return foreignV;};
  assertSame(foreignV,bound.invoke(foreign));
  Tail transfer=new Tail(0x337c065L,TargetKind.DIRECT_RVA,0x337c0c0L,new Entry(image,E,initial,incoming));
  NormalReturn foreignReturn=new NormalReturn(foreignV,0x8888000000000001L,0x9999000000000002L,changed);
  fallback.tail=t->{assertSame(transfer,t);foreignTails[0]++;return foreignReturn;};
  assertSame(foreignReturn,bound.tail(transfer));
  fallback.gs=()->{foreignGs[0]++;return 0xaaaa000000000003L;};
  assertEquals(0xaaaa000000000003L,bound.readGsQword58());
  assertEquals(1,foreignCalls[0]);assertEquals(1,foreignTails[0]);assertEquals(1,foreignGs[0]);
  assertEquals(expected,mem.ops);assertEquals(3,opaque[0]);assertEquals(1,budgets[0]);
 }
}
