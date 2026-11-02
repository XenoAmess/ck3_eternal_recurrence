package org.xar.ck3.control.g2.m2.nativecode;

import java.lang.reflect.Proxy;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner source/rational literals for the new MULSS partial-entry domain, no host FP. */
public final class QueueGrowthMulssBoundary606 {
    private QueueGrowthMulssBoundary606() { }
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
        if(!condition) throw new AssertionError("606 literal contract mismatch");
    }
    private static void reject(Runnable action) {
        try { action.run(); }
        catch(IllegalArgumentException expected) { return; }
        throw new AssertionError("Expected source-domain rejection");
    }
    private static Registers registers(int leftBits) {
        var v=new VolatileBits(0xF100000000000001L,0x8100000000003000L,0x8100000000004000L,
            8,0xF200000000000009L,0xF30000000000000AL,0xF40000000000000BL,
            new Bits128(Integer.toUnsignedLong(leftBits),0),X1,X2,X3,X4,X5);
        return GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(IMAGE,SP,v,N));
    }
    private static GovernmentCrtBoundary185Api.Entry snapshot(Registers r) {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE,r.rsp,r.volatileBits(),r.nonvolatileBits());
    }
    private static VolatileBits changed(VolatileBits before,int bits) {
        return new VolatileBits(before.raxBits(),before.rcxBits(),before.rdxBits(),before.r8Bits(),
            before.r9Bits(),before.r10Bits(),before.r11Bits(),new Bits128(Integer.toUnsignedLong(bits),0),
            before.xmm1(),before.xmm2(),before.xmm3(),before.xmm4(),before.xmm5());
    }
    private static final class Read {
        int count;
        final QueueAppend597Api.Memory memory;
        Read(Registers r,int right,RuntimeException marker) {
            GovernmentCrtBoundary185Api.Entry before=snapshot(r);
            memory=(QueueAppend597Api.Memory)Proxy.newProxyInstance(QueueAppend597Api.Memory.class.getClassLoader(),
                new Class<?>[]{QueueAppend597Api.Memory.class},(proxy,method,args)->{
                    if(!method.getName().equals("readDword")||args==null||args.length!=1)
                        throw new AssertionError("Unexpected Memory port "+method.getName());
                    check(((Long)args[0]).longValue()==IMAGE+0x49F64F0L);
                    check(++count==1&&snapshot(r).equals(before)); // fresh once, before any XMM commit
                    if(marker!=null) throw marker;
                    return Integer.valueOf(right);
                });
        }
    }
    private static void normal(int left,int right,int pre,int result,int post) {
        normal(left,right,Mxcsr.exact(pre),result,Mxcsr.exact(post));
    }
    private static void normal(int left,int right,Mxcsr pre,int result,Mxcsr post) {
        Registers r=registers(left);GovernmentCrtBoundary185Api.Entry before=snapshot(r);Read read=new Read(r,right,null);
        QueueGrowthMulss606.Result actual=QueueGrowthMulss606.execute(IMAGE,r,true,pre,ORIGIN,read.memory);
        check(actual instanceof QueueGrowthMulss606.Completed&&read.count==1);
        check(((QueueGrowthMulss606.Completed)actual).mxcsr().equals(post));
        check(r.volatileBits().equals(changed(before.volatileBits(),result)));
        check(r.nonvolatileBits().equals(before.nonvolatileBits())&&r.rsp==before.rspBits());
    }
    private static void fault(int left,int right,int pre,int flags,int post) {
        stopped(registers(left),right,Mxcsr.exact(pre),StopReason.ARCHITECTURAL_FP_CONDITION,flags,Mxcsr.exact(post),1);
    }
    private static void stopped(Registers r,int right,Mxcsr pre,StopReason reason,int flags,Mxcsr post,int reads) {
        GovernmentCrtBoundary185Api.Entry before=snapshot(r);Read read=new Read(r,right,null);
        QueueGrowthMulss606.Result actual=QueueGrowthMulss606.execute(IMAGE,r,false,pre,ORIGIN,read.memory);
        check(actual instanceof QueueGrowthMulss606.NotCompleted&&read.count==reads);
        QueueFp604Api.Stopped stop=((QueueGrowthMulss606.NotCompleted)actual).stopped();
        check(stop.reason()==reason&&stop.raisedConditionBits()==flags&&stop.originCallSiteRva()==ORIGIN);
        check(stop.snapshot().instructionRva()==0x880385&&!stop.snapshot().directionFlagSet());
        check(stop.snapshot().mxcsr().equals(post)&&stop.snapshot().currentState().equals(before));
        check(snapshot(r).equals(before)); // no XMM/GPR/N/SP write and no caller spill repair
    }
    private static void productCore() {
        check(QueueFiniteProduct606.multiply(1,0x3FC00000).equals(new QueueFiniteProduct606.Product(false,12582912,-23)));
        check(QueueFiniteProduct606.multiply(-2147483648L,0xFF7FFFFF).equals(new QueueFiniteProduct606.Product(false,36028794871480320L,104)));
        check(QueueFiniteProduct606.multiply(2,1).equals(new QueueFiniteProduct606.Product(false,2,-149)));
        check(QueueFiniteProduct606.multiply(0,0x80000000).equals(new QueueFiniteProduct606.Product(true,0,-149)));
        check(QueueFiniteProduct606.multiply(2147483648L,0x3F800000).equals(new QueueFiniteProduct606.Product(false,18014398509481984L,-23)));
        reject(()->QueueFiniteProduct606.multiply(2147483649L,0x3F800000));
        reject(()->QueueFiniteProduct606.multiply(-2147483649L,0x3F800000));
        reject(()->QueueFiniteProduct606.multiply(1,0x7F800000));
        reject(()->QueueFiniteProduct606.multiply(1,0x7FC12345));
        reject(()->new QueueFiniteProduct606.Product(false,-1,0));
        reject(()->new QueueFiniteProduct606.Product(false,36028794871480321L,0));
        reject(()->new QueueFiniteProduct606.Product(false,0,-150));
        reject(()->new QueueFiniteProduct606.Product(false,0,105));
    }
    private static void exactAndZero() {
        normal(0x3F800000,0x3FC00000,0x1F80,0x3FC00000,0x1F80);
        normal(0x40000000,0x40000000,0x0FA0,0x40800000,0x0FA0); // old PE does not create a new trap
        normal(0,0xBF800000,0x1F80,0x80000000,0x1F80);
        normal(0xBF800000,0x80000000,0x1F80,0,0x1F80);
        normal(0x3F800000,0x3FC00000,new Mxcsr(0x1F80,0xFFC0),0x3FC00000,new Mxcsr(0x1F80,0xFFC0));
    }
    private static void roundNormal() {
        int[] pre={0x1F80,0x3F80,0x5F80,0x7F80},post={0x1FA0,0x3FA0,0x5FA0,0x7FA0};
        int[] positive={0x4B000002,0x4B000002,0x4B000003,0x4B000002};
        int[] negative={0xCB000002,0xCB000003,0xCB000002,0xCB000002};
        for(int rc=0;rc<4;rc++) {
            normal(0x4B000001,0x3F800001,pre[rc],positive[rc],post[rc]);
            normal(0xCB000001,0x3F800001,pre[rc],negative[rc],post[rc]);
        }
    }
    private static void normalPrecisionStop() {
        fault(0x4B000001,0x3F800001,0x0F80,0x20,0x0FA0);
        stopped(registers(0x4B000001),0x3F800001,new Mxcsr(0x0F80,0xFFC0),
            StopReason.ARCHITECTURAL_FP_CONDITION,0x20,new Mxcsr(0x0FA0,0xFFE0),1);
    }
    private static void denormalFirst() {
        fault(0x3F800000,1,0,2,2); // DM0 precedes hypothetical U/P, all masks clear
        fault(0,1,0,2,2); // zero left does not remove the denormal operand condition
    }
    private static void unmaskedTiny() {
        fault(0x3F800000,1,0x0780,0x12,0x0792);
        fault(0x3F800000,1,0x8780,0x12,0x8792); // FTZ ignored when UM0
    }
    private static void exactTiny() {
        normal(0x3F800000,1,0x0F80,1,0x0F82); // UM1 FTZ0 PM0: exact subnormal is not new P
        normal(0xBF800000,1,0x0F80,0x80000001,0x0F82);
    }
    private static void flushTiny() {
        fault(0x3F800000,1,0x8F80,0x32,0x8FB2);
        normal(0x3F800000,1,0x9F80,0,0x9FB2);
        normal(0xBF800000,1,0x9F80,0x80000000,0x9FB2);
    }
    private static void daz() {
        normal(0x3F800000,1,0x0040,0,0x0040); // DAZ1 suppresses new D, no masked U/P needed
        normal(0x3F800000,0x80000001,0x0040,0x80000000,0x0040);
    }
    private static void amplifiedDenormal() {
        normal(0x40000000,0x007FFFFF,0x1F80,0x00FFFFFE,0x1F82);
        normal(0x40000000,0x807FFFFF,0x1F80,0x80FFFFFE,0x1F82);
    }
    private static void overflowStops() {
        fault(0x40000000,0x7F7FFFFF,0x0B80,8,0x0B88); // exact unbounded: O only, even PM0
        fault(0x40000000,0x7F7FFFFF,0x0F80,0x28,0x0FA8); // masked O forces P, PM0 stops
        fault(0x40400000,0x7F7FFFFF,0x0B80,0x28,0x0BA8); // inexact unbounded: O plus P
    }
    private static void overflowRounded() {
        int[] pre={0x1F80,0x3F80,0x5F80,0x7F80},post={0x1FA8,0x3FA8,0x5FA8,0x7FA8};
        int[] positive={0x7F800000,0x7F7FFFFF,0x7F800000,0x7F7FFFFF};
        int[] negative={0xFF800000,0xFF800000,0xFF7FFFFF,0xFF7FFFFF};
        for(int rc=0;rc<4;rc++) {
            normal(0x40000000,0x7F7FFFFF,pre[rc],positive[rc],post[rc]);
            normal(0xC0000000,0x7F7FFFFF,pre[rc],negative[rc],post[rc]);
        }
    }
    private static void nanAndInfinity() {
        normal(0x3F800000,0x7FC12345,0,0x7FC12345,0);
        normal(0x3F800000,0xFF812345,0x0080,0xFFC12345,0x0081);
        fault(0x3F800000,0x7F812345,0,1,1);
        normal(0,0x7F800000,0x0080,0xFFC00000,0x0081);
        fault(0,0xFF800000,0,1,1);
        normal(0xBF800000,0x7F800000,0,0xFF800000,0); // infinity operand is not numeric O
    }
    private static void missingUnsupportedAndMarker() {
        stopped(registers(0x3F800000),0x3F800000,Mxcsr.unknown(),StopReason.MISSING_FP_INPUT,0,Mxcsr.unknown(),0);
        stopped(registers(0x3F000000),0x3F800000,Mxcsr.exact(0x1F80),StopReason.UNSUPPORTED_FP_DOMAIN,0,Mxcsr.exact(0x1F80),0);
        stopped(registers(0x80000000),0x3F800000,Mxcsr.exact(0x1F80),StopReason.UNSUPPORTED_FP_DOMAIN,0,Mxcsr.exact(0x1F80),0); // not actual CVT zero
        Registers bad=registers(0x3F800000);bad.x0=new Bits128(0x000000013F800000L,0);
        stopped(bad,0x3F800000,Mxcsr.exact(0x1F80),StopReason.UNSUPPORTED_FP_DOMAIN,0,Mxcsr.exact(0x1F80),0);
        Registers r=registers(0x3F800000);GovernmentCrtBoundary185Api.Entry before=snapshot(r);
        RuntimeException marker=new IllegalStateException("original operand-read marker");Read read=new Read(r,0,marker);
        try {
            QueueGrowthMulss606.execute(IMAGE,r,true,Mxcsr.exact(0x1F80),ORIGIN,read.memory);
            throw new AssertionError("Operand marker swallowed");
        } catch(RuntimeException actual) { check(actual==marker&&read.count==1&&snapshot(r).equals(before)); }
    }
    public static int verify() {
        productCore();exactAndZero();roundNormal();normalPrecisionStop();denormalFirst();
        unmaskedTiny();exactTiny();flushTiny();daz();amplifiedDenormal();overflowStops();
        overflowRounded();nanAndInfinity();missingUnsupportedAndMarker();return 14;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
