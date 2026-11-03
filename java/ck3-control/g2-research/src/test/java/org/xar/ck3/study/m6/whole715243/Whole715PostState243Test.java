package org.xar.ck3.study.m6.whole715243;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
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
import org.xar.ck3.study.m6.poststate240.PostState240Api.VectorCompleted;
import org.xar.ck3.study.m6.poststate240.PostState240Api.VectorResult;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate243.OpaqueSseOutcomeProvider243;

/** Two new whole715 cases. The real source body performs the16-byte copy, not this fixture. */
public final class Whole715PostState243Test {
    private static final long I=0x140000000L,S=0xC008L,F=S-0x478L;
    private static final long D=0x2000L,T=0x3000L,A=0x4000L,B=0x5000L;
    private static final long DB=0x6000L,TB=0x7000L,NEW=0x8000L,TABLE=0xA000L;
    private static final long ALLOC_TARGET=0xF715001L,FREE_TARGET=0xF715002L;
    private static final long ORIGIN=0x37295FBL,RET=0xA171522334455667L,CALL_GUARD=0xD17158899AABBCCDL;
    private static final int LITERAL=0x3FC00000; // Parent-required1.5f rawbits; neverchanged.
    private static final Bits128 ZERO=new Bits128(0,0);
    private static final Bits128 DATA=new Bits128(0xD1C2B3A495867768L,0x1021324354657687L);
    private static final Bits128 OLD=new Bits128(0x0123456789ABCDEFL,0x8899AABBCCDDEEFFL);
    private static final Bits128 NEW_BEFORE=new Bits128(0xCCBBAA9988776655L,0x4433221100FFEEDDL);
    private static final Bits128 ALLOC_XMM=new Bits128(0xA110CA7E12345678L,0xB110CA7E87654321L);
    // Explicit owned underlying5F82 has pre-existing sticky Denormal, initially not known.
    private static final Mxcsr PRE=new Mxcsr(0x5F80,0xFFC0);
    private static final Mxcsr FP1=new Mxcsr(0x5F82,0xFFC2),FP2=new Mxcsr(0x5F82,0xFFE2);
    private static final Mxcsr FP3=Mxcsr.exact(0x5F82),ALLOC_FP=Mxcsr.exact(0x7FA1),FREE_FP=Mxcsr.exact(0xBF84);
    private static int scenes,checks;
    private Whole715PostState243Test() { }

    public static void main(String[] args) {
        if(args.length==0){normal16();literalFault();}
        else if(args.length==1 && args[0].equals("normal16"))normal16();
        else if(args.length==1 && args[0].equals("literalFault"))literalFault();
        else throw new IllegalArgumentException("expected normal16, literalFault or no selector");
        System.out.println("PASS new715WholeScenes="+scenes+" checks="+checks
                +" actualSourceMOV128=true ordinaryMemoryErrorNotTypedStop=true"
                +" oldCasesRepeated=false controlledFPAndChildPortsOnly=true hardwareFP=false Native=false Game=false");
    }

    private static void normal16() {
        Ram ram=ram(null);Script stages=new Script(false);int[] calls={0},budgets={0,0};
        VolatileBits allocated=x0(rax(v(0x715100),NEW),ALLOC_XMM);
        VolatileBits freed=x0(v(0x715200),DATA);
        CallOutcome242Api.OutcomePort opaque=frame->{
            int index=calls[0]++;check(index<2);Call call=frame.call();
            long site=index==0?0x21A51B9L:0x21A5223L;
            equal(frame.ownerEntryRva(),0x21A5050L);equal(call.callSiteRva(),site);
            equal(call.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(frame.instructionLength(),3);
            equal(call.targetBits(),index==0?ALLOC_TARGET:FREE_TARGET);
            equal(call.rspBits(),F);equal(frame.childEntry().rspBits(),F-8);
            equal(frame.returnRipBits(),I+site+3);equal(ram.peekQ(F-8),I+site+3);
            equal(frame.childEntry().volatileBits(),call.volatileBits());
            equal(frame.childEntry().nonvolatileBits(),call.nonvolatileBits());
            equal(frame.normalRule(),CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N);
            equal(frame.preDirectionFlagSet(),index==0);equal(frame.preMxcsr(),index==0?FP3:ALLOC_FP);
            equal(call.volatileBits().raxBits(),TABLE);equal(call.volatileBits().rcxBits(),A);
            equal(call.volatileBits().rdxBits(),index==0?16L:DB);equal(call.volatileBits().r8Bits(),8L);
            equal(call.volatileBits().r9Bits(),index==0?incoming().r9Bits():allocated.r9Bits());
            equal(call.volatileBits().xmm0(),index==0?ZERO:DATA);
            if(index==0) {
                equal(call.nonvolatileBits().r13Bits(),1L);equal(call.nonvolatileBits().r15Bits(),1L);
                equal(ram.peek128(NEW),NEW_BEFORE);
            } else {
                equal(ram.peek128(NEW),DATA);equal(ram.peek128(TB),DATA);
                equal(ram.reads.stream().filter(a->a.equals(new Access("R",16,TB))).count(),1L);
                equal(ram.writes.stream().filter(a->a.equals(new Access("W",16,NEW))).count(),1L);
                equal(call.volatileBits().xmm1(),allocated.xmm1());
                equal(call.nonvolatileBits().rbxBits(),TB+16);
                equal(call.nonvolatileBits().r12Bits(),NEW);
            }
            VolatileBits result=index==0?allocated:freed;
            NormalReturn returned=new NormalReturn(result,frame.returnRipBits(),call.rspBits(),call.nonvolatileBits());
            return new Normal(new FullCopy437Api.CallResult(returned,index!=0),index==0?ALLOC_FP:FREE_FP);
        };
        WholeTransferPostState242 whole=new WholeTransferPostState242(new OpaqueSseOutcomeProvider243(stages),
                budget(budgets,true),opaque);
        Outcome outcome=whole.transfer715(input(),ram);
        check(outcome instanceof Normal);Normal actual=(Normal)outcome;NormalReturn nr=actual.base().normalReturn();
        equal(stages.calls,3);equal(calls[0],2);equal(budgets[0],1);equal(budgets[1],1);
        equal(actual.base().postDirectionFlagSet(),true);equal(actual.postMxcsr(),FREE_FP);
        check(!actual.postMxcsr().equals(PRE));check(!actual.postMxcsr().equals(FP3));check(!actual.postMxcsr().equals(ALLOC_FP));
        equal(nr.volatileBits(),raxR11(freed,D,S-0x28));equal(nr.volatileBits().xmm0(),DATA);
        check(!nr.volatileBits().xmm0().equals(ZERO));check(!nr.volatileBits().xmm0().equals(ALLOC_XMM));
        equal(nr.nonvolatileBits(),nonvolatile());equal(nr.returnRipBits(),RET);equal(nr.callerRspBits(),S+8);
        equal(ram.peek128(NEW),DATA);equal(ram.peek128(TB),DATA);equal(ram.peek128(DB),OLD);
        equal(ram.peekQ(D),NEW);equal(ram.peekD(D+0xC),1);equal(ram.peekD(D+8),1);
        equal(ram.peekD(T+0xC),0);equal(ram.peekQ(T),TB);
        equal(ram.reads.stream().filter(a->a.equals(new Access("R",16,TB))).count(),1L);
        equal(ram.writes.stream().filter(a->a.equals(new Access("W",16,NEW))).count(),1L);
        equal(ram.reads.stream().filter(a->a.equals(new Access("R",4,I+0x49F64F0L))).count(),1L);
        equal(ram.reads.stream().filter(a->a.equals(new Access("R",8,S))).count(),1L);
        equal(ram.writes.stream().filter(a->a.equals(new Access("W",8,F-8))).count(),2L);
        scenes++;System.out.println("PASS actual715WholePositiveOneMOV128PostLastChild");
    }

    private static void literalFault() {
        IllegalStateException original=new IllegalStateException("ordinary715literalMemoryPortFailure");
        Ram ram=ram(original);Script stages=new Script(true);int[] calls={0},budgets={0,0};
        CallOutcome242Api.OutcomePort noCalls=frame->{calls[0]++;throw new AssertionError("allocator/free afterliteralMemoryfailure");};
        WholeTransferPostState242 whole=new WholeTransferPostState242(new OpaqueSseOutcomeProvider243(stages),
                budget(budgets,false),noCalls);
        try {
            Outcome invented=whole.transfer715(input(),ram);
            throw new AssertionError("ordinaryMemoryfailure converted toOutcome "+invented);
        } catch(RuntimeException failure) {
            check(failure==original);check(!(failure instanceof PostState240Api.StoppedTransfer));
        }
        equal(stages.calls,1);check(stages.cvtReturned);equal(calls[0],0);
        equal(budgets[0],1);equal(budgets[1],0);
        equal(stages.cvtInput.before().instructionRva(),0x21A5192L);
        equal(stages.cvtInput.before().mxcsr(),PRE);
        // Internal post-CVT Context is not exposed by this raw failure. Its commit/marker order
        // is source-proved from the pinned Frame/growth body, not invented as a runtime Snapshot.
        equal(ram.reads.stream().filter(a->a.equals(new Access("R",4,I+0x49F64F0L))).count(),1L);
        equal(ram.peekQ(F-8),CALL_GUARD);equal(ram.peekQ(S),RET);
        equal(ram.peekQ(D),DB);equal(ram.peekD(D+8),0);equal(ram.peekD(D+0xC),0);
        equal(ram.peekD(T+0xC),1);equal(ram.peek128(NEW),NEW_BEFORE);equal(ram.peek128(TB),DATA);
        check(!ram.reads.contains(new Access("R",8,S)));check(!ram.reads.contains(new Access("R",8,A)));
        check(ram.reads.stream().noneMatch(a->a.width()==16));check(ram.writes.stream().noneMatch(a->a.width()==16));
        equal(ram.writes,List.of(new Access("W",8,S+8),new Access("W",8,S+0x10),
                new Access("W",8,S+0x18),new Access("W",8,S-8),new Access("W",8,S-0x10),
                new Access("W",8,S-0x18),new Access("W",8,S-0x20),new Access("W",8,S-0x28),
                new Access("W",4,D+0xC)));
        equal(ram.peekQ(S+8),nonvolatile().rbxBits());equal(ram.peekQ(S+0x10),nonvolatile().rbpBits());
        equal(ram.peekQ(S+0x18),nonvolatile().rsiBits());
        scenes++;System.out.println("PASS actual715WholeLiteralMemoryExceptionIdentityNoTypedStop");
    }

    private static final class Script implements FloatingStages {
        final boolean literalWillFail;int calls;boolean cvtReturned;FpFrame cvtInput;
        Script(boolean literalWillFail){this.literalWillFail=literalWillFail;}
        @Override public VectorResult convertSignedDwords(FpFrame frame) {
            equal(calls++,0);base(frame,0x21A5192L,PRE);equal(frame.before().currentState(),beforeCvt());
            cvtInput=frame;cvtReturned=true;return new VectorCompleted(ZERO,true,FP1);
        }
        @Override public VectorResult multiplyLowSingle(FpFrame frame,int multiplierRaw32) {
            check(!literalWillFail);equal(calls++,1);base(frame,0x21A5195L,FP1);
            equal(frame.before().currentState(),beforeCvt());equal(multiplierRaw32,LITERAL);
            return new VectorCompleted(ZERO,true,FP2);
        }
        @Override public IntegerResult truncateLowSingle(FpFrame frame) {
            check(!literalWillFail);equal(calls++,2);base(frame,0x21A519DL,FP2);
            equal(frame.before().currentState(),beforeCvt());return new IntegerCompleted(0,true,FP3);
        }
        private static void base(FpFrame frame,long site,Mxcsr before) {
            equal(frame.originCallSiteRva(),ORIGIN);equal(frame.before().instructionRva(),site);
            equal(frame.before().directionFlagSet(),true);equal(frame.before().mxcsr(),before);
            equal(frame.before().currentState().imageBaseBits(),I);equal(frame.before().currentState().rspBits(),F);
        }
    }

    private static Entry beforeCvt() {
        VolatileBits v=incoming();NonvolatileBits n=nonvolatile();
        return new Entry(I,F,new VolatileBits(0L,A,T,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                ZERO,v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5()),
                new NonvolatileBits(TB,0L,D,TB+16,n.r12Bits(),n.r13Bits(),T,1L,n.xmm6()));
    }
    private static Budget budget(int[] count,boolean allowCopy) {
        return (site,cursor,end)->{
            if(site==0x21A5050L){equal(++count[0],1);equal(cursor,S);equal(end,0L);}
            else {check(allowCopy);equal(site,0x21A51D0L);equal(++count[1],1);equal(cursor,TB);equal(end,TB+16);}
        };
    }
    private static PostState240Api.Input input(){return new PostState240Api.Input(new Entry(I,S,incoming(),nonvolatile()),true,PRE,ORIGIN);}
    private static Ram ram(RuntimeException literalFailure) {
        Ram ram=new Ram(literalFailure);ram.seedQ(S,RET);ram.seedQ(F-8,CALL_GUARD);
        ram.seedQ(D,DB);ram.seedD(D+8,0);ram.seedD(D+0xC,9);ram.seedQ(D+0x10,A);
        ram.seedQ(T,TB);ram.seedD(T+8,5);ram.seedD(T+0xC,1);ram.seedQ(T+0x10,B);
        ram.seedQ(A,TABLE);ram.seedQ(TABLE+8,ALLOC_TARGET);ram.seedQ(TABLE+0x10,FREE_TARGET);
        ram.seedD(I+0x49F64F0L,LITERAL);ram.seed128(TB,DATA);ram.seed128(DB,OLD);ram.seed128(NEW,NEW_BEFORE);
        return ram;
    }
    private record Access(String kind,int width,long address) { }
    private static final class Ram implements Memory {
        final RuntimeException literalFailure;final Map<Long,Integer> bytes=new HashMap<>();
        final List<Access> reads=new ArrayList<>(),writes=new ArrayList<>();
        Ram(RuntimeException literalFailure){this.literalFailure=literalFailure;}
        void put(long a,long value,int width){for(int j=0;j<width;j++)bytes.put(a+j,(int)(value>>>(j*8))&255);}
        void seedQ(long a,long value){put(a,value,8);}void seedD(long a,int value){put(a,Integer.toUnsignedLong(value),4);}
        void seed128(long a,Bits128 value){seedQ(a,value.lowBits());seedQ(a+8,value.highBits());}
        long peek(long a,int width){long value=0;for(int j=0;j<width;j++){Integer b=bytes.get(a+j);if(b==null)throw new AssertionError("unheld715RAM "+Long.toHexString(a+j));value|=(long)b<<(j*8);}return value;}
        long peekQ(long a){return peek(a,8);}int peekD(long a){return (int)peek(a,4);}
        Bits128 peek128(long a){return new Bits128(peekQ(a),peekQ(a+8));}
        @Override public long readQword(long a){reads.add(new Access("R",8,a));return peekQ(a);}
        @Override public int readDword(long a){reads.add(new Access("R",4,a));if(a==I+0x49F64F0L&&literalFailure!=null)throw literalFailure;return peekD(a);}
        @Override public Bits128 read128(long a){reads.add(new Access("R",16,a));return peek128(a);}
        @Override public void writeQword(long a,long value){writes.add(new Access("W",8,a));seedQ(a,value);}
        @Override public void writeDword(long a,int value){writes.add(new Access("W",4,a));seedD(a,value);}
        @Override public void write128(long a,Bits128 value){writes.add(new Access("W",16,a));seed128(a,value);}
        @Override public int readUnsignedByte(long a){throw new AssertionError("unexpected715BYTE");}
        @Override public void writeByte(long a,int value){throw new AssertionError("unexpected715BYTEwrite");}
        @Override public int lockedXaddDword(long a,int delta){throw new AssertionError("unexpected715ATOMIC");}
    }
    private static Bits128 x(long tag){return new Bits128(0x8000000000000000L|tag,0xF000000000000000L|tag);}
    private static VolatileBits v(long tag){return new VolatileBits(0x8100000000000000L|(tag+1),0x8200000000000000L|(tag+2),0x8300000000000000L|(tag+3),0x8800000000000000L|(tag+8),0x8900000000000000L|(tag+9),0x8A00000000000000L|(tag+10),0x8B00000000000000L|(tag+11),x(tag+16),x(tag+32),x(tag+48),x(tag+64),x(tag+80),x(tag+96));}
    private static VolatileBits incoming(){VolatileBits v=v(0x715);return new VolatileBits(v.raxBits(),D,T,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static NonvolatileBits nonvolatile(){return new NonvolatileBits(0x91000000000000B1L,0x92000000000000B2L,0x93000000000000B3L,0x94000000000000B4L,0xF000000100000005L,0x96000000000000B6L,0x97000000000000B7L,0x98000000000000B8L,x(0xB9));}
    private static VolatileBits rax(VolatileBits v,long a){return raxR11(v,a,v.r11Bits());}
    private static VolatileBits raxR11(VolatileBits v,long a,long r11){return new VolatileBits(a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),r11,v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static VolatileBits x0(VolatileBits v,Bits128 value){return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),value,v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static void check(boolean condition){checks++;if(!condition)throw new AssertionError("check="+checks);}
    private static void equal(Object actual,Object expected){checks++;if(!Objects.equals(actual,expected))throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);}
}
