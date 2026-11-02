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

/** New composition literals only; mature byte-storage/trace fixture reused, no old subject tests run. */
final class BridgeFullState293Test {
    static final long I=0x180000000L,S=0x100000L,B=S-0x68L,P=0x2000L,T=0x5000L,RIP=0x7fff12345678L;
    static VolatileBits regs(long seed,long a,long c,long d,long e,long f) {
        return RotateFullState292Test.regs(seed,a,c,d,e,f);
    }
    static VolatileBits bits(VolatileBits v,long a,long c,long d,long e,long f) {
        return new VolatileBits(a,c,d,e,f,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static NonvolatileBits active(NonvolatileBits n,long bx,long bp,long si,long r12,long r13) {
        return new NonvolatileBits(bx,bp,si,n.rdiBits(),r12,r13,n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    static void frame(Observed m,long right,long scratch,long cap,long firstCut,long secondCut,long firstCount,long secondCount,int tag) {
        m.m.put(S,RIP);m.m.put(S+0x28,right);m.m.put(S+0x30,scratch);m.m.put(S+0x38,cap);
        m.m.put(S+0x40,0x1122334455667700L|(tag&255));m.m.put(S+0x48,firstCut);m.m.put(S+0x50,secondCut);
        m.m.put(S+0x58,firstCount);m.m.put(S+0x60,secondCount);
    }
    static void words(Map<Long,Byte> map,long at,long...data) {
        for(int i=0;i<data.length;i++)qword(map,at+8L*i,data[i]);
    }
    static void bridgePrologue(Map<Long,Byte> map,NonvolatileBits n,long first,long last,long leftRemainder,long secondCount,long scratch,long cap) {
        qword(map,S+0x18,last);qword(map,S+8,first);
        qword(map,S-8,n.rbxBits());qword(map,S-0x10,n.rbpBits());qword(map,S-0x18,n.rsiBits());
        qword(map,S-0x20,n.r12Bits());qword(map,S-0x28,n.r13Bits());
        qword(map,B+0x30,cap);qword(map,B+0x28,scratch);qword(map,S+0x20,leftRemainder);qword(map,B+0x20,secondCount);
    }
    static final class Reject extends Gate47Fixture273.Calls {
        @Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected call "+c);}
    }

    @Test void complete231To292To291UsesSinglePushAndFreshTailArgumentsAllState() {
        var m=new Observed();frame(m,1,T,1,P,P+80,0,1,0x80);words(m.m.data,P,1,2,3,4,5);
        var n=n(700);var in=regs(100,-1,P,P+40,P+80,1);
        var expected=new HashMap<>(m.m.snapshot());bridgePrologue(expected,n,P,P+80,1,1,T,1);
        qword(expected,S-0x70,I+0x1A83362L);qword(expected,S-0x58,n.r14Bits());qword(expected,S-0x78,n.r15Bits());
        qword(expected,S-0x68,n.rbxBits());qword(expected,S-0x60,n.rdiBits());qword(expected,S-0xA0,I+0xF0F1EEL);
        words(expected,T,1,2,3,4,5);expected.put(B+0x38,(byte)0x80);
        long newRip=0x777788889999L;
        qword(expected,S-8,801);qword(expected,S-0x10,802);qword(expected,S-0x18,803);qword(expected,S-0x20,804);qword(expected,S-0x28,805);
        qword(expected,S+0x18,0x7777);qword(expected,S+0x20,7);qword(expected,S+0x28,5);qword(expected,S+0x50,0x8888);qword(expected,S,newRip);
        var p1=regs(300,11,12,13,14,15);var p2=regs(400,21,22,23,24,25);var p3=regs(500,31,32,33,34,35);var p4=regs(600,41,42,43,44,45);
        var copy1N=new NonvolatileBits(n.rbxBits(),1,n.rsiBits(),T+40,T,1,40,P,n.xmm6());
        var copy2N=new NonvolatileBits(P+40,1,n.rsiBits(),40,T,1,40,P,n.xmm6());
        var expectedFirstV=new VolatileBits(T+40,P,P+40,40,1,in.r10Bits(),in.r11Bits(),new Bits128(5,0),new Bits128(3,4),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
        var expectedCalls=List.of(new Call(0xF0F1D0L,TargetKind.DIRECT_RVA,0x4226860L,S-0x98,expectedFirstV,copy1N),
                new Call(0xF0F1E9L,TargetKind.DIRECT_RVA,0x4226860L,S-0x98,bits(p1,11,P+40,T,40,15),copy2N),
                new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,B,bits(p2,P+40,P,P,P+40,0),active(n,128,1,P+40,T,1)));
        var expectedTail=new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A81AB0L,
                new Entry(I,S,bits(p3,31,P+40,0x8888,0x7777,7),active(n,801,802,803,804,805)));
        var seen=new ArrayList<Call>();var budgets=new ArrayList<Long>();NormalReturn[] returned={null};
        var result=BridgeFullState293.execute(new Entry(I,S,in,n),m,new GovernmentCrtBoundary185Api.Calls(){
            @Override public VolatileBits invoke(Call c) {
                int k=seen.size();assertEquals(expectedCalls.get(k),c);seen.add(c);
                assertEquals(I+c.callSiteRva()+5,m.m.readQword(c.rspBits()-8));
                if(k==0)return p1;if(k==1)return p2;
                m.m.put(S-8,801);m.m.put(S-0x10,802);m.m.put(S-0x18,803);m.m.put(S-0x20,804);m.m.put(S-0x28,805);
                m.m.put(S+0x18,0x7777);m.m.put(S+0x20,7);m.m.put(S+0x28,6);m.m.put(S+0x50,0x8888);m.m.put(S,newRip);
                m.m.data.put(S+0x40,(byte)0xFF);return p3;
            }
            @Override public NormalReturn tail(Tail t) {
                assertEquals(expectedTail,t);assertFalse(m.touches.contains(new Touch("R8",S)));
                assertEquals(0x1122334455667780L,m.m.readQword(S+0x40));
                returned[0]=new NormalReturn(p4,m.readQword(t.entry().rspBits()),t.entry().rspBits()+8,t.entry().nonvolatileBits());return returned[0];
            }
            @Override public long readGsQword58(){throw new AssertionError("unused GS");}
        },(site,guard)->{assertEquals(0xF0ABA0L,site);budgets.add(guard);});
        assertEquals(expectedCalls,seen);assertEquals(List.of(P),budgets);assertSame(returned[0],result);
        assertEquals(new NormalReturn(p4,newRip,S+8,expectedTail.entry().nonvolatileBits()),result);
        assertEquals(expected,m.m.snapshot());
        assertEquals(2,m.touches.stream().filter(x->x.equals(new Touch("W8",S-0x70))).count());
        assertEquals(3,m.touches.stream().filter(x->x.equals(new Touch("W8",S-0xA0))).count());
        assertEquals(List.of(new Touch("W1",S+0x40),new Touch("W8",S+0x28),new Touch("R8",S-0x28),new Touch("R8",S-0x20),
                new Touch("R8",S-0x18),new Touch("R8",S-0x10),new Touch("R8",S-8),new Touch("R8",S)),m.touches.subList(m.touches.size()-8,m.touches.size()));
    }
    @Test void zeroRemainderStillCallsActual292AndMergeAndForwardsExactTailReturn() {
        var m=new Observed();frame(m,1,T,7,P+40,P+40,1,0,0xFF);
        var n=n(700);var in=regs(100,-1,P,P+40,P+80,1);var post=regs(900,500,501,502,503,504);
        var expected=new HashMap<>(m.m.snapshot());bridgePrologue(expected,n,P,P+80,0,0,T,7);
        qword(expected,S-0x58,n.r14Bits());qword(expected,S-0x78,n.r15Bits());qword(expected,S-0x70,I+0x1A83362L);expected.put(B+0x38,(byte)0xFF);
        var expectedCall=new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,B,
                bits(in,P+40,P,P+40,P+40,1),active(n,255,0,P+40,T,7));
        var expectedTail=new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A81AB0L,new Entry(I,S,bits(post,500,P+40,P+40,P+80,0),n));
        var calls=new ArrayList<Call>();NormalReturn[] forwarded={null};
        var out=BridgeFullState293.execute(new Entry(I,S,in,n),m,new GovernmentCrtBoundary185Api.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(expectedCall,c);calls.add(c);assertEquals(I+0x1A83362L,m.m.readQword(B-8));return post;}
            @Override public NormalReturn tail(Tail t){assertEquals(expectedTail,t);assertFalse(m.touches.contains(new Touch("R8",S)));forwarded[0]=new NormalReturn(post,m.readQword(S),S+8,n);return forwarded[0];}
            @Override public long readGsQword58(){throw new AssertionError("unused GS");}
        },(site,guard)->{throw new AssertionError("zero child no rowloop");});
        assertEquals(List.of(expectedCall),calls);assertSame(forwarded[0],out);assertEquals(expected,m.m.snapshot());
        assertEquals(2,m.touches.stream().filter(x->x.equals(new Touch("W8",S-0x70))).count());
        assertEquals(0,m.touches.stream().filter(x->x.equals(new Touch("W8",S-0xA0))).count());
    }

    @Test void actualChildReturnAliasRejectsAfterItsOwnCallsWithoutMergeOrTail() {
        var m=new Observed();frame(m,1,S-0x70,1,P,P+80,0,1,0x80);words(m.m.data,P,0x123,2,3,4,5);
        var seen=new ArrayList<Long>();
        assertThrows(UnsupportedOperationException.class,()->BridgeFullState293.execute(new Entry(I,S,regs(100,-1,P,P+40,P+80,1),n(700)),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(0x4226860L,c.targetBits());seen.add(c.callSiteRva());return c.volatileBits();}
        },(site,guard)->{}));
        assertEquals(List.of(0xF0F1D0L,0xF0F1E9L),seen);assertEquals(0x123,m.m.readQword(S-0x70));
        assertEquals(new Touch("R8",S-0x70),m.touches.getLast());
        assertFalse(m.touches.contains(new Touch("R1",S+0x40)));assertFalse(m.touches.contains(new Touch("R8",S)));
    }

    @Test void correctChildRipWithChangedSavedNonvolatileIsRejectedWithoutFakeRestore() {
        var m=new Observed();frame(m,1,T,1,P,P+80,0,1,0x80);words(m.m.data,P,1,2,3,4,5);
        var seen=new ArrayList<Long>();
        assertThrows(UnsupportedOperationException.class,()->BridgeFullState293.execute(new Entry(I,S,regs(100,-1,P,P+40,P+80,1),n(700)),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(0x4226860L,c.targetBits());seen.add(c.callSiteRva());if(seen.size()==1)m.m.put(S-0x68,0xBAD);return c.volatileBits();}
        },(site,guard)->{}));
        assertEquals(List.of(0xF0F1D0L,0xF0F1E9L),seen);assertEquals(I+0x1A83327L,m.m.readQword(S-0x70));assertEquals(0xBAD,m.m.readQword(S-0x68));
        assertEquals(new Touch("R8",S-0x70),m.touches.getLast());assertFalse(m.touches.contains(new Touch("R1",S+0x40)));
    }

    @Test void opaqueMergeAndTailFailuresPreserveRealPushAndUnwindBoundaries() {
        var n=n(700);var in=regs(100,-1,P,P+40,P+80,1);var error=new IllegalStateException("actual port refusal");
        var callFailure=new Observed();frame(callFailure,1,T,7,P+40,P+40,1,0,0xFF);
        assertSame(error,assertThrows(IllegalStateException.class,()->BridgeFullState293.execute(new Entry(I,S,in,n),callFailure,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(0x1A8335DL,c.callSiteRva());throw error;}
        },(site,guard)->{throw new AssertionError("zero row");})));
        assertEquals(I+0x1A83362L,callFailure.m.readQword(S-0x70));assertEquals(new Touch("W8",S-0x70),callFailure.touches.getLast());
        assertFalse(callFailure.touches.contains(new Touch("R8",S-0x28)));assertFalse(callFailure.touches.contains(new Touch("R8",S)));
        var tailFailure=new Observed();frame(tailFailure,1,T,7,P+40,P+40,1,0,0xFF);var tails=new ArrayList<Tail>();
        assertSame(error,assertThrows(IllegalStateException.class,()->BridgeFullState293.execute(new Entry(I,S,in,n),tailFailure,new GovernmentCrtBoundary185Api.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(0x1A8335DL,c.callSiteRva());return c.volatileBits();}
            @Override public NormalReturn tail(Tail t){assertEquals(S,t.entry().rspBits());assertEquals(n,t.entry().nonvolatileBits());tails.add(t);throw error;}
            @Override public long readGsQword58(){throw new AssertionError("unused GS");}
        },(site,guard)->{throw new AssertionError("zero row");})));
        assertEquals(1,tails.size());assertEquals(new Touch("R8",S-8),tailFailure.touches.getLast());assertFalse(tailFailure.touches.contains(new Touch("R8",S)));
    }

    @Test void missingLaterStackArgumentStopsAtActualReadWithoutCallsOrLocalWrites() {
        var m=new Observed();frame(m,1,T,7,P+40,P+40,1,0,0xFF);
        for(int i=0;i<8;i++)m.m.data.remove(S+0x48+i);
        assertThrows(UnsupportedOperationException.class,()->BridgeFullState293.execute(new Entry(I,S,regs(100,-1,P,P+40,P+80,1),n(700)),m,new Reject(),(site,guard)->{throw new AssertionError("no child yet");}));
        assertEquals(7,m.m.writes.size());
        assertEquals(List.of(new Touch("W8",S+0x18),new Touch("W8",S+8),new Touch("W8",S-8),new Touch("W8",S-0x10),new Touch("W8",S-0x18),
                new Touch("W8",S-0x20),new Touch("W8",S-0x28),new Touch("R8",S+0x38),new Touch("R8",S+0x58),new Touch("R8",S+0x30),new Touch("R8",S+0x60),new Touch("R8",S+0x50),new Touch("R8",S+0x48)),m.touches);
        assertFalse(m.m.data.containsKey(S+0x20));assertFalse(m.touches.contains(new Touch("R8",S)));
    }
}
