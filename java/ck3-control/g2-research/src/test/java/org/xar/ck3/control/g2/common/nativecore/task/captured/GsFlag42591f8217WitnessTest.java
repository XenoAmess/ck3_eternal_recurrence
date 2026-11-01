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
public final class GsFlag42591f8217WitnessTest {
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
    @Test
    public void signedNegativeReturnsOneAndRestoresFreshRam217() {
        long E = 0x7B0000000108L;
        long I = 0x140000000L;
        long G = 0x9000000000000000L;
        long P = 0x8000000000000000L;
        long W = E - 0x28L;
        long savedRBX = 0x1111111111111111L;
        long retRip = 0x2222222222222222L;
        long poison = 0x3333333333333333L;

        Mem m = new Mem();
        m.b.putQ(E - 8, savedRBX);
        m.b.putQ(E, retRip);
        m.b.putQ(E + 8, poison);
        m.b.putQ(G + 0x20, P);
        m.b.putD(P + 8, -1);

        List<String> events = new ArrayList<>();
        long[] gsCount = {0};

        Ports ports = new Ports() {
            @Override public long readGsQword60() {
                events.add("gs60");
                gsCount[0]++;
                if (gsCount[0] > 1) throw new AssertionError("GS60 called more than once");
                if (m.b.rawD(E + 8) != 0) throw new AssertionError("Slot E+8 not zero before GS");
                m.b.ops.add(new Op("gs60", 0x60, G));
                m.writeQword(E - 8, 0x4444444444444444L);
                m.writeQword(E, 0x5555555555555555L);
                return G;
            }
        };

        Entry entry = new Entry(I, E, v(0x1000L), nv(0x2000L));
        NormalReturn nr = GsFlag42591f8217.execute(entry, m, ports);

        assertEquals(1, gsCount[0]);
        assertEquals(0, events.size() - 1);
        assertEquals("gs60", events.get(0));

        assertEquals(0x4444444444444444L, nr.nonvolatileBits().rbxBits());
        assertEquals(0x5555555555555555L, nr.returnRipBits());
        assertEquals(E + 8, nr.callerRspBits());
        assertEquals(0x3333333300000000L, m.b.rawQ(E + 8));
        assertEquals(List.of(new Op("wq", E - 8, entry.nonvolatileBits().rbxBits()), new Op("wd", E + 8, 0),
                new Op("gs60", 0x60, G), new Op("wq", E - 8, 0x4444444444444444L), new Op("wq", E, 0x5555555555555555L),
                new Op("rq", G + 0x20, P), new Op("rd", P + 8, 0xFFFFFFFFL),
                new Op("rq", E - 8, 0x4444444444444444L), new Op("rq", E, 0x5555555555555555L)), m.b.ops);

        VolatileBits expectedV = q(entry.volatileBits(), 1L, P, entry.volatileBits().rdxBits(), entry.volatileBits().r8Bits(), entry.volatileBits().r9Bits(), entry.volatileBits().r10Bits(), entry.volatileBits().r11Bits());
        assertEquals(expectedV, nr.volatileBits());

        assertEquals(entry.nonvolatileBits().rbpBits(), nr.nonvolatileBits().rbpBits());
        assertEquals(entry.nonvolatileBits().rsiBits(), nr.nonvolatileBits().rsiBits());
        assertEquals(entry.nonvolatileBits().rdiBits(), nr.nonvolatileBits().rdiBits());
        assertEquals(entry.nonvolatileBits().r12Bits(), nr.nonvolatileBits().r12Bits());
        assertEquals(entry.nonvolatileBits().r13Bits(), nr.nonvolatileBits().r13Bits());
        assertEquals(entry.nonvolatileBits().r14Bits(), nr.nonvolatileBits().r14Bits());
        assertEquals(entry.nonvolatileBits().r15Bits(), nr.nonvolatileBits().r15Bits());
        assertEquals(entry.nonvolatileBits().xmm6(), nr.nonvolatileBits().xmm6());
    }
 @Test void nonnegativeFreshPostDwordChoosesZeroOrOne217() {
  int[] post={1,0x80000001};long[] finalRax={0,1};int[] flags={0,0x7FFFFFFF};
  for(int k=0;k<2;k++) {
   int supplied=post[k],flag=flags[k];long wanted=finalRax[k],I=0x180000000L,E=0x7C0000000108L,W=E-0x28,G=0x610000000000L+k*0x10000L,P=0x620000000000L+k*0x10000L,rip=0xEF11000000001234L+k,poison=0xA7A6A5A4A3A2A1A0L;
   Mem m=new Mem();NonvolatileBits n=nv(0x110000000000L+k*0x1000L);VolatileBits initial=v(0x220000000000L+k*0x1000L),reply=v(0x330000000000L+k*0x1000L);
   NonvolatileBits active=new NonvolatileBits(0,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
   m.b.putQ(E,rip);m.b.putQ(E+8,poison);m.b.putQ(G+0x20,P);m.b.putD(P+8,flag);List<Call> seen=new ArrayList<>();
   Ports ports=new Ports() {
    @Override public long readGsQword60() {m.b.ops.add(new Op("gs60",0x60,G));assertEquals(0,m.b.rawD(E+8));return G;}
    @Override public VolatileBits invoke(Call call) {
     seen.add(call);assertEquals(new Call(0x425921BL,TargetKind.DIRECT_RVA,0x424E620L,W,q(initial,G,E+8,initial.rdxBits(),initial.r8Bits(),initial.r9Bits(),initial.r10Bits(),initial.r11Bits()),active),call);
     assertEquals(I+0x4259220L,m.b.rawQ(W-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));m.writeDword(E+8,supplied);return reply;
    }
   };
   NormalReturn got=GsFlag42591f8217.execute(new Entry(I,E,initial,n),m,ports);assertEquals(1,seen.size());
   assertEquals(new NormalReturn(q(reply,wanted,reply.rcxBits(),reply.rdxBits(),reply.r8Bits(),reply.r9Bits(),reply.r10Bits(),reply.r11Bits()),rip,E+8,n),got);
   assertEquals(0xA7A6A5A400000000L|Integer.toUnsignedLong(supplied),m.b.rawQ(E+8));
   assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("wd",E+8,0),new Op("gs60",0x60,G),new Op("rq",G+0x20,P),new Op("rd",P+8,Integer.toUnsignedLong(flag)),new Op("wq",W-8,I+0x4259220L),new Op("call",0x425921BL,0x424E620L),new Op("wd",E+8,Integer.toUnsignedLong(supplied)),new Op("rd",E+8,Integer.toUnsignedLong(supplied)),new Op("rq",E-8,n.rbxBits()),new Op("rq",E,rip)),m.b.ops);
  }
 }

 @Test void actualParent215FirstCallConsumesNegativeChild217() {
  long I=0x1C0000000L,E=0x7D0000000108L,PW=E-0x28,CE=E-0x30,G=0x630000000000L,P=0x640000000000L,lowC=0xF500008BL,t558=0xA100000000005581L;
  Mem m=new Mem();NonvolatileBits n=nv(0x440000000000L);VolatileBits z=v(0x550000000000L),initial=q(z,z.raxBits(),0xABCD0066F500008BL,z.rdxBits(),z.r8Bits(),z.r9Bits(),z.r10Bits(),z.r11Bits()),b=v(0x660000000000L),c=v(0x770000000000L);
  VolatileBits childResult=q(initial,1,P,initial.rdxBits(),initial.r8Bits(),initial.r9Bits(),initial.r10Bits(),initial.r11Bits());
  NonvolatileBits active=new NonvolatileBits(lowC,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(G+0x20,P);m.b.putD(P+8,-1);m.b.putQ(PW,0xA7A6A5A4A3A2A1A0L);m.b.putQ(I+0x43DA558L,t558);
  List<Call> expected=List.of(new Call(0x42422C0L,TargetKind.DIRECT_RVA,0x42422D0L,PW,q(childResult,1,lowC,childResult.rdxBits(),childResult.r8Bits(),childResult.r9Bits(),childResult.r10Bits(),childResult.r11Bits()),active),new Call(0x42422C7L,TargetKind.INDIRECT_ABSOLUTE,t558,PW,q(b,b.raxBits(),lowC,b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits()),active));
  List<Call> seen=new ArrayList<>();List<VolatileBits> replies=List.of(b,c);long[] next={0x42422C5L,0x42422CDL};
  Ports fallback=new Ports() {
   @Override public long readGsQword60() {m.b.ops.add(new Op("gs60",0x60,G));return G;}
   @Override public VolatileBits invoke(Call call) {int k=seen.size();seen.add(call);assertEquals(expected.get(k),call);assertEquals(I+next[k],m.b.rawQ(PW-8));m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));return replies.get(k);}
  };
  TerminalAbort4242284215.Calls60 bound=GsFlag42591f8217Calls.bind(I,m,fallback);List<VolatileBits> returned=new ArrayList<>();
  Ports observing=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    if(call.callSiteRva()==0x424228CL){assertEquals(new Call(0x424228CL,TargetKind.DIRECT_RVA,0x42591F8L,PW,initial,active),call);assertEquals(I+0x4242291L,m.b.rawQ(CE));m.b.ops.add(new Op("bind",call.callSiteRva(),call.targetBits()));VolatileBits value=bound.invoke(call);returned.add(value);return value;}return bound.invoke(call);
   }
  };
  assertThrows(UnsupportedOperationException.class,()->TerminalAbort4242284215.execute(new Entry(I,E,initial,n),m,observing));assertEquals(expected,seen);assertEquals(List.of(childResult),returned);
  assertEquals(List.of(new Op("wq",E-8,n.rbxBits()),new Op("wq",PW-8,I+0x4242291L),new Op("bind",0x424228CL,0x42591F8L),new Op("wq",CE-8,lowC),new Op("wd",CE+8,0),new Op("gs60",0x60,G),new Op("rq",G+0x20,P),new Op("rd",P+8,0xFFFFFFFFL),new Op("rq",CE-8,lowC),new Op("rq",CE,I+0x4242291L),new Op("wq",PW-8,I+0x42422C5L),new Op("call",0x42422C0L,0x42422D0L),new Op("rq",I+0x43DA558L,t558),new Op("wq",PW-8,I+0x42422CDL),new Op("call",0x42422C7L,t558)),m.b.ops);
 }

}
