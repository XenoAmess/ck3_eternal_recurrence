package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Snapshot;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.StopReason;

/** Owner sufficient MULSS385 domain with zero new FP conditions for any MXCSR:
 * actual CVT integer left, fresh normal finite right, exact normal or signed-zero result.
 * Other domains stop as unsupported software admission; no FP condition is fabricated. */
public final class QueueGrowthPartialMulss611 {
    private QueueGrowthPartialMulss611() { }
    private static QueueGrowthMulss606.NotCompleted unsupported(long image,Registers r,
            boolean df,Mxcsr state,long origin) {
        var entry=new GovernmentCrtBoundary185Api.Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits());
        return new QueueGrowthMulss606.NotCompleted(new Stopped(StopReason.UNSUPPORTED_FP_DOMAIN,
            new Snapshot(entry,0x880385,df,state),0,origin));
    }
    private static Long integerLeft(int bits) {
        int magnitudeBits=bits&0x7FFFFFFF;
        if(magnitudeBits==0)return bits==0?Long.valueOf(0):null;
        int field=magnitudeBits>>>23,exponent=field-127;
        if(field==0||field==255||exponent<0||exponent>31)return null;
        long significand=0x800000L|(magnitudeBits&0x7FFFFF),magnitude;
        if(exponent>=23)magnitude=significand<<(exponent-23);
        else {
            int shift=23-exponent;
            if((significand&((1L<<shift)-1))!=0)return null;
            magnitude=significand>>>shift;
        }
        if(magnitude>0x80000000L)return null;
        return Long.valueOf(bits<0?-magnitude:magnitude);
    }
    public static QueueGrowthMulss606.Result execute(long imageBaseBits,Registers r,
            boolean directionFlagSet,Mxcsr mxcsr,long originCallSiteRva,QueueAppend597Api.Memory memory) {
        Objects.requireNonNull(r);Objects.requireNonNull(r.x0);Objects.requireNonNull(mxcsr);Objects.requireNonNull(memory);
        Long left=integerLeft((int)r.x0.lowBits());
        if(left==null||r.x0.highBits()!=0||(r.x0.lowBits()>>>32)!=0)
            return unsupported(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva);
        int right=memory.readDword(imageBaseBits+0x49F64F0L); // once, before commit; never reread via fallback
        int field=(right>>>23)&0xFF;
        if(field==0||field==255)return unsupported(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva);
        var encoded=QueueExactNormalProduct611.encode(QueueFiniteProduct606.multiply(left.longValue(),right));
        if(encoded.isEmpty())return unsupported(imageBaseBits,r,directionFlagSet,mxcsr,originCallSiteRva);
        Bits128 prior=r.x0;
        r.x0=new Bits128((prior.lowBits()&0xFFFFFFFF00000000L)|Integer.toUnsignedLong(encoded.getAsInt()),prior.highBits());
        return new QueueGrowthMulss606.Completed(mxcsr);
    }
}
