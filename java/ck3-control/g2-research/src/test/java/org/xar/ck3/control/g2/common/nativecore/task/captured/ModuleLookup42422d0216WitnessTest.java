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
public final class ModuleLookup42422d0216WitnessTest {
 static Bits128 x(long b) { return new Bits128(b,b+1); }
 static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
 static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
 static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
 static class Ports implements TerminalAbort4242284215.Calls60 {
  public VolatileBits invoke(Call c) { throw new AssertionError(c); }
  public NormalReturn tail(Tail t) { throw new AssertionError(t); }
  public long readGsQword58() { throw new AssertionError("GS58"); }
  public long readGsQword60() { throw new AssertionError("GS60"); }
 }
 @Test void lowEaxZeroKeepsHighRaxAndRestoresFreshSlots216() {
  long I=0x140000000L,E=0x770000000108L,W=E-0x28,slot=E+0x10,oldSlot=0xCC11000000001234L,t458=0xA100000000004581L;
  long lowC=0xF1230041L,freshBx=0xD211000000000099L,freshRip=0xE322000000000088L;
  Mem m=new Mem();NonvolatileBits n=nv(0x110000000000L);VolatileBits z=v(0x220000000000L);
  VolatileBits initial=q(z,z.raxBits(),0xABCD2233F1230041L,z.rdxBits(),z.r8Bits(),z.r9Bits(),z.r10Bits(),z.r11Bits());
  VolatileBits a0=v(0x330000000000L),a=q(a0,0xFEDC000000000000L,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits());
  NonvolatileBits active=new NonvolatileBits(lowC,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(slot,oldSlot);m.b.putQ(E,0xEF33000000000123L);m.b.putQ(I+0x43DA458L,t458);List<Call> seen=new ArrayList<>();
  Ports ports=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    seen.add(call);assertEquals(new Call(0x42422ECL,TargetKind.INDIRECT_ABSOLUTE,t458,W,q(initial,initial.raxBits(),0,I+0x4423EB8L,slot,initial.r9Bits(),initial.r10Bits(),initial.r11Bits()),active),call);
    assertEquals(I+0x42422F2L,m.b.rawQ(W-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));m.writeQword(E-8,freshBx);m.writeQword(E,freshRip);return a;
   }
  };
  NormalReturn got=ModuleLookup42422d0216.execute(new Entry(I,E,initial,n),m,ports);
  NonvolatileBits restored=new NonvolatileBits(freshBx,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  assertEquals(1,seen.size());assertEquals(new NormalReturn(q(a,a.raxBits(),0,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),freshRip,E+8,restored),got);
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("rq",slot,oldSlot),new Op("wq",slot,0),new Op("rq",I+0x43DA458L,t458),new Op("wq",W-8,I+0x42422F2L),new Op("call",0x42422ECL,t458),new Op("wq",E-8,freshBx),new Op("wq",E,freshRip),new Op("rq",slot,0),new Op("rq",E-8,freshBx),new Op("rq",E,freshRip)),m.b.ops);
 }

 @Test void fourCallsUseFreshCleanupSlotAndFinalWholeV216() {
  long I=0x180000000L,E=0x780000000108L,W=E-0x28,slot=E+0x10,oldSlot=0xCC44000000001234L,rip=0xEF55000000005678L,lowC=0xF2000053L;
  long h1=0xA100000000001111L,h2=0xB200000000002222L,t458=0xA300000000004583L,t680=0xA400000000006804L,tBba8=0xA50000000000BBA5L,old7=0xA600000000007C06L,t7=0xB700000000007C07L;
  Mem m=new Mem();NonvolatileBits n=nv(0x440000000000L);VolatileBits z=v(0x550000000000L);
  VolatileBits initial=q(z,z.raxBits(),0xABCD0022F2000053L,z.rdxBits(),z.r8Bits(),z.r9Bits(),z.r10Bits(),z.r11Bits());
  VolatileBits a0=v(0x660000000000L),a=q(a0,0x8000000000000001L,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits());
  VolatileBits b0=v(0x770000000000L),b=q(b0,0x9000000000000000L,b0.rcxBits(),b0.rdxBits(),b0.r8Bits(),b0.r9Bits(),b0.r10Bits(),b0.r11Bits()),c=v(0x880000000000L),d=v(0x990000000000L);
  NonvolatileBits active=new NonvolatileBits(lowC,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(slot,oldSlot);m.b.putQ(E,rip);m.b.putQ(I+0x43DA458L,t458);m.b.putQ(I+0x43DA680L,t680);m.b.putQ(I+0x43DBBA8L,tBba8);m.b.putQ(I+0x43DA7C0L,old7);
  List<Call> expected=List.of(new Call(0x42422ECL,TargetKind.INDIRECT_ABSOLUTE,t458,W,q(initial,initial.raxBits(),0,I+0x4423EB8L,slot,initial.r9Bits(),initial.r10Bits(),initial.r11Bits()),active),
   new Call(0x4242302L,TargetKind.INDIRECT_ABSOLUTE,t680,W,q(a,a.raxBits(),h1,I+0x4423ED0L,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),active),
   new Call(0x424230FL,TargetKind.INDIRECT_ABSOLUTE,tBba8,W,q(b,b.raxBits(),lowC,b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits()),active),
   new Call(0x424231FL,TargetKind.INDIRECT_ABSOLUTE,t7,W,q(c,c.raxBits(),h2,c.rdxBits(),c.r8Bits(),c.r9Bits(),c.r10Bits(),c.r11Bits()),active));
  List<Call> seen=new ArrayList<>();List<VolatileBits> replies=List.of(a,b,c,d);long[] next={0x42422F2L,0x4242308L,0x4242315L,0x4242325L};
  Ports ports=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    int k=seen.size();seen.add(call);assertEquals(expected.get(k),call);assertEquals(I+next[k],m.b.rawQ(W-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));
    if(k==0)m.writeQword(slot,h1);if(k==2){m.writeQword(slot,h2);m.writeQword(I+0x43DA7C0L,t7);}return replies.get(k);
   }
  };
  NormalReturn got=ModuleLookup42422d0216.execute(new Entry(I,E,initial,n),m,ports);assertEquals(expected,seen);assertEquals(new NormalReturn(d,rip,E+8,n),got);
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("rq",slot,oldSlot),new Op("wq",slot,0),new Op("rq",I+0x43DA458L,t458),new Op("wq",W-8,I+0x42422F2L),new Op("call",0x42422ECL,t458),new Op("wq",slot,h1),new Op("rq",slot,h1),new Op("rq",I+0x43DA680L,t680),new Op("wq",W-8,I+0x4242308L),new Op("call",0x4242302L,t680),new Op("rq",I+0x43DBBA8L,tBba8),new Op("wq",W-8,I+0x4242315L),new Op("call",0x424230FL,tBba8),new Op("wq",slot,h2),new Op("wq",I+0x43DA7C0L,t7),new Op("rq",slot,h2),new Op("rq",I+0x43DA7C0L,t7),new Op("wq",W-8,I+0x4242325L),new Op("call",0x424231FL,t7),new Op("rq",E-8,n.rbxBits()),new Op("rq",E,rip)),m.b.ops);
 }

 @Test void actualParent215C0ConsumesNormalChildThenInt3216() {
  long I=0x1C0000000L,E=0x790000000108L,PW=E-0x28,CE=E-0x30,CW=E-0x58,slot=E-0x20,lowC=0xF3000067L,oldSlot=0xCC66000000001234L,t458=0xA700000000004587L,t558=0xB800000000005588L;
  Mem m=new Mem();NonvolatileBits n=nv(0xAA0000000000L);VolatileBits z=v(0xBB0000000000L),initial=q(z,z.raxBits(),0xABCD0044F3000067L,z.rdxBits(),z.r8Bits(),z.r9Bits(),z.r10Bits(),z.r11Bits());
  VolatileBits a0=v(0xCC0000000000L),a=q(a0,0xABCD000000000001L,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits());
  VolatileBits b0=v(0xDD0000000000L),b=q(b0,0xFEDC000000000000L,b0.rcxBits(),b0.rdxBits(),b0.r8Bits(),b0.r9Bits(),b0.r10Bits(),b0.r11Bits()),c=v(0xEE0000000000L);
  VolatileBits parentCallV=q(a,a.raxBits(),lowC,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),childResult=q(b,b.raxBits(),0,b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits());
  NonvolatileBits active=new NonvolatileBits(lowC,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(slot,oldSlot);m.b.putQ(I+0x43DA458L,t458);m.b.putQ(I+0x43DA558L,t558);
  List<Call> expected=List.of(new Call(0x424228CL,TargetKind.DIRECT_RVA,0x42591F8L,PW,initial,active),
   new Call(0x42422ECL,TargetKind.INDIRECT_ABSOLUTE,t458,CW,q(parentCallV,parentCallV.raxBits(),0,I+0x4423EB8L,slot,parentCallV.r9Bits(),parentCallV.r10Bits(),parentCallV.r11Bits()),active),
   new Call(0x42422C7L,TargetKind.INDIRECT_ABSOLUTE,t558,PW,q(childResult,childResult.raxBits(),lowC,childResult.rdxBits(),childResult.r8Bits(),childResult.r9Bits(),childResult.r10Bits(),childResult.r11Bits()),active));
  List<Call> seen=new ArrayList<>();List<VolatileBits> replies=List.of(a,b,c);long[] next={0x4242291L,0x42422F2L,0x42422CDL};
  Ports fallback=new Ports() {
   @Override public VolatileBits invoke(Call call) {int k=seen.size();seen.add(call);assertEquals(expected.get(k),call);assertEquals(I+next[k],m.b.rawQ(k==1?CW-8:PW-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));return replies.get(k);}
  };
  TerminalAbort4242284215.Calls60 bound=ModuleLookup42422d0216Calls.bind(I,m,fallback);List<VolatileBits> returned=new ArrayList<>();
  Ports observing=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    if(call.callSiteRva()==0x42422C0L){assertEquals(new Call(0x42422C0L,TargetKind.DIRECT_RVA,0x42422D0L,PW,parentCallV,active),call);assertEquals(I+0x42422C5L,m.b.rawQ(CE));m.b.ops.add(new Op("bind",call.callSiteRva(),call.targetBits()));VolatileBits value=bound.invoke(call);returned.add(value);return value;}return bound.invoke(call);
   }
  };
  assertThrows(UnsupportedOperationException.class,()->TerminalAbort4242284215.execute(new Entry(I,E,initial,n),m,observing));assertEquals(expected,seen);assertEquals(List.of(childResult),returned);
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("wq",PW-8,I+0x4242291L),new Op("call",0x424228CL,0x42591F8L),new Op("wq",PW-8,I+0x42422C5L),new Op("bind",0x42422C0L,0x42422D0L),new Op("wq",CE-8,lowC),new Op("rq",slot,oldSlot),new Op("wq",slot,0),new Op("rq",I+0x43DA458L,t458),new Op("wq",CW-8,I+0x42422F2L),new Op("call",0x42422ECL,t458),new Op("rq",slot,0),new Op("rq",CE-8,lowC),new Op("rq",CE,I+0x42422C5L),new Op("rq",I+0x43DA558L,t558),new Op("wq",PW-8,I+0x42422CDL),new Op("call",0x42422C7L,t558)),m.b.ops);
 }

 @Test void actualParent213OptionalCallConsumesChildAndReturns216() {
  long I=0x200000000L,E=0x7A0000000108L,PW=E-0x58,CE=E-0x60,CW=E-0x88,slot=E-0x50,lowC=0xF4000079L,p=0x630000000100L,h=p+0x80,rip=0xEF77000000001234L,oldSlot=0xCC77000000005678L,t620=0xA900000000006209L,t458=0xBA0000000000458AL;
  Mem m=new Mem();NonvolatileBits n=nv(0x1100000000000L);VolatileBits z=v(0x1200000000000L),initial=q(z,z.raxBits(),0xABCD0055F4000079L,0xABCD0000F2345678L,0x1234567800000000L,z.r9Bits(),z.r10Bits(),z.r11Bits());
  VolatileBits a0=v(0x1300000000000L),a=q(a0,p,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits());
  VolatileBits b0=v(0x1400000000000L),b=q(b0,0xFEDC000000000000L,b0.rcxBits(),b0.rdxBits(),b0.r8Bits(),b0.r9Bits(),b0.r10Bits(),b0.r11Bits()),c=v(0x1500000000000L);
  VolatileBits parentCallV=q(a,0x20B,lowC,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),childResult=q(b,b.raxBits(),0,b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits());
  NonvolatileBits active=new NonvolatileBits(lowC,E-8,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(E,rip);m.b.putQ(slot,oldSlot);m.b.putQ(I+0x43DA620L,t620);m.b.putQ(I+0x43DA458L,t458);m.b.put(p,0x5A4D,2);m.b.putD(p+0x3C,0x80);m.b.putD(h,0x4550);m.b.put(h+0x18,0x20B,2);m.b.putD(h+0x84,15);m.b.putD(h+0xF8,1);
  List<Call> expected=List.of(new Call(0x42421E7L,TargetKind.INDIRECT_ABSOLUTE,t620,PW,q(initial,initial.raxBits(),0,initial.rdxBits(),initial.r8Bits(),initial.r9Bits(),initial.r10Bits(),initial.r11Bits()),active),
   new Call(0x42422ECL,TargetKind.INDIRECT_ABSOLUTE,t458,CW,q(parentCallV,parentCallV.raxBits(),0,I+0x4423EB8L,slot,parentCallV.r9Bits(),parentCallV.r10Bits(),parentCallV.r11Bits()),active),
   new Call(0x4242266L,TargetKind.DIRECT_RVA,0x42420C0L,PW,q(childResult,2,E-0x38,E-0x30,E-0x28,E-0x34,childResult.r10Bits(),childResult.r11Bits()),active));
  List<Call> seen=new ArrayList<>();List<VolatileBits> replies=List.of(a,b,c);long[] next={0x42421EDL,0x42422F2L,0x424226BL};
  Ports fallback=new Ports() {
   @Override public VolatileBits invoke(Call call) {int k=seen.size();seen.add(call);assertEquals(expected.get(k),call);assertEquals(I+next[k],m.b.rawQ(k==1?CW-8:PW-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));if(k==2)m.writeDword(E+0x18,0xABCDE201);return replies.get(k);}
  };
  TerminalAbort4242284215.Calls60 bound=ModuleLookup42422d0216Calls.bind(I,m,fallback);List<VolatileBits> returned=new ArrayList<>();
  Ports observing=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    if(call.callSiteRva()==0x424222AL){assertEquals(new Call(0x424222AL,TargetKind.DIRECT_RVA,0x42422D0L,PW,parentCallV,active),call);assertEquals(I+0x424222FL,m.b.rawQ(CE));m.b.ops.add(new Op("bind",call.callSiteRva(),call.targetBits()));VolatileBits value=bound.invoke(call);returned.add(value);return value;}return bound.invoke(call);
   }
  };
  NormalReturn got=TerminalTailTarget42421c8213.execute(new Entry(I,E,initial,n),m,observing);assertEquals(expected,seen);assertEquals(List.of(childResult),returned);assertEquals(new NormalReturn(c,rip,E+8,n),got);
  assertEquals(List.of(new Op("wq",E+8,n.rbxBits()),new Op("wd",E+0x18,0),new Op("wd",E+0x10,0xF2345678L),new Op("wq",E-8,n.rbpBits()),new Op("rq",I+0x43DA620L,t620),new Op("wq",PW-8,I+0x42421EDL),new Op("call",0x42421E7L,t620),new Op("rw",p,0x5A4D),new Op("rd",p+0x3C,0x80),new Op("rd",h,0x4550),new Op("rw",h+0x18,0x20B),new Op("rd",h+0x84,15),new Op("rd",h+0xF8,1),new Op("wq",PW-8,I+0x424222FL),new Op("bind",0x424222AL,0x42422D0L),
   new Op("wq",CE-8,lowC),new Op("rq",slot,oldSlot),new Op("wq",slot,0),new Op("rq",I+0x43DA458L,t458),new Op("wq",CW-8,I+0x42422F2L),new Op("call",0x42422ECL,t458),new Op("rq",slot,0),new Op("rq",CE-8,lowC),new Op("rq",CE,I+0x424222FL),
   new Op("wb",E+0x20,0),new Op("wq",E-0x28,E+0x10),new Op("wq",E-0x20,E+0x18),new Op("wq",E-0x18,E+0x20),new Op("wd",E-0x34,2),new Op("wd",E-0x30,2),new Op("wq",PW-8,I+0x424226BL),new Op("call",0x4242266L,0x42420C0L),new Op("wd",E+0x18,0xABCDE201L),new Op("rd",E+0x18,0xABCDE201L),new Op("rq",E+8,n.rbxBits()),new Op("rq",E-8,n.rbpBits()),new Op("rq",E,rip)),m.b.ops);
 }

}
