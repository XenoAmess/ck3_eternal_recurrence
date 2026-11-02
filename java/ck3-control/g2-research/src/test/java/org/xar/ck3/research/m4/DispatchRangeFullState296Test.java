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

/** Owner source literals after production review, not blind/Native/opaque-helper qualification. */
final class DispatchRangeFullState296Test {
    static final long I=0x180000000L,S=0x800008L,G=S-0x68L,C=S-0x70L,P=0x10000L,T=0x40000L,RIP=0x7fff778899AAL;
    static final int TAG=0xFE;
    static VolatileBits input(long seed,long count,long end){return RotateFullState292Test.regs(seed,seed+1,P,end,count,T);}
    static VolatileBits post(long seed){return RotateFullState292Test.regs(seed,seed+1,seed+2,seed+3,seed+4,seed+5);}
    static VolatileBits args(VolatileBits v,long a,long c,long d,long e,long f){return new VolatileBits(a,c,d,e,f,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    static NonvolatileBits offered(NonvolatileBits n,long floor,long ceil,long mid,long cap,long end){return new NonvolatileBits(TAG,floor,P,ceil,mid,cap,end,T,n.xmm6());}
    static void frame(Observed m,long cap){m.m.put(S,RIP);m.m.put(S+0x28,cap);m.m.put(S+0x30,0x8899AABBCCDDEE00L|TAG);}
    static void prologue(Map<Long,Byte> m,NonvolatileBits n,boolean main){
        qword(m,S-8,n.rsiBits());qword(m,S-0x10,n.rdiBits());qword(m,S-0x18,n.r14Bits());qword(m,S-0x20,n.r15Bits());
        if(main){qword(m,S+8,n.rbxBits());qword(m,S+0x10,n.rbpBits());qword(m,S+0x18,n.r12Bits());qword(m,S-0x28,n.r13Bits());}
    }
    static GovernmentCrtBoundary185Api.Calls noCalls(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected port "+c);}};}
    static void fullSuffix(Observed m){assertEquals(List.of(new Touch("R8",G+0x40),new Touch("R8",G+0x80),new Touch("R8",G+0x78),new Touch("R8",G+0x70),new Touch("R8",S-0x20),new Touch("R8",S-0x18),new Touch("R8",S-0x10),new Touch("R8",S-8),new Touch("R8",S)),m.touches.subList(m.touches.size()-9,m.touches.size()));}

    @Test void signedShortTailUsesActual295WithNoExtraPushOrParentRet() {
        for(long count:new long[]{Long.MIN_VALUE,1}) {
            var m=new Observed();m.m.put(S,RIP);var n=n(0x5566778800000000L);long end=count<0?P:P+40;var in=input(0xE000000000000000L,count,end);
            var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,false);qword(expected,S+0x18,n.rsiBits());qword(expected,S-8,n.rdiBits());if(count>0)qword(expected,S+0x10,n.rbxBits());
            var out=DispatchRangeFullState296.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->{throw new AssertionError("short no budget");});
            assertEquals(new NormalReturn(args(in,end,P,end,count,T),RIP,S+8,n),out);assertEquals(expected,m.m.snapshot());
            assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("R8",S))).count());
            assertEquals(List.of(new Touch("R8",S-0x20),new Touch("R8",S-0x18),new Touch("R8",S-0x10),new Touch("R8",S-8)),m.touches.subList(4,8));
            assertFalse(m.touches.stream().anyMatch(t->t.op().equals("R4")||t.op().equals("R16")));
        }
    }

    @Test void oddDirectSplitPreservesAllPortPostsByteNeighborsAndFreshSavedFrame() {
        long end=P+1320,mid=P+680;var m=new Observed();frame(m,17);m.m.put(G+0x20,0x1122334455667788L);m.m.put(G+0x28,0x2233445566778899L);m.m.put(G+0x30,0x33445566778899AAL);m.m.put(G+0x38,0x445566778899AABBL);
        var n=n(0x5566778800000000L);var in=input(0xE000000000000000L,33,end);var p1=post(0xA000000000000000L);var p2=post(0xB000000000000000L);var p3=post(0xC000000000000000L);var nv=offered(n,16,17,mid,17,end);
        var expectedCalls=List.of(new Call(0x1A81363L,TargetKind.DIRECT_RVA,0x1A81780L,G,args(in,85,P,mid,17,T),nv),new Call(0x1A81378L,TargetKind.DIRECT_RVA,0x1A81780L,G,args(p1,p1.raxBits(),mid,end,16,T),nv),new Call(0x1A813C6L,TargetKind.DIRECT_RVA,0x1A81AB0L,G,args(p2,p2.raxBits(),P,mid,end,17),nv));
        var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);qword(expected,G+0x20,16);qword(expected,G+0x28,T);qword(expected,G+0x30,17);expected.put(G+0x38,(byte)TAG);qword(expected,C,I+0x1A813CBL);
        long change=0x1234567800000000L,newRip=0x7fffABCDEF01L;
        qword(expected,G+0x40,change+13);qword(expected,G+0x80,change+12);qword(expected,G+0x78,change+5);qword(expected,G+0x70,change+3);
        qword(expected,S-0x20,change+15);qword(expected,S-0x18,change+14);qword(expected,S-0x10,change+7);qword(expected,S-8,change+6);qword(expected,S,newRip);
        var seen=new ArrayList<Call>();var out=DispatchRangeFullState296.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            int k=seen.size();assertEquals(expectedCalls.get(k),c);seen.add(c);assertEquals(I+c.callSiteRva()+5,m.m.readQword(C));
            if(k<2){assertEquals(0x11223344556677FEL,m.m.readQword(G+0x20));return k==0?p1:p2;}
            assertEquals(16,m.m.readQword(G+0x20));assertEquals(T,m.m.readQword(G+0x28));assertEquals(17,m.m.readQword(G+0x30));assertEquals(0x445566778899AAFEL,m.m.readQword(G+0x38));
            m.m.put(G+0x40,change+13);m.m.put(G+0x80,change+12);m.m.put(G+0x78,change+5);m.m.put(G+0x70,change+3);
            m.m.put(S-0x20,change+15);m.m.put(S-0x18,change+14);m.m.put(S-0x10,change+7);m.m.put(S-8,change+6);m.m.put(S,newRip);return p3;
        }},(site,guard)->{throw new AssertionError("no self/row loops");});
        var finalN=new NonvolatileBits(change+3,change+5,change+6,change+7,change+12,change+13,change+14,change+15,n.xmm6());
        assertEquals(expectedCalls,seen);assertEquals(new NormalReturn(p3,newRip,S+8,finalN),out);assertEquals(expected,m.m.snapshot());fullSuffix(m);
        assertEquals(3,m.touches.stream().filter(t->t.equals(new Touch("W8",C))).count());assertFalse(m.touches.contains(new Touch("R8",C)));
    }

    @Test void recursionConsumesTwoReal295ChildrenAndOnlyRootMergePort() {
        long end=P+1320,mid=P+680;var m=new Observed();frame(m,0);var data=new HashMap<Long,Byte>();
        for(int k=0;k<33;k++)words(data,P+k*40L,row(k,100-k));m.m.data.putAll(data);
        var n=n(700);var in=input(0xE000000000000000L,33,end);var p=post(0xA000000000000000L);long[] last=row(32,68);
        var mergeV=new VolatileBits(end,P,mid,end,17,in.r10Bits(),in.r11Bits(),in.xmm0(),in.xmm1(),new Bits128(last[0],last[1]),new Bits128(last[2],last[3]),new Bits128(last[4],0),in.xmm5());
        var expectedCall=new Call(0x1A813C6L,TargetKind.DIRECT_RVA,0x1A81AB0L,G,mergeV,offered(n,16,17,mid,0,end));var seen=new ArrayList<Call>();var self=new ArrayList<Touch>();var rows=new ArrayList<Long>();
        var out=DispatchRangeFullState296.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(expectedCall,c);seen.add(c);assertEquals(16,m.m.readQword(G+0x20));assertEquals(0,m.m.readQword(G+0x30));return p;}},(site,guard)->{if(site==0x1A81210L)rows.add(guard);else self.add(new Touch(Long.toHexString(site),guard));});
        assertEquals(List.of(expectedCall),seen);assertEquals(List.of(new Touch("1a81388",17),new Touch("1a813a2",16)),self);var expectedRows=new ArrayList<Long>();for(int k=1;k<17;k++)expectedRows.add(P+k*40L);for(int k=18;k<33;k++)expectedRows.add(P+k*40L);assertEquals(expectedRows,rows);
        for(var e:data.entrySet())assertEquals(e.getValue(),m.m.data.get(e.getKey()),"row byte "+e.getKey());
        assertEquals(new NormalReturn(p,RIP,S+8,n),out);fullSuffix(m);assertEquals(I+0x1A813CBL,m.m.readQword(C));
        assertEquals(3,m.touches.stream().filter(t->t.equals(new Touch("W8",C))).count());assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("R8",C))).count());
    }

    @Test void actualRecursiveChildRetOrSavedNCorruptionRejectsBeforeSecondChild() {
        for(boolean corruptRip:new boolean[]{true,false}) {
            var m=new Observed();frame(m,0);words(m.m.data,P,row(0,1));for(int k=1;k<33;k++)words(m.m.data,P+k*40L,row(k,101-k));
            var n=n(700);var self=new ArrayList<Touch>();var port=new ArrayList<Long>();
            assertThrows(UnsupportedOperationException.class,()->DispatchRangeFullState296.execute(new Entry(I,S,input(100,33,P+1320),n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0x1A81247L,c.callSiteRva());port.add(c.callSiteRva());assertEquals(1,port.size());m.m.put(corruptRip?C:C+0x10,0xBAD);return c.volatileBits();}},(site,guard)->{if(site!=0x1A81210L)self.add(new Touch(Long.toHexString(site),guard));}));
            assertEquals(List.of(new Touch("1a81388",17)),self);assertEquals(List.of(0x1A81247L),port);assertEquals(new Touch("R8",C),m.touches.getLast());assertFalse(m.touches.contains(new Touch("R8",G+0x40)));assertFalse(m.touches.contains(new Touch("R8",S)));
            assertEquals(0xBAD,m.m.readQword(corruptRip?C:C+0x10));
        }
    }

    @Test void finiteBudgetAndOpaqueExceptionsRetainSourceWritesWithoutNewChildPush() {
        var m=new Observed();frame(m,0);var n=n(700);var in=input(100,33,P+1320);var stop=new IllegalArgumentException("finite self");var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);expected.put(G+0x28,(byte)TAG);qword(expected,G+0x20,0);
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->DispatchRangeFullState296.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->{assertEquals(0x1A81388L,site);assertEquals(17,guard);throw stop;})));assertEquals(expected,m.m.snapshot());assertFalse(m.touches.contains(new Touch("W8",C)));
        var deeper=new Observed();frame(deeper,0);var guards=new ArrayList<Touch>();
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->DispatchRangeFullState296.execute(new Entry(I,S,input(100,65,P+2600),n),deeper,noCalls(),(site,guard)->{guards.add(new Touch(Long.toHexString(site),guard));if(guards.size()==2)throw stop;})));
        assertEquals(List.of(new Touch("1a81388",33),new Touch("1a81388",17)),guards);assertEquals(I+0x1A8138DL,deeper.m.readQword(C));assertFalse(deeper.touches.contains(new Touch("W8",S-0xE0)));assertFalse(deeper.touches.contains(new Touch("R8",S)));
        var aborted=new Observed();frame(aborted,17);var error=new IllegalStateException("opaque denied");var seen=new ArrayList<Long>();
        assertSame(error,assertThrows(IllegalStateException.class,()->DispatchRangeFullState296.execute(new Entry(I,S,in,n),aborted,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){seen.add(c.callSiteRva());if(seen.size()==2)throw error;return post(300);}},(site,guard)->{throw new AssertionError("direct");})));
        assertEquals(List.of(0x1A81363L,0x1A81378L),seen);assertEquals(I+0x1A8137DL,aborted.m.readQword(C));assertEquals(new Touch("W8",C),aborted.touches.getLast());assertFalse(aborted.touches.contains(new Touch("R8",G+0x40)));
    }

    @Test void fullWidthOddCountSplitWrapsRawPointersWithoutIntegerNormalization() {
        long count=Long.MAX_VALUE,ceil=0x4000000000000000L,floor=0x3FFFFFFFFFFFFFFFL,end=0x7fff123456780000L;var m=new Observed();frame(m,Long.MAX_VALUE);var n=n(700);var in=input(0xE000000000000000L,count,end);var seen=new ArrayList<Call>();
        var out=DispatchRangeFullState296.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            int k=seen.size();seen.add(c);assertEquals(offered(n,floor,ceil,P,Long.MAX_VALUE,end),c.nonvolatileBits());
            if(k==0){assertEquals(0x1A81363L,c.callSiteRva());assertEquals(ceil,c.volatileBits().raxBits());assertEquals(P,c.volatileBits().rcxBits());assertEquals(P,c.volatileBits().rdxBits());assertEquals(ceil,c.volatileBits().r8Bits());}
            else if(k==1){assertEquals(0x1A81378L,c.callSiteRva());assertEquals(P,c.volatileBits().rcxBits());assertEquals(end,c.volatileBits().rdxBits());assertEquals(floor,c.volatileBits().r8Bits());}
            else{assertEquals(0x1A813C6L,c.callSiteRva());assertEquals(ceil,c.volatileBits().r9Bits());assertEquals(floor,m.m.readQword(G+0x20));}
            return c.volatileBits();
        }},(site,guard)->{throw new AssertionError("raw direct");});
        assertEquals(3,seen.size());assertEquals(n,out.nonvolatileBits());assertEquals(RIP,out.returnRipBits());assertEquals(S+8,out.callerRspBits());assertEquals(ceil,out.volatileBits().raxBits());
    }

    @Test void signedCapacityBoundaryChoosesRecursionWithoutRewritingNegativeCapacity() {
        for(long cap:new long[]{16,-1}) {
            var m=new Observed();frame(m,cap);for(int k=0;k<33;k++)words(m.m.data,P+k*40L,row(k,100-k));var n=n(700);var self=new ArrayList<Long>();var seen=new ArrayList<Call>();
            var out=DispatchRangeFullState296.execute(new Entry(I,S,input(100,33,P+1320),n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){seen.add(c);assertEquals(0x1A813C6L,c.callSiteRva());assertEquals(cap,c.nonvolatileBits().r13Bits());assertEquals(cap,m.m.readQword(G+0x30));return c.volatileBits();}},(site,guard)->{if(site!=0x1A81210L)self.add(site);});
            assertEquals(List.of(0x1A81388L,0x1A813A2L),self);assertEquals(1,seen.size());assertEquals(n,out.nonvolatileBits());assertEquals(RIP,out.returnRipBits());
        }
    }
}
