package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Owner orchestration of held172 normal instructions; both lower outcomes remain explicit. */
public final class Element172FullState636 {
    private Element172FullState636() { }
    public static QueueFp604Api.Outcome execute(Element172Fp636Api.Input input,
            Element172Fp636Api.Memory memory,Element172Fp636Api.Calls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        GovernmentCrtBoundary185Api.Entry e=input.entry();long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean df=input.directionFlagSet();QueueFp604Api.Mxcsr fp=input.mxcsr();
        memory.writeQword(r.rsp+8,r.rbx);
        memory.writeQword(r.rsp+0x10,r.rsi);
        r.rsp-=8;memory.writeQword(r.rsp,r.rdi);
        r.rsp-=0x20;
        r.rdi=r.rcx;
        r.rax=image+0x45648a0L;memory.writeQword(r.rcx,r.rax);
        r.rsi=0;
        r.rax=Integer.toUnsignedLong(memory.readDword(r.rdx+8));
        r.rbx=r.rdx;memory.writeDword(r.rcx+8,(int)r.rax);
        r.rcx+=0x10;memory.writeQword(r.rdi+0x18,r.rsi);
        r.rax=image+0x54de260L;memory.writeQword(r.rdi+0x20,r.rsi);
        memory.writeQword(r.rcx,r.rsi);memory.writeQword(r.rcx+8,r.rsi);memory.writeQword(r.rcx+0x10,r.rax);
        r.r9=memory.readDword(r.rdx+0x1c);r.r8=memory.readQword(r.rdx+0x10);r.rdx=0;
        r.r9=(r.r9<<4)+r.r8;
        QueueFp604Api.Outcome first=call(image,0x3729846L,0x8c70b0L,r,df,fp,memory,calls);
        if(first instanceof QueueFp604Api.Stopped stopped)return stopped;
        QueueFp604Api.Normal normal=(QueueFp604Api.Normal)first;
        df=normal.base().postDirectionFlagSet();fp=normal.postMxcsr();
        memory.writeQword(r.rdi+0x30,r.rsi);r.rcx=r.rdi+0x28;
        memory.writeQword(r.rdi+0x38,r.rsi);r.rax=image+0x54de268L;
        memory.writeQword(r.rcx,r.rsi);r.rdx=0;
        memory.writeQword(r.rcx+8,r.rsi);memory.writeQword(r.rcx+0x10,r.rax);
        r.r8=memory.readQword(r.rbx+0x28);r.rax=memory.readDword(r.rbx+0x34);
        r.r9=r.r8+r.rax*4;
        QueueFp604Api.Outcome second=call(image,0x3729877L,0xadd0d0L,r,df,fp,memory,calls);
        if(second instanceof QueueFp604Api.Stopped stopped)return stopped;
        normal=(QueueFp604Api.Normal)second;
        return Element172Epilogue636.finish(r,memory,normal.base().postDirectionFlagSet(),normal.postMxcsr());
    }
    private static QueueFp604Api.Outcome call(long image,long site,long target,Registers r,
            boolean df,QueueFp604Api.Mxcsr fp,Element172Fp636Api.Memory memory,Element172Fp636Api.Calls calls) {
        long pre=r.rsp,rip=image+site+5;
        GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,pre,r.volatileBits(),r.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child=new GovernmentCrtBoundary185Api.Entry(image,pre-8,call.volatileBits(),call.nonvolatileBits());
        Element172Fp636Api.CallFrame frame=new Element172Fp636Api.CallFrame(call,child,df,fp,5,rip);
        r.rsp=child.rspBits();memory.writeQword(r.rsp,rip);
        QueueFp604Api.Outcome offered=Objects.requireNonNull(calls.invoke(frame));
        if(offered instanceof QueueFp604Api.Normal normal) {
            frame.checkNormalReturn(normal);
            r.apply(normal.base().normalReturn().volatileBits());r.rsp=normal.base().normalReturn().callerRspBits();
        }
        return offered;
    }
}
