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
public final class TerminalAbort4242284215WitnessTest {
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
 @Test void gsShiftOneSkipsTwoIatsButCarriesRdx215() {
  long I=0x140000000L,E=0x740000000108L,W=E-0x28,G=0x612345678000L,inputC=0xCAFE1122F1230041L,lowC=0xF1230041L;
  long oldTarget=0xA100000000001234L,freshTarget=0xB200000000005678L;
  Mem m=new Mem();NonvolatileBits n=nv(0x110000000000L);VolatileBits z=v(0x220000000000L);
  VolatileBits initial=q(z,z.raxBits(),inputC,z.rdxBits(),z.r8Bits(),z.r9Bits(),z.r10Bits(),z.r11Bits());
  VolatileBits a0=v(0x330000000000L),a=q(a0,0xCAFE000000000002L,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits()),b=v(0x440000000000L),c=v(0x550000000000L);
  NonvolatileBits active=new NonvolatileBits(lowC,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putD(G+0xBC,0x100);m.b.putQ(I+0x43DA558L,oldTarget);
  List<Call> expected=List.of(new Call(0x424228CL,TargetKind.DIRECT_RVA,0x42591F8L,W,initial,active),
   new Call(0x42422C0L,TargetKind.DIRECT_RVA,0x42422D0L,W,q(a,G,lowC,1,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),active),
   new Call(0x42422C7L,TargetKind.INDIRECT_ABSOLUTE,freshTarget,W,q(b,b.raxBits(),lowC,b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits()),active));
  List<Call> seen=new ArrayList<>();List<VolatileBits> replies=List.of(a,b,c);long[] next={0x4242291L,0x42422C5L,0x42422CDL};
  Ports ports=new Ports() {
   @Override public long readGsQword60() {m.b.ops.add(new Op("gs60",0x60,G));return G;}
   @Override public VolatileBits invoke(Call call) {
    int k=seen.size();seen.add(call);assertEquals(expected.get(k),call);assertEquals(I+next[k],m.b.rawQ(W-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));
    if(k==1)m.writeQword(I+0x43DA558L,freshTarget);return replies.get(k);
   }
  };
  assertThrows(UnsupportedOperationException.class,()->TerminalAbort4242284215.execute(new Entry(I,E,initial,n),m,ports));
  assertEquals(expected,seen);
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("wq",W-8,I+0x4242291L),new Op("call",0x424228CL,0x42591F8L),new Op("gs60",0x60,G),new Op("rd",G+0xBC,0x100),
   new Op("wq",W-8,I+0x42422C5L),new Op("call",0x42422C0L,0x42422D0L),new Op("wq",I+0x43DA558L,freshTarget),new Op("rq",I+0x43DA558L,freshTarget),new Op("wq",W-8,I+0x42422CDL),new Op("call",0x42422C7L,freshTarget)),m.b.ops);
 }

 @Test void unsignedGsShiftAndFiveWholeFrames215() {
  long I=0x180000000L,E=0x750000000108L,W=E-0x28,G=0x623456789000L,inputC=0xDEAD0033F1000013L,lowC=0xF1000013L;
  long t798=0xA100000000007981L,old778=0xA200000000007782L,t778=0xB200000000007783L,old558=0xA300000000005584L,t558=0xC300000000005585L;
  Mem m=new Mem();NonvolatileBits n=nv(0x660000000000L);VolatileBits z=v(0x770000000000L);
  VolatileBits initial=q(z,z.raxBits(),inputC,z.rdxBits(),z.r8Bits(),z.r9Bits(),z.r10Bits(),z.r11Bits());
  VolatileBits a0=v(0x880000000000L),a=q(a0,0xCAFE000000000002L,0xFEED0000AABBCCD0L,a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits());
  VolatileBits b0=v(0x990000000000L),b=q(b0,0xFED1000001234567L,b0.rcxBits(),b0.rdxBits(),b0.r8Bits(),b0.r9Bits(),b0.r10Bits(),b0.r11Bits()),c=v(0xAA0000000000L),d=v(0xBB0000000000L),e=v(0xCC0000000000L);
  NonvolatileBits active=new NonvolatileBits(lowC,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putD(G+0xBC,0x80000200);m.b.putQ(I+0x43DA798L,t798);m.b.putQ(I+0x43DA778L,old778);m.b.putQ(I+0x43DA558L,old558);
  List<Call> expected=List.of(new Call(0x424228CL,TargetKind.DIRECT_RVA,0x42591F8L,W,initial,active),
   new Call(0x42422ADL,TargetKind.INDIRECT_ABSOLUTE,t798,W,q(a,G,a.rcxBits(),0x00800002L,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),active),
   new Call(0x42422B8L,TargetKind.INDIRECT_ABSOLUTE,t778,W,q(b,b.raxBits(),b.raxBits(),lowC,b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits()),active),
   new Call(0x42422C0L,TargetKind.DIRECT_RVA,0x42422D0L,W,q(c,c.raxBits(),lowC,c.rdxBits(),c.r8Bits(),c.r9Bits(),c.r10Bits(),c.r11Bits()),active),
   new Call(0x42422C7L,TargetKind.INDIRECT_ABSOLUTE,t558,W,q(d,d.raxBits(),lowC,d.rdxBits(),d.r8Bits(),d.r9Bits(),d.r10Bits(),d.r11Bits()),active));
  List<Call> seen=new ArrayList<>();List<VolatileBits> replies=List.of(a,b,c,d,e);long[] next={0x4242291L,0x42422B3L,0x42422BEL,0x42422C5L,0x42422CDL};
  Ports ports=new Ports() {
   @Override public long readGsQword60() {m.b.ops.add(new Op("gs60",0x60,G));return G;}
   @Override public VolatileBits invoke(Call call) {
    int k=seen.size();seen.add(call);assertEquals(expected.get(k),call);assertEquals(I+next[k],m.b.rawQ(W-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));
    if(k==1)m.writeQword(I+0x43DA778L,t778);if(k==3)m.writeQword(I+0x43DA558L,t558);return replies.get(k);
   }
  };
  assertThrows(UnsupportedOperationException.class,()->TerminalAbort4242284215.execute(new Entry(I,E,initial,n),m,ports));assertEquals(expected,seen);
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("wq",W-8,I+0x4242291L),new Op("call",0x424228CL,0x42591F8L),new Op("gs60",0x60,G),new Op("rd",G+0xBC,0x80000200L),
   new Op("rq",I+0x43DA798L,t798),new Op("wq",W-8,I+0x42422B3L),new Op("call",0x42422ADL,t798),new Op("wq",I+0x43DA778L,t778),new Op("rq",I+0x43DA778L,t778),new Op("wq",W-8,I+0x42422BEL),new Op("call",0x42422B8L,t778),
   new Op("wq",W-8,I+0x42422C5L),new Op("call",0x42422C0L,0x42422D0L),new Op("wq",I+0x43DA558L,t558),new Op("rq",I+0x43DA558L,t558),new Op("wq",W-8,I+0x42422CDL),new Op("call",0x42422C7L,t558)),m.b.ops);
 }

 @Test void actualParent227eOwnsSlotAndEntersChild215() {
  long I=0x1C0000000L,E=0x760000000108L,PW=E-0x58,CE=E-0x60,CW=E-0x88,inputC=0x5555AABBF1230041L,lowC=0xF1230041L,t558=0xD400000000005581L;
  Mem m=new Mem();NonvolatileBits n=nv(0xDD0000000000L);VolatileBits z=v(0xEE0000000000L);
  VolatileBits initial=q(z,z.raxBits(),inputC,0xAABB000081234567L,0x1234567800000007L,z.r9Bits(),z.r10Bits(),z.r11Bits()),h=v(0x1100000000000L);
  VolatileBits childV=q(h,h.raxBits(),lowC,h.rdxBits(),h.r8Bits(),h.r9Bits(),h.r10Bits(),h.r11Bits());
  VolatileBits a0=v(0x1200000000000L),a=q(a0,0xFEDC000000000001L,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits()),b=v(0x1300000000000L),c=v(0x1400000000000L);
  NonvolatileBits active=new NonvolatileBits(lowC,E-8,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(E,0xE500000000001234L);m.b.putQ(I+0x43DA558L,t558);
  List<Call> expected=List.of(new Call(0x4242266L,TargetKind.DIRECT_RVA,0x42420C0L,PW,q(initial,2,E-0x38,E-0x30,E-0x28,E-0x34,initial.r10Bits(),initial.r11Bits()),active),
   new Call(0x424228CL,TargetKind.DIRECT_RVA,0x42591F8L,CW,childV,active),
   new Call(0x42422C0L,TargetKind.DIRECT_RVA,0x42422D0L,CW,q(a,a.raxBits(),lowC,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),active),
   new Call(0x42422C7L,TargetKind.INDIRECT_ABSOLUTE,t558,CW,q(b,b.raxBits(),lowC,b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits()),active));
  List<Call> seen=new ArrayList<>();List<VolatileBits> replies=List.of(h,a,b,c);long[] next={0x424226BL,0x4242291L,0x42422C5L,0x42422CDL};
  Ports fallback=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    int k=seen.size();seen.add(call);assertEquals(expected.get(k),call);assertEquals(I+next[k],m.b.rawQ(k==0?PW-8:CW-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));
    if(k==0)m.writeDword(E+0x18,0);return replies.get(k);
   }
  };
  TerminalAbort4242284215.Calls60 bound=TerminalAbort4242284215Calls.bind(I,m,fallback);List<Call> dispatched=new ArrayList<>();
  Ports observing=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    if(call.callSiteRva()==0x424227EL) {
     assertEquals(new Call(0x424227EL,TargetKind.DIRECT_RVA,0x4242284L,PW,childV,active),call);assertEquals(I+0x4242283L,m.b.rawQ(PW-8));dispatched.add(call);m.b.ops.add(new Op("bind",call.callSiteRva(),call.targetBits()));
    }
    return bound.invoke(call);
   }
  };
  assertThrows(UnsupportedOperationException.class,()->TerminalTailTarget42421c8213.execute(new Entry(I,E,initial,n),m,observing));
  assertEquals(expected,seen);assertEquals(1,dispatched.size());assertEquals(I+0x4242283L,m.b.rawQ(CE));assertEquals(lowC,m.b.rawQ(CE-8));
  assertEquals(List.of(new Op("wq",E+8,n.rbxBits()),new Op("wd",E+0x18,7),new Op("wd",E+0x10,0x81234567L),new Op("wq",E-8,n.rbpBits()),
   new Op("wb",E+0x20,0),new Op("wq",E-0x28,E+0x10),new Op("wq",E-0x20,E+0x18),new Op("wq",E-0x18,E+0x20),new Op("wd",E-0x34,2),new Op("wd",E-0x30,2),new Op("wq",PW-8,I+0x424226BL),new Op("call",0x4242266L,0x42420C0L),new Op("wd",E+0x18,0),new Op("rd",E+0x18,0),
   new Op("wq",PW-8,I+0x4242283L),new Op("bind",0x424227EL,0x4242284L),new Op("wq",CE-8,lowC),new Op("wq",CW-8,I+0x4242291L),new Op("call",0x424228CL,0x42591F8L),new Op("wq",CW-8,I+0x42422C5L),new Op("call",0x42422C0L,0x42422D0L),new Op("rq",I+0x43DA558L,t558),new Op("wq",CW-8,I+0x42422CDL),new Op("call",0x42422C7L,t558)),m.b.ops);
 }

}
