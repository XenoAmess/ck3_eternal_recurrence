package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner orchestration of the complete held103 normal path; two lower calls are opaque. */
public final class EmbeddedQueueFullState3727EC0 {
    private EmbeddedQueueFullState3727EC0() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            EmbeddedQueue591Api.Memory memory,EmbeddedQueue591Api.Calls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var e=input.entry();long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
            image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean df=input.directionFlagSet();
        r.rsp-=8;memory.writeQword(r.rsp,r.rbx);r.rsp-=0x20;
        int flag=memory.readUnsignedByte(r.rcx+0x4E)&0xFF;
        r.rbx=r.rcx;
        if(flag==0) {
            df=call(image,0x3727ECFL,0x3727580L,r,df,memory,calls);
            int id=memory.readDword(r.rbx+0x48);
            r.rdx=(r.rdx&~0xFFL)|(id==-1?0L:1L);
            if((r.rdx&0xFFL)!=(r.rax&0xFFL)) {
                r.rcx=1;
                long lock=image+0x5C9FF68L;
                EmbeddedQueueLock591.acquire(r,memory,input.budget(),lock);
                r.rdx=r.rsp+0x38;
                memory.writeQword(r.rdx,r.rbx);
                r.rcx=image+0x5468A68L;
                df=call(image,0x3727F0DL,0x880340L,r,df,memory,calls);
                memory.writeByte(r.rbx+0x4E,1);
                memory.writeDword(lock,0);
            }
        }
        r.rsp+=0x20;r.rbx=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),rip,r.rsp+8,r.nonvolatileBits()),df);
    }
    private static boolean call(long image,long site,long target,Registers r,boolean df,
            EmbeddedQueue591Api.Memory memory,EmbeddedQueue591Api.Calls calls) {
        long rip=image+site+5;memory.writeQword(r.rsp-8,rip);
        var c=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            target,r.rsp,r.volatileBits(),r.nonvolatileBits());
        var frame=new EmbeddedQueue591Api.CallFrame(c,new GovernmentCrtBoundary185Api.Entry(
            image,r.rsp-8,c.volatileBits(),c.nonvolatileBits()),df,5,rip);
        FullCopy437Api.CallResult actual=calls.invoke(frame);frame.checkNormalReturn(actual);
        r.apply(actual.normalReturn().volatileBits());return actual.postDirectionFlagSet();
    }
}
