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
public final class OutHelper424e620218WitnessTest {
 static Bits128 x(long b) { return new Bits128(b,b+1); }
 static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
 static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
 static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
 static class Ports implements TerminalAbort4242284215.Calls60 {
  java.util.function.Function<Call,VolatileBits> invoke=c->{throw new AssertionError(c);};
  java.util.function.Function<Tail,NormalReturn> tail=t->{throw new AssertionError(t);};
  java.util.function.LongSupplier readGsQword58=()->{throw new AssertionError("GS58");};
  java.util.function.LongSupplier readGsQword60=()->{throw new AssertionError("GS60");};
  public VolatileBits invoke(Call c) { return invoke.apply(c); }
  public NormalReturn tail(Tail t) { return tail.apply(t); }
  public long readGsQword58() { return readGsQword58.getAsLong(); }
  public long readGsQword60() { return readGsQword60.getAsLong(); }
 }
@Test void resolverZeroRestoresFreshSlotsAndExplicitErrorEax218() {
    long E = 0x7E0000000108L, I = 0x140000000L, W = E - 0x28L;
    long rcx = 0x1234567890ABCDEFL;
    VolatileBits z = v(0x100L), vIn = q(z, z.raxBits(), rcx, z.rdxBits(), z.r8Bits(), z.r9Bits(), z.r10Bits(), z.r11Bits());
    NonvolatileBits nvIn = nv(0x200L);
    Entry entry = new Entry(I, E, vIn, nvIn);
    Mem m = new Mem();
    Ports p = new Ports();
    List<Op> ops = new ArrayList<>();
    p.invoke = c -> {
        ops.add(new Op("call", c.callSiteRva(), c.targetBits()));
        assertEquals(0x424E643L, c.callSiteRva());
        assertEquals(I + 0x424E648L, m.b.rawQ(W - 8));
        m.b.ops.add(new Op("call", c.callSiteRva(), c.targetBits()));
        assertEquals(TargetKind.DIRECT_RVA, c.kind());
        assertEquals(0x424E448L, c.targetBits());
        assertEquals(W, c.rspBits());
        assertEquals(q(vIn, vIn.raxBits(), 0x1CL, I + 0x4427010L, I + 0x442700CL, I + 0x4427010L, vIn.r10Bits(), vIn.r11Bits()), c.volatileBits());
        assertEquals(new NonvolatileBits(rcx, nvIn.rbpBits(), nvIn.rsiBits(), nvIn.rdiBits(), nvIn.r12Bits(), nvIn.r13Bits(), nvIn.r14Bits(), nvIn.r15Bits(), nvIn.xmm6()), c.nonvolatileBits());
        m.writeQword(E - 8L, 0xCAFEBABE00000000L);
        m.writeQword(E, 0xDEADBEEF00000000L);
        return q(vIn, 0L, vIn.rcxBits(), vIn.rdxBits(), vIn.r8Bits(), vIn.r9Bits(), vIn.r10Bits(), vIn.r11Bits());
    };
    p.tail = t -> { throw new AssertionError("tail"); };
    p.readGsQword58 = () -> { throw new AssertionError("gs58"); };
    p.readGsQword60 = () -> { throw new AssertionError("gs60"); };
    NormalReturn nr = OutHelper424e620218.execute(entry, m, p);
    assertEquals(0x00000000C0000225L, nr.volatileBits().raxBits());
    assertEquals(vIn.rcxBits(), nr.volatileBits().rcxBits());
    assertEquals(vIn.rdxBits(), nr.volatileBits().rdxBits());
    assertEquals(vIn.r8Bits(), nr.volatileBits().r8Bits());
    assertEquals(vIn.r9Bits(), nr.volatileBits().r9Bits());
    assertEquals(vIn.r10Bits(), nr.volatileBits().r10Bits());
    assertEquals(vIn.r11Bits(), nr.volatileBits().r11Bits());
    assertEquals(vIn.xmm0(), nr.volatileBits().xmm0());
    assertEquals(vIn.xmm1(), nr.volatileBits().xmm1());
    assertEquals(vIn.xmm2(), nr.volatileBits().xmm2());
    assertEquals(vIn.xmm3(), nr.volatileBits().xmm3());
    assertEquals(vIn.xmm4(), nr.volatileBits().xmm4());
    assertEquals(vIn.xmm5(), nr.volatileBits().xmm5());
    assertEquals(0xDEADBEEF00000000L, nr.returnRipBits());
    assertEquals(E + 8L, nr.callerRspBits());
    assertEquals(0xCAFEBABE00000000L, nr.nonvolatileBits().rbxBits());
    assertEquals(nvIn.rbpBits(), nr.nonvolatileBits().rbpBits());
    assertEquals(nvIn.rsiBits(), nr.nonvolatileBits().rsiBits());
    assertEquals(nvIn.rdiBits(), nr.nonvolatileBits().rdiBits());
    assertEquals(nvIn.r12Bits(), nr.nonvolatileBits().r12Bits());
    assertEquals(nvIn.r13Bits(), nr.nonvolatileBits().r13Bits());
    assertEquals(nvIn.r14Bits(), nr.nonvolatileBits().r14Bits());
    assertEquals(nvIn.r15Bits(), nr.nonvolatileBits().r15Bits());
    assertEquals(nvIn.xmm6(), nr.nonvolatileBits().xmm6());
    assertEquals(1, ops.size());
    assertEquals(List.of(new Op("wq", E - 8, nvIn.rbxBits()), new Op("wq", W - 8, I + 0x424E648L),
            new Op("call", 0x424E643L, 0x424E448L), new Op("wq", E - 8, 0xCAFEBABE00000000L),
            new Op("wq", E, 0xDEADBEEF00000000L), new Op("rq", E - 8, 0xCAFEBABE00000000L),
            new Op("rq", E, 0xDEADBEEF00000000L)), m.b.ops);
    assertEquals("call", ops.get(0).kind());
}
 @Test void resolverNonzeroPopsBeforeFreshTailAndReturnsExactObject218() {
  long I=0x180000000L,E=0x7F0000000108L,W=E-0x28,inputC=0xABCDEF0123456789L,freshBx=0xB100000000001234L,oldTarget=0xA20000000000BBA2L,target=0xC30000000000BBA3L;
  Mem m=new Mem();NonvolatileBits n=nv(0x110000000000L);VolatileBits z=v(0x220000000000L),initial=q(z,z.raxBits(),inputC,z.rdxBits(),z.r8Bits(),z.r9Bits(),z.r10Bits(),z.r11Bits());
  VolatileBits a0=v(0x330000000000L),a=q(a0,0x9000000000000000L,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits());
  NonvolatileBits active=new NonvolatileBits(inputC,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6()),restored=new NonvolatileBits(freshBx,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  NormalReturn supplied=new NormalReturn(v(0x440000000000L),0xD400000000004444L,0xE500000000005555L,nv(0x550000000000L));
  m.b.putQ(E,0xEF66000000001234L);m.b.putQ(I+0x43DBBA8L,oldTarget);List<Call> calls=new ArrayList<>();List<Tail> tails=new ArrayList<>();Ports ports=new Ports();
  ports.invoke=call->{calls.add(call);assertEquals(new Call(0x424E643L,TargetKind.DIRECT_RVA,0x424E448L,W,q(initial,initial.raxBits(),0x1C,I+0x4427010L,I+0x442700CL,I+0x4427010L,initial.r10Bits(),initial.r11Bits()),active),call);assertEquals(I+0x424E648L,m.b.rawQ(W-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));m.writeQword(E-8,freshBx);m.writeQword(I+0x43DBBA8L,target);return a;};
  ports.tail=tail->{tails.add(tail);assertEquals(new Tail(0x424E65CL,TargetKind.INDIRECT_ABSOLUTE,target,new Entry(I,E,q(a,a.raxBits(),-6,inputC,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),restored)),tail);m.b.ops.add(new Op("tail",tail.jumpSiteRva(),tail.targetBits()));return supplied;};
  NormalReturn got=OutHelper424e620218.execute(new Entry(I,E,initial,n),m,ports);assertSame(supplied,got);assertEquals(1,calls.size());assertEquals(1,tails.size());
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("wq",W-8,I+0x424E648L),new Op("call",0x424E643L,0x424E448L),new Op("wq",E-8,freshBx),new Op("wq",I+0x43DBBA8L,target),new Op("rq",E-8,freshBx),new Op("rq",I+0x43DBBA8L,target),new Op("tail",0x424E65CL,target)),m.b.ops);
 }

 @Test void actualParent217OutCallUsesTailChildThenFreshPostDword218() {
  long I=0x1C0000000L,E=0x800000000108L,PW=E-0x28,CE=E-0x30,CW=E-0x58,out=E+8,G=0x610000000000L,P=0x620000000000L,target=0xA60000000000BBA6L,rip=0xEF77000000001234L;
  Mem m=new Mem();NonvolatileBits n=nv(0x660000000000L);VolatileBits initial=v(0x770000000000L),a0=v(0x880000000000L),a=q(a0,0x9000000000000000L,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits()),tailV=v(0x990000000000L);
  NonvolatileBits parentActive=new NonvolatileBits(0,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6()),childActive=new NonvolatileBits(out,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  VolatileBits parentCallV=q(initial,G,out,initial.rdxBits(),initial.r8Bits(),initial.r9Bits(),initial.r10Bits(),initial.r11Bits());NormalReturn supplied=new NormalReturn(tailV,I+0x4259220L,PW,parentActive);
  m.b.putQ(E,rip);m.b.putQ(out,0xA7A6A5A4A3A2A1A0L);m.b.putQ(G+0x20,P);m.b.putD(P+8,0);m.b.putQ(I+0x43DBBA8L,target);List<Call> calls=new ArrayList<>();List<Tail> tails=new ArrayList<>();Ports fallback=new Ports();
  fallback.readGsQword60=()->{m.b.ops.add(new Op("gs60",0x60,G));assertEquals(0,m.b.rawD(out));return G;};
  fallback.invoke=call->{calls.add(call);assertEquals(new Call(0x424E643L,TargetKind.DIRECT_RVA,0x424E448L,CW,q(parentCallV,G,0x1C,I+0x4427010L,I+0x442700CL,I+0x4427010L,initial.r10Bits(),initial.r11Bits()),childActive),call);assertEquals(I+0x424E648L,m.b.rawQ(CW-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));return a;};
  fallback.tail=tail->{tails.add(tail);assertEquals(new Tail(0x424E65CL,TargetKind.INDIRECT_ABSOLUTE,target,new Entry(I,CE,q(a,a.raxBits(),-6,out,a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),parentActive)),tail);m.b.ops.add(new Op("tail",tail.jumpSiteRva(),tail.targetBits()));m.writeDword(out,1);return supplied;};
  TerminalAbort4242284215.Calls60 bound=OutHelper424e620218Calls.bind(I,m,fallback);List<VolatileBits> returned=new ArrayList<>();Ports observing=new Ports();observing.readGsQword60=bound::readGsQword60;
  observing.invoke=call->{assertEquals(new Call(0x425921BL,TargetKind.DIRECT_RVA,0x424E620L,PW,parentCallV,parentActive),call);assertEquals(I+0x4259220L,m.b.rawQ(CE));m.b.ops.add(new Op("bind",call.callSiteRva(),call.targetBits()));VolatileBits value=bound.invoke(call);returned.add(value);return value;};
  NormalReturn got=GsFlag42591f8217.execute(new Entry(I,E,initial,n),m,observing);assertEquals(1,calls.size());assertEquals(1,tails.size());assertEquals(1,returned.size());assertSame(tailV,returned.get(0));
  assertEquals(new NormalReturn(q(tailV,0,tailV.rcxBits(),tailV.rdxBits(),tailV.r8Bits(),tailV.r9Bits(),tailV.r10Bits(),tailV.r11Bits()),rip,E+8,n),got);assertEquals(0xA7A6A5A400000001L,m.b.rawQ(out));
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("wd",out,0),new Op("gs60",0x60,G),new Op("rq",G+0x20,P),new Op("rd",P+8,0),new Op("wq",PW-8,I+0x4259220L),new Op("bind",0x425921BL,0x424E620L),new Op("wq",CE-8,0),new Op("wq",CW-8,I+0x424E648L),new Op("call",0x424E643L,0x424E448L),new Op("rq",CE-8,0),new Op("rq",I+0x43DBBA8L,target),new Op("tail",0x424E65CL,target),new Op("wd",out,1),new Op("rd",out,1),new Op("rq",E-8,n.rbxBits()),new Op("rq",E,rip)),m.b.ops);
 }

}
