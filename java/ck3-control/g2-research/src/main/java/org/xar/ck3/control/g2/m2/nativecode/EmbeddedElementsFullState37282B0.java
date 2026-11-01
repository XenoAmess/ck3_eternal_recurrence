package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Exact held322-byte normal represented-state execution; all lower calls remain opaque. */
public final class EmbeddedElementsFullState37282B0 {
    private EmbeddedElementsFullState37282B0() { }
    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input,
            FullCopy437Api.Memory memory, EmbeddedElements578Api.Calls calls) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);Objects.requireNonNull(calls);
        GovernmentCrtBoundary185Api.Entry e=input.entry();
        long image=e.imageBaseBits();
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
            image,e.rspBits(),e.volatileBits(),e.nonvolatileBits()));
        boolean df=input.directionFlagSet();
        memory.writeQword(r.rsp+8,r.rbx);
        memory.writeQword(r.rsp+0x10,r.rbp);
        memory.writeQword(r.rsp+0x18,r.rsi);
        memory.writeQword(r.rsp+0x20,r.rdi);
        r.rsp-=8;memory.writeQword(r.rsp,r.r12);
        r.rsp-=8;memory.writeQword(r.rsp,r.r14);
        r.rsp-=8;memory.writeQword(r.rsp,r.r15);
        r.rsp-=0x30;
        r.rsi=r.rcx;
        if(r.rcx!=r.rdx) {
            r.rbx=memory.readDword(r.rdx+0xC);
            r.rbp=memory.readQword(r.rdx);
            df=call(image,0x37282E1L,0x889780L,5,false,r,df,memory,calls);
            r.rax=memory.readDword(r.rsi+0xC);
            if((int)r.rbx>(int)r.rax) {
                if((int)r.rbx>memory.readDword(r.rsi+8)) {
                    r.rcx=memory.readQword(r.rsi+0x10);
                    r.rax=memory.readQword(r.rcx);
                    r.r9=memory.readQword(r.rax+8);
                    r.rax=Integer.toUnsignedLong((int)r.rbx);
                    r.rdx=(r.rax+r.rax*8)<<3;
                    r.r8=8;
                    df=call(image,0x3728316L,r.r9,3,true,r,df,memory,calls);
                    r.r12=r.rax;
                    r.r14=Integer.toUnsignedLong(memory.readDword(r.rsi+0xC));
                    r.r15=memory.readQword(r.rsi);
                    if((int)r.r14>0) {
                        memory.writeQword(r.rsp+0x20,r.rax);
                        r.rdi=r.rax;
                        memory.writeQword(r.rsp+0x28,r.rax);
                        do {
                            input.budget().beforeStep(0x3728335L,r.r15);
                            r.rdx=r.r15;r.rcx=r.rdi;
                            df=call(image,0x372833BL,0x37295B0L,5,false,r,df,memory,calls);
                            r.rdi+=0x48;
                            memory.writeQword(r.rsp+0x28,r.rdi);
                            r.r14=Integer.toUnsignedLong((int)r.r14-1);
                            r.r15+=0x48;
                        } while((int)r.r14>0);
                        r.r14=Integer.toUnsignedLong(memory.readDword(r.rsi+0xC));
                    }
                    r.r9=Integer.toUnsignedLong((int)r.rbx);
                    r.r8=Integer.toUnsignedLong((int)r.r14);
                    r.rdx=r.r12;r.rcx=r.rsi;
                    df=call(image,0x372836CL,0xDBDB80L,5,false,r,df,memory,calls);
                }
            } else {
                r.rdx=memory.readQword(r.rsi);
                r.rcx=r.rax+r.rax*8;
                r.r14=r.rdx+r.rcx*8;
                r.rcx=r.rbx+r.rbx*8;
                r.rdi=r.rdx+r.rcx*8;
                while(r.rdi!=r.r14) {
                    input.budget().beforeStep(0x3728390L,r.rdi);
                    r.rax=memory.readQword(r.rdi);
                    r.rdx=0;r.rcx=r.rdi;
                    long target=memory.readQword(r.rax);
                    df=call(image,0x3728398L,target,2,true,r,df,memory,calls);
                    r.rdi+=0x48;
                }
            }
            memory.writeDword(r.rsi+0xC,(int)r.rbx);
            if((int)r.rbx>0) {
                r.rdi=memory.readQword(r.rsi);
                do {
                    input.budget().beforeStep(0x37283B0L,r.rbp);
                    r.rdx=r.rbp;r.rcx=r.rdi;
                    df=call(image,0x37283B6L,0x37297F0L,5,false,r,df,memory,calls);
                    r.rdi+=0x48;
                    r.rbx=Integer.toUnsignedLong((int)r.rbx-1);
                    r.rbp+=0x48;
                } while((int)r.rbx>0);
            }
        }
        r.rax=r.rsi;
        r.rbx=memory.readQword(r.rsp+0x50);
        r.rbp=memory.readQword(r.rsp+0x58);
        r.rsi=memory.readQword(r.rsp+0x60);
        r.rdi=memory.readQword(r.rsp+0x68);
        r.rsp+=0x30;
        r.r15=memory.readQword(r.rsp);r.rsp+=8;
        r.r14=memory.readQword(r.rsp);r.rsp+=8;
        r.r12=memory.readQword(r.rsp);r.rsp+=8;
        long rip=memory.readQword(r.rsp);
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),rip,r.rsp+8,r.nonvolatileBits()),df);
    }
    private static boolean call(long image,long site,long target,int length,boolean indirect,
            Registers r,boolean df,FullCopy437Api.Memory memory,EmbeddedElements578Api.Calls calls) {
        long rip=image+site+length;
        memory.writeQword(r.rsp-8,rip);
        GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(site,
            indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            target,r.rsp,r.volatileBits(),r.nonvolatileBits());
        EmbeddedElements578Api.CallFrame frame=new EmbeddedElements578Api.CallFrame(call,
            new GovernmentCrtBoundary185Api.Entry(image,r.rsp-8,call.volatileBits(),call.nonvolatileBits()),df,length,rip);
        FullCopy437Api.CallResult result=calls.invoke(frame);
        frame.checkNormalReturn(result);
        r.apply(result.normalReturn().volatileBits());
        return result.postDirectionFlagSet();
    }
}
