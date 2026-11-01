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
public final class CallbackSpan424e1ac231WitnessTest {
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

 @Test void zeroCountPreservesIncomingWholeFrame231() {
  long image=0x100000000L;
  long[][] ranges={{0x500000000L,0x500000000L},{0x8000000000000000L,0x1000000000000000L}};
  for(int variant=0;variant<2;variant++) {
   long e=0x900000000L+variant*0x1000L,freshRet=0xA100000000000100L+variant;
   HookMemory32 m=new HookMemory32();VolatileBits seed=v(0x1100000000000100L+variant*0x100L);
   VolatileBits in=q(seed,seed.raxBits(),ranges[variant][0],ranges[variant][1],seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
   NonvolatileBits n=nv(0x2200000000000200L+variant*0x100L);
   NonvolatileBits restored=ns(n,0xB100000000000100L+variant,0xB200000000000200L+variant,0xB300000000000300L+variant,0xB400000000000400L+variant,n.r14Bits(),n.r15Bits());
   m.b.putQ(e,0xC100000000000100L+variant);
   m.expected=List.of(
    new Op("wq",e+8,n.rbxBits()),new Op("wq",e+0x10,n.rbpBits()),new Op("wq",e+0x18,n.rsiBits()),new Op("wq",e-8,n.rdiBits()),
    new Op("rq",e+8,restored.rbxBits()),new Op("rq",e+0x10,restored.rbpBits()),new Op("rq",e+0x18,restored.rsiBits()),new Op("rq",e-8,restored.rdiBits()),new Op("rq",e,freshRet));
   assertEquals(9,m.expected.size());int[] rewrite={0},opaqueCalls={0};
   m.afterWriteQword=(a,value)->{
    if(a==e-8) {
     assertEquals(0,rewrite[0]++);m.b.putQ(e+8,restored.rbxBits());m.b.putQ(e+0x10,restored.rbpBits());
     m.b.putQ(e+0x18,restored.rsiBits());m.b.putQ(e-8,restored.rdiBits());m.b.putQ(e,freshRet);
    }
   };
   Ports p=new Ports();p.invoke=c->{opaqueCalls[0]++;throw new AssertionError(c);};
   assertEquals(0,rewrite[0]);assertEquals(0,opaqueCalls[0]);
   NormalReturn actual=CallbackSpan424e1ac231.execute(new Entry(image,e,in,n),m,p);
   m.done();assertEquals(1,rewrite[0]);assertEquals(0,opaqueCalls[0]);assertTrue(m.base.exchanges.isEmpty());
   assertEquals(new NormalReturn(in,freshRet,e+8,restored),actual);
  }
 }

@Test void positiveFourElementsCarriesActualV231() {
    long image = 0x100000000L;
    long e = 0x200000L;
    long w = e - 0x28L;
    long start = 0x300000L;
    long end = start + 32L;
    long a = 0x1111111111111111L;
    long b = 0x2222222222222222L;
    long t1 = 0x43DBBA8L;
    long t2 = 0x43DBBA9L;

    HookMemory32 m = new HookMemory32();
    // Seed prologue spill values (actual entry NV fields)
    NonvolatileBits entryN = nv(0x2000L);
    m.b.putQ(e + 8L, entryN.rbxBits());
    m.b.putQ(e + 0x10L, entryN.rbpBits());
    m.b.putQ(e + 0x18L, entryN.rsiBits());
    m.b.putQ(e - 8L, entryN.rdiBits());
    m.b.putQ(e, image + 0x424E20FL);
    // Seed elements
    m.b.putQ(start, a);
    m.b.putQ(start + 8L, 0L);
    m.b.putQ(start + 16L, b);
    m.b.putQ(start + 24L, 0L);
    // Seed IAT
    m.b.putQ(image + 0x43DBBA8L, t1);

    VolatileBits seed=v(0x1000L);
    VolatileBits entryV=q(seed,seed.raxBits(),start,end,seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
    NonvolatileBits restored=ns(entryN,0x1000000000000000L,0x2000000000000000L,0x3000000000000000L,0x4000000000000000L,entryN.r14Bits(),entryN.r15Bits());
    long freshRet=0xA500000000000500L;
    VolatileBits secondReply=v(0x5200000000000200L);
    Entry entry = new Entry(image, e, entryV, entryN);

    int[] callCount = {0};
    Ports ports = new Ports();
    ports.invoke = c -> {
        assertTrue(callCount[0]<2);callCount[0]++;
        if (callCount[0] == 1) {
            // Active NV for first call: BX=start, BP=0, SI=0, DI=4, rest entry
            NonvolatileBits activeNV1 = ns(entryN, start, 0L, 0L, 4L, entryN.r14Bits(), entryN.r15Bits());
            ck(c, 0x424E1E9L, TargetKind.INDIRECT_ABSOLUTE, t1, w, q(entryV, a, start, end, entryV.r8Bits(), entryV.r9Bits(), entryV.r10Bits(), entryV.r11Bits()), activeNV1, m, image, 6);
            // Mutate IAT slot to t2 for next read
            m.b.putQ(image + 0x43DBBA8L, t2);
            // Return distinct V with high sentinels in RCX/RDX
            return q(v(0x5100000000000100L), 0x9999999999999999L, 0xAAAAAAAAAAAAAAAAL, 0xBBBBBBBBBBBBBBBBL, 0xCCCCCCCCCCCCCCCCL, 0xDDDDDDDDDDDDDDDDL, 0xEEEEEEEEEEEEEEEEL, 0xFFFFFFFFFFFFFFFFL);
        } else {
            // Active NV for second call: BX=start+16, BP=0, SI=2, DI=4, rest entry
            NonvolatileBits activeNV2 = ns(entryN, start + 16L, 0L, 2L, 4L, entryN.r14Bits(), entryN.r15Bits());
            // Args: RAX=b, RCX/RDX/R8/R9/R10/R11/XMM from first reply (UNKNOWN not 0)
            VolatileBits firstReplyV = q(v(0x5100000000000100L), 0x9999999999999999L, 0xAAAAAAAAAAAAAAAAL, 0xBBBBBBBBBBBBBBBBL, 0xCCCCCCCCCCCCCCCCL, 0xDDDDDDDDDDDDDDDDL, 0xEEEEEEEEEEEEEEEEL, 0xFFFFFFFFFFFFFFFFL);
            ck(c, 0x424E1E9L, TargetKind.INDIRECT_ABSOLUTE, t2, w, q(firstReplyV, b, firstReplyV.rcxBits(), firstReplyV.rdxBits(), firstReplyV.r8Bits(), firstReplyV.r9Bits(), firstReplyV.r10Bits(), firstReplyV.r11Bits()), activeNV2, m, image, 6);
            // Mutate outer NV homes and RET for epilogue
            m.b.putQ(e + 8L, 0x1000000000000000L);
            m.b.putQ(e + 0x10L, 0x2000000000000000L);
            m.b.putQ(e + 0x18L, 0x3000000000000000L);
            m.b.putQ(e - 8L, 0x4000000000000000L);
            m.b.putQ(e,freshRet);
            // The final zero element overwrites this nonzero callback reply RAX.
            return secondReply;
        }
    };
    ports.tail = t -> { throw new AssertionError("TAIL"); };
    ports.readGsQword58 = () -> { throw new AssertionError("GS58"); };
    ports.readGsQword60 = () -> { throw new AssertionError("GS60"); };

    m.expected = List.of(
        new Op("wq", e + 8L, entryN.rbxBits()),
        new Op("wq", e + 0x10L, entryN.rbpBits()),
        new Op("wq", e + 0x18L, entryN.rsiBits()),
        new Op("wq", e - 8L, entryN.rdiBits()),
        new Op("rq", start, a),
        new Op("rq", image + 0x43DBBA8L, t1),
        new Op("wq", w - 8L, image + 0x424E1EFL),
        new Op("rq", start + 8L, 0L),
        new Op("rq", start + 16L, b),
        new Op("rq", image + 0x43DBBA8L, t2),
        new Op("wq", w - 8L, image + 0x424E1EFL),
        new Op("rq", start + 24L, 0L),
        new Op("rq", e + 8L, 0x1000000000000000L),
        new Op("rq", e + 0x10L, 0x2000000000000000L),
        new Op("rq", e + 0x18L, 0x3000000000000000L),
        new Op("rq", e - 8L, 0x4000000000000000L),
        new Op("rq", e,freshRet)
    );

    assertEquals(17,m.expected.size());assertEquals(0,callCount[0]);
    NormalReturn nr = CallbackSpan424e1ac231.execute(entry, m, ports);
    m.done();
    assertEquals(2, callCount[0]);assertTrue(m.base.exchanges.isEmpty());
    VolatileBits finalV=q(secondReply,0,secondReply.rcxBits(),secondReply.rdxBits(),secondReply.r8Bits(),secondReply.r9Bits(),secondReply.r10Bits(),secondReply.r11Bits());
    assertEquals(new NormalReturn(finalV,freshRet,e+8,restored),nr);
}
}
