package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Snapshot;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner actual MULSS880385 in the source-proven CVT(signedDWORD) left domain.
 * Explicit software controls/capability domain only; no host FP, OS handler or whole227. */
public final class QueueGrowthMulss606 {
    private QueueGrowthMulss606() { }
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
        return new NotCompleted(new Stopped(reason,new Snapshot(entry,0x880385,df,raised(state,flags)),flags,origin));
    }
    private static Completed commit(Registers r,int bits,Mxcsr state,int flags) {
        Bits128 prior=r.x0;
        r.x0=new Bits128((prior.lowBits()&0xFFFFFFFF00000000L)|Integer.toUnsignedLong(bits),prior.highBits());
        return new Completed(raised(state,flags));
    }
    private static Long integerLeft(int bits) {
        int magnitudeBits=bits&0x7FFFFFFF;
        if(magnitudeBits==0) return bits==0?Long.valueOf(0):null; // actual CVT produces +0 only
        int field=magnitudeBits>>>23,exponent=field-127;
        if(field==0||field==255||exponent<0||exponent>31) return null;
        long significand=0x800000L|(magnitudeBits&0x7FFFFF),magnitude;
        if(exponent>=23) magnitude=significand<<(exponent-23);
        else {
            int shift=23-exponent;
            if((significand&((1L<<shift)-1))!=0) return null;
            magnitude=significand>>>shift;
        }
        if(magnitude>0x80000000L) return null;
        return Long.valueOf(bits<0?-magnitude:magnitude);
    }
    public static Result execute(long imageBaseBits,Registers r,boolean directionFlagSet,
            Mxcsr mxcsr,long originCallSiteRva,QueueAppend597Api.Memory memory) {
        Objects.requireNonNull(r);Objects.requireNonNull(r.x0);Objects.requireNonNull(mxcsr);Objects.requireNonNull(memory);
        Long decoded=integerLeft((int)r.x0.lowBits());
        if(r.x0.highBits()!=0||(r.x0.lowBits()>>>32)!=0||decoded==null)
            return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.UNSUPPORTED_FP_DOMAIN,0);
        // Conservative software admission before instruction/operand access, not a hardware-fault claim.
        if((mxcsr.knownMaskBits()&0xFFC0)!=0xFFC0)
            return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.MISSING_FP_INPUT,0);
        long left=decoded.longValue();
        int right=memory.readDword(imageBaseBits+0x49F64F0L); // actual fresh operand at385
        int exponentField=(right>>>23)&0xFF,fraction=right&0x7FFFFF,controls=mxcsr.valueBits();
        boolean negative=(left<0)^(right<0);
        int sign=negative?0x80000000:0;
        if(exponentField==255) {
            if(fraction!=0) {
                if((fraction&0x400000)!=0) return commit(r,right,mxcsr,0); // unique right QNaN
                if((controls&0x80)==0)
                    return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,1);
                return commit(r,right|0x400000,mxcsr,1);
            }
            if(left!=0) return commit(r,sign|0x7F800000,mxcsr,0);
            if((controls&0x80)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,1);
            return commit(r,0xFFC00000,mxcsr,1);
        }
        int flags=0;
        if(exponentField==0&&fraction!=0) {
            if((controls&0x40)!=0) return commit(r,sign,mxcsr,0); // DAZ input signed zero
            flags=2;
            if((controls&0x100)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,flags);
        }
        QueueFiniteProduct606.Product exact=QueueFiniteProduct606.multiply(left,right);
        long coefficient=exact.coefficient();
        sign=exact.negative()?0x80000000:0;
        if(coefficient==0) return commit(r,sign,mxcsr,flags);
        int top=63-Long.numberOfLeadingZeros(coefficient),shift=Math.max(0,top-23);
        long significand=top<=23?coefficient<<(23-top):coefficient>>>shift;
        long remainder=coefficient&((1L<<shift)-1);
        boolean inexact=remainder!=0;
        int rounding=(controls>>>13)&3;
        if(inexact) {
            boolean increment;
            if(rounding==0) {
                long half=1L<<(shift-1);
                increment=remainder>half||(remainder==half&&(significand&1)!=0);
            } else increment=rounding==1?exact.negative():rounding==2&&!exact.negative();
            if(increment) significand++;
        }
        if(significand==(1L<<24)) { significand>>>=1;top++; }
        int exponent=top+exact.exponent2(); // rounded24-bit significand, unbounded exponent
        if(exponent>127) {
            flags|=8;
            if((controls&0x400)==0) {
                if(inexact) flags|=0x20;
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,flags);
            }
            flags|=0x20;
            if((controls&0x1000)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,flags);
            boolean infinity=rounding==0||(rounding==1&&exact.negative())||(rounding==2&&!exact.negative());
            return commit(r,sign|(infinity?0x7F800000:0x7F7FFFFF),mxcsr,flags);
        }
        if(exponent<-126) {
            // Source proof: integer CVT output times a subnormal can be tiny only exactly on 2^-149 grid.
            if(exact.exponent2()!=-149||coefficient>=0x800000||inexact)
                throw new IllegalStateException("MULSS source-domain tiny proof violated");
            if((controls&0x800)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,flags|0x10);
            if((controls&0x8000)==0) return commit(r,sign|(int)coefficient,mxcsr,flags);
            flags|=0x30;
            if((controls&0x1000)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,flags);
            return commit(r,sign,mxcsr,flags);
        }
        if(inexact) {
            flags|=0x20;
            if((controls&0x1000)==0)
                return stop(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva,StopReason.ARCHITECTURAL_FP_CONDITION,flags);
        }
        return commit(r,sign|((exponent+127)<<23)|((int)significand&0x7FFFFF),mxcsr,flags);
    }
}
