package org.xar.ck3.research.m3.range9d260;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Complete held normal 126-byte protocol; the three lower outcomes remain explicit. */
public final class Range9DFullState260 {
    private Range9DFullState260() { }
    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            Range9DFp260Api.Memory memory,Range9DFp260Api.Calls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var entry=input.base().entry();long image=entry.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        boolean df=input.base().directionFlagSet();QueueFp604Api.Mxcsr fp=input.mxcsr();
        memory.writeQword(r.rsp+8,r.rbx);memory.writeQword(r.rsp+0x10,r.rsi);
        r.rsp-=8;memory.writeQword(r.rsp,r.rdi);r.rsp-=0x20;
        r.rbx=r.r8;r.rsi=r.rdx;r.rdi=r.rcx;
        if(r.rcx==r.rdx) {r.rax=r.rbx;return early(r,memory,df,fp);}
        if(r.rsi==r.rbx) {r.rax=r.rdi;return early(r,memory,df,fp);}
        QueueFp604Api.Outcome outcome=call(image,0x9D0998L,r,memory,calls,df,fp);
        if(outcome instanceof QueueFp604Api.Stopped)return outcome;
        QueueFp604Api.Normal normal=(QueueFp604Api.Normal)outcome;
        df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        r.rdx=r.rbx;r.rcx=r.rsi;
        outcome=call(image,0x9D09A3L,r,memory,calls,df,fp);
        if(outcome instanceof QueueFp604Api.Stopped)return outcome;
        normal=(QueueFp604Api.Normal)outcome;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        r.rdx=r.rbx;r.rcx=r.rdi;
        outcome=call(image,0x9D09AEL,r,memory,calls,df,fp);
        if(outcome instanceof QueueFp604Api.Stopped)return outcome;
        normal=(QueueFp604Api.Normal)outcome;df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        r.rbx-=r.rsi;r.rsi=memory.readQword(r.rsp+0x38);r.rbx>>=2;
        r.rax=r.rdi+r.rbx*4;r.rbx=memory.readQword(r.rsp+0x30);
        return popReturn(r,memory,df,fp);
    }
    private static QueueFp604Api.Normal early(Registers r,Range9DFp260Api.Memory memory,
            boolean df,QueueFp604Api.Mxcsr fp) {
        r.rbx=memory.readQword(r.rsp+0x30);r.rsi=memory.readQword(r.rsp+0x38);
        return popReturn(r,memory,df,fp);
    }
    private static QueueFp604Api.Normal popReturn(Registers r,Range9DFp260Api.Memory memory,
            boolean df,QueueFp604Api.Mxcsr fp) {
        r.rsp+=0x20;r.rdi=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);r.rsp+=8;
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits()),df),fp);
    }
    private static QueueFp604Api.Outcome call(long image,long site,Registers r,
            Range9DFp260Api.Memory memory,Range9DFp260Api.Calls calls,boolean df,QueueFp604Api.Mxcsr fp) {
        long pre=r.rsp,ret=image+site+5;
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4220AA4L,pre,r.volatileBits(),r.nonvolatileBits());
        var child=new GovernmentCrtBoundary185Api.Entry(image,pre-8,call.volatileBits(),call.nonvolatileBits());
        var frame=new Range9DFp260Api.CallFrame(call,child,df,fp,5,ret);
        r.rsp=pre-8;memory.writeQword(r.rsp,ret);
        QueueFp604Api.Outcome outcome=Objects.requireNonNull(calls.invoke(frame));
        if(outcome instanceof QueueFp604Api.Normal normal) {
            frame.checkNormalReturn(normal);r.apply(normal.base().normalReturn().volatileBits());
            r.rsp=normal.base().normalReturn().callerRspBits();
        }
        return outcome;
    }
}
