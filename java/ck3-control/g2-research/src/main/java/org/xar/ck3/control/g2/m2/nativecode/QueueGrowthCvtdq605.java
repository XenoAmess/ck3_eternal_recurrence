package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Snapshot;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner implementation of actual CVTDQ2PS88037B after the held MOVD zero-upper96.
 * Only represented SSE128 state and Precision condition; no OS delivery, later FP or spill. */
public final class QueueGrowthCvtdq605 {
    private QueueGrowthCvtdq605() { }
    public sealed interface Result permits Completed,NotCompleted { }
    public record Completed(Mxcsr mxcsr) implements Result {
        public Completed { Objects.requireNonNull(mxcsr); }
    }
    public record NotCompleted(Stopped stopped) implements Result {
        public NotCompleted { Objects.requireNonNull(stopped); }
    }
    private static NotCompleted stop(long image,Registers r,boolean df,Mxcsr state,
            long origin,StopReason reason,int conditions) {
        var entry=new GovernmentCrtBoundary185Api.Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits());
        return new NotCompleted(new Stopped(reason,new Snapshot(entry,0x88037B,df,state),conditions,origin));
    }
    public static Result execute(long imageBaseBits,Registers r,boolean directionFlagSet,
            Mxcsr mxcsr,long originCallSiteRva) {
        Objects.requireNonNull(r);Objects.requireNonNull(mxcsr);Objects.requireNonNull(r.x0);
        if(r.x0.highBits()!=0 || (r.x0.lowBits()>>>32)!=0)
            return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.UNSUPPORTED_FP_DOMAIN,0);
        int source=(int)r.x0.lowBits();
        long magnitude=source<0?-(long)source:(long)source;
        if(magnitude==0) {
            r.x0=new Bits128(0,0);return new Completed(mxcsr);
        }
        int exponent=63-Long.numberOfLeadingZeros(magnitude);
        int shift=Math.max(0,exponent-23);
        long significand=exponent<=23?magnitude<<(23-exponent):magnitude>>>shift;
        long remainder=magnitude&((1L<<shift)-1);
        Mxcsr post=mxcsr;
        if(remainder!=0) {
            if((mxcsr.knownMaskBits()&0x1000)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.MISSING_FP_INPUT,0);
            post=new Mxcsr(mxcsr.valueBits()|0x20,mxcsr.knownMaskBits()|0x20);
            if((mxcsr.valueBits()&0x1000)==0)
                return stop(imageBaseBits,r,directionFlagSet,post,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,0x20);
            if((mxcsr.knownMaskBits()&0x6000)!=0x6000)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.MISSING_FP_INPUT,0);
            int rounding=(mxcsr.valueBits()>>>13)&3;
            boolean increment=false;
            if(rounding==0) {
                long half=1L<<(shift-1);
                increment=remainder>half || (remainder==half && (significand&1)!=0);
            } else if(rounding==1) increment=source<0;
            else if(rounding==2) increment=source>0;
            if(increment) significand++;
        }
        if(significand==(1L<<24)) { significand>>>=1;exponent++; }
        int bits=(source<0?0x80000000:0)|((exponent+127)<<23)|((int)significand&0x7FFFFF);
        r.x0=new Bits128(Integer.toUnsignedLong(bits),0);
        return new Completed(post);
    }
}
