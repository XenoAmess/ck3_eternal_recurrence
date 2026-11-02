package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.n;
import static org.xar.ck3.research.m4.Gate47Fixture273.qword;
import static org.xar.ck3.research.m4.SmallRangeFullState295Test.row;
import static org.xar.ck3.research.m4.SmallRangeFullState295Test.words;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.RotateFullState292Test.Observed;
import org.xar.ck3.research.m4.RotateFullState292Test.Touch;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Frozen without reading new adapter candidate; existing producers/byte fixture remain binary-only. */
final class BridgeMergeCalls298Test {
    static final long I=0x180000000L,J=I+0x123000L,S=0x100000L,B=S-0x68L,P=0x2000L,T=0x5000L,RIP=0x7fff12345678L;
    static VolatileBits input(long first,long mid,long end,long left){return RotateFullState292Test.regs(0xA000000000000000L,0xB000000000000001L,first,mid,end,left);}
    static VolatileBits bits(VolatileBits v,long a,long c,long d,long e,long f,long t){return new VolatileBits(a,c,d,e,f,t,v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    static NonvolatileBits active(NonvolatileBits n,long bx,long bp,long si,long r12,long r13){return new NonvolatileBits(bx,bp,si,n.rdiBits(),r12,r13,n.r14Bits(),n.r15Bits(),n.xmm6());}
    static void rows(Observed m,int...score){for(int k=0;k<score.length;k++)words(m.m.data,P+40L*k,row(k,score[k]));}
    static LoopBudget noBudget(){return (site,cursor)->{throw new AssertionError("unexpected loop "+site);};}
    static Calls noCalls(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected normal "+c);}@Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected tail "+t);}};}
    static LoopBudget budget(){int[] n={0};return (site,cursor)->{assertTrue(site==0x1A81AD0L||site==0x1A81B00L);assertTrue(++n[0]<20);};}

    @Test void actual293ConsumesBothNewMergeBoundariesWithoutAnAdapterPushOrRetPreRead() {
        var m=new Observed();m.m.put(S,RIP);m.m.put(S+0x28,1);m.m.put(S+0x30,T);m.m.put(S+0x38,7);m.m.put(S+0x40,0x11223344556677FFL);m.m.put(S+0x48,P+40);m.m.put(S+0x50,P+40);m.m.put(S+0x58,1);m.m.put(S+0x60,0);
        var n=n(0x5566778800000000L);var in=input(P,P+40,P+80,1);var expected=new HashMap<>(m.m.snapshot());
        qword(expected,S+0x18,P+80);qword(expected,S+8,P);qword(expected,S-8,n.rbxBits());qword(expected,S-0x10,n.rbpBits());qword(expected,S-0x18,n.rsiBits());qword(expected,S-0x20,n.r12Bits());qword(expected,S-0x28,n.r13Bits());qword(expected,B+0x30,7);qword(expected,B+0x28,T);qword(expected,S+0x20,0);qword(expected,B+0x20,0);qword(expected,S-0x58,n.r14Bits());qword(expected,S-0x78,n.r15Bits());qword(expected,S-0x70,I+0x1A83362L);expected.put(B+0x38,(byte)0xFF);
        var normalV=bits(in,P+40,P,P+40,P+40,1,in.r10Bits());var offeredN=active(n,255,0,P+40,T,7);var tailV=bits(in,P+40,P+40,P+40,P+80,0,in.r10Bits());var normal=new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,B,normalV,offeredN);var tail=new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A81AB0L,new Entry(I,S,tailV,n));
        var bound=BridgeMergeCalls298.bind(I,m,noCalls(),noBudget());var seen=new ArrayList<Object>();NormalReturn[] actualTail={null};
        var out=BridgeFullState293.execute(new Entry(I,S,in,n),m,new Calls(){@Override public VolatileBits invoke(Call c){assertEquals(normal,c);seen.add(c);return bound.invoke(c);}@Override public NormalReturn tail(Tail t){assertEquals(tail,t);seen.add(t);assertFalse(m.touches.contains(new Touch("R8",S)));actualTail[0]=bound.tail(t);return actualTail[0];}@Override public long readGsQword58(){throw new AssertionError("unused GS");}},noBudget());
        assertSame(actualTail[0],out);assertEquals(List.of(normal,tail),seen);assertEquals(new NormalReturn(bits(in,P+40,P+40,P+40,P+80,0,P+80),RIP,S+8,n),out);assertEquals(expected,m.m.snapshot());
        assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("W8",S-0x70))).count());assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("R8",S-0x70))).count());assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("R8",S))).count());assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("W8",S-8))).count());
        int last=-1;for(int k=0;k<m.touches.size();k++)if(m.touches.get(k).equals(new Touch("W8",S-0x70)))last=k;assertEquals(new Touch("R8",S-0x70),m.touches.get(last+1));assertEquals(List.of(new Touch("W8",S-8),new Touch("R8",S-8),new Touch("R8",S)),m.touches.subList(m.touches.size()-3,m.touches.size()));
    }

    @Test void exactNormalUsesRealTargetRetAndRejectsActualRipNonvolatileOrOpaqueTailSp() {
        var n=n(0x5566778800000000L);var empty=input(P,P+80,P+80,Long.MIN_VALUE);var m=new Observed();m.m.put(S,I+0x1A83362L);var before=m.m.snapshot();var bound=BridgeMergeCalls298.bind(I,m,noCalls(),noBudget());
        assertEquals(empty,bound.invoke(new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,S+8,empty,n)));assertEquals(before,m.m.snapshot());assertEquals(List.of(new Touch("R8",S)),m.touches);
        var wrongRip=new Observed();wrongRip.m.put(S,0xBAD);assertThrows(UnsupportedOperationException.class,()->BridgeMergeCalls298.bind(I,wrongRip,noCalls(),noBudget()).invoke(new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,S+8,empty,n)));assertEquals(List.of(new Touch("R8",S)),wrongRip.touches);
        var wrongN=new Observed();wrongN.m.put(S,I+0x1A83362L);wrongN.m.put(S+0x28,7);rows(wrongN,100,10,60,40,20);var raw=input(P,P+80,P+200,2);
        assertThrows(UnsupportedOperationException.class,()->BridgeMergeCalls298.bind(I,wrongN,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x1A81B49L,c.callSiteRva());wrongN.m.put(S-8,0xBAD);return c.volatileBits();}},budget()).invoke(new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,S+8,raw,n)));assertEquals(0xBAD,wrongN.m.readQword(S-8));assertEquals(new Touch("R8",S),wrongN.touches.getLast());
        var wrongSp=new Observed();wrongSp.m.put(S,I+0x1A83362L);wrongSp.m.put(S+0x28,7);wrongSp.m.put(S+0x40,0x11223344556677FEL);rows(wrongSp,100,50,10,60,20);var tails=new ArrayList<Tail>();
        assertThrows(UnsupportedOperationException.class,()->BridgeMergeCalls298.bind(I,wrongSp,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("no COPY");}@Override public NormalReturn tail(Tail t){assertEquals(0x1A82450L,t.targetBits());tails.add(t);return new NormalReturn(t.entry().volatileBits(),I+0x1A83362L,S+16,n);}},budget()).invoke(new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,S+8,input(P,P+120,P+200,3),n)));assertEquals(1,tails.size());assertFalse(wrongSp.touches.contains(new Touch("R8",S)));assertEquals(new Touch("R8",S-8),wrongSp.touches.getLast());
    }

    @Test void matchedTailPreservesActualEntryImageAndOpaqueNormalReturnOrExceptionIdentity() {
        var n=n(700);var in=input(P,P+120,P+200,3);var v=RotateFullState292Test.regs(900,901,902,903,904,905);var returned=new NormalReturn(v,0xBAD,0xDDD,n(999));var error=new IllegalStateException("opaque776 rejected");
        for(boolean fail:new boolean[]{false,true}){var m=new Observed();m.m.put(S,RIP);m.m.put(S+0x28,7);m.m.put(S+0x40,0x11223344556677FEL);rows(m,100,50,10,60,20);var expected=new HashMap<>(m.m.snapshot());qword(expected,S-8,n.rbxBits());qword(expected,S+8,n.rdiBits());var seen=new ArrayList<Tail>();
            var targetTail=new Tail(0x1A81B9CL,TargetKind.DIRECT_RVA,0x1A82450L,new Entry(J,S,bits(in,254,P+40,P+120,P+200,2,P+160),n));var bound=BridgeMergeCalls298.bind(I,m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("no COPY");}@Override public NormalReturn tail(Tail t){assertEquals(targetTail,t);seen.add(t);if(fail)throw error;return returned;}},budget());var offered=new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A81AB0L,new Entry(J,S,in,n));
            if(fail)assertSame(error,assertThrows(IllegalStateException.class,()->bound.tail(offered)));else assertSame(returned,bound.tail(offered));assertEquals(List.of(targetTail),seen);assertEquals(expected,m.m.snapshot());assertFalse(m.touches.contains(new Touch("R8",S)));assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("W8",S-8))).count());assertFalse(m.touches.contains(new Touch("W8",S-0x70)));
        }
    }

    @Test void everyForeignSiteTargetKindAndGsForwardsOriginalObjectsWithoutMemoryOrBudget() {
        var m=new Observed();var n=n(700);var v=input(P,P+40,P+80,1);var post=RotateFullState292Test.regs(900,901,902,903,904,905);var nr=new NormalReturn(post,31,32,n);var seen=new ArrayList<Object>();int[] gs={0};var bound=BridgeMergeCalls298.bind(I,m,new Calls(){@Override public VolatileBits invoke(Call c){seen.add(c);return post;}@Override public NormalReturn tail(Tail t){seen.add(t);return nr;}@Override public long readGsQword58(){gs[0]++;return 0xABCDEF0011223344L;}},noBudget());
        var calls=List.of(new Call(0x1A8335EL,TargetKind.DIRECT_RVA,0x1A81AB0L,S+8,v,n),new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB1L,S+8,v,n),new Call(0x1A8335DL,TargetKind.INDIRECT_ABSOLUTE,0x1A81AB0L,S+8,v,n));var tails=List.of(new Tail(0x1A833A3L,TargetKind.DIRECT_RVA,0x1A81AB0L,new Entry(I,S,v,n)),new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A81AB1L,new Entry(I,S,v,n)),new Tail(0x1A833A2L,TargetKind.INDIRECT_ABSOLUTE,0x1A81AB0L,new Entry(I,S,v,n)));
        for(var c:calls)assertSame(post,bound.invoke(c));for(var t:tails)assertSame(nr,bound.tail(t));assertEquals(0xABCDEF0011223344L,bound.readGsQword58());assertEquals(1,gs[0]);for(int k=0;k<3;k++){assertSame(calls.get(k),seen.get(k));assertSame(tails.get(k),seen.get(k+3));}assertTrue(m.touches.isEmpty());assertTrue(m.m.snapshot().isEmpty());
    }
}
