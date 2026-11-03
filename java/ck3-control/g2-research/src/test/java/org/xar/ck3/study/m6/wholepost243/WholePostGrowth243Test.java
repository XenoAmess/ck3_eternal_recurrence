package org.xar.ck3.study.m6.wholepost243;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Budget;
import org.xar.ck3.study.m6.postentry242.WholeTransferPostState242;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api.FloatingStages;
import org.xar.ck3.study.m6.poststate240.PostState240Api.FpFrame;
import org.xar.ck3.study.m6.poststate240.PostState240Api.IntegerCompleted;
import org.xar.ck3.study.m6.poststate240.PostState240Api.IntegerResult;
import org.xar.ck3.study.m6.poststate240.PostState240Api.StageStopped;
import org.xar.ck3.study.m6.poststate240.PostState240Api.VectorCompleted;
import org.xar.ck3.study.m6.poststate240.PostState240Api.VectorResult;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate243.OpaqueSseOutcomeProvider243;

/** Two NEW whole-Outcome fixtures; no legacy NR adapter, host FP or actual child algorithm. */
public final class WholePostGrowth243Test {
    private static final long I=0x140000000L,S=0xA008L,F=S-0x48L;
    private static final long D=0x2000L,T=0x3000L,A=0x4000L,B=0x5000L;
    private static final long DB=0x6000L,TB=0x7000L,NEW=0x8000L,TABLE=0xB000L;
    private static final long ALLOC_TARGET=0xF243001L,FREE_TARGET=0xF243002L;
    private static final long ORIGIN=0x3729620L,RET=0xAA00112233445566L,NEW_RET=0xBB66778899AABBCCL;
    private static final long CALL_GUARD=0xCCDDEEFF12345678L,NEW_R12=0xF123456789ABCDEFL;
    private static final int LITERAL=0x3FC00000,DATA=0x77665544;
    private static final Bits128 ZERO=new Bits128(0,0);
    // Explicit owned fixture: underlying sticky Precision was already set, initially unknown.
    // These successive records reveal knowledge; zero arithmetic is not claimed to raise it.
    private static final Mxcsr PRE=new Mxcsr(0x1F80,0xFFC0);
    private static final Mxcsr FP1=new Mxcsr(0x1FA0,0xFFE0);
    private static final Mxcsr FP2=new Mxcsr(0x1FA0,0xFFE1);
    private static final Mxcsr FP3=Mxcsr.exact(0x1FA0);
    private static final Mxcsr[] CHILD_POST={Mxcsr.exact(0x3FA1),Mxcsr.exact(0x5FA2),
            Mxcsr.exact(0x7FA4),Mxcsr.exact(0x1FA8),Mxcsr.exact(0x9F90)};
    private static final boolean[] CHILD_DF={false,true,false,true,false};
    private static final long[] SITES={0xB2EF9EL,0xB2EFADL,0xB2EFBBL,0xB2EFD2L,0xB2EFE5L};
    private static int scenes,checks;
    private WholePostGrowth243Test() { }

    public static void main(String[] args) {
        if(args.length==0) { normal();stopped(); }
        else if(args.length==1 && args[0].equals("normal")) normal();
        else if(args.length==1 && args[0].equals("stopped")) stopped();
        else throw new IllegalArgumentException("expected normal, stopped or no selector");
        System.out.println("PASS newWholePostScenes="+scenes+" checks="+checks
                +" actualTypedWholeDispatcher=true oldCasesRepeated=false"
                +" controlledStageAndChildEffectsOnly=true hardwareFP=false Native=false Game=false");
    }

    private static void normal() {
        Ram ram=ram();Script script=new Script(false);int[] childCalls={0},budgets={0};
        VolatileBits[] children={rax(v(0xC100),NEW),v(0xC200),v(0xC300),v(0xC400),v(0xC500)};
        CallOutcome242Api.OutcomePort opaque=frame->{
            int index=childCalls[0]++;
            check(index<5);Call call=frame.call();long site=SITES[index];
            equal(frame.ownerEntryRva(),0xB2EEE0L);equal(call.callSiteRva(),site);
            equal(frame.imageBaseBits(),I);equal(call.rspBits(),F);equal(frame.childEntry().rspBits(),F-8);
            equal(frame.childEntry().volatileBits(),call.volatileBits());
            equal(frame.childEntry().nonvolatileBits(),call.nonvolatileBits());
            equal(frame.normalRule(),CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N);
            int length=index==0||index==4?3:5;
            equal(frame.instructionLength(),length);equal(frame.returnRipBits(),I+site+length);
            equal(ram.peekQ(F-8),frame.returnRipBits());
            equal(frame.preDirectionFlagSet(),index==0?true:CHILD_DF[index-1]);
            equal(frame.preMxcsr(),index==0?FP3:CHILD_POST[index-1]);
            VolatileBits actual=call.volatileBits();
            equal(actual.r9Bits(),index==0?incoming().r9Bits():children[index-1].r9Bits());
            equal(actual.xmm0(),index==0?ZERO:children[index-1].xmm0());
            if(index==0) {
                equal(call.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(call.targetBits(),ALLOC_TARGET);
                equal(actual.raxBits(),TABLE);equal(actual.rcxBits(),A);equal(actual.rdxBits(),4L);equal(actual.r8Bits(),4L);
                equal(call.nonvolatileBits().rsiBits(),1L);equal(call.nonvolatileBits().r12Bits(),4L);
            } else if(index==4) {
                equal(call.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(call.targetBits(),FREE_TARGET);
                equal(actual.raxBits(),TABLE);equal(actual.rcxBits(),A);equal(actual.rdxBits(),DB);equal(actual.r8Bits(),4L);
                ram.writeQword(F+0x28,NEW_R12);ram.writeQword(S,NEW_RET);
            } else {
                equal(call.kind(),TargetKind.DIRECT_RVA);equal(call.targetBits(),0x4226860L);
                equal(actual.rcxBits(),index==3?NEW+4:NEW);
                equal(actual.rdxBits(),index==2?TB:DB);equal(actual.r8Bits(),index==2?4L:0L);
                if(index==2)ram.writeDword(NEW,DATA); // explicit fixture effect; no COPY algorithm
            }
            NormalReturn nr=new NormalReturn(children[index],frame.returnRipBits(),call.rspBits(),call.nonvolatileBits());
            return new Normal(new FullCopy437Api.CallResult(nr,CHILD_DF[index]),CHILD_POST[index]);
        };
        WholeTransferPostState242 whole=new WholeTransferPostState242(
                new OpaqueSseOutcomeProvider243(script),budget(budgets),opaque);
        Outcome outcome=whole.move4(input(),ram);
        check(outcome instanceof Normal);Normal actual=(Normal)outcome;
        equal(script.calls,3);equal(childCalls[0],5);equal(budgets[0],1);
        equal(actual.postMxcsr(),CHILD_POST[4]);equal(actual.base().postDirectionFlagSet(),false);
        check(!actual.postMxcsr().equals(PRE));check(actual.base().postDirectionFlagSet()!=input().directionFlagSet());
        NormalReturn nr=actual.base().normalReturn();
        equal(nr.volatileBits(),rax(children[4],D));equal(nr.nonvolatileBits(),withR12(nonvolatile(),NEW_R12));
        equal(nr.returnRipBits(),NEW_RET);equal(nr.callerRspBits(),S+8);
        equal(ram.peekQ(D),NEW);equal(ram.peekD(D+0xC),1);equal(ram.peekD(D+8),1);
        equal(ram.peekD(T+0xC),0);equal(ram.peekQ(T),TB);equal(ram.peekD(NEW),DATA);
        equal(ram.reads.stream().filter(a->a.equals(new Access("R",8,S))).count(),1L);
        equal(ram.writes.stream().filter(a->a.equals(new Access("W",8,F-8))).count(),5L);
        scenes++;System.out.println("PASS actualB2WholeNormalPostStateChain");
    }

    private static void stopped() {
        Ram ram=ram();Script script=new Script(true);int[] childCalls={0},budgets={0};
        CallOutcome242Api.OutcomePort noCalls=frame->{childCalls[0]++;throw new AssertionError("allocator/COPY/free after stage2 stop");};
        WholeTransferPostState242 whole=new WholeTransferPostState242(
                new OpaqueSseOutcomeProvider243(script),budget(budgets),noCalls);
        Outcome outcome=whole.move4(input(),ram);
        check(outcome instanceof Stopped);check(outcome==script.stopped);
        Stopped actual=(Stopped)outcome;
        equal(script.calls,2);equal(childCalls[0],0);equal(budgets[0],1);
        equal(actual.reason(),StopReason.UNSUPPORTED_FP_DOMAIN);equal(actual.raisedConditionBits(),0);
        equal(actual.originCallSiteRva(),ORIGIN);equal(actual.snapshot().instructionRva(),0xB2EF83L);
        equal(actual.snapshot().mxcsr(),FP1);equal(actual.snapshot().directionFlagSet(),true);
        equal(actual.snapshot().currentState(),expectedStage2());
        check(!actual.snapshot().mxcsr().equals(PRE));
        equal(ram.peekQ(F-8),CALL_GUARD);equal(ram.peekQ(S),RET);
        equal(ram.peekQ(D),DB);equal(ram.peekD(D+8),0);equal(ram.peekD(D+0xC),0);
        equal(ram.peekD(T+0xC),1);equal(ram.peekQ(T),TB);
        check(!ram.reads.contains(new Access("R",8,S)));
        check(!ram.reads.contains(new Access("R",8,A)));
        check(!ram.reads.contains(new Access("R",8,TABLE+8)));
        equal(ram.reads.stream().filter(a->a.equals(new Access("R",4,I+0x49F64F0L))).count(),1L);
        equal(ram.writes,List.of(new Access("W",8,S-8),new Access("W",8,S-0x10),
                new Access("W",8,S-0x18),new Access("W",8,F+0x50),new Access("W",4,D+0xC),
                new Access("W",8,F+0x28),new Access("W",8,F+0x58),
                new Access("W",8,F+0x60),new Access("W",8,F+0x20)));
        scenes++;System.out.println("PASS actualB2WholeTypedStage2StopCurrentPostCvtSnapshot");
    }

    private static final class Script implements FloatingStages {
        final boolean stopAtMultiply;int calls;Stopped stopped;
        Script(boolean stopAtMultiply){this.stopAtMultiply=stopAtMultiply;}
        @Override public VectorResult convertSignedDwords(FpFrame frame) {
            equal(calls++,0);base(frame,0xB2EF7DL,PRE);
            equal(frame.before().currentState().volatileBits().xmm0(),ZERO);
            equal(frame.before().currentState().volatileBits().r8Bits(),4L);
            equal(frame.before().currentState().nonvolatileBits().rsiBits(),nonvolatile().rsiBits());
            return new VectorCompleted(ZERO,true,FP1);
        }
        @Override public VectorResult multiplyLowSingle(FpFrame frame,int multiplierRaw32) {
            equal(calls++,1);base(frame,0xB2EF83L,FP1);equal(multiplierRaw32,LITERAL);
            equal(frame.before().currentState(),expectedStage2());
            if(stopAtMultiply) {
                StageStopped offered=OpaqueSseOutcomeProvider243.beforeOperation(frame,StopReason.UNSUPPORTED_FP_DOMAIN);
                stopped=offered.actual();return offered;
            }
            return new VectorCompleted(ZERO,true,FP2);
        }
        @Override public IntegerResult truncateLowSingle(FpFrame frame) {
            equal(calls++,2);check(!stopAtMultiply);base(frame,0xB2EF8BL,FP2);
            equal(frame.before().currentState(),expectedStage2());
            return new IntegerCompleted(0,true,FP3);
        }
        private static void base(FpFrame frame,long site,Mxcsr before) {
            equal(frame.originCallSiteRva(),ORIGIN);equal(frame.before().instructionRva(),site);
            equal(frame.before().currentState().imageBaseBits(),I);equal(frame.before().currentState().rspBits(),F);
            equal(frame.before().directionFlagSet(),true);equal(frame.before().mxcsr(),before);
        }
    }

    private static Entry expectedStage2() {
        VolatileBits v=incoming();NonvolatileBits n=nonvolatile();
        return new Entry(I,F,new VolatileBits(0L,A,T,4L,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                ZERO,v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5()),
                new NonvolatileBits(TB,0L,1L,n.rdiBits(),4L,1L,D,T,n.xmm6()));
    }
    private static Budget budget(int[] count) {
        return (site,cursor,end)->{equal(++count[0],1);equal(site,0xB2EEE0L);equal(cursor,S);equal(end,0L);};
    }
    private static PostState240Api.Input input(){return new PostState240Api.Input(new Entry(I,S,incoming(),nonvolatile()),true,PRE,ORIGIN);}
    private static Ram ram() {
        Ram ram=new Ram();ram.seedQ(S,RET);ram.seedQ(F-8,CALL_GUARD);
        ram.seedQ(D,DB);ram.seedD(D+8,0);ram.seedD(D+0xC,9);ram.seedQ(D+0x10,A);
        ram.seedQ(T,TB);ram.seedD(T+8,5);ram.seedD(T+0xC,1);ram.seedQ(T+0x10,B);
        ram.seedQ(A,TABLE);ram.seedQ(TABLE+8,ALLOC_TARGET);ram.seedQ(TABLE+0x10,FREE_TARGET);
        ram.seedD(I+0x49F64F0L,LITERAL);ram.seedD(TB,DATA);ram.seedD(DB,0x01020304);
        return ram;
    }
    private record Access(String kind,int width,long address) { }
    private static final class Ram implements Memory {
        final Map<Long,Integer> bytes=new HashMap<>();final List<Access> reads=new ArrayList<>(),writes=new ArrayList<>();
        void seedQ(long a,long value){put(a,value,8);}
        void seedD(long a,int value){put(a,Integer.toUnsignedLong(value),4);}
        void put(long a,long value,int width){for(int j=0;j<width;j++)bytes.put(a+j,(int)(value>>>(j*8))&255);}
        long peek(long a,int width){long value=0;for(int j=0;j<width;j++){Integer b=bytes.get(a+j);if(b==null)throw new AssertionError("unheldRAM "+Long.toHexString(a+j));value|=(long)b<<(j*8);}return value;}
        long peekQ(long a){return peek(a,8);}int peekD(long a){return (int)peek(a,4);}
        @Override public long readQword(long a){reads.add(new Access("R",8,a));return peekQ(a);}
        @Override public int readDword(long a){reads.add(new Access("R",4,a));return peekD(a);}
        @Override public void writeQword(long a,long value){writes.add(new Access("W",8,a));seedQ(a,value);}
        @Override public void writeDword(long a,int value){writes.add(new Access("W",4,a));seedD(a,value);}
        @Override public int readUnsignedByte(long a){throw new AssertionError("unexpectedBYTE");}
        @Override public void writeByte(long a,int value){throw new AssertionError("unexpectedBYTEwrite");}
        @Override public Bits128 read128(long a){throw new AssertionError("unexpected128read");}
        @Override public void write128(long a,Bits128 value){throw new AssertionError("unexpected128write");}
        @Override public int lockedXaddDword(long a,int delta){throw new AssertionError("unexpectedATOMIC");}
    }
    private static Bits128 x(long tag){return new Bits128(0x8000000000000000L|tag,0xF000000000000000L|tag);}
    private static VolatileBits v(long tag){return new VolatileBits(0x8100000000000000L|tag+1,0x8200000000000000L|tag+2,0x8300000000000000L|tag+3,0x8800000000000000L|tag+8,0x8900000000000000L|tag+9,0x8A00000000000000L|tag+10,0x8B00000000000000L|tag+11,x(tag+16),x(tag+32),x(tag+48),x(tag+64),x(tag+80),x(tag+96));}
    private static VolatileBits incoming(){VolatileBits v=v(0x100);return new VolatileBits(v.raxBits(),D,T,0x8000000000000038L,0xF000000000000009L,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static NonvolatileBits nonvolatile(){return new NonvolatileBits(0x91000000000000B1L,0x92000000000000B2L,0x93000000000000B3L,0x94000000000000B4L,0xF000000100000005L,0x96000000000000B6L,0x97000000000000B7L,0x98000000000000B8L,x(0xB9));}
    private static NonvolatileBits withR12(NonvolatileBits n,long r12){return new NonvolatileBits(n.rbxBits(),n.rbpBits(),n.rsiBits(),n.rdiBits(),r12,n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static VolatileBits rax(VolatileBits v,long rax){return new VolatileBits(rax,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static void check(boolean condition){checks++;if(!condition)throw new AssertionError("check="+checks);}
    private static void equal(Object actual,Object expected){checks++;if(!Objects.equals(actual,expected))throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);}
}
