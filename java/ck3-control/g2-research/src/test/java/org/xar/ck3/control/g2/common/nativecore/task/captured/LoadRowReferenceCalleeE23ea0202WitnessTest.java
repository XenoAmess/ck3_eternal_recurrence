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

/** Two new literal147B-source behaviors, artificial RAM and opaque ports only. */
public final class LoadRowReferenceCalleeE23ea0202WitnessTest {
    private static final long IMAGE=0x140000000L,S=0x900008L,W=0x8FFFE0L;
    private static final long L=0x1111222230A8L,R=0x222233334088L,DP=0x1111222230B0L,SP=0x222233334090L;
    private static final long E=0x333344445000L,VD=0x6100L,VS=0x6200L,VS2=0x6300L,VE=0x6400L;
    private static final long F0=0x777700001100L,F1=0x777700001200L,F2=0x777700001300L;
    private static final long KEY=0xDEADBEEF11223344L,RET=0xAABBCCDD12345678L,SENTINEL=0xDDDDEEEEFFFF0000L;
    private static final NonvolatileBits NV=new NonvolatileBits(0x8101,0x8202,0x8303,0x8404,
            0x8505,0x8606,0x8707,0x8808,new Bits128(0x8909,0x8A0A));

    // Existing tuple assembly mechanics only, no target branch/traversal oracle.
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
    private static NonvolatileBits nv(long bx,long si,long di) {
        return new NonvolatileBits(bx,NV.rbpBits(),si,di,NV.r12Bits(),NV.r13Bits(),NV.r14Bits(),NV.r15Bits(),NV.xmm6());
    }
    private static Op rq(long a,long v) { return new Op("rq",a,v); }
    private static Op wq(long a,long v) { return new Op("wq",a,v); }
    private static class NoCalls implements Calls {
        @Override public VolatileBits invoke(Call c) { throw new AssertionError("Unexpected invoke "+c); }
        @Override public NormalReturn tail(Tail t) { throw new AssertionError("Unexpected tail "+t); }
        @Override public long readGsQword58() { throw new AssertionError("Unexpected GS read"); }
    }
    private static Bytes aliasRam() {
        Bytes m=new Bytes();m.putQ(S,RET);m.putQ(L,KEY);m.putQ(L+0x40,SENTINEL);return m;
    }

    @Test
    void selfAliasStillCopiesKeyBeforeSkippingPayloadAndBothRealAdaptersUseThatPath() {
        VolatileBits in=tuple(script(1),0x1101,L,L,0x4401),expected=tuple(in,L,L,L,0x4401);
        Bytes m=aliasRam();
        NormalReturn out=LoadRowReferenceCalleeE23ea0202.execute(new Entry(IMAGE,S,in,NV),m,new NoCalls());
        assertEquals(new NormalReturn(expected,RET,S+8,NV),out);assertEquals(SENTINEL,m.rawQ(L+0x40));
        assertEquals(List.of(wq(S+8,NV.rbxBits()),wq(S+0x10,NV.rsiBits()),wq(S-8,NV.rdiBits()),
                rq(L,KEY),wq(L,KEY),rq(S+0x10,NV.rsiBits()),rq(S+8,NV.rbxBits()),rq(S-8,NV.rdiBits()),rq(S,RET)),m.ops);
        for(long site:new long[]{0x337B987,0x337BA17}) {
            Bytes child=aliasRam();Calls bound=LoadRowReferenceCalleeE23ea0202Calls.bind(IMAGE,child,new NoCalls());
            long pre=S+8;child.writeQword(pre-8,IMAGE+site+5); // parent owns physical E8 CALL push.
            assertEquals(expected,bound.invoke(new Call(site,TargetKind.DIRECT_RVA,0xE23EA0,pre,in,NV)));
            assertEquals(SENTINEL,child.rawQ(L+0x40));
            assertEquals(List.of(wq(S,IMAGE+site+5),wq(S+8,NV.rbxBits()),wq(S+0x10,NV.rsiBits()),wq(S-8,NV.rdiBits()),
                    rq(L,KEY),wq(L,KEY),rq(S+0x10,NV.rsiBits()),rq(S+8,NV.rbxBits()),rq(S-8,NV.rdiBits()),rq(S,IMAGE+site+5)),child.ops);
        }
    }

    @Test
    void releaseCloneFreshReleasePreservesDlAndReturnsHeldDestinationBeforeFreshStackRestore() {
        Bytes m=new Bytes();m.putQ(S,RET);m.putQ(R,KEY);m.putQ(L,SENTINEL);
        m.putQ(L+0x40,DP);m.putQ(DP,VD);m.putQ(VD+0x20,F0);
        m.putQ(R+0x40,0x999900001000L);m.putQ(SP,VS);m.putQ(VS+8,0xBAD0);
        VolatileBits in=tuple(script(1),0x1101,L,R,0x4401),a=script(10);
        long clone=0x444455556000L,restoredSi=0x9182736455L,restoredBx=0xA1A2A3A4L;
        long restoredDi=0xB1B2B3B4L,lateReturn=0xC1C2C3C4C5C6C7C8L;
        VolatileBits b=tuple(script(20),clone,0x2214,0xAABBCCDDEEFF7799L,0x4414),c=script(30);
        NonvolatileBits local=nv(L,DP,SP);int[] count={0};
        Calls ports=new NoCalls() {
            @Override public VolatileBits invoke(Call actual) {
                int n=count[0]++;
                if(n==0) {
                    assertEquals(new Call(0xE23ED7,TargetKind.INDIRECT_ABSOLUTE,F0,W,
                            tuple(in,VD,DP,0x222233334000L,0x4401),local),actual);
                    assertEquals(IMAGE+0xE23EDA,m.rawQ(W-8));assertEquals(KEY,m.rawQ(L));
                    m.putQ(R+0x40,SP);m.putQ(SP,VS2);m.putQ(VS2+8,F1);return a;
                }
                if(n==1) {
                    assertEquals(new Call(0xE23EF6,TargetKind.INDIRECT_ABSOLUTE,F1,W,
                            tuple(a,VS2,SP,DP,0x440A),local),actual);
                    assertEquals(IMAGE+0xE23EF9,m.rawQ(W-8));assertEquals(0,m.rawQ(L+0x40));
                    m.putQ(R+0x40,E);m.putQ(E,VE);m.putQ(VE+0x20,F2);return b;
                }
                if(n==2) {
                    assertEquals(new Call(0xE23F0F,TargetKind.INDIRECT_ABSOLUTE,F2,W,
                            tuple(b,VE,E,0xAABBCCDDEEFF7701L,0x4414),local),actual);
                    assertEquals(IMAGE+0xE23F12,m.rawQ(W-8));assertEquals(clone,m.rawQ(L+0x40));
                    m.putQ(S+0x10,restoredSi);m.putQ(S+8,restoredBx);m.putQ(S-8,restoredDi);m.putQ(S,lateReturn);return c;
                }
                throw new AssertionError("Unexpected opaque call "+n);
            }
        };
        NormalReturn out=LoadRowReferenceCalleeE23ea0202.execute(new Entry(IMAGE,S,in,NV),m,ports);
        assertEquals(3,count[0]);
        assertEquals(new NormalReturn(tuple(c,L,c.rcxBits(),c.rdxBits(),c.r8Bits()),lateReturn,S+8,nv(restoredBx,restoredSi,restoredDi)),out);
        assertEquals(KEY,m.rawQ(L));assertEquals(clone,m.rawQ(L+0x40));assertEquals(0,m.rawQ(R+0x40));
        assertEquals(List.of(wq(S+8,NV.rbxBits()),wq(S+0x10,NV.rsiBits()),wq(S-8,NV.rdiBits()),rq(R,KEY),wq(L,KEY),
                rq(L+0x40,DP),rq(DP,VD),rq(VD+0x20,F0),wq(W-8,IMAGE+0xE23EDA),
                wq(L+0x40,0),rq(R+0x40,SP),rq(SP,VS2),rq(VS2+8,F1),wq(W-8,IMAGE+0xE23EF9),
                wq(L+0x40,clone),rq(R+0x40,E),rq(E,VE),rq(VE+0x20,F2),wq(W-8,IMAGE+0xE23F12),
                wq(R+0x40,0),rq(S+0x10,restoredSi),rq(S+8,restoredBx),rq(S-8,restoredDi),rq(S,lateReturn)),m.ops);
    }
}
