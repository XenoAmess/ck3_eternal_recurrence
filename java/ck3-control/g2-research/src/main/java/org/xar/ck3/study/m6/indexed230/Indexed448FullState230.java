package org.xar.ck3.study.m6.indexed230;

import java.util.Objects;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.study.m6.indexed229.AtomicIndexedMemory229;
import org.xar.ck3.study.m6.indexed229.Indexed448AtomicBridge229;

/** Source-specific represented registers around one mature470B business invocation. */
public final class Indexed448FullState230 {
    private Indexed448FullState230() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,AtomicIndexedMemory229 memory,
            GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(entry);Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);Objects.requireNonNull(budget);
        State state=new State(entry,memory,calls,budget);
        long selected=Indexed448AtomicBridge229.execute(state,state.ports(),
                new IndexedHelper225Api.Input(entry.imageBaseBits(),(int)entry.volatileBits().rcxBits(),
                        entry.volatileBits().rdxBits(),entry.volatileBits().r8Bits(),entry.volatileBits().r9Bits()));
        return state.finish(selected);
    }

    private static IllegalStateException mismatch(){return new IllegalStateException("source observation mismatch");}
    private static long u32(int value){return Integer.toUnsignedLong(value);}

    private static final class State implements AtomicIndexedMemory229 {
        private final long image,pre;
        private final AtomicIndexedMemory229 memory;
        private final GovernmentCrtBoundary185Api.Calls calls;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final Registers r;
        private int pc=0x424E477;
        private boolean targetReady;
        private long target;

        State(GovernmentCrtBoundary185Api.Entry entry,AtomicIndexedMemory229 memory,
                GovernmentCrtBoundary185Api.Calls calls,GovernmentCrtBoundary185Api.LoopBudget budget){
            this.image=entry.imageBaseBits();this.pre=entry.rspBits()-0x48L;
            this.memory=memory;this.calls=calls;this.budget=budget;
            r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,pre,
                    entry.volatileBits(),entry.nonvolatileBits()));
            long s=entry.rspBits();
            memory.writeQword(s+0x8L,r.rbx);memory.writeQword(s+0x10L,r.rbp);memory.writeQword(s+0x18L,r.rsi);
            memory.writeQword(s-0x8L,r.rdi);memory.writeQword(s-0x10L,r.r12);memory.writeQword(s-0x18L,r.r13);
            memory.writeQword(s-0x20L,r.r14);memory.writeQword(s-0x28L,r.r15);
            r.r15=u32((int)r.rcx);r.r14=image;r.r12=r.r9;r.rbp=r.r8;r.r13=r.rdx;
        }

        // Pure blocks stop before the next original observation, transfer, or epilogue.
        private void advance(){
            while(true){
                switch(pc){
                    case 0x424E486 -> {
                        r.rdi=-1L;r.rax=u32((int)r.r10);r.rdx=r.r10^r.rcx;r.rax&=0x3FL;
                        r.rcx=(r.rcx&~0xFFL)|(r.rax&0xFFL);
                        r.rdx=Long.rotateRight(r.rdx,(int)r.rcx&63);
                        if(r.rdx==-1L)pc=0x424E5FF;
                        else if(r.rdx!=0L){r.rax=r.rdx;pc=0x424E601;}
                        else pc=0x424E4B1;
                    }
                    case 0x424E4B1 -> pc=r.r8==r.r12?0x424E593:0x424E4BA;
                    case 0x424E4C5 -> pc=r.rbx==0L?0x424E4D8:(r.rbx==r.rdi?0x424E57F:0x424E57A);
                    case 0x424E4E0 -> {r.rdx=0L;r.rcx=r.r14;r.r8=0x800L;pc=0x424E4EB;}
                    case 0x424E4F1 -> {r.rbx=r.rax;pc=r.rax!=0L?0x424E548:0x424E4F9;}
                    case 0x424E4FF -> {
                        if((int)r.rax!=0x57)pc=0x424E546;
                        else{r.rbx=u32((int)r.rax-0x50);r.rcx=r.r14;r.r8=u32((int)r.rbx);r.rdx=image+0x44226A0L;pc=0x424E514;}
                    }
                    case 0x424E519 -> {
                        if((int)r.rax==0)pc=0x424E546;
                        else{r.r8=u32((int)r.rbx);r.rdx=image+0x4426EC8L;r.rcx=r.r14;pc=0x424E52A;}
                    }
                    case 0x424E52F -> {
                        if((int)r.rax==0)pc=0x424E546;
                        else{r.r8=0L;r.rdx=0L;r.rcx=r.r14;pc=0x424E53B;}
                    }
                    case 0x424E541 -> {r.rbx=r.rax;pc=0x424E548;}
                    case 0x424E546 -> {r.rbx=0L;pc=0x424E548;}
                    case 0x424E548 -> {r.r14=image;r.rax=r.rbx==0L?r.rdi:r.rbx;pc=r.rbx==0L?0x424E557:0x424E564;}
                    case 0x424E55F -> pc=0x424E57F;
                    case 0x424E56C -> {if(r.rax==0L)pc=0x424E57A;else{r.rcx=r.rbx;pc=0x424E574;}}
                    case 0x424E57A -> pc=r.rbx!=0L?0x424E5D4:0x424E57F;
                    case 0x424E57F -> {r.rbp+=0x4L;pc=r.rbp!=r.r12?0x424E4BA:0x424E58C;}
                    case 0x424E593 -> {r.rbx=0L;pc=0x424E595;}
                    case 0x424E595 -> {if(r.rbx==0L)pc=0x424E5E4;else{r.rdx=r.r13;r.rcx=r.rbx;pc=0x424E5A0;}}
                    case 0x424E5A6 -> pc=r.rax==0L?0x424E5DD:0x424E5AB;
                    case 0x424E5B2 -> {
                        r.rdx=0x40L;r.rcx=u32((int)r.r8)&0x3FL;r.rdx=u32((int)r.rdx-(int)r.rcx);
                        r.rcx=(r.rcx&~0xFFL)|(r.rdx&0xFFL);
                        r.rdx=Long.rotateRight(r.rax,(int)r.rcx&63)^r.r8;pc=0x424E5CA;
                    }
                    case 0x424E5D2 -> pc=0x424E601;
                    case 0x424E5DB -> pc=0x424E595;
                    case 0x424E5E4 -> {
                        r.rax=u32((int)r.r10)&0x3FL;r.rcx=u32(0x40-(int)r.rax);
                        r.rdi=Long.rotateRight(r.rdi,(int)r.rcx&63)^r.r10;pc=0x424E5F7;
                    }
                    case 0x424E5FF -> {r.rax=0L;pc=0x424E601;}
                    default -> {return;}
                }
            }
        }

        private long read(long address,long expected){if(address!=expected)throw mismatch();return memory.readQword(address);}
        @Override public long readQword(long address){
            advance();long observed;
            switch(pc){
                case 0x424E477 -> {observed=read(address,r.r14+r.r15*8L+0x5C5D790L);r.rcx=observed;pc=0x424E47F;}
                case 0x424E47F -> {observed=read(address,image+0x542F0B8L);r.r10=observed;pc=0x424E486;}
                case 0x424E4BD -> {observed=read(address,r.r14+r.rsi*8L+0x5C5D6F0L);r.rbx=observed;pc=0x424E4C5;}
                case 0x424E4D8 -> {observed=read(address,r.r14+r.rsi*8L+0x44269D0L);r.r14=observed;pc=0x424E4E0;}
                case 0x424E58C -> {observed=read(address,image+0x542F0B8L);r.r10=observed;pc=0x424E593;}
                case 0x424E5AB -> {observed=read(address,image+0x542F0B8L);r.r8=observed;pc=0x424E5B2;}
                case 0x424E5D4 -> {observed=read(address,image+0x542F0B8L);r.r10=observed;pc=0x424E5DB;}
                case 0x424E5DD -> {observed=read(address,image+0x542F0B8L);r.r10=observed;pc=0x424E5E4;}
                case 0x424E4EB,0x424E4F9,0x424E53B,0x424E574,0x424E5A0 -> {
                    if(targetReady)throw mismatch();
                    long offset=switch(pc){case 0x424E4F9 -> 0x43DA738L;case 0x424E574 -> 0x43DA7C0L;case 0x424E5A0 -> 0x43DA680L;default -> 0x43DA478L;};
                    observed=read(address,image+offset);target=observed;targetReady=true;
                }
                default -> throw mismatch();
            }
            return observed;
        }
        @Override public int readDword(long address){
            advance();if(pc!=0x424E4BA||address!=r.rbp)throw mismatch();
            budget.beforeStep(0x424E4BAL,r.rbp);int value=memory.readDword(address);
            r.rsi=u32(value);pc=0x424E4BD;return value;
        }
        @Override public long exchangeQword(long address,long value){
            advance();long expectedAddress,expectedValue;
            switch(pc){
                case 0x424E557,0x424E564 -> {expectedAddress=r.r14+r.rsi*8L+0x5C5D6F0L;expectedValue=r.rax;}
                case 0x424E5CA -> {expectedAddress=r.r14+r.r15*8L+0x5C5D790L;expectedValue=r.rdx;}
                case 0x424E5F7 -> {expectedAddress=r.r14+r.r15*8L+0x5C5D790L;expectedValue=r.rdi;}
                default -> throw mismatch();
            }
            if(address!=expectedAddress||value!=expectedValue)throw mismatch();
            long old=memory.exchangeQword(address,value);
            switch(pc){
                case 0x424E557 -> {r.rax=old;pc=0x424E55F;}
                case 0x424E564 -> {r.rax=old;pc=0x424E56C;}
                case 0x424E5CA -> {r.rdx=old;pc=0x424E5D2;}
                case 0x424E5F7 -> {r.rdi=old;pc=0x424E5FF;}
                default -> throw mismatch();
            }
            return old;
        }
        @Override public void writeDword(long address,int value){memory.writeDword(address,value);}
        @Override public void writeQword(long address,long value){memory.writeQword(address,value);}
        @Override public int readUnsignedByte(long address){return memory.readUnsignedByte(address);}
        @Override public void writeByte(long address,int value){memory.writeByte(address,value);}
        @Override public int lockedXaddDword(long address,int value){return memory.lockedXaddDword(address,value);}
        @Override public Bits128 read128(long address){return memory.read128(address);}
        @Override public void write128(long address,Bits128 value){memory.write128(address,value);}

        private long invoke(long site,GovernmentCrtBoundary185Api.TargetKind kind,long actualTarget){
            advance();if(site!=pc||r.rsp!=pre)throw mismatch();
            boolean direct=pc==0x424E514||pc==0x424E52A;
            if(direct){if(kind!=GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA||targetReady||actualTarget!=0x4246A60L)throw mismatch();}
            else if(kind!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE||!targetReady||target!=actualTarget)throw mismatch();
            long length=direct?5L:6L;memory.writeQword(pre-8L,image+site+length);
            r.apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(site,kind,actualTarget,pre,r.volatileBits(),r.nonvolatileBits())));
            targetReady=false;pc=(int)(site+length);return r.rax;
        }
        IndexedHelper225Api.Ports ports(){
            return new IndexedHelper225Api.Ports(){
                @Override public long call43da478(IndexedHelper225Api.Memory ignored,long site,long target,long c,int d,int b){
                    advance();if((pc!=0x424E4EB&&pc!=0x424E53B)||r.rcx!=c||r.rdx!=u32(d)||r.r8!=u32(b))throw mismatch();
                    return invoke(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target);
                }
                @Override public int call43da738(IndexedHelper225Api.Memory ignored,long site,long target){
                    advance();if(pc!=0x424E4F9)throw mismatch();return(int)invoke(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target);
                }
                @Override public int call4246a60(IndexedHelper225Api.Memory ignored,long site,long c,long d,int b){
                    advance();if((pc!=0x424E514&&pc!=0x424E52A)||r.rcx!=c||r.rdx!=d||r.r8!=u32(b))throw mismatch();
                    return(int)invoke(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x4246A60L);
                }
                @Override public void call43da7c0(IndexedHelper225Api.Memory ignored,long site,long target,long c){
                    advance();if(pc!=0x424E574||r.rcx!=c)throw mismatch();invoke(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target);
                }
                @Override public long call43da680(IndexedHelper225Api.Memory ignored,long site,long target,long c,long d){
                    advance();if(pc!=0x424E5A0||r.rcx!=c||r.rdx!=d)throw mismatch();return invoke(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target);
                }
            };
        }
        private long pop(){long value=memory.readQword(r.rsp);r.rsp+=8L;return value;}
        GovernmentCrtBoundary185Api.NormalReturn finish(long selected){
            advance();if(pc!=0x424E601||targetReady||r.rax!=selected)throw new IllegalStateException("source scalar mismatch");
            r.rbx=memory.readQword(pre+0x50L);r.rbp=memory.readQword(pre+0x58L);r.rsi=memory.readQword(pre+0x60L);
            r.rsp=pre+0x20L;r.r15=pop();r.r14=pop();r.r13=pop();r.r12=pop();r.rdi=pop();
            long actualRip=memory.readQword(r.rsp);
            return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),actualRip,r.rsp+8L,r.nonvolatileBits());
        }
    }
}
