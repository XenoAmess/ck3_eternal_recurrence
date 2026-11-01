package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
/** Only declared input values/protocol and mechanical constructors, no expected Scene. */
public final class EmbeddedInitData557 {
 private EmbeddedInitData557() { }
 public record Cell(int widthBytes,long addressBits,long lowBits) { }
 public sealed interface Step permits Read,Write,Invoke { }
 public record Read(int widthBytes,long addressBits,long lowBits) implements Step { }
 public record Write(int widthBytes,long addressBits,long lowBits) implements Step { }
 public record Invoke(EmbeddedInit550Api.CallFrame frame,FullCopy437Api.CallResult result,List<Write> effects) implements Step { }
 public record Scene(String name,GovernmentCrtBoundary185Api.Entry entry,boolean directionFlagSet,List<Cell> initialMemory,List<Step> steps,FullCopy437Api.CallResult expectedResult,List<Cell> finalMemory) { }
 public static final long M=0x3300000000L,E=0x810000000000F008L,D=0x8100000000020000L,VT2=0x8100000000007000L,ALIAS_VT=D-0x24L,TARGET1=0x7FFF111122223333L,TARGET2=0x7FFF444455556666L,RET=0xAABBCCDD11223344L,RET2=0x1122334455667788L,RESTORED_RSI=0xDEADBEEF11223344L;
 public static Bits128 x(long seed) { return new Bits128(seed,~seed); }
 public static VolatileBits v(long seed,long ax,long cx,long dx) { return new VolatileBits(ax,cx,dx,seed+8,seed+9,seed+10,seed+11,x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60)); }
 public static NonvolatileBits n(long bx,long bp,long si,long di,long a12,long a13,long a14,long a15) { return new NonvolatileBits(bx,bp,si,di,a12,a13,a14,a15,x(0x2060)); }
 public static NonvolatileBits n0() { return n(0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008); }
 public static VolatileBits v0() { return v(0x1000,0x8877665544332211L,D,0xFEEDBEEF01020304L); }
 public static Cell c(int width,long address,long low) { return new Cell(width,address,low); }
 public static Read r(int width,long address,long low) { return new Read(width,address,low); }
 public static Write w(int width,long address,long low) { return new Write(width,address,low); }
 public static EmbeddedInit550Api.CallFrame cf(long site,long target,VolatileBits v,NonvolatileBits n,boolean df) { long body=E-0x28;return new EmbeddedInit550Api.CallFrame(new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,body,v,n),new GovernmentCrtBoundary185Api.Entry(M,body-8,v,n),df,3,M+site+3); }
 public static FullCopy437Api.CallResult result(VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df) { return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df); }
}
