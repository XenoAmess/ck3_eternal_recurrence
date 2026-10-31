package org.xar.ck3.research.m1;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.*;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import static org.xar.ck3.research.m1.GovernmentThreadWait179Witness.*;

/** Owner literal fixture directly from original99B after model source was rejected. */
public final class GovernmentThreadWait179FastCase {
    private GovernmentThreadWait179FastCase() { }
    public static Scene scene() {
        long base=0x100000000L, stack=0x9000L, rip=0x5566778899aabbccL;
        VolatileBits in=v(0x1111111180000000L),post=v(0x3333333300000000L);
        NonvolatileBits nv=n(0x2222222200000000L);
        VolatileBits offered=new VolatileBits(0xfedcba9876543210L,0x105c5cb08L,0x105c5cb18L,0x80000001L,
            in.r9Bits(),in.r10Bits(),in.r11Bits(),in.xmm0(),in.xmm1(),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
        return new Scene("fast-rawRax-cfg-fullV",new Entry(base,stack,in,nv),List.of(
            w(0x8ff8L,0x2222222200000000L),r(0x105c5cb40L,0xfedcba9876543210L),r(0x8ff8L,0x2222222200000000L),
            p(new IatCall(0x4223b5aL,0x43dbba8L,0x9000L,true,offered,nv),post),r(0x9000L,rip)
        ),new NormalReturn(post,nv,rip,0x9008L));
    }
}
