package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.RotateFullState292Test.Observed;
import org.xar.ck3.research.m4.RotateFullState292Test.Touch;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner source literals. Owner wrote the whole producer; binder/counter were not read
 * before this Test was frozen. No COPY algorithm or hardware claim is made.
 */
final class ScratchMergeFullState302Test {
    static final long I=0x180000000L,E=0xA0000L,G=E-0x68L,P=0x2000L,T=0x6000L,RIP=0x7fff12345678L;
    static long[] row(int id,int score){return new long[]{0xAABBCCDD00000000L|Integer.toUnsignedLong(score),0x1100000000000000L+id,0x2200000000000000L+id,0x3300000000000000L+id,0x4400000000000000L+id};}
    static void words(Map<Long,Byte> map,long at,long[] values){for(int i=0;i<5;i++)qword(map,at+i*8L,values[i]);}
    static Bits128 first(long[] r){return new Bits128(r[0],r[1]);}
    static Bits128 second(long[] r){return new Bits128(r[2],r[3]);}
    static Bits128 last(long[] r){return new Bits128(r[4],0);}
    static VolatileBits in(long first,long middle,long last,long left){var v=v(100,0xFEED,first,middle);return new VolatileBits(v.raxBits(),first,middle,last,left,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    static VolatileBits bits(VolatileBits v,long a,long c,long d,long r8,long r9,long r10,long r11,Bits128 x0,Bits128 x1){return new VolatileBits(a,c,d,r8,r9,r10,r11,x0,x1,v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    static NonvolatileBits homes(NonvolatileBits n,long bx,long si,long di){return new NonvolatileBits(bx,n.rbpBits(),si,di,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    static Observed frame(long right,long capacity,boolean ret){var m=new Observed();m.m.put(E+0x28,right);m.m.put(E+0x30,T);m.m.put(E+0x38,capacity);m.m.put(E+0x40,0x11223344556677E1L);if(ret)m.m.put(E,RIP);return m;}
    static void rows(Observed m,int...scores){for(int i=0;i<scores.length;i++)words(m.m.data,P+i*40L,row(i+1,scores[i]));}
    static void prologue(Map<Long,Byte> map,NonvolatileBits n,boolean right){qword(map,E+0x10,n.rbxBits());qword(map,E-8,n.rdiBits());if(right)qword(map,E+8,n.rsiBits());}
    static GovernmentCrtBoundary185Api.Calls unused(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected call "+c);}};}
    static LoopBudget finite(List<Long> sites){return(site,guard)->{sites.add(site);assertTrue(sites.size()<20);};}

    @Test void wholeEntryGeneralBranchConsumesReal301WithoutRepeatingPrologue() {
        var m=frame(0,-1,true);var n=n(700);var v=in(P,P,P,0);var sites=new ArrayList<Long>();LoopBudget budget=finite(sites);
        var calls=BridgeMergeCalls298.bind(I,m,unused(),budget);
        var out=ScratchMergeFullState302.execute(new Entry(I,E,v,n),m,calls,budget);
        assertEquals(RIP,out.returnRipBits());assertEquals(E+8,out.callerRspBits());assertEquals(n,out.nonvolatileBits());assertEquals(E-0x18,out.volatileBits().r11Bits());
        assertEquals(List.of(new Touch("W8",E+0x10),new Touch("W8",E-8),new Touch("R8",G+0x90),new Touch("R8",G+0xA0),new Touch("R1",G+0xA8),new Touch("W1",G+0xA8),new Touch("W8",G+0xA0),new Touch("W8",G+0x90),new Touch("R8",G+0x78),new Touch("R8",G+0x60)),m.touches.subList(0,10));
        assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("W8",E-8))).count());assertTrue(sites.isEmpty());
    }

    @Test void leftScratchRightExhaustionProducesExactOpaqueTailWithoutRetRead() {
        var m=frame(2,2,false);rows(m,1,2,3,4);var n=n(700);var v=in(P,P+80,P+160,2);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,false);
        words(expected,T,row(1,1));words(expected,T+40,row(2,2));words(expected,P,row(3,3));words(expected,P+40,row(4,4));
        var tailV=bits(v,1,P+80,T,80,P+160,P+80,T+40,last(row(4,4)),second(row(4,4)));
        var offered=new Tail(0x1A8252FL,TargetKind.DIRECT_RVA,0x4226860L,new Entry(I,E,tailV,n));var marker=new NormalReturn(v,0xABC,0xDEF,n);var seen=new ArrayList<Tail>();
        var calls=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected normal");}@Override public NormalReturn tail(Tail t){assertEquals(offered,t);seen.add(t);return marker;}};
        assertSame(marker,ScratchMergeFullState302.execute(new Entry(I,E,v,n),m,calls,finite(new ArrayList<>())));
        assertEquals(1,seen.size());assertEquals(expected,m.m.snapshot());assertFalse(m.touches.contains(new Touch("R8",E)));
    }

    @Test void leftScratchNormalCallConsumesAllPostBitsAndFreshSpilledRowAndHomes() {
        var m=frame(2,2,true);rows(m,5,4,3,2);var n=n(700);var v=in(P,P+80,P+160,2);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,false);
        words(expected,T,row(1,5));words(expected,T+40,row(2,4));words(expected,P,row(3,3));words(expected,P+40,row(1,5));
        var fresh=row(9,-7);qword(expected,G+0x40,fresh[0]);qword(expected,G+0x48,fresh[1]);qword(expected,G+0x50,fresh[2]);qword(expected,G+0x58,fresh[3]);qword(expected,G+0x90,fresh[4]);qword(expected,E-8,0x666);
        qword(expected,E+0x10,0x555);qword(expected,E,0x777);qword(expected,G-8,I+0x1A8258DL);words(expected,P+120,fresh);
        var post=v(2000,0x101,0x202,0x303);var calls=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            assertEquals(new Call(0x1A82588L,TargetKind.DIRECT_RVA,0x4226860L,G,
                    bits(v,5,P+80,P+120,40,P+120,P+80,T+40,last(row(2,4)),second(row(1,5))),homes(n,P+80,n.rsiBits(),40)),c);
            assertEquals(I+0x1A8258DL,m.m.readQword(G-8));
            qword(m.m.data,G+0x40,fresh[0]);qword(m.m.data,G+0x48,fresh[1]);qword(m.m.data,G+0x50,fresh[2]);qword(m.m.data,G+0x58,fresh[3]);qword(m.m.data,G+0x90,fresh[4]);
            m.m.put(E+0x10,0x555);m.m.put(E-8,0x666);m.m.put(E,0x777);return post;
        }};
        var out=ScratchMergeFullState302.execute(new Entry(I,E,v,n),m,calls,finite(new ArrayList<>()));
        assertEquals(new NormalReturn(bits(post,post.raxBits(),post.rcxBits(),post.rdxBits(),post.r8Bits(),post.r9Bits(),post.r10Bits(),post.r11Bits(),last(fresh),second(fresh)),0x777,E+8,homes(n,0x555,n.rsiBits(),0x666)),out);
        assertEquals(expected,m.m.snapshot());assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("W8",G-8))).count());
    }

    @Test void rightScratchLeftExhaustionPreservesFullTailFrameAndAllDataPrefix() {
        var m=frame(2,2,false);rows(m,1,2,3,4,5);var n=n(700);var v=in(P,P+120,P+200,3);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);
        words(expected,T,row(4,4));words(expected,T+40,row(5,5));words(expected,P+160,row(3,3));words(expected,P+120,row(2,2));words(expected,P+80,row(1,1));words(expected,P+40,row(5,5));
        var offered=new Tail(0x1A826A5L,TargetKind.DIRECT_RVA,0x4226860L,new Entry(I,E,bits(v,1,P,T,40,P+80,P+120,v.r11Bits(),last(row(5,5)),second(row(5,5))),n));var marker=new NormalReturn(v,0x123,0x456,n);
        var calls=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected normal");}@Override public NormalReturn tail(Tail t){assertEquals(offered,t);return marker;}};
        assertSame(marker,ScratchMergeFullState302.execute(new Entry(I,E,v,n),m,calls,finite(new ArrayList<>())));assertEquals(expected,m.m.snapshot());assertFalse(m.touches.contains(new Touch("R8",E)));
    }

    @Test void rightScratchNormalCallPreservesOpaquePostAndReloadsRsiBeforeLastStore() {
        var m=frame(2,2,true);rows(m,5,4,3,2,1);var n=n(700);var v=in(P,P+120,P+200,3);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);
        words(expected,T,row(4,2));words(expected,T+40,row(5,1));words(expected,P+160,row(3,3));words(expected,P+120,row(5,1));words(expected,P+80,row(2,4));words(expected,P,row(4,2));
        qword(expected,G-8,I+0x1A826FCL);qword(expected,E+8,0x111);qword(expected,E+0x10,0x222);qword(expected,E-8,0x333);var post=v(3000,0x444,0x555,0x666);
        var calls=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            assertEquals(new Call(0x1A826F7L,TargetKind.DIRECT_RVA,0x4226860L,G,
                    bits(v,4,P+40,P,40,P+120,P+120,v.r11Bits(),last(row(2,4)),second(row(2,4))),homes(n,P,T,P+200)),c);
            m.m.put(E+8,0x111);m.m.put(E+0x10,0x222);m.m.put(E-8,0x333);return post;
        }};
        var out=ScratchMergeFullState302.execute(new Entry(I,E,v,n),m,calls,finite(new ArrayList<>()));
        assertEquals(new NormalReturn(bits(post,post.raxBits(),post.rcxBits(),post.rdxBits(),post.r8Bits(),post.r9Bits(),post.r10Bits(),post.r11Bits(),last(row(4,2)),second(row(4,2))),RIP,E+8,homes(n,0x222,0x111,0x333)),out);
        assertEquals(expected,m.m.snapshot());
        int at=m.touches.lastIndexOf(new Touch("R8",G+0x70));assertTrue(at>0);assertEquals(new Touch("W8",P+0x20),m.touches.get(at+1));
    }

    @Test void signedNegativeAndTieScoresChooseScratchAtTheLiteralLessOrEqualBranch() {
        for(int rightScore:new int[]{Integer.MIN_VALUE,-1}) {
            var m=frame(2,2,true);rows(m,-1,-2,0,rightScore);var marker=new IllegalStateException("normal opaque stop");
            var calls=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x1A82588L,c.callSiteRva());throw marker;}};
            assertSame(marker,assertThrows(IllegalStateException.class,()->ScratchMergeFullState302.execute(new Entry(I,E,in(P,P+80,P+160,2),n(700)),m,calls,finite(new ArrayList<>()))));
            assertEquals(I+0x1A8258DL,m.m.readQword(G-8));assertFalse(m.touches.contains(new Touch("R8",E)));
        }
    }

    @Test void actual297TailEntersWhole302ExactlyOnceWithoutCallerPushOrDefaultR9() {
        var m=frame(2,2,false);rows(m,1,2,3,4);var n=n(700);var v=in(P,P+80,P+160,2);var marker=new NormalReturn(v,0x123,0x456,n);var seen=new ArrayList<Tail>();
        var fallback=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected normal");}@Override public NormalReturn tail(Tail t){assertEquals(0x1A8252FL,t.jumpSiteRva());assertEquals(E,t.entry().rspBits());assertEquals(80,t.entry().volatileBits().r8Bits());assertEquals(n,t.entry().nonvolatileBits());seen.add(t);return marker;}};
        var result=MergeRangeFullState297.execute(new Entry(I,E,v,n),m,ScratchMergeCalls302.bind(m,fallback,finite(new ArrayList<>())),finite(new ArrayList<>()));
        assertSame(marker,result);assertEquals(1,seen.size());assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("W8",E-8))).count());
        assertFalse(m.touches.contains(new Touch("R8",E)));assertEquals(3,m.m.readDword(P));assertEquals(4,m.m.readDword(P+40));
    }

    @Test void binderForwardsForeignTailInvokeAndGsWithoutMemoryEligibilityReads() {
        var m=new Observed();var n=n(700);var v=in(P,P+80,P+160,2);var e=new Entry(-1,E,v,n);var marker=new NormalReturn(v,0xABC,0xDEF,n);var seen=new ArrayList<Object>();
        var fallback=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){seen.add(c);return v;}@Override public NormalReturn tail(Tail t){seen.add(t);return marker;}@Override public long readGsQword58(){return Long.MIN_VALUE;}};
        var calls=ScratchMergeCalls302.bind(m,fallback,(site,guard)->{throw new AssertionError("foreign budget");});
        for(var t:List.of(new Tail(0x1A81B9BL,TargetKind.DIRECT_RVA,0x1A82450L,e),new Tail(0x1A81B9CL,TargetKind.DIRECT_RVA,0x1A82451L,e),new Tail(0x1A81B9CL,TargetKind.INDIRECT_ABSOLUTE,0x1A82450L,e))){assertSame(marker,calls.tail(t));assertSame(t,seen.getLast());}
        var c=new Call(0x1A81B49L,TargetKind.DIRECT_RVA,0x4226860L,E,v,n);assertSame(v,calls.invoke(c));assertSame(c,seen.getLast());assertEquals(Long.MIN_VALUE,calls.readGsQword58());assertTrue(m.touches.isEmpty());
    }

    @Test void budgetAndMissingLaterRowLoadRetainExactSourceSideEffects() {
        var n=n(700);var m=frame(2,2,false);rows(m,1,2,3,4);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,false);var stop=new IllegalArgumentException("finite copy loop");
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->ScratchMergeFullState302.execute(new Entry(I,E,in(P,P+80,P+160,2),n),m,unused(),(site,guard)->{assertEquals(0x1A824A0L,site);assertEquals(P,guard);throw stop;})));
        assertEquals(expected,m.m.snapshot());assertEquals(new Touch("R8",G+0x98),m.touches.getLast());
        var missing=frame(2,2,false);qword(missing.m.data,P,11);qword(missing.m.data,P+8,12);expected=new HashMap<>(missing.m.snapshot());prologue(expected,n,false);qword(expected,T,11);qword(expected,T+8,12);
        assertThrows(UnsupportedOperationException.class,()->ScratchMergeFullState302.execute(new Entry(I,E,in(P,P+80,P+160,2),n),missing,unused(),finite(new ArrayList<>())));
        assertEquals(expected,missing.m.snapshot());assertEquals(new Touch("R16",P+0x10),missing.touches.getLast());
    }
}
