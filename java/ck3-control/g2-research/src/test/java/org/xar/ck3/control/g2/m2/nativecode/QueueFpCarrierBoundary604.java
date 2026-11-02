package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.QueueCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Snapshot;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner frozen-contract checks only: no FP arithmetic, native state, old entry, or Memory. */
public final class QueueFpCarrierBoundary604 {
    private QueueFpCarrierBoundary604() { }
    private static final long IMAGE=0x140000000L, SP=0x8100000000009000L;
    private static final Bits128 X0=new Bits128(0xA000000000000001L,0xB000000000000002L);
    private static final Bits128 X1=new Bits128(0xA100000000000003L,0xB100000000000004L);
    private static final Bits128 X2=new Bits128(0xA200000000000005L,0xB200000000000006L);
    private static final Bits128 X3=new Bits128(0xA300000000000007L,0xB300000000000008L);
    private static final Bits128 X4=new Bits128(0xA400000000000009L,0xB40000000000000AL);
    private static final Bits128 X5=new Bits128(0xA50000000000000BL,0xB50000000000000CL);
    private static final Bits128 X6=new Bits128(0xA60000000000000DL,0xB60000000000000EL);
    private static final VolatileBits V=new VolatileBits(0x8000000000000001L,0x8100000000000002L,
        0x8200000000000003L,0x8300000000000004L,0x8400000000000005L,
        0x8500000000000006L,0x8600000000000007L,X0,X1,X2,X3,X4,X5);
    private static final NonvolatileBits N=new NonvolatileBits(0x9100000000000001L,
        0x9200000000000002L,0x9300000000000003L,0x9400000000000004L,
        0x9500000000000005L,0x9600000000000006L,0x9700000000000007L,
        0x9800000000000008L,X6);
    private static final GovernmentCrtBoundary185Api.Entry ENTRY=
        new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,V,N);

    private static void check(boolean condition) {
        if(!condition) throw new AssertionError("604 contract mismatch");
    }
    private static void reject(Class<? extends Throwable> expected,Runnable task) {
        try { task.run(); }
        catch(Throwable actual) {
            if(actual.getClass()!=expected) throw new AssertionError("Wrong rejection",actual);
            return;
        }
        throw new AssertionError("Missing rejection "+expected.getName());
    }
    private static void canonical() {
        check(Mxcsr.unknown().equals(new Mxcsr(0,0)));
        check(!Mxcsr.unknown().isExact());
        reject(IllegalStateException.class,()->Mxcsr.unknown().requireExactBits());
        int[] exact={0,0x1F80,0x1FA0,0xFFFF};
        for(int bits:exact) {
            Mxcsr x=Mxcsr.exact(bits);
            check(x.isExact()&&x.valueBits()==bits&&x.knownMaskBits()==0xFFFF);
            check(x.requireExactBits()==bits);
        }
        Mxcsr partial=new Mxcsr(0x1F80,0xFFC0);
        check(!partial.isExact()&&partial.valueBits()==0x1F80&&partial.knownMaskBits()==0xFFC0);
        reject(IllegalStateException.class,partial::requireExactBits);
        int[][] invalid={{-1,0xFFFF},{0x10000,0xFFFF},{0,-1},{0,0x10000},{1,0},{0x20,0xFFC0}};
        for(int[] x:invalid) reject(IllegalArgumentException.class,()->new Mxcsr(x[0],x[1]));
        reject(IllegalArgumentException.class,()->Mxcsr.exact(-1));
        reject(IllegalArgumentException.class,()->Mxcsr.exact(0x10000));
    }
    private static FullCopy437Api.CallResult baseResult(long rip,long sp,NonvolatileBits nv) {
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(V,rip,sp,nv),true);
    }
    private static void unknownTransport() {
        GovernmentCrtBoundary185Api.LoopBudget budget=(header,address)->{
            throw new AssertionError("API called budget");
        };
        FullCopy437Api.Input base=new FullCopy437Api.Input(ENTRY,true,budget);
        Mxcsr unknown=Mxcsr.unknown();Input input=new Input(base,unknown);
        check(input.base()==base&&input.mxcsr()==unknown&&input.base().budget()==budget);
        FullCopy437Api.CallResult nr=baseResult(IMAGE+0x1111,SP+8,N);
        Normal normal=new Normal(nr,unknown);
        check(normal.base()==nr&&normal.base().normalReturn()==nr.normalReturn());
        check(normal.postMxcsr()==unknown&&!normal.postMxcsr().isExact());
        check(normal.base().normalReturn().volatileBits()==V&&normal.base().normalReturn().nonvolatileBits()==N);
        reject(NullPointerException.class,()->new Input(null,unknown));
        reject(NullPointerException.class,()->new Input(base,null));
        reject(NullPointerException.class,()->new Normal(null,unknown));
        reject(NullPointerException.class,()->new Normal(nr,null));
    }
    private static void controlGuard() {
        Mxcsr pre=Mxcsr.exact(0x1F80);
        QueueFp604Api.requireKnownControlsPreserved(pre,Mxcsr.exact(0x1FA0));
        QueueFp604Api.requireKnownControlsPreserved(pre,Mxcsr.exact(0x1FBF));
        QueueFp604Api.requireKnownControlsPreserved(new Mxcsr(0x1F80,0xFFC0),Mxcsr.exact(0x1FA0));
        reject(IllegalArgumentException.class,()->QueueFp604Api.requireKnownControlsPreserved(pre,Mxcsr.exact(0x3F80)));
        reject(IllegalStateException.class,()->QueueFp604Api.requireKnownControlsPreserved(Mxcsr.unknown(),pre));
        reject(IllegalStateException.class,()->QueueFp604Api.requireKnownControlsPreserved(pre,new Mxcsr(0,0x003F)));
        reject(NullPointerException.class,()->QueueFp604Api.requireKnownControlsPreserved(null,pre));
        reject(NullPointerException.class,()->QueueFp604Api.requireKnownControlsPreserved(pre,null));
    }
    private static GovernmentCrtBoundary185Api.Call call(long site,long target,boolean indirect) {
        return new GovernmentCrtBoundary185Api.Call(site,indirect?
            GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:
            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,SP,V,N);
    }
    private static GovernmentCrtBoundary185Api.Entry child() {
        return new GovernmentCrtBoundary185Api.Entry(IMAGE,SP-8,V,N);
    }
    private static Normal actual(long rip,long sp,NonvolatileBits nv,int mxcsr) {
        return new Normal(baseResult(rip,sp,nv),Mxcsr.exact(mxcsr));
    }
    private static final NonvolatileBits WRONG_N=new NonvolatileBits(9,N.rbpBits(),N.rsiBits(),N.rdiBits(),
        N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
    private static QueueCallFrame queueFrame(long site,long target,long returnRva) {
        return new QueueCallFrame(new EmbeddedQueue591Api.CallFrame(call(site,target,false),child(),true,5,IMAGE+returnRva),Mxcsr.exact(0x1F80));
    }
    private static AppendCallFrame appendFrame(long site,long target,int length,long returnRva) {
        return new AppendCallFrame(new QueueAppend597Api.CallFrame(call(site,target,length==3),child(),true,length,IMAGE+returnRva),Mxcsr.exact(0x1F80));
    }
    private static void frames() {
        long[][] queues={{0x3727ECF,0x3727580,0x3727ED4},{0x3727F0D,0x880340,0x3727F12}};
        for(long[] row:queues) {
            QueueCallFrame frame=queueFrame(row[0],row[1],row[2]);long rip=IMAGE+row[2];
            Normal ok=actual(rip,SP,N,0x1FA0);frame.checkNormalReturn(ok);
            check(frame.base().call().callSiteRva()==row[0]&&frame.preMxcsr().requireExactBits()==0x1F80);
            frame.checkNormalReturn(actual(rip,SP,N,0x3F80)); // controls policy is deliberately separate
            reject(IllegalArgumentException.class,()->frame.checkNormalReturn(actual(rip+1,SP,N,0x1FA0)));
            reject(IllegalArgumentException.class,()->frame.checkNormalReturn(actual(rip,SP+8,N,0x1FA0)));
            reject(IllegalArgumentException.class,()->frame.checkNormalReturn(actual(rip,SP,WRONG_N,0x1FA0)));
            reject(NullPointerException.class,()->frame.checkNormalReturn(null));
        }
        long[][] appends={{0x88039F,0x7FFF000000001001L,3,0x8803A2},
            {0x8803C5,0x4226860,5,0x8803CA},{0x8803DA,0x7FFF000000002002L,3,0x8803DD}};
        for(long[] row:appends) {
            AppendCallFrame frame=appendFrame(row[0],row[1],(int)row[2],row[3]);long rip=IMAGE+row[3];
            frame.checkNormalReturn(actual(rip,SP,N,0x1FA0));
            check(frame.base().call().targetBits()==row[1]&&frame.base().childEntry().rspBits()==SP-8);
            frame.checkNormalReturn(actual(rip,SP,N,0x3F80));
            reject(IllegalArgumentException.class,()->frame.checkNormalReturn(actual(rip+1,SP,N,0x1FA0)));
            reject(IllegalArgumentException.class,()->frame.checkNormalReturn(actual(rip,SP+8,N,0x1FA0)));
            reject(IllegalArgumentException.class,()->frame.checkNormalReturn(actual(rip,SP,WRONG_N,0x1FA0)));
            reject(NullPointerException.class,()->frame.checkNormalReturn(null));
        }
        reject(NullPointerException.class,()->new QueueCallFrame(null,Mxcsr.unknown()));
        reject(NullPointerException.class,()->new AppendCallFrame(null,Mxcsr.unknown()));
        reject(NullPointerException.class,()->new QueueCallFrame(queueFrame(0x3727ECF,0x3727580,0x3727ED4).base(),null));
        reject(NullPointerException.class,()->new AppendCallFrame(appendFrame(0x88039F,0x1000,3,0x8803A2).base(),null));
    }
    private static void snapshots() {
        Mxcsr state=Mxcsr.exact(0x1F80);Snapshot snapshot=new Snapshot(ENTRY,0x88037B,true,state);
        Stopped missing=new Stopped(StopReason.MISSING_FP_INPUT,snapshot,0,0);
        Stopped condition=new Stopped(StopReason.ARCHITECTURAL_FP_CONDITION,snapshot,0x20,0x3727F0D);
        check(missing.snapshot()==snapshot&&missing.reason()==StopReason.MISSING_FP_INPUT);
        check(condition.snapshot().currentState()==ENTRY&&snapshot.mxcsr()==state&&snapshot.directionFlagSet());
        check(snapshot.currentState().volatileBits().xmm0()==X0&&snapshot.currentState().nonvolatileBits().xmm6()==X6);
        check(snapshot.currentState().rspBits()==SP&&snapshot.instructionRva()==0x88037B);
        check(condition.raisedConditionBits()==0x20&&condition.originCallSiteRva()==0x3727F0D);
        new Snapshot(ENTRY,0x123456,true,Mxcsr.unknown()); // no invented PC whitelist
        for(StopReason reason:StopReason.values()) {
            new Stopped(reason,snapshot,0,0);
            if(reason!=StopReason.ARCHITECTURAL_FP_CONDITION)
                reject(IllegalArgumentException.class,()->new Stopped(reason,snapshot,1,0));
        }
        reject(IllegalArgumentException.class,()->new Stopped(StopReason.ARCHITECTURAL_FP_CONDITION,snapshot,-1,0));
        reject(IllegalArgumentException.class,()->new Stopped(StopReason.ARCHITECTURAL_FP_CONDITION,snapshot,0x40,0));
        reject(NullPointerException.class,()->new Stopped(null,snapshot,0,0));
        reject(NullPointerException.class,()->new Stopped(StopReason.MISSING_FP_INPUT,null,0,0));
        reject(NullPointerException.class,()->new Snapshot(null,0,true,state));
        reject(NullPointerException.class,()->new Snapshot(ENTRY,0,true,null));
    }
    private static void callbacks() {
        QueueCallFrame q=queueFrame(0x3727F0D,0x880340,0x3727F12);
        AppendCallFrame a=appendFrame(0x88039F,0x7FFF010101010101L,3,0x8803A2);
        Normal normal=actual(IMAGE+0x3727F12,SP,N,0x1FA0);
        Stopped stop=new Stopped(StopReason.ARCHITECTURAL_FP_CONDITION,
            new Snapshot(ENTRY,0x880385,true,Mxcsr.exact(0x9FA0)),0x20,0x3727F0D);
        QueueFp604Api.QueueCalls queue=offered->{check(offered==q);return normal;};
        QueueFp604Api.AppendCalls append=offered->{check(offered==a);return stop;};
        check(queue.invoke(q)==normal&&append.invoke(a)==stop);
        RuntimeException marker=new IllegalStateException("original callback marker");
        QueueFp604Api.QueueCalls bad=offered->{check(offered==q);throw marker;};
        try { bad.invoke(q);throw new AssertionError("Callback unexpectedly returned"); }
        catch(RuntimeException actual) { check(actual==marker); }
        check(normal.postMxcsr().requireExactBits()==0x1FA0);
    }
    public static int verify() {
        canonical();unknownTransport();controlGuard();frames();snapshots();callbacks();return 6;
    }
    public static void main(String[] args) { System.out.println(verify()); }
}
