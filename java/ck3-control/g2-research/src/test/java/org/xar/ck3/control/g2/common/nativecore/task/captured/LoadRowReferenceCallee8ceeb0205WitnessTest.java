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
public final class LoadRowReferenceCallee8ceeb0205WitnessTest {
    static Bits128 x(long b) { return new Bits128(b,b+1); }
    static VolatileBits v(long b) { return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60)); }
    static NonvolatileBits nv(long b) { return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80)); }
    static VolatileBits q(VolatileBits b,long a,long c,long dd,long r8,long r9,long r10,long r11) { return new VolatileBits(a,c,dd,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5()); }
    static class Ports implements Calls {
        public VolatileBits invoke(Call call) { throw new AssertionError(call); }
        public NormalReturn tail(Tail transfer) { throw new AssertionError(transfer); }
        public long readGsQword58() { throw new AssertionError("GS"); }
    }

    static final long IMAGE=0x140000000L,S=0x70000000L,GS=0xFEDC000000100000L,THREAD=0xABCDEF0000200000L;
    static final long GUARD=IMAGE+0x5C673D0L,STORAGE=IMAGE+0x5C673E0L,RIP=0x8877665544332211L;
    static VolatileBits input() {
        VolatileBits b=v(0x1000);
        return q(b,0x1111222233334444L,0x5555666677778888L,0xFEDCBA9876543210L,
                b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits());
    }
    static Bytes memory(int thread,int guard,long stack,long rip) {
        Bytes m=new Bytes();m.putQ(GS,THREAD);m.putD(THREAD+0x10,thread);m.putD(GUARD,guard);m.putQ(stack,rip);return m;
    }
    @Test void fastUsesSignedGuardAndActualGsPointer() {
        Bytes m=memory(Integer.MAX_VALUE,Integer.MIN_VALUE,S,RIP);int[] gsCount={0};
        Calls ports=new Ports(){public long readGsQword58(){gsCount[0]++;return GS;}};
        VolatileBits in=input();NonvolatileBits n=nv(0x2000);
        NormalReturn got=LoadRowReferenceCallee8ceeb0205.execute(new Entry(IMAGE,S,in,n),m,ports);
        assertEquals(new NormalReturn(q(in,STORAGE,THREAD,16,in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits()),RIP,S+8,n),got);
        assertEquals(1,gsCount[0]);
        assertEquals(List.of(new Op("rq",GS,THREAD),new Op("rd",THREAD+0x10,0x7FFFFFFFL),
                new Op("rd",GUARD,0x80000000L),new Op("rq",S,RIP)),m.ops);
    }
    @Test void slowHeaderFreshGuardSkipsFooterAndKeepsItsWholeReturn() {
        Bytes m=memory(-7,0,S,RIP);int[] gsCount={0},calls={0};
        VolatileBits in=input(),reply=v(0x3000);NonvolatileBits n=nv(0x4000);long nextRip=0xEE00112233445566L;
        Calls ports=new Ports(){
            public long readGsQword58(){gsCount[0]++;return GS;}
            public VolatileBits invoke(Call c){calls[0]++;
                assertEquals(new Call(0x8CEEE3L,TargetKind.DIRECT_RVA,0x4223A84L,S-0x28,
                        q(in,0xFFFFFFF9L,GUARD,16,in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits()),n),c);
                assertEquals(IMAGE+0x8CEEE8L,m.rawQ(S-0x30));
                m.writeDword(GUARD,33);m.writeQword(S,nextRip);return reply;
            }
        };
        NormalReturn got=LoadRowReferenceCallee8ceeb0205.execute(new Entry(IMAGE,S,in,n),m,ports);
        assertEquals(new NormalReturn(q(reply,STORAGE,reply.rcxBits(),reply.rdxBits(),reply.r8Bits(),reply.r9Bits(),reply.r10Bits(),reply.r11Bits()),nextRip,S+8,n),got);
        assertEquals(1,gsCount[0]);assertEquals(1,calls[0]);
        assertEquals(0xA5,m.rawB(STORAGE+4));assertEquals(0xA5,m.rawB(IMAGE+0x5C67434L));
        assertTrue(m.ops.contains(new Op("rd",GUARD,33)));
    }
    @Test void slowInitializerWritesExactBytesThenKeepsFooterReturn() {
        Bytes m=memory(-7,0,S,RIP);int[] gsCount={0},calls={0};
        VolatileBits in=input(),a=v(0x5000),b=v(0x6000);NonvolatileBits n=nv(0x7000);
        long nextRip=0xFFEEDDCCBBAA0099L;
        Calls ports=new Ports(){
            public long readGsQword58(){gsCount[0]++;return GS;}
            public VolatileBits invoke(Call c){
                if(calls[0]++==0) {
                    assertEquals(new Call(0x8CEEE3L,TargetKind.DIRECT_RVA,0x4223A84L,S-0x28,
                            q(in,0xFFFFFFF9L,GUARD,16,in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits()),n),c);
                    assertEquals(IMAGE+0x8CEEE8L,m.rawQ(S-0x30));m.writeDword(GUARD,-1);return a;
                }
                assertEquals(2,calls[0]);
                assertEquals(new Call(0x8CEF06L,TargetKind.DIRECT_RVA,0x4223A24L,S-0x28,
                        q(a,a.raxBits(),GUARD,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits()),n),c);
                assertEquals(IMAGE+0x8CEF0BL,m.rawQ(S-0x30));
                assertEquals(0,m.rawB(STORAGE+4));assertEquals(255,m.rawB(IMAGE+0x5C67434L));
                assertEquals(0xA5,m.rawB(STORAGE+3));assertEquals(0xA5,m.rawB(STORAGE+5));
                assertEquals(0xA5,m.rawB(IMAGE+0x5C67433L));assertEquals(0xA5,m.rawB(IMAGE+0x5C67435L));
                m.writeQword(S,nextRip);return b;
            }
        };
        NormalReturn got=LoadRowReferenceCallee8ceeb0205.execute(new Entry(IMAGE,S,in,n),m,ports);
        assertEquals(new NormalReturn(q(b,STORAGE,b.rcxBits(),b.rdxBits(),b.r8Bits(),b.r9Bits(),b.r10Bits(),b.r11Bits()),nextRip,S+8,n),got);
        assertEquals(1,gsCount[0]);assertEquals(2,calls[0]);
        assertEquals(List.of(new Op("wb",STORAGE+4,0),new Op("wb",IMAGE+0x5C67434L,255)),
                m.ops.stream().filter(o->o.kind().equals("wb")).toList());
    }
    @Test void bothActualC0CallSitesUseParentsPhysicalReturnSlot() {
        VolatileBits in=input();NonvolatileBits n=nv(0x8000);
        for(long site:new long[]{0x337C161L,0x337C1C3L}) {
            long ret=IMAGE+site+5;Bytes m=memory(0,-1,S-8,ret);int[] gsCount={0};
            Calls ports=new Ports(){public long readGsQword58(){gsCount[0]++;return GS;}};
            Calls bound=LoadRowReferenceCallee8ceeb0205Calls.bind(IMAGE,m,ports);
            m.writeQword(S-8,ret); // Parent already pushed its actual CALL return.
            assertEquals(q(in,STORAGE,THREAD,16,in.r8Bits(),in.r9Bits(),in.r10Bits(),in.r11Bits()),
                    bound.invoke(new Call(site,TargetKind.DIRECT_RVA,0x8CEEB0L,S,in,n)));
            assertEquals(1,gsCount[0]);
            assertEquals(List.of(new Op("wq",S-8,ret),new Op("rq",GS,THREAD),new Op("rd",THREAD+0x10,0),
                    new Op("rd",GUARD,0xFFFFFFFFL),new Op("rq",S-8,ret)),m.ops);
        }
    }
}
