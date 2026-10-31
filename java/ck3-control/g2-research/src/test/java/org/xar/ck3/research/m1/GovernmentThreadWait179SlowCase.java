package org.xar.ck3.research.m1;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.*;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import static org.xar.ck3.research.m1.GovernmentThreadWait179Witness.*;

/** Owner literal slow fixture: no target execution is used to create expected values. */
public final class GovernmentThreadWait179SlowCase {
    private GovernmentThreadWait179SlowCase() { }
    public static Scene scene() {
        long base=0x100000000L,stack=0x9000L,rip=0x66778899aabbccddL;
        VolatileBits in=v(0x1111111180000000L),post1=v(0x3333333300000000L),post2=v(0x4444444400000000L),post3=v(0x5555555500000000L);
        NonvolatileBits nv=n(0x2222222200000000L);
        NonvolatileBits during=new NonvolatileBits(0x80000001L,nv.rbpBits(),nv.rsiBits(),nv.rdiBits(),nv.r12Bits(),nv.r13Bits(),nv.r14Bits(),nv.r15Bits(),nv.xmm6());
        VolatileBits first=new VolatileBits(0,0x105c5cb18L,in.rdxBits(),in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits(),
            in.xmm0(),in.xmm1(),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
        VolatileBits second=new VolatileBits(post1.raxBits(),0xabcdef0123456789L,0x80000001L,0,post1.r9Bits(),post1.r10Bits(),post1.r11Bits(),
            post1.xmm0(),post1.xmm1(),post1.xmm2(),post1.xmm3(),post1.xmm4(),post1.xmm5());
        VolatileBits tail=new VolatileBits(post2.raxBits(),0x105c5cb18L,post2.rdxBits(),post2.r8Bits(),post2.r9Bits(),post2.r10Bits(),post2.r11Bits(),
            post2.xmm0(),post2.xmm1(),post2.xmm2(),post2.xmm3(),post2.xmm4(),post2.xmm5());
        return new Scene("slow-twoCalls-enterTail-fullV",new Entry(base,stack,in,nv),List.of(
            w(0x8ff8L,0x2222222200000000L),r(0x105c5cb40L,0),w(0x8fd0L,0x104223b6eL),
            p(new IatCall(0x4223b68L,0x43da4f0L,0x8fd8L,false,first,during),post1),r(0x105c5cb10L,0xabcdef0123456789L),
            w(0x8fd0L,0x104223b80L),p(new IatCall(0x4223b7aL,0x43da518L,0x8fd8L,false,second,during),post2),
            r(0x8ff8L,0x2222222200000000L),p(new IatCall(0x4223b8cL,0x43da500L,0x9000L,true,tail,nv),post3),r(0x9000L,rip)
        ),new NormalReturn(post3,nv,rip,0x9008L));
    }
}
