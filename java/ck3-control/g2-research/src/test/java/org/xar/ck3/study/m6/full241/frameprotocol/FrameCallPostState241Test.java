package org.xar.ck3.study.m6.full241.frameprotocol;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238Api;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Frame;
import org.xar.ck3.study.m6.full239.Transfer4Calls239;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api.*;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.CallFrame;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api.NormalRule;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Provider;

/**
 * Three independent new assembled-Frame/CALL protocol proposals. No body or FP kernel runs.
 * All qualified effects and known entries are explicit synthetic typed record suppliers.
 * Each source dispatch is invoked once; this is not an invokePrepared replay/dedup assertion.
 */
public final class FrameCallPostState241Test {
    private static final long I=0x140000000L,MOVE=0xB2EEE0L,SWAP=0xB2EDF0L;
    private static final long D=0x2000L,T=0x3000L,DB=0x6000L,TB=0x7000L,NEW=0x8000L;
    private static final long ALLOC_TARGET=0xBAD24101L,OUTER_SLOT=0x9008L;
    private static int scenes,checks;
    private FrameCallPostState241Test() { }

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("new Frame protocol cases only");
        purePrepareThenTypedIndirectAndDirect();scenes++;
        knownRegistryFreshNThenInnerStopped();scenes++;
        legacyConstructorKeeps185Ports();scenes++;
        System.out.println("PASS scenes="+scenes+" checks="+checks
                +" sourceDispatchSinglePushEffect=true purePreparation=true"
                +" syntheticQualifiedEffectsOnly=true wholeBodyRuns=0 fpAlgorithmRuns=0"
                +" oldContextProvider643CarrierAnd239Scenes=0 Native=false Game=false hardwareABI=false");
    }

    private static void purePrepareThenTypedIndirectAndDirect() {
        long pre=0x8B60L;Ram m=new Ram();m.poke(D,DB);
        VolatileBits initial=change(v(0x100L),0xA000L,0x4000L,4L,4L);
        NonvolatileBits initialN=new NonvolatileBits(TB,0L,1L,D,4L,1L,D,T,x(0xB9L));
        Entry entry=new Entry(I,pre,initial,initialN);
        Mxcsr before=new Mxcsr(0x1F80,0xFFC0),afterFirst=Mxcsr.exact(0x1FA0);
        Mxcsr afterSecond=new Mxcsr(0x80,0x80);
        VolatileBits first=rax(v(0x1100L),NEW),second=v(0x2200L);
        CallFrame[] prepared=new CallFrame[2];int[] effects={0},budgets={0};
        CallOutcome242Api.OutcomePort opaque=actual->{
            int index=effects[0]++;check(index<2);
            equal(actual,prepared[index]);equal(actual.normalRule(),NormalRule.OPAQUE_PRESERVES_N);
            equal(actual.call().rspBits(),pre);equal(actual.childEntry().rspBits(),pre-8L);
            equal(m.writes.size(),index+1);
            if(index==0) {
                equal(actual.call().callSiteRva(),0xB2EF9EL);
                equal(actual.call().kind(),TargetKind.INDIRECT_ABSOLUTE);
                equal(actual.call().targetBits(),ALLOC_TARGET);equal(actual.instructionLength(),3);
                equal(actual.call().volatileBits(),initial);equal(actual.call().nonvolatileBits(),initialN);
                equal(actual.preDirectionFlagSet(),false);equal(actual.preMxcsr(),before);
                equal(m.peek(pre-8L),I+0xB2EFA1L);
                return normal(actual,first,initialN,true,afterFirst);
            }
            equal(actual.call().callSiteRva(),0xB2EFADL);equal(actual.instructionLength(),5);
            equal(actual.call().kind(),TargetKind.DIRECT_RVA);equal(actual.call().targetBits(),0x4226860L);
            equal(actual.call().volatileBits(),change(first,NEW,NEW,DB,0L));
            NonvolatileBits currentN=withRdi(initialN,NEW);
            equal(actual.call().nonvolatileBits(),currentN);
            equal(actual.preDirectionFlagSet(),true);equal(actual.preMxcsr(),afterFirst);
            equal(m.peek(pre-8L),I+0xB2EFB2L);
            return normal(actual,second,currentN,false,afterSecond);
        };
        Frame f=new Frame(new PostState240Api.Input(entry,false,before,0x3729620L),m,
                new NoStages(),(site,cursor,end)->budgets[0]++,opaque,blockedRegistry(),MOVE);
        check(f.postStateContext().boundTo(I,f.r));equal(m.writes.size(),0);equal(effects[0],0);
        Entry unchanged=f.postStateContext().currentState();
        prepared[0]=CallOutcome242Provider.prepare(MOVE,0xB2EF9EL,ALLOC_TARGET,
                f.postStateContext().currentState(),f.postStateContext().directionFlagSet(),
                f.postStateContext().mxcsr());
        equal(f.postStateContext().currentState(),unchanged);
        equal(m.writes.size(),0);equal(m.reads.size(),0);equal(effects[0],0);
        f.indirect(0xB2EF9EL,ALLOC_TARGET);
        equal(effects[0],1);equal(f.r.volatileBits(),first);equal(f.r.nonvolatileBits(),initialN);
        equal(f.r.rsp,pre);equal(f.postStateContext().directionFlagSet(),true);
        equal(f.postStateContext().mxcsr(),afterFirst);

        // Only the actual four register effects after allocation; no allocator/COPY implementation.
        f.r.rdx=m.readQword(f.r.r14);f.r.r8=0L;f.r.rcx=f.r.rax;f.r.rdi=f.r.rax;
        Entry copyPrefix=f.postStateContext().currentState();
        prepared[1]=CallOutcome242Provider.prepare(MOVE,0xB2EFADL,0x4226860L,
                copyPrefix,f.postStateContext().directionFlagSet(),f.postStateContext().mxcsr());
        equal(m.writes.size(),1);equal(effects[0],1);equal(f.postStateContext().currentState(),copyPrefix);
        Transfer4Calls239.direct(f,0xB2EFADL,0x4226860L); // actual public guard, not a copied branch.
        equal(effects[0],2);equal(budgets[0],0);
        equal(m.writes,List.of(new Write(pre-8L,I+0xB2EFA1L),new Write(pre-8L,I+0xB2EFB2L)));
        equal(f.r.volatileBits(),second);equal(f.r.nonvolatileBits(),withRdi(initialN,NEW));
        equal(f.r.rsp,pre);equal(f.postStateContext().directionFlagSet(),false);
        equal(f.postStateContext().mxcsr(),afterSecond);
    }

    private static void knownRegistryFreshNThenInnerStopped() {
        long pre=0x8BB0L;Ram m=new Ram();m.poke(OUTER_SLOT,0xABCDEF0011223344L);
        Entry entry=new Entry(I,pre,v(0x3300L),n(0x4400L));
        VolatileBits returned=v(0x5500L);NonvolatileBits fresh=n(0x6600L);
        Mxcsr before=new Mxcsr(0x1F80,0xFFC0),afterFirst=Mxcsr.exact(0x1FA0);
        int[] known={0},budgets={0},afterStop={0};List<Long> budgetSites=new ArrayList<>();
        Stopped[] exactStop={null};
        EntryExecutor moveSupplier=(input,memory)->{
            int index=known[0]++;check(index<2);check(memory==m);
            equal(input.entry().rspBits(),pre-8L);equal(m.writes.size(),index+1);
            if(index==0) {
                equal(input.originCallSiteRva(),0xB2EE82L);
                equal(input.entry().volatileBits(),entry.volatileBits());
                equal(input.entry().nonvolatileBits(),entry.nonvolatileBits());
                equal(input.directionFlagSet(),false);equal(input.mxcsr(),before);
                equal(m.peek(pre-8L),I+0xB2EE87L);
                return new Normal(new FullCopy437Api.CallResult(
                        new NormalReturn(returned,I+0xB2EE87L,pre,fresh),true),afterFirst);
            }
            equal(input.originCallSiteRva(),0xB2EE8EL);
            equal(input.entry().volatileBits(),change(returned,returned.raxBits(),
                    fresh.rbxBits(),fresh.rdiBits(),returned.r8Bits()));
            equal(input.entry().nonvolatileBits(),fresh);
            equal(input.directionFlagSet(),true);equal(input.mxcsr(),afterFirst);
            equal(m.peek(pre-8L),I+0xB2EE93L);
            VolatileBits inner=change(v(0x7700L),NEW,NEW,0L,0L);
            NonvolatileBits innerN=new NonvolatileBits(TB,0L,1L,NEW,4L,1L,
                    fresh.rbxBits(),fresh.rdiBits(),fresh.xmm6());
            exactStop[0]=new Stopped(StopReason.MISSING_POST_STATE,
                    new Snapshot(new Entry(I,pre-8L-0x48L,inner,innerN),0xB2EFADL,
                            false,new Mxcsr(0x80,0x80)),0,0xB2EFADL);
            return exactStop[0];
        };
        KnownEntryRegistry registry=new KnownEntryRegistry(blockedEntry(),moveSupplier,blockedEntry());
        Frame f=new Frame(new PostState240Api.Input(entry,false,before,0xB2EF18L),m,
                new NoStages(),(site,cursor,end)->{
                    equal(cursor,pre);equal(end,0L);equal(m.writes.size(),budgets[0]);
                    budgetSites.add(site);budgets[0]++;
                },frame->{throw new AssertionError("known route invoked opaque supplier");},registry,SWAP);
        f.recursive(0xB2EE82L);
        equal(known[0],1);equal(f.r.volatileBits(),returned);equal(f.r.nonvolatileBits(),fresh);
        equal(f.r.rsp,pre);equal(f.postStateContext().directionFlagSet(),true);
        equal(f.postStateContext().mxcsr(),afterFirst);
        f.r.rdx=f.r.rdi;f.r.rcx=f.r.rbx; // actual source argument-setting prefix before B2EE8E.
        Entry prefix=f.postStateContext().currentState();
        boolean transferred=false;
        try {
            f.recursive(0xB2EE8EL);
            afterStop[0]++;
            f.recursive(0xB2EE9BL); // must never be reached after the offered stop.
            m.readQword(OUTER_SLOT); // no fabricated outer epilogue/RET.
        } catch(StoppedTransfer transfer) {
            check(transfer.actual()==exactStop[0]);
            check(transfer.actual().snapshot()==exactStop[0].snapshot());
            equal(transfer.actual().originCallSiteRva(),0xB2EFADL);
            equal(transfer.actual().snapshot().instructionRva(),0xB2EFADL);
            equal(transfer.actual().snapshot().currentState().rspBits(),pre-8L-0x48L);
            equal(transfer.actual().snapshot().directionFlagSet(),false);
            equal(transfer.actual().snapshot().mxcsr(),new Mxcsr(0x80,0x80));
            transferred=true;
        }
        check(transferred);equal(afterStop[0],0);equal(known[0],2);equal(budgets[0],2);
        equal(budgetSites,List.of(0xB2EE82L,0xB2EE8EL));
        equal(m.writes,List.of(new Write(pre-8L,I+0xB2EE87L),new Write(pre-8L,I+0xB2EE93L)));
        equal(f.postStateContext().currentState(),prefix);
        equal(f.postStateContext().instructionRva(),0xB2EE8EL);
        equal(f.postStateContext().directionFlagSet(),true);equal(f.postStateContext().mxcsr(),afterFirst);
        check(m.reads.isEmpty()); // the synthetic supplier's peek did not count as a producer read.
    }

    private static void legacyConstructorKeeps185Ports() {
        long pre=0x8B60L;Ram m=new Ram();Entry entry=new Entry(I,pre,v(0x8800L),n(0x9900L));
        VolatileBits first=v(0xAA00L),second=v(0xBB00L);int[] scalar={0};
        Calls oldCalls=new Calls() {
            @Override public VolatileBits invoke(Call call) {
                int index=scalar[0]++;check(index<2);equal(call.rspBits(),pre);
                equal(call.nonvolatileBits(),entry.nonvolatileBits());equal(m.writes.size(),index+1);
                if(index==0) {
                    equal(call.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(call.callSiteRva(),0xB2EF9EL);
                    equal(call.targetBits(),ALLOC_TARGET);equal(call.volatileBits(),entry.volatileBits());
                    equal(m.peek(pre-8L),I+0xB2EFA1L);return first;
                }
                equal(call.kind(),TargetKind.DIRECT_RVA);equal(call.callSiteRva(),0xB2EFADL);
                equal(call.targetBits(),0x4226860L);equal(call.volatileBits(),first);
                equal(m.peek(pre-8L),I+0xB2EFB2L);return second;
            }
            @Override public NormalReturn tail(Tail transfer) {throw new AssertionError("unexpected legacy tail");}
            @Override public long readGsQword58() {throw new AssertionError("unexpected legacy GS");}
        };
        Frame old=new Frame(entry,m,oldCalls,null,(site,cursor,end)->{
            throw new AssertionError("opaque legacy protocol used recursive budget");
        },child->{throw new AssertionError("opaque legacy protocol invoked Self");});
        expectNoPostState(old);equal(m.writes.size(),0);
        old.indirect(0xB2EF9EL,ALLOC_TARGET);equal(old.r.volatileBits(),first);
        Transfer4Calls239.direct(old,0xB2EFADL,0x4226860L);
        equal(scalar[0],2);equal(old.r.volatileBits(),second);
        equal(old.r.nonvolatileBits(),entry.nonvolatileBits());equal(old.r.rsp,pre);
        equal(m.writes,List.of(new Write(pre-8L,I+0xB2EFA1L),new Write(pre-8L,I+0xB2EFB2L)));

        Ram recursiveRam=new Ram();Entry recursiveEntry=new Entry(I,pre,v(0xCC00L),n(0xDD00L));
        VolatileBits full=v(0xEE00L);NonvolatileBits actualN=n(0xFF00L);
        int[] selves={0},budgets={0};
        Frame legacyKnown=new Frame(recursiveEntry,recursiveRam,null,null,(site,cursor,end)->{
            equal(site,0xB2EF18L);equal(cursor,pre);equal(end,0L);
            equal(recursiveRam.writes.size(),0);budgets[0]++;
        },child->{
            equal(child.rspBits(),pre-8L);equal(child.volatileBits(),recursiveEntry.volatileBits());
            equal(child.nonvolatileBits(),recursiveEntry.nonvolatileBits());
            equal(recursiveRam.writes,List.of(new Write(pre-8L,I+0xB2EF1DL)));selves[0]++;
            return new NormalReturn(full,I+0xB2EF1DL,pre,actualN);
        });
        expectNoPostState(legacyKnown);legacyKnown.recursive(0xB2EF18L);
        equal(selves[0],1);equal(budgets[0],1);equal(legacyKnown.r.volatileBits(),full);
        equal(legacyKnown.r.nonvolatileBits(),actualN);equal(legacyKnown.r.rsp,pre);
        equal(recursiveRam.writes,List.of(new Write(pre-8L,I+0xB2EF1DL)));
    }

    private static Normal normal(CallFrame frame,VolatileBits v,NonvolatileBits n,boolean df,Mxcsr mx) {
        return new Normal(new FullCopy437Api.CallResult(
                new NormalReturn(v,frame.returnRipBits(),frame.call().rspBits(),n),df),mx);
    }
    private static KnownEntryRegistry blockedRegistry() {
        return new KnownEntryRegistry(blockedEntry(),blockedEntry(),blockedEntry());
    }
    private static EntryExecutor blockedEntry() {
        return (input,memory)->{throw new AssertionError("unexpected known supplier");};
    }
    private static void expectNoPostState(Frame frame) {
        boolean absent=false;
        try {frame.postStateContext();}catch(NullPointerException expected) {absent=true;}
        check(absent);
    }
    private static NonvolatileBits withRdi(NonvolatileBits n,long rdi) {
        return new NonvolatileBits(n.rbxBits(),n.rbpBits(),n.rsiBits(),rdi,n.r12Bits(),
                n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static Bits128 x(long t) {return new Bits128(0x8000000000000000L|t,0xF000000000000000L|t);}
    private static VolatileBits v(long t) {
        return new VolatileBits(t+1L,t+2L,t+3L,0x8000000000000000L|t+8L,
                0xF000000000000000L|t+9L,t+10L,t+11L,
                x(t+16L),x(t+32L),x(t+48L),x(t+64L),x(t+80L),x(t+96L));
    }
    private static NonvolatileBits n(long t) {
        return new NonvolatileBits(0x8100000000000000L|t+1L,0x8200000000000000L|t+2L,
                0x8300000000000000L|t+3L,0x8400000000000000L|t+4L,0xF500000100000000L|t+5L,
                0x8600000000000000L|t+6L,0x8700000000000000L|t+7L,0x8800000000000000L|t+8L,x(t+144L));
    }
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long r8) {
        return new VolatileBits(a,c,d,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits rax(VolatileBits v,long a) {
        return change(v,a,v.rcxBits(),v.rdxBits(),v.r8Bits());
    }
    private static final class NoStages implements FloatingStages {
        @Override public VectorResult convertSignedDwords(FpFrame frame) {throw new AssertionError("no FP in protocol");}
        @Override public VectorResult multiplyLowSingle(FpFrame frame,int raw) {throw new AssertionError("no FP in protocol");}
        @Override public IntegerResult truncateLowSingle(FpFrame frame) {throw new AssertionError("no FP in protocol");}
    }
    private record Write(long address,long value) { }
    private static final class Ram implements Memory {
        private final Map<Long,Integer> data=new HashMap<>();
        final List<Write> writes=new ArrayList<>();final List<Long> reads=new ArrayList<>();
        void poke(long a,long value) {for(int j=0;j<8;j++)data.put(a+j,(int)(value>>>(j*8))&255);}
        void poke32(long a,int value) {for(int j=0;j<4;j++)data.put(a+j,(value>>>(j*8))&255);}
        int byteAt(long a) {
            Integer b=data.get(a);if(b==null)throw new UnsupportedOperationException("unheldFrame241 "+Long.toHexString(a));
            return b;
        }
        long peek(long a) {long v=0L;for(int j=0;j<8;j++)v|=(long)byteAt(a+j)<<(j*8);return v;}
        @Override public long readQword(long a) {reads.add(a);return peek(a);}
        @Override public void writeQword(long a,long v) {writes.add(new Write(a,v));poke(a,v);}
        @Override public int readDword(long a) {reads.add(a);int v=0;for(int j=0;j<4;j++)v|=byteAt(a+j)<<(j*8);return v;}
        @Override public int readUnsignedByte(long a) {reads.add(a);return byteAt(a);}
        @Override public void writeDword(long a,int v) {throw new AssertionError("no DWORD write in Frame protocol");}
        @Override public void writeByte(long a,int v) {throw new AssertionError("no byte write in Frame protocol");}
        @Override public Bits128 read128(long a) {return new Bits128(readQword(a),readQword(a+8L));}
        @Override public void write128(long a,Bits128 v) {throw new AssertionError("no vector write in Frame protocol");}
        @Override public int lockedXaddDword(long a,int addend) {throw new AssertionError("no atomic in Frame protocol");}
    }
    private static void equal(Object actual,Object expected) {
        checks++;if(!java.util.Objects.equals(actual,expected))
            throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);
    }
    private static void check(boolean condition) {
        checks++;if(!condition)throw new AssertionError("check="+checks);
    }
}
