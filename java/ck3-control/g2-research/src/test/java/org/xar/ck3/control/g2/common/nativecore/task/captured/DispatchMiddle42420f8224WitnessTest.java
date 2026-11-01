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
public final class DispatchMiddle42420f8224WitnessTest {
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

@Test void earlyFlagRetainsWholeEntryAndFreshReturn224() {
    long image = 0x10000000L, e = 0x200000L, work = e - 0x28L;
    long flagAddr = image + 0x5C5D2E8L;
    Mem32 m = new Mem32();
    m.b.putB(flagAddr, 1); // nonzero flag
    m.b.putQ(e - 8L, 0xDEADBEEFL); // saved RBX seed
    m.b.putQ(e, image + 0x42421B2L); // RET RIP seed

    VolatileBits entryV = v(0x1111111111111111L);
    NonvolatileBits entryNV = nv(0x2222222222222222L);
    Entry entry = new Entry(image, e, entryV, entryNV);

    Ports p = new Ports(); // all throw
    NormalReturn nr = DispatchMiddle42420f8224.execute(entry, m, p);

    assertEquals(4, m.b.ops.size());
    assertEquals(new Op("wq", e - 8L, entryNV.rbxBits()), m.b.ops.get(0));
    assertEquals(new Op("rb", flagAddr, 1), m.b.ops.get(1));
    assertEquals(new Op("rq", e - 8L, entryNV.rbxBits()), m.b.ops.get(2));
    assertEquals(new Op("rq", e, image + 0x42421B2L), m.b.ops.get(3));

    assertEquals(0, m.exchanges.size());
    assertEquals(image + 0x42421B2L, nr.returnRipBits());
    assertEquals(e + 8L, nr.callerRspBits());
    assertEquals(entryV, nr.volatileBits());
    assertEquals(nd(entryNV, entryNV.rbxBits(), entryNV.rdiBits()), nr.nonvolatileBits());
}
 @Test void cookiePointerAliasAndFourCallsUseFreshSourceBits224() {
  long image=0x140000000L,e=0x770000000108L,work=e-0x28L,p=image+0x542F0B8L,a=0x810000000100L;
  long decoded=0xE100000012345678L,cookieB=a^decoded,iatTarget=0xF200000087654321L;
  long second=0x820000001000L,third=0x820000002000L,output=0x820000003000L;
  long freshBx=0xA3000000ABCDEF01L,freshRip=0xB400000012345678L;
  Mem32 m=new Mem32();m.b.putB(image+0x5C5D2E8L,0);m.b.putD(image+0x5C5D2DCL,0x87654321);
  m.b.putQ(p,a);m.b.putD(a,0);m.b.putQ(image+0x5C5D2E0L,cookieB);m.b.putQ(image+0x43DBBA8L,iatTarget);
  m.b.putQ(p+8,0x830000001000L);m.b.putQ(p+0x10L,0x830000002000L);m.b.putD(second,0);m.b.putD(third,0);m.b.putB(output,0x7F);m.b.putQ(e,0x1111222233334444L);
  VolatileBits seed=v(0xC500000000004000L),initial=q(seed,seed.raxBits(),p,seed.rdxBits(),seed.r8Bits(),seed.r9Bits(),seed.r10Bits(),seed.r11Bits());
  NonvolatileBits saved=nv(0xD600000000005000L),active=nd(saved,p,saved.rdiBits());
  VolatileBits first=v(0x9100000000001000L),de88=v(0xA200000000002000L),error1=v(0xB300000000003000L),error2=v(0xC400000000004000L);
  Ports ports=new Ports();int[] calls={0};
  ports.invoke=call->{
   int step=calls[0]++;
   if(step==0) {
    ck(call,0x4242147L,TargetKind.INDIRECT_ABSOLUTE,iatTarget,work,q(initial,decoded,0,0,0,initial.r9Bits(),initial.r10Bits(),initial.r11Bits()),active,m,image,6);
    assertEquals(List.of(new Exchange(image+0x5C5D2DCL,0x87654321,1)),m.exchanges);
    m.writeQword(e-8,freshBx);return first;
   }
   if(step==1) {
    ck(call,0x4242162L,TargetKind.DIRECT_RVA,0x424DE88L,work,q(first,first.raxBits(),image+0x5C5D698L,first.rdxBits(),first.r8Bits(),first.r9Bits(),first.r10Bits(),first.r11Bits()),active,m,image,5);
    m.writeQword(p,second);return de88;
   }
   if(step==2) {
    ck(call,0x424217EL,TargetKind.DIRECT_RVA,0x424E1ACL,work,q(de88,second,image+0x441ED48L,image+0x441ED70L,de88.r8Bits(),de88.r9Bits(),de88.r10Bits(),de88.r11Bits()),active,m,image,5);
    m.writeQword(p+8,third);return error1;
   }
   if(step==3) {
    ck(call,0x4242191L,TargetKind.DIRECT_RVA,0x424E1ACL,work,q(error1,error1.raxBits(),image+0x441ED78L,image+0x441ED80L,error1.r8Bits(),error1.r9Bits(),error1.r10Bits(),error1.r11Bits()),active,m,image,5);
    m.writeQword(p+0x10L,output);m.writeQword(e,freshRip);return error2;
   }
   throw new AssertionError(call);
  };
  NormalReturn nr=DispatchMiddle42420f8224.execute(new Entry(image,e,initial,saved),m,ports);
  assertEquals(4,calls[0]);assertEquals(q(error2,output,error2.rcxBits(),error2.rdxBits(),error2.r8Bits(),error2.r9Bits(),error2.r10Bits(),error2.r11Bits()),nr.volatileBits());
  assertEquals(nd(saved,freshBx,saved.rdiBits()),nr.nonvolatileBits());assertEquals(freshRip,nr.returnRipBits());assertEquals(e+8,nr.callerRspBits());
  assertEquals(List.of(new Exchange(image+0x5C5D2DCL,0x87654321,1)),m.exchanges);assertEquals(1,m.b.rawD(image+0x5C5D2DCL));assertEquals(1,m.b.rawB(image+0x5C5D2E8L));assertEquals(1,m.b.rawB(output));
  assertEquals(List.of(
   new Op("wq",e-8,saved.rbxBits()),new Op("rb",image+0x5C5D2E8L,0),new Op("xchg32",image+0x5C5D2DCL,1),
   new Op("rq",p,a),new Op("rd",a,0),new Op("rq",p,a),new Op("rq",image+0x5C5D2E0L,cookieB),new Op("rq",image+0x43DBBA8L,iatTarget),
   new Op("wq",work-8,image+0x424214DL),new Op("wq",e-8,freshBx),new Op("wq",work-8,image+0x4242167L),new Op("wq",p,second),
   new Op("rq",p,second),new Op("rd",second,0),new Op("wq",work-8,image+0x4242183L),new Op("wq",p+8,third),
   new Op("wq",work-8,image+0x4242196L),new Op("wq",p+0x10L,output),new Op("wq",e,freshRip),
   new Op("rq",p+8,third),new Op("rd",third,0),new Op("wb",image+0x5C5D2E8L,1),new Op("rq",p+0x10L,output),new Op("wb",output,1),new Op("rq",e-8,freshBx),new Op("rq",e,freshRip)),m.b.ops);
 }

 @Test void actual223ParentBindsNormalMiddle224() {
  long image=0x180000000L,e=0x780000000108L,parentWork=e-0x28L,childWork=e-0x58L;
  long context=0x840000001000L,firstPtr=0x840000002000L,thirdPtr=0x840000003000L,entryD=0x840000004000L,lastD=0x840000005000L,rip=0xD500000012345678L;
  Mem32 m=new Mem32();m.b.putB(image+0x5C5D2E8L,0);m.b.putD(image+0x5C5D2DCL,0xFEDCBA98);
  m.b.putQ(context,firstPtr);m.b.putD(firstPtr,2);m.b.putQ(context+8,thirdPtr);m.b.putD(thirdPtr,0xFFFFFFFF);m.b.putQ(context+0x10L,0x850000001000L);
  m.b.putD(entryD,0x80000002);m.b.putD(lastD,0x12345678);m.b.putQ(e,rip);
  VolatileBits seed=v(0xE600000000001000L),initial=q(seed,seed.raxBits(),seed.rcxBits(),entryD,context,lastD,seed.r10Bits(),seed.r11Bits());
  NonvolatileBits saved=nv(0xF700000000002000L),parentActive=nd(saved,lastD,context),childActive=nd(parentActive,context,context);
  VolatileBits enter=v(0x9100000000003000L),childReply=v(0xA200000000004000L),leave=v(0xB300000000005000L);
  VolatileBits middleIn=q(enter,enter.raxBits(),context,enter.rdxBits(),enter.r8Bits(),enter.r9Bits(),enter.r10Bits(),enter.r11Bits());
  Ports fallback=new Ports();int[] callbacks={0},matchingMiddle={0};
  fallback.invoke=call->{
   int step=callbacks[0]++;
   if(step==0) {
    ck(call,0x42420D7L,TargetKind.DIRECT_RVA,0x4247FFCL,parentWork,q(initial,initial.raxBits(),0x80000002L,entryD,context,lastD,initial.r10Bits(),initial.r11Bits()),parentActive,m,image,5);return enter;
   }
   if(step==1) {
    ck(call,0x4242191L,TargetKind.DIRECT_RVA,0x424E1ACL,childWork,q(enter,firstPtr,image+0x441ED78L,image+0x441ED80L,enter.r8Bits(),enter.r9Bits(),enter.r10Bits(),enter.r11Bits()),childActive,m,image,5);
    m.writeDword(lastD,0xFEE10001);return childReply;
   }
   if(step==2) {
    ck(call,0x42420E8L,TargetKind.DIRECT_RVA,0x4248050L,parentWork,q(childReply,thirdPtr,0xFEE10001L,childReply.rdxBits(),childReply.r8Bits(),childReply.r9Bits(),childReply.r10Bits(),childReply.r11Bits()),parentActive,m,image,5);return leave;
   }
   throw new AssertionError(call);
  };
  TerminalAbort4242284215.Calls60 bound=DispatchMiddle42420f8224Calls.bind(image,m,fallback);
  Ports observed=new Ports();observed.invoke=call->{if(call.callSiteRva()==0x42420E0L){matchingMiddle[0]++;ck(call,0x42420E0L,TargetKind.DIRECT_RVA,0x42420F8L,parentWork,middleIn,parentActive,m,image,5);}return bound.invoke(call);};
  NormalReturn nr=DispatchHelper42420c0223.execute(new Entry(image,e,initial,saved),m,observed);
  assertEquals(3,callbacks[0]);assertEquals(1,matchingMiddle[0]);assertEquals(leave,nr.volatileBits());assertEquals(saved,nr.nonvolatileBits());assertEquals(rip,nr.returnRipBits());assertEquals(e+8,nr.callerRspBits());
  assertEquals(List.of(new Exchange(image+0x5C5D2DCL,0xFEDCBA98,1)),m.exchanges);assertEquals(0,m.b.rawB(image+0x5C5D2E8L));assertEquals(1,m.b.rawD(image+0x5C5D2DCL));
  assertEquals(List.of(
   new Op("wq",e+8,saved.rbxBits()),new Op("wq",e+0x20L,lastD),new Op("wq",e-8,saved.rdiBits()),new Op("rd",entryD,0x80000002L),
   new Op("wq",e-0x30L,image+0x42420DCL),new Op("wq",e-0x30L,image+0x42420E5L),new Op("wq",e-0x38L,lastD),
   new Op("rb",image+0x5C5D2E8L,0),new Op("xchg32",image+0x5C5D2DCL,1),new Op("rq",context,firstPtr),new Op("rd",firstPtr,2),new Op("rq",context,firstPtr),new Op("rd",firstPtr,2),
   new Op("wq",e-0x60L,image+0x4242196L),new Op("wd",lastD,0xFEE10001L),new Op("rq",context+8,thirdPtr),new Op("rd",thirdPtr,0xFFFFFFFFL),
   new Op("rq",e-0x38L,lastD),new Op("rq",e-0x30L,image+0x42420E5L),new Op("rd",lastD,0xFEE10001L),new Op("wq",e-0x30L,image+0x42420EDL),
   new Op("rq",e+8,saved.rbxBits()),new Op("rq",e-8,saved.rdiBits()),new Op("rq",e,rip)),m.b.ops);
 }

}
