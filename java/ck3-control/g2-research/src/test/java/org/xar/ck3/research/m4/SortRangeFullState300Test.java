package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m4.RotateFullState292Test.Observed;
import org.xar.ck3.research.m4.RotateFullState292Test.Touch;

/** Owner source literals, frozen outside model input; no algorithm/hardware or Game proof. */
final class SortRangeFullState300Test {
    static final long I=0x180000000L,S=0x90000L,P=0x2000L,T=0x5000L,RIP=0x77112233L,G=S-0x78L;
    static VolatileBits input(long first,long end,long count,long scratch){return RotateFullState292Test.regs(100,0x123,first,end,count,scratch);}
    static VolatileBits vr(VolatileBits v,long a,long c,long d,long r8,long r9,long r10,long r11,Bits128 x0,Bits128 x1,Bits128 x2,Bits128 x3,Bits128 x4) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,x0,x1,x2,x3,x4,v.xmm5());
    }
    static NonvolatileBits nr(NonvolatileBits n,long bx,long bp,long si,long di,long r12,long r13,long r14,long r15){return new NonvolatileBits(bx,bp,si,di,r12,r13,r14,r15,n.xmm6());}
    static Observed memory(){var m=new Observed();m.m.put(S,RIP);m.m.data.put(S+0x28L,(byte)0xA7);return m;}
    static void words(Map<Long,Byte> m,long p,long...x){RotateFullState292Test.words(m,p,x);}
    static long[] row(int id,int score){return SmallRangeFullState295Test.row(id,score);}
    static void descending(Observed m,int count){for(int k=0;k<count;k++)words(m.m.data,P+40L*k,row(k+1,count-k));}
    static void assertRow(Observed m,long p,long[] r){for(int k=0;k<5;k++)assertEquals(r[k],m.m.readQword(p+8L*k));}
    static GovernmentCrtBoundary185Api.LoopBudget finite(){int[] steps={0};return(s,g)->{if(++steps[0]>1200)throw new AssertionError("finite source witness");};}
    static GovernmentCrtBoundary185Api.Calls unexpected(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected normal port "+c);}};}
    static void outerHomes(Map<Long,Byte> m,NonvolatileBits n,boolean large){
        qword(m,S+24,n.rbxBits());qword(m,S+32,n.rsiBits());qword(m,S-8,n.rdiBits());qword(m,S-16,n.r12Bits());
        qword(m,S-24,n.r13Bits());qword(m,S-32,n.r14Bits());qword(m,S-40,n.r15Bits());if(large)qword(m,S+16,n.rbpBits());
    }

    @Test void emptySmallPathExecutesReal295AndFreshFullOuterFrame() {
        var m=memory();var n=n(700);var in=input(P,P,0,T);var expected=new HashMap<>(m.m.snapshot());outerHomes(expected,n,false);
        qword(expected,G-8,I+0x1A818BCL);qword(expected,G+16,n.rsiBits());qword(expected,G-16,P);
        var out=SortRangeFullState300.execute(new Entry(I,S,in,n),m,unexpected(),(s,g)->{throw new AssertionError("empty should not loop");});
        var v=vr(in,P,P,P,0,T,in.r10Bits(),S-40,in.xmm0(),in.xmm1(),in.xmm2(),in.xmm3(),in.xmm4());
        assertEquals(new NormalReturn(v,RIP,S+8,n),out);assertEquals(expected,m.m.snapshot());
        assertEquals(List.of(new Touch("W8",S+24),new Touch("W8",S+32),new Touch("W8",S-8),new Touch("W8",S-16),
                new Touch("W8",S-24),new Touch("W8",S-32),new Touch("W8",S-40)),m.touches.subList(0,7));
        assertEquals(List.of(new Touch("R8",S+24),new Touch("R8",S+32),new Touch("R8",S-40),new Touch("R8",S-32),
                new Touch("R8",S-24),new Touch("R8",S-16),new Touch("R8",S-8),new Touch("R8",S)),m.touches.subList(m.touches.size()-8,m.touches.size()));
        assertFalse(m.touches.contains(new Touch("R1",S+40))); // no large tag read
    }

    @Test void twoSortedRowsUseRealSmallCaptureAndKeepFullVolatileAndXmmBits() {
        var m=memory();descending(m,2);var n=n(700);var in=input(P,P+80,2,T);var r=row(2,1);
        var out=SortRangeFullState300.execute(new Entry(I,S,in,n),m,unexpected(),finite());
        assertEquals(new NormalReturn(vr(in,P+80,1,P+80,P+40,T,in.r10Bits(),S-40,in.xmm0(),in.xmm1(),
                new Bits128(r[0],r[1]),new Bits128(r[2],r[3]),new Bits128(r[4],0)),RIP,S+8,n),out);
        assertRow(m,P,row(1,2));assertRow(m,P+40,row(2,1));assertEquals(I+0x1A818BCL,m.m.readQword(G-8));
        assertFalse(m.touches.contains(new Touch("W8",S+16))); // conditional full809 RBP save not taken
    }

    @Test void rowBasicBlocksKeepMovdHighZerosAndAliasedFreshFinalReloadOrder() {
        var m=memory();words(m.m.data,P,0xAABBCCDD80000001L,2,3,4,5);
        var in=input(P,P+40,33,T);var n=n(700);var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,G,in,n));r.rbx=P;r.rdi=T;
        SortRowFrames300.capture(r,m);
        assertEquals(P,r.rcx);assertEquals(0x80000001L,r.rdx);assertEquals(new Bits128(5,0),r.x4);
        assertEquals(List.of(new Touch("R16",P),new Touch("R16",P+16),new Touch("R8",P+32),new Touch("W16",G+48),new Touch("W16",G+64),new Touch("W8",G+128)),m.touches);
        assertEquals(new Bits128(0xAABBCCDD80000001L,2),r.x2);assertEquals(new Bits128(3,4),r.x3);
        m.touches.clear();r.rdi=G+128;
        // The first destination write aliases the later qword reload: finalXMM0 must become first.low, not old5.
        SortRowFrames300.restoreFront(r,m);
        assertEquals(new Bits128(0xAABBCCDD80000001L,0),r.x0);assertEquals(new Bits128(3,4),r.x1);
        assertEquals(List.of(new Touch("R16",G+48),new Touch("R16",G+64),new Touch("W16",G+128),new Touch("R8",G+128),new Touch("W16",G+144),new Touch("W8",G+160)),m.touches);
        assertEquals(0xAABBCCDD80000001L,m.m.readQword(G+160));
    }

    @Test void count33ConsumesReal299AndFullTailPostThenFreshOuterHomesAndRet() {
        var m=memory();descending(m,33);var n=n(700);var in=input(P,P+1320,33,T);var post=input(101,102,103,104);
        var seen=new ArrayList<Tail>();long changedRip=0xABCDL;
        var last=row(33,1);var previous=row(32,2);
        var expectedV=vr(in,P,P,T,1320,64,T,P+1280,new Bits128(last[4],0),new Bits128(last[2],last[3]),
                new Bits128(previous[0],previous[1]),new Bits128(previous[2],previous[3]),new Bits128(previous[4],0));
        var expectedN=nr(n,0xA7,n.rbpBits(),T+1320,P+1280,P,T,33,P+1320);
        var out=SortRangeFullState300.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){throw new AssertionError("no normal opaque COPY expected");}
            @Override public NormalReturn tail(Tail t){
                seen.add(t);assertEquals(new Tail(0x1A82449L,TargetKind.DIRECT_RVA,0x4226860L,new Entry(I,G-8,expectedV,expectedN)),t);
                assertEquals(I+0x1A81A3EL,m.m.readQword(G-8));
                m.m.put(S+24,0xAAA);m.m.put(S+32,0xBBB);m.m.put(S-8,0xCCC);m.m.put(S-16,0xDDD);
                m.m.put(S-24,0xEEE);m.m.put(S-32,0xFFF);m.m.put(S-40,0x999);m.m.put(S+16,0xBAD);m.m.put(S,changedRip);
                return new NormalReturn(post,I+0x1A81A3EL,G,t.entry().nonvolatileBits());
            }
        },finite());
        assertEquals(1,seen.size());
        var finalV=vr(post,post.raxBits(),post.rcxBits(),post.rdxBits(),post.r8Bits(),post.r9Bits(),post.r10Bits(),S-40,post.xmm0(),post.xmm1(),post.xmm2(),post.xmm3(),post.xmm4());
        assertEquals(new NormalReturn(finalV,changedRip,S+8,nr(n,0xAAA,n.rbpBits(),0xBBB,0xCCC,0xDDD,0xEEE,0xFFF,0x999)),out);
        for(int k=0;k<33;k++)assertRow(m,T+40L*k,row(k+1,33-k));
        assertEquals(n.rbpBits(),out.nonvolatileBits().rbpBits()); // largeRBP restore happened before latecallback
    }

    @Test void actualFrontCopyAndInsertionShiftPrefixesAreNotWholeArrayShortcuts() {
        var m=memory();descending(m,33);words(m.m.data,P,row(1,1));words(m.m.data,P+40,row(2,2));var n=n(700);var in=input(P,P+1320,33,T);
        var fail=new UnsupportedOperationException("opaque COPY cannot assume DF");var expectedN=nr(n,P+40,1,P+1280,P,P,T,33,P+1320);
        assertSame(fail,assertThrows(UnsupportedOperationException.class,()->SortRangeFullState300.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(0x1A8182AL,c.callSiteRva());assertEquals(0x4226860L,c.targetBits());assertEquals(G,c.rspBits());
                assertEquals(P+40,c.volatileBits().rcxBits());assertEquals(P,c.volatileBits().rdxBits());assertEquals(40,c.volatileBits().r8Bits());
                assertEquals(in.raxBits(),c.volatileBits().raxBits());assertEquals(expectedN,c.nonvolatileBits());throw fail;}
        },finite())));
        assertEquals(I+0x1A8182FL,m.m.readQword(G-8));assertEquals(row(2,2)[4],m.m.readQword(G+128));
        assertFalse(m.touches.contains(new Touch("R8",S)));
        var shifted=memory();descending(shifted,33);words(shifted.m.data,P,row(1,100));words(shifted.m.data,P+40,row(2,90));words(shifted.m.data,P+80,row(3,95));
        var stop=new IllegalStateException("next actual insertion header");int[] iterations={0};
        assertSame(stop,assertThrows(IllegalStateException.class,()->SortRangeFullState300.execute(new Entry(I,S,in,n),shifted,unexpected(),(site,guard)->{
            if(site==0x1A817F0L&&++iterations[0]==3)throw stop;
        })));
        assertRow(shifted,P,row(1,100));assertRow(shifted,P+40,row(3,95));assertRow(shifted,P+80,row(2,90));
        assertTrue(shifted.touches.contains(new Touch("R16",P+40)));assertTrue(shifted.touches.contains(new Touch("W16",P+80)));
    }

    @Test void real296CallerConsumesBothNewPortsThenOriginalMergeFallback() {
        var m=memory();descending(m,33);m.m.put(S+40,17);m.m.data.put(S+48,(byte)0xA7);var n=n(700);var in=input(P,P+1320,33,T);
        var post=input(201,202,203,204);var seen=new ArrayList<Call>();
        var calls=SortRangeCalls300.bind(I,m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            seen.add(c);assertEquals(0x1A813C6L,c.callSiteRva());assertEquals(0x1A81AB0L,c.targetBits());return post;
        }},finite());
        var out=DispatchRangeFullState296.execute(new Entry(I,S,in,n),m,calls,finite());
        assertEquals(1,seen.size());assertEquals(new NormalReturn(post,RIP,S+8,n),out);
        for(int k=0;k<33;k++)assertRow(m,P+40L*k,row(k+1,33-k));
        assertTrue(m.touches.contains(new Touch("W8",S-0x70L))); // actual296's ownedsinglepush reused by newcallee
    }

    @Test void realChildFrameFailuresAndCallerReturnCorruptionCannotBecomeNormal() {
        for(int which=0;which<3;which++) {
            final int k=which;var m=memory();descending(m,33);var n=n(700);var in=input(P,P+1320,33,T);
            assertThrows(UnsupportedOperationException.class,()->SortRangeFullState300.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){
                @Override public VolatileBits invoke(Call c){throw new AssertionError("unused normal");}
                @Override public NormalReturn tail(Tail t){var offered=t.entry().nonvolatileBits();
                    var changed=nr(offered,offered.rbxBits()+1,offered.rbpBits(),offered.rsiBits(),offered.rdiBits(),offered.r12Bits(),offered.r13Bits(),offered.r14Bits(),offered.r15Bits());
                    return new NormalReturn(t.entry().volatileBits(),k==0?0:I+0x1A81A3EL,k==1?0:G,k==2?changed:offered);}
            },finite()));
            assertFalse(m.touches.contains(new Touch("R8",S)));
        }
        for(long site:new long[]{0x1A81363L,0x1A81378L}) {
            var m=memory();m.m.put(S,0);var n=n(700);var in=input(P,P,0,T);
            var bound=SortRangeCalls300.bind(I,m,unexpected(),finite());
            assertThrows(UnsupportedOperationException.class,()->bound.invoke(new Call(site,TargetKind.DIRECT_RVA,0x1A81780L,S+8,in,n)));
            assertEquals(new Touch("W8",S+24),m.touches.getFirst()); // qualification did not pre-read entryRET
        }
        var alias=memory();descending(alias,33);alias.m.put(S,I+0x1A81368L);var original=n(700);var input=input(P,P+1320,33,T);
        var binding=SortRangeCalls300.bind(I,alias,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){throw new AssertionError("unused COPY");}
            @Override public NormalReturn tail(Tail t){alias.m.put(S+24,original.rbxBits()+1);
                return new NormalReturn(t.entry().volatileBits(),I+0x1A81A3EL,G,t.entry().nonvolatileBits());}
        },finite());
        assertThrows(UnsupportedOperationException.class,()->binding.invoke(new Call(0x1A81363L,TargetKind.DIRECT_RVA,0x1A81780L,S+8,input,original)));
    }

    @Test void allForeignNormalTailAndGsForwardExactObjectsWithoutMemory() {
        var m=memory();var n=n(700);var in=input(P,P,0,T);var seen=new ArrayList<Call>();var tails=new ArrayList<Tail>();var nr=new NormalReturn(in,1,2,n);
        var bound=SortRangeCalls300.bind(I,m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){seen.add(c);return in;}
            @Override public NormalReturn tail(Tail t){tails.add(t);return nr;}
            @Override public long readGsQword58(){return 0xABCD;}
        },(s,g)->{throw new AssertionError("foreign budget");});
        for(Call c:List.of(new Call(0x1A81364L,TargetKind.DIRECT_RVA,0x1A81780L,S,in,n),new Call(0x1A81363L,TargetKind.DIRECT_RVA,0,S,in,n),new Call(0x1A81363L,TargetKind.INDIRECT_ABSOLUTE,0x1A81780L,S,in,n))){assertSame(in,bound.invoke(c));assertSame(c,seen.getLast());}
        var tail=new Tail(0x1A81363L,TargetKind.DIRECT_RVA,0x1A81780L,new Entry(I+1,S,in,n));assertSame(nr,bound.tail(tail));assertSame(tail,tails.getFirst());
        assertEquals(0xABCD,bound.readGsQword58());assertTrue(m.touches.isEmpty());
    }
}
