package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;

/** Literal106B normal-source witnesses using artificial byte RAM, never native/Game execution. */
public final class LoadRowReferenceCallee87c9b0201WitnessTest {
    private static final long IMAGE=0x140000000L,S=0x800008L,W=0x7FFFE0L;
    private static final long L=0x111122223000L,R=0x222233334000L,D=0x333344445000L;
    private static final long VR=0x6100L,VD=0x6200L,VD2=0x6300L;
    private static final long F0=0x777700001100L,F1=0x777700001200L,RET=0xAABBCCDD12345678L;
    private static final long SENTINEL=0xDDDDEEEEFFFF0000L;
    private static final NonvolatileBits NV=new NonvolatileBits(0x8101,0x8202,0x8303,0x8404,
            0x8505,0x8606,0x8707,0x8808,new Bits128(0x8909,0x8A0A));

    // Mechanical tuple constructors only; no target control flow or memory-derived expected oracle.
    private static VolatileBits script(long k) {
        return new VolatileBits(0x1100+k,0x2200+k,0x1122334455667700L+k,
                0x4400+k,0x5500+k,0x6600+k,0x7700+k,
                new Bits128(0x100000000L+k,0x200000000L+k),new Bits128(0x300000000L+k,0x400000000L+k),
                new Bits128(0x500000000L+k,0x600000000L+k),new Bits128(0x700000000L+k,0x800000000L+k),
                new Bits128(0x900000000L+k,0xA00000000L+k),new Bits128(0xB00000000L+k,0xC00000000L+k));
    }
    private static VolatileBits tuple(VolatileBits v,long ax,long cx,long dx,long r8) {
        return new VolatileBits(ax,cx,dx,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static NonvolatileBits nv(long bx,long di) {
        return new NonvolatileBits(bx,NV.rbpBits(),NV.rsiBits(),di,NV.r12Bits(),NV.r13Bits(),NV.r14Bits(),NV.r15Bits(),NV.xmm6());
    }
    private static VolatileBits incoming() { return tuple(script(1),0x1101,L,R,0x4401); }
    private static Entry entry() { return new Entry(IMAGE,S,incoming(),NV); }
    private static Bytes ram() { Bytes m=new Bytes();m.putQ(S,RET);m.putQ(L+0x38,SENTINEL);return m; }
    private static Op rq(long a,long v) { return new Op("rq",a,v); }
    private static Op wq(long a,long v) { return new Op("wq",a,v); }
    private static class NoCalls implements Calls {
        @Override public VolatileBits invoke(Call c) { throw new AssertionError("Unexpected invoke "+c); }
        @Override public NormalReturn tail(Tail t) { throw new AssertionError("Unexpected tail "+t); }
        @Override public long readGsQword58() { throw new AssertionError("Unexpected GS read"); }
    }

    @Test
    void nullAndExternalSourceHaveDistinctLiteralEffectsWithoutCalls() {
        Bytes empty=ram();empty.putQ(R+0x38,0);
        NormalReturn skipped=LoadRowReferenceCallee87c9b0201.execute(entry(),empty,new NoCalls());
        assertEquals(new NormalReturn(tuple(incoming(),0x1101,0,R,0x4401),RET,S+8,NV),skipped);
        assertEquals(SENTINEL,empty.rawQ(L+0x38));assertEquals(0,empty.rawQ(R+0x38));
        assertEquals(List.of(wq(S+8,NV.rbxBits()),wq(S-8,NV.rdiBits()),rq(R+0x38,0),
                rq(S+8,NV.rbxBits()),rq(S-8,NV.rdiBits()),rq(S,RET)),empty.ops);

        Bytes external=ram();external.putQ(R+0x38,D);
        NormalReturn moved=LoadRowReferenceCallee87c9b0201.execute(entry(),external,new NoCalls());
        assertEquals(new NormalReturn(tuple(incoming(),0x1101,D,R,0x4401),RET,S+8,NV),moved);
        assertEquals(D,external.rawQ(L+0x38));assertEquals(0,external.rawQ(R+0x38));
        assertEquals(List.of(wq(S+8,NV.rbxBits()),wq(S-8,NV.rdiBits()),rq(R+0x38,D),
                wq(L+0x38,D),wq(R+0x38,0),rq(S+8,NV.rbxBits()),rq(S-8,NV.rdiBits()),rq(S,RET)),external.ops);
    }

    @Test
    void selfSourceUsesTwoRealCallbacksFreshReceiverExactDlAndPhysicalReturn() {
        Bytes m=ram();m.putQ(R+0x38,R);m.putQ(R,VR);m.putQ(VR+8,F0);
        m.putQ(D,VD);m.putQ(VD+0x20,0xBAD0L);
        long clone=0x444455556000L,bx=0x99887766L,di=0x88776655L,rip=0xFFEEDDCCBBAA0099L;
        VolatileBits a=tuple(script(10),clone,0x220A,0xAABBCCDDEEFF7788L,0x440A),b=script(20);
        m.putQ(b.rdxBits()+0x38,SENTINEL);
        NonvolatileBits local=nv(R,L);int[] count={0};
        Calls ports=new NoCalls() {
            @Override public VolatileBits invoke(Call c) {
                int n=count[0]++;
                if(n==0) {
                    assertEquals(new Call(0x87C9D4,TargetKind.INDIRECT_ABSOLUTE,F0,W,
                            tuple(incoming(),VR,R,L,0x4401),local),c);
                    assertEquals(IMAGE+0x87C9D7,m.rawQ(W-8));
                    m.putQ(R+0x38,D);m.putQ(D,VD2);m.putQ(VD2+0x20,F1);return a;
                }
                if(n==1) {
                    assertEquals(new Call(0x87C9ED,TargetKind.INDIRECT_ABSOLUTE,F1,W,
                            tuple(a,VD2,D,0xAABBCCDDEEFF7701L,0x440A),local),c);
                    assertEquals(IMAGE+0x87C9F0,m.rawQ(W-8));assertEquals(clone,m.rawQ(L+0x38));
                    m.putQ(S+8,bx);m.putQ(S-8,di);m.putQ(S,rip);return b;
                }
                throw new AssertionError("Unexpected opaque call "+n);
            }
        };
        NormalReturn out=LoadRowReferenceCallee87c9b0201.execute(entry(),m,ports);
        assertEquals(2,count[0]);assertEquals(new NormalReturn(b,rip,S+8,nv(bx,di)),out);
        assertEquals(clone,m.rawQ(L+0x38));assertEquals(0,m.rawQ(R+0x38));
        assertEquals(SENTINEL,m.rawQ(b.rdxBits()+0x38)); // clear uses held RBX, not returned RDX.
        assertEquals(List.of(wq(S+8,NV.rbxBits()),wq(S-8,NV.rdiBits()),rq(R+0x38,R),rq(R,VR),
                rq(VR+8,F0),wq(W-8,IMAGE+0x87C9D7),wq(L+0x38,clone),rq(R+0x38,D),
                rq(D,VD2),rq(VD2+0x20,F1),wq(W-8,IMAGE+0x87C9F0),wq(R+0x38,0),
                rq(S+8,bx),rq(S-8,di),rq(S,rip)),m.ops);
    }

    @Test
    void threeActualParentSitesExecuteChildAndOtherEdgesPassThrough() {
        for(long site:new long[]{0x337B93E,0x337B9CE,0x337BB4A}) {
            Bytes m=ram();m.putQ(R+0x38,0);
            Calls bound=LoadRowReferenceCallee87c9b0201Calls.bind(IMAGE,m,new NoCalls());
            long pre=S+8;
            m.writeQword(pre-8,IMAGE+site+5); // actual parent owns the physical E8 CALL push.
            VolatileBits out=bound.invoke(new Call(site,TargetKind.DIRECT_RVA,0x87C9B0,pre,incoming(),NV));
            assertEquals(tuple(incoming(),0x1101,0,R,0x4401),out);assertEquals(SENTINEL,m.rawQ(L+0x38));
            assertEquals(List.of(wq(S,IMAGE+site+5),wq(S+8,NV.rbxBits()),wq(S-8,NV.rdiBits()),rq(R+0x38,0),
                    rq(S+8,NV.rbxBits()),rq(S-8,NV.rdiBits()),rq(S,IMAGE+site+5)),m.ops);
        }
        Bytes m=new Bytes();VolatileBits reply=script(30);Call[] seen={null};Tail[] tailSeen={null};
        NormalReturn tailReply=new NormalReturn(script(40),0x76543210FEDCL,0x12340008L,NV);
        Calls delegate=new Calls() {
            @Override public VolatileBits invoke(Call c) { assertNull(seen[0]);seen[0]=c;return reply; }
            @Override public NormalReturn tail(Tail t) { assertNull(tailSeen[0]);tailSeen[0]=t;return tailReply; }
            @Override public long readGsQword58() { return 0xFEDCBA9876543210L; }
        };
        Calls bound=LoadRowReferenceCallee87c9b0201Calls.bind(IMAGE,m,delegate);
        Call[] wrong={new Call(0x337B93F,TargetKind.DIRECT_RVA,0x87C9B0,S,incoming(),NV),
                new Call(0x337B9CE,TargetKind.INDIRECT_ABSOLUTE,0x87C9B0,S,incoming(),NV),
                new Call(0x337BB4A,TargetKind.DIRECT_RVA,0x87C9B1,S,incoming(),NV)};
        for(Call c:wrong) { seen[0]=null;assertSame(reply,bound.invoke(c));assertSame(c,seen[0]); }
        Tail t=new Tail(0x337B93E,TargetKind.DIRECT_RVA,0x87C9B0,entry());
        assertSame(tailReply,bound.tail(t));assertSame(t,tailSeen[0]);
        assertEquals(0xFEDCBA9876543210L,bound.readGsQword58());assertTrue(m.ops.isEmpty());
    }
}
