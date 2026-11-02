package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Complete held normal809; mature295/299 and row291, with opaque185 COPY only. */
public final class SortRangeFullState300 {
    private SortRangeFullState300() { }
    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(),entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        memory.writeQword(r.rsp+0x18L,r.rbx);memory.writeQword(r.rsp+0x20L,r.rsi);
        push(r,memory,r.rdi);push(r,memory,r.r12);push(r,memory,r.r13);
        push(r,memory,r.r14);push(r,memory,r.r15);r.rsp-=0x50L;
        r.r13=r.r9;r.r14=r.r8;r.r15=r.rdx;r.r12=r.rcx;r.rdi=r.rcx;
        if(r.r8>0x20L) {
            memory.writeQword(r.rsp+0x88L,r.rbp);r.rbp=(r.r8-0x21L)>>>5;r.rbp++;
            do {
                budget.beforeStep(0x1A817D0L,r.rdi);r.rsi=r.rdi+0x500L;
                if(r.rdi!=r.rsi) {
                    r.rbx=r.rdi+0x28L;
                    if(r.rbx!=r.rsi) {
                        do {
                            budget.beforeStep(0x1A817F0L,r.rbx);SortRowFrames300.capture(r,memory);
                            if((int)r.rdx>memory.readDword(r.rdi)) {
                                r.r8=r.rbx;r.rdx=r.rdi;r.r8-=r.rdi;r.rcx-=r.r8;r.rcx+=0x28L;
                                opaqueCopy(entry.imageBaseBits(),r,memory,calls);SortRowFrames300.restoreFront(r,memory);
                            } else {
                                int previous=memory.readDword(r.rbx-0x28L);r.rax=r.rbx-0x28L;
                                if((int)r.rdx>previous) {
                                    do {
                                        budget.beforeStep(0x1A81860L,r.rax);transfer(r,memory,r.rax,r.rcx);
                                        r.rcx=r.rax;r.rax-=0x28L;
                                    } while((int)r.rdx>memory.readDword(r.rax));
                                }
                                memory.write128(r.rcx,r.x2);memory.write128(r.rcx+0x10L,r.x3);
                                memory.writeQword(r.rcx+0x20L,r.x4.lowBits());
                            }
                            r.rbx+=0x28L;
                        } while(r.rbx!=r.rsi);
                    }
                }
                r.rdi=r.rsi;r.rbp--;
            } while(r.rbp!=0L);
            r.rbp=memory.readQword(r.rsp+0x88L);
        }
        r.rdx=r.r15;r.rcx=r.rdi;
        child(entry.imageBaseBits(),0x1A818B7L,true,r,memory,calls,budget);
        if(r.r14>0x20L) {
            r.rbx=r.r14;r.rdx=r.r12;r.rcx=r.r13;
            do {
                budget.beforeStep(0x1A818D0L,r.rdx);r.rbx-=0x20L;r.r11=r.rdx+0x500L;
                r.rax=0x20L;r.r8=r.r11;if(r.rbx<r.rax)r.rax=r.rbx;
                r.rbx-=r.rax;r.rax=r.rax+r.rax*4L;r.rax+=0xA0L;r.r10=r.rdx+r.rax*8L;
                for(;;) {
                    budget.beforeStep(0x1A818FCL,r.rdx);r.rax=Integer.toUnsignedLong(memory.readDword(r.rdx));
                    r.r9=r.rcx;r.rcx+=0x28L;
                    if(memory.readDword(r.r8)>(int)r.rax) {
                        transfer(r,memory,r.r8,r.r9);r.r8+=0x28L;
                        if(r.r8!=r.r10)continue;
                        if(r.rdx!=r.r11) {
                            do {
                                budget.beforeStep(0x1A81940L,r.rdx);transfer(r,memory,r.rdx,r.rcx);
                                r.rdx+=0x28L;r.rcx+=0x28L;
                            } while(r.rdx!=r.r11);
                        }
                    } else {
                        transfer(r,memory,r.rdx,r.r9);r.rdx+=0x28L;
                        if(r.rdx!=r.r11)continue;
                        if(r.r8!=r.r10) {
                            do {
                                budget.beforeStep(0x1A819A0L,r.r8);transfer(r,memory,r.r8,r.rcx);
                                r.r8+=0x28L;r.rcx+=0x28L;
                            } while(r.r8!=r.r10);
                        }
                    }
                    break;
                }
                r.rdx=r.r10;
            } while(r.rbx>0x20L);
            if(r.r10!=r.r15) {
                r.rcx-=r.r10;
                do {
                    budget.beforeStep(0x1A819E0L,r.r10);transfer(r,memory,r.r10,r.rcx+r.r10);r.r10+=0x28L;
                } while(r.r10!=r.r15);
            }
            r.rbx=Integer.toUnsignedLong(memory.readUnsignedByte(r.rsp+0xA0L));
            r.rax=r.r14+r.r14*4L;r.rsi=r.rax*8L;
            memory.writeByte(r.rsp+0x28L,(int)r.rbx);r.rsi+=r.r13;
            memory.writeQword(r.rsp+0x20L,r.r14);r.rdx=r.rsi;r.r9=0x40L;r.r8=r.r12;r.rcx=r.r13;
            child(entry.imageBaseBits(),0x1A81A39L,false,r,memory,calls,budget);
            r.rdi=0x80L;
            if(r.r14>r.rdi) {
                do {
                    budget.beforeStep(0x1A81A50L,r.rdi);
                    memory.writeByte(r.rsp+0x28L,(int)r.rbx);r.r9=r.rdi;r.r8=r.r13;
                    memory.writeQword(r.rsp+0x20L,r.r14);r.rdx=r.r15;r.rcx=r.r12;
                    child(entry.imageBaseBits(),0x1A81A65L,false,r,memory,calls,budget);
                    r.rdi+=r.rdi;memory.writeByte(r.rsp+0x28L,(int)r.rbx);r.r9=r.rdi;
                    memory.writeQword(r.rsp+0x20L,r.r14);r.r8=r.r12;r.rdx=r.rsi;r.rcx=r.r13;
                    child(entry.imageBaseBits(),0x1A81A82L,false,r,memory,calls,budget);r.rdi+=r.rdi;
                } while(r.r14>r.rdi);
            }
        }
        r.r11=r.rsp+0x50L;r.rbx=memory.readQword(r.r11+0x40L);r.rsi=memory.readQword(r.r11+0x48L);
        r.rsp=r.r11;r.r15=pop(r,memory);r.r14=pop(r,memory);r.r13=pop(r,memory);
        r.r12=pop(r,memory);r.rdi=pop(r,memory);long rip=memory.readQword(r.rsp);r.rsp+=8L;
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),rip,r.rsp,r.nonvolatileBits());
    }
    private static void child(long image,long site,boolean small,Registers r,
            GovernmentCrtBoundary185Api.Memory m,GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        long pre=r.rsp;var offered=r.nonvolatileBits();m.writeQword(pre-8L,image+site+5L);
        var entry=new GovernmentCrtBoundary185Api.Entry(image,pre-8L,r.volatileBits(),offered);
        var nr=small?SmallRangeFullState295.execute(entry,m,calls,budget):PassFullState299.execute(entry,m,calls,budget);
        if(nr.returnRipBits()!=image+site+5L||nr.callerRspBits()!=pre||!nr.nonvolatileBits().equals(offered))
            throw new UnsupportedOperationException("Child left represented normal continuation");
        r.apply(nr.volatileBits());
    }
    private static void opaqueCopy(long image,Registers r,GovernmentCrtBoundary185Api.Memory m,GovernmentCrtBoundary185Api.Calls calls) {
        long pre=r.rsp;m.writeQword(pre-8L,image+0x1A8182FL);
        r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(0x1A8182AL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4226860L,pre,r.volatileBits(),r.nonvolatileBits())));
    }
    private static void transfer(Registers r,GovernmentCrtBoundary185Api.Memory m,long source,long destination) {
        var row=Copy40Row291.transfer(m,source,destination);r.x0=row.xmm0();r.x1=row.xmm1();
    }
    private static void push(Registers r,GovernmentCrtBoundary185Api.Memory m,long bits){r.rsp-=8L;m.writeQword(r.rsp,bits);}
    private static long pop(Registers r,GovernmentCrtBoundary185Api.Memory m){long x=m.readQword(r.rsp);r.rsp+=8L;return x;}
}
