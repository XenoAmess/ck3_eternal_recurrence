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
public final class LoadRowReferenceWhole199Witness241Test {
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
 public void whole199OccupiedRowMovesThroughReal201And202() {
  long image=0x8100000100000000L,E=0x7000000000500000L;
  long self=0x8200000000010000L,rows=0x8300000000020000L,out=0x8400000000030000L;
  long key=0x8500000000040000L,descriptor=0x8600000000050000L;
  long newKey=0x8700000000060001L,firstOldKey=0x8800000000070002L,secondOldKey=0x8900000000080003L;
  long cur=rows+0x50L,next=cur+0x50L,bp=E-0x4fL,work=E-0x118L,child=work-8L;
  long tempKey=bp-0x49L,tempDescriptor=bp-0x41L;
  long rawHash=0xfedcba9812345670L,hash=0x12345670L,oldHash=0xa1b2c3d4L;
  long oldRip=0x9000000000090004L,freshRip=0x91000000000a0005L;
  VolatileBits seed=v(0x1111000000000000L);
  VolatileBits initial=q(seed,0xcafe00000000babeL,self,out,rawHash,key,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits incoming=n(0x2222000000000000L),changed=n(0x3333000000000000L);
  VolatileBits afterFp=new VolatileBits(initial.raxBits(),initial.rcxBits(),initial.rdxBits(),
   initial.r8Bits(),initial.r9Bits(),initial.r10Bits(),initial.r11Bits(),
   new Bits128(0x40400000L,0),new Bits128(0x3eaaaaabL,0),
   initial.xmm2(),initial.xmm3(),initial.xmm4(),initial.xmm5());
  NonvolatileBits active=new NonvolatileBits(cur,bp,self,out,0,cur+0x10L,
   (incoming.r14Bits()&~0xffL)|2L,incoming.r15Bits(),incoming.xmm6());
  NonvolatileBits restored=new NonvolatileBits(changed.rbxBits(),incoming.rbpBits(),incoming.rsiBits(),
   incoming.rdiBits(),incoming.r12Bits(),incoming.r13Bits(),incoming.r14Bits(),changed.r15Bits(),incoming.xmm6());
  Bytes mem=new Bytes();
  mem.putQ(E,oldRip);mem.putQ(E+0x30L,descriptor);mem.putD(E+0x1cL,0xaabbccdd);
  mem.putQ(self+8L,rows);mem.putD(self+0x10L,0);mem.putD(self+0x14L,3);
  mem.putB(self+0x18L,2);mem.putD(self+0x1cL,0x3f666666);
  mem.putB(rows+4L,1);mem.putQ(rows+8L,firstOldKey);
  mem.putB(cur+4L,1);mem.putD(cur,(int)oldHash);mem.putQ(cur+8L,secondOldKey);mem.putQ(cur+0x48L,0);
  mem.putB(next+4L,0);mem.putQ(descriptor+0x38L,0);mem.putQ(key,newKey);
  mem.putQ(out,0x92000000000b0006L);mem.putB(out+8L,0x7f);
  mem.putB(cur+5L,0x66);mem.putB(next+5L,0x77);mem.putB(out+9L,0x88);
  int[] budgetSteps={0},fpSteps={0},matched={0},opaque={0};
  LoopBudget budget=(pc,address)->{
   assertEquals(0x337b831L,pc);assertEquals(rows,address);assertEquals(1,++budgetSteps[0]);
   // Explicit controlled software effects after the real prologue, not observed RAM writes.
   mem.putQ(E+0x10L,changed.rbxBits());mem.putQ(E-0x38L,changed.r15Bits());mem.putQ(E,freshRip);
  };
  LoadRowReferenceCallee337b7e0199Api.Float32 floating=new LoadRowReferenceCallee337b7e0199Api.Float32() {
   public int convertSignedDwordToFloatBits(int bits) {
    int step=fpSteps[0]++;
    if(step==0){assertEquals(1,bits);return 0x3f800000;}
    if(step==1){assertEquals(3,bits);return 0x40400000;}
    throw new AssertionError("unexpected CVTDQ2PS step "+step);
   }
   public int divideScalarFloatBits(int left,int right) {
    assertEquals(2,fpSteps[0]++);assertEquals(0x3f800000,left);assertEquals(0x40400000,right);
    return 0x3eaaaaab;
   }
   public boolean orderedAbove(int left,int right) {
    assertEquals(3,fpSteps[0]++);assertEquals(0x3eaaaaab,left);assertEquals(0x3f666666,right);
    return false;
   }
  };
  Ports fallback=new Ports();
  fallback.invoke=c->{opaque[0]++;throw new AssertionError("unexpected original fallback "+c);};
  Calls graph=LoadRowReferenceOuter240Calls.bind(image,mem,fallback,budget,floating);
  Ports observingParent=new Ports();
  observingParent.invoke=c->switch(matched[0]++) {
   case 0 -> {
    expectCall(c,0x337b93eL,TargetKind.DIRECT_RVA,0x87c9b0L,work,
     q(afterFp,secondOldKey,next+0x10L,cur+0x10L,rawHash,key,initial.r10Bits(),initial.r11Bits()),active);
    VolatileBits reply=graph.invoke(c);
    assertEquals(q(afterFp,secondOldKey,0,cur+0x10L,rawHash,key,initial.r10Bits(),initial.r11Bits()),reply);
    yield reply;
   }
   case 1 -> {
    expectCall(c,0x337b987L,TargetKind.DIRECT_RVA,0xe23ea0L,work,
     q(afterFp,descriptor,cur+8L,tempKey,hash,key,initial.r10Bits(),initial.r11Bits()),active);
    VolatileBits reply=graph.invoke(c);
    assertEquals(q(afterFp,cur+8L,0,tempKey,hash,key,initial.r10Bits(),initial.r11Bits()),reply);
    yield reply;
   }
   default -> throw new AssertionError("unexpected parent CALL "+c);
  };
  List<Op> expected=List.of(
   new Op("wq",E+0x10L,incoming.rbxBits()),new Op("wq",E+0x20L,key),new Op("wd",E+0x18L,hash),
   new Op("wq",E-8L,incoming.rbpBits()),new Op("wq",E-0x10L,incoming.rsiBits()),
   new Op("wq",E-0x18L,incoming.rdiBits()),new Op("wq",E-0x20L,incoming.r12Bits()),
   new Op("wq",E-0x28L,incoming.r13Bits()),new Op("wq",E-0x30L,incoming.r14Bits()),
   new Op("wq",E-0x38L,incoming.r15Bits()),new Op("rd",self+0x14L,3),new Op("rq",self+8L,rows),
   new Op("rb",rows+4L,1),new Op("rq",key,newKey),new Op("rq",rows+8L,firstOldKey),
   new Op("rb",cur+4L,1),new Op("rb",self+0x18L,2),new Op("rd",self+0x10L,0),
   new Op("rd",self+0x1cL,0x3f666666L),new Op("rb",cur+4L,1),new Op("rd",cur,oldHash),
   new Op("rb",cur+0x54L,0),new Op("wd",next,oldHash),new Op("wb",next+4L,2),
   new Op("rq",cur+8L,secondOldKey),new Op("wq",next+8L,secondOldKey),new Op("wq",next+0x48L,0),
   new Op("wq",work-8L,image+0x337b943L),
   new Op("wq",child+8L,cur),new Op("wq",child-8L,out),new Op("rq",cur+0x48L,0),
   new Op("rq",child+8L,cur),new Op("rq",child-8L,out),new Op("rq",child,image+0x337b943L),
   new Op("rd",bp+0x67L,hash),new Op("wd",cur,hash),new Op("wb",cur+4L,2),
   new Op("rq",bp+0x6fL,key),new Op("rq",key,newKey),new Op("wq",tempKey,newKey),
   new Op("wq",bp+0x57L,tempDescriptor),new Op("wq",bp-9L,0),
   new Op("rq",bp+0x7fL,descriptor),new Op("rq",descriptor+0x38L,0),
   new Op("wq",work-8L,image+0x337b98cL),
   new Op("wq",child+8L,cur),new Op("wq",child+0x10L,self),new Op("wq",child-8L,out),
   new Op("rq",tempKey,newKey),new Op("wq",cur+8L,newKey),new Op("rq",cur+0x48L,0),
   new Op("rq",tempKey+0x40L,0),new Op("rq",child+0x10L,self),new Op("rq",child+8L,cur),
   new Op("rq",child-8L,out),new Op("rq",child,image+0x337b98cL),
   new Op("rq",bp-9L,0),new Op("rd",self+0x10L,0),new Op("wd",self+0x10L,1),
   new Op("wq",out,cur),new Op("wb",out+8L,1),new Op("rq",E+0x10L,changed.rbxBits()),
   new Op("rq",E-0x38L,changed.r15Bits()),new Op("rq",E-0x30L,incoming.r14Bits()),
   new Op("rq",E-0x28L,incoming.r13Bits()),new Op("rq",E-0x20L,incoming.r12Bits()),
   new Op("rq",E-0x18L,incoming.rdiBits()),new Op("rq",E-0x10L,incoming.rsiBits()),
   new Op("rq",E-8L,incoming.rbpBits()),new Op("rq",E,freshRip));
  assertEquals(70,expected.size());assertTrue(mem.ops.isEmpty());
  assertEquals(0,matched[0]);assertEquals(0,fpSteps[0]);assertEquals(0,budgetSteps[0]);assertEquals(0,opaque[0]);
  NormalReturn result=LoadRowReferenceCallee337b7e0199.execute(new Entry(image,E,initial,incoming),
   mem,observingParent,budget,floating);
  assertEquals(new NormalReturn(q(afterFp,out,0,tempKey,hash,key,initial.r10Bits(),initial.r11Bits()),
   freshRip,E+8L,restored),result);
  assertEquals(expected,mem.ops);assertEquals(2,matched[0]);assertEquals(4,fpSteps[0]);
  assertEquals(1,budgetSteps[0]);assertEquals(0,opaque[0]);
  assertEquals(hash,Integer.toUnsignedLong(mem.rawD(cur)));assertEquals(2,mem.rawB(cur+4L));
  assertEquals(newKey,mem.rawQ(cur+8L));assertEquals(0,mem.rawQ(cur+0x48L));
  assertEquals(oldHash,Integer.toUnsignedLong(mem.rawD(next)));assertEquals(2,mem.rawB(next+4L));
  assertEquals(secondOldKey,mem.rawQ(next+8L));assertEquals(0,mem.rawQ(next+0x48L));
  assertEquals(1,mem.rawD(self+0x10L));assertEquals(cur,mem.rawQ(out));assertEquals(1,mem.rawB(out+8L));
  assertEquals(firstOldKey,mem.rawQ(rows+8L));assertEquals(1,mem.rawB(rows+4L));
  assertEquals(0xaabbccdd,mem.rawD(E+0x1cL));assertEquals(0x66,mem.rawB(cur+5L));
  assertEquals(0x77,mem.rawB(next+5L));assertEquals(0x88,mem.rawB(out+9L));
 }
}
