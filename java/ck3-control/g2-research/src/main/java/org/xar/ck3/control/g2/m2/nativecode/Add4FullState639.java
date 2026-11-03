package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner normal351 state orchestration. All seven lower outcomes remain explicit. */
public final class Add4FullState639 {
    private Add4FullState639() { }
    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,Add4Fp639Api.Memory memory,
            Add4Fp639Api.Calls calls,long originCallSiteRva) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var e=input.base().entry();long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean df=input.base().directionFlagSet();QueueFp604Api.Mxcsr fp=input.mxcsr();
        if(r.r8==r.r9)return ret(r,df,fp,memory);
        r.rsp-=8;memory.writeQword(r.rsp,r.rbx);r.rsp-=8;memory.writeQword(r.rsp,r.r13);
        r.rsp-=8;memory.writeQword(r.rsp,r.r14);r.rsp-=8;memory.writeQword(r.rsp,r.r15);r.rsp-=0x28;
        r.rax=memory.readDword(r.rcx+0xc);r.r14=r.rcx;memory.writeQword(r.rsp+0x20,r.r12);
        r.r15=r.r9;r.r15-=r.r8;r.rbx=(int)r.rdx;r.r12=r.r15;r.r13=r.r8;
        r.rdx=Integer.toUnsignedLong(memory.readDword(r.r14+8));r.r12>>=2;
        r.rcx=Integer.toUnsignedLong((int)(r.rax+r.r12));memory.writeDword(r.rsp+0x50,(int)r.rcx);
        if((int)r.rcx<=(int)r.rdx) {
            r.rcx=r.rax;r.r8=r.r15;r.rax=memory.readQword(r.r14);r.rdx=r.r13;r.rcx=r.rax+r.rcx*4;
            QueueFp604Api.Outcome offered=call(image,0xadd1f7,0x4226860,5,r,df,fp,memory,calls);
            if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
            QueueFp604Api.Normal normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
            r.rcx=memory.readDword(r.r14+0xc);r.r9=memory.readQword(r.r14);
            r.rax=Integer.toUnsignedLong((int)(r.rcx+r.r12));memory.writeDword(r.r14+0xc,(int)r.rax);
            r.rdx=r.r9+r.rcx*4;r.rax=(int)r.rax;r.rcx=r.r9+r.rbx*4;r.r8=r.r9+r.rax*4;
            offered=call(image,0xadd219,0x9d0950,5,r,df,fp,memory,calls);
            if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
            normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
            r.r12=memory.readQword(r.rsp+0x20);r.rsp+=0x28;
            r.r15=memory.readQword(r.rsp);r.rsp+=8;r.r14=memory.readQword(r.rsp);r.rsp+=8;
            r.r13=memory.readQword(r.rsp);r.rsp+=8;r.rbx=memory.readQword(r.rsp);r.rsp+=8;
            return ret(r,df,fp,memory);
        }
        r.x0=new Bits128(r.rdx&0xffffffffL,0);r.r8=4;memory.writeQword(r.rsp+0x58,r.rbp);r.rbp=r.rcx&0xffffffffL;
        QueueGrowthCvtdq605.Result cvt=QueueGrowthCvtdq605.execute(image,r,df,fp,originCallSiteRva);
        if(cvt instanceof QueueGrowthCvtdq605.NotCompleted stop)return at(stop.stopped(),0xadd128);
        fp=((QueueGrowthCvtdq605.Completed)cvt).mxcsr();
        memory.writeQword(r.rsp+0x60,r.rsi);memory.writeQword(r.rsp+0x68,r.rdi);
        QueueGrowthMulss606.Result mul=QueueGrowthMulss606.execute(image,r,df,fp,originCallSiteRva,memory);
        if(mul instanceof QueueGrowthMulss606.NotCompleted stop)return at(stop.stopped(),0xadd135);
        fp=((QueueGrowthMulss606.Completed)mul).mxcsr();
        QueueGrowthCvtt607.Result trunc=QueueGrowthCvtt607.execute(image,r,df,fp,originCallSiteRva);
        if(trunc instanceof QueueGrowthCvtt607.NotCompleted stop)return at(stop.stopped(),0xadd13d);
        fp=((QueueGrowthCvtt607.Completed)trunc).mxcsr();
        // CMP flags survive the following MOV RCX; capture comparison before that register is overwritten.
        boolean chooseConverted=(int)r.rcx<(int)r.rax;r.rcx=memory.readQword(r.r14+0x10);
        if(chooseConverted)r.rbp=Integer.toUnsignedLong((int)r.rax);
        r.rdx=r.rbp&0xffffffffL;r.rax=memory.readQword(r.rcx);r.rdx<<=2;
        long target=memory.readQword(r.rax+8);
        QueueFp604Api.Outcome offered=call(image,0xadd153,target,3,r,df,fp,memory,calls);
        if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
        QueueFp604Api.Normal normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        r.rdx=memory.readQword(r.r14);r.rdi=r.rbx;r.rbx*=4;r.rcx=r.rax;r.r8=r.rbx;r.rsi=r.rax;
        offered=call(image,0xadd16d,0x4226860,5,r,df,fp,memory,calls);
        if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
        normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        r.rcx=r.rbx+r.rsi;r.r8=r.r15;r.rdx=r.r13;
        offered=call(image,0xadd17c,0x4226860,5,r,df,fp,memory,calls);
        if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
        normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        r.rax=memory.readQword(r.r14);r.r8=memory.readDword(r.r14+0xc);r.r8<<=2;
        r.rdx=r.rbx+r.rax;r.r8-=r.rdx;r.r8+=r.rax;r.rax=(int)r.r12;r.rax+=r.rdi;r.rcx=r.rsi+r.rax*4;
        offered=call(image,0xadd1a0,0x4226860,5,r,df,fp,memory,calls);
        if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
        normal=(QueueFp604Api.Normal)offered;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        r.rcx=memory.readQword(r.r14+0x10);r.r8=4;r.rdx=memory.readQword(r.r14);r.rax=memory.readQword(r.rcx);
        target=memory.readQword(r.rax+0x10);
        offered=call(image,0xadd1b5,target,3,r,df,fp,memory,calls);
        if(offered instanceof QueueFp604Api.Stopped stopped)return stopped;
        normal=(QueueFp604Api.Normal)offered;
        return Add4GrowthCommit639.finish(r,memory,normal.base().postDirectionFlagSet(),normal.postMxcsr());
    }
    private static QueueFp604Api.Stopped at(QueueFp604Api.Stopped stop,long pc) {
        var old=stop.snapshot();return new QueueFp604Api.Stopped(stop.reason(),new QueueFp604Api.Snapshot(old.currentState(),pc,old.directionFlagSet(),old.mxcsr()),stop.raisedConditionBits(),stop.originCallSiteRva());
    }
    private static QueueFp604Api.Normal ret(Registers r,boolean df,QueueFp604Api.Mxcsr fp,Add4Fp639Api.Memory memory) {
        long rip=memory.readQword(r.rsp);r.rsp+=8;
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits()),df),fp);
    }
    private static QueueFp604Api.Outcome call(long image,long site,long target,int length,Registers r,boolean df,QueueFp604Api.Mxcsr fp,Add4Fp639Api.Memory memory,Add4Fp639Api.Calls calls) {
        var kind=length==3?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        long pre=r.rsp,rip=image+site+length;
        var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,r.volatileBits(),r.nonvolatileBits());
        var child=new GovernmentCrtBoundary185Api.Entry(image,pre-8,call.volatileBits(),call.nonvolatileBits());
        var frame=new Add4Fp639Api.CallFrame(call,child,df,fp,length,rip);
        r.rsp=pre-8;memory.writeQword(r.rsp,rip);
        QueueFp604Api.Outcome offered=Objects.requireNonNull(calls.invoke(frame));
        if(offered instanceof QueueFp604Api.Normal normal) { frame.checkNormalReturn(normal);r.apply(normal.base().normalReturn().volatileBits());r.rsp=normal.base().normalReturn().callerRspBits(); }
        return offered;
    }
}
