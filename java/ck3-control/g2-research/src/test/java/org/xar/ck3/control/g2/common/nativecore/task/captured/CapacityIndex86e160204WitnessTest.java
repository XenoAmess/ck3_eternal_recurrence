package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
public final class CapacityIndex86e160204WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }
    @Test void directSmallAndLargeKeepAllSourceRegisterEffects() {
        long image=0x140000000L,s=0x200000L,rip=0x123456789ABCDEF0L;
        NonvolatileBits n=nv(0x9000);
        VolatileBits a=q(v(0x1000),0xAA55,0x11223344FFFFFFFFL,0xFEDCBA9880000005L,0x11112222,0x33334444,0x55556666,0x77778888);
        VolatileBits b=q(v(0x2000),0x55AA,0x1234567800000002L,0x765432107FFFFFFFL,0xAAAA1111L,0xBBBB2222L,0xCCCC3333L,0xDDDD4444L);
        VolatileBits wa=q(a,3,0x80000005L,a.rdxBits(),0,0x80000005L,a.r10Bits(),a.r11Bits());
        VolatileBits wb=q(b,3,0x80000000L,31,1,0x7fffffffL,b.r10Bits(),b.r11Bits());
        VolatileBits[] inputs={a,b},expected={wa,wb};
        for(int i=0;i<inputs.length;i++) {
            Bytes m=new Bytes();m.putQ(s,rip);
            NormalReturn actual=CapacityIndex86e160204.execute(new Entry(image,s,inputs[i],n),m);
            assertEquals(new NormalReturn(expected[i],rip,s+8,n),actual);
            assertEquals(List.of(new Op("rq",s,rip)),m.ops);
        }
    }

    @Test void threeActualParentsUseSamePhysicalReturnSlot() {
        long image=0x140000000L,pre=0x300000L;
        VolatileBits in=q(v(0x3000),0x1234,0x9876543200000003L,0x7654321000000005L,0x4321,0x2345,0x3456,0x4567);
        VolatileBits expected=q(in,7,7,30,2,5,in.r10Bits(),in.r11Bits());NonvolatileBits n=nv(0xA000);
        for(long site:new long[]{0x337BB7CL,0x337C051L,0x337C873L}) {
            Bytes m=new Bytes();long next=image+site+5;m.writeQword(pre-8,next);
            Calls bound=CapacityIndex86e160204Calls.bind(image,m,new Ports());
            assertEquals(expected,bound.invoke(new Call(site,TargetKind.DIRECT_RVA,0x86E160L,pre,in,n)));
            assertEquals(List.of(new Op("wq",pre-8,next),new Op("rq",pre-8,next)),m.ops);
        }
    }
}
