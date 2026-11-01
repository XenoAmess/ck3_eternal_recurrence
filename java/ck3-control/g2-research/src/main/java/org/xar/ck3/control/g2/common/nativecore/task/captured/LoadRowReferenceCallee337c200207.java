package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Held968B normal CFG; opaque calls, explicit finite budgets and Float32 ports. */
public final class LoadRowReferenceCallee337c200207 {
    private LoadRowReferenceCallee337c200207() { }
    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry, GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls, GovernmentCrtBoundary185Api.LoopBudget budget,
            LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        State s = new State(entry, memory, calls, budget, floating);
        LoadRowReferenceCallee337c200207Probe.run(s);
        while (true) {
            switch (s.pc) {
                case 0x337C292 -> LoadRowReferenceCallee337c200207Front.run(s);
                case 0x337C420 -> LoadRowReferenceCallee337c200207Displace.run(s);
                case 0x337C555, 0x337C598 -> { return LoadRowReferenceCallee337c200207Growth.run(s); }
                default -> throw new IllegalStateException("Unclosed normal PC " + Integer.toHexString(s.pc));
            }
        }
    }
    static long z32(int value) { return Integer.toUnsignedLong(value); }
    static long low8(long original, int value) { return (original & ~0xFFL) | (value & 0xFFL); }

    static final class State {
        final long image;
        long rsp,rax,rcx,rdx,r8,r9,r10,r11,rbx,rbp,rsi,rdi,r12,r13,r14,r15;
        int pc;
        GovernmentPrimaryTail155Api.Bits128 x0,x1,x2,x3,x4,x5,x6;
        final GovernmentCrtBoundary185Api.Memory m;
        final GovernmentCrtBoundary185Api.Calls calls;
        final GovernmentCrtBoundary185Api.LoopBudget budget;
        final LoadRowReferenceCallee337b7e0199Api.Float32 floating;
        State(GovernmentCrtBoundary185Api.Entry e,GovernmentCrtBoundary185Api.Memory memory,
                GovernmentCrtBoundary185Api.Calls ports,GovernmentCrtBoundary185Api.LoopBudget b,
                LoadRowReferenceCallee337b7e0199Api.Float32 f) {
            image=e.imageBaseBits();rsp=e.rspBits();m=memory;calls=ports;budget=b;floating=f;
            GovernmentPrimaryTail155Api.VolatileBits v=e.volatileBits();
            rax=v.raxBits();rcx=v.rcxBits();rdx=v.rdxBits();r8=v.r8Bits();r9=v.r9Bits();r10=v.r10Bits();r11=v.r11Bits();
            x0=v.xmm0();x1=v.xmm1();x2=v.xmm2();x3=v.xmm3();x4=v.xmm4();x5=v.xmm5();
            GovernmentPrimaryTail155Api.NonvolatileBits n=e.nonvolatileBits();
            rbx=n.rbxBits();rbp=n.rbpBits();rsi=n.rsiBits();rdi=n.rdiBits();r12=n.r12Bits();r13=n.r13Bits();r14=n.r14Bits();r15=n.r15Bits();x6=n.xmm6();
        }
        GovernmentPrimaryTail155Api.VolatileBits v() {
            return new GovernmentPrimaryTail155Api.VolatileBits(rax,rcx,rdx,r8,r9,r10,r11,x0,x1,x2,x3,x4,x5);
        }
        GovernmentPrimaryTail155Api.NonvolatileBits nv() {
            return new GovernmentPrimaryTail155Api.NonvolatileBits(rbx,rbp,rsi,rdi,r12,r13,r14,r15,x6);
        }
        void apply(GovernmentPrimaryTail155Api.VolatileBits v) {
            rax=v.raxBits();rcx=v.rcxBits();rdx=v.rdxBits();r8=v.r8Bits();r9=v.r9Bits();r10=v.r10Bits();r11=v.r11Bits();
            x0=v.xmm0();x1=v.xmm1();x2=v.xmm2();x3=v.xmm3();x4=v.xmm4();x5=v.xmm5();
        }
        void call(long site,GovernmentCrtBoundary185Api.TargetKind kind,long target,int length) {
            m.writeQword(rsp-8,image+site+length);
            apply(calls.invoke(new GovernmentCrtBoundary185Api.Call(site,kind,target,rsp,v(),nv())));
        }
        void direct(long site,long target) { call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,5); }
        void indirect(long site,long target,int length) { call(site,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,length); }
        void push(long value) { rsp-=8;m.writeQword(rsp,value); }
        long pop() { long value=m.readQword(rsp);rsp+=8;return value; }
        GovernmentCrtBoundary185Api.NormalReturn ret() {
            long rip=m.readQword(rsp);rsp+=8;
            return new GovernmentCrtBoundary185Api.NormalReturn(v(),rip,rsp,nv());
        }
    }
}
