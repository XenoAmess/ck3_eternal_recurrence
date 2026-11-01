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
public final class DispatchMiddleSpanComposition233WitnessTest {
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

 @Test void actual224TwoSpansReachOriginalTail233() {
  long image=0x10000000L,E=0x20000000L,W=E-0x28L,C= W-8L,CW=C-0x28L;
  long P=0x3000000L,p0=0x3100000L,p3=0x3200000L;
  long first=image+0x441ED48L,firstEnd=image+0x441ED70L;
  long second=image+0x441ED78L,secondEnd=image+0x441ED80L;
  long cookie=0xC10000000000102DL,element=0xD100000000001234L,iat=image+0x4267630L;
  long oldRet=0x8100000000000123L,freshRet=0x8200000000000456L,freshBX=0x8300000000000789L;
  VolatileBits seed=v(0xA100000000010000L);
  VolatileBits inV=q(seed,seed.raxBits(),P,seed.rdxBits(),seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
  NonvolatileBits inN=nv(0xB100000000010000L),outerN=nd(inN,P,inN.rdiBits());
  VolatileBits beforeDE=q(inV,cookie,image+0x5C5D698L,cookie,inV.r8Bits(),inV.r9Bits(),inV.r10Bits(),inV.r11Bits());
  VolatileBits afterDE=v(0xC200000000020000L),tailV=v(0xD200000000020000L);
  VolatileBits beforeTail=q(afterDE,element,second,secondEnd,afterDE.r8Bits(),afterDE.r9Bits(),afterDE.r10Bits(),afterDE.r11Bits());
  NonvolatileBits tailN=ns(inN,second,0L,0L,1L,inN.r14Bits(),inN.r15Bits());
  NormalReturn offered=new NormalReturn(tailV,image+0x424E1EFL,CW,tailN);
  VolatileBits expectedV=q(tailV,p3,tailV.rcxBits(),tailV.rdxBits(),tailV.r8Bits(),tailV.r9Bits(),tailV.r10Bits(),tailV.r11Bits());
  NormalReturn expectedNR=new NormalReturn(expectedV,freshRet,E+8L,nd(inN,freshBX,inN.rdiBits()));
  HookMemory32 m=new HookMemory32();
  m.b.putB(image+0x5C5D2E8L,0);m.b.putD(image+0x5C5D2DCL,0x89ABCDEF);
  m.b.putQ(P,p0);m.b.putD(p0,0);m.b.putQ(P+8L,p3);m.b.putD(p3,7);
  m.b.putQ(image+0x542F0B8L,cookie);m.b.putQ(image+0x5C5D2E0L,cookie);
  m.b.putQ(first,0);m.b.putQ(first+8L,0);m.b.putQ(first+16L,0);m.b.putQ(first+24L,0);m.b.putQ(first+32L,0);
  m.b.putQ(second,element);m.b.putQ(image+0x43DBBA8L,iat);m.b.putQ(E,oldRet);
  m.expected=List.of(
   new Op("wq",E-8L,inN.rbxBits()),
   new Op("rb",image+0x5C5D2E8L,0),
   new Op("xchg32",image+0x5C5D2DCL,1),
   new Op("rq",P,p0),new Op("rd",p0,0),
   new Op("rq",image+0x542F0B8L,cookie),new Op("rq",image+0x5C5D2E0L,cookie),
   new Op("wq",W-8L,image+0x4242167L),
   new Op("rq",P,p0),new Op("rd",p0,0),
   new Op("wq",W-8L,image+0x4242183L),
   new Op("wq",C+8L,P),new Op("wq",C+0x10L,inN.rbpBits()),
   new Op("wq",C+0x18L,inN.rsiBits()),new Op("wq",C-8L,inN.rdiBits()),
   new Op("rq",first,0),new Op("rq",first+8L,0),new Op("rq",first+16L,0),
   new Op("rq",first+24L,0),new Op("rq",first+32L,0),
   new Op("rq",C+8L,P),new Op("rq",C+0x10L,inN.rbpBits()),
   new Op("rq",C+0x18L,inN.rsiBits()),new Op("rq",C-8L,inN.rdiBits()),new Op("rq",C,image+0x4242183L),
   new Op("wq",W-8L,image+0x4242196L),
   new Op("wq",C+8L,P),new Op("wq",C+0x10L,inN.rbpBits()),
   new Op("wq",C+0x18L,inN.rsiBits()),new Op("wq",C-8L,inN.rdiBits()),
   new Op("rq",second,element),new Op("rq",image+0x43DBBA8L,iat),new Op("wq",CW-8L,image+0x424E1EFL),
   new Op("rq",C+8L,P),new Op("rq",C+0x10L,inN.rbpBits()),
   new Op("rq",C+0x18L,inN.rsiBits()),new Op("rq",C-8L,inN.rdiBits()),new Op("rq",C,image+0x4242196L),
   new Op("rq",P+8L,p3),new Op("rd",p3,7),new Op("rq",E-8L,freshBX),new Op("rq",E,freshRet));
  Ports ports=new Ports();int[] deCalls={0},tails={0};
  ports.invoke=c->{
   assertEquals(0,deCalls[0]++);
   ck(c,0x4242162L,TargetKind.DIRECT_RVA,0x424DE88L,W,beforeDE,outerN,m,image,5);
   return afterDE;
  };
  ports.tail=t->{
   assertEquals(0,tails[0]++);
   assertEquals(new Tail(0x4267630L,TargetKind.INDIRECT_ABSOLUTE,element,new Entry(image,CW-8L,beforeTail,tailN)),t);
   assertEquals(image+0x424E1EFL,m.b.rawQ(CW-8L));
   assertEquals(image+0x4242196L,m.b.rawQ(C));
   m.b.putQ(E-8L,freshBX);m.b.putQ(E,freshRet);
   return offered;
  };
  assertEquals(5L,(firstEnd-first)/8L);assertEquals(42,m.expected.size());
  assertEquals(0,deCalls[0]);assertEquals(0,tails[0]);assertEquals(0,m.observed);assertTrue(m.base.exchanges.isEmpty());
  NormalReturn actual=DispatchMiddleSpanComposition233.execute(new Entry(image,E,inV,inN),m,ports);
  m.done();assertEquals(42,m.observed);assertEquals(1,deCalls[0]);assertEquals(1,tails[0]);
  assertEquals(expectedNR,actual);
  assertEquals(1,m.base.exchanges.size());
  var exchange=m.base.exchanges.get(0);
  assertEquals(image+0x5C5D2DCL,exchange.address());assertEquals(0x89ABCDEF,exchange.before());assertEquals(1,exchange.after());
  assertEquals(1,m.b.rawD(image+0x5C5D2DCL));
  // Two admitted direct routes are physical/source evidence, not fallback Call callbacks.
  assertEquals(2L,m.b.ops.stream().filter(op->op.kind().equals("wq")&&op.address()==W-8L
   &&(op.value()==image+0x4242183L||op.value()==image+0x4242196L)).count());
 }

}
