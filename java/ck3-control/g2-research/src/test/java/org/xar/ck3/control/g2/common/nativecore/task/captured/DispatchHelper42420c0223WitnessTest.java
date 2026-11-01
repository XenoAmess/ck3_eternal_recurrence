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
public final class DispatchHelper42420c0223WitnessTest {
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
 static void ck(Call c,long site,long target,long work,VolatileBits value,NonvolatileBits n,Mem m,long image) {
  assertEquals(new Call(site,TargetKind.DIRECT_RVA,target,work,value,n),c);
  assertEquals(image+site+5,m.b.rawQ(work-8));
 }

 @Test void directThreeCallsPreserveActualVAndFreshHomes223() {
  long image=0x140000000L,e=0x740000000108L,work=e-0x28L;
  long d=0x880000001000L,context=0x880000003000L,last=0x880000002000L;
  long newBx=0xA123456789ABCDEFL,newDi=0xB123456789ABCDEFL,newRip=0xC123456789ABCDEFL;
  Mem m=new Mem();m.b.putD(d,0x80000001);m.b.putD(last,0x12345678);m.b.putQ(e,0x1111222233334444L);
  VolatileBits seed=v(0xD100000000001000L);
  VolatileBits initial=q(seed,seed.raxBits(),seed.rcxBits(),d,context,last,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits saved=nv(0xE100000000002000L),active=nd(saved,last,context);
  VolatileBits first=v(0xA100000000003000L),middle=v(0xB100000000004000L),leave=v(0xC100000000005000L);
  Ports ports=new Ports();int[] calls={0};
  ports.invoke=call->{
   int step=calls[0]++;
   if(step==0) {
    ck(call,0x42420D7L,0x4247FFCL,work,q(initial,initial.raxBits(),0x80000001L,d,context,last,initial.r10Bits(),initial.r11Bits()),active,m,image);
    assertEquals(saved.rbxBits(),m.b.rawQ(e+8));assertEquals(last,m.b.rawQ(e+0x20));assertEquals(saved.rdiBits(),m.b.rawQ(e-8));
    m.writeDword(last,0x11111111);m.writeQword(e+8,newBx);return first;
   }
   if(step==1) {
    ck(call,0x42420E0L,0x42420F8L,work,q(first,first.raxBits(),context,first.rdxBits(),first.r8Bits(),first.r9Bits(),first.r10Bits(),first.r11Bits()),active,m,image);
    m.writeDword(last,0xFEEDBEEF);m.writeQword(e-8,newDi);return middle;
   }
   if(step==2) {
    ck(call,0x42420E8L,0x4248050L,work,q(middle,middle.raxBits(),0xFEEDBEEFL,middle.rdxBits(),middle.r8Bits(),middle.r9Bits(),middle.r10Bits(),middle.r11Bits()),active,m,image);
    m.writeQword(e,newRip);return leave;
   }
   throw new AssertionError(call);
  };
  NormalReturn nr=DispatchHelper42420c0223.execute(new Entry(image,e,initial,saved),m,ports);
  assertEquals(3,calls[0]);assertEquals(leave,nr.volatileBits());assertEquals(newRip,nr.returnRipBits());assertEquals(e+8,nr.callerRspBits());assertEquals(nd(saved,newBx,newDi),nr.nonvolatileBits());
  assertEquals(List.of(
   new Op("wq",e+8,saved.rbxBits()),new Op("wq",e+0x20,last),new Op("wq",e-8,saved.rdiBits()),
   new Op("rd",d,0x80000001L),new Op("wq",work-8,image+0x42420DCL),
   new Op("wd",last,0x11111111L),new Op("wq",e+8,newBx),
   new Op("wq",work-8,image+0x42420E5L),new Op("wd",last,0xFEEDBEEFL),new Op("wq",e-8,newDi),
   new Op("rd",last,0xFEEDBEEFL),new Op("wq",work-8,image+0x42420EDL),new Op("wq",e,newRip),
   new Op("rq",e+8,newBx),new Op("rq",e-8,newDi),new Op("rq",e,newRip)),m.b.ops);
 }

 @Test void parent213CallsActualNewDispatchBinding223() {
  long image=0x180000000L,p=0x750000000108L,parentWork=p-0x58L,childWork=p-0x88L,rip=0x9876543210ABCDEFL;
  Mem m=new Mem();m.b.putQ(p,rip);
  VolatileBits seed=v(0x8100000000001000L);
  VolatileBits initial=q(seed,0x1111222233334444L,0x12345678FEDCBA98L,0xB200000076543210L,0xC300000000000001L,0xD400000012345678L,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits saved=nv(0xE500000000002000L);
  NonvolatileBits parentActive=new NonvolatileBits(0xFEDCBA98L,p-8,saved.rsiBits(),saved.rdiBits(),saved.r12Bits(),saved.r13Bits(),saved.r14Bits(),saved.r15Bits(),saved.xmm6());
  NonvolatileBits childActive=nd(parentActive,p-0x34L,p-0x28L);
  VolatileBits parentCallV=q(initial,2,p-0x38L,p-0x30L,p-0x28L,p-0x34L,initial.r10Bits(),initial.r11Bits());
  VolatileBits first=v(0xA600000000003000L),middle=v(0xB700000000004000L),leave=v(0xC800000000005000L);
  Ports fallback=new Ports();int[] childCalls={0},parentCalls={0};
  fallback.invoke=call->{
   int step=childCalls[0]++;
   if(step==0) {
    ck(call,0x42420D7L,0x4247FFCL,childWork,q(parentCallV,2,2,p-0x30L,p-0x28L,p-0x34L,initial.r10Bits(),initial.r11Bits()),childActive,m,image);
    assertEquals(p+0x10L,m.b.rawQ(p-0x28L));assertEquals(p+0x18L,m.b.rawQ(p-0x20L));assertEquals(p+0x20L,m.b.rawQ(p-0x18L));
    assertEquals(0,m.b.rawB(p+0x20L));return first;
   }
   if(step==1) {
    ck(call,0x42420E0L,0x42420F8L,childWork,q(first,first.raxBits(),p-0x28L,first.rdxBits(),first.r8Bits(),first.r9Bits(),first.r10Bits(),first.r11Bits()),childActive,m,image);
    m.writeDword(p+0x18L,0x80000001);return middle;
   }
   if(step==2) {
    ck(call,0x42420E8L,0x4248050L,childWork,q(middle,middle.raxBits(),2,middle.rdxBits(),middle.r8Bits(),middle.r9Bits(),middle.r10Bits(),middle.r11Bits()),childActive,m,image);return leave;
   }
   throw new AssertionError(call);
  };
  TerminalAbort4242284215.Calls60 bound=DispatchHelper42420c0223Calls.bind(image,m,fallback);
  Ports observed=new Ports();observed.invoke=call->{parentCalls[0]++;ck(call,0x4242266L,0x42420C0L,parentWork,parentCallV,parentActive,m,image);return bound.invoke(call);};
  NormalReturn nr=TerminalTailTarget42421c8213.execute(new Entry(image,p,initial,saved),m,observed);
  assertEquals(1,parentCalls[0]);assertEquals(3,childCalls[0]);assertEquals(leave,nr.volatileBits());assertEquals(saved,nr.nonvolatileBits());assertEquals(rip,nr.returnRipBits());assertEquals(p+8,nr.callerRspBits());
  assertEquals(0x80000001,m.b.rawD(p+0x18L));
  assertEquals(List.of(
   new Op("wq",p+8,saved.rbxBits()),new Op("wd",p+0x18L,1),new Op("wd",p+0x10L,0x76543210L),new Op("wq",p-8,saved.rbpBits()),
   new Op("wb",p+0x20L,0),new Op("wq",p-0x28L,p+0x10L),new Op("wq",p-0x20L,p+0x18L),new Op("wq",p-0x18L,p+0x20L),
   new Op("wd",p-0x34L,2),new Op("wd",p-0x30L,2),new Op("wq",p-0x60L,image+0x424226BL),
   new Op("wq",p-0x58L,0xFEDCBA98L),new Op("wq",p-0x40L,p-0x34L),new Op("wq",p-0x68L,saved.rdiBits()),
   new Op("rd",p-0x30L,2),new Op("wq",p-0x90L,image+0x42420DCL),new Op("wq",p-0x90L,image+0x42420E5L),
   new Op("wd",p+0x18L,0x80000001L),new Op("rd",p-0x34L,2),new Op("wq",p-0x90L,image+0x42420EDL),
   new Op("rq",p-0x58L,0xFEDCBA98L),new Op("rq",p-0x68L,saved.rdiBits()),new Op("rq",p-0x60L,image+0x424226BL),
   new Op("rd",p+0x18L,0x80000001L),new Op("rq",p+8,saved.rbxBits()),new Op("rq",p-8,saved.rbpBits()),new Op("rq",p,rip)),m.b.ops);
 }

 @Test void opaqueExceptionPropagatesWithoutEpilogue223() {
  long image=0x1C0000000L,e=0x760000000108L,d=0x890000001000L,context=0x890000002000L,last=0x890000003000L;
  Mem m=new Mem();m.b.putD(d,0xF1234567);m.b.putQ(e,0xAAAABBBBCCCCDDDDL);
  VolatileBits seed=v(0xD900000000001000L),initial=q(seed,seed.raxBits(),seed.rcxBits(),d,context,last,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits saved=nv(0xEA00000000002000L),active=nd(saved,last,context);
  RuntimeException failure=new RuntimeException("controlled opaque failure");int[] calls={0};Ports ports=new Ports();
  ports.invoke=call->{calls[0]++;ck(call,0x42420D7L,0x4247FFCL,e-0x28L,q(initial,initial.raxBits(),0xF1234567L,d,context,last,initial.r10Bits(),initial.r11Bits()),active,m,image);throw failure;};
  RuntimeException thrown=assertThrows(RuntimeException.class,()->DispatchHelper42420c0223.execute(new Entry(image,e,initial,saved),m,ports));
  assertSame(failure,thrown);assertEquals(1,calls[0]);
  assertEquals(List.of(new Op("wq",e+8,saved.rbxBits()),new Op("wq",e+0x20L,last),new Op("wq",e-8,saved.rdiBits()),new Op("rd",d,0xF1234567L),new Op("wq",e-0x30L,image+0x42420DCL)),m.b.ops);
 }

}
