package org.xar.ck3.study.m6.postwitness242;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Budget;
import org.xar.ck3.study.m6.postentry242.WholeTransferPostState242;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate243.OpaqueSseOutcomeProvider243;

/** One new actual whole-Outcome recursion scene. Only ordinary opaque children are scripted. */
public final class KnownRecursiveOutcome242Test {
    private static final long I=0x140000000L,S=0x19008L,F=S-0x458L,E=F-8L,H=E-0x48L;
    private static final long TEMP=F+0x20L,Q=F+0x40L,K=I+0x44BBB10L,L=I+0x54DE268L;
    private static final long D=0x12000L,T=0x13000L,A=0x14000L,B=0x15000L;
    private static final long DB=0x16000L,TB=0x17000L,NEW=0x18000L;
    private static final long ALLOC_TARGET=0xBAD24201L,FREE_TARGET=0xBAD24202L;
    private static final long RET=0xA1B2C3D4E5F6071L,FRESH_R12=0xF00000020000A0A5L;
    private static final int HELD_LITERAL_RAW=0x3FC00000;
    private static final Bits128 ZERO=new Bits128(0L,0L);
    private static final QueueFp604Api.Mxcsr M0=new QueueFp604Api.Mxcsr(0x1F80,0xFFC0);
    private static final boolean[] POST_DF={true,false,true,false,true,false,false,true};
    private static final QueueFp604Api.Mxcsr[] POST_M={
            new QueueFp604Api.Mxcsr(0x1F81,0xFFFF),new QueueFp604Api.Mxcsr(0x1F82,0xFFFF),
            new QueueFp604Api.Mxcsr(0x1F84,0xFFFF),new QueueFp604Api.Mxcsr(0x1F88,0xFFFF),
            new QueueFp604Api.Mxcsr(0x1F90,0xFFFF),new QueueFp604Api.Mxcsr(0x1FA0,0xFFFF),
            new QueueFp604Api.Mxcsr(0x1F80,0xFFC1),new QueueFp604Api.Mxcsr(0x3F82,0xFFFF)};
    private static int checks;
    private KnownRecursiveOutcome242Test() { }

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("one new scene242 only");
        threeActualMovesPropagateOpaquePoststate();
        System.out.println("PASS newScenes=1 checks="+checks
                +" threeActualKnownMoveReturns=true finalCleanupPostApplied=true freshSavedR12=true"
                +" partialMxcsrNotMerged=true actual243StageWrapper=true legacyKnownOutcomeCallbacks=0"
                +" controlledOpaqueChildrenOnly=true heldLiteral4B=true syntheticVtable=true"
                +" Native=false Game=false hardwareABI=false");
    }

    private static void threeActualMovesPropagateOpaquePoststate() {
        Ram memory=ram();
        VolatileBits initial=change(v(0x100L),0xE001L,D,T,v(0x100L).r8Bits());
        NonvolatileBits original=n0();
        VolatileBits[] returned={change(v(0x1100L),NEW,v(0x1100L).rcxBits(),v(0x1100L).rdxBits(),v(0x1100L).r8Bits()),
                v(0x2200L),v(0x3300L),v(0x4400L),v(0x5500L),v(0x6600L),v(0x7700L),v(0x8800L)};
        int[] calls={0},stages={0},budgets={0};
        List<Long> actualOpaqueSites=new ArrayList<>();
        List<Boolean> actualPreDf=new ArrayList<>();
        List<QueueFp604Api.Mxcsr> actualPreMxcsr=new ArrayList<>();

        // Declared qualified opaque effects, wrapped by the actual243 source-site/environment guard.
        // No Java float arithmetic or default FP environment supplies a result here.
        PostState240Api.FloatingStages qualified=new PostState240Api.FloatingStages() {
            private void before(PostState240Api.FpFrame frame,int expectedIndex,long site) {
                eq(stages[0]++,expectedIndex);eq(calls[0],0);
                eq(frame.before().instructionRva(),site);eq(frame.originCallSiteRva(),0xB2EE82L);
                eq(frame.before().directionFlagSet(),false);eq(frame.before().mxcsr(),M0);
                VolatileBits expectedV=zeroX0(change(initial,0L,Q,D,4L));
                NonvolatileBits expectedN=localN(DB,0L,expectedIndex==0?0L:1L,T,4L,1L,TEMP,D,original);
                eq(frame.before().currentState(),new Entry(I,H,expectedV,expectedN));
                if(expectedIndex==0)eq(memory.multiplierReads,0);
                else eq(memory.multiplierReads,1);
            }
            @Override public PostState240Api.VectorResult convertSignedDwords(PostState240Api.FpFrame frame) {
                before(frame,0,0xB2EF7DL);
                return new PostState240Api.VectorCompleted(ZERO,false,M0);
            }
            @Override public PostState240Api.VectorResult multiplyLowSingle(PostState240Api.FpFrame frame,int raw) {
                before(frame,1,0xB2EF83L);eq(raw,HELD_LITERAL_RAW);
                return new PostState240Api.VectorCompleted(ZERO,false,M0);
            }
            @Override public PostState240Api.IntegerResult truncateLowSingle(PostState240Api.FpFrame frame) {
                before(frame,2,0xB2EF8BL);
                return new PostState240Api.IntegerCompleted(0,false,M0);
            }
        };

        Budget budget=(site,cursor,end)->{
            int index=budgets[0]++;
            long[] sites={0xB2EDF0L,0xB2EE82L,0xB2EEE0L,0xB2EE8EL,0xB2EEE0L,0xB2EE9BL,0xB2EEE0L};
            long[] cursors={S,F,E,F,E,F,E};
            check(index<sites.length);eq(site,sites[index]);eq(cursor,cursors[index]);eq(end,0L);
            if(index==1) {
                eq(calls[0],0);eq(stages[0],0);
                header(memory,TEMP,0L,0,0,Q);header(memory,D,DB,3,1,A);header(memory,T,TB,3,2,B);
                eq(memory.peek(Q),K);eq(memory.peek(F+0x448L),L);
            } else if(index==3) {
                eq(calls[0],5);eq(stages[0],3);
                header(memory,TEMP,NEW,1,1,Q);header(memory,D,DB,3,0,A);header(memory,T,TB,3,2,B);
                eq(memory.peek(H+0x28L),FRESH_R12);eq(memory.peek(E),I+0xB2EE87L);
                eq(memory.knownRetReads,List.of(I+0xB2EE87L));
            } else if(index==5) {
                eq(calls[0],6);
                header(memory,TEMP,NEW,1,1,Q);header(memory,D,DB,3,2,A);header(memory,T,TB,3,0,B);
                eq(memory.peek(H+0x28L),FRESH_R12);eq(memory.peek(E),I+0xB2EE93L);
                eq(memory.knownRetReads,List.of(I+0xB2EE87L,I+0xB2EE93L));
            }
        };

        CallOutcome242Api.OutcomePort opaque=frame->{
            int index=calls[0]++;
            check(index<8);eq(stages[0],3);
            long[] sites={0xB2EF9EL,0xB2EFADL,0xB2EFBBL,0xB2EFD2L,0xB2EFE5L,0xB2EFFEL,0xB2EFFEL,0xB2EEBBL};
            long site=sites[index];boolean indirect=index==0||index==4||index==7;
            Call call=frame.call();
            actualOpaqueSites.add(call.callSiteRva());actualPreDf.add(frame.preDirectionFlagSet());actualPreMxcsr.add(frame.preMxcsr());
            // Known whole outcomes are exclusively supplied by the real internal registry, never this callback.
            eq(frame.normalRule(),CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N);
            eq(frame.ownerEntryRva(),index==7?0xB2EDF0L:0xB2EEE0L);eq(frame.imageBaseBits(),I);
            eq(call.callSiteRva(),site);eq(call.kind(),indirect?TargetKind.INDIRECT_ABSOLUTE:TargetKind.DIRECT_RVA);
            eq(call.targetBits(),index==0?ALLOC_TARGET:indirect?FREE_TARGET:0x4226860L);
            long preSP=index==7?F:H;int length=indirect?3:5;
            eq(call.rspBits(),preSP);eq(frame.instructionLength(),length);
            eq(frame.returnRipBits(),I+site+length);eq(memory.peek(preSP-8L),I+site+length);
            eq(frame.preDirectionFlagSet(),index==0?false:POST_DF[index-1]);
            eq(frame.preMxcsr(),index==0?M0:POST_M[index-1]);

            VolatileBits expectedV;
            NonvolatileBits expectedN;
            if(index<5) {
                expectedN=localN(DB,0L,1L,index==0?T:NEW,4L,1L,TEMP,D,original);
                if(index==0)expectedV=zeroX0(change(initial,K,Q,4L,4L));
                else if(index==1)expectedV=change(returned[0],NEW,NEW,0L,0L);
                else if(index==2)expectedV=change(returned[1],returned[1].raxBits(),NEW,DB,4L);
                else if(index==3)expectedV=change(returned[2],1L,NEW+4L,0L,0L);
                else expectedV=change(returned[3],K,Q,0L,4L);
            } else if(index==5) {
                expectedV=change(returned[4],3L,DB,TB,8L);
                expectedN=localN(TB,0L,0L,T,8L,2L,D,T,original);
            } else if(index==6) {
                expectedV=change(returned[5],3L,TB,NEW,4L);
                expectedN=localN(NEW,0L,0L,T,4L,1L,T,TEMP,original);
            } else {
                expectedV=change(returned[6],K,Q,NEW,4L);
                expectedN=localN(D,original.rbpBits(),0L,T,FRESH_R12,original.r13Bits(),
                        original.r14Bits(),original.r15Bits(),original);
            }
            eq(call.volatileBits(),expectedV);eq(call.nonvolatileBits(),expectedN);
            eq(frame.childEntry(),new Entry(I,preSP-8L,expectedV,expectedN));

            if(index==2) {
                eq(memory.peek32(DB),0x11223344);memory.writeDword(NEW,0x11223344);
            } else if(index==4) {
                // The ordinary opaque port preserves actual local N; only this genuine save slot changes.
                eq(memory.peek(H+0x28L),original.r12Bits());memory.writeQword(H+0x28L,FRESH_R12);
            } else if(index==5) {
                eq(memory.peek(H+0x28L),FRESH_R12);
                header(memory,D,DB,3,0,A);header(memory,T,TB,3,2,B);
                eq(memory.peek32(TB),0x55667788);eq(memory.peek32(TB+4L),0x99AABBCC);
                memory.writeDword(DB,0x55667788);memory.writeDword(DB+4L,0x99AABBCC);
            } else if(index==6) {
                eq(memory.peek(H+0x28L),FRESH_R12);
                header(memory,T,TB,3,0,B);header(memory,TEMP,NEW,1,1,Q);
                eq(memory.peek32(NEW),0x11223344);memory.writeDword(TB,0x11223344);
            } else if(index==7) {
                header(memory,D,DB,3,2,A);header(memory,T,TB,3,1,B);header(memory,TEMP,NEW,1,0,Q);
                eq(memory.knownRetReads,List.of(I+0xB2EE87L,I+0xB2EE93L,I+0xB2EEA0L));
                eq(memory.rootRetReads,0);
                eq(frame.preMxcsr().knownMaskBits(),0xFFC1);check(!frame.preMxcsr().isExact());
            }
            NormalReturn actualOpaqueNormal=new NormalReturn(returned[index],frame.returnRipBits(),
                    call.rspBits(),call.nonvolatileBits());
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(actualOpaqueNormal,POST_DF[index]),POST_M[index]);
        };

        WholeTransferPostState242 actual=new WholeTransferPostState242(new OpaqueSseOutcomeProvider243(qualified),budget,opaque);
        QueueFp604Api.Outcome offered=actual.swap4(new PostState240Api.Input(new Entry(I,S,initial,original),false,M0,0L),memory);
        check(offered instanceof QueueFp604Api.Normal);
        QueueFp604Api.Normal normal=(QueueFp604Api.Normal)offered;
        NormalReturn out=normal.base().normalReturn();
        eq(calls[0],8);eq(stages[0],3);eq(budgets[0],7);
        eq(actualOpaqueSites,List.of(0xB2EF9EL,0xB2EFADL,0xB2EFBBL,0xB2EFD2L,0xB2EFE5L,0xB2EFFEL,0xB2EFFEL,0xB2EEBBL));
        eq(actualPreDf,List.of(false,true,false,true,false,true,false,false));
        eq(actualPreMxcsr,List.of(M0,POST_M[0],POST_M[1],POST_M[2],POST_M[3],POST_M[4],POST_M[5],POST_M[6]));
        eq(normal.base().postDirectionFlagSet(),true);eq(normal.postMxcsr(),POST_M[7]);
        check(normal.base().postDirectionFlagSet()!=false);check(!normal.postMxcsr().equals(M0));
        eq(out.volatileBits(),r11(returned[7],S-8L));
        eq(out.nonvolatileBits(),new NonvolatileBits(original.rbxBits(),original.rbpBits(),original.rsiBits(),original.rdiBits(),
                FRESH_R12,original.r13Bits(),original.r14Bits(),original.r15Bits(),original.xmm6()));
        eq(out.returnRipBits(),RET);eq(out.callerRspBits(),S+8L);
        eq(memory.savedR12Writes,List.of(original.r12Bits(),FRESH_R12,FRESH_R12,FRESH_R12));
        eq(memory.knownRetReads,List.of(I+0xB2EE87L,I+0xB2EE93L,I+0xB2EEA0L));eq(memory.rootRetReads,1);
        header(memory,D,DB,3,2,A);header(memory,T,TB,3,1,B);header(memory,TEMP,NEW,1,0,Q);
        eq(memory.peek32(DB),0x55667788);eq(memory.peek32(DB+4L),0x99AABBCC);eq(memory.peek32(DB+8L),0x2468ACE0);
        eq(memory.peek32(TB),0x11223344);eq(memory.peek32(TB+4L),0x99AABBCC);eq(memory.peek32(TB+8L),0x10203040);
        eq(memory.peek32(NEW),0x11223344);check(!memory.has(NEW+4L));
        eq(memory.peek(S),RET);eq(memory.peek(S+8L),original.rbxBits());eq(memory.peek(S+0x10L),original.rsiBits());eq(memory.peek(S-8L),original.rdiBits());
        eq(memory.peek(Q),K);eq(memory.peek(F+0x448L),L);eq(memory.peek(K+8L),ALLOC_TARGET);eq(memory.peek(K+0x10L),FREE_TARGET);
        eq(memory.literalQwordReads,List.of(K+8L,K+0x10L,K+0x10L));eq(memory.multiplierReads,1);
        check(!memory.qReads.contains(L));check(!memory.qReads.contains(K));
    }

    private static Ram ram() {
        Ram memory=new Ram();memory.poke(S,RET);
        seedHeader(memory,D,DB,3,1,A);seedHeader(memory,T,TB,3,2,B);
        memory.poke32(DB,0x11223344);memory.poke32(DB+4L,0x13579BDF);memory.poke32(DB+8L,0x2468ACE0);
        memory.poke32(TB,0x55667788);memory.poke32(TB+4L,0x99AABBCC);memory.poke32(TB+8L,0x10203040);
        // Held raw operand from existing4B c0e336a5...; these vtable pointer slots are synthetic.
        memory.poke32(I+0x49F64F0L,HELD_LITERAL_RAW);memory.poke(K+8L,ALLOC_TARGET);memory.poke(K+0x10L,FREE_TARGET);
        return memory;
    }
    private static void seedHeader(Ram m,long p,long buffer,int capacity,int count,long allocator) {
        m.poke(p,buffer);m.poke32(p+8L,capacity);m.poke32(p+0xCL,count);m.poke(p+0x10L,allocator);
    }
    private static void header(Ram m,long p,long buffer,int capacity,int count,long allocator) {
        eq(m.peek(p),buffer);eq(m.peek32(p+8L),capacity);eq(m.peek32(p+0xCL),count);eq(m.peek(p+0x10L),allocator);
    }
    private static Bits128 x(long tag) { return new Bits128(0x8000000000000000L|tag,0xF000000000000000L|tag); }
    private static VolatileBits v(long tag) {
        return new VolatileBits(0xA000000000000000L|tag|1L,0xB000000000000000L|tag|2L,0xC000000000000000L|tag|3L,
                0xD000000000000000L|tag|8L,0xE000000000000000L|tag|9L,0xF000000000000000L|tag|10L,
                0x9000000000000000L|tag|11L,x(tag+0x10L),x(tag+0x20L),x(tag+0x30L),x(tag+0x40L),x(tag+0x50L),x(tag+0x60L));
    }
    private static NonvolatileBits n0() {
        return new NonvolatileBits(0xB100000000000001L,0xB200000000000002L,0xB300000000000003L,0xB400000000000004L,
                0xD00000010000A005L,0xB600000000000006L,0xB700000000000007L,0xB800000000000008L,x(0xB9L));
    }
    private static NonvolatileBits localN(long b,long p,long s,long d,long r12,long r13,long r14,long r15,NonvolatileBits original) {
        return new NonvolatileBits(b,p,s,d,r12,r13,r14,r15,original.xmm6());
    }
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long r8) {
        return new VolatileBits(a,c,d,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits zeroX0(VolatileBits v) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),ZERO,v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits r11(VolatileBits v,long bits) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),bits,v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }

    /** Pure stable sparse byte RAM; no read manufactures a path or alters another byte. */
    private static final class Ram implements Memory {
        private final Map<Long,Integer> bytes=new HashMap<>();
        private final List<Long> qReads=new ArrayList<>(),knownRetReads=new ArrayList<>(),savedR12Writes=new ArrayList<>(),literalQwordReads=new ArrayList<>();
        private int rootRetReads,multiplierReads;
        boolean has(long address) { return bytes.containsKey(address); }
        void poke(long address,long value) { for(int j=0;j<8;j++)bytes.put(address+j,(int)(value>>>(j*8))&255); }
        void poke32(long address,int value) { for(int j=0;j<4;j++)bytes.put(address+j,(value>>>(j*8))&255); }
        int byteAt(long address) {
            Integer value=bytes.get(address);
            if(value==null)throw new UnsupportedOperationException("unheld-recursive242RAM "+Long.toHexString(address));
            return value;
        }
        long peek(long address) { long value=0;for(int j=0;j<8;j++)value|=(long)byteAt(address+j)<<(j*8);return value; }
        int peek32(long address) { int value=0;for(int j=0;j<4;j++)value|=byteAt(address+j)<<(j*8);return value; }
        @Override public long readQword(long address) {
            long value=peek(address);qReads.add(address);
            if(address==E)knownRetReads.add(value);if(address==S)rootRetReads++;
            if(address>=K&&address<K+0x18L)literalQwordReads.add(address);
            return value;
        }
        @Override public int readDword(long address) { if(address==I+0x49F64F0L)multiplierReads++;return peek32(address); }
        @Override public int readUnsignedByte(long address) { return byteAt(address); }
        @Override public void writeQword(long address,long value) {
            if(address==H+0x28L)savedR12Writes.add(value);poke(address,value);
        }
        @Override public void writeDword(long address,int value) { poke32(address,value); }
        @Override public void writeByte(long address,int value) { bytes.put(address,value&255); }
        @Override public Bits128 read128(long address) { return new Bits128(readQword(address),readQword(address+8L)); }
        @Override public void write128(long address,Bits128 value) { writeQword(address,value.lowBits());writeQword(address+8L,value.highBits()); }
        @Override public int lockedXaddDword(long address,int value) { throw new AssertionError("unexpected recursive242atomic"); }
    }
    private static void eq(long actual,long expected) { checks++;if(actual!=expected)throw new AssertionError("check="+checks+" actual="+Long.toHexString(actual)+" expected="+Long.toHexString(expected)); }
    private static void eq(boolean actual,boolean expected) { checks++;if(actual!=expected)throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected); }
    private static void eq(Object actual,Object expected) { checks++;if(!Objects.equals(actual,expected))throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected); }
    private static void check(boolean condition) { checks++;if(!condition)throw new AssertionError("check="+checks); }
}
