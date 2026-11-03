package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner projection of complete held424 normal entry. Three lower outcomes remain explicit.
 * Numeric semantics are reused from605/606/607; only stop instruction addresses are local here. */
public final class Range16FullState638 {
    private Range16FullState638() { }
    /** originCallSiteRva is supplied by the actual caller; it is never inferred from a scalar port. */
    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,Range16Fp638Api.Memory memory,
            Range16Fp638Api.Calls calls,long originCallSiteRva) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var e=input.base().entry();long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean df=input.base().directionFlagSet();QueueFp604Api.Mxcsr fp=input.mxcsr();
        var budget=input.base().budget();
        if(r.r8==r.r9)return finish(image,r,df,fp,memory);
        r.rsp-=8;memory.writeQword(r.rsp,r.rbx);
        r.rsp-=8;memory.writeQword(r.rsp,r.rsi);
        r.rsp-=8;memory.writeQword(r.rsp,r.rdi);
        r.rsp-=8;memory.writeQword(r.rsp,r.r14);
        r.rsp-=0x28;
        r.rax=memory.readDword(r.rcx+0xc);r.rbx=r.r8;
        memory.writeQword(r.rsp+0x50,r.rbp);r.rdi=r.rcx;
        r.rcx=Integer.toUnsignedLong(memory.readDword(r.rcx+8));
        r.rbp=r.r9;r.rbp-=r.rbx;memory.writeQword(r.rsp+0x20,r.r15);
        r.rbp>>=4;r.rsi=r.r9;r.r14=(int)r.rdx;
        r.r15=Integer.toUnsignedLong((int)(r.rax+r.rbp));
        if((int)r.r15<=(int)r.rcx) {
            Range16NoGrowth638.copyAndPrepare(r,memory,budget);
            QueueFp604Api.Outcome offered=call(image,0x8c723fL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x8f8550L,5,r,df,fp,memory,calls);
            if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
            QueueFp604Api.Normal normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        } else {
            r.x0=new Bits128(r.rcx&0xffffffffL,0);r.r8=8;r.rcx=memory.readQword(r.rdi+0x10);
            QueueGrowthCvtdq605.Result cvt=QueueGrowthCvtdq605.execute(image,r,df,fp,originCallSiteRva);
            if(cvt instanceof QueueGrowthCvtdq605.NotCompleted stop)return at(stop.stopped(),0x8c7104L);
            fp=((QueueGrowthCvtdq605.Completed)cvt).mxcsr();
            memory.writeQword(r.rsp+0x58,r.r12);memory.writeQword(r.rsp+0x60,r.r13);r.r13=r.r15;
            QueueGrowthMulss606.Result mul=QueueGrowthMulss606.execute(image,r,df,fp,originCallSiteRva,memory);
            if(mul instanceof QueueGrowthMulss606.NotCompleted stop)return at(stop.stopped(),0x8c7114L);
            fp=((QueueGrowthMulss606.Completed)mul).mxcsr();
            QueueGrowthCvtt607.Result trunc=QueueGrowthCvtt607.execute(image,r,df,fp,originCallSiteRva);
            if(trunc instanceof QueueGrowthCvtt607.NotCompleted stop)return at(stop.stopped(),0x8c711cL);
            fp=((QueueGrowthCvtt607.Completed)trunc).mxcsr();
            if((int)r.r15<(int)r.rax)r.r13=Integer.toUnsignedLong((int)r.rax);
            r.rax=memory.readQword(r.rcx);r.rdx=r.r13&0xffffffffL;r.rdx<<=4;
            long target=memory.readQword(r.rax+8);
            QueueFp604Api.Outcome offered=call(image,0x8c7131L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,3,r,df,fp,memory,calls);
            if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
            QueueFp604Api.Normal normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
            r.rcx=memory.readQword(r.rdi);r.r10=r.r14;r.r10<<=4;r.r12=r.rax;r.rdx=r.rax;r.r8=r.r10+r.rcx;
            if(r.rcx!=r.r8)do {
                budget.beforeStep(0x8c7150L,r.rcx);r.x0=memory.read128(r.rcx);r.rcx+=0x10;r.rdx+=0x10;
                memory.write128(r.rdx-0x10,r.x0);
            } while(r.rcx!=r.r8);
            r.rcx=r.r10;r.rcx-=r.rbx;r.rcx+=r.r12;
            do {
                budget.beforeStep(0x8c7170L,r.rbx);r.x0=memory.read128(r.rbx);memory.write128(r.rcx+r.rbx,r.x0);r.rbx+=0x10;
            } while(r.rbx!=r.rsi);
            r.r9=memory.readQword(r.rdi);r.rdx=memory.readDword(r.rdi+0xc);r.rdx<<=4;
            r.rcx=(int)r.rbp;r.rdx+=r.r9;r.rcx+=r.r14;r.rax=r.r10+r.r9;r.rcx<<=4;r.rcx+=r.r12;
            if(r.rax!=r.rdx) {
                do {
                    budget.beforeStep(0x8c71b0L,r.rax);r.x0=memory.read128(r.rax);r.rax+=0x10;r.rcx+=0x10;
                    memory.write128(r.rcx-0x10,r.x0);
                } while(r.rax!=r.rdx);
                r.r9=memory.readQword(r.rdi);
            }
            r.rcx=memory.readQword(r.rdi+0x10);r.r8=8;r.rdx=r.r9;r.rax=memory.readQword(r.rcx);
            target=memory.readQword(r.rax+0x10);
            offered=call(image,0x8c71d7L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,3,r,df,fp,memory,calls);
            if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
            normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
            memory.writeQword(r.rdi,r.r12);r.r12=memory.readQword(r.rsp+0x58);
            memory.writeDword(r.rdi+8,(int)r.r13);r.r13=memory.readQword(r.rsp+0x60);memory.writeDword(r.rdi+0xc,(int)r.r15);
        }
        r.rbp=memory.readQword(r.rsp+0x50);r.r15=memory.readQword(r.rsp+0x20);r.rsp+=0x28;
        r.r14=memory.readQword(r.rsp);r.rsp+=8;r.rdi=memory.readQword(r.rsp);r.rsp+=8;
        r.rsi=memory.readQword(r.rsp);r.rsp+=8;r.rbx=memory.readQword(r.rsp);r.rsp+=8;
        return finish(image,r,df,fp,memory);
    }
    private static QueueFp604Api.Stopped at(QueueFp604Api.Stopped stop,long pc) {
        QueueFp604Api.Snapshot old=stop.snapshot();
        return new QueueFp604Api.Stopped(stop.reason(),new QueueFp604Api.Snapshot(old.currentState(),pc,old.directionFlagSet(),old.mxcsr()),stop.raisedConditionBits(),stop.originCallSiteRva());
    }
    private static QueueFp604Api.Normal finish(long image,Registers r,boolean df,QueueFp604Api.Mxcsr fp,Range16Fp638Api.Memory memory) {
        long rip=memory.readQword(r.rsp);r.rsp+=8;
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits()),df),fp);
    }
    private static QueueFp604Api.Outcome call(long image,long site,GovernmentCrtBoundary185Api.TargetKind kind,long target,int length,
            Registers r,boolean df,QueueFp604Api.Mxcsr fp,Range16Fp638Api.Memory memory,Range16Fp638Api.Calls calls) {
        long pre=r.rsp,rip=image+site+length;
        var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,r.volatileBits(),r.nonvolatileBits());
        var child=new GovernmentCrtBoundary185Api.Entry(image,pre-8,call.volatileBits(),call.nonvolatileBits());
        var frame=new Range16Fp638Api.CallFrame(call,child,df,fp,length,rip);
        r.rsp=pre-8;memory.writeQword(r.rsp,rip);
        QueueFp604Api.Outcome offered=Objects.requireNonNull(calls.invoke(frame));
        if(offered instanceof QueueFp604Api.Normal normal) {
            frame.checkNormalReturn(normal);r.apply(normal.base().normalReturn().volatileBits());r.rsp=normal.base().normalReturn().callerRspBits();
        }
        return offered;
    }
}
