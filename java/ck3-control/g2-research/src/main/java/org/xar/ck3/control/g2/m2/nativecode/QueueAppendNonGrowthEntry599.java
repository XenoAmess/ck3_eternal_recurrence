package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

/** Owner raw-entry original227 NON-GROWTH branch only. Growth explicitly unsupported;
 * no default FP/control state, whole227/all-machine-state or591 binding claim. */
public final class QueueAppendNonGrowthEntry599 {
    private QueueAppendNonGrowthEntry599() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            QueueAppend597Api.Memory memory) {
        Objects.requireNonNull(input); Objects.requireNonNull(memory);
        var e=input.entry();
        var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                e.imageBaseBits(),e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        memory.writeQword(r.rsp+0x10,r.rbx);
        memory.writeQword(r.rsp+0x18,r.rsi);
        memory.writeQword(r.rsp+0x20,r.rdi);
        r.rsp-=8; memory.writeQword(r.rsp,r.r14);
        r.rsp-=0x20;
        r.rax=memory.readDword(r.rcx+0xC);
        r.rbx=r.rcx;
        r.rcx=Integer.toUnsignedLong(memory.readDword(r.rcx+8));
        r.r14=r.rdx;
        if((int)r.rax==(int)r.rcx)
            throw new UnsupportedOperationException("growth FP input not represented");
        QueueAppendNonGrowthBlock597.append(r,memory);
        return QueueAppendEpilogue599.finish(r,memory,input.directionFlagSet());
    }
}
