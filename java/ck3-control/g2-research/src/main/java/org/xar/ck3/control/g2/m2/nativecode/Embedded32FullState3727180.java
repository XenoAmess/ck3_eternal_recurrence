package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Complete held394 normal represented source; all six lower calls remain opaque. */
public final class Embedded32FullState3727180 {
    private Embedded32FullState3727180() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory, Embedded32Copy581Api.Calls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        var e=input.entry();long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
            image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean df=input.directionFlagSet();
        r.rsp-=8;memory.writeQword(r.rsp,r.rsi);
        r.rsp-=8;memory.writeQword(r.rsp,r.r14);
        r.rsp-=8;memory.writeQword(r.rsp,r.r15);
        r.rsp-=0x30;
        r.rax=r.rdx+0x10;r.r15=r.rdx;r.rsi=r.rcx+0x10;r.r14=r.rcx;
        if(r.rsi!=r.rax) {
            memory.writeQword(r.rsp+0x60,r.rdi);
            r.rcx=r.rsi;r.rdi=memory.readDword(r.rax+0xC);
            memory.writeQword(r.rsp+0x28,r.r12);
            memory.writeQword(r.rsp+0x20,r.r13);
            r.r13=memory.readQword(r.rax);
            df=call(image,0x37271BAL,0x889660L,5,false,r,df,memory,calls);
            r.rcx=memory.readDword(r.rsi+0xC);r.r12=image+0x448D230L;
            if((int)r.rdi>(int)r.rcx) {
                if((int)r.rdi>memory.readDword(r.rsi+8)) {
                    r.rcx=memory.readQword(r.rsi+0x10);r.r8=8;
                    r.rdx=Integer.toUnsignedLong((int)r.rdi)<<5;
                    r.rax=memory.readQword(r.rcx);
                    long target=memory.readQword(r.rax+8);
                    df=call(image,0x37271EEL,target,3,true,r,df,memory,calls);
                    r.r8=Integer.toUnsignedLong(memory.readDword(r.rsi+0xC));r.r10=r.rax;
                    if((int)r.r8>0) {
                        r.rcx=memory.readQword(r.rsi);r.rdx=r.rax+0xC;r.rcx+=0xC;
                        do {
                            input.budget().beforeStep(0x3727210L,r.rcx);
                            memory.writeQword(r.rdx-0xC,r.r12);
                            r.rdx+=0x20;r.rax=Integer.toUnsignedLong(memory.readDword(r.rcx-4));
                            r.rcx+=0x20;memory.writeDword(r.rdx-0x24,(int)r.rax);
                            r.r8=Integer.toUnsignedLong((int)r.r8-1);
                            r.rax=Integer.toUnsignedLong(memory.readDword(r.rcx-0x20));
                            memory.writeDword(r.rdx-0x20,(int)r.rax);
                            r.x0=memory.read128(r.rcx-0x1C);memory.write128(r.rdx-0x1C,r.x0);
                        } while((int)r.r8>0);
                        r.r8=Integer.toUnsignedLong(memory.readDword(r.rsi+0xC));
                    }
                    r.r9=Integer.toUnsignedLong((int)r.rdi);r.rdx=r.r10;r.rcx=r.rsi;
                    df=call(image,0x3727249L,0x8874D0L,5,false,r,df,memory,calls);
                }
            } else {
                memory.writeQword(r.rsp+0x50,r.rbx);r.rbx=r.rdi;
                memory.writeQword(r.rsp+0x58,r.rbp);r.rbp=r.rcx;
                r.rbp<<=5;r.rbp+=memory.readQword(r.rsi);
                r.rbx<<=5;r.rbx+=memory.readQword(r.rsi);
                while(r.rbx!=r.rbp) {
                    input.budget().beforeStep(0x3727273L,r.rbx);
                    r.rax=memory.readQword(r.rbx);r.rdx=0;r.rcx=r.rbx;
                    long target=memory.readQword(r.rax);
                    df=call(image,0x372727BL,target,2,true,r,df,memory,calls);
                    r.rbx+=0x20;
                }
                r.rbp=memory.readQword(r.rsp+0x58);r.rbx=memory.readQword(r.rsp+0x50);
            }
            memory.writeDword(r.rsi+0xC,(int)r.rdi);
            if((int)r.rdi>0) {
                r.rcx=memory.readQword(r.rsi);r.rdx=r.r13+0xC;
                do {
                    input.budget().beforeStep(0x37272A0L,r.rdx);
                    memory.writeQword(r.rcx,r.r12);r.rcx+=0x20;
                    r.rax=Integer.toUnsignedLong(memory.readDword(r.rdx-4));r.rdx+=0x20;
                    memory.writeDword(r.rcx-0x18,(int)r.rax);
                    r.rdi=Integer.toUnsignedLong((int)r.rdi-1);
                    r.rax=Integer.toUnsignedLong(memory.readDword(r.rdx-0x20));
                    memory.writeDword(r.rcx-0x14,(int)r.rax);
                    r.x0=memory.read128(r.rdx-0x1C);memory.write128(r.rcx-0x10,r.x0);
                } while((int)r.rdi>0);
            }
            r.rdi=memory.readQword(r.rsp+0x60);
            r.r12=memory.readQword(r.rsp+0x28);r.r13=memory.readQword(r.rsp+0x20);
        }
        r.rax=Integer.toUnsignedLong(memory.readDword(r.r15+0x28));
        r.rdx=r.r15+0x30;r.rcx=r.r14+0x30;
        memory.writeDword(r.r14+0x28,(int)r.rax);
        df=call(image,0x37272F0L,0x37282B0L,5,false,r,df,memory,calls);
        r.rcx=r.r14;
        df=call(image,0x37272F8L,0x3727EC0L,5,false,r,df,memory,calls);
        r.rax=r.r14;r.rsp+=0x30;
        r.r15=memory.readQword(r.rsp);r.rsp+=8;
        r.r14=memory.readQword(r.rsp);r.rsp+=8;
        r.rsi=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),rip,r.rsp+8,r.nonvolatileBits()),df);
    }
    private static boolean call(long image,long site,long target,int length,boolean indirect,
            Registers r,boolean df,FullCopy437Api.Memory memory,Embedded32Copy581Api.Calls calls) {
        long rip=image+site+length;memory.writeQword(r.rsp-8,rip);
        var call=new GovernmentCrtBoundary185Api.Call(site,
            indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            target,r.rsp,r.volatileBits(),r.nonvolatileBits());
        var frame=new Embedded32Copy581Api.CallFrame(call,
            new GovernmentCrtBoundary185Api.Entry(image,r.rsp-8,call.volatileBits(),call.nonvolatileBits()),df,length,rip);
        FullCopy437Api.CallResult result=calls.invoke(frame);frame.checkNormalReturn(result);
        r.apply(result.normalReturn().volatileBits());return result.postDirectionFlagSet();
    }
}
