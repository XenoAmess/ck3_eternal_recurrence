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
public final class StackResultIndexedTails229WitnessTest {
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
 static void ck(Call c,long site,TargetKind kind,long target,long work,VolatileBits value,NonvolatileBits n,Mem m,long image,int len) {
  assertEquals(new Call(site,kind,target,work,value,n),c);assertEquals(image+site+len,m.b.rawQ(work-8));
 }

 @Test void actual227ParentComposesBothIndexedTails229() {
  long I=0x100000000L,S=0x800000000L,W=S-0x28L,T=I+0x5C5D330L,D=0x500000000L,C=0x600000000L,A=0x81000000ABCDEF01L;
  long t500=0xA100000000000100L,t4f0old=0xA200000000000200L,t4f0new=0xA300000000000300L;
  long ret0=0xB100000000000100L,bx1=0xB200000000000200L,di1=0xB300000000000300L,ret1=0xB400000000000400L;
  Mem m=new Mem();m.b.putQ(S,ret0);m.b.putD(D,-2);m.b.putD(C,0x12345678);
  m.b.putQ(I+0x43DA500L,t500);m.b.putQ(I+0x43DA4F0L,t4f0old);
  VolatileBits base=v(0x1100000000000100L);
  VolatileBits incoming=q(base,base.raxBits(),base.rcxBits(),D,A,C,base.r10Bits(),base.r11Bits());
  NonvolatileBits n=nv(0x2200000000000200L),enterNV=nd(n,C,A),leaveNV=nd(n,C,0x8000000FL);
  VolatileBits enter=v(0x3300000000000300L),middleBase=v(0x4400000000000400L),leave=v(0x5500000000000500L);
  VolatileBits middle=q(middleBase,0xABCD12348000000FL,middleBase.rcxBits(),middleBase.rdxBits(),middleBase.r8Bits(),middleBase.r9Bits(),middleBase.r10Bits(),middleBase.r11Bits());
  VolatileBits enterCallV=q(incoming,incoming.raxBits(),0xFFFFFFFEL,D,A,C,incoming.r10Bits(),incoming.r11Bits());
  VolatileBits leaveCallV=q(middle,0xABCD12348000000FL,3,middle.rdxBits(),middle.r8Bits(),middle.r9Bits(),middle.r10Bits(),middle.r11Bits());
  Ports fallback=new Ports();int[] matched={0},midCalls={0},tails={0};
  fallback.invoke=c->{
   assertEquals(0,midCalls[0]++);
   ck(c,0x424DB94L,TargetKind.DIRECT_RVA,0x424DD60L,W,q(enter,enter.raxBits(),A,enter.rdxBits(),enter.r8Bits(),enter.r9Bits(),enter.r10Bits(),enter.r11Bits()),enterNV,m,I,5);
   return middle;
  };
  fallback.tail=t->{
   int ordinal=tails[0]++;
   if(ordinal==0) {
    assertEquals(new Tail(0x424800EL,TargetKind.INDIRECT_ABSOLUTE,t500,new Entry(I,W-8,q(enterCallV,T,T-80,D,A,C,incoming.r10Bits(),incoming.r11Bits()),enterNV)),t);
    assertEquals(I+0x424DB90L,m.b.rawQ(W-8));m.b.putD(C,3);m.b.putQ(I+0x43DA4F0L,t4f0new);
    return new NormalReturn(enter,I+0x424DB90L,W,enterNV);
   }
   assertEquals(1,ordinal);
   assertEquals(new Tail(0x4248062L,TargetKind.INDIRECT_ABSOLUTE,t4f0new,new Entry(I,W-8,q(leaveCallV,T,T+120,middle.rdxBits(),middle.r8Bits(),middle.r9Bits(),middle.r10Bits(),middle.r11Bits()),leaveNV)),t);
   assertEquals(I+0x424DBA2L,m.b.rawQ(W-8));m.b.putQ(S+8,bx1);m.b.putQ(S-8,di1);m.b.putQ(S,ret1);
   return new NormalReturn(leave,I+0x424DBA2L,W,leaveNV);
  };
  var bound=StackResultIndexedTails229Calls.bind(I,m,fallback);Ports observing=new Ports();
  observing.invoke=c->{
   if(c.callSiteRva()==0x424DB8BL) {assertEquals(0,matched[0]++);ck(c,0x424DB8BL,TargetKind.DIRECT_RVA,0x4247FFCL,W,enterCallV,enterNV,m,I,5);}
   if(c.callSiteRva()==0x424DB9DL) {assertEquals(1,matched[0]++);ck(c,0x424DB9DL,TargetKind.DIRECT_RVA,0x4248050L,W,leaveCallV,leaveNV,m,I,5);}
   return bound.invoke(c);
  };
  observing.tail=bound::tail;observing.readGsQword58=bound::readGsQword58;observing.readGsQword60=bound::readGsQword60;
  NormalReturn result=StackResult424db74227.execute(new Entry(I,S,incoming,n),m,observing);
  assertEquals(new NormalReturn(q(leave,0x8000000FL,leave.rcxBits(),leave.rdxBits(),leave.r8Bits(),leave.r9Bits(),leave.r10Bits(),leave.r11Bits()),ret1,S+8,nd(n,bx1,di1)),result);
  assertEquals(2,matched[0]);assertEquals(1,midCalls[0]);assertEquals(2,tails[0]);
  assertEquals(List.of(new Op("wq",S+8,n.rbxBits()),new Op("wq",S+0x20,C),new Op("wq",S-8,n.rdiBits()),new Op("rd",D,0xFFFFFFFEL),
   new Op("wq",W-8,I+0x424DB90L),new Op("rq",I+0x43DA500L,t500),new Op("wq",W-8,I+0x424DB99L),new Op("rd",C,3),
   new Op("wq",W-8,I+0x424DBA2L),new Op("rq",I+0x43DA4F0L,t4f0new),new Op("rq",S+8,bx1),new Op("rq",S-8,di1),new Op("rq",S,ret1)),m.b.ops);
 }

@Test void foreignIdentityAndBadMatchedStack229() {
    long image = 0x10000000L;
    long w = 0x20000000L;
    Mem m = new Mem();
    Ports p = new Ports();
    VolatileBits fv = v(0x100L);
    NonvolatileBits fnv = nv(0x200L);
    Call fc = new Call(0x424DB8BL, TargetKind.DIRECT_RVA, 0x424DD60L, w, fv, fnv);
    int[] foreignCounts = new int[4];
    VolatileBits foreignReply = v(0x8A00000000000100L);
    p.invoke = c -> { assertSame(fc, c); foreignCounts[0]++; return foreignReply; };
    var bound = StackResultIndexedTails229Calls.bind(image, m, p);
    assertSame(foreignReply, bound.invoke(fc));
    Tail ft = new Tail(0x424DB9DL, TargetKind.INDIRECT_ABSOLUTE, 0x4248050L, new Entry(image, w, fv, fnv));
    NormalReturn fnr = new NormalReturn(v(0x8B00000000000200L), 0x8C00000000000300L, 0x8D00000000000400L, nv(0x8E00000000000500L));
    p.tail = t -> { assertSame(ft, t); foreignCounts[1]++; return fnr; };
    assertSame(fnr, bound.tail(ft));
    p.readGsQword58 = () -> { foreignCounts[2]++; return 0x5858585858585858L; };
    p.readGsQword60 = () -> { foreignCounts[3]++; return 0x6060606060606060L; };
    assertEquals(0x5858585858585858L, bound.readGsQword58());
    assertEquals(0x6060606060606060L, bound.readGsQword60());
    int[] cnt = new int[]{0};
    VolatileBits b = v(0x300L);
    VolatileBits iv = q(b, b.raxBits(), 0xFFFFFFFEL, b.rdxBits(), b.r8Bits(), b.r9Bits(), b.r10Bits(), b.r11Bits());
    NonvolatileBits inv = nv(0x400L);
    Call mc = new Call(0x424DB8BL, TargetKind.DIRECT_RVA, 0x4247FFCL, w, iv, inv);
    m.b.putQ(w - 8L, image + 0x424DB90L);
    long iat = 0x4247FFCL;
    m.b.putQ(image + 0x43DA500L, iat);
    long rax = image + 0x5c5d330L;
    long rcx = rax - 80L;
    VolatileBits tv = q(iv, rax, rcx, iv.rdxBits(), iv.r8Bits(), iv.r9Bits(), iv.r10Bits(), iv.r11Bits());
    Entry te = new Entry(image, w - 8L, tv, inv);
    Tail mt = new Tail(0x424800EL, TargetKind.INDIRECT_ABSOLUTE, iat, te);
    p.tail = t -> {
        assertEquals(mt, t);
        cnt[0]++;
        return new NormalReturn(tv, image + 0x424DB90L, w + 8L, inv);
    };
    assertThrows(AssertionError.class, () -> bound.invoke(mc));
    assertEquals(1, cnt[0]);
    assertEquals(List.of(new Op("rq", image + 0x43DA500L, iat)), m.b.ops);
    assertEquals(image + 0x424DB90L, m.b.rawQ(w - 8L));
    assertArrayEquals(new int[]{1,1,1,1}, foreignCounts);
}
}
