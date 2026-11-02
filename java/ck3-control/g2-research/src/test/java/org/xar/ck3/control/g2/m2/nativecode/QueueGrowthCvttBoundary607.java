package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner literal arithmetic/architecture checks for actual CVTT88038D only. */
public final class QueueGrowthCvttBoundary607 {
    private QueueGrowthCvttBoundary607() { }
    private static final long IMAGE=0x140000000L,SP=0x8100000000008000L,ORIGIN=0x3727F0DL;
    private static final Bits128 X1=new Bits128(0x9100000000000001L,0xA100000000000002L);
    private static final Bits128 X2=new Bits128(0x9200000000000003L,0xA200000000000004L);
    private static final Bits128 X3=new Bits128(0x9300000000000005L,0xA300000000000006L);
    private static final Bits128 X4=new Bits128(0x9400000000000007L,0xA400000000000008L);
    private static final Bits128 X5=new Bits128(0x9500000000000009L,0xA50000000000000AL);
    private static final Bits128 X6=new Bits128(0x960000000000000BL,0xA60000000000000CL);
    private static final NonvolatileBits N=new NonvolatileBits(0x8100000000001000L,17,18,
        0x8100000000002000L,0xCC00000000000003L,0xDD00000000000004L,
        0xEE00000000000005L,0xFF00000000000006L,X6);
    private static void check(boolean condition) {
        if(!condition) throw new AssertionError("607 literal contract mismatch");
    }
    private static Registers registers(int source) {
        var v=new VolatileBits(0xF100000000000001L,0x8100000000003000L,0x8100000000004000L,
            8,0xF200000000000009L,0xF30000000000000AL,0xF40000000000000BL,
            new Bits128(0xC100000000000000L|Integer.toUnsignedLong(source),0xD100000000000002L),X1,X2,X3,X4,X5);
        return GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(IMAGE,SP,v,N));
    }
    private static GovernmentCrtBoundary185Api.Entry snapshot(Registers r) {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE,r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
    private static VolatileBits changed(VolatileBits v,int bits) {
        return new VolatileBits(Integer.toUnsignedLong(bits),v.rcxBits(),v.rdxBits(),v.r8Bits(),
            v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static void normal(int bits,Mxcsr pre,int result,Mxcsr post) {
        Registers r=registers(bits);var before=snapshot(r);
        var actual=QueueGrowthCvtt607.execute(IMAGE,r,true,pre,ORIGIN);
        check(actual instanceof QueueGrowthCvtt607.Completed);
        check(((QueueGrowthCvtt607.Completed)actual).mxcsr().equals(post));
        check(r.volatileBits().equals(changed(before.volatileBits(),result)));
        check(r.nonvolatileBits().equals(before.nonvolatileBits())&&r.rsp==before.rspBits());
    }
    private static void stop(int bits,Mxcsr pre,StopReason reason,int raised,Mxcsr post) {
        Registers r=registers(bits);var before=snapshot(r);
        var actual=QueueGrowthCvtt607.execute(IMAGE,r,true,pre,ORIGIN);
        check(actual instanceof QueueGrowthCvtt607.NotCompleted);
        var stopped=((QueueGrowthCvtt607.NotCompleted)actual).stopped();
        check(stopped.reason()==reason&&stopped.raisedConditionBits()==raised&&stopped.originCallSiteRva()==ORIGIN);
        check(stopped.snapshot().instructionRva()==0x88038D&&stopped.snapshot().directionFlagSet());
        check(stopped.snapshot().currentState().equals(before)&&stopped.snapshot().mxcsr().equals(post));
        check(snapshot(r).equals(before)); // includes prior full RAX and every XMM, N and SP
    }
    private static void integral(int source,int value,boolean inexact) {
        var actual=QueueFiniteTruncate607.truncate(source);
        check(actual.equals(new QueueFiniteTruncate607.Integral(value,inexact)));
    }
    private static void outside(int source) {
        check(QueueFiniteTruncate607.truncate(source) instanceof QueueFiniteTruncate607.OutOfRange);
    }
    private static void nonfinite(int source) {
        try { QueueFiniteTruncate607.truncate(source); }
        catch(IllegalArgumentException expected) { return; }
        throw new AssertionError("607 nonfinite core input accepted");
    }
    public static int verify() {
        // 1. Exact core values, including both signed zeros and valid -2^31.
        integral(0,0,false);integral(0x80000000,0,false);integral(0x3F800000,1,false);
        integral(0xBF800000,-1,false);integral(0x4EFFFFFF,0x7FFFFF80,false);
        integral(0xCF000000,0x80000000,false);
        // 2. Toward-zero fractions and subnormals without any host FP conversion.
        integral(0x3FE00000,1,true);integral(0xBFE00000,-1,true);
        integral(0x3F000000,0,true);integral(0xBF000000,0,true);
        integral(1,0,true);integral(0x80000001,0,true);
        // 3. Signed bounds and huge finite exponents: range check must precede overflow.
        outside(0x4F000000);outside(0xCF000001);outside(0x5F000000);
        outside(0x5F800000);outside(0x7F7FFFFF);outside(0xFF7FFFFF);
        // 4. Nonfinite inputs belong to the owner instruction, not a fake core integer.
        nonfinite(0x7F800000);nonfinite(0xFF800000);nonfinite(0x7FC12345);nonfinite(0x7F812345);
        // 5. Exact values need no controls; all scalar source upper bits remain held.
        Mxcsr unknown=Mxcsr.unknown();
        normal(0,unknown,0,unknown);normal(0x80000000,unknown,0,unknown);
        normal(0xBF800000,unknown,-1,unknown);normal(0xCF000000,unknown,0x80000000,unknown);
        // 6. Masked valid fractions set only PE and zeroextend negative r32 output.
        Mxcsr pm=new Mxcsr(0x1000,0x1000),pmP=new Mxcsr(0x1020,0x1020);
        normal(0x3FE00000,pm,1,pmP);normal(0xBFE00000,pm,-1,pmP);
        normal(0x3F000000,pm,0,pmP);normal(0xBF000000,pm,0,pmP);
        // 7. Unmasked precision sets PE but retains whole RAX, including high32.
        stop(0x3FE00000,new Mxcsr(0,0x1000),StopReason.ARCHITECTURAL_FP_CONDITION,0x20,new Mxcsr(0x20,0x1020));
        // 8. All NaNs/Inf and signed range Invalid produce indefinite only when masked.
        Mxcsr im=new Mxcsr(0x80,0x80),imI=new Mxcsr(0x81,0x81);
        for(int bits:new int[]{0x4F000000,0xCF000001,0x7F800000,0xFF800000,0x7FC12345,0x7F812345})
            normal(bits,im,0x80000000,imI);
        // 9. Invalid precedes Precision; prior PE sticky remains, no new PE is invented.
        stop(0x7FC12345,new Mxcsr(0x20,0xA0),StopReason.ARCHITECTURAL_FP_CONDITION,1,new Mxcsr(0x21,0xA1));
        stop(0x4F000000,new Mxcsr(0,0x80),StopReason.ARCHITECTURAL_FP_CONDITION,1,new Mxcsr(1,0x81));
        // 10. Global DAZ substitution, no DE even when DM is clear; FTZ is irrelevant.
        for(int bits:new int[]{1,0x80000001}) {
            normal(bits,new Mxcsr(0x40,0x1140),0,new Mxcsr(0x40,0x1140));
            normal(bits,new Mxcsr(0x1000,0x1140),0,new Mxcsr(0x1020,0x1160));
            stop(bits,new Mxcsr(0,0x1140),StopReason.ARCHITECTURAL_FP_CONDITION,0x20,new Mxcsr(0x20,0x1160));
        }
        // 11. Missing reached controls is an unexecuted software-domain outcome.
        stop(1,unknown,StopReason.MISSING_FP_INPUT,0,unknown);
        stop(0x3F000000,unknown,StopReason.MISSING_FP_INPUT,0,unknown);
        stop(0x4F000000,unknown,StopReason.MISSING_FP_INPUT,0,unknown);
        // 12. Old I/P do not self-trigger, and RC/DM/FTZ cannot change integer truncation.
        normal(0x3F800000,Mxcsr.exact(0x21),1,Mxcsr.exact(0x21));
        for(int rc:new int[]{0,0x2000,0x4000,0x6000}) {
            int controls=0x9000|rc;
            normal(0xBFE00000,Mxcsr.exact(controls),-1,Mxcsr.exact(controls|0x20));
        }
        // 13. Same integer bits distinguish valid -2^31 from masked Invalid by new IE.
        normal(0xCF000000,im,0x80000000,im);
        normal(0x4F000000,im,0x80000000,imI);
        return 13;
    }
    public static void main(String[] args) {
        if(args.length!=0) throw new IllegalArgumentException("No args");
        System.out.println(verify());
    }
}
