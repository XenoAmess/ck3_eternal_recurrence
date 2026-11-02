package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Snapshot;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner actual CVTTSS2SI r32,xmm0 at88038D. Explicit MXCSR knowledge only;
 * no host FP, Memory, OS delivery, CALL/RET or whole227 implementation. */
public final class QueueGrowthCvtt607 {
    private QueueGrowthCvtt607() { }
    public sealed interface Result permits Completed,NotCompleted { }
    public record Completed(Mxcsr mxcsr) implements Result {
        public Completed { Objects.requireNonNull(mxcsr); }
    }
    public record NotCompleted(Stopped stopped) implements Result {
        public NotCompleted { Objects.requireNonNull(stopped); }
    }
    private static Mxcsr raised(Mxcsr state,int flags) {
        return flags==0?state:new Mxcsr(state.valueBits()|flags,state.knownMaskBits()|flags);
    }
    private static NotCompleted stop(long image,Registers r,boolean df,Mxcsr state,
            long origin,StopReason reason,int flags) {
        var entry=new GovernmentCrtBoundary185Api.Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits());
        return new NotCompleted(new Stopped(reason,new Snapshot(entry,0x88038D,df,raised(state,flags)),flags,origin));
    }
    private static Completed commit(Registers r,int bits,Mxcsr state,int flags) {
        r.rax=Integer.toUnsignedLong(bits); // architectural r32 write zeroextends
        return new Completed(raised(state,flags));
    }
    private static Result invalid(long image,Registers r,boolean df,Mxcsr state,long origin) {
        if((state.knownMaskBits()&0x80)==0)
            return stop(image,r,df,state,origin,StopReason.MISSING_FP_INPUT,0);
        if((state.valueBits()&0x80)==0)
            return stop(image,r,df,state,origin,StopReason.ARCHITECTURAL_FP_CONDITION,1);
        return commit(r,0x80000000,state,1);
    }
    public static Result execute(long imageBaseBits,Registers r,boolean directionFlagSet,
            Mxcsr mxcsr,long originCallSiteRva) {
        Objects.requireNonNull(r);Objects.requireNonNull(r.x0);Objects.requireNonNull(mxcsr);
        int bits=(int)r.x0.lowBits(),field=(bits>>>23)&0xFF,fraction=bits&0x7FFFFF;
        if(field==255) return invalid(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva);
        if(field==0&&fraction!=0) {
            // Global DAZ substitution is independent of CVTT's absence of Denormal exceptions.
            if((mxcsr.knownMaskBits()&0x40)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.MISSING_FP_INPUT,0);
            if((mxcsr.valueBits()&0x40)!=0) return commit(r,0,mxcsr,0);
        }
        QueueFiniteTruncate607.Result value=QueueFiniteTruncate607.truncate(bits);
        if(value instanceof QueueFiniteTruncate607.OutOfRange)
            return invalid(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva);
        QueueFiniteTruncate607.Integral integral=(QueueFiniteTruncate607.Integral)value;
        if(!integral.inexact()) return commit(r,integral.valueBits(),mxcsr,0);
        if((mxcsr.knownMaskBits()&0x1000)==0)
            return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.MISSING_FP_INPUT,0);
        if((mxcsr.valueBits()&0x1000)==0)
            return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,0x20);
        return commit(r,integral.valueBits(),mxcsr,0x20);
    }
}
