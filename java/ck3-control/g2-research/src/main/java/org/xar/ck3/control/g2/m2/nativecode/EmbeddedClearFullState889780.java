package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Held93 normal source; virtual lower call stays opaque. No Native/EH qualification. */
public final class EmbeddedClearFullState889780 {
    private EmbeddedClearFullState889780() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory, EmbeddedClear587Api.Calls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        GovernmentCrtBoundary185Api.Entry e=input.entry();
        long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
            image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean df=input.directionFlagSet();
        memory.writeQword(r.rsp+0x10,r.rsi);
        r.rsp-=8;memory.writeQword(r.rsp,r.rdi);
        r.rsp-=0x20;
        r.rdi=Integer.toUnsignedLong(memory.readDword(r.rcx+0xC));
        r.rsi=r.rcx;
        if((int)r.rdi<=0) return EmbeddedClearNonPositive587.finish(r,df,memory);
        memory.writeQword(r.rsp+0x30,r.rbx);
        r.rbx=memory.readQword(r.rcx);
        do {
            // Finite software projection, before the first Memory operation at the source header.
            input.budget().beforeStep(0x8897A0L,r.rbx);
            r.rax=memory.readQword(r.rbx);
            r.rdx=0;
            r.rcx=r.rbx;
            long target=memory.readQword(r.rax);
            long rip=image+0x8897AAL;
            memory.writeQword(r.rsp-8,rip);
            GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(
                0x8897A8L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                target,r.rsp,r.volatileBits(),r.nonvolatileBits());
            EmbeddedClear587Api.CallFrame frame=new EmbeddedClear587Api.CallFrame(call,
                new GovernmentCrtBoundary185Api.Entry(image,r.rsp-8,call.volatileBits(),call.nonvolatileBits()),
                df,2,rip);
            FullCopy437Api.CallResult actual=calls.invoke(frame);
            frame.checkNormalReturn(actual);
            r.apply(actual.normalReturn().volatileBits());
            df=actual.postDirectionFlagSet();
            r.rdi=Integer.toUnsignedLong((int)r.rdi-1);
            r.rbx+=0x48;
        } while((int)r.rdi>0);
        r.rbx=memory.readQword(r.rsp+0x30);
        memory.writeDword(r.rsi+0xC,0);
        r.rsi=memory.readQword(r.rsp+0x38);
        r.rsp+=0x20;
        r.rdi=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);r.rsp+=8;
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),rip,r.rsp,r.nonvolatileBits()),df);
    }
}
