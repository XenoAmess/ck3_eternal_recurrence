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
public final class EncodedClear424dd60228ParentWitnessTest {
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

 @Test void actualParentUsesTwoIndexedTailsAndClearChild228() {
  long i=0x100000000L,e=0x900000000L,w=e-0x28L,s=e-0x30L;
  long d=0x500000000L,context=0x500001000L,last=0x500002000L,outer=0x500003000L;
  long table=i+0x5C5D330L,t1=0xA100000000000100L,t2=0xA200000000000200L;
  long freshBx=0xB100000000000100L,freshDi=0xB200000000000200L,freshRet=0xB300000000000300L;
  HookMemory m=new HookMemory();
  VolatileBits seed=v(0x1100000000000100L);
  VolatileBits in=q(seed,seed.raxBits(),seed.rcxBits(),d,context,last,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits n=nv(0x2200000000000200L),active=nd(n,last,context),leaveNv=nd(n,last,0xFFFFFFFFL);
  VolatileBits enterReply=v(0x3300000000000300L),leaveReply=v(0x4400000000000400L);
  VolatileBits beforeEnter=q(in,in.raxBits(),0xFFFFFFFEL,d,context,last,in.r10Bits(),in.r11Bits());
  VolatileBits beforeMiddle=q(enterReply,enterReply.raxBits(),context,enterReply.rdxBits(),enterReply.r8Bits(),enterReply.r9Bits(),enterReply.r10Bits(),enterReply.r11Bits());
  VolatileBits middleReply=q(enterReply,0xFFFFFFFFL,context,enterReply.rdxBits(),enterReply.r8Bits(),enterReply.r9Bits(),enterReply.r10Bits(),enterReply.r11Bits());
  VolatileBits beforeLeave=q(enterReply,0xFFFFFFFFL,3L,enterReply.rdxBits(),enterReply.r8Bits(),enterReply.r9Bits(),enterReply.r10Bits(),enterReply.r11Bits());
  VolatileBits enterTail=q(in,table,table-80L,d,context,last,in.r10Bits(),in.r11Bits());
  VolatileBits leaveTail=q(enterReply,table,table+120L,enterReply.rdxBits(),enterReply.r8Bits(),enterReply.r9Bits(),enterReply.r10Bits(),enterReply.r11Bits());
  VolatileBits finalV=q(leaveReply,0xFFFFFFFFL,leaveReply.rcxBits(),leaveReply.rdxBits(),leaveReply.r8Bits(),leaveReply.r9Bits(),leaveReply.r10Bits(),leaveReply.r11Bits());
  List<Call> parentCalls=List.of(
   new Call(0x424DB8BL,TargetKind.DIRECT_RVA,0x4247FFCL,w,beforeEnter,active),
   new Call(0x424DB94L,TargetKind.DIRECT_RVA,0x424DD60L,w,beforeMiddle,active),
   new Call(0x424DB9DL,TargetKind.DIRECT_RVA,0x4248050L,w,beforeLeave,leaveNv));
  List<Tail> tailCalls=List.of(
   new Tail(0x424800EL,TargetKind.INDIRECT_ABSOLUTE,t1,new Entry(i,s,enterTail,active)),
   new Tail(0x4248062L,TargetKind.INDIRECT_ABSOLUTE,t2,new Entry(i,s,leaveTail,leaveNv)));
  List<NormalReturn> tailReplies=List.of(
   new NormalReturn(enterReply,i+0x424DB90L,w,active),
   new NormalReturn(leaveReply,i+0x424DBA2L,w,leaveNv));
  List<VolatileBits> invokeReplies=List.of(enterReply,middleReply,leaveReply);
  long[] returnSlots={i+0x424DB90L,i+0x424DB99L,i+0x424DBA2L};
  m.b.putD(d,0xFFFFFFFE);m.b.putD(last,9);m.b.putQ(context,outer);m.b.putQ(outer,0);
  m.b.putQ(i+0x43DA500L,t1);m.b.putQ(i+0x43DA4F0L,t2);m.b.putQ(e,0xC100000000000100L);
  m.expected=List.of(
   new Op("wq",e+8,n.rbxBits()),new Op("wq",e+0x20,last),new Op("wq",e-8,n.rdiBits()),
   new Op("rd",d,0xFFFFFFFEL),new Op("wq",s,i+0x424DB90L),new Op("rq",i+0x43DA500L,t1),
   new Op("wq",s,i+0x424DB99L),
   new Op("wq",s+8,last),new Op("wq",s+0x10,n.rbpBits()),new Op("wq",s+0x18,n.rsiBits()),
   new Op("wq",s-8,context),new Op("wq",s-0x10,n.r14Bits()),new Op("wq",s-0x18,n.r15Bits()),
   new Op("rq",context,outer),new Op("rq",outer,0),
   new Op("rq",s+8,last),new Op("rq",s+0x10,n.rbpBits()),new Op("rq",s+0x18,n.rsiBits()),
   new Op("rq",s-0x18,n.r15Bits()),new Op("rq",s-0x10,n.r14Bits()),new Op("rq",s-8,context),new Op("rq",s,i+0x424DB99L),
   new Op("rd",last,3),new Op("wq",s,i+0x424DBA2L),new Op("rq",i+0x43DA4F0L,t2),
   new Op("rq",e+8,freshBx),new Op("rq",e-8,freshDi),new Op("rq",e,freshRet));
  assertEquals(28,m.expected.size());
  int[] observer={0},tails={0},opaqueInvoke={0};
  Ports opaque=new Ports();
  opaque.invoke=c->{opaqueInvoke[0]++;throw new AssertionError("unexpected opaque CALL "+c);};
  opaque.tail=t->{
   assertTrue(tails[0]<2);int k=tails[0]++;
   assertEquals(tailCalls.get(k),t);
   assertEquals(k==0?i+0x424DB90L:i+0x424DBA2L,m.b.rawQ(s));
   if(k==0)m.b.putD(last,3);
   else {m.b.putQ(e+8,freshBx);m.b.putQ(e-8,freshDi);m.b.putQ(e,freshRet);}
   return tailReplies.get(k);
  };
  TerminalAbort4242284215.Calls60 clear=EncodedClear424dd60228Calls.bind(i,m,opaque);
  TerminalAbort4242284215.Calls60 indexed=StackResultIndexedTails229Calls.bind(i,m,clear);
  TerminalAbort4242284215.Calls60 observed=new TerminalAbort4242284215.Calls60() {
   public VolatileBits invoke(Call c) {
    assertTrue(observer[0]<3);int k=observer[0]++;
    assertEquals(parentCalls.get(k),c);assertEquals(returnSlots[k],m.b.rawQ(s));
    VolatileBits actual=indexed.invoke(c);assertEquals(invokeReplies.get(k),actual);
    if(k!=1)assertSame(invokeReplies.get(k),actual);
    return actual;
   }
   public NormalReturn tail(Tail t) {return indexed.tail(t);}
   public long readGsQword58() {return indexed.readGsQword58();}
   public long readGsQword60() {return indexed.readGsQword60();}
  };
  assertEquals(0,observer[0]);assertEquals(0,tails[0]);assertEquals(0,opaqueInvoke[0]);
  NormalReturn actual=StackResult424db74227.execute(new Entry(i,e,in,n),m,observed);
  m.done();assertEquals(3,observer[0]);assertEquals(2,tails[0]);assertEquals(0,opaqueInvoke[0]);
  assertEquals(new NormalReturn(finalV,freshRet,e+8,nd(n,freshBx,freshDi)),actual);
  assertEquals(0L,m.b.rawQ(outer));assertEquals(i+0x424DBA2L,m.b.rawQ(s));
 }

}
