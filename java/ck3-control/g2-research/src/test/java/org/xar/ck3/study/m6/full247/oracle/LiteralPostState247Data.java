package org.xar.ck3.study.m6.full247.oracle;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Independent oracle data only, using complete held185/604 types. No production247 API.
 * No body, getter, allocator, free kernel, IEEE operation or Native capture is implemented.
 * Opaque Normal/Stopped records below are supplied synthetic protocol data, not oldNR wrappers.
 */
public final class LiteralPostState247Data {
    public static final long I=0x140000000L,S=0x9008L,P=S-0x28L,C=P-8L;
    public static final long A=0x2000L,TA=0x3000L,B=0x4000L,TB=0x5000L;
    public static final long GET=0xBAD24701L,ALLOC=0xBAD24702L,FREE=0xBAD24703L;
    public static final long RET=0xABCDEF0011223344L,FRESH_RET=0xEEDDCCBBAA998877L;
    public static final long FRESH_BX=0xF1000000000000B1L,FRESH_DI=0xF2000000000000B4L;
    private LiteralPostState247Data() { }

    /** Data records are confined to the oracle package; they are not a competing production Frame API. */
    public record Allocate51(Entry input,boolean inputDF,Mxcsr inputMxcsr,
            Map<Long,Long> initialQwords,Call firstCall,Normal firstNormal,
            Map<Long,Long> firstRamEffects,Tail expectedTail,boolean expectedTailDF,
            Mxcsr expectedTailMxcsr,Normal tailNormal) { }
    public record Free58(Entry input,boolean inputDF,Mxcsr inputMxcsr,
            Map<Long,Long> initialQwords,Call firstCall,Normal firstNormal,
            Call secondCall,boolean expectedSecondDF,Mxcsr expectedSecondMxcsr,
            Normal secondNormal,Map<Long,Long> secondRamEffects,Normal expectedReturn) { }
    public record Self58(Entry input,boolean inputDF,Mxcsr inputMxcsr,
            Map<Long,Long> initialQwords,Normal expectedReturn) { }
    public record ReturnWrite(long address,long value) { }
    public record StopData(String name,Stopped offered,List<ReturnWrite> sourceCallPushes,
            int expectedPortInvocations,boolean noTail,boolean noSecondCall,boolean noOuterRet) { }

    public static Allocate51 allocate51() {
        Entry in=input(0x100L,A,0xF100000000006000L,0x8000000000000038L);
        NonvolatileBits local=replaceBxDi(in.nonvolatileBits(),in.volatileBits().r8Bits(),in.volatileBits().rdxBits());
        Call first=new Call(0x855883L,TargetKind.INDIRECT_ABSOLUTE,GET,P,
                rax(in.volatileBits(),TA),local);
        VolatileBits v1=rax(v(0x1100L),B);
        Normal child=normal(v1,local,I+0x855886L,P,true,Mxcsr.exact(0x1FA0));
        VolatileBits tailV=change(v1,B,B,in.volatileBits().rdxBits(),in.volatileBits().r8Bits(),ALLOC);
        NonvolatileBits restored=replaceBxDi(in.nonvolatileBits(),FRESH_BX,FRESH_DI);
        Tail tail=new Tail(0x8558A0L,TargetKind.INDIRECT_ABSOLUTE,ALLOC,
                new Entry(I,S,tailV,restored));
        Normal tailResult=normal(v(0x2200L),restored,FRESH_RET,S+8L,false,new Mxcsr(0x80,0x80));
        return new Allocate51(in,false,partialInput(),initialRam(),first,child,freshSavedSlots(),
                tail,true,Mxcsr.exact(0x1FA0),tailResult);
    }

    public static Free58 free58() {
        Entry in=input(0x3300L,A,0xF100000000007000L,0x8000000000000048L);
        NonvolatileBits local=replaceBxDi(in.nonvolatileBits(),in.volatileBits().rdxBits(),in.volatileBits().r8Bits());
        Call first=new Call(0x85584CL,TargetKind.INDIRECT_ABSOLUTE,GET,P,
                rax(in.volatileBits(),TA),local);
        VolatileBits v1=rax(v(0x4400L),B),v2=v(0x5500L);
        Normal firstNormal=normal(v1,local,I+0x85584FL,P,true,Mxcsr.exact(0x1FA0));
        VolatileBits secondV=change(v1,B,B,in.volatileBits().rdxBits(),in.volatileBits().r8Bits(),TB);
        Call second=new Call(0x85585BL,TargetKind.INDIRECT_ABSOLUTE,FREE,P,secondV,local);
        Mxcsr finalMx=new Mxcsr(0x80,0x80);
        Normal secondNormal=normal(v2,local,I+0x85585FL,P,false,finalMx); // four-byte CALL.
        Normal returned=normal(v2,replaceBxDi(in.nonvolatileBits(),FRESH_BX,FRESH_DI),
                FRESH_RET,S+8L,false,finalMx);
        return new Free58(in,false,partialInput(),initialRam(),first,firstNormal,
                second,true,Mxcsr.exact(0x1FA0),secondNormal,freshSavedSlots(),returned);
    }

    public static Self58 self58Wrap64() {
        Entry in=input(0x6600L,0xFFFFFFFFFFFFFFF8L,0L,0x8000000000000058L);
        Mxcsr partial=partialInput();
        Normal returned=normal(rax(in.volatileBits(),0L),in.nonvolatileBits(),RET,S+8L,true,partial);
        // Deliberately no object/vtable bytes at wrapped RCX. The source must never read them.
        return new Self58(in,true,partial,Map.of(S,RET),returned);
    }

    /**
     * Three necessary negative data variants, not extra test executions.
     * Inner instruction RVAs are opaque supplier sentinels, not held/captured kernel PCs.
     */
    public static List<StopData> stoppedPrefixes() {
        return List.of(
                stop("allocate-first-stopped",0x855883L,0xD24701L,
                        List.of(new ReturnWrite(C,I+0x855886L)),1,true,false,true),
                stop("free-first-stopped",0x85584CL,0xD24702L,
                        List.of(new ReturnWrite(C,I+0x85584FL)),1,false,true,true),
                stop("free-second-stopped",0x85585BL,0xD24703L,
                        List.of(new ReturnWrite(C,I+0x85584FL),new ReturnWrite(C,I+0x85585FL)),
                        2,false,false,true));
    }

    private static StopData stop(String name,long sourceCall,long opaqueInstruction,
            List<ReturnWrite> pushes,int calls,boolean noTail,boolean noSecond,boolean noOuterRet) {
        long tag=sourceCall&0xFFFFL;
        Entry inner=new Entry(I,C-0x60L,v(tag),n(tag+0x100L));
        Stopped actual=new Stopped(StopReason.MISSING_POST_STATE,
                new Snapshot(inner,opaqueInstruction,true,Mxcsr.unknown()),0,sourceCall);
        return new StopData(name,actual,pushes,calls,noTail,noSecond,noOuterRet);
    }
    private static Mxcsr partialInput() {return new Mxcsr(0x1F80,0xFFC0);}
    private static Map<Long,Long> initialRam() {
        Map<Long,Long> ram=new LinkedHashMap<>();
        ram.put(S,RET);ram.put(A,TA);ram.put(TA+0x38L,GET);ram.put(B,TB);
        ram.put(TB+8L,ALLOC);ram.put(TB+0x10L,FREE);
        return Map.copyOf(ram);
    }
    private static Map<Long,Long> freshSavedSlots() {
        return Map.of(S+8L,FRESH_BX,S-8L,FRESH_DI,S,FRESH_RET);
    }
    private static Entry input(long tag,long rcx,long rdx,long r8) {
        VolatileBits v=v(tag);
        return new Entry(I,S,change(v,v.raxBits(),rcx,rdx,r8,v.r9Bits()),n(tag+0x100L));
    }
    private static Normal normal(VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df,Mxcsr mx) {
        return new Normal(new FullCopy437Api.CallResult(new NormalReturn(v,rip,sp,n),df),mx);
    }
    private static NonvolatileBits replaceBxDi(NonvolatileBits n,long bx,long di) {
        return new NonvolatileBits(bx,n.rbpBits(),n.rsiBits(),di,n.r12Bits(),n.r13Bits(),
                n.r14Bits(),n.r15Bits(),n.xmm6());
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
    private static VolatileBits rax(VolatileBits v,long a) {
        return change(v,a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits());
    }
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long r8,long r9) {
        return new VolatileBits(a,c,d,r8,r9,v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
}
