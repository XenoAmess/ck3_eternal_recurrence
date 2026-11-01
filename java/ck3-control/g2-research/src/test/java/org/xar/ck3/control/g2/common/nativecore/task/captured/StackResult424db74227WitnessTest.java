package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalTailTarget42421c8213WitnessTest.Mem;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class StackResult424db74227WitnessTest {
 static Bits128 x(long b) {return new Bits128(b,b+1);}
 static VolatileBits v(long b) {return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60));}
 static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) {return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());}
 static NonvolatileBits nv(long b) {return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80));}
 static final class Ports implements TerminalAbort4242284215.Calls60 {
  java.util.function.Function<Call,VolatileBits> invoke=c->{throw new AssertionError(c);};
  java.util.function.Function<Tail,NormalReturn> tail=t->{throw new AssertionError(t);};
  java.util.function.LongSupplier readGsQword58=()->{throw new AssertionError("GS58");};
  java.util.function.LongSupplier readGsQword60=()->{throw new AssertionError("GS60");};
  public VolatileBits invoke(Call c) {return invoke.apply(c);}
  public NormalReturn tail(Tail t) {return tail.apply(t);}
  public long readGsQword58() {return readGsQword58.getAsLong();}
  public long readGsQword60() {return readGsQword60.getAsLong();}
 }
 static NonvolatileBits nd(NonvolatileBits n,long bx,long di) {return new NonvolatileBits(bx,n.rbpBits(),n.rsiBits(),di,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
 static void ck(Call c,long site,TargetKind kind,long target,long work,VolatileBits value,NonvolatileBits n,Mem m,long image,int len) {
  assertEquals(new Call(site,kind,target,work,value,n),c);assertEquals(image+site+len,m.b.rawQ(work-8));
 }

 @Test void directSavedMiddleAndFreshCleanupFrame227() {
  long I=0x100000000L,E=0x800000000L,W=E-0x28L,D=0x500000000L,C=0x600000000L,A=0x81000000ABCDEF01L;
  long ret0=0x8200000000000100L,ret1=0x8300000000000200L,bx1=0x8400000000000300L,di1=0x8500000000000400L;
  Mem m=new Mem();m.b.putQ(E,ret0);m.b.putD(D,0xFEDCBA98);m.b.putD(C,0x12345678);
  VolatileBits base=v(0x1100000000000100L);
  VolatileBits incoming=q(base,base.raxBits(),base.rcxBits(),D,A,C,base.r10Bits(),base.r11Bits());
  NonvolatileBits n=nv(0x2200000000000200L),active=nd(n,C,A);
  VolatileBits enter=v(0x3300000000000300L),middleBase=v(0x4400000000000400L),leave=v(0x5500000000000500L);
  VolatileBits middle=q(middleBase,0xABCD12348000000FL,middleBase.rcxBits(),middleBase.rdxBits(),middleBase.r8Bits(),middleBase.r9Bits(),middleBase.r10Bits(),middleBase.r11Bits());
  Ports p=new Ports();int[] calls={0};
  p.invoke=c->{
   int ordinal=calls[0]++;
   if(ordinal==0) {
    ck(c,0x424DB8BL,TargetKind.DIRECT_RVA,0x4247FFCL,W,q(incoming,incoming.raxBits(),0xFEDCBA98L,D,A,C,incoming.r10Bits(),incoming.r11Bits()),active,m,I,5);
    m.b.putD(C,0x8000010A);return enter;
   }
   if(ordinal==1) {
    ck(c,0x424DB94L,TargetKind.DIRECT_RVA,0x424DD60L,W,q(enter,enter.raxBits(),A,enter.rdxBits(),enter.r8Bits(),enter.r9Bits(),enter.r10Bits(),enter.r11Bits()),active,m,I,5);
    return middle;
   }
   assertEquals(2,ordinal);
   ck(c,0x424DB9DL,TargetKind.DIRECT_RVA,0x4248050L,W,q(middle,0xABCD12348000000FL,0x8000010AL,middle.rdxBits(),middle.r8Bits(),middle.r9Bits(),middle.r10Bits(),middle.r11Bits()),nd(n,C,0x8000000FL),m,I,5);
   m.b.putQ(E+8,bx1);m.b.putQ(E-8,di1);m.b.putQ(E,ret1);return leave;
  };
  NormalReturn result=StackResult424db74227.execute(new Entry(I,E,incoming,n),m,p);
  assertEquals(new NormalReturn(q(leave,0x8000000FL,leave.rcxBits(),leave.rdxBits(),leave.r8Bits(),leave.r9Bits(),leave.r10Bits(),leave.r11Bits()),ret1,E+8,nd(n,bx1,di1)),result);
  assertEquals(3,calls[0]);assertEquals(C,m.b.rawQ(E+0x20));
  assertEquals(List.of(new Op("wq",E+8,n.rbxBits()),new Op("wq",E+0x20,C),new Op("wq",E-8,n.rdiBits()),
   new Op("rd",D,0xFEDCBA98L),new Op("wq",W-8,I+0x424DB90L),new Op("wq",W-8,I+0x424DB99L),
   new Op("rd",C,0x8000010AL),new Op("wq",W-8,I+0x424DBA2L),
   new Op("rq",E+8,bx1),new Op("rq",E-8,di1),new Op("rq",E,ret1)),m.b.ops);
 }

 @Test void actual226ParentComposesThreeOpaqueChildCalls227() {
  long I=0x100000000L,S=0x900000000L,PW=S-0x38L,E=S-0x40L,W=E-0x28L;
  long ret0=0x8A00000000000100L,ret1=0x8B00000000000200L,unknown=0x8C00000000000300L;
  int high18=0x8D001122,high20=0x8E003344;
  Mem m=new Mem();m.b.putQ(S,ret0);m.b.putQ(S+0x10,unknown);m.b.putD(S+0x1C,high18);m.b.putD(S+0x24,high20);
  VolatileBits incoming=v(0x6600000000000600L);NonvolatileBits n=nv(0x7700000000000700L);
  VolatileBits parentCallV=q(incoming,2,S+0x10,S+0x20,S-0x18,S+0x18,incoming.r10Bits(),S);
  NonvolatileBits active=nd(n,S+0x18,S-0x18);
  VolatileBits enter=v(0x8800000000000800L),middleBase=v(0x9900000000000900L),leave=v(0xAA00000000000A00L);
  VolatileBits middle=q(middleBase,0xCDEF56788000003DL,middleBase.rcxBits(),middleBase.rdxBits(),middleBase.r8Bits(),middleBase.r9Bits(),middleBase.r10Bits(),middleBase.r11Bits());
  Ports fallback=new Ports();int[] opaque={0},matching={0};
  fallback.invoke=c->{
   int ordinal=opaque[0]++;
   if(ordinal==0) {
    ck(c,0x424DB8BL,TargetKind.DIRECT_RVA,0x4247FFCL,W,q(parentCallV,2,2,S+0x20,S-0x18,S+0x18,incoming.r10Bits(),S),active,m,I,5);
    assertEquals(unknown,m.b.rawQ(S+0x10));assertEquals(high18,m.b.rawD(S+0x1C));assertEquals(high20,m.b.rawD(S+0x24));
    m.b.putD(S+0x18,0x8000020B);return enter;
   }
   if(ordinal==1) {
    ck(c,0x424DB94L,TargetKind.DIRECT_RVA,0x424DD60L,W,q(enter,enter.raxBits(),S-0x18,enter.rdxBits(),enter.r8Bits(),enter.r9Bits(),enter.r10Bits(),enter.r11Bits()),active,m,I,5);
    return middle;
   }
   assertEquals(2,ordinal);
   ck(c,0x424DB9DL,TargetKind.DIRECT_RVA,0x4248050L,W,q(middle,0xCDEF56788000003DL,0x8000020BL,middle.rdxBits(),middle.r8Bits(),middle.r9Bits(),middle.r10Bits(),middle.r11Bits()),nd(n,S+0x18,0x8000003DL),m,I,5);
   m.b.putQ(S,ret1);return leave;
  };
  var bound=StackResult424db74227Calls.bind(I,m,fallback);Ports observing=new Ports();
  observing.invoke=c->{assertEquals(0,matching[0]++);ck(c,0x424DEB8L,TargetKind.DIRECT_RVA,0x424DB74L,PW,parentCallV,n,m,I,5);return bound.invoke(c);};
  observing.tail=bound::tail;observing.readGsQword58=bound::readGsQword58;observing.readGsQword60=bound::readGsQword60;
  NormalReturn result=StackContext424de88226.execute(new Entry(I,S,incoming,n),m,observing);
  assertEquals(new NormalReturn(q(leave,0x8000003DL,leave.rcxBits(),leave.rdxBits(),leave.r8Bits(),leave.r9Bits(),leave.r10Bits(),leave.r11Bits()),ret1,S+8,n),result);
  assertEquals(3,opaque[0]);assertEquals(1,matching[0]);
  assertEquals(List.of(new Op("wq",S+8,incoming.rcxBits()),new Op("wq",S-0x18,S+8),new Op("wd",S+0x18,2),new Op("wd",S+0x20,2),
   new Op("wq",E,I+0x424DEBDL),new Op("wq",E+8,n.rbxBits()),new Op("wq",E+0x20,S+0x18),new Op("wq",E-8,n.rdiBits()),
   new Op("rd",S+0x20,2),new Op("wq",W-8,I+0x424DB90L),new Op("wq",W-8,I+0x424DB99L),new Op("rd",S+0x18,0x8000020BL),new Op("wq",W-8,I+0x424DBA2L),
   new Op("rq",E+8,n.rbxBits()),new Op("rq",E-8,n.rdiBits()),new Op("rq",E,I+0x424DEBDL),new Op("rq",S,ret1)),m.b.ops);
  assertEquals(unknown,m.b.rawQ(S+0x10));assertEquals(high18,m.b.rawD(S+0x1C));assertEquals(high20,m.b.rawD(S+0x24));
 }

}
