package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Shape and constructor-only recipe mechanics. No Scene, expected literal, Host or subject body. */
public final class PendingPageFullData519 {
    private PendingPageFullData519() { }
    /** Width1/4 unsigned scalar, width8 arbitrary raw64. */
    public record Cell(int widthBytes, long addressBits, long valueBits) { }
    public sealed interface Step permits Read, Write, Invoke, Budget { }
    public record Read(int widthBytes, long addressBits, long valueBits) implements Step { }
    public record Write(int widthBytes, long addressBits, long valueBits) implements Step { }
    public record Invoke(FullPage495Api.CallFrame frame,
            FullCopy437Api.CallResult result, List<Write> effects) implements Step { }
    public record Budget(long headerRva, long guardAddressBits, boolean stop) implements Step { }
    public record Scene(String name, GovernmentCrtBoundary185Api.Entry entry,
            boolean directionFlagSet, List<Cell> initialMemory, List<Step> steps,
            FullCopy437Api.CallResult expectedResult, boolean expectedBudgetStop,
            List<Cell> finalMemory) { }

    public static Bits128 x(long seed) { return new Bits128(seed, ~seed); }
    /** Explicit recipe poison pattern, no source state or fixed Scene seed. */
    public static VolatileBits v(long seed, long ax, long cx, long dx) {
        return new VolatileBits(ax,cx,dx,seed+8,seed+9,seed+0xA,seed+0xB,
                x(seed+0x10),x(seed+0x20),x(seed+0x30),x(seed+0x40),x(seed+0x50),x(seed+0x60));
    }
    public static NonvolatileBits n(long bx,long bp,long si,long di,long r12,long r13,long r14,long r15,Bits128 x6) {
        return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,x6);
    }
    public static Cell c(int width,long address,long bits) { return new Cell(width,address,bits); }
    public static Read r(int width,long address,long bits) { return new Read(width,address,bits); }
    public static Write w(int width,long address,long bits) { return new Write(width,address,bits); }
    public static Budget b(long header,long guard,boolean stop) { return new Budget(header,guard,stop); }
    /** All supplied381 CALLs are direct5; values remain independent Book arguments. */
    public static FullPage495Api.CallFrame f(long image,long site,long target,long preSp,VolatileBits v,NonvolatileBits n,boolean df) {
        return new FullPage495Api.CallFrame(new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,preSp,v,n),
                new GovernmentCrtBoundary185Api.Entry(image,preSp-8,v,n),df,5,image+site+5);
    }
    public static FullCopy437Api.CallResult result(VolatileBits v,long rip,long sp,NonvolatileBits n,boolean df) {
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df);
    }
    public static Invoke i(FullPage495Api.CallFrame frame,FullCopy437Api.CallResult result,List<Write> effects) {
        return new Invoke(frame,result,effects);
    }
}
