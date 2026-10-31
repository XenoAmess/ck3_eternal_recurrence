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

/** Artificial byte RAM and opaque callbacks; expected states follow only the complete296B ASM. */
public final class LoadRowReferenceCalleeA636f0200WitnessTest {
    private static final long IMAGE = 0x0000000140000000L;
    private static final long S = 0x700008L, W = 0x6FFFA0L, TEMP = 0x6FFFC0L, H = 0x6FFFF8L;
    private static final long L = 0x100020003000L, R = 0x200030004000L, D = 0x300040005000L;
    private static final long VL = 0x5100L, VR = 0x5200L, VD = 0x5300L, VT = 0x5400L, VD2 = 0x5500L;
    private static final long F0 = 0x700000001100L, F1 = 0x700000001200L, F2 = 0x700000001300L;
    private static final long F3 = 0x700000001400L, F4 = 0x700000001500L, F5 = 0x700000001600L;
    private static final long RET = 0x123456789ABCD001L;
    private static final NonvolatileBits NV = new NonvolatileBits(0x8101L,0x8202L,0x8303L,0x8404L,
            0x8505L,0x8606L,0x8707L,0x8808L,new Bits128(0x8909L,0x8A0AL));

    // Tuple assembly is mechanical: no target execution, traversal, branch or memory-derived oracle.
    private static VolatileBits script(long k) {
        return new VolatileBits(0x1100L+k,0x2200L+k,0x1122334455667700L+k,
                0x4400L+k,0x5500L+k,0x6600L+k,0x7700L+k,
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
    private static Bytes ram() { Bytes m=new Bytes();m.putQ(S,RET);return m; }
    private static VolatileBits incoming() { return tuple(script(1),0x1101L,L,R,0x4401L); }
    private static Entry entry() { return new Entry(IMAGE,S,incoming(),NV); }
    private static class NoCalls implements Calls {
        @Override public VolatileBits invoke(Call c) { throw new AssertionError("Unexpected invoke "+c); }
        @Override public NormalReturn tail(Tail t) { throw new AssertionError("Unexpected tail "+t); }
        @Override public long readGsQword58() { throw new AssertionError("Unexpected GS read"); }
    }
    private static void call(Call actual,long site,long target,VolatileBits v,NonvolatileBits n,Bytes m,long next) {
        assertEquals(new Call(site,TargetKind.INDIRECT_ABSOLUTE,target,W,v,n),actual);
        assertEquals(IMAGE+next,m.rawQ(W-8));
    }

    @Test
    void fastSwapUsesRawPointersAndPhysicalReturn() {
        Bytes m=ram();m.putQ(L+0x38,D);m.putQ(R+0x38,0x400050006000L);
        NormalReturn out=LoadRowReferenceCalleeA636f0200.execute(entry(),m,new NoCalls());
        assertEquals(new NormalReturn(tuple(incoming(),0x400050006000L,D,R,0x4401L),RET,S+8,NV),out);
        assertEquals(0x400050006000L,m.rawQ(L+0x38));assertEquals(D,m.rawQ(R+0x38));
        assertEquals(List.of(wq(S+0x10,NV.rbxBits()),wq(S-8,NV.rdiBits()),
                rq(L+0x38,D),rq(R+0x38,0x400050006000L),wq(L+0x38,0x400050006000L),wq(R+0x38,D),
                rq(S+0x10,NV.rbxBits()),rq(S-8,NV.rdiBits()),rq(S,RET)),m.ops);
        assertEquals(0xA5A5A5A5A5A5A5A5L,m.rawQ(S+8)); // fast path never saves RSI.
    }

    @Test
    void twoSelfSourcesReachAllSixCallsWithFreshMemoryAndSavedRegisters() {
        Bytes m=ram();m.putQ(L+0x38,L);m.putQ(R+0x38,R);
        m.putQ(L,VL);m.putQ(VL+8,F0);m.putQ(D,VD);m.putQ(VD+0x20,F1);
        m.putQ(R,VR);m.putQ(VR+8,F2);m.putQ(VR+0x20,F3);m.putQ(TEMP,VT);m.putQ(VT+8,F4);
        long cloneLeft=0x400050006000L,cloneRight=0x400050007000L;
        long restoredSi=0x9182736455L,lateSi=0x9988776655L;
        long restoredBx=0xA1A2A3A4L,restoredDi=0xB1B2B3B4L,lateReturn=0xC1C2C3C4C5C6C7C8L;
        VolatileBits a=tuple(script(10),TEMP,0x220AL,0x112233445566770AL,0x440AL);
        VolatileBits b=script(20);
        VolatileBits c=tuple(script(30),cloneLeft,0x221EL,0x112233445566771EL,0x441EL);
        VolatileBits d=script(40);
        VolatileBits e=tuple(script(50),cloneRight,0x2232L,0x1122334455667732L,0x4432L);
        VolatileBits f=script(60);
        NonvolatileBits local=nv(R,0,L),afterSi=nv(R,restoredSi,L);
        int[] n={0};
        Calls ports=new NoCalls() {
            @Override public VolatileBits invoke(Call actual) {
                int at=n[0]++;
                switch(at) {
                    case 0:
                        call(actual,0xA63746L,F0,tuple(incoming(),VL,L,TEMP,0),local,m,0xA63749L);
                        m.putQ(L+0x38,D);return a;
                    case 1:
                        // SETNE DL retains A's upper56; RCX is a fresh container read.
                        call(actual,0xA63763L,F1,tuple(a,VD,D,0x1122334455667701L,TEMP),local,m,0xA63766L);
                        assertEquals(TEMP,m.rawQ(H));return b;
                    case 2:
                        call(actual,0xA6378DL,F2,tuple(b,VR,R,L,TEMP),local,m,0xA63790L);
                        assertEquals(0,m.rawQ(L+0x38));return c;
                    case 3:
                        // Equal-to-R receiver sets only DL to0; C's R8 survives into this call.
                        call(actual,0xA637A6L,F3,tuple(c,VR,R,0x1122334455667700L,0x441EL),local,m,0xA637A9L);
                        assertEquals(cloneLeft,m.rawQ(L+0x38));m.putQ(S+8,restoredSi);return d;
                    case 4:
                        call(actual,0xA637DCL,F4,tuple(d,VT,TEMP,R,TEMP),afterSi,m,0xA637DFL);
                        assertEquals(0,m.rawQ(R+0x38));
                        m.putQ(H,D);m.putQ(D,VD2);m.putQ(VD2+0x20,F5);m.putQ(S+8,lateSi);return e;
                    case 5:
                        // Final SETNE follows a fresh LEA TEMP, rather than E's returned RDX.
                        call(actual,0xA637FBL,F5,tuple(e,VD2,D,0x6FFF01L,0x4432L),afterSi,m,0xA637FEL);
                        assertEquals(cloneRight,m.rawQ(R+0x38));
                        m.putQ(S+0x10,restoredBx);m.putQ(S-8,restoredDi);m.putQ(S,lateReturn);return f;
                    default: throw new AssertionError("Unexpected opaque call "+at);
                }
            }
        };
        NormalReturn out=LoadRowReferenceCalleeA636f0200.execute(entry(),m,ports);
        assertEquals(6,n[0]);assertEquals(new NormalReturn(f,lateReturn,S+8,nv(restoredBx,restoredSi,restoredDi)),out);
        assertEquals(lateSi,m.rawQ(S+8));assertEquals(cloneLeft,m.rawQ(L+0x38));assertEquals(cloneRight,m.rawQ(R+0x38));
        // One coherent RAM and literal instruction-order operations, including all six owned pushes.
        assertEquals(List.of(wq(S+0x10,NV.rbxBits()),wq(S-8,NV.rdiBits()),rq(L+0x38,L),
                wq(S+8,NV.rsiBits()),wq(H,0),rq(L,VL),rq(VL+8,F0),wq(W-8,IMAGE+0xA63749L),
                rq(L+0x38,D),wq(H,TEMP),rq(D,VD),rq(VD+0x20,F1),wq(W-8,IMAGE+0xA63766L),
                rq(H,TEMP),wq(L+0x38,0),rq(R+0x38,R),rq(R,VR),rq(VR+8,F2),wq(W-8,IMAGE+0xA63790L),
                wq(L+0x38,cloneLeft),rq(R+0x38,R),rq(R,VR),rq(VR+0x20,F3),wq(W-8,IMAGE+0xA637A9L),
                rq(H,TEMP),wq(R+0x38,0),rq(S+8,restoredSi),rq(TEMP,VT),rq(VT+8,F4),wq(W-8,IMAGE+0xA637DFL),
                rq(H,D),wq(R+0x38,cloneRight),rq(D,VD2),rq(VD2+0x20,F5),wq(W-8,IMAGE+0xA637FEL),
                rq(S+0x10,restoredBx),rq(S-8,restoredDi),rq(S,lateReturn)),m.ops);
    }

    @Test
    void secondSelfWithNullFirstAndFreshNullAfterCloneSkipsOtherCalls() {
        Bytes m=ram();m.putQ(L+0x38,0);m.putQ(R+0x38,R);m.putQ(R,VR);m.putQ(VR+8,F2);
        long restoredSi=0xAA11L,restoredBx=0xBB22L,restoredDi=0xCC33L,lateReturn=0xDD4400550066L;
        VolatileBits reply=tuple(script(70),D,0x2246L,0x1122334455667746L,0x4446L);
        int[] count={0};
        Calls ports=new NoCalls() {
            @Override public VolatileBits invoke(Call actual) {
                assertEquals(0,count[0]++);
                call(actual,0xA6378DL,F2,tuple(incoming(),VR,R,L,0),nv(R,0,L),m,0xA63790L);
                m.putQ(R+0x38,0);m.putQ(S+8,restoredSi);m.putQ(S+0x10,restoredBx);
                m.putQ(S-8,restoredDi);m.putQ(S,lateReturn);return reply;
            }
        };
        NormalReturn out=LoadRowReferenceCalleeA636f0200.execute(entry(),m,ports);
        assertEquals(1,count[0]);
        assertEquals(new NormalReturn(tuple(reply,D,0,0x1122334455667746L,0),lateReturn,S+8,nv(restoredBx,restoredSi,restoredDi)),out);
        assertEquals(List.of(wq(S+0x10,NV.rbxBits()),wq(S-8,NV.rdiBits()),rq(L+0x38,0),rq(R+0x38,R),
                wq(S+8,NV.rsiBits()),wq(H,0),rq(R+0x38,R),rq(R,VR),rq(VR+8,F2),wq(W-8,IMAGE+0xA63790L),
                wq(L+0x38,D),rq(R+0x38,0),rq(H,0),rq(S+8,restoredSi),
                rq(S+0x10,restoredBx),rq(S-8,restoredDi),rq(S,lateReturn)),m.ops);
    }

    @Test
    void actualThreeSiteAdaptersExecuteChildAndWrongEdgesPreserveObjects() {
        // The three literal sites are the three actual E8 rel32 call instructions in337B7E0.
        for(long site:new long[]{0x337B8EDL,0x337BA8BL,0x337BAE2L}) {
            Bytes m=new Bytes();m.putQ(L+0x38,D);m.putQ(R+0x38,0x400050006000L);
            Calls bound=LoadRowReferenceCalleeA636f0200Calls.bind(IMAGE,m,new NoCalls());
            long before=S+8; // parent E8 CALL owns the physical return slot; adapter exposes child entry=S.
            m.writeQword(S,IMAGE+site+5);
            VolatileBits out=bound.invoke(new Call(site,TargetKind.DIRECT_RVA,0xA636F0L,before,incoming(),NV));
            assertEquals(tuple(incoming(),0x400050006000L,D,R,0x4401L),out);
            assertEquals(List.of(wq(S,IMAGE+site+5),wq(S+0x10,NV.rbxBits()),wq(S-8,NV.rdiBits()),
                    rq(L+0x38,D),rq(R+0x38,0x400050006000L),wq(L+0x38,0x400050006000L),wq(R+0x38,D),
                    rq(S+0x10,NV.rbxBits()),rq(S-8,NV.rdiBits()),rq(S,IMAGE+site+5)),m.ops);
        }
        Bytes m=new Bytes();VolatileBits reply=script(80);Call[] seen={null};Tail[] tailSeen={null};
        NormalReturn tailReply=new NormalReturn(script(90),0x999988887777L,0x66665555L,NV);
        Calls external=new Calls() {
            @Override public VolatileBits invoke(Call c) { assertNull(seen[0]);seen[0]=c;return reply; }
            @Override public NormalReturn tail(Tail t) { assertNull(tailSeen[0]);tailSeen[0]=t;return tailReply; }
            @Override public long readGsQword58() { return 0xFEDCBA9876543210L; }
        };
        Calls bound=LoadRowReferenceCalleeA636f0200Calls.bind(IMAGE,m,external);
        Call[] wrong={new Call(0x337B8EEL,TargetKind.DIRECT_RVA,0xA636F0L,S,incoming(),NV),
                new Call(0x337B8EDL,TargetKind.INDIRECT_ABSOLUTE,0xA636F0L,S,incoming(),NV),
                new Call(0x337BA8BL,TargetKind.DIRECT_RVA,0xA636F1L,S,incoming(),NV)};
        for(Call c:wrong) { seen[0]=null;assertSame(reply,bound.invoke(c));assertSame(c,seen[0]); }
        Tail transfer=new Tail(0x337BAE2L,TargetKind.DIRECT_RVA,0xA636F0L,entry());
        assertSame(tailReply,bound.tail(transfer));assertSame(transfer,tailSeen[0]);
        assertEquals(0xFEDCBA9876543210L,bound.readGsQword58());assertTrue(m.ops.isEmpty());
    }
}
