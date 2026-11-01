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
public final class IndexedHelper424e448225WitnessTest {
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
 static void ck(Call c,long site,TargetKind kind,long target,long work,VolatileBits value,NonvolatileBits n,Mem64 m,long image,int len) {
  assertEquals(new Call(site,kind,target,work,value,n),c);assertEquals(image+site+len,m.b.rawQ(work-8));
 }
 static NonvolatileBits n8(NonvolatileBits n,long bx,long bp,long si,long di,long r12,long r13,long r14,long r15) {return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,n.xmm6());}
 record Exchange(long address,long before,long after) { }
 static final class Mem64 implements IndexedHelper424e448225.Memory64 {
  final Mem base=new Mem();
  final LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes b=base.b;
  final List<Exchange> exchanges=new ArrayList<>();
  public long exchangeQword(long a,long value) {long old=b.rawQ(a);exchanges.add(new Exchange(a,old,value));b.ops.add(new Op("xchg64",a,value));b.putQ(a,value);return old;}
  public int readDword(long a) {return base.readDword(a);}
  public long readQword(long a) {return base.readQword(a);}
  public int readUnsignedByte(long a) {return base.readUnsignedByte(a);}
  public void writeDword(long a,int value) {base.writeDword(a,value);}
  public void writeQword(long a,long value) {base.writeQword(a,value);}
  public void writeByte(long a,int value) {base.writeByte(a,value);}
  public int lockedXaddDword(long a,int addend) {return base.lockedXaddDword(a,addend);}
  public Bits128 read128(long a) {return base.read128(a);}
  public void write128(long a,Bits128 value) {base.write128(a,value);}
 }

 @Test void cachedFastPathsKeepPartialClAndFreshFrame225() {
  long image=0x140000000L,e=0x790000000108L;
  long[] indices={3L,0x80000003L},encoded={0x8111223344556677L,-1L};
  long[] expectedRax={0x8111223344556677L,0L},expectedRcx={0x8111223344556600L,0xFFFFFFFFFFFFFF00L};
  for(int row=0;row<2;row++) {
   Mem64 m=new Mem64();long slot=image+0x5C5D790L+indices[row]*8L,rip=0xB700000012340000L+row;
   m.b.putQ(slot,encoded[row]);m.b.putQ(image+0x542F0B8L,0);m.b.putQ(e,rip);
   VolatileBits seed=v(0xC800000000001000L);
   VolatileBits initial=q(seed,seed.raxBits(),0xA700000000000000L|indices[row],seed.rdxBits(),seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
   NonvolatileBits saved=nv(0xD900000000002000L);
   NormalReturn nr=IndexedHelper424e448225.execute(new Entry(image,e,initial,saved),m,new Ports());
   assertEquals(q(initial,expectedRax[row],expectedRcx[row],encoded[row],initial.r8Bits(),initial.r9Bits(),0,initial.r11Bits()),nr.volatileBits());
   assertEquals(saved,nr.nonvolatileBits());assertEquals(rip,nr.returnRipBits());assertEquals(e+8,nr.callerRspBits());assertTrue(m.exchanges.isEmpty());
   long[] homes={e+8,e+0x10L,e+0x18L,e-8,e-0x10L,e-0x18L,e-0x20L,e-0x28L};
   long[] bits={saved.rbxBits(),saved.rbpBits(),saved.rsiBits(),saved.rdiBits(),saved.r12Bits(),saved.r13Bits(),saved.r14Bits(),saved.r15Bits()};
   List<Op> expected=new ArrayList<>();for(int j=0;j<8;j++)expected.add(new Op("wq",homes[j],bits[j]));
   expected.add(new Op("rq",slot,encoded[row]));expected.add(new Op("rq",image+0x542F0B8L,0));
   for(int j:new int[]{0,1,2,7,6,5,4,3})expected.add(new Op("rq",homes[j],bits[j]));expected.add(new Op("rq",e,rip));
   assertEquals(19,expected.size());assertEquals(expected,m.b.ops);
  }
 }

 @Test void exchangeOldBitsSurviveTwoLoadersAndFreshCookies225() {
  long image=0x180000000L,e=0x7A0000000108L,work=e-0x48L,name=0x890000010000L,list=0x890000020000L,end=list+8;
  long path20=0x890000030000L,path21=0x890000040000L,slot=image+0x5C5D790L,cache20=image+0x5C5D6F0L+20*8L,cache21=image+0x5C5D6F0L+21*8L,cookie=image+0x542F0B8L;
  long oldA=0xCD00000087654321L,oldB=0xEF0000000A0B0C0DL,module=0xAB00000012345678L,resolved=0x9100000011223344L,c2=0xA20000005566778AL;
  long loadTarget=0xB300000000001111L,errorTarget=0xC400000000002222L,releaseTarget=0xD500000000003333L,resolveTarget=0xE600000000004444L,rip=0xF700000000005555L;
  Mem64 m=new Mem64();assertEquals(slot,cache20);m.b.putQ(slot,0);m.b.putQ(cache21,0);m.b.putQ(cookie,0);m.b.putD(list,20);m.b.putD(list+4,21);
  m.b.putQ(image+0x44269D0L+20*8L,path20);m.b.putQ(image+0x44269D0L+21*8L,path21);
  m.b.putQ(image+0x43DA478L,loadTarget);m.b.putQ(image+0x43DA738L,errorTarget);m.b.putQ(image+0x43DA7C0L,releaseTarget);m.b.putQ(image+0x43DA680L,resolveTarget);m.b.putQ(e,0x1111222233334444L);
  VolatileBits seed=v(0x8200000000001000L),initial=q(seed,seed.raxBits(),0xDE00000000000000L,name,list,end,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits saved=nv(0x9300000000002000L);
  VolatileBits a=v(0xA400000000003000L),b=v(0xB500000000004000L),c=v(0xC600000000005000L),release=v(0xD700000000006000L),answer=v(0xE800000000007000L);
  VolatileBits load1=q(a,0,a.rcxBits(),a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits());
  VolatileBits error=q(b,0xC700000000000005L,b.rcxBits(),b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits());
  VolatileBits load2=q(c,module,c.rcxBits(),c.rdxBits(),c.r8Bits(),c.r9Bits(),c.r10Bits(),c.r11Bits());
  VolatileBits finalReply=q(answer,resolved,answer.rcxBits(),answer.rdxBits(),answer.r8Bits(),answer.r9Bits(),answer.r10Bits(),answer.r11Bits());
  NonvolatileBits firstNv=n8(saved,0,list,20,-1L,end,name,path20,0),secondNv=n8(saved,0,list+4,21,-1L,end,name,path21,0),foundNv=n8(saved,module,list+4,21,-1L,end,name,image,0);
  long[] homes={e+8,e+0x10L,e+0x18L,e-8,e-0x10L,e-0x18L,e-0x20L,e-0x28L};
  long[] restored={0xA900000000000001L,0xA900000000000002L,0xA900000000000003L,0xA900000000000004L,0xA900000000000005L,0xA900000000000006L,0xA900000000000007L,0xA900000000000008L};
  Ports ports=new Ports();int[] calls={0};
  ports.invoke=call->{
   int step=calls[0]++;
   if(step==0){ck(call,0x424E4EBL,TargetKind.INDIRECT_ABSOLUTE,loadTarget,work,q(initial,0,path20,0,0x800,end,0,initial.r11Bits()),firstNv,m,image,6);return load1;}
   if(step==1){ck(call,0x424E4F9L,TargetKind.INDIRECT_ABSOLUTE,errorTarget,work,load1,firstNv,m,image,6);m.writeQword(slot,oldA);return error;}
   if(step==2){ck(call,0x424E4EBL,TargetKind.INDIRECT_ABSOLUTE,loadTarget,work,q(error,oldA,path21,0,0x800,error.r9Bits(),error.r10Bits(),error.r11Bits()),secondNv,m,image,6);m.writeQword(cache21,oldB);return load2;}
   if(step==3){ck(call,0x424E574L,TargetKind.INDIRECT_ABSOLUTE,releaseTarget,work,q(load2,oldB,module,load2.rdxBits(),load2.r8Bits(),load2.r9Bits(),load2.r10Bits(),load2.r11Bits()),foundNv,m,image,6);m.writeQword(cookie,c2);return release;}
   if(step==4){ck(call,0x424E5A0L,TargetKind.INDIRECT_ABSOLUTE,resolveTarget,work,q(release,release.raxBits(),module,name,release.r8Bits(),release.r9Bits(),c2,release.r11Bits()),foundNv,m,image,6);m.writeQword(cookie,0);for(int j=0;j<8;j++)m.writeQword(homes[j],restored[j]);m.writeQword(e,rip);return finalReply;}
   throw new AssertionError(call);
  };
  NormalReturn nr=IndexedHelper424e448225.execute(new Entry(image,e,initial,saved),m,ports);
  assertEquals(5,calls[0]);assertEquals(q(finalReply,resolved,64,-1L,0,finalReply.r9Bits(),finalReply.r10Bits(),finalReply.r11Bits()),nr.volatileBits());
  assertEquals(n8(saved,restored[0],restored[1],restored[2],restored[3],restored[4],restored[5],restored[6],restored[7]),nr.nonvolatileBits());assertEquals(rip,nr.returnRipBits());assertEquals(e+8,nr.callerRspBits());
  assertEquals(List.of(new Exchange(slot,oldA,-1L),new Exchange(cache21,oldB,module),new Exchange(slot,-1L,resolved)),m.exchanges);
  assertEquals(resolved,m.b.rawQ(slot));assertEquals(module,m.b.rawQ(cache21));assertEquals(5,m.b.writesAt(work-8).size());assertEquals(53,m.b.ops.size());
  List<Op> expected=new ArrayList<>(List.of(new Op("rq",slot,0),new Op("rq",cookie,0),new Op("rd",list,20),new Op("rq",slot,0),
   new Op("rq",image+0x44269D0L+20*8L,path20),new Op("rq",image+0x43DA478L,loadTarget),new Op("rq",image+0x43DA738L,errorTarget),new Op("xchg64",slot,-1L),
   new Op("rd",list+4,21),new Op("rq",cache21,0),new Op("rq",image+0x44269D0L+21*8L,path21),new Op("rq",image+0x43DA478L,loadTarget),new Op("xchg64",cache21,module),
   new Op("rq",image+0x43DA7C0L,releaseTarget),new Op("rq",cookie,c2),new Op("rq",image+0x43DA680L,resolveTarget),new Op("rq",cookie,0),new Op("xchg64",slot,resolved)));
  for(int j:new int[]{0,1,2,7,6,5,4,3})expected.add(new Op("rq",homes[j],restored[j]));expected.add(new Op("rq",e,rip));
  assertEquals(expected,m.b.ops.stream().filter(op->op.kind().equals("rq")||op.kind().equals("rd")||op.kind().equals("xchg64")).toList());
 }

 @Test void actual218BindingTailsWithExactOpaqueIdentity225() {
  long image=0x1C0000000L,e=0x7B0000000108L,work=e-0x28L,child=e-0x30L,encoded=0x9100000012345678L,target=0xA2000000CAFEBABEL;
  Mem64 m=new Mem64();long slot=image+0x5C5D790L+0x1CL*8L;
  m.b.putQ(slot,encoded);m.b.putQ(image+0x542F0B8L,0);m.b.putQ(image+0x43DBBA8L,target);m.b.putQ(e,0xF3000000ABCD1234L);
  VolatileBits seed=v(0xB400000000001000L),initial=q(seed,seed.raxBits(),0x8A0000000000F00DL,seed.rdxBits(),seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
  NonvolatileBits saved=nv(0xC500000000002000L),active=nd(saved,initial.rcxBits(),saved.rdiBits());
  VolatileBits callV=q(initial,initial.raxBits(),0x1CL,image+0x4427010L,image+0x442700CL,image+0x4427010L,initial.r10Bits(),initial.r11Bits());
  VolatileBits tailV=q(initial,encoded,-6L,initial.rcxBits(),image+0x442700CL,image+0x4427010L,0,initial.r11Bits());
  NormalReturn arbitrary=new NormalReturn(v(0xD600000000003000L),0xE700000012345678L,0xF800000087654321L,nv(0x9900000000004000L));
  Ports fallback=new Ports();int[] matching={0},tails={0};
  fallback.tail=transfer->{tails[0]++;assertEquals(new Tail(0x424E65CL,TargetKind.INDIRECT_ABSOLUTE,target,new Entry(image,e,tailV,saved)),transfer);return arbitrary;};
  TerminalAbort4242284215.Calls60 bound=IndexedHelper424e448225Calls.bind(image,m,fallback);
  Ports observed=new Ports();observed.invoke=call->{matching[0]++;ck(call,0x424E643L,TargetKind.DIRECT_RVA,0x424E448L,work,callV,active,m,image,5);return bound.invoke(call);};observed.tail=bound::tail;
  NormalReturn result=OutHelper424e620218.execute(new Entry(image,e,initial,saved),m,observed);
  assertSame(arbitrary,result);assertEquals(1,matching[0]);assertEquals(1,tails[0]);assertTrue(m.exchanges.isEmpty());
  long[] homes={child+8,child+0x10L,child+0x18L,child-8,child-0x10L,child-0x18L,child-0x20L,child-0x28L};
  long[] bits={active.rbxBits(),active.rbpBits(),active.rsiBits(),active.rdiBits(),active.r12Bits(),active.r13Bits(),active.r14Bits(),active.r15Bits()};
  List<Op> expected=new ArrayList<>(List.of(new Op("wq",e-8,saved.rbxBits()),new Op("wq",child,image+0x424E648L)));
  for(int j=0;j<8;j++)expected.add(new Op("wq",homes[j],bits[j]));expected.add(new Op("rq",slot,encoded));expected.add(new Op("rq",image+0x542F0B8L,0));
  for(int j:new int[]{0,1,2,7,6,5,4,3})expected.add(new Op("rq",homes[j],bits[j]));expected.add(new Op("rq",child,image+0x424E648L));
  expected.add(new Op("rq",e-8,saved.rbxBits()));expected.add(new Op("rq",image+0x43DBBA8L,target));
  assertEquals(23,expected.size());assertEquals(expected,m.b.ops);
 }

}
