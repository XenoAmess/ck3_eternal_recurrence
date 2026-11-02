package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Exact represented normal231B: real292 child, opaque normal/tail merge ports, no flags/EH claim. */
public final class BridgeFullState293 {
    private BridgeFullState293() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+0x18L,r.r8);
        memory.writeQword(r.rsp+8L,r.rcx);
        push(r,memory,r.rbx);push(r,memory,r.rbp);push(r,memory,r.rsi);
        push(r,memory,r.r12);push(r,memory,r.r13);r.rsp-=0x40L;
        r.r13=memory.readQword(r.rsp+0xA0L);
        r.rax=r.r9;r.rax-=memory.readQword(r.rsp+0xC0L);
        r.r12=memory.readQword(r.rsp+0x98L);r.r9=r.rax;
        r.rbp=memory.readQword(r.rsp+0xC8L);
        r.r8=memory.readQword(r.rsp+0xB8L);r.rcx=memory.readQword(r.rsp+0xB0L);
        memory.writeQword(r.rsp+0x30L,r.r13);
        memory.writeQword(r.rsp+0x28L,r.r12);
        memory.writeQword(r.rsp+0x88L,r.rax);
        memory.writeQword(r.rsp+0x20L,r.rbp);
        BridgeRotateCall293.invoke(entry.imageBaseBits(),r,memory,calls,budget);

        r.rbx=Integer.toUnsignedLong(memory.readUnsignedByte(r.rsp+0xA8L));
        r.r8=r.rax;r.r9=memory.readQword(r.rsp+0xC0L);r.rsi=r.rax;
        r.rdx=memory.readQword(r.rsp+0xB0L);r.rcx=memory.readQword(r.rsp+0x70L);
        memory.writeByte(r.rsp+0x38L,(int)r.rbx);
        memory.writeQword(r.rsp+0x30L,r.r13);
        memory.writeQword(r.rsp+0x28L,r.r12);
        memory.writeQword(r.rsp+0x20L,r.rbp);
        memory.writeQword(r.rsp-8L,entry.imageBaseBits()+0x1A83362L);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(0x1A8335DL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x1A81AB0L,
                r.rsp,r.volatileBits(),r.nonvolatileBits())));

        r.rcx=memory.readQword(r.rsp+0x90L);r.r9=memory.readQword(r.rsp+0x88L);
        r.rcx-=r.rbp;r.r8=memory.readQword(r.rsp+0x80L);
        r.rdx=memory.readQword(r.rsp+0xB8L);
        memory.writeByte(r.rsp+0xA8L,(int)r.rbx);
        memory.writeQword(r.rsp+0x90L,r.rcx);
        r.rcx=r.rsi;r.rsp+=0x40L;
        r.r13=pop(r,memory);r.r12=pop(r,memory);r.rsi=pop(r,memory);
        r.rbp=pop(r,memory);r.rbx=pop(r,memory);
        return calls.tail(new GovernmentCrtBoundary185Api.Tail(0x1A833A2L,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x1A81AB0L,
                new GovernmentCrtBoundary185Api.Entry(entry.imageBaseBits(),r.rsp,
                        r.volatileBits(),r.nonvolatileBits())));
    }

    private static void push(Registers r,GovernmentCrtBoundary185Api.Memory m,long bits) {
        r.rsp-=8L;m.writeQword(r.rsp,bits);
    }
    private static long pop(Registers r,GovernmentCrtBoundary185Api.Memory m) {
        long bits=m.readQword(r.rsp);r.rsp+=8L;return bits;
    }
}
