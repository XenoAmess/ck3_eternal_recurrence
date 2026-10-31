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
public final class LoadRowReferenceCallee337c040203WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }
    static final LoadRowReferenceCallee337b7e0199Api.Float32 NO_FP = new LoadRowReferenceCallee337b7e0199Api.Float32() {
        public int convertSignedDwordToFloatBits(int n) { throw new AssertionError("convert "+n); }
        public int divideScalarFloatBits(int a,int b) { throw new AssertionError("divide"); }
        public boolean orderedAbove(int a,int b) { throw new AssertionError("compare"); }
    };
    static final LoopBudget NO_LOOP = (header,cursor) -> { throw new AssertionError("budget"); };
    @Test void normalTailUsesActualReturnedR10AndParentAdapter() {
        final long image=0x140000000L,pre=0x200000L,self=0x500000L;
        VolatileBits base=v(0x1000),in=q(base,0xA100000000000111L,self,0x112233L,0x445566L,0x778899L,0xABCDEF,0x987654);
        NonvolatileBits n=nv(0x8000);
        for(boolean adapter:new boolean[]{false,true}) {
            Bytes m=new Bytes();long s=adapter?pre-8:pre,w=s-0x28;
            m.putD(self+0x14,0x7fffffff);m.putQ(s,0x5555666677778888L);
            if(adapter)m.writeQword(pre-8,image+0x337BAEA+5);
            VolatileBits returned=q(v(0x9000),0xAABBCCDDFFFFFFFFL,31,32,33,34,0xFEDCBA9876543210L,36);
            VolatileBits first=q(in,in.raxBits(),0x80000000L,1,in.r8Bits(),in.r9Bits(),self,in.r11Bits());
            VolatileBits tail=q(returned,returned.raxBits(),returned.r10Bits(),0xffffffffL,returned.r8Bits(),returned.r9Bits(),returned.r10Bits(),returned.r11Bits());
            NormalReturn actual=adapter?new NormalReturn(v(0xB000),image+0x337BAEA+5,pre,n):new NormalReturn(v(0xC000),0xDDDDEEEEL,0xFFFF0000L,nv(0xD000));
            List<Call> calls=new ArrayList<>();List<Tail> tails=new ArrayList<>();
            Calls ports=new Ports(){
                public VolatileBits invoke(Call c){calls.add(c);assertEquals(image+0x337C056,m.rawQ(w-8));return returned;}
                public NormalReturn tail(Tail t){tails.add(t);return actual;}
            };
            if(adapter) {
                Calls bound=LoadRowReferenceCallees337c203Calls.bind(image,m,ports,NO_LOOP,NO_FP);
                assertSame(actual.volatileBits(),bound.invoke(new Call(0x337BAEAL,TargetKind.DIRECT_RVA,0x337C040L,pre,in,n)));
            } else assertSame(actual,LoadRowReferenceCallee337c040203.execute(new Entry(image,s,in,n),m,ports));
            assertEquals(List.of(new Call(0x337C051L,TargetKind.DIRECT_RVA,0x86E160L,w,first,n)),calls);
            assertEquals(List.of(new Tail(0x337C064L,TargetKind.DIRECT_RVA,0x337C0C0L,new Entry(image,s,tail,n))),tails);
            List<Op> expected=new ArrayList<>();
            if(adapter)expected.add(new Op("wq",s,image+0x337BAEA+5));
            expected.add(new Op("rd",self+0x14,0x7fffffff));expected.add(new Op("wq",w-8,image+0x337C056));
            assertEquals(expected,m.ops);
        }
    }

    @Test void fatalThreeCallsThenInt3HasNoNormalReturn() {
        long image=0x140000000L,s=0x300000L,w=s-0x28,self=0x600000L;
        Bytes m=new Bytes();m.putD(self+0x14,-1);m.putQ(s,0xDEADBEEFL);
        VolatileBits in=q(v(0x1100),0x2200,self,0x3300,0x4400,0x5500,0x6600,0x7700),a=q(v(0xA000),31,101,102,103,104,0xBEEFAAAAL,106),b=v(0xB000),c=v(0xC000);
        NonvolatileBits n=nv(0x8800);List<Call> seen=new ArrayList<>();
        Calls ports=new Ports(){public VolatileBits invoke(Call call){seen.add(call);return switch(seen.size()){case 1->a;case 2->b;case 3->c;default->throw new AssertionError(call);};}};
        assertThrows(RuntimeException.class,()->LoadRowReferenceCallee337c040203.execute(new Entry(image,s,in,n),m,ports));
        VolatileBits first=q(in,in.raxBits(),0,1,in.r8Bits(),in.r9Bits(),self,in.r11Bits());
        VolatileBits second=q(a,a.raxBits(),w+0x30,a.r10Bits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits());
        assertEquals(List.of(new Call(0x337C051L,TargetKind.DIRECT_RVA,0x86E160L,w,first,n),new Call(0x337C071L,TargetKind.DIRECT_RVA,0x86F210L,w,second,n),new Call(0x337C076L,TargetKind.DIRECT_RVA,0x4232CF4L,w,b,n)),seen);
        assertEquals(List.of(new Op("rd",self+0x14,0xffffffffL),new Op("wq",w-8,image+0x337C056),new Op("wq",w-8,image+0x337C076),new Op("wq",w-8,image+0x337C07B)),m.ops);
    }
}
