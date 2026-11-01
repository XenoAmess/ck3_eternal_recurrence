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
public final class WordCompare4246a60221WitnessTest {
 static final class Words implements TerminalTailTarget42421c8213.Memory16 {
  final Mem base=new Mem();
  final org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes b=base.b;
  java.util.function.Function<Long,Integer> word=a->(int)b.raw(a,2);
  public int readUnsigned16(long a) { int value=word.apply(a);if(value<0||value>65535)throw new AssertionError(value);b.ops.add(new Op("rw",a,value));return value; }
  public int readDword(long a) {return base.readDword(a);}
  public long readQword(long a) {return base.readQword(a);}
  public int readUnsignedByte(long a) {return base.readUnsignedByte(a);}
  public void writeDword(long a,int v) {base.writeDword(a,v);}
  public void writeQword(long a,long v) {base.writeQword(a,v);}
  public void writeByte(long a,int v) {base.writeByte(a,v);}
  public int lockedXaddDword(long a,int v) {return base.lockedXaddDword(a,v);}
  public Bits128 read128(long a) {return base.read128(a);}
  public void write128(long a,Bits128 v) {base.write128(a,v);}
 }
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

@Test void zeroCountReadsOnlyFreshRetAndPreservesPointers221() {
    long E = 0x810000000108L;
    long I = 0x140000000L;
    Words m = new Words();
    m.word = (a) -> { throw new AssertionError("WORD read on count0"); };
    m.b.putQ(E, I);
    VolatileBits entryV = q(v(0x1000L), 0x123456789ABCDEF0L, 0xFEDCBA9876543210L, 0x1111111111111111L, 0L, v(0x1000L).r9Bits(), v(0x1000L).r10Bits(), v(0x1000L).r11Bits());
    NonvolatileBits entryNV = nv(0x2000L);
    Entry entry = new Entry(I, E, entryV, entryNV);
    NormalReturn nr = WordCompare4246a60221.execute(entry, m);
    assertEquals(I, nr.returnRipBits());
    assertEquals(E + 8L, nr.callerRspBits());
    assertSame(entryNV, nr.nonvolatileBits());
    assertEquals(0L, nr.volatileBits().raxBits());
    assertEquals(entryV.rcxBits(), nr.volatileBits().rcxBits());
    assertEquals(entryV.rdxBits(), nr.volatileBits().rdxBits());
    assertEquals(entryV.r8Bits(), nr.volatileBits().r8Bits());
    assertEquals(entryV.r9Bits(), nr.volatileBits().r9Bits());
    assertEquals(entryV.r10Bits(), nr.volatileBits().r10Bits());
    assertEquals(entryV.r11Bits(), nr.volatileBits().r11Bits());
    assertEquals(entryV.xmm0(), nr.volatileBits().xmm0());
    assertEquals(entryV.xmm1(), nr.volatileBits().xmm1());
    assertEquals(entryV.xmm2(), nr.volatileBits().xmm2());
    assertEquals(entryV.xmm3(), nr.volatileBits().xmm3());
    assertEquals(entryV.xmm4(), nr.volatileBits().xmm4());
    assertEquals(entryV.xmm5(), nr.volatileBits().xmm5());
    List<Op> expected = List.of(new Op("rq", E, I));
    assertEquals(expected, m.b.ops);
}
@Test void countOneAndSevenUseFreshFinalWords221() {
    // Fixture 1: count=1, left=1, right=0xFFFF
    Words m1 = new Words();
    long e1 = 0x1000L;
    long img1 = 0x400000L;
    long rcx1 = 0x2000L;
    long rdx1 = 0x3000L;
    long r8_1 = 1L;
    m1.b.put(rcx1, 1L, 2);
    m1.b.put(rdx1, 0xFFFFL, 2);
    m1.b.putQ(e1, 0x4246A8BL);
    VolatileBits v1 = q(v(0x100L), v(0x100L).raxBits(), rcx1, rdx1, r8_1, v(0x100L).r9Bits(), v(0x100L).r10Bits(), v(0x100L).r11Bits());
    NonvolatileBits nv1 = nv(0x200L);
    Entry entry1 = new Entry(img1, e1, v1, nv1);
    NormalReturn nr1 = WordCompare4246a60221.execute(entry1, m1);
    assertEquals(0x00000000FFFF0002L, nr1.volatileBits().raxBits());
    assertEquals(0xFFFFL, nr1.volatileBits().rcxBits());
    assertEquals(rdx1, nr1.volatileBits().rdxBits());
    assertEquals(0L, nr1.volatileBits().r8Bits());
    assertEquals(v1.r9Bits(), nr1.volatileBits().r9Bits());
    assertEquals(v1.r10Bits(), nr1.volatileBits().r10Bits());
    assertEquals(v1.r11Bits(), nr1.volatileBits().r11Bits());
    assertEquals(v1.xmm0(), nr1.volatileBits().xmm0());
    assertEquals(v1.xmm1(), nr1.volatileBits().xmm1());
    assertEquals(v1.xmm2(), nr1.volatileBits().xmm2());
    assertEquals(v1.xmm3(), nr1.volatileBits().xmm3());
    assertEquals(v1.xmm4(), nr1.volatileBits().xmm4());
    assertEquals(v1.xmm5(), nr1.volatileBits().xmm5());
    assertEquals(0x4246A8BL, nr1.returnRipBits());
    assertEquals(e1 + 8L, nr1.callerRspBits());
    assertSame(nv1, nr1.nonvolatileBits());
    List<Op> ops1 = m1.b.ops;
    assertEquals(3, ops1.size());
    assertEquals(new Op("rw", rcx1, 1), ops1.get(0));
    assertEquals(new Op("rw", rdx1, 0xFFFF), ops1.get(1));
    assertEquals(new Op("rq", e1, 0x4246A8BL), ops1.get(2));

    // Fixture 2: count=7, 6 equal pairs, final mismatch
    Words m2 = new Words();
    long e2 = 0x5000L;
    long img2 = 0x400000L;
    long rcx2 = 0x6000L;
    long rdx2 = 0x7000L;
    long r8_2 = 7L;
    long[] leftWords = {11, 12, 13, 14, 15, 16, 1234};
    long[] rightWords = {11, 12, 13, 14, 15, 16, 1235};
    for (int i = 0; i < 7; i++) {
        m2.b.put(rcx2 + 2L * i, leftWords[i], 2);
        m2.b.put(rdx2 + 2L * i, rightWords[i], 2);
    }
    m2.b.putQ(e2, 0x4246A8BL);
    VolatileBits v2 = q(v(0x300L), v(0x300L).raxBits(), rcx2, rdx2, r8_2, v(0x300L).r9Bits(), v(0x300L).r10Bits(), v(0x300L).r11Bits());
    NonvolatileBits nv2 = nv(0x400L);
    Entry entry2 = new Entry(img2, e2, v2, nv2);
    NormalReturn nr2 = WordCompare4246a60221.execute(entry2, m2);
    assertEquals(0xFFFFFFFFL, nr2.volatileBits().raxBits());
    assertEquals(1235L, nr2.volatileBits().rcxBits());
    assertEquals(rdx2 + 12L, nr2.volatileBits().rdxBits());
    assertEquals(0L, nr2.volatileBits().r8Bits());
    assertEquals(v2.r9Bits(), nr2.volatileBits().r9Bits());
    assertEquals(v2.r10Bits(), nr2.volatileBits().r10Bits());
    assertEquals(v2.r11Bits(), nr2.volatileBits().r11Bits());
    assertEquals(v2.xmm0(), nr2.volatileBits().xmm0());
    assertEquals(v2.xmm1(), nr2.volatileBits().xmm1());
    assertEquals(v2.xmm2(), nr2.volatileBits().xmm2());
    assertEquals(v2.xmm3(), nr2.volatileBits().xmm3());
    assertEquals(v2.xmm4(), nr2.volatileBits().xmm4());
    assertEquals(v2.xmm5(), nr2.volatileBits().xmm5());
    assertEquals(0x4246A8BL, nr2.returnRipBits());
    assertEquals(e2 + 8L, nr2.callerRspBits());
    assertSame(nv2, nr2.nonvolatileBits());
    List<Op> ops2 = m2.b.ops;
    assertEquals(15, ops2.size());
    for (int i = 0; i < 7; i++) {
        assertEquals(new Op("rw", rcx2 + 2L * i, leftWords[i]), ops2.get(2 * i));
        assertEquals(new Op("rw", rdx2 + 2L * i, rightWords[i]), ops2.get(2 * i + 1));
    }
    assertEquals(new Op("rq", e2, 0x4246A8BL), ops2.get(14));
}
    @Test
    public void negativeRawCountRereadsChangedNulAndFreshRet221() {
        long E = 0x840000000108L;
        long I = 0x1C0000000L;
        long L = 0x100000000L;
        long R = 0x200000000L;
        long R8 = -1L;
        long RIP = I + 0x4246a8bL;

        Words m = new Words();
        m.b.put(E, RIP, 8);
        m.b.put(L, 0, 2);
        m.b.put(R, 0xFFFF, 2);

        int[] count = {0};
        m.word = (a) -> {
            if (a == L) {
                count[0]++;
                if (count[0] == 2) {
                    m.b.put(L, 1, 2);
                    m.writeQword(E, RIP + 1);
                }
            }
            return (int)m.b.raw(a, 2);
        };

        VolatileBits v = q(v(0), v(0).raxBits(), L, R, R8, v(0).r9Bits(), v(0).r10Bits(), v(0).r11Bits());
        NonvolatileBits nv = nv(0);
        Entry entry = new Entry(I, E, v, nv);

        NormalReturn nr = WordCompare4246a60221.execute(entry, m);

        assertEquals(RIP + 1, nr.returnRipBits());
        assertEquals(E + 8, nr.callerRspBits());
        assertSame(nv, nr.nonvolatileBits());

        VolatileBits rv = nr.volatileBits();
        assertEquals(0xFFFF0002L, rv.raxBits());
        assertEquals(0xFFFFL, rv.rcxBits());
        assertEquals(R, rv.rdxBits());
        assertEquals(-2L, rv.r8Bits());
        assertEquals(v.r9Bits(), rv.r9Bits());
        assertEquals(v.r10Bits(), rv.r10Bits());
        assertEquals(v.r11Bits(), rv.r11Bits());
        assertEquals(v.xmm0(), rv.xmm0());
        assertEquals(v.xmm1(), rv.xmm1());
        assertEquals(v.xmm2(), rv.xmm2());
        assertEquals(v.xmm3(), rv.xmm3());
        assertEquals(v.xmm4(), rv.xmm4());
        assertEquals(v.xmm5(), rv.xmm5());

        List<Op> ops = m.b.ops;
        assertEquals(5, ops.size());
        assertEquals("rw", ops.get(0).kind());
        assertEquals(L, ops.get(0).address());
        assertEquals(0, ops.get(0).value());
        assertEquals("wq", ops.get(1).kind());
        assertEquals(E, ops.get(1).address());
        assertEquals(RIP + 1, ops.get(1).value());
        assertEquals("rw", ops.get(2).kind());
        assertEquals(L, ops.get(2).address());
        assertEquals(1, ops.get(2).value());
        assertEquals("rw", ops.get(3).kind());
        assertEquals(R, ops.get(3).address());
        assertEquals(0xFFFF, ops.get(3).value());
        assertEquals("rq", ops.get(4).kind());
        assertEquals(E, ops.get(4).address());
        assertEquals(RIP + 1, ops.get(4).value());
    }
 @Test void native225OrderedPairDescriptorsUseRealBindings221() {
  long I=0x140000000L,S=0x8500000000C0L,L=0x820000000100L,R1=I+0x44226A0L,R2=I+0x4426EC8L,cursor=0x830000000200L,end=cursor+4,name=I+0x4427010L;
  Words m=new Words();m.b.put(L,5,2);m.b.put(R1,6,2);m.b.put(R2,9,2);
  NonvolatileBits n=new NonvolatileBits(7,cursor,20,-1,end,name,L,0x1C,x(0x660000000000L));VolatileBits z=v(0x110000000000L);
  VolatileBits firstV=q(z,0xFACE000000000057L,L,R1,7,z.r9Bits(),z.r10Bits(),z.r11Bits());
  TerminalAbort4242284215.Calls60 bound=WordCompare4246a60221Calls.bind(I,m,new Ports());
  Call first=new Call(0x424E514L,TargetKind.DIRECT_RVA,0x4246A60L,S,firstV,n);
  m.writeQword(S-8,I+0x424E519L);VolatileBits actualFirst=bound.invoke(first);
  assertEquals(q(firstV,0xFFFFFFFFL,6,R1,6,firstV.r9Bits(),firstV.r10Bits(),firstV.r11Bits()),actualFirst);
  VolatileBits secondV=q(z,0xFFFFFFFFL,L,R2,7,z.r9Bits(),z.r10Bits(),z.r11Bits());assertEquals(actualFirst.raxBits(),secondV.raxBits());
  Call second=new Call(0x424E52AL,TargetKind.DIRECT_RVA,0x4246A60L,S,secondV,n);
  m.writeQword(S-8,I+0x424E52FL);VolatileBits actualSecond=bound.invoke(second);
  assertEquals(q(secondV,0xFFFFFFFCL,9,R2,6,secondV.r9Bits(),secondV.r10Bits(),secondV.r11Bits()),actualSecond);
  assertEquals(List.of(new Op("wq",S-8,I+0x424E519L),new Op("rw",L,5),new Op("rw",R1,6),new Op("rw",L,5),new Op("rw",R1,6),new Op("rq",S-8,I+0x424E519L),new Op("wq",S-8,I+0x424E52FL),new Op("rw",L,5),new Op("rw",R2,9),new Op("rw",L,5),new Op("rw",R2,9),new Op("rq",S-8,I+0x424E52FL)),m.b.ops);
 }

}
