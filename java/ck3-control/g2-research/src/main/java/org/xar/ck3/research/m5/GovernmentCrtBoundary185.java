package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner body after two rejected model rounds; raw normal ports only. */
public final class GovernmentCrtBoundary185 {
    private GovernmentCrtBoundary185() { }

    public static NormalReturn execute3A84(Entry entry,Memory memory,Calls calls,LoopBudget budget) {
        State s=new State(entry);
        pushRbx(s,memory);
        s.rbx=s.rcx;
        s.rcx=s.image+0x5c5cb18L;
        indirectCall(s,memory,calls,0x4223a94L,0x43da500L);
        for(;;) {
            budget.beforeStep(0x4223a9aL,s.rbx);
            int guard=memory.readDword(s.rbx);
            if(guard==0) {
                int observed=memory.readDword(s.rbx);
                memory.writeDword(s.rbx,observed | -1);
                break;
            }
            if(guard==-1) {
                s.rcx=100L;
                directCall(s,memory,calls,0x4223aa9L,0x4223b30L);
                continue;
            }
            s.rax=calls.readGsQword58();
            s.rcx=u32(memory.readDword(s.image+0x5c5cbc4L));
            s.r8=0x10L;
            s.rdx=memory.readQword(s.rax+s.rcx*8L);
            s.rax=u32(memory.readDword(s.image+0x542f090L));
            memory.writeDword(s.rdx+s.r8,(int)s.rax);
            break;
        }
        s.rcx=s.image+0x5c5cb18L;
        popRbx(s,memory);
        long target=memory.readQword(s.image+0x43da4f0L);
        return calls.tail(new Tail(0x4223ae4L,TargetKind.INDIRECT_ABSOLUTE,target,s.entry()));
    }

    public static NormalReturn execute3A24(Entry entry,Memory memory,Calls calls) {
        State s=new State(entry);
        pushRbx(s,memory);
        s.rbx=s.rcx;
        s.rcx=s.image+0x5c5cb18L;
        indirectCall(s,memory,calls,0x4223a34L,0x43da500L);
        s.rax=u32(memory.readDword(s.image+0x542f090L));
        s.rcx=s.image+0x5c5cb18L;
        s.rdx=u32(memory.readDword(s.image+0x5c5cbc4L));
        s.rax=u32((int)s.rax+1);
        memory.writeDword(s.image+0x542f090L,(int)s.rax);
        memory.writeDword(s.rbx,(int)s.rax);
        s.rax=calls.readGsQword58();
        s.r9=0x10L;
        s.r8=memory.readQword(s.rax+s.rdx*8L);
        s.rax=u32(memory.readDword(s.image+0x542f090L));
        memory.writeDword(s.r8+s.r9,(int)s.rax);
        indirectCall(s,memory,calls,0x4223a74L,0x43da4f0L);
        popRbx(s,memory);
        return calls.tail(new Tail(0x4223a7fL,TargetKind.DIRECT_RVA,0x4223aecL,s.entry()));
    }

    public static NormalReturn execute3F24(Entry entry,Memory memory,Calls calls) {
        State s=new State(entry);
        s.rsp-=0x28L;
        directCall(s,memory,calls,0x4223f28L,0x4223ee8L);
        // NEG64 sets CF iff the full64 input is nonzero; SBB/NEG/DEC write EAX.
        s.rax=s.rax==0L?0xffffffffL:0L;
        s.rsp+=0x28L;
        long returnRip=memory.readQword(s.rsp);
        return new NormalReturn(s.v(),returnRip,s.rsp+8L,s.nv());
    }

    private static long u32(int n) { return Integer.toUnsignedLong(n); }
    private static void pushRbx(State s,Memory m) {
        s.rsp-=8L;m.writeQword(s.rsp,s.rbx);s.rsp-=0x20L;
    }
    private static void popRbx(State s,Memory m) {
        s.rsp+=0x20L;s.rbx=m.readQword(s.rsp);s.rsp+=8L;
    }
    private static void directCall(State s,Memory m,Calls c,long site,long targetRva) {
        call(s,m,c,site,TargetKind.DIRECT_RVA,targetRva,5L);
    }
    private static void indirectCall(State s,Memory m,Calls c,long site,long slotRva) {
        long target=m.readQword(s.image+slotRva);
        call(s,m,c,site,TargetKind.INDIRECT_ABSOLUTE,target,6L);
    }
    private static void call(State s,Memory m,Calls c,long site,TargetKind kind,long target,long length) {
        m.writeQword(s.rsp-8L,s.image+site+length);
        s.apply(c.invoke(new Call(site,kind,target,s.rsp,s.v(),s.nv())));
    }
    private static final class State {
        final long image;
        final NonvolatileBits originalNv;
        long rsp,rax,rcx,rdx,r8,r9,r10,r11,rbx;
        Bits128 x0,x1,x2,x3,x4,x5;
        State(Entry e) {
            image=e.imageBaseBits();rsp=e.rspBits();originalNv=e.nonvolatileBits();
            rbx=originalNv.rbxBits();apply(e.volatileBits());
        }
        void apply(VolatileBits v) {
            rax=v.raxBits();rcx=v.rcxBits();rdx=v.rdxBits();r8=v.r8Bits();r9=v.r9Bits();
            r10=v.r10Bits();r11=v.r11Bits();x0=v.xmm0();x1=v.xmm1();x2=v.xmm2();
            x3=v.xmm3();x4=v.xmm4();x5=v.xmm5();
        }
        VolatileBits v() { return new VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5); }
        NonvolatileBits nv() { return new NonvolatileBits(rbx,originalNv.rbpBits(),originalNv.rsiBits(),
                originalNv.rdiBits(),originalNv.r12Bits(),originalNv.r13Bits(),originalNv.r14Bits(),
                originalNv.r15Bits(),originalNv.xmm6()); }
        Entry entry() { return new Entry(image,rsp,v(),nv()); }
    }
}
