package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.QueueCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.QueueCalls;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;

/** Owner actual103 normal source with explicit MXCSR/callback stop propagation.
 * A stopped append does not execute the later flag write, unlock or epilogue. */
public final class EmbeddedQueueFpFull609 {
    private EmbeddedQueueFpFull609() { }
    public static Outcome execute(Input input,EmbeddedQueueFp609Api.Memory memory,QueueCalls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var entry=input.base().entry();long image=entry.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
            image,entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        boolean df=input.base().directionFlagSet();Mxcsr state=input.mxcsr();
        r.rsp-=8;memory.writeQword(r.rsp,r.rbx);r.rsp-=0x20;
        int flag=memory.readUnsignedByte(r.rcx+0x4E)&0xFF;r.rbx=r.rcx;
        if(flag==0) {
            Outcome returned=call(image,r,df,state,memory,calls,0x3727ECF,0x3727580);
            if(returned instanceof Stopped)return returned;
            Normal normal=(Normal)returned;df=normal.base().postDirectionFlagSet();state=normal.postMxcsr();
            int id=memory.readDword(r.rbx+0x48);
            r.rdx=(r.rdx&~0xFFL)|(id==-1?0L:1L);
            if((r.rdx&0xFFL)!=(r.rax&0xFFL)) {
                r.rcx=1;long lock=image+0x5C9FF68L;
                EmbeddedQueueLock591.acquire(r,memory,input.base().budget(),lock);
                r.rdx=r.rsp+0x38;memory.writeQword(r.rdx,r.rbx);
                r.rcx=image+0x5468A68L;
                returned=call(image,r,df,state,memory,calls,0x3727F0D,0x880340);
                if(returned instanceof Stopped)return returned;
                normal=(Normal)returned;df=normal.base().postDirectionFlagSet();state=normal.postMxcsr();
                memory.writeByte(r.rbx+0x4E,1);memory.writeDword(lock,0);
            }
        }
        r.rsp+=0x20;r.rbx=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);
        return new Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),rip,r.rsp+8,r.nonvolatileBits()),df),state);
    }
    private static Outcome call(long image,Registers r,boolean df,Mxcsr state,
            EmbeddedQueueFp609Api.Memory memory,QueueCalls calls,long site,long target) {
        long rip=image+site+5;
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            target,r.rsp,r.volatileBits(),r.nonvolatileBits());
        var child=new GovernmentCrtBoundary185Api.Entry(image,r.rsp-8,call.volatileBits(),call.nonvolatileBits());
        var frame=new QueueCallFrame(new EmbeddedQueue591Api.CallFrame(call,child,df,5,rip),state);
        r.rsp-=8;memory.writeQword(r.rsp,rip);
        Outcome returned=Objects.requireNonNull(calls.invoke(frame));
        if(returned instanceof Normal normal) {
            frame.checkNormalReturn(normal);r.apply(normal.base().normalReturn().volatileBits());
            r.rsp=normal.base().normalReturn().callerRspBits();
        }
        return returned;
    }
}
