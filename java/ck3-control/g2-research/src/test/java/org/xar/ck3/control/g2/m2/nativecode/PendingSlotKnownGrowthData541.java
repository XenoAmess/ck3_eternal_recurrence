package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
/** Pure declarations, owned recipe constants, mechanical constructors; no scene/trace/expected state. */
public final class PendingSlotKnownGrowthData541 {
 private PendingSlotKnownGrowthData541() { }
 public record Cell(int widthBytes,long addressBits,long lowBits,long highBits) { }
 public sealed interface Step permits Read,Write,GrowthInvoke,ContextInvoke,Budget { }
 public record Read(int widthBytes,long addressBits,long lowBits,long highBits) implements Step { }
 public record Write(int widthBytes,long addressBits,long lowBits,long highBits) implements Step { }
 public record GrowthInvoke(PendingSlotCapacityFullState412Api.CallFrame frame,PendingSlotCapacityFullState412Api.CallResult result,List<Write> effects) implements Step { }
 public record ContextInvoke(FullContext493Api.CallFrame frame,FullCopy437Api.CallResult result,List<Write> effects) implements Step { }
 public record Budget(long headerRva,long guardBits) implements Step { }
 public record Scene(String name,GovernmentCrtBoundary185Api.Entry entry,boolean directionFlagSet,List<Cell> initialMemory,List<Step> steps,FullCopy437Api.CallResult expectedResult,List<Cell> finalMemory) { }
 public static final long M=0x3300000000L,E=0x810000000000D008L,RET=0xAABBCCDD11223344L;
 public static final long R=0x8100000000004FF8L,T=0x8100000000005000L,S=0x8100000000010000L,P3=0x810000000000A100L,P4=0x810000000000A200L,P5=0x810000000000A300L,P6=0x810000000000A400L;
 public static final long H=0x8100000000030000L,P=0x8100000000040000L,C=P+0x5C8L,DST=C+0x18L;
 public static final long OLD_BUFFER=0x8100000000001400L,NEW_BUFFER=0x8100000000001200L,ALLOCATOR=0x8100000000006000L,ALLOCATOR2=0x8100000000006100L,VT=0x8100000000007000L,VT2=0x8100000000007100L,ALLOC_TARGET=0x7FFF111122223333L,RELEASE_TARGET=0x7FFF444455556666L;
 public static Bits128 x(long seed) { return new Bits128(seed,~seed); }
 public static VolatileBits v(long seed,long ax,long cx,long dx) { return new VolatileBits(ax,cx,dx,seed+8,seed+9,seed+10,seed+11,x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60)); }
 public static NonvolatileBits n(long bx,long bp,long si,long di,long a12,long a13,long a14,long a15) { return new NonvolatileBits(bx,bp,si,di,a12,a13,a14,a15,x(0x2060)); }
 public static NonvolatileBits n0() { return n(0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008); }
 public static VolatileBits v0() { return new VolatileBits(0x8877665544332211L,R,S,P3,P4,0x100A,0x100B,x(0x1010),x(0x1020),x(0x1030),x(0x1040),x(0x1050),x(0x1060)); }
 public static Cell c(int width,long address,long low) { return new Cell(width,address,low,0); }
 public static Read r(int width,long address,long low) { return new Read(width,address,low,0); }
 public static Write w(int width,long address,long low) { return new Write(width,address,low,0); }
 public static Cell c128(long address,long low,long high) { return new Cell(16,address,low,high); }
 public static Read r128(long address,long low,long high) { return new Read(16,address,low,high); }
 public static Write w128(long address,long low,long high) { return new Write(16,address,low,high); }
 public static FullCopy437Api.CallResult result(VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df) { return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df); }
 public static PendingSlotCapacityFullState412Api.CallResult growResult(VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df) { return new PendingSlotCapacityFullState412Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df); }
 public static FullContext493Api.CallFrame cf(long site,long target,long preSP,VolatileBits v,NonvolatileBits n,boolean df) { return new FullContext493Api.CallFrame(new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,preSP,v,n),new GovernmentCrtBoundary185Api.Entry(M,preSP-8,v,n),df,5,M+site+5); }
 public static PendingSlotCapacityFullState412Api.CallFrame gf(long site,long target,long preSP,VolatileBits v,NonvolatileBits n,boolean df,int length) { return new PendingSlotCapacityFullState412Api.CallFrame(new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,preSP,v,n),new GovernmentCrtBoundary185Api.Entry(M,preSP-8,v,n),df,length,M+site+length); }
}
