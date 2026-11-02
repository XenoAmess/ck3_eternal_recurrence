package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCalls;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;

/** Owner complete held normal227 with explicit partial MXCSR and three opaque FP-aware
 * callbacks. No CPU/OS capture, general RFLAGS, callee algorithm or implicit FP defaults. */
public final class QueueAppendPartialFpWhole611 {
    private QueueAppendPartialFpWhole611() { }

    public static Outcome execute(Input input,QueueAppend597Api.Memory memory,
            AppendCalls calls,long originCallSiteRva) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var entry=input.base().entry();long image=entry.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
            image,entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        boolean df=input.base().directionFlagSet();Mxcsr state=input.mxcsr();
        memory.writeQword(r.rsp+0x10,r.rbx);
        memory.writeQword(r.rsp+0x18,r.rsi);
        memory.writeQword(r.rsp+0x20,r.rdi);
        r.rsp-=8;memory.writeQword(r.rsp,r.r14);r.rsp-=0x20;
        r.rax=memory.readDword(r.rcx+0xC); // actual MOVSXD, not MOV EAX
        r.rbx=r.rcx;
        r.rcx=Integer.toUnsignedLong(memory.readDword(r.rcx+8));
        r.r14=r.rdx;
        if((int)r.rax!=(int)r.rcx) {
            QueueAppendNonGrowthBlock597.append(r,memory);
            return new Normal(QueueAppendEpilogue599.finish(r,memory,df),state);
        }
        QueueAppendGrowthPreFp602.prepare(r,memory);
        var cvt=QueueGrowthCvtdq605.execute(image,r,df,state,originCallSiteRva);
        if(cvt instanceof QueueGrowthCvtdq605.NotCompleted stopped) return stopped.stopped();
        state=((QueueGrowthCvtdq605.Completed)cvt).mxcsr();
        memory.writeQword(r.rsp+0x30,r.rbp); // only reached after CVT completed
        r.rbp=Integer.toUnsignedLong((int)r.rsi);
        var mul=(state.knownMaskBits()&0xFFC0)==0xFFC0
            ?QueueGrowthMulss606.execute(image,r,df,state,originCallSiteRva,memory)
            :QueueGrowthPartialMulss611.execute(image,r,df,state,originCallSiteRva,memory);
        if(mul instanceof QueueGrowthMulss606.NotCompleted stopped) return stopped.stopped();
        state=((QueueGrowthMulss606.Completed)mul).mxcsr();
        var cvtt=QueueGrowthCvtt607.execute(image,r,df,state,originCallSiteRva);
        if(cvtt instanceof QueueGrowthCvtt607.NotCompleted stopped) return stopped.stopped();
        state=((QueueGrowthCvtt607.Completed)cvtt).mxcsr();
        long target=QueueGrowthAllocateSetup608.prepare(r,memory);
        Outcome returned=call(image,r,df,state,memory,calls,0x88039F,
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,3,0x8803A2);
        if(returned instanceof Stopped) return returned;
        Normal normal=(Normal)returned;df=normal.base().postDirectionFlagSet();state=normal.postMxcsr();
        if(QueueAppendGrowthStore598.prepare(r,memory)) {
            r.rdx=memory.readQword(r.rbx);r.r8=r.rax<<3;r.rcx=r.rdi;
            returned=call(image,r,df,state,memory,calls,0x8803C5,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226860,5,0x8803CA);
            if(returned instanceof Stopped) return returned;
            normal=(Normal)returned;df=normal.base().postDirectionFlagSet();state=normal.postMxcsr();
        }
        r.rcx=memory.readQword(r.rbx+0x10);r.r8=8;
        r.rdx=memory.readQword(r.rbx);r.rax=memory.readQword(r.rcx);
        target=memory.readQword(r.rax+0x10);
        returned=call(image,r,df,state,memory,calls,0x8803DA,
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,3,0x8803DD);
        if(returned instanceof Stopped) return returned;
        normal=(Normal)returned;df=normal.base().postDirectionFlagSet();state=normal.postMxcsr();
        memory.writeDword(r.rbx+8,(int)r.rbp);
        r.rbp=memory.readQword(r.rsp+0x30);
        memory.writeQword(r.rbx,r.rdi);memory.writeDword(r.rbx+0xC,(int)r.rsi);
        return new Normal(QueueAppendEpilogue599.finish(r,memory,df),state);
    }

    private static Outcome call(long image,Registers r,boolean df,Mxcsr state,
            QueueAppend597Api.Memory memory,AppendCalls calls,long site,
            GovernmentCrtBoundary185Api.TargetKind kind,long target,int length,long returnRva) {
        long rip=image+returnRva;
        var offered=new GovernmentCrtBoundary185Api.Call(site,kind,target,
            r.rsp,r.volatileBits(),r.nonvolatileBits());
        var child=new GovernmentCrtBoundary185Api.Entry(image,r.rsp-8,
            offered.volatileBits(),offered.nonvolatileBits());
        var base=new QueueAppend597Api.CallFrame(offered,child,df,length,rip);
        var frame=new AppendCallFrame(base,state);
        r.rsp-=8;memory.writeQword(r.rsp,rip); // one actual CALL push
        Outcome returned=Objects.requireNonNull(calls.invoke(frame));
        if(returned instanceof Normal normal) {
            frame.checkNormalReturn(normal); // before apply, no state repair or FP equality invented
            r.apply(normal.base().normalReturn().volatileBits());
            r.rsp=normal.base().normalReturn().callerRspBits();
        }
        // A child stop has its own current state; do not fake an outer unwind or normal return.
        return returned;
    }
}
