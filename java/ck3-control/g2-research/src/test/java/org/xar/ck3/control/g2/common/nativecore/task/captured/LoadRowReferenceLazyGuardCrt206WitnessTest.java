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
public final class LoadRowReferenceLazyGuardCrt206WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }

    @Test void actualLazyGuardCallsBothMatureCoresOnTheSameMemory() {
        long image=0x140000000L,s=0x72000000L,gs=0xFEDC000000100000L;
        long ta=0xABCDEF0000200000L,tb=0xABCDEF0000300000L,guard=image+0x5C673D0L;
        long lock=image+0x5C5CB18L,enter=0xFE00000000000011L,leave=0xFD00000000000022L;
        long finalRip=0xEE00112233445566L;
        Bytes m=new Bytes();m.putQ(s,0x1122334455667788L);m.putQ(gs,ta);m.putD(ta+0x10,-7);
        m.putQ(gs+16,tb);m.putD(guard,0);m.putQ(image+0x43DA500L,enter);m.putQ(image+0x43DA4F0L,leave);
        m.putD(image+0x542F090L,7);m.putD(image+0x5C5CBC4L,2);
        VolatileBits base=v(0x1000),in=q(base,0xAABBCCDDEEFF0011L,0xBBCCDDEEFF001122L,
                0xCCDDEEFF00112233L,base.r8Bits(),base.r9Bits(),base.r10Bits(),base.r11Bits());
        VolatileBits e1=v(0x3000),t1=v(0x4000),e2=v(0x5000),e3=v(0x6000),t2=v(0x7000);
        NonvolatileBits n=nv(0x8000);
        NonvolatileBits local=new NonvolatileBits(guard,n.rbpBits(),n.rsiBits(),n.rdiBits(),
                n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
        List<Call> wantedCalls=List.of(
            new Call(0x4223A94L,TargetKind.INDIRECT_ABSOLUTE,enter,s-0x58,
                    q(in,0xFFFFFFF9L,lock,16,in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits()),local),
            new Call(0x4223A34L,TargetKind.INDIRECT_ABSOLUTE,enter,s-0x58,
                    q(t1,t1.raxBits(),lock,t1.rdxBits(),t1.r8Bits(),t1.r9Bits(),t1.r10Bits(),t1.r11Bits()),local),
            new Call(0x4223A74L,TargetKind.INDIRECT_ABSOLUTE,leave,s-0x58,
                    q(e2,8,lock,2,tb,16,e2.r10Bits(),e2.r11Bits()),local));
        List<Tail> wantedTails=List.of(
            new Tail(0x4223AE4L,TargetKind.INDIRECT_ABSOLUTE,leave,
                    new Entry(image,s-0x30,q(e1,e1.raxBits(),lock,e1.rdxBits(),e1.r8Bits(),e1.r9Bits(),e1.r10Bits(),e1.r11Bits()),n)),
            new Tail(0x4223A7FL,TargetKind.DIRECT_RVA,0x4223AECL,new Entry(image,s-0x30,e3,n)));
        VolatileBits[] replies={e1,e2,e3},tailReplies={t1,t2};int[] callCount={0},tailCount={0},gsCount={0};
        Calls ports=new Ports(){
            public long readGsQword58(){gsCount[0]++;return gs;}
            public VolatileBits invoke(Call call){
                int k=callCount[0]++;assertTrue(k<3);assertEquals(wantedCalls.get(k),call);
                assertEquals(image+call.callSiteRva()+6,m.rawQ(s-0x60));
                return replies[k];
            }
            public NormalReturn tail(Tail tail){
                int k=tailCount[0]++;assertTrue(k<2);assertEquals(wantedTails.get(k),tail);
                long rip=m.readQword(tail.entry().rspBits());
                assertEquals(image+(k==0?0x8CEEE8L:0x8CEF0BL),rip);
                if(k==0) assertEquals(-1,m.rawD(guard));
                if(k==1) {
                    assertEquals(8,m.rawD(guard));assertEquals(8,m.rawD(image+0x542F090L));
                    assertEquals(8,m.rawD(tb+0x10));m.writeQword(s,finalRip);
                }
                return new NormalReturn(tailReplies[k],rip,tail.entry().rspBits()+8,n);
            }
        };
        List<Op> budgets=new ArrayList<>();
        Calls bound=LoadRowReferenceLazyGuardCrt206Calls.bind(image,m,ports,
                (h,a)->budgets.add(new Op("budget",h,a)));
        NormalReturn got=LoadRowReferenceCallee8ceeb0205.execute(new Entry(image,s,in,n),m,bound);
        assertEquals(new NormalReturn(q(t2,image+0x5C673E0L,t2.rcxBits(),t2.rdxBits(),t2.r8Bits(),t2.r9Bits(),t2.r10Bits(),t2.r11Bits()),finalRip,s+8,n),got);
        assertEquals(3,callCount[0]);assertEquals(2,tailCount[0]);assertEquals(2,gsCount[0]);
        assertEquals(List.of(new Op("budget",0x4223A9AL,guard)),budgets);
        assertEquals(List.of(new Op("wb",image+0x5C673E4L,0),new Op("wb",image+0x5C67434L,255)),
                m.ops.stream().filter(o->o.kind().equals("wb")).toList());
        assertEquals(0xA5,m.rawB(image+0x5C673E3L));assertEquals(0xA5,m.rawB(image+0x5C673E5L));
        assertEquals(0xA5,m.rawB(image+0x5C67433L));assertEquals(0xA5,m.rawB(image+0x5C67435L));
        assertEquals(-7,m.rawD(ta+0x10));assertEquals(8,m.rawD(tb+0x10));assertEquals(8,m.rawD(guard));
    }
}
