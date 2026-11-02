package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.HashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.RotateFullState292Test.Observed;
import org.xar.ck3.research.m4.RotateFullState292Test.Touch;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner source-literal oracle, frozen before inspecting the new candidate or counter response.
 * Mature APIs/implementations were known; this is candidate-blind, not whole-algorithm-blind.
 * Only the internal ten-instruction normal block is qualified, not complete776 admission.
 */
final class ScratchGeneralTail301Test {
    static final long I=0x180000000L,G=0x90000L,E=G+0x68L,P=0x2000L,T=0x5000L,RIP=0x7fff11223344L;
    static final long SAVED_BX=0xABCD1234567890EFL,SAVED_DI=0xFEDCBA9876543210L,TAG=0x11223344556677E1L;
    static VolatileBits input(long capacity,long right,long last,long left,long middle) {
        var s=v(100,0xDEAD,capacity,right);
        return new VolatileBits(s.raxBits(),capacity,right,last,left,middle,s.r11Bits(),
                s.xmm0(),s.xmm1(),s.xmm2(),s.xmm3(),s.xmm4(),s.xmm5());
    }
    static NonvolatileBits homes(NonvolatileBits n,long bx,long di) {
        return new NonvolatileBits(bx,n.rbpBits(),n.rsiBits(),di,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    static VolatileBits expected(VolatileBits v,NonvolatileBits n,int tag) {
        return new VolatileBits(tag,n.rbxBits(),v.r10Bits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static List<Touch> trace(long g) {
        return List.of(new Touch("R1",g+0xA8L),new Touch("W1",g+0xA8L),new Touch("W8",g+0xA0L),
                new Touch("W8",g+0x90L),new Touch("R8",g+0x78L),new Touch("R8",g+0x60L));
    }
    static Observed frame(long g) {
        var m=new Observed();m.m.put(g+0xA8L,TAG);m.m.put(g+0xA0L,0x1111);m.m.put(g+0x90L,0x2222);
        m.m.put(g+0x78L,SAVED_BX);m.m.put(g+0x60L,SAVED_DI);return m;
    }
    static GovernmentCrtBoundary185Api.Calls unexpected() {
        return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected "+c);}};
    }
    static class Delegating implements GovernmentCrtBoundary185Api.Memory {
        final Observed base;
        Delegating(Observed base){this.base=base;}
        @Override public int readUnsignedByte(long p){return base.readUnsignedByte(p);}
        @Override public int readDword(long p){return base.readDword(p);}
        @Override public long readQword(long p){return base.readQword(p);}
        @Override public Bits128 read128(long p){return base.read128(p);}
        @Override public void writeByte(long p,int x){base.writeByte(p,x);}
        @Override public void writeDword(long p,int x){base.writeDword(p,x);}
        @Override public void writeQword(long p,long x){base.writeQword(p,x);}
        @Override public void write128(long p,Bits128 x){base.write128(p,x);}
        @Override public int lockedXaddDword(long p,int x){return base.lockedXaddDword(p,x);}
    }

    @Test void exactTransferPreservesAllBitsAndByteWidthWithoutReadingReturn() {
        var m=frame(G);var n=rbx(n(700),P);var v=input(0xAABBCCDD11223344L,0x9988776655443322L,P+80,2,P+40);
        var map=new HashMap<>(m.m.snapshot());qword(map,G+0xA0L,v.rcxBits());qword(map,G+0x90L,v.rdxBits());
        var out=ScratchGeneralTail301.transfer(new Entry(I,G,v,n),m);
        assertEquals(new Tail(0x1A82753L,TargetKind.DIRECT_RVA,0x1A82F00L,
                new Entry(I,E,expected(v,n,0xE1),homes(n,SAVED_BX,SAVED_DI))),out);
        assertEquals(trace(G),m.touches);assertEquals(map,m.m.snapshot());
        assertFalse(m.m.data.containsKey(E));assertEquals(TAG,m.m.readQword(G+0xA8L));
    }

    @Test void highBitsAndWrappedStackArithmeticAreRawMachineValues() {
        long g=Long.MAX_VALUE-0x50L,image=0xF000000000000123L;
        var m=frame(g);var n=rbx(n(900),0xF123456789ABCDEFL);
        var v=input(Long.MIN_VALUE+17,Long.MAX_VALUE-3,0xE123456789ABCDEFL,-11,0xD123456789ABCDEFL);
        var out=ScratchGeneralTail301.transfer(new Entry(image,g,v,n),m);
        assertEquals(new Tail(0x1A82753L,TargetKind.DIRECT_RVA,0x1A82F00L,
                new Entry(image,g+0x68L,expected(v,n,0xE1),homes(n,SAVED_BX,SAVED_DI))),out);
        assertEquals(trace(g),m.touches);assertEquals(v.rcxBits(),m.m.readQword(g+0xA0L));
        assertEquals(v.rdxBits(),m.m.readQword(g+0x90L));
    }

    @Test void savedHomesAreReadFreshAfterAllEarlierStores() {
        var m=frame(G);var n=rbx(n(700),P);var v=input(-1,0,P,0,P);
        var hooked=new Delegating(m){@Override public void writeQword(long p,long x){
            super.writeQword(p,x);if(p==G+0x90L){base.m.put(G+0x78L,0x12345678);base.m.put(G+0x60L,0x87654321L);}
        }};
        var out=ScratchGeneralTail301.transfer(new Entry(I,G,v,n),hooked);
        assertEquals(homes(n,0x12345678,0x87654321L),out.entry().nonvolatileBits());assertEquals(trace(G),m.touches);
    }

    @Test void missingFirstByteCannotProduceAnyStoreOrSyntheticTail() {
        var m=new Observed();var n=n(700);var v=input(-1,0,P,0,P);
        assertThrows(UnsupportedOperationException.class,()->ScratchGeneralTail301.transfer(new Entry(I,G,v,n),m));
        assertEquals(List.of(new Touch("R1",G+0xA8L)),m.touches);assertTrue(m.m.snapshot().isEmpty());
    }

    @Test void missingSavedRbxRetainsThreeStorePrefixAndDoesNotReadRdi() {
        var m=frame(G);for(int i=0;i<8;i++)m.m.data.remove(G+0x78L+i);
        var v=input(Long.MIN_VALUE,Long.MAX_VALUE,P,0,P);var map=new HashMap<>(m.m.snapshot());
        qword(map,G+0xA0L,v.rcxBits());qword(map,G+0x90L,v.rdxBits());
        assertThrows(UnsupportedOperationException.class,()->ScratchGeneralTail301.transfer(new Entry(I,G,v,n(700)),m));
        assertEquals(trace(G).subList(0,5),m.touches);assertEquals(map,m.m.snapshot());
    }

    @Test void capacityStoreExceptionRetainsBytePrefixAndExactExceptionIdentity() {
        var m=frame(G);var marker=new IllegalStateException("owned capacity port stop");var map=m.m.snapshot();
        var stopped=new Delegating(m){@Override public void writeQword(long p,long x){
            if(p==G+0xA0L){base.touches.add(new Touch("W8",p));throw marker;}super.writeQword(p,x);
        }};
        assertSame(marker,assertThrows(IllegalStateException.class,()->ScratchGeneralTail301.transfer(new Entry(I,G,input(-1,0,P,0,P),n(700)),stopped)));
        assertEquals(trace(G).subList(0,3),m.touches);assertEquals(map,m.m.snapshot());assertEquals(1,m.m.writes.size());
    }

    @Test void executeEntersRealGeneralAndReturnsThroughMatureZeroCountChain() {
        var m=frame(G);m.m.put(G+0x98L,T);m.m.put(E,RIP);var n=rbx(n(700),P);var v=input(-1,0,P,0,P);
        LoopBudget budget=(site,guard)->{throw new AssertionError("zero-count loop "+Long.toHexString(site));};
        var calls=BridgeMergeCalls298.bind(I,m,unexpected(),budget);
        var out=ScratchGeneralTail301.execute(new Entry(I,G,v,n),m,calls,budget);
        assertEquals(RIP,out.returnRipBits());assertEquals(E+8,out.callerRspBits());assertEquals(homes(n,SAVED_BX,SAVED_DI),out.nonvolatileBits());
        assertEquals(E-0x18L,out.volatileBits().r11Bits());assertEquals(v.xmm0(),out.volatileBits().xmm0());
        assertEquals(v.xmm1(),out.volatileBits().xmm1());assertEquals(v.xmm2(),out.volatileBits().xmm2());
        assertEquals(v.xmm3(),out.volatileBits().xmm3());assertEquals(v.xmm4(),out.volatileBits().xmm4());assertEquals(v.xmm5(),out.volatileBits().xmm5());
        assertEquals(trace(G),m.touches.subList(0,6));
        assertEquals(List.of(new Touch("W8",E+8),new Touch("W8",E+0x10),new Touch("W8",E+0x18),new Touch("W8",E+0x20)),m.touches.subList(6,10));
        assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("W8",E-8))).count());assertEquals(n.r12Bits(),m.m.readQword(E-8));
        assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("R8",E))).count());
        assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("W1",G+0xA8))).count());
    }

    @Test void executePropagatesActualUnknownPortWithoutReadingOuterReturn() {
        var m=frame(G);m.m.put(G+0x98L,T);m.m.put(E,RIP);var n=rbx(n(700),P);var marker=new IllegalStateException("actual merge port");
        var calls=new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){
            assertEquals(0x1A8335DL,c.callSiteRva());assertEquals(0x1A81AB0L,c.targetBits());throw marker;
        }};
        assertSame(marker,assertThrows(IllegalStateException.class,()->ScratchGeneralTail301.execute(new Entry(I,G,input(-1,0,P,0,P),n),m,calls,(site,guard)->{throw new AssertionError("zero loop");})));
        assertEquals(trace(G),m.touches.subList(0,6));assertFalse(m.touches.contains(new Touch("R8",E)));
        assertEquals(new Touch("W8",E-0xF0L),m.touches.getLast());
    }
}
