package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.DispatchMiddle42420f8224WitnessTest.Mem32;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class CallbackSpanStaticDispatch232WitnessTest {
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
 static void ck(Call c,long site,TargetKind kind,long target,long work,VolatileBits value,NonvolatileBits n,HookMemory32 m,long image,int len) {
  assertEquals(new Call(site,kind,target,work,value,n),c);assertEquals(image+site+len,m.b.rawQ(work-8));
 }
 static NonvolatileBits ns(NonvolatileBits n,long bx,long bp,long si,long di,long r14,long r15) {return new NonvolatileBits(bx,bp,si,di,n.r12Bits(),n.r13Bits(),r14,r15,n.xmm6());}
 static final class HookMemory32 implements DispatchMiddle42420f8224.Memory32 {
  final Mem32 base=new Mem32();
  final LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes b=base.b;
  List<Op> expected=List.of();int observed;
  java.util.function.BiConsumer<Long,Long> afterWriteQword=(a,value)->{};
  void emit() {assertTrue(observed<expected.size(),"unexpected RAM operation");assertEquals(expected.get(observed++),b.ops.get(b.ops.size()-1));}
  void done() {assertEquals(expected.size(),observed);assertEquals(expected,b.ops);}
  public int readDword(long a) {int z=base.readDword(a);emit();return z;}
  public long readQword(long a) {long z=base.readQword(a);emit();return z;}
  public int readUnsignedByte(long a) {int z=base.readUnsignedByte(a);emit();return z;}
  public void writeDword(long a,int z) {base.writeDword(a,z);emit();}
  public void writeQword(long a,long z) {base.writeQword(a,z);emit();afterWriteQword.accept(a,z);}
  public void writeByte(long a,int z) {base.writeByte(a,z);emit();}
  public int lockedXaddDword(long a,int z) {int q=base.lockedXaddDword(a,z);emit();return q;}
  public Bits128 read128(long a) {Bits128 z=base.read128(a);emit();return z;}
  public void write128(long a,Bits128 z) {base.write128(a,z);emit();}
  public int exchangeDword(long a,int value) {int z=base.exchangeDword(a,value);emit();return z;}
  public int readUnsigned16(long a) {int z=base.readUnsigned16(a);emit();return z;}
 }

@Test void normalTailIntegration() {
    long image = 0x1000000L;
    long E = 0x2000000L;
    long W = E - 0x28L;
    long start = 0x3000000L;
    long end = start + 8L;
    long element = 0xA400000000000400L;
    long iatTarget = image + 0x4267630L;
    long retRip = image + 0x424E1EFL;

    VolatileBits seedV = v(0xA100000000000100L);
    NonvolatileBits inN = nv(0xB100000000000100L);
    VolatileBits inV = q(seedV, seedV.raxBits(), start, end, seedV.r8Bits(), seedV.r9Bits(), seedV.r10Bits(), seedV.r11Bits());
    NonvolatileBits activeN = ns(inN, start, 0L, 0L, 1L, inN.r14Bits(), inN.r15Bits());
    VolatileBits callV = q(inV, element, inV.rcxBits(), inV.rdxBits(), inV.r8Bits(), inV.r9Bits(), inV.r10Bits(), inV.r11Bits());
    VolatileBits replyV = q(v(0x100000000L), 0x100000000L, 0x110L, 0x120L, 0x130L, 0x140L, 0x150L, 0x160L);
    NormalReturn opaqueNR = new NormalReturn(replyV, retRip, W, activeN);

    HookMemory32 m = new HookMemory32();
    m.b.putQ(image + 0x43DBBA8L, iatTarget);
    m.b.putQ(start, element);
    m.b.putQ(E + 8L, 0x5000000L);
    m.b.putQ(E + 0x10L, 0x6000000L);
    m.b.putQ(E + 0x18L, 0x7000000L);
    m.b.putQ(E - 8L, 0x8000000L);
    m.b.putQ(E, 0x9100000L);

    m.expected = List.of(
        new Op("wq", E + 8L, inN.rbxBits()),
        new Op("wq", E + 0x10L, inN.rbpBits()),
        new Op("wq", E + 0x18L, inN.rsiBits()),
        new Op("wq", E - 8L, inN.rdiBits()),
        new Op("rq", start, element),
        new Op("rq", image + 0x43DBBA8L, iatTarget),
        new Op("wq", W - 8L, retRip),
        new Op("rq", E + 8L, 0x5000000L),
        new Op("rq", E + 0x10L, 0x6000000L),
        new Op("rq", E + 0x18L, 0x7000000L),
        new Op("rq", E - 8L, 0x8000000L),
        new Op("rq", E, 0x9000000L)
    );
    m.observed = 0;

    Ports p = new Ports();
    int[] tailCount = new int[]{0};
    int[] invokeCount = new int[]{0};
    p.invoke = c -> { invokeCount[0]++; throw new AssertionError("unexpected invoke"); };
    p.tail = t -> {
        assertEquals(0,tailCount[0]++);
        assertEquals(new Tail(0x4267630L, TargetKind.INDIRECT_ABSOLUTE, element, new Entry(image, W - 8L, callV, activeN)), t);
        assertEquals(retRip, m.b.rawQ(W - 8L));
        m.b.putQ(E+8L,0x5000000L);m.b.putQ(E+0x10L,0x6000000L);
        m.b.putQ(E+0x18L,0x7000000L);m.b.putQ(E-8L,0x8000000L);m.b.putQ(E,0x9000000L);
        return opaqueNR;
    };
    p.readGsQword58 = () -> { throw new AssertionError("GS58"); };
    p.readGsQword60 = () -> { throw new AssertionError("GS60"); };

    TerminalAbort4242284215.Calls60 bound=CallbackSpanStaticDispatch232Calls.bind(image,p);
    int[] parentCount={0};
    TerminalAbort4242284215.Calls60 observedCalls60=new TerminalAbort4242284215.Calls60() {
        public VolatileBits invoke(Call c) {
            assertEquals(0,parentCount[0]++);
            ck(c,0x424E1E9L,TargetKind.INDIRECT_ABSOLUTE,iatTarget,W,callV,activeN,m,image,6);
            VolatileBits actual=bound.invoke(c);assertSame(replyV,actual);return actual;
        }
        public NormalReturn tail(Tail t) {return bound.tail(t);}
        public long readGsQword58() {return bound.readGsQword58();}
        public long readGsQword60() {return bound.readGsQword60();}
    };

    assertEquals(12,m.expected.size());assertEquals(0,parentCount[0]);assertEquals(0,tailCount[0]);assertEquals(0,invokeCount[0]);
    Entry childEntry = new Entry(image, E, inV, inN);
    NormalReturn finalNR = CallbackSpan424e1ac231.execute(childEntry, m, observedCalls60);
    assertEquals(1,parentCount[0]);assertTrue(m.base.exchanges.isEmpty());

    m.done();
    assertEquals(12, m.observed);
    assertEquals(1, tailCount[0]);
    assertEquals(0, invokeCount[0]);
    assertSame(replyV, finalNR.volatileBits());
    assertEquals(0x5000000L, finalNR.nonvolatileBits().rbxBits());
    assertEquals(0x6000000L, finalNR.nonvolatileBits().rbpBits());
    assertEquals(0x7000000L, finalNR.nonvolatileBits().rsiBits());
    assertEquals(0x8000000L, finalNR.nonvolatileBits().rdiBits());
    assertEquals(inN.r12Bits(), finalNR.nonvolatileBits().r12Bits());
    assertEquals(inN.r13Bits(), finalNR.nonvolatileBits().r13Bits());
    assertEquals(inN.r14Bits(), finalNR.nonvolatileBits().r14Bits());
    assertEquals(inN.r15Bits(), finalNR.nonvolatileBits().r15Bits());
    assertEquals(inN.xmm6(), finalNR.nonvolatileBits().xmm6());
    assertEquals(0x9000000L, finalNR.returnRipBits());
    assertEquals(E + 8L, finalNR.callerRspBits());
}
}
