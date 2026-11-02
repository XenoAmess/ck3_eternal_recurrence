package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner literal oracle; no host floating arithmetic, Memory, old entry, or target-derived expected. */
public final class QueueGrowthCvtdqBoundary605 {
    private QueueGrowthCvtdqBoundary605() { }
    private static final long IMAGE=0x140000000L,SP=0x8100000000008000L,ORIGIN=0x3727F0DL;
    private static final Bits128 X1=new Bits128(0x9100000000000001L,0xA100000000000002L);
    private static final Bits128 X2=new Bits128(0x9200000000000003L,0xA200000000000004L);
    private static final Bits128 X3=new Bits128(0x9300000000000005L,0xA300000000000006L);
    private static final Bits128 X4=new Bits128(0x9400000000000007L,0xA400000000000008L);
    private static final Bits128 X5=new Bits128(0x9500000000000009L,0xA50000000000000AL);
    private static final Bits128 X6=new Bits128(0x960000000000000BL,0xA60000000000000CL);
    private static final NonvolatileBits N=new NonvolatileBits(0x8100000000001000L,
        0xBB00000000000002L,0,0x8100000000002000L,0xCC00000000000003L,
        0xDD00000000000004L,0xEE00000000000005L,0xFF00000000000006L,X6);
    private static Registers registers(int count) {
        VolatileBits v=new VolatileBits((long)count,0x8100000000003000L,0x8100000000004000L,
            8,0xF100000000000009L,0xF20000000000000AL,0xF30000000000000BL,
            new Bits128(Integer.toUnsignedLong(count),0),X1,X2,X3,X4,X5);
        Registers r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(IMAGE,SP,v,N));
        r.rsi=Integer.toUnsignedLong(count+1);return r;
    }
    private static GovernmentCrtBoundary185Api.Entry snapshot(Registers r) {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE,r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
    private static void check(boolean condition) {
        if(!condition) throw new AssertionError("605 literal contract mismatch");
    }
    private static VolatileBits converted(VolatileBits v,int expectedBits) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
            new Bits128(Integer.toUnsignedLong(expectedBits),0),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static void completed(int count,Mxcsr input,int expectedBits,Mxcsr expectedState) {
        Registers r=registers(count);GovernmentCrtBoundary185Api.Entry before=snapshot(r);
        QueueGrowthCvtdq605.Result actual=QueueGrowthCvtdq605.execute(IMAGE,r,true,input,ORIGIN);
        check(actual instanceof QueueGrowthCvtdq605.Completed);
        QueueGrowthCvtdq605.Completed result=(QueueGrowthCvtdq605.Completed)actual;
        check(result.mxcsr().equals(expectedState));
        check(r.volatileBits().equals(converted(before.volatileBits(),expectedBits)));
        check(r.nonvolatileBits().equals(before.nonvolatileBits())&&r.rsp==before.rspBits());
    }
    private static void exactUnknown() {
        int[] counts={0,1,-1,Integer.MIN_VALUE};
        int[] bits={0,0x3F800000,0xBF800000,0xCF000000};
        for(int i=0;i<counts.length;i++) completed(counts[i],Mxcsr.unknown(),bits[i],Mxcsr.unknown());
        completed(1,new Mxcsr(0x20,0x20),0x3F800000,new Mxcsr(0x20,0x20));
    }
    private static void nearest() {
        int[] counts={16777217,16777219,33554431};
        int[] bits={0x4B800000,0x4B800002,0x4C000000};
        for(int i=0;i<counts.length;i++) completed(counts[i],Mxcsr.exact(0x1F80),bits[i],Mxcsr.exact(0x1FA0));
    }
    private static final int[] PRE={0x1F80,0x3F80,0x5F80,0x7F80};
    private static final int[] POST={0x1FA0,0x3FA0,0x5FA0,0x7FA0};
    private static void positiveRc() {
        int[] bits={0x4B800000,0x4B800000,0x4B800001,0x4B800000};
        for(int rc=0;rc<4;rc++) completed(16777217,Mxcsr.exact(PRE[rc]),bits[rc],Mxcsr.exact(POST[rc]));
    }
    private static void negativeRc() {
        int[] bits={0xCB800000,0xCB800001,0xCB800000,0xCB800000};
        for(int rc=0;rc<4;rc++) completed(-16777217,Mxcsr.exact(PRE[rc]),bits[rc],Mxcsr.exact(POST[rc]));
    }
    private static void intMax() {
        int[] bits={0x4F000000,0x4EFFFFFF,0x4F000000,0x4EFFFFFF};
        for(int rc=0;rc<4;rc++) completed(Integer.MAX_VALUE,Mxcsr.exact(PRE[rc]),bits[rc],Mxcsr.exact(POST[rc]));
    }
    private static void stopped(Registers r,Mxcsr input,StopReason reason,Mxcsr expected,int raised) {
        GovernmentCrtBoundary185Api.Entry before=snapshot(r);
        QueueGrowthCvtdq605.Result actual=QueueGrowthCvtdq605.execute(IMAGE,r,false,input,ORIGIN);
        check(actual instanceof QueueGrowthCvtdq605.NotCompleted);
        QueueFp604Api.Stopped stop=((QueueGrowthCvtdq605.NotCompleted)actual).stopped();
        check(stop.reason()==reason&&stop.raisedConditionBits()==raised&&stop.originCallSiteRva()==ORIGIN);
        check(stop.snapshot().instructionRva()==0x88037B&&!stop.snapshot().directionFlagSet());
        check(stop.snapshot().mxcsr().equals(expected)&&stop.snapshot().currentState().equals(before));
        check(snapshot(r).equals(before)); // no destination, fullRAX, GPR/N/XMM/SP or prior spill repair
    }
    private static void unmaskedPrecision() {
        stopped(registers(16777217),new Mxcsr(0,0x1000),StopReason.ARCHITECTURAL_FP_CONDITION,new Mxcsr(0x20,0x1020),0x20);
        stopped(registers(-16777217),Mxcsr.exact(0x0F80),StopReason.ARCHITECTURAL_FP_CONDITION,Mxcsr.exact(0x0FA0),0x20);
        stopped(registers(16777217),new Mxcsr(0x4000,0x5000),StopReason.ARCHITECTURAL_FP_CONDITION,new Mxcsr(0x4020,0x5020),0x20);
    }
    private static void missingKnowledge() {
        stopped(registers(16777217),new Mxcsr(0,0x6000),StopReason.MISSING_FP_INPUT,new Mxcsr(0,0x6000),0);
        stopped(registers(16777217),new Mxcsr(0x1000,0x1000),StopReason.MISSING_FP_INPUT,new Mxcsr(0x1000,0x1000),0);
        stopped(registers(16777217),new Mxcsr(0x3000,0x3000),StopReason.MISSING_FP_INPUT,new Mxcsr(0x3000,0x3000),0);
    }
    private static void unsupportedShape() {
        Registers high32=registers(1);high32.x0=new Bits128(0x0000000100000001L,0);
        stopped(high32,Mxcsr.exact(0x1F80),StopReason.UNSUPPORTED_FP_DOMAIN,Mxcsr.exact(0x1F80),0);
        Registers high64=registers(1);high64.x0=new Bits128(1,0x8100000000000001L);
        stopped(high64,Mxcsr.unknown(),StopReason.UNSUPPORTED_FP_DOMAIN,Mxcsr.unknown(),0);
    }
    private static void stickyExact() {
        completed(3,Mxcsr.exact(0x0FA0),0x40400000,Mxcsr.exact(0x0FA0));
        completed(2,new Mxcsr(0x20,0x1020),0x40000000,new Mxcsr(0x20,0x1020));
        completed(-2147483648,new Mxcsr(0x20,0x20),0xCF000000,new Mxcsr(0x20,0x20));
    }
    public static int verify() {
        exactUnknown();nearest();positiveRc();negativeRc();intMax();
        unmaskedPrecision();missingKnowledge();unsupportedShape();stickyExact();return 9;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
