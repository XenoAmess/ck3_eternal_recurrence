package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/**
 * Exact translation of the 193-byte normal callee at 2D0B490.
 * Entry.frameRspBits is the actual callee-entry RSP (S), with the return address already pushed.
 * Internal opaque calls use the existing Tail155 Calls/OpaqueCall boundary.
 */
public final class GovernmentCallee164 {

    private GovernmentCallee164() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls calls) {
        Registers r = GovernmentCallee164Api.registers(entry);
        long image = entry.imageBaseBits();
        long S = entry.frameRspBits();

        memory.writeQword(S + 0x10L, r.rsi);

        long rsp1 = S - 8L;
        memory.writeQword(rsp1, r.rdi);

        long W = rsp1 - 0x20L;
        r.rsp = W;

        int byteVal = memory.readUnsignedByte(r.rcx + 0x0CL);
        r.rax = Integer.toUnsignedLong(byteVal);

        r.rsi = r.rdx;

        r.rdi = r.rcx;

        boolean cmpEqual = (byteVal == 2);

        if (!cmpEqual) {

            return executeBranch2D0B4B5(r, memory, calls, image, W, S);
        }

        r.rax = 0L;

        r.rsi = memory.readQword(W + 0x38L);

        long rsp2 = W + 0x20L;

        r.rdi = memory.readQword(rsp2);
        long rsp3 = rsp2 + 8L;
        r.rsp = rsp3;

        return finishReturn(r, memory, S);
    }

    private static NormalReturn executeBranch2D0B4B5(Registers r, Memory memory, Calls calls, long image, long W, long S) {

        memory.writeQword(W + 0x30L, r.rbx);

        boolean testZero = (r.rax & 0xFFL) == 0L;

        if (testZero) {
            return executeBranch2D0B52E(r, memory, calls, image, W, S);
        }

        int ebxVal = memory.readDword(r.rcx + 0x08L);
        r.rbx = Integer.toUnsignedLong(ebxVal);

        long siteRsp = W;
        VolatileBits vBefore = r.volatileBits();
        NonvolatileBits nBefore = r.nonvolatileBits();
        OpaqueCall call1 = new OpaqueCall(0x2D0B4C1L, 0x3F8A7E0L, siteRsp, vBefore, nBefore);
        VolatileBits vAfter1 = calls.invoke(call1);
        r.apply(vAfter1);

        r.rdx = r.rbx;

        r.rcx = r.rax;

        VolatileBits vBefore2 = r.volatileBits();
        NonvolatileBits nBefore2 = r.nonvolatileBits();
        OpaqueCall call2 = new OpaqueCall(0x2D0B4CBL, 0x3F8A6D0L, siteRsp, vBefore2, nBefore2);
        VolatileBits vAfter2 = calls.invoke(call2);
        r.apply(vAfter2);

        long val10 = memory.readQword(r.rax + 0x10L);
        boolean cmpZero = (val10 == 0L);

        if (cmpZero) {
            return executeBranch2D0B52E(r, memory, calls, image, W, S);
        }

        int ebxVal2 = memory.readDword(r.rdi + 0x08L);
        r.rbx = Integer.toUnsignedLong(ebxVal2);

        memory.writeByte(r.rdi + 0x0CL, 2);

        VolatileBits vBefore3 = r.volatileBits();
        NonvolatileBits nBefore3 = r.nonvolatileBits();
        OpaqueCall call3 = new OpaqueCall(0x2D0B4DEL, 0x3F8A7E0L, siteRsp, vBefore3, nBefore3);
        VolatileBits vAfter3 = calls.invoke(call3);
        r.apply(vAfter3);

        r.rdx = r.rbx;

        r.rcx = r.rax;

        VolatileBits vBefore4 = r.volatileBits();
        NonvolatileBits nBefore4 = r.nonvolatileBits();
        OpaqueCall call4 = new OpaqueCall(0x2D0B4E8L, 0x3F8A6D0L, siteRsp, vBefore4, nBefore4);
        VolatileBits vAfter4 = calls.invoke(call4);
        r.apply(vAfter4);

        long val18 = memory.readQword(r.rax + 0x18L);

        boolean jbTaken = (Long.compareUnsigned(val18, 0x10L) < 0);

        int r8dVal = memory.readDword(r.rax + 0x10L);
        r.r8 = Integer.toUnsignedLong(r8dVal);

        if (jbTaken) {

            r.rdx = r.rax;
        } else {

            r.rax = memory.readQword(r.rax);

            r.rdx = r.rax;
        }

        VolatileBits vBefore5 = r.volatileBits();
        NonvolatileBits nBefore5 = r.nonvolatileBits();
        OpaqueCall call5 = new OpaqueCall(0x2D0B4FEL, 0x3F7E220L, siteRsp, vBefore5, nBefore5);
        VolatileBits vAfter5 = calls.invoke(call5);
        r.apply(vAfter5);

        r.rdx = Integer.toUnsignedLong((int)r.rax);

        r.rcx = r.rsi;

        VolatileBits vBefore6 = r.volatileBits();
        NonvolatileBits nBefore6 = r.nonvolatileBits();
        OpaqueCall call6 = new OpaqueCall(0x2D0B508L, 0x16F40A0L, siteRsp, vBefore6, nBefore6);
        VolatileBits vAfter6 = calls.invoke(call6);
        r.apply(vAfter6);

        r.rbx = memory.readQword(W + 0x30L);

        r.rcx = 0L;

        memory.writeQword(r.rdi, r.rax);

        int cmpVal = memory.readDword(r.rax + 0x38L);
        boolean setne = (cmpVal != 0x4744624F);

        r.rcx = setne ? 1L : 0L;

        r.rax = r.rcx;

        r.rsi = memory.readQword(W + 0x38L);

        long rsp4 = W + 0x20L;

        r.rdi = memory.readQword(rsp4);
        long rsp5 = rsp4 + 8L;
        r.rsp = rsp5;

        return finishReturn(r, memory, S);
    }

    private static NormalReturn executeBranch2D0B52E(Registers r, Memory memory, Calls calls, long image, long W, long S) {

        r.rbx = memory.readQword(W + 0x30L);

        r.rsi = memory.readQword(W + 0x38L);

        memory.writeByte(r.rdi + 0x0CL, 2);

        r.rax = memory.readQword(image + 0x5D213E8L);

        memory.writeQword(r.rdi, r.rax);

        r.rax = 2L;

        long rsp6 = W + 0x20L;

        r.rdi = memory.readQword(rsp6);
        long rsp7 = rsp6 + 8L;
        r.rsp = rsp7;

        return finishReturn(r, memory, S);
    }
    private static NormalReturn finishReturn(Registers r, Memory memory, long s) {
        long rip = memory.readQword(s);
        r.rsp = s + 8L;
        return new NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, r.rsp);
    }

}
