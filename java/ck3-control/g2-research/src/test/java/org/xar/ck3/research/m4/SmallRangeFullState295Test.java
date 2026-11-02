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
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner source literals; production reviewed, no Native/COPY/DF or blind-oracle claim. */
final class SmallRangeFullState295Test {
    static final long I=0x180000000L,S=0x400000L,G=S-0x48L,P=0x20000L,RIP=0x7fff44332211L;
    static long[] row(int id,int score){return new long[]{0xAABBCCDD00000000L|Integer.toUnsignedLong(score),0x1100000000000000L+id,0x2200000000000000L+id,0x3300000000000000L+id,0x4400000000000000L+id};}
    static void words(Map<Long,Byte> m,long at,long...xs){for(int i=0;i<xs.length;i++)qword(m,at+8L*i,xs[i]);}
    static void rows(Observed m,int...scores){for(int i=0;i<scores.length;i++)words(m.m.data,P+i*40L,row(i,scores[i]));}
    static void temp(Map<Long,Byte> map,long[] x){words(map,G+0x20,x[0],x[1],x[2],x[3]);qword(map,G+0x50,x[4]);}
    static void prologue(Map<Long,Byte> map,NonvolatileBits n,boolean empty){qword(map,S+0x18,n.rsiBits());qword(map,S-8,n.rdiBits());if(!empty)qword(map,S+0x10,n.rbxBits());}
    static VolatileBits bits(VolatileBits v,long a,long c,long d,long e,Bits128 x0,Bits128 x1,Bits128 x2,Bits128 x3,Bits128 x4){return new VolatileBits(a,c,d,e,v.r9Bits(),v.r10Bits(),v.r11Bits(),x0,x1,x2,x3,x4,v.xmm5());}
    static Bits128 first(long[] x){return new Bits128(x[0],x[1]);}
    static Bits128 second(long[] x){return new Bits128(x[2],x[3]);}
    static Bits128 tail(long[] x){return new Bits128(x[4],0);}
    static org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls noCalls(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected opaque call "+c);}};}
    static void suffix(Observed m,boolean empty){var expected=new ArrayList<Touch>();if(!empty)expected.add(new Touch("R8",S+0x10));expected.add(new Touch("R8",S+0x18));expected.add(new Touch("R8",S-8));expected.add(new Touch("R8",S));assertEquals(expected,m.touches.subList(m.touches.size()-expected.size(),m.touches.size()));}

    @Test void rowBlocksKeepWidthOrderAndFreshAliasedStackSnapshots() {
        var m=new Observed();var data=row(3,Integer.MIN_VALUE);words(m.m.data,P,data);var n=rbx(n(700),P);
        var in=v(0xE000000000000000L,0x777788889999AAAAL,0x123456789ABCDEFL,0x88889999AAAABBBBL);
        var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,G,in,n));
        var expected=new HashMap<>(m.m.snapshot());temp(expected,data);SmallRowBlocks295.capture(r,m);
        assertEquals(bits(in,in.raxBits(),0x80000000L,in.rdxBits(),P,in.xmm0(),in.xmm1(),first(data),second(data),tail(data)),r.volatileBits());assertEquals(n,r.nonvolatileBits());assertEquals(G,r.rsp);assertEquals(expected,m.m.snapshot());
        assertEquals(List.of(new Touch("R16",P),new Touch("R16",P+16),new Touch("R8",P+32),new Touch("W16",G+32),new Touch("W16",G+48),new Touch("W8",G+80)),m.touches);
        var alias=new Observed();words(alias.m.data,G+32,11,12,13,14);alias.m.put(G+80,15);
        var rn=new NonvolatileBits(700,701,G+40,703,704,705,706,707,new Bits128(708,709));
        var ar=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,G,in,rn));var ae=new HashMap<>(alias.m.snapshot());words(ae,G+40,11,12,13,14,15);
        SmallRowBlocks295.restoreFront(ar,alias);
        assertEquals(bits(in,in.raxBits(),in.rcxBits(),in.rdxBits(),in.r8Bits(),new Bits128(15,0),new Bits128(13,14),in.xmm2(),in.xmm3(),in.xmm4()),ar.volatileBits());assertEquals(rn,ar.nonvolatileBits());assertEquals(G,ar.rsp);assertEquals(ae,alias.m.snapshot());
        assertEquals(List.of(new Touch("R16",G+32),new Touch("R16",G+48),new Touch("W16",G+40),new Touch("R8",G+80),new Touch("W16",G+56),new Touch("W8",G+72)),alias.touches);
    }

    @Test void emptyAndSingleRowHaveDistinctFramePrefixesAndNoPayloadRead() {
        for(boolean empty:new boolean[]{true,false}) {
            var m=new Observed();m.m.put(S,RIP);var n=n(0x3344556600000000L);long end=empty?P:P+40;
            var in=v(0xE000000000000000L,Long.MIN_VALUE+1,P,end);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,empty);
            var out=SmallRangeFullState295.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->{throw new AssertionError("no loop");});
            assertEquals(new NormalReturn(rax(in,end),RIP,S+8,n),out);assertEquals(expected,m.m.snapshot());suffix(m,empty);
            assertFalse(m.touches.stream().anyMatch(t->t.op().equals("R4")||t.op().equals("R16")));
            assertEquals(empty?2:3,m.touches.stream().filter(t->t.op().equals("W8")).count());
        }
    }

    @Test void descendingTiesAndNegativeScoresStayStableWithFullPayloadAndVolatiles() {
        int[][] scores={{9,5,5},{Integer.MAX_VALUE,-1,Integer.MIN_VALUE}};
        for(int[] s:scores) {
            var m=new Observed();m.m.put(S,RIP);rows(m,s);var n=n(700);var in=v(0xE000000000000000L,-1,P,P+120);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,false);var last=row(2,s[2]);temp(expected,last);var headers=new ArrayList<Long>();
            var out=SmallRangeFullState295.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->{assertEquals(0x1A81210L,site);headers.add(guard);});
            assertEquals(List.of(P+40,P+80),headers);assertEquals(expected,m.m.snapshot());suffix(m,false);
            assertEquals(new NormalReturn(bits(in,P+120,Integer.toUnsignedLong(s[2]),P+120,P+80,in.xmm0(),in.xmm1(),first(last),second(last),tail(last)),RIP,S+8,n),out);
            assertEquals(0,m.touches.stream().filter(t->t.equals(new Touch("W8",G-8))).count());
        }
    }

    @Test void interiorShiftConsumesActual291OnceAndRetainsSourceXmmState() {
        var m=new Observed();m.m.put(S,RIP);rows(m,9,1,5);var n=n(700);var in=v(0xE000000000000000L,-1,P,P+120);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,false);var one=row(1,1);var five=row(2,5);words(expected,P+40,five);words(expected,P+80,one);temp(expected,five);
        var headers=new ArrayList<Touch>();var out=SmallRangeFullState295.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->headers.add(new Touch(Long.toHexString(site),guard)));
        assertEquals(List.of(new Touch("1a81210",P+40),new Touch("1a81210",P+80),new Touch("1a81280",P+40)),headers);
        assertEquals(expected,m.m.snapshot());suffix(m,false);
        assertEquals(new NormalReturn(bits(in,P+120,5,P+120,P+40,tail(one),second(one),first(five),second(five),tail(five)),RIP,S+8,n),out);
        int pos=m.touches.indexOf(new Touch("R16",P+40));
        // The first read of row1 is its earlier capture; select the later actual interleaved shift.
        pos=m.touches.subList(pos+1,m.touches.size()).indexOf(new Touch("R16",P+40))+pos+1;
        assertEquals(List.of(new Touch("R16",P+40),new Touch("W16",P+80),new Touch("R16",P+56),new Touch("W16",P+96),new Touch("R8",P+72),new Touch("W8",P+112)),m.touches.subList(pos,pos+6));
    }

    @Test void frontCallUsesSinglePushFullOpaquePostAndFreshStackSavedState() {
        var m=new Observed();m.m.put(S,RIP);rows(m,1,9);var n=n(0x3344556600000000L);var in=v(0xE000000000000000L,0x9988776655443322L,P,P+80);var post=v(0xA000000000000000L,0xB000000000000001L,0xC000000000000002L,0xD000000000000003L);
        var nine=row(1,9);var one=row(0,1);long[] actualTemp={0xF000000000000001L,0xE000000000000002L,0xD000000000000003L,0xC000000000000004L,0xB000000000000005L};
        long newB=0xABCDEF1234567801L,newS=0xABCDEF1234567802L,newD=0xABCDEF1234567803L,newRip=0x7fff88887777L;
        var offered=bits(in,in.raxBits(),P+40,P,40,in.xmm0(),in.xmm1(),first(nine),second(nine),tail(nine));
        var offeredN=new NonvolatileBits(P+40,n.rbpBits(),P,P+80,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());var expectedCall=new Call(0x1A81247L,TargetKind.DIRECT_RVA,0x4226860L,G,offered,offeredN);
        var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,false);temp(expected,actualTemp);words(expected,P,actualTemp);words(expected,P+40,one);qword(expected,G-8,I+0x1A8124CL);qword(expected,S+0x10,newB);qword(expected,S+0x18,newS);qword(expected,S-8,newD);qword(expected,S,newRip);var seen=new ArrayList<Call>();
        var out=SmallRangeFullState295.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            assertEquals(expectedCall,c);seen.add(c);assertEquals(I+0x1A8124CL,m.m.readQword(G-8));assertFalse(m.touches.contains(new Touch("R8",S)));
            words(m.m.data,P+40,one);temp(m.m.data,actualTemp);m.m.put(S+0x10,newB);m.m.put(S+0x18,newS);m.m.put(S-8,newD);m.m.put(S,newRip);return post;
        }},(site,guard)->{assertEquals(0x1A81210L,site);assertEquals(P+40,guard);});
        var finalN=new NonvolatileBits(newB,n.rbpBits(),newS,newD,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
        assertEquals(List.of(expectedCall),seen);assertEquals(expected,m.m.snapshot());suffix(m,false);
        assertEquals(new NormalReturn(bits(post,P+80,post.rcxBits(),post.rdxBits(),post.r8Bits(),tail(actualTemp),second(actualTemp),post.xmm2(),post.xmm3(),post.xmm4()),newRip,S+8,finalN),out);
        assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("W8",G-8))).count());assertFalse(m.touches.contains(new Touch("R8",G-8)));
    }

    @Test void budgetsMissingRowsAndOpaqueExceptionsKeepActualPriorFrames() {
        var n=n(700);var in=v(100,-1,P,P+80);var outer=new Observed();outer.m.put(S,RIP);rows(outer,1,9);var expected=new HashMap<>(outer.m.snapshot());prologue(expected,n,false);var stop=new IllegalArgumentException("finite outer");
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->SmallRangeFullState295.execute(new Entry(I,S,in,n),outer,noCalls(),(site,guard)->{assertEquals(0x1A81210L,site);throw stop;})));assertEquals(expected,outer.m.snapshot());assertFalse(outer.touches.contains(new Touch("R16",P+40)));
        var missing=new Observed();missing.m.put(S,RIP);words(missing.m.data,P,row(0,1));
        assertThrows(UnsupportedOperationException.class,()->SmallRangeFullState295.execute(new Entry(I,S,in,n),missing,noCalls(),(site,guard)->{}));assertEquals(new Touch("R16",P+40),missing.touches.getLast());assertEquals(3,missing.m.writes.size());
        var inner=new Observed();inner.m.put(S,RIP);rows(inner,9,1,5);expected=new HashMap<>(inner.m.snapshot());prologue(expected,n,false);temp(expected,row(2,5));
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->SmallRangeFullState295.execute(new Entry(I,S,v(100,-1,P,P+120),n),inner,noCalls(),(site,guard)->{if(site==0x1A81280L)throw stop;})));assertEquals(expected,inner.m.snapshot());
        var aborted=new Observed();aborted.m.put(S,RIP);rows(aborted,1,9);var error=new IllegalStateException("opaque refusal");
        assertSame(error,assertThrows(IllegalStateException.class,()->SmallRangeFullState295.execute(new Entry(I,S,in,n),aborted,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x1A81247L,c.callSiteRva());throw error;}},(site,guard)->{})));
        assertEquals(new Touch("W8",G-8),aborted.touches.getLast());assertEquals(I+0x1A8124CL,aborted.m.readQword(G-8));assertFalse(aborted.touches.contains(new Touch("R8",S)));
    }

    @Test void partialBlockFaultsRetainActualLoadAndWritePrefixes() {
        var in=v(100,-1,0x9988776655443322L,3);var n=rbx(n(700),P);var m=new Observed();words(m.m.data,P,11,12,13,14);var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,G,in,n));var before=m.m.snapshot();
        assertThrows(UnsupportedOperationException.class,()->SmallRowBlocks295.capture(r,m));assertEquals(before,m.m.snapshot());assertEquals(List.of(new Touch("R16",P),new Touch("R16",P+16),new Touch("R8",P+32)),m.touches);
        assertEquals(bits(in,in.raxBits(),in.rcxBits(),in.rdxBits(),P,in.xmm0(),in.xmm1(),new Bits128(11,12),new Bits128(13,14),in.xmm4()),r.volatileBits());
        var restore=new Observed();words(restore.m.data,G+32,21,22,23,24);words(restore.m.data,P,31,32,33,34,35);var rn=new NonvolatileBits(700,701,P,703,704,705,706,707,new Bits128(708,709));var rr=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,G,in,rn));var expected=new HashMap<>(restore.m.snapshot());words(expected,P,21,22);
        assertThrows(UnsupportedOperationException.class,()->SmallRowBlocks295.restoreFront(rr,restore));assertEquals(expected,restore.m.snapshot());assertEquals(List.of(new Touch("R16",G+32),new Touch("R16",G+48),new Touch("W16",P),new Touch("R8",G+80)),restore.touches);
        assertEquals(bits(in,in.raxBits(),in.rcxBits(),in.rdxBits(),in.r8Bits(),new Bits128(21,22),new Bits128(23,24),in.xmm2(),in.xmm3(),in.xmm4()),rr.volatileBits());assertEquals(rn,rr.nonvolatileBits());
    }
}
