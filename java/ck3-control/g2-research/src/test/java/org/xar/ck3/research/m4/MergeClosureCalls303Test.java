package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.RotateFullState292Test.Observed;
import org.xar.ck3.research.m4.RotateFullState292Test.Touch;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner literals, frozen before reading new router/counter. Mature algorithms known.
 * Tests qualify exact port composition, not COPY semantics or native stack/flags.
 */
final class MergeClosureCalls303Test {
    static final long I=0x180000000L,S=0xB0000L,P=0x2000L,T=0x6000L,RIP=0x7fff12345678L;
    static VolatileBits regs(long first,long middle,long last,long left){var x=v(100,0xABC,first,middle);return new VolatileBits(x.raxBits(),first,middle,last,left,x.r10Bits(),x.r11Bits(),x.xmm0(),x.xmm1(),x.xmm2(),x.xmm3(),x.xmm4(),x.xmm5());}
    static void frame(Observed m,long entry,long right,long capacity,boolean ret){m.m.put(entry+0x28,right);m.m.put(entry+0x30,T);m.m.put(entry+0x38,capacity);m.m.put(entry+0x40,0x11223344556677E1L);if(ret)m.m.put(entry,RIP);}
    static void rows(Observed m){for(int id=1;id<=4;id++){long at=P+(id-1)*40L;m.m.put(at,0xAABBCCDD00000000L+id);m.m.put(at+8,0x1100000000000000L+id);m.m.put(at+16,0x2200000000000000L+id);m.m.put(at+24,0x3300000000000000L+id);m.m.put(at+32,0x4400000000000000L+id);}}
    static LoopBudget noLoop(){return(site,guard)->{throw new AssertionError("unexpected loop "+Long.toHexString(site));};}
    static LoopBudget finite(){var sites=new ArrayList<Long>();return(site,guard)->{sites.add(site);assertTrue(sites.size()<20);};}
    static GovernmentCrtBoundary185Api.Calls noUnknown(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unclosed invoke "+c);}@Override public NormalReturn tail(Tail t){throw new AssertionError("unclosed tail "+t);}};}

    @Test void constructorAndEveryForeignPortForwardOnceWithoutEligibilityMemoryWork() {
        var m=new Observed();var n=n(700);var v=regs(P,P+80,P+160,2);var marker=new NormalReturn(v,0x123,0x456,n);var seen=new ArrayList<Object>();
        var unknown=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){seen.add(c);return v;}@Override public NormalReturn tail(Tail t){seen.add(t);return marker;}@Override public long readGsQword58(){seen.add("GS");return Long.MIN_VALUE;}};
        var router=MergeClosureCalls303.bind(I,m,unknown,noLoop());assertTrue(seen.isEmpty());assertTrue(m.touches.isEmpty());
        for(var c:List.of(new Call(0x1A8335CL,TargetKind.DIRECT_RVA,0x1A81AB0L,S,v,n),new Call(0x1A8335DL,TargetKind.INDIRECT_ABSOLUTE,0x1A81AB0L,S,v,n),new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A82450L,S,v,n),new Call(0x1A82588L,TargetKind.DIRECT_RVA,0x4226860L,S,v,n))){int before=seen.size();assertSame(v,router.invoke(c));assertEquals(before+1,seen.size());assertSame(c,seen.getLast());}
        var e=new Entry(-1,S,v,n);
        for(var t:List.of(new Tail(0x1A833A1L,TargetKind.DIRECT_RVA,0x1A81AB0L,e),new Tail(0x1A833A2L,TargetKind.INDIRECT_ABSOLUTE,0x1A81AB0L,e),new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A82450L,e),new Tail(0x1A81B9BL,TargetKind.DIRECT_RVA,0x1A82450L,e),new Tail(0x1A81B9CL,TargetKind.INDIRECT_ABSOLUTE,0x1A82450L,e),new Tail(0x1A81B9CL,TargetKind.DIRECT_RVA,0x1A81AB0L,e),new Tail(0x1A8252FL,TargetKind.DIRECT_RVA,0x4226860L,e))){int before=seen.size();assertSame(marker,router.tail(t));assertEquals(before+1,seen.size());assertSame(t,seen.getLast());}
        int before=seen.size();assertEquals(Long.MIN_VALUE,router.readGsQword58());assertEquals(before+1,seen.size());assertEquals("GS",seen.getLast());assertTrue(m.touches.isEmpty());
    }

    @Test void exactNormalRetainsMatureSinglePushConventionAndOriginalReturnGuard() {
        var m=new Observed();m.m.put(S-8,I+0x1A83362L);var v=regs(P,P+40,P+40,7);var n=n(700);
        var router=MergeClosureCalls303.bind(I,m,noUnknown(),noLoop());var c=new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,S,v,n);
        assertEquals(v,router.invoke(c));assertEquals(List.of(new Touch("R8",S-8)),m.touches);assertTrue(m.m.writes.isEmpty());
        var bad=new Observed();bad.m.put(S-8,I+0x1A83363L);var snapshot=bad.m.snapshot();
        assertThrows(UnsupportedOperationException.class,()->MergeClosureCalls303.bind(I,bad,noUnknown(),noLoop()).invoke(c));
        assertEquals(snapshot,bad.m.snapshot());assertEquals(List.of(new Touch("R8",S-8)),bad.touches);
    }

    @Test void normalBridgePortRecursesThroughActual297Then302ToOnlyUnknownCopy() {
        long child=S-8;var m=new Observed();frame(m,child,2,2,false);m.m.put(child,I+0x1A83362L);rows(m);var n=n(700);var in=regs(P,P+80,P+160,2);var post=v(2000,0x123,0x456,0x789);var seen=new ArrayList<Tail>();
        var unknown=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected unknown normal");}@Override public NormalReturn tail(Tail t){
            assertEquals(0x1A8252FL,t.jumpSiteRva());assertEquals(0x4226860L,t.targetBits());assertEquals(child,t.entry().rspBits());assertEquals(I,t.entry().imageBaseBits());assertEquals(n,t.entry().nonvolatileBits());assertEquals(80,t.entry().volatileBits().r8Bits());assertEquals(3,m.m.readDword(P));assertEquals(4,m.m.readDword(P+40));seen.add(t);
            return new NormalReturn(post,m.readQword(child),child+8,t.entry().nonvolatileBits());
        }};
        var out=MergeClosureCalls303.bind(I,m,unknown,finite()).invoke(new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,S,in,n));
        assertSame(post,out);assertEquals(1,seen.size());assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("W8",child-8))).count());assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("R8",child))).count());
    }

    @Test void bridgeTailCarriesActualEntryImageAndReturnsOpaqueResultIdentityWithoutNormalGuard() {
        long actualImage=0xF000000000000123L;var m=new Observed();frame(m,S,2,2,false);rows(m);var n=n(700);var in=regs(P,P+80,P+160,2);var marker=new NormalReturn(v(3000,1,2,3),0xABC,0xDEF,n(900));
        var unknown=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected normal");}@Override public NormalReturn tail(Tail t){assertEquals(0x1A8252FL,t.jumpSiteRva());assertEquals(actualImage,t.entry().imageBaseBits());assertEquals(S,t.entry().rspBits());return marker;}};
        var out=MergeClosureCalls303.bind(I,m,unknown,finite()).tail(new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A81AB0L,new Entry(actualImage,S,in,n)));
        assertSame(marker,out);assertFalse(m.touches.contains(new Touch("R8",S)));
    }

    @Test void scratchGeneralRecursionReturnsThroughAllThreeKnownPortsWithoutAnyUnknownFallback() {
        var m=new Observed();frame(m,S,0,-1,true);var n=n(700);var in=regs(P,P,P,0);
        var out=MergeClosureCalls303.bind(I,m,noUnknown(),noLoop()).tail(new Tail(0x1A81B9CL,TargetKind.DIRECT_RVA,0x1A82450L,new Entry(I,S,in,n)));
        assertEquals(RIP,out.returnRipBits());assertEquals(S+8,out.callerRspBits());assertEquals(n,out.nonvolatileBits());assertEquals(S-0x18,out.volatileBits().r11Bits());
        assertEquals(I+0x1A83362L,m.m.readQword(S-0xF0L));assertEquals(2,m.touches.stream().filter(t->t.equals(new Touch("W8",S-0xF0L))).count());
        assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("R8",S))).count());
    }

    @Test void matureNormalRipSpAndNonvolatileGuardsStillRejectAfterActualMemoryEffects() {
        for(int bad=0;bad<3;bad++) {
            int which=bad;long pre=S+0x1000L*bad,child=pre-8;var m=new Observed();frame(m,child,2,2,false);m.m.put(child,I+0x1A83362L);rows(m);var n=n(700);var in=regs(P,P+80,P+160,2);
            var unknown=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unknown normal");}@Override public NormalReturn tail(Tail t){
                assertEquals(0x1A8252FL,t.jumpSiteRva());m.writeQword(P,0xBEEFL);
                return new NormalReturn(in,I+0x1A83362L+(which==0?1:0),pre+(which==1?8:0),which==2?n(900):n);
            }};
            var router=MergeClosureCalls303.bind(I,m,unknown,finite());
            assertThrows(UnsupportedOperationException.class,()->router.invoke(new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,pre,in,n)));
            assertEquals(0xBEEFL,m.m.readQword(P));assertEquals(new Touch("W8",P),m.touches.getLast());
        }
    }
}
