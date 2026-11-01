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
public final class EncodedClearFree61Site230WitnessTest {
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

 @Test void markerOnlyParentUsesRealFree61HeapCall230() {
  long i=0x100000000L,e=0x900000000L,w=e-0x38L,ce=e-0x40L,cw=ce-0x28L;
  long z=0x500000000L,o=0x500001000L,d=0x500002000L,b=0x8000L,end=0x8008L;
  long cookie=0x40L,afterCookie=0x80L,heap=0xA100000000000100L,target=0xA200000000000200L;
  long oldRet=0xA300000000000300L,freshRet=0xA400000000000400L;
  HookMemory m=new HookMemory();
  VolatileBits seed=v(0x1100000000000100L);
  VolatileBits in=q(seed,seed.raxBits(),z,seed.rdxBits(),seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
  NonvolatileBits n=nv(0x2200000000000200L);
  NonvolatileBits active=ns(n,b-8,end,z,b,cookie,b);
  NonvolatileBits restored=ns(n,0xB100000000000100L,0xB200000000000200L,0xB300000000000300L,0xB400000000000400L,0xB500000000000500L,0xB600000000000600L);
  VolatileBits beforeFree=q(in,cookie,b,in.rdxBits(),cookie,in.r9Bits(),in.r10Bits(),in.r11Bits());
  VolatileBits beforeHeap=q(in,cookie,heap,0,b,in.r9Bits(),in.r10Bits(),in.r11Bits());
  VolatileBits heapReply=v(0x3300000000000300L);
  VolatileBits finalV=q(heapReply,0,d,heapReply.rdxBits(),afterCookie,heapReply.r9Bits(),heapReply.r10Bits(),heapReply.r11Bits());
  m.b.putQ(z,o);m.b.putQ(o,d);m.b.putQ(d,0x8040L);m.b.putQ(d+8,0x8048L);m.b.putQ(b,cookie);
  m.b.putQ(i+0x542F0B8L,cookie);m.b.putQ(i+0x5C5DE30L,heap);m.b.putQ(i+0x43DA748L,target);m.b.putQ(e,oldRet);
  m.expected=List.of(
   new Op("wq",e+8,n.rbxBits()),new Op("wq",e+0x10,n.rbpBits()),new Op("wq",e+0x18,n.rsiBits()),
   new Op("wq",e-8,n.rdiBits()),new Op("wq",e-0x10,n.r14Bits()),new Op("wq",e-0x18,n.r15Bits()),
   new Op("rq",z,o),new Op("rq",o,d),new Op("rq",i+0x542F0B8L,cookie),new Op("rq",d,0x8040L),new Op("rq",d+8,0x8048L),
   new Op("rq",b,cookie),new Op("wq",w-8,i+0x424DE37L),
   new Op("wq",ce-8,b-8),new Op("rq",i+0x5C5DE30L,heap),new Op("rq",i+0x43DA748L,target),
   new Op("wq",cw-8,i+0x424E380L),new Op("rq",ce-8,b-8),new Op("rq",ce,i+0x424DE37L),
   new Op("rq",i+0x542F0B8L,afterCookie),
   new Op("rq",z,o),new Op("rq",o,d),new Op("wq",d,afterCookie),
   new Op("rq",z,o),new Op("rq",o,d),new Op("wq",d+8,afterCookie),
   new Op("rq",z,o),new Op("rq",o,d),new Op("wq",d+0x10,afterCookie),
   new Op("rq",e+8,restored.rbxBits()),new Op("rq",e+0x10,restored.rbpBits()),new Op("rq",e+0x18,restored.rsiBits()),
   new Op("rq",e-0x18,restored.r15Bits()),new Op("rq",e-0x10,restored.r14Bits()),new Op("rq",e-8,restored.rdiBits()),new Op("rq",e,freshRet));
  assertEquals(36,m.expected.size());
  int[] parent={0},opaqueCall={0};
  Ports opaque=new Ports();
  opaque.invoke=c->{
   assertEquals(0,opaqueCall[0]++);
   ck(c,0x424E37AL,TargetKind.INDIRECT_ABSOLUTE,target,cw,beforeHeap,active,m,i,6);
   assertEquals(i+0x424DE37L,m.b.rawQ(ce));assertEquals(b-8,m.b.rawQ(ce-8));
   m.b.putQ(i+0x542F0B8L,afterCookie);
   m.b.putQ(e+8,restored.rbxBits());m.b.putQ(e+0x10,restored.rbpBits());m.b.putQ(e+0x18,restored.rsiBits());
   m.b.putQ(e-8,restored.rdiBits());m.b.putQ(e-0x10,restored.r14Bits());m.b.putQ(e-0x18,restored.r15Bits());m.b.putQ(e,freshRet);
   return heapReply;
  };
  TerminalAbort4242284215.Calls60 bound=EncodedClearFree61Site230Calls.bind(i,m,opaque);
  TerminalAbort4242284215.Calls60 observed=new TerminalAbort4242284215.Calls60() {
   public VolatileBits invoke(Call c) {
    assertEquals(0,parent[0]++);
    ck(c,0x424DE32L,TargetKind.DIRECT_RVA,0x424E364L,w,beforeFree,active,m,i,5);
    assertEquals(0,opaqueCall[0]);VolatileBits actual=bound.invoke(c);
    assertEquals(1,opaqueCall[0]);assertEquals(heapReply,actual);return actual;
   }
   public NormalReturn tail(Tail t) {return bound.tail(t);}
   public long readGsQword58() {return bound.readGsQword58();}
   public long readGsQword60() {return bound.readGsQword60();}
  };
  assertEquals(0,parent[0]);assertEquals(0,opaqueCall[0]);
  NormalReturn actual=EncodedClear424dd60228.execute(new Entry(i,e,in,n),m,observed);
  m.done();assertEquals(1,parent[0]);assertEquals(1,opaqueCall[0]);
  assertEquals(new NormalReturn(finalV,freshRet,e+8,restored),actual);
  assertEquals(cookie,m.b.rawQ(b));assertEquals(afterCookie,m.b.rawQ(d));assertEquals(afterCookie,m.b.rawQ(d+8));assertEquals(afterCookie,m.b.rawQ(d+0x10));
 }

}
