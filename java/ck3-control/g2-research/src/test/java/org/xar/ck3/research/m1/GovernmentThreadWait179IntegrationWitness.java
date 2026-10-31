package org.xar.ck3.research.m1;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.*;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import static org.xar.ck3.research.m1.GovernmentThreadWait179Witness.*;

/** One new actual Header→Wait composition; strict trace rejects a duplicate CALL push. */
public final class GovernmentThreadWait179IntegrationWitness {
    private GovernmentThreadWait179IntegrationWitness() { }
    private static VolatileBits v4(VolatileBits v,long a,long c,long d,long e) {
        return new VolatileBits(a,c,d,e,v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    public static void main(String[] args) {
        long base=0x100000000L,rip=0x0123456789abcdefL;
        VolatileBits seed=v(0x1111111100000000L),in=v4(seed,seed.raxBits(),0x5000L,seed.rdxBits(),seed.r8Bits());
        VolatileBits enterPost=v(0x3333333300000000L),waitPost=v(0x4444444400000000L),leavePost=v(0x5555555500000000L);
        NonvolatileBits nv=n(0x2222222200000000L);
        NonvolatileBits headerN=new NonvolatileBits(0x5000L,nv.rbpBits(),nv.rsiBits(),nv.rdiBits(),nv.r12Bits(),nv.r13Bits(),nv.r14Bits(),nv.r15Bits(),nv.xmm6());
        VolatileBits enter=v4(in,in.raxBits(),0x105c5cb18L,in.rdxBits(),in.r8Bits());
        VolatileBits dispatch=v4(enterPost,0xfedcba9876543210L,0x105c5cb08L,0x105c5cb18L,100);
        VolatileBits leave=v4(waitPost,waitPost.raxBits(),0x105c5cb18L,waitPost.rdxBits(),waitPost.r8Bits());
        Script script=new Script(List.of(
            w(0xff8L,0x2222222200000000L),w(0xfd0L,0x104223a9aL),
            p(new IatCall(0x4223a94L,0x43da500L,0xfd8L,false,enter,headerN),enterPost),
            dr(0x5000L,0xffffffffL),dr(0x5000L,0xffffffffL),w(0xfd0L,0x104223aaeL),
            w(0xfc8L,0x5000L),r(0x105c5cb40L,0xfedcba9876543210L),r(0xfc8L,0x5000L),
            p(new IatCall(0x4223b5aL,0x43dbba8L,0xfd0L,true,dispatch,headerN),waitPost),r(0xfd0L,0x104223aaeL),
            dr(0x5000L,0),dr(0x5000L,0),dw(0x5000L,0xffffffffL),r(0xff8L,0x2222222200000000L),
            p(new IatCall(0x4223ae4L,0x43da4f0L,0x1000L,true,leave,nv),leavePost),r(0x1000L,rip)
        ));
        int[] waits={0};
        var ports=GovernmentThreadWait179Calls.bind(base,script,script);
        NormalReturn actual=GovernmentThreadHeader178.execute(new Entry(base,0x1000L,in,nv),script,ports,(site,address,guard)->{
            if(site!=0x4223aa4L||address!=0x5000L||guard!=-1) throw new AssertionError("wrong wait budget input");
            waits[0]++;
        });
        script.complete();
        if(waits[0]!=1||!actual.equals(new NormalReturn(leavePost,nv,rip,0x1008L))) throw new AssertionError("composition result");
        System.out.println("PASS one new Header→Wait composition; single caller push/full V/N");
    }
}
