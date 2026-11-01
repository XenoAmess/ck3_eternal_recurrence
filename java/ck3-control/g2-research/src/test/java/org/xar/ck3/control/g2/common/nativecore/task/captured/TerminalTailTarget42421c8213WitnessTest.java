package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class TerminalTailTarget42421c8213WitnessTest {
 static Bits128 x(long b) { return new Bits128(b,b+1); }
 static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
 static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
 static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
 static class Ports implements Calls {
  public VolatileBits invoke(Call c) { throw new AssertionError(c); }
  public NormalReturn tail(Tail t) { throw new AssertionError(t); }
  public long readGsQword58() { throw new AssertionError("GS"); }
 }
 static final class Mem implements TerminalTailTarget42421c8213.Memory16 {
  final Bytes b=new Bytes();
  public int readDword(long a) { return b.readDword(a); }
  public long readQword(long a) { return b.readQword(a); }
  public int readUnsignedByte(long a) { return b.readUnsignedByte(a); }
  public void writeDword(long a,int value) { b.writeDword(a,value); }
  public void writeQword(long a,long value) { b.writeQword(a,value); }
  public void writeByte(long a,int value) { b.writeByte(a,value); }
  public int lockedXaddDword(long a,int addend) { return b.lockedXaddDword(a,addend); }
  public Bits128 read128(long a) { return b.read128(a); }
  public void write128(long a,Bits128 value) { b.write128(a,value); }
  public int readUnsigned16(long a) { int value=(int)b.raw(a,2);b.ops.add(new Op("rw",a,value));return value; }
 }
 @Test void parentTailNormalRestoresFreshSharedHomes213() {
  long I=0x140000000L,E=0x730000000108L,W=E-0x58,iat=0x8A00000001234567L;
  long inputC=0xABCDEF0180000091L,freshBx=0x81F1000000000011L,freshBp=0x82F2000000000022L,freshRip=0x83F3000000000033L;
  Mem m=new Mem(); NonvolatileBits n=nv(0x441100000000L);
  VolatileBits in=v(0x110000000000L);
  in=q(in,in.raxBits(),inputC,0xABC1000000000033L,0xABC2000000000044L,in.r9Bits(),in.r10Bits(),in.r11Bits());
  VolatileBits initial=in,parentV=q(in,in.raxBits(),inputC,2,0,in.r9Bits(),in.r10Bits(),in.r11Bits());
  VolatileBits a0=v(0x220000000000L),a=q(a0,0,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits()),b=v(0x330000000000L);
  NonvolatileBits active=new NonvolatileBits(0x80000091L,E-8,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(I+0x43DA620L,iat);m.b.putQ(E,I+0x345678L);
  m.b.putQ(E+0x10,0xD7D6D5D4D3D2D1D0L);m.b.putQ(E+0x18,0xC7C6C5C4C3C2C1C0L);m.b.putQ(E+0x20,0xE7E6E5E4E3E2E1E0L);
  List<Call> seen=new ArrayList<>();
  Calls ports=new Ports() {
   @Override public VolatileBits invoke(Call c) {
    seen.add(c);m.b.ops.add(new Op("call",c.callSiteRva(),c.targetBits()));
    if(seen.size()==1) {
     assertEquals(new Call(0x42421E7L,TargetKind.INDIRECT_ABSOLUTE,iat,W,q(parentV,parentV.raxBits(),0,2,0,parentV.r9Bits(),parentV.r10Bits(),parentV.r11Bits()),active),c);
     assertEquals(I+0x42421EDL,m.b.rawQ(W-8));return a;
    }
    assertEquals(2,seen.size());
    assertEquals(new Call(0x4242266L,TargetKind.DIRECT_RVA,0x42420C0L,W,q(a,2,E-0x38,E-0x30,E-0x28,E-0x34,a.r10Bits(),a.r11Bits()),active),c);
    assertEquals(I+0x424226BL,m.b.rawQ(W-8));
    m.writeDword(E+0x18,0xFEDCBA98);m.writeQword(E+8,freshBx);m.writeQword(E-8,freshBp);m.writeQword(E,freshRip);return b;
   }
  };
  Calls bound=TerminalTailTarget42421c8213Calls.bind(m,ports);List<NormalReturn> actualTailReturns=new ArrayList<>();
  Calls observing=new Ports() {
   @Override public NormalReturn tail(Tail t) {
    assertEquals(new Tail(0x424235BL,TargetKind.DIRECT_RVA,0x42421C8L,new Entry(I,E,parentV,n)),t);
    m.b.ops.add(new Op("tail",t.jumpSiteRva(),t.targetBits()));
    NormalReturn nr=bound.tail(t);actualTailReturns.add(nr);return nr;
   }
  };
  NormalReturn got=TerminalTail4242354212.execute(new Entry(I,E,initial,n),m,observing);
  assertEquals(1,actualTailReturns.size());assertSame(actualTailReturns.get(0),got);assertEquals(2,seen.size());
  NonvolatileBits restored=new NonvolatileBits(freshBx,freshBp,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  assertEquals(new NormalReturn(b,freshRip,E+8,restored),got);
  assertEquals(0xD7D6D5D400000002L,m.b.rawQ(E+0x10));assertEquals(0xC7C6C5C4FEDCBA98L,m.b.rawQ(E+0x18));assertEquals(0xE7E6E5E4E3E2E100L,m.b.rawQ(E+0x20));
  assertEquals(List.of(
   new Op("tail",0x424235BL,0x42421C8L),new Op("wq",E+8,n.rbxBits()),new Op("wd",E+0x18,0),new Op("wd",E+0x10,2),new Op("wq",E-8,n.rbpBits()),
   new Op("rq",I+0x43DA620L,iat),new Op("wq",W-8,I+0x42421EDL),new Op("call",0x42421E7L,iat),
   new Op("wb",E+0x20,0),new Op("wq",E-0x28,E+0x10),new Op("wq",E-0x20,E+0x18),new Op("wq",E-0x18,E+0x20),new Op("wd",E-0x34,2),new Op("wd",E-0x30,2),
   new Op("wq",W-8,I+0x424226BL),new Op("call",0x4242266L,0x42420C0L),new Op("wd",E+0x18,0xFEDCBA98L),new Op("wq",E+8,freshBx),new Op("wq",E-8,freshBp),new Op("wq",E,freshRip),
   new Op("rd",E+0x18,0xFEDCBA98L),new Op("rq",E+8,freshBx),new Op("rq",E-8,freshBp),new Op("rq",E,freshRip)),m.b.ops);
 }

 @Test void signedNegativePeOffsetAndExactWords213() {
  long I=0x180000000L,E=0x730000000108L,W=E-0x58,iat=0x8B00000007654321L;
  long p=0x610000000100L,h=p-0x80,inputC=0xFACEB00C90000027L,rip=0x9182000000001177L;
  Mem m=new Mem();NonvolatileBits n=nv(0x550000000000L);VolatileBits in0=v(0x660000000000L);
  VolatileBits in=q(in0,in0.raxBits(),inputC,0xABCD0000F1234567L,0x9876543200000000L,in0.r9Bits(),in0.r10Bits(),in0.r11Bits());
  VolatileBits a0=v(0x770000000000L),a=q(a0,p,a0.rcxBits(),a0.rdxBits(),a0.r8Bits(),a0.r9Bits(),a0.r10Bits(),a0.r11Bits()),b=v(0x880000000000L),c=v(0x990000000000L);
  NonvolatileBits active=new NonvolatileBits(0x90000027L,E-8,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(I+0x43DA620L,iat);m.b.putQ(E,rip);m.b.putQ(E+0x10,0xA7A6A5A4A3A2A1A0L);m.b.putQ(E+0x18,0xB7B6B5B4B3B2B1B0L);
  m.b.put(p,0x5A4D,2);m.b.putD(p+0x3C,-128);m.b.putD(h,0x4550);m.b.put(h+0x18,0x20B,2);m.b.putD(h+0x84,0x8000000F);m.b.putD(h+0xF8,1);
  List<Call> seen=new ArrayList<>();Calls ports=new Ports() {
   @Override public VolatileBits invoke(Call call) {
    seen.add(call);m.b.ops.add(new Op("call",call.callSiteRva(),call.targetBits()));
    if(seen.size()==1) {
     assertEquals(new Call(0x42421E7L,TargetKind.INDIRECT_ABSOLUTE,iat,W,q(in,in.raxBits(),0,in.rdxBits(),in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits()),active),call);
     assertEquals(I+0x42421EDL,m.b.rawQ(W-8));return a;
    }
    if(seen.size()==2) {
     assertEquals(new Call(0x424222AL,TargetKind.DIRECT_RVA,0x42422D0L,W,q(a,0x20B,0x90000027L,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),active),call);
     assertEquals(I+0x424222FL,m.b.rawQ(W-8));return b;
    }
    assertEquals(3,seen.size());assertEquals(new Call(0x4242266L,TargetKind.DIRECT_RVA,0x42420C0L,W,q(b,2,E-0x38,E-0x30,E-0x28,E-0x34,b.r10Bits(),b.r11Bits()),active),call);
    assertEquals(I+0x424226BL,m.b.rawQ(W-8));m.writeDword(E+0x18,0x80000001);return c;
   }
  };
  NormalReturn got=TerminalTailTarget42421c8213.execute(new Entry(I,E,in,n),m,ports);
  assertEquals(3,seen.size());assertEquals(new NormalReturn(c,rip,E+8,n),got);
  assertEquals(0xA7A6A5A4F1234567L,m.b.rawQ(E+0x10));assertEquals(0xB7B6B5B480000001L,m.b.rawQ(E+0x18));
  assertEquals(List.of(
   new Op("wq",E+8,n.rbxBits()),new Op("wd",E+0x18,0),new Op("wd",E+0x10,0xF1234567L),new Op("wq",E-8,n.rbpBits()),new Op("rq",I+0x43DA620L,iat),new Op("wq",W-8,I+0x42421EDL),new Op("call",0x42421E7L,iat),
   new Op("rw",p,0x5A4D),new Op("rd",p+0x3C,0xFFFFFF80L),new Op("rd",h,0x4550),new Op("rw",h+0x18,0x20B),new Op("rd",h+0x84,0x8000000FL),new Op("rd",h+0xF8,1),new Op("wq",W-8,I+0x424222FL),new Op("call",0x424222AL,0x42422D0L),
   new Op("wb",E+0x20,0),new Op("wq",E-0x28,E+0x10),new Op("wq",E-0x20,E+0x18),new Op("wq",E-0x18,E+0x20),new Op("wd",E-0x34,2),new Op("wd",E-0x30,2),new Op("wq",W-8,I+0x424226BL),new Op("call",0x4242266L,0x42420C0L),new Op("wd",E+0x18,0x80000001L),
   new Op("rd",E+0x18,0x80000001L),new Op("rq",E+8,n.rbxBits()),new Op("rq",E-8,n.rbpBits()),new Op("rq",E,rip)),m.b.ops);
 }

 @Test void nonzeroR8SkipsIatAndOwnsSoftwareInt3213() {
  long I=0x1C0000000L,E=0x730000000108L,W=E-0x58,inputC=0xAA550033F1000023L,rip=0xFFEEDDCCBBAA0099L;
  Mem m=new Mem();NonvolatileBits n=nv(0xA10000000000L);VolatileBits z=v(0xB20000000000L);
  VolatileBits in=q(z,z.raxBits(),inputC,0xFFFF00008ABCDEFFL,0x1234567800000007L,z.r9Bits(),z.r10Bits(),z.r11Bits()),a=v(0xC30000000000L),b=v(0xD40000000000L);
  NonvolatileBits active=new NonvolatileBits(0xF1000023L,E-8,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
  m.b.putQ(E,rip);List<Call> seen=new ArrayList<>();Calls ports=new Ports() {
   @Override public VolatileBits invoke(Call c) {
    seen.add(c);m.b.ops.add(new Op("call",c.callSiteRva(),c.targetBits()));
    if(seen.size()==1) {
     assertEquals(new Call(0x4242266L,TargetKind.DIRECT_RVA,0x42420C0L,W,q(in,2,E-0x38,E-0x30,E-0x28,E-0x34,in.r10Bits(),in.r11Bits()),active),c);
     assertEquals(I+0x424226BL,m.b.rawQ(W-8));m.writeDword(E+0x18,0);return a;
    }
    assertEquals(2,seen.size());assertEquals(new Call(0x424227EL,TargetKind.DIRECT_RVA,0x4242284L,W,q(a,a.raxBits(),0xF1000023L,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),active),c);
    assertEquals(I+0x4242283L,m.b.rawQ(W-8));return b;
   }
  };
  assertThrows(UnsupportedOperationException.class,()->TerminalTailTarget42421c8213.execute(new Entry(I,E,in,n),m,ports));
  assertEquals(2,seen.size());assertEquals(rip,m.b.rawQ(E));
  assertEquals(List.of(
   new Op("wq",E+8,n.rbxBits()),new Op("wd",E+0x18,7),new Op("wd",E+0x10,0x8ABCDEFFL),new Op("wq",E-8,n.rbpBits()),
   new Op("wb",E+0x20,0),new Op("wq",E-0x28,E+0x10),new Op("wq",E-0x20,E+0x18),new Op("wq",E-0x18,E+0x20),new Op("wd",E-0x34,2),new Op("wd",E-0x30,2),
   new Op("wq",W-8,I+0x424226BL),new Op("call",0x4242266L,0x42420C0L),new Op("wd",E+0x18,0),new Op("rd",E+0x18,0),new Op("wq",W-8,I+0x4242283L),new Op("call",0x424227EL,0x4242284L)),m.b.ops);
 }

}
