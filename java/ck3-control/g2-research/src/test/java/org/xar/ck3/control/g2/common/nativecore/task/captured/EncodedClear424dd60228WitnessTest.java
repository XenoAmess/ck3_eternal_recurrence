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
public final class EncodedClear424dd60228WitnessTest {
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
 static void ck(Call c,long site,TargetKind kind,long target,long work,VolatileBits value,NonvolatileBits n,HookMemory m,long image,int len) {
  assertEquals(new Call(site,kind,target,work,value,n),c);assertEquals(image+site+len,m.b.rawQ(work-8));
 }
 static NonvolatileBits ns(NonvolatileBits n,long bx,long bp,long si,long di,long r14,long r15) {return new NonvolatileBits(bx,bp,si,di,n.r12Bits(),n.r13Bits(),r14,r15,n.xmm6());}
 static final class HookMemory implements Memory {
  final Mem base=new Mem();
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
 }

 @Test void earlyNullAndGuardFrames228() {
  for(int variant=0;variant<3;variant++) {
   long I=0x100000000L,E=0x800000000L,Z=0x500000000L,O=0x500001000L,D=0x500002000L;
   long C=0x8100000000000040L,encoded=variant==1?0x8100000000000040L:0x7EFFFFFFFFFFFFBFL;
   long ret0=0x8200000000000100L,ret1=0x8300000000000200L+variant;
   HookMemory m=new HookMemory();m.b.putQ(E,ret0);m.b.putQ(Z,O);m.b.putQ(O,variant==0?0:D);
   m.b.putQ(I+0x542F0B8L,C);m.b.putQ(D,encoded);m.b.putQ(D+8,0x8100000000005040L);
   VolatileBits base=v(0x1100000000000100L+variant*0x100L);
   VolatileBits incoming=q(base,base.raxBits(),Z,base.rdxBits(),base.r8Bits(),base.r9Bits(),base.r10Bits(),base.r11Bits());
   NonvolatileBits n=nv(0x2200000000000200L),fresh=nv(0x3300000000000300L+variant*0x100L);
   NonvolatileBits restored=ns(n,fresh.rbxBits(),fresh.rbpBits(),fresh.rsiBits(),fresh.rdiBits(),fresh.r14Bits(),fresh.r15Bits());
   int[] changed={0},calls={0};
   m.afterWriteQword=(a,value)->{if(a==E-0x18) {
    assertEquals(0,changed[0]++);m.b.putQ(E+8,restored.rbxBits());m.b.putQ(E+0x10,restored.rbpBits());m.b.putQ(E+0x18,restored.rsiBits());
    m.b.putQ(E-8,restored.rdiBits());m.b.putQ(E-0x10,restored.r14Bits());m.b.putQ(E-0x18,restored.r15Bits());m.b.putQ(E,ret1);
   }};
   List<Op> expected=new ArrayList<>(List.of(new Op("wq",E+8,n.rbxBits()),new Op("wq",E+0x10,n.rbpBits()),new Op("wq",E+0x18,n.rsiBits()),
    new Op("wq",E-8,n.rdiBits()),new Op("wq",E-0x10,n.r14Bits()),new Op("wq",E-0x18,n.r15Bits()),new Op("rq",Z,O),new Op("rq",O,variant==0?0:D)));
   if(variant!=0) expected.addAll(List.of(new Op("rq",I+0x542F0B8L,C),new Op("rq",D,encoded),new Op("rq",D+8,0x8100000000005040L)));
   expected.addAll(List.of(new Op("rq",E+8,restored.rbxBits()),new Op("rq",E+0x10,restored.rbpBits()),new Op("rq",E+0x18,restored.rsiBits()),
    new Op("rq",E-0x18,restored.r15Bits()),new Op("rq",E-0x10,restored.r14Bits()),new Op("rq",E-8,restored.rdiBits()),new Op("rq",E,ret1)));
   m.expected=List.copyOf(expected);Ports p=new Ports();p.invoke=c->{calls[0]++;throw new AssertionError(c);};
   NormalReturn result=EncodedClear424dd60228.execute(new Entry(I,E,incoming,n),m,p);m.done();
   VolatileBits out=variant==0?q(incoming,0xFFFFFFFFL,Z,incoming.rdxBits(),incoming.r8Bits(),incoming.r9Bits(),incoming.r10Bits(),incoming.r11Bits())
    :q(incoming,0,0,incoming.rdxBits(),C,incoming.r9Bits(),incoming.r10Bits(),incoming.r11Bits());
   assertEquals(new NormalReturn(out,ret1,E+8,restored),result);assertEquals(1,changed[0]);assertEquals(0,calls[0]);assertEquals(variant==0?15:18,m.observed);
  }
 }

@Test void acceptedEmptyRangeKeepsFreePostFrame228() {
    long image = 0x100000000L;
    long e = 0x424DD60L;
    long w = e - 0x38L;
    long begin = 0x1000L;
    long end = 0x1000L;
    long cookie = 0L;
    long newCookie = 0x1234567890ABCDEFL;
    long entryCtx = 0x2000L;
    long outer1 = 0x3000L;
    long desc1 = 0x4000L;
    long outer2 = 0x5000L;
    long desc2 = 0x6000L;
    long outer3 = 0x7000L;
    long desc3 = 0x8000L;

    HookMemory m = new HookMemory();
    m.b.putQ(e + 8L, 0L);
    m.b.putQ(e + 0x10L, 0L);
    m.b.putQ(e + 0x18L, 0L);
    m.b.putQ(e - 8L, 0L);
    m.b.putQ(e - 0x10L, 0L);
    m.b.putQ(e - 0x18L, 0L);
    m.b.putQ(e, image + 0x424DE75L);
    m.b.putQ(entryCtx, outer1);
    m.b.putQ(outer1, desc1);
    m.b.putQ(desc1, begin);
    m.b.putQ(desc1 + 8L, end);
    m.b.putQ(outer2, desc2);m.b.putQ(outer3, desc3);
    m.b.putQ(image + 0x542F0B8L, cookie);
    m.b.putQ(image + 0x43DBBA8L, 0L);
    m.b.putQ(image + 0x424E364L, 0L);

    int[] freeCount = new int[]{0};
    int[] chainSwitch = new int[]{0};
    m.afterWriteQword = (a, v) -> {
        if (a == desc1) { assertEquals(0, chainSwitch[0]++); m.b.putQ(entryCtx, outer2); }
        else if (a == desc2 + 8L) { assertEquals(1, chainSwitch[0]++); m.b.putQ(entryCtx, outer3); }
    };

    VolatileBits b = v(0x100L);
    VolatileBits entryV = q(b, b.raxBits(), entryCtx, b.rdxBits(), b.r8Bits(), b.r9Bits(), b.r10Bits(), b.r11Bits());
    NonvolatileBits entryNV = nv(0x200L);
    NonvolatileBits restored = ns(entryNV, 0xA100000000000100L, 0xA200000000000200L, 0xA300000000000300L, 0xA400000000000400L, 0xA500000000000500L, 0xA600000000000600L);
    long freshRet = 0xA700000000000700L;VolatileBits freeReply = v(0xB100000000000100L);
    Entry entry = new Entry(image, e, entryV, entryNV);

    Ports p = new Ports();
    p.invoke = c -> {
        if (c.callSiteRva() == 0x424DE32L) {
            assertEquals(0, freeCount[0]++);
            ck(c, 0x424DE32L, TargetKind.DIRECT_RVA, 0x424E364L, w,
                q(entryV, begin - 1L, begin, entryV.rdxBits(), cookie, entryV.r9Bits(), entryV.r10Bits(), entryV.r11Bits()),
                ns(entryNV, end - 8L, end, entryCtx, begin, cookie, begin), m, image, 5);
            m.b.putQ(image + 0x542F0B8L, newCookie);m.b.putQ(entryCtx, outer1);
            m.b.putQ(e + 8, restored.rbxBits());m.b.putQ(e + 0x10, restored.rbpBits());m.b.putQ(e + 0x18, restored.rsiBits());
            m.b.putQ(e - 8, restored.rdiBits());m.b.putQ(e - 0x10, restored.r14Bits());m.b.putQ(e - 0x18, restored.r15Bits());m.b.putQ(e, freshRet);
            return freeReply;
        }
        throw new AssertionError(c);
    };

    m.expected = List.of(
        new Op("wq", e + 8L, entryNV.rbxBits()),
        new Op("wq", e + 0x10L, entryNV.rbpBits()),
        new Op("wq", e + 0x18L, entryNV.rsiBits()),
        new Op("wq", e - 8L, entryNV.rdiBits()),
        new Op("wq", e - 0x10L, entryNV.r14Bits()),
        new Op("wq", e - 0x18L, entryNV.r15Bits()),
        new Op("rq", entryCtx, outer1),
        new Op("rq", outer1, desc1),
        new Op("rq", image + 0x542F0B8L, cookie),
        new Op("rq", desc1, begin),
        new Op("rq", desc1 + 8L, end),
        new Op("wq", w - 8L, image + 0x424DE37L),
        new Op("rq", image + 0x542F0B8L, newCookie),
        new Op("rq", entryCtx, outer1),
        new Op("rq", outer1, desc1),
        new Op("wq", desc1, newCookie),
        new Op("rq", entryCtx, outer2),
        new Op("rq", outer2, desc2),
        new Op("wq", desc2 + 8L, newCookie),
        new Op("rq", entryCtx, outer3),
        new Op("rq", outer3, desc3),
        new Op("wq", desc3 + 16L, newCookie),
        new Op("rq", e + 8L, restored.rbxBits()),
        new Op("rq", e + 0x10L, restored.rbpBits()),
        new Op("rq", e + 0x18L, restored.rsiBits()),
        new Op("rq", e - 0x18L, restored.r15Bits()),
        new Op("rq", e - 0x10L, restored.r14Bits()),
        new Op("rq", e - 8L, restored.rdiBits()),
        new Op("rq", e, freshRet)
    );

    NormalReturn nr = EncodedClear424dd60228.execute(entry, m, p);
    m.done();
    assertEquals(1, freeCount[0]);assertEquals(2, chainSwitch[0]);assertEquals(29, m.observed);
    assertEquals(new NormalReturn(q(freeReply, 0, desc3, freeReply.rdxBits(), newCookie, freeReply.r9Bits(), freeReply.r10Bits(), freeReply.r11Bits()), freshRet, e + 8, restored), nr);
    assertEquals(newCookie, m.b.rawQ(desc1));assertEquals(newCookie, m.b.rawQ(desc2 + 8));assertEquals(newCookie, m.b.rawQ(desc3 + 0x10));
}
 @Test void oneIatReloadsChangedAndUnchangedBounds228() {
  for(boolean changed:new boolean[]{false,true}) {
   long I=0x100000000L,E=0x900000000L,W=E-0x38L,Z=0x500000000L,O=0x500001000L,D=0x500002000L,B=0x8000L,END=0x8008L;
   long L=0x1200000000000100L,T=0xA100000000000100L,ret=0xA200000000000200L,encBegin=changed?0xFFFFFFFFFFFFFFBFL:0x8040L,encEnd=changed?0x40L:0x8048L;
   HookMemory m=new HookMemory();m.b.putQ(E,ret);m.b.putQ(Z,O);m.b.putQ(O,D);m.b.putQ(D,B);m.b.putQ(D+8,END);
   m.b.putQ(I+0x542F0B8L,0);m.b.putQ(B,L);m.b.putQ(I+0x43DBBA8L,T);
   VolatileBits base=v(0x1300000000000300L);
   VolatileBits incoming=q(base,base.raxBits(),Z,base.rdxBits(),base.r8Bits(),base.r9Bits(),base.r10Bits(),base.r11Bits());
   NonvolatileBits n=nv(0x2400000000000400L);
   VolatileBits iatReply=v(0x3500000000000500L),freeReply=v(0x4600000000000600L);
   Ports p=new Ports();int[] iat={0},free={0};
   p.invoke=c->{
    if(c.callSiteRva()==0x424DDE5L) {
     assertEquals(0,iat[0]++);
     ck(c,0x424DDE5L,TargetKind.INDIRECT_ABSOLUTE,T,W,q(incoming,L,0,incoming.rdxBits(),0,incoming.r9Bits(),incoming.r10Bits(),incoming.r11Bits()),ns(n,B,END,Z,B,0,B),m,I,6);
     m.b.putQ(I+0x542F0B8L,0x40);m.b.putQ(D,encBegin);m.b.putQ(D+8,encEnd);return iatReply;
    }
    assertFalse(changed);assertEquals(0,free[0]++);
    ck(c,0x424DE32L,TargetKind.DIRECT_RVA,0x424E364L,W,q(iatReply,END,B,D,0x40,B,iatReply.r10Bits(),iatReply.r11Bits()),ns(n,B-8,END,Z,B,0,B),m,I,5);
    m.b.putQ(I+0x542F0B8L,0x80);return freeReply;
   };
   List<Op> expected=new ArrayList<>(List.of(new Op("wq",E+8,n.rbxBits()),new Op("wq",E+0x10,n.rbpBits()),new Op("wq",E+0x18,n.rsiBits()),
    new Op("wq",E-8,n.rdiBits()),new Op("wq",E-0x10,n.r14Bits()),new Op("wq",E-0x18,n.r15Bits()),
    new Op("rq",Z,O),new Op("rq",O,D),new Op("rq",I+0x542F0B8L,0),new Op("rq",D,B),new Op("rq",D+8,END),
    new Op("rq",B,L),new Op("wq",B,0),new Op("rq",I+0x43DBBA8L,T),new Op("wq",W-8,I+0x424DDEBL),
    new Op("rq",I+0x542F0B8L,0x40),new Op("rq",Z,O),new Op("rq",O,D),new Op("rq",D,encBegin),new Op("rq",D+8,encEnd)));
   if(!changed) expected.addAll(List.of(new Op("wq",W-8,I+0x424DE37L),new Op("rq",I+0x542F0B8L,0x80)));
   long clearCookie=changed?0x40L:0x80L;
   expected.addAll(List.of(new Op("rq",Z,O),new Op("rq",O,D),new Op("wq",D,clearCookie),
    new Op("rq",Z,O),new Op("rq",O,D),new Op("wq",D+8,clearCookie),new Op("rq",Z,O),new Op("rq",O,D),new Op("wq",D+0x10,clearCookie),
    new Op("rq",E+8,n.rbxBits()),new Op("rq",E+0x10,n.rbpBits()),new Op("rq",E+0x18,n.rsiBits()),
    new Op("rq",E-0x18,n.r15Bits()),new Op("rq",E-0x10,n.r14Bits()),new Op("rq",E-8,n.rdiBits()),new Op("rq",E,ret)));
   m.expected=List.copyOf(expected);
   NormalReturn result=EncodedClear424dd60228.execute(new Entry(I,E,incoming,n),m,p);m.done();
   VolatileBits out=changed?q(iatReply,0,D,D,0x40,-1,iatReply.r10Bits(),iatReply.r11Bits())
    :q(freeReply,0,D,freeReply.rdxBits(),0x80,freeReply.r9Bits(),freeReply.r10Bits(),freeReply.r11Bits());
   assertEquals(new NormalReturn(out,ret,E+8,n),result);assertEquals(1,iat[0]);assertEquals(changed?0:1,free[0]);assertEquals(changed?36:38,m.observed);
   assertEquals(clearCookie,m.b.rawQ(D));assertEquals(clearCookie,m.b.rawQ(D+8));assertEquals(clearCookie,m.b.rawQ(D+0x10));
  }
 }

}
