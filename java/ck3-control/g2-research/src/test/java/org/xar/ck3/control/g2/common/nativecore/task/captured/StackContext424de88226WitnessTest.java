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
public final class StackContext424de88226WitnessTest {
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
 static void ck(Call c,long site,TargetKind kind,long target,long work,VolatileBits value,NonvolatileBits n,Mem32 m,long image,int len) {
  assertEquals(new Call(site,kind,target,work,value,n),c);assertEquals(image+site+len,m.b.rawQ(work-8));
 }
 record Exchange(long address,int before,int after) { }
 static final class Mem32 implements DispatchMiddle42420f8224.Memory32 {
  final Mem base=new Mem();
  final LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes b=base.b;
  final List<Exchange> exchanges=new ArrayList<>();
  public int exchangeDword(long a,int value) {
   int old=b.rawD(a);exchanges.add(new Exchange(a,old,value));b.ops.add(new Op("xchg32",a,Integer.toUnsignedLong(value)));b.putD(a,value);return old;
  }
  public int readDword(long a) {return base.readDword(a);}
  public long readQword(long a) {return base.readQword(a);}
  public int readUnsignedByte(long a) {return base.readUnsignedByte(a);}
  public void writeDword(long a,int value) {base.writeDword(a,value);}
  public void writeQword(long a,long value) {base.writeQword(a,value);}
  public void writeByte(long a,int value) {base.writeByte(a,value);}
  public int lockedXaddDword(long a,int addend) {return base.lockedXaddDword(a,addend);}
  public Bits128 read128(long a) {return base.read128(a);}
  public void write128(long a,Bits128 value) {base.write128(a,value);}
  public int readUnsigned16(long a) {return base.readUnsigned16(a);}
 }

@Test void directFramePreservesDwordNeighborsAndFreshRet226() {
    long image = 0x100000000L;
    long E = 0x200000000L;
    long W = E - 0x38L;
    long entryRCX = 0x1111111111111111L;
    long entryR10 = 0x2222222222222222L;
    long entryR11 = 0x3333333333333333L;
    long seedE10 = 0x4444444444444444L;
    int seedHigh18 = 0x55555555;
    int seedHigh20 = 0x66666666;
    long seedRet = 0x7777777777777777L;
    long newRet = 0x8888888888888888L;

    Mem32 m = new Mem32();
    m.b.putQ(E + 0x10L, seedE10);
    m.b.putD(E + 0x18L + 4L, seedHigh18);
    m.b.putD(E + 0x20L + 4L, seedHigh20);
    m.b.putQ(E, seedRet);

    VolatileBits entryV = new VolatileBits(
        entryRCX + 0x80L, entryRCX, entryRCX + 2, entryRCX + 3, entryRCX + 4, entryR10, entryR11,
        x(entryRCX + 10), x(entryRCX + 20), x(entryRCX + 30), x(entryRCX + 40), x(entryRCX + 50), x(entryRCX + 60)
    );
    NonvolatileBits entryNV = nv(entryRCX);
    Entry entry = new Entry(image, E, entryV, entryNV);
    VolatileBits reply = v(0x8A00000000010000L);

    Ports p = new Ports();
    p.invoke = c -> {
        ck(c, 0x424DEB8L, TargetKind.DIRECT_RVA, 0x424DB74L, W,
            q(entryV, 2L, E + 0x10L, E + 0x20L, E - 0x18L, E + 0x18L, entryR10, E), entryNV, m, image, 5);
        assertEquals(seedE10, m.b.rawQ(E + 0x10L));
        assertEquals(2, m.b.rawD(E + 0x18L));
        assertEquals(seedHigh18, m.b.rawD(E + 0x18L + 4L));
        assertEquals(2, m.b.rawD(E + 0x20L));
        assertEquals(seedHigh20, m.b.rawD(E + 0x20L + 4L));
        m.b.putQ(E, newRet);
        return reply;
    };

    NormalReturn nr = StackContext424de88226.execute(entry, m, p);

    assertEquals(newRet, nr.returnRipBits());
    assertEquals(E + 8L, nr.callerRspBits());
    assertEquals(entryNV, nr.nonvolatileBits());
    assertEquals(reply, nr.volatileBits());

    List<Op> ops = m.b.ops;
    assertEquals(6, ops.size());
    assertEquals("wq", ops.get(0).kind()); assertEquals(E + 8L, ops.get(0).address()); assertEquals(entryRCX, ops.get(0).value());
    assertEquals("wq", ops.get(1).kind()); assertEquals(E - 0x18L, ops.get(1).address()); assertEquals(E + 8L, ops.get(1).value());
    assertEquals("wd", ops.get(2).kind()); assertEquals(E + 0x18L, ops.get(2).address()); assertEquals(2L, ops.get(2).value());
    assertEquals("wd", ops.get(3).kind()); assertEquals(E + 0x20L, ops.get(3).address()); assertEquals(2L, ops.get(3).value());
    assertEquals("wq", ops.get(4).kind()); assertEquals(W - 8L, ops.get(4).address()); assertEquals(image + 0x424DEB8L + 5L, ops.get(4).value());
    assertEquals("rq", ops.get(5).kind()); assertEquals(E, ops.get(5).address()); assertEquals(newRet, ops.get(5).value());
}
 @Test void actual224ParentUsesNewChildThenOpaqueExit226() {
  long I=0x100000000L,S=0x800000000L,W=S-0x28L,E=S-0x30L,CW=E-0x38L;
  long P=0x500000000L,A=0x600000000L,B=0x700000000L;
  long originalRet=0x8A00000000000100L,freshRet=0x8B00000000000200L,freshBX=0x8C00000000000300L;
  long unknown=0x8D00000000000400L; int high18=0x8E001122,high20=0x8F003344;
  Mem32 m=new Mem32();
  m.b.putQ(S,originalRet);m.b.putQ(P,A);m.b.putQ(P+8,B);m.b.putD(A,1);m.b.putD(B,1);
  m.b.putB(I+0x5C5D2E8L,0);m.b.putD(I+0x5C5D2DCL,0x80000007);
  m.b.putQ(E+0x10,unknown);m.b.putD(E+0x1C,high18);m.b.putD(E+0x24,high20);
  VolatileBits base=v(0x8100000000001000L);
  VolatileBits incoming=q(base,base.raxBits(),P,base.rdxBits(),base.r8Bits(),base.r9Bits(),base.r10Bits(),base.r11Bits());
  NonvolatileBits n=nv(0x8200000000002000L),active=nd(n,P,n.rdiBits());
  VolatileBits childReply=v(0x8300000000003000L),exitReply=v(0x8400000000004000L);
  VolatileBits parentCallV=q(incoming,A,I+0x5C5D6B0L,incoming.rdxBits(),incoming.r8Bits(),incoming.r9Bits(),incoming.r10Bits(),incoming.r11Bits());
  VolatileBits childCallV=q(incoming,2,E+0x10,E+0x20,E-0x18,E+0x18,incoming.r10Bits(),E);
  VolatileBits exitCallV=q(childReply,A,I+0x441ED78L,I+0x441ED80L,childReply.r8Bits(),childReply.r9Bits(),childReply.r10Bits(),childReply.r11Bits());
  Ports fallback=new Ports();int[] opaque={0},matching={0};
  fallback.invoke=c->{
   int ordinal=opaque[0]++;
   if(ordinal==0) {
    ck(c,0x424DEB8L,TargetKind.DIRECT_RVA,0x424DB74L,CW,childCallV,active,m,I,5);
    assertEquals(I+0x5C5D6B0L,m.b.rawQ(E+8));assertEquals(E+8,m.b.rawQ(E-0x18));
    assertEquals(unknown,m.b.rawQ(E+0x10));
    assertEquals(2,m.b.rawD(E+0x18));assertEquals(high18,m.b.rawD(E+0x1C));
    assertEquals(2,m.b.rawD(E+0x20));assertEquals(high20,m.b.rawD(E+0x24));
    assertEquals(I+0x4242167L,m.b.rawQ(E));
    return childReply;
   }
   assertEquals(1,ordinal);
   ck(c,0x4242191L,TargetKind.DIRECT_RVA,0x424E1ACL,W,exitCallV,active,m,I,5);
   m.b.putQ(S-8,freshBX);m.b.putQ(S,freshRet);
   return exitReply;
  };
  var bound=StackContext424de88226Calls.bind(I,m,fallback);
  Ports observing=new Ports();
  observing.invoke=c->{
   if(c.callSiteRva()==0x4242162L) {
    assertEquals(0,matching[0]++);
    ck(c,0x4242162L,TargetKind.DIRECT_RVA,0x424DE88L,W,parentCallV,active,m,I,5);
   }
   return bound.invoke(c);
  };
  observing.tail=bound::tail;observing.readGsQword58=bound::readGsQword58;observing.readGsQword60=bound::readGsQword60;
  NormalReturn result=DispatchMiddle42420f8224.execute(new Entry(I,S,incoming,n),m,observing);
  assertEquals(new NormalReturn(q(exitReply,B,exitReply.rcxBits(),exitReply.rdxBits(),exitReply.r8Bits(),exitReply.r9Bits(),exitReply.r10Bits(),exitReply.r11Bits()),freshRet,S+8,nd(n,freshBX,n.rdiBits())),result);
  assertEquals(2,opaque[0]);assertEquals(1,matching[0]);
  assertEquals(List.of(new Exchange(I+0x5C5D2DCL,0x80000007,1)),m.exchanges);
  assertEquals(List.of(
   new Op("wq",S-8,n.rbxBits()),new Op("rb",I+0x5C5D2E8L,0),new Op("xchg32",I+0x5C5D2DCL,1),
   new Op("rq",P,A),new Op("rd",A,1),new Op("wq",E,I+0x4242167L),
   new Op("wq",E+8,I+0x5C5D6B0L),new Op("wq",E-0x18,E+8),new Op("wd",E+0x18,2),new Op("wd",E+0x20,2),
   new Op("wq",CW-8,I+0x424DEBDL),new Op("rq",E,I+0x4242167L),
   new Op("rq",P,A),new Op("rd",A,1),new Op("wq",E,I+0x4242196L),
   new Op("rq",P+8,B),new Op("rd",B,1),new Op("rq",S-8,freshBX),new Op("rq",S,freshRet)),m.b.ops);
  assertEquals(unknown,m.b.rawQ(E+0x10));assertEquals(high18,m.b.rawD(E+0x1C));assertEquals(high20,m.b.rawD(E+0x24));
  assertEquals(0,m.b.rawB(I+0x5C5D2E8L));
 }

}
