package org.xar.ck3.research.m5;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m5.GovernmentInitialStack213Test.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.StackProbe78FullState290;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New whole Initial/Probe/Wrapper/Retry/Allocate DATA integration; old213 fixtures binary reused. */
final class GovernmentInitialAllocation214Test {
    static final long H=0x600000L,HEAP=0x700000L,TARGET=0x123456789abL;
    static final VolatileBits HEAP_OUT=scalar(v(0x9000,0x9999),H,0x9999);
    static final VolatileBits REDUCE_OUT=v(0xa000,0xaaaa),FREE_OUT=v(0xb000,0xbbbb);
    record Step(long site,long value) { }

    @Test void wholeInitialExecutesRealAllocationChainAndKeepsEveryFrameWriteAndActualJoin() {
        Ram m=seeded(2048,false,0);m.seed(q(I+0x5c5de30L,HEAP));m.seed(q(I+0x43da768L,TARGET));
        var before=new HashMap<>(m.data);var steps=new ArrayList<Step>();var outerSeen=new ArrayList<OpaqueCall>();
        var lowerSeen=new ArrayList<GovernmentCrtBoundary185Api.Call>();int[] gs10={0};
        var nAtHeap=new NonvolatileBits(8192,BP,2048,G,N.r12Bits(),0,A,A+16384,X6);
        var heapCall=new GovernmentCrtBoundary185Api.Call(0x424fddeL,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,TARGET,F-0x90,
                new VolatileBits(1,HEAP,0,8192,IN.r9Bits(),IN.r10Bits(),IN.r11Bits(),new Bits128(I+0x9d09e0L,0),new Bits128(PAT,0),IN.xmm2(),IN.xmm3(),IN.xmm4(),IN.xmm5()),nAtHeap);
        var lower=new GovernmentCrtBoundary185Api.Calls(){
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call c){assertEquals(heapCall,c);lowerSeen.add(c);assertEquals(I+0x424fde4L,m.readQword(F-0x98));return HEAP_OUT;}
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail t){throw new AssertionError("no allocation tail port");}
            @Override public long readGsQword58(){throw new AssertionError("allocation has no GS58");}
        };
        var nAtOuter=new NonvolatileBits(1024,BP,2048,G,N.r12Bits(),0,A,A+16384,X6);
        var reduce=new OpaqueCall(0x30a30a4L,0x30abbb0L,F,
                new VolatileBits(H,A,A+16384,2048,H,HEAP_OUT.r10Bits(),HEAP_OUT.r11Bits(),HEAP_OUT.xmm0(),HEAP_OUT.xmm1(),HEAP_OUT.xmm2(),HEAP_OUT.xmm3(),HEAP_OUT.xmm4(),HEAP_OUT.xmm5()),nAtOuter);
        var free=new OpaqueCall(0x30a30beL,0x40ec530L,F,scalar(REDUCE_OUT,REDUCE_OUT.raxBits(),H),nAtOuter);
        var outer=new GovernmentInitialFrame162Api.Calls(){
            @Override public VolatileBits invoke(OpaqueCall c){assertEquals(outerSeen.isEmpty()?reduce:free,c);assertTrue(outerSeen.size()<2);outerSeen.add(c);return outerSeen.size()==1?REDUCE_OUT:FREE_OUT;}
            @Override public long readGsQword58(){throw new AssertionError("diagnostic absent");}
        };
        var actual=GovernmentInitialAllocation214.execute(entry(),m,outer,(site,capacity)->{assertEquals(0x30a3040L,site);assertEquals(1024,capacity);steps.add(new Step(site,capacity));},
                ()->{gs10[0]++;return 0;},(site,page)->{throw new AssertionError("no page probe");},lower,
                (site,size)->{assertEquals(0x4223baeL,site);assertEquals(8192,size);assertEquals(21,m.writes.size());steps.add(new Step(site,size));});
        assertEquals(List.of(new Step(0x30a3040,1024),new Step(0x4223bae,8192)),steps);assertEquals(1,gs10[0]);
        assertEquals(List.of(heapCall),lowerSeen);assertEquals(List.of(reduce,free),outerSeen);
        assertEquals(new GovernmentInitialFrame162Api.Join(0x30a3162L,I,F,scalar(FREE_OUT,0,FREE_OUT.rcxBits()),new NonvolatileBits(1024,BP,2048,G,0x158,0,A,1,X6)),actual);
        var writes=new ArrayList<>(commonAfterProbe(false,9));
        writes.add(q(F-8,I+0x30a3054L));writes.add(q(F-0x38,I+0x42242d5L));writes.add(q(F-0x40,1024));
        writes.add(q(F-0x68,I+0x4223bb3L));writes.add(q(F-0x70,8192));writes.add(q(F-0x98,I+0x424fde4L));
        writes.add(q(BP+0x1d0,H));writes.add(q(BP+0x1d8,1024));writes.add(q(F+0x28,BP+0xe0));writes.add(q(F+0x20,1024));
        assertEquals(28,writes.size());assertImage(before,m,writes);
    }

    @Test void innerAllocationBudgetRejectsBeforeItsPushAndAddedNullPortsRejectBeforeEffects() {
        var noOuter=new GovernmentInitialFrame162Api.Calls(){
            @Override public VolatileBits invoke(OpaqueCall c){throw new AssertionError("no outer before allocation completes");}
            @Override public long readGsQword58(){throw new AssertionError("no GS58");}
        };
        var noLower=new GovernmentCrtBoundary185Api.Calls(){
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call c){throw new AssertionError("no actual allocation call after rejected budget");}
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail t){throw new AssertionError("no tail");}
            @Override public long readGsQword58(){throw new AssertionError("no allocation GS58");}
        };
        Ram m=seeded(2048,false,0);var before=new HashMap<>(m.data);var steps=new ArrayList<Step>();var stop=new UnsupportedOperationException("finite allocation work");
        assertSame(stop,assertThrows(UnsupportedOperationException.class,()->GovernmentInitialAllocation214.execute(entry(),m,noOuter,
                (site,capacity)->{assertEquals(0x30a3040L,site);assertEquals(1024,capacity);steps.add(new Step(site,capacity));},()->0,
                (site,page)->{throw new AssertionError("no probe page");},noLower,(site,size)->{assertEquals(0x4223baeL,site);assertEquals(8192,size);steps.add(new Step(site,size));throw stop;})));
        assertEquals(List.of(new Step(0x30a3040,1024),new Step(0x4223bae,8192)),steps);
        var writes=new ArrayList<>(commonAfterProbe(false,9));writes.add(q(F-8,I+0x30a3054L));writes.add(q(F-0x38,I+0x42242d5L));writes.add(q(F-0x40,1024));assertEquals(21,writes.size());assertImage(before,m,writes);
        Ram untouched=new Ram();StackProbe78FullState290.Gs10 noGs=()->{throw new AssertionError("no GS before null rejection");};
        GovernmentInitialFrame162Api.LoopBudget noInitial=(site,capacity)->{throw new AssertionError("no initial attempt before null rejection");};
        GovernmentCrtBoundary185Api.LoopBudget noBudget=(site,size)->{throw new AssertionError("no budget before null rejection");};
        assertThrows(NullPointerException.class,()->GovernmentInitialAllocation214.execute(entry(),untouched,noOuter,noInitial,noGs,noBudget,null,noBudget));
        assertThrows(NullPointerException.class,()->GovernmentInitialAllocation214.execute(entry(),untouched,noOuter,noInitial,noGs,noBudget,noLower,null));
        assertTrue(untouched.data.isEmpty());assertTrue(untouched.writes.isEmpty());
    }
}
