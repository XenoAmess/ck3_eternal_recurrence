package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

public final class SmallRowBlocks295 {
    private SmallRowBlocks295() { }

    public static void capture(Registers r, GovernmentCrtBoundary185Api.Memory memory) {
        // 0x1A81210: movups xmm2, xmmword ptr [rbx]
        r.x2 = memory.read128(r.rbx);
        // 0x1A81213: mov r8, rbx
        r.r8 = r.rbx;
        // 0x1A81216: movups xmm3, xmmword ptr [rbx + 0x10]
        r.x3 = memory.read128(r.rbx + 0x10L);
        // 0x1A8121A: movsd xmm4, qword ptr [rbx + 0x20]
        long qword = memory.readQword(r.rbx + 0x20L);
        r.x4 = new Bits128(qword, 0L);
        // 0x1A8121F: movd ecx, xmm2
        r.rcx = Integer.toUnsignedLong((int)r.x2.lowBits());
        // 0x1A81223: movups xmmword ptr [rsp + 0x20], xmm2
        memory.write128(r.rsp + 0x20L, r.x2);
        // 0x1A81228: movups xmmword ptr [rsp + 0x30], xmm3
        memory.write128(r.rsp + 0x30L, r.x3);
        // 0x1A8122D: movsd qword ptr [rsp + 0x50], xmm4
        memory.writeQword(r.rsp + 0x50L, r.x4.lowBits());
    }

    public static void restoreFront(Registers r, GovernmentCrtBoundary185Api.Memory memory) {
        // 0x1A8124C: movups xmm0, xmmword ptr [rsp + 0x20]
        r.x0 = memory.read128(r.rsp + 0x20L);
        // 0x1A81251: movups xmm1, xmmword ptr [rsp + 0x30]
        r.x1 = memory.read128(r.rsp + 0x30L);
        // 0x1A81256: movups xmmword ptr [rsi], xmm0
        memory.write128(r.rsi, r.x0);
        // 0x1A81259: movsd xmm0, qword ptr [rsp + 0x50]
        long qword = memory.readQword(r.rsp + 0x50L);
        r.x0 = new Bits128(qword, 0L);
        // 0x1A8125F: movups xmmword ptr [rsi + 0x10], xmm1
        memory.write128(r.rsi + 0x10L, r.x1);
        // 0x1A81263: movsd qword ptr [rsi + 0x20], xmm0
        memory.writeQword(r.rsi + 0x20L, r.x0.lowBits());
    }
}