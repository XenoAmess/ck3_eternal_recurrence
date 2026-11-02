package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import static org.xar.ck3.research.m4.SmallRangeFullState295Test.row;
import static org.xar.ck3.research.m4.SmallRangeFullState295Test.words;
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

/** Owner source-derived literals after reviewing production; opaque COPY/776 are not algorithms. */
final class MergeRangeFullState297Test {
    static final long I=0x180000000L,S=0x800008L,G=S-0x68L,C=S-0x70L,P=0x10000L,RIP=0x7fff778899AAL;
    static VolatileBits input(long first,long mid,long end,long left){return RotateFullState292Test.regs(100,0xE000000000000001L,first,mid,end,left);}
    static VolatileBits post(){return RotateFullState292Test.regs(0xB000000000000000L,1001,1002,1003,1004,1005);}
    static VolatileBits bits(VolatileBits v,long a,long c,long d,long e,long f,long t,Bits128 x0,Bits128 x1){return new VolatileBits(a,c,d,e,f,t,v.r11Bits(),x0,x1,v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    static NonvolatileBits nv(NonvolatileBits n,long bx,long di){return new NonvolatileBits(bx,n.rbpBits(),n.rsiBits(),di,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    static void frame(Observed m){m.m.put(S,RIP);m.m.put(S+0x28,7);m.m.put(S+0x40,0x11223344556677FEL);}
    static void rows(Observed m,long first,int...score){for(int k=0;k<score.length;k++)words(m.m.data,first+k*40L,row(k,score[k]));}
    static GovernmentCrtBoundary185Api.Calls noCalls(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected normal "+c);}@Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected tail "+t);}};}
    static LoopBudget bounded(List<Touch> seen){return (site,cursor)->{assertTrue(site==0x1A81AD0L||site==0x1A81B00L);seen.add(new Touch(Long.toHexString(site),cursor));assertTrue(seen.size()<50);};}
    static List<Touch> suffix(){return List.of(new Touch("R8",S-8),new Touch("R8",S));}
    static void localWords(Map<Long,Byte> e,long firstTemp,long secondTemp,long[] data){words(e,firstTemp,data[0],data[1]);words(e,secondTemp,data[2],data[3]);qword(e,G+0x78,data[4]);}

    @Test void rawEqualPointersAndSignedTiePrefixKeepFullStateAndExactReads() {
        var n=n(700);var empty=new Observed();empty.m.put(S,RIP);var in=input(P,P+80,P+80,Long.MIN_VALUE);
        var out=MergeRangeFullState297.execute(new Entry(I,S,in,n),empty,noCalls(),(site,cursor)->{throw new AssertionError("early budget");});
        assertEquals(new NormalReturn(in,RIP,S+8,n),out);assertEquals(List.of(new Touch("R8",S)),empty.touches);
        var left0=new Observed();left0.m.put(S,RIP);in=input(P,P,P+80,-1);var e=new HashMap<>(left0.m.snapshot());qword(e,S-8,n.rbxBits());
        var expected=bits(in,in.raxBits(),P,P,P+80,-1,P+80,in.xmm0(),in.xmm1());
        out=MergeRangeFullState297.execute(new Entry(I,S,in,n),left0,noCalls(),(site,cursor)->{throw new AssertionError("empty left");});
        assertEquals(new NormalReturn(expected,RIP,S+8,n),out);assertEquals(e,left0.m.snapshot());assertEquals(List.of(new Touch("W8",S-8),new Touch("R8",S-8),new Touch("R8",S)),left0.touches);
        var m=new Observed();frame(m);rows(m,P,0,-1,-1);in=input(P,P+80,P+120,2);e=new HashMap<>(m.m.snapshot());qword(e,S-8,n.rbxBits());var guards=new ArrayList<Touch>();
        out=MergeRangeFullState297.execute(new Entry(I,S,in,n),m,noCalls(),bounded(guards));
        assertEquals(new NormalReturn(bits(in,0xFFFFFFFFL,P,P+80,P+120,0,P+120,in.xmm0(),in.xmm1()),RIP,S+8,n),out);assertEquals(e,m.m.snapshot());
        assertEquals(List.of(new Touch("1a81ad0",P),new Touch("1a81ad0",P+40)),guards);assertEquals(List.of(new Touch("W8",S-8),new Touch("R4",P+80),new Touch("R4",P),new Touch("R4",P+40),new Touch("R8",S-8),new Touch("R8",S)),m.touches);
    }

    @Test void leftSingletonReloadsCallbackTempsAllPostsAndFreshFrameInSourceOrder() {
        var m=new Observed();frame(m);rows(m,P,100,10,60,40,20);var n=n(700);var in=input(P,P+80,P+200,2);var p=post();long[] data=row(1,10);var e=new HashMap<>(m.m.snapshot());qword(e,S-8,n.rbxBits());qword(e,S+8,n.rdiBits());localWords(e,G+0x40,G+0x50,data);qword(e,C,I+0x1A81B4EL);
        long a=0xA100000000000001L,b=0xA200000000000002L,c=0xA300000000000003L,d=0xA400000000000004L,q=0xA500000000000005L,newRip=0x12345678L;
        words(e,G+0x40,a,b);words(e,G+0x50,c,d);qword(e,G+0x78,q);qword(e,S+8,0xAA);qword(e,S-8,0xBB);qword(e,S,newRip);words(e,P+160,a,b,c,d,q);
        var offered=bits(in,10,P+40,P+80,120,1,P+160,new Bits128(data[4],0),in.xmm1());var expectedCall=new Call(0x1A81B49L,TargetKind.DIRECT_RVA,0x4226860L,G,offered,nv(n,P+40,120));var seen=new ArrayList<Call>();int[] at={0};
        var out=MergeRangeFullState297.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call call){assertEquals(expectedCall,call);seen.add(call);assertEquals(I+0x1A81B4EL,m.m.readQword(C));words(m.m.data,G+0x40,a,b);words(m.m.data,G+0x50,c,d);m.m.put(G+0x78,q);m.m.put(S+8,0xAA);m.m.put(S-8,0xBB);m.m.put(S,newRip);at[0]=m.touches.size();return p;}},bounded(new ArrayList<>()));
        assertEquals(List.of(expectedCall),seen);assertEquals(new NormalReturn(bits(p,p.raxBits(),p.rcxBits(),p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),new Bits128(q,0),new Bits128(c,d)),newRip,S+8,nv(n,0xBB,0xAA)),out);assertEquals(e,m.m.snapshot());
        assertEquals(List.of(new Touch("R16",G+0x40),new Touch("R16",G+0x50),new Touch("W16",P+160),new Touch("R8",G+0x78),new Touch("W16",P+176),new Touch("W8",P+192),new Touch("R8",S+8),new Touch("R8",S-8),new Touch("R8",S)),m.touches.subList(at[0],m.touches.size()));assertFalse(m.touches.contains(new Touch("R8",C)));
    }

    @Test void rightSingletonTieAndNegativeBackscanRestoreRdiBetweenTwoFreshLoads() {
        var m=new Observed();frame(m);rows(m,P,100,10,60,10,-20);var n=n(700);var in=input(P,P+80,P+200,2);var p=post();long[] data=row(2,60);var e=new HashMap<>(m.m.snapshot());qword(e,S-8,n.rbxBits());qword(e,S+8,n.rdiBits());localWords(e,G+0x50,G+0x40,data);qword(e,C,I+0x1A81BD2L);words(e,P+40,data);var seen=new ArrayList<Call>();var guards=new ArrayList<Touch>();int[] at={0};
        var offered=bits(in,10,P+80,P+40,40,1,P+40,new Bits128(data[4],0),in.xmm1());var expectedCall=new Call(0x1A81BCDL,TargetKind.DIRECT_RVA,0x4226860L,G,offered,nv(n,P+40,P+120));
        var out=MergeRangeFullState297.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call call){assertEquals(expectedCall,call);seen.add(call);at[0]=m.touches.size();return p;}},bounded(guards));
        assertEquals(List.of(expectedCall),seen);assertEquals(new NormalReturn(bits(p,p.raxBits(),p.rcxBits(),p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),new Bits128(data[4],0),new Bits128(data[2],data[3])),RIP,S+8,n),out);assertEquals(e,m.m.snapshot());
        assertEquals(List.of(new Touch("1a81ad0",P),new Touch("1a81ad0",P+40),new Touch("1a81b00",P+200),new Touch("1a81b00",P+160),new Touch("1a81b00",P+120)),guards);
        assertEquals(List.of(new Touch("R16",G+0x50),new Touch("R8",S+8),new Touch("R16",G+0x40),new Touch("W16",P+40),new Touch("R8",G+0x78),new Touch("W16",P+56),new Touch("W8",P+72),new Touch("R8",S-8),new Touch("R8",S)),m.touches.subList(at[0],m.touches.size()));
    }

    @Test void unknown776TailKeepsByteNeighborsRawFrameAndActualNormalReturnIdentity() {
        var m=new Observed();frame(m);rows(m,P,100,50,10,60,20);var n=n(700);var in=input(P,P+120,P+200,3);var e=new HashMap<>(m.m.snapshot());qword(e,S-8,n.rbxBits());qword(e,S+8,n.rdiBits());qword(e,S+0x28,7);e.put(S+0x40,(byte)0xFE);var p=post();var returned=new NormalReturn(p,0xBAD,0xDDD,n(900));var seen=new ArrayList<Tail>();
        var expected=new Tail(0x1A81B9CL,TargetKind.DIRECT_RVA,0x1A82450L,new Entry(I,S,bits(in,254,P+40,P+120,P+200,2,P+160,in.xmm0(),in.xmm1()),n));
        var out=MergeRangeFullState297.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("no COPY on tail");}@Override public NormalReturn tail(Tail t){assertEquals(expected,t);seen.add(t);assertEquals(0x11223344556677FEL,m.m.readQword(S+0x40));return returned;}},bounded(new ArrayList<>()));
        assertSame(returned,out);assertEquals(List.of(expected),seen);assertEquals(e,m.m.snapshot());assertFalse(m.touches.contains(new Touch("R8",S)));assertFalse(m.touches.contains(new Touch("W8",C)));assertEquals(new Touch("R8",S-8),m.touches.getLast());
    }

    @Test void finiteLoopsAndOpaqueThrowKeepOnlyActualPrefixWithoutSyntheticEpilogue() {
        var n=n(700);var error=new IllegalArgumentException("finite stop");
        for(long site:new long[]{0x1A81AD0L,0x1A81B00L}){var m=new Observed();frame(m);rows(m,P,100,10,60,40,20);var e=new HashMap<>(m.m.snapshot());qword(e,S-8,n.rbxBits());if(site==0x1A81B00L)qword(e,S+8,n.rdiBits());
            assertSame(error,assertThrows(IllegalArgumentException.class,()->MergeRangeFullState297.execute(new Entry(I,S,input(P,P+80,P+200,2),n),m,noCalls(),(s,cursor)->{if(s==site)throw error;})));assertEquals(e,m.m.snapshot());assertFalse(m.touches.contains(new Touch("W8",C)));assertFalse(m.touches.contains(new Touch("R8",S)));if(site==0x1A81AD0L)assertFalse(m.touches.contains(new Touch("R4",P)));else assertFalse(m.touches.contains(new Touch("R4",P+160)));
        }
        var m=new Observed();frame(m);rows(m,P,100,10,60,40,20);var e=new HashMap<>(m.m.snapshot());qword(e,S-8,n.rbxBits());qword(e,S+8,n.rdiBits());localWords(e,G+0x40,G+0x50,row(1,10));qword(e,C,I+0x1A81B4EL);
        assertSame(error,assertThrows(IllegalArgumentException.class,()->MergeRangeFullState297.execute(new Entry(I,S,input(P,P+80,P+200,2),n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x1A81B49L,c.callSiteRva());throw error;}},bounded(new ArrayList<>()))));assertEquals(e,m.m.snapshot());assertEquals(new Touch("W8",C),m.touches.getLast());assertFalse(m.touches.contains(new Touch("R8",S)));
    }

    @Test void destinationAliasingSavedRbxUsesInterleavedSourceFrameAndFreshPop() {
        long first=G-0x10,mid=G+0x18,end=G+0x68;var m=new Observed();frame(m);rows(m,first,10,60,20);var n=n(700);var in=input(first,mid,end,1);var data=row(0,10);var e=new HashMap<>(m.m.snapshot());qword(e,S-8,n.rbxBits());qword(e,S+8,n.rdiBits());localWords(e,G+0x40,G+0x50,data);qword(e,C,I+0x1A81B4EL);words(e,G+0x40,data);
        var out=MergeRangeFullState297.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x1A81B49L,c.callSiteRva());assertEquals(mid,c.volatileBits().rdxBits());assertEquals(80,c.volatileBits().r8Bits());assertEquals(new Bits128(data[4],0),c.volatileBits().xmm0());return c.volatileBits();}},bounded(new ArrayList<>()));
        assertEquals(new NormalReturn(bits(in,10,first,mid,80,1,G+0x40,new Bits128(data[4],0),new Bits128(data[2],data[3])),RIP,S+8,nv(n,data[4],n.rdiBits())),out);assertEquals(e,m.m.snapshot());assertEquals(suffix(),m.touches.subList(m.touches.size()-2,m.touches.size()));assertEquals(data[4],m.m.readQword(S-8));
    }

    @Test void actual296ConsumerExecutesOnlyNew329OnceAndPreservesFullParentContinuation() {
        var m=new Observed();long pg=S-0x68,pc=pg-8,mid=P+680,end=P+1320;m.m.put(S,RIP);m.m.put(S+0x28,17);m.m.put(S+0x30,0x8899AABBCCDDEEFEL);for(int k=0;k<33;k++)words(m.m.data,P+k*40L,row(k,100-k));var n=n(700);var in=RotateFullState292Test.regs(100,0xE000000000000001L,P,end,33,0x40000);var p1=post();var p2=RotateFullState292Test.regs(500,501,502,503,504,505);var e=new HashMap<>(m.m.snapshot());
        qword(e,S-8,n.rsiBits());qword(e,S-0x10,n.rdiBits());qword(e,S-0x18,n.r14Bits());qword(e,S-0x20,n.r15Bits());qword(e,S+8,n.rbxBits());qword(e,S+0x10,n.rbpBits());qword(e,S+0x18,n.r12Bits());qword(e,S-0x28,n.r13Bits());qword(e,pg+0x20,16);qword(e,pg+0x28,0x40000);qword(e,pg+0x30,17);e.put(pg+0x38,(byte)0xFE);qword(e,pc,I+0x1A813CBL);qword(e,pg-0x10,254);
        var seen=new ArrayList<Call>();var guards=new ArrayList<Touch>();GovernmentCrtBoundary185Api.Calls fallback=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){seen.add(c);assertEquals(0x1A81780L,c.targetBits());assertEquals(seen.size()==1?0x1A81363L:0x1A81378L,c.callSiteRva());return seen.size()==1?p1:p2;}};
        var out=DispatchRangeFullState296.execute(new Entry(I,S,in,n),m,MergeRangeCalls297.bind(I,m,fallback,bounded(guards)),bounded(new ArrayList<>()));
        assertEquals(2,seen.size());var expectedV=bits(p2,83,P,mid,end,0,end,p2.xmm0(),p2.xmm1());assertEquals(new NormalReturn(expectedV,RIP,S+8,n),out);assertEquals(e,m.m.snapshot());var expectedGuards=new ArrayList<Touch>();for(int k=0;k<17;k++)expectedGuards.add(new Touch("1a81ad0",P+k*40L));assertEquals(expectedGuards,guards);
        assertEquals(3,m.touches.stream().filter(t->t.equals(new Touch("W8",pc))).count());assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("R8",pc))).count());int last=-1;for(int k=0;k<m.touches.size();k++)if(m.touches.get(k).equals(new Touch("W8",pc)))last=k;assertEquals(new Touch("W8",pg-0x10),m.touches.get(last+1));
    }

    @Test void exactAdapterForwardsForeignPortsAndRejectsRealRetOrSavedNMutation() {
        var m=new Observed();var n=n(700);var in=input(P,P+80,P+200,2);var seen=new ArrayList<Object>();var p=post();var result=new NormalReturn(p,31,32,n);GovernmentCrtBoundary185Api.Calls fallback=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){seen.add(c);return p;}@Override public NormalReturn tail(Tail t){seen.add(t);return result;}@Override public long readGsQword58(){return 77;}};var bound=MergeRangeCalls297.bind(I,m,fallback,(site,cursor)->{throw new AssertionError("foreign budget");});
        var calls=List.of(new Call(0x1A813C7L,TargetKind.DIRECT_RVA,0x1A81AB0L,S+8,in,n),new Call(0x1A813C6L,TargetKind.DIRECT_RVA,0x1A81AB1L,S+8,in,n),new Call(0x1A813C6L,TargetKind.INDIRECT_ABSOLUTE,0x1A81AB0L,S+8,in,n));for(var c:calls)assertSame(p,bound.invoke(c));var t=new Tail(0x1A813C6L,TargetKind.DIRECT_RVA,0x1A81AB0L,new Entry(I,S,in,n));assertSame(result,bound.tail(t));assertEquals(77,bound.readGsQword58());for(int k=0;k<3;k++)assertSame(calls.get(k),seen.get(k));assertSame(t,seen.getLast());assertTrue(m.touches.isEmpty());
        for(boolean rip:new boolean[]{true,false}){var a=new Observed();frame(a);a.m.put(S,I+0x1A813CBL);rows(a,P,100,10,60,40,20);var selected=MergeRangeCalls297.bind(I,a,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x1A81B49L,c.callSiteRva());a.m.put(rip?S:S-8,0xBAD);return c.volatileBits();}},bounded(new ArrayList<>()));
            assertThrows(UnsupportedOperationException.class,()->selected.invoke(new Call(0x1A813C6L,TargetKind.DIRECT_RVA,0x1A81AB0L,S+8,in,n)));assertEquals(0xBAD,a.m.readQword(rip?S:S-8));assertEquals(new Touch("R8",S),a.touches.getLast());assertEquals(1,a.touches.stream().filter(x->x.equals(new Touch("W8",S-8))).count());assertEquals(1,a.touches.stream().filter(x->x.equals(new Touch("R8",S))).count());
        }
    }
}
