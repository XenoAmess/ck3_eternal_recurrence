package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Gate47Fixture273.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner source literals; reviewed production, no Native or whole-domain equivalence claim. */
final class RotateFullState292Test {
    static final long I=0x180000000L,S=0x90000L,RIP=0x7fff00112233L,P=0x2000L,T=0x5000L;
    record Touch(String op,long address) { }
    static final class Observed implements GovernmentCrtBoundary185Api.Memory {
        final Gate47Fixture273.Memory m=new Gate47Fixture273.Memory();
        final List<Touch> touches=new ArrayList<>();
        @Override public int readUnsignedByte(long p){touches.add(new Touch("R1",p));return m.readUnsignedByte(p);}
        @Override public int readDword(long p){touches.add(new Touch("R4",p));return m.readDword(p);}
        @Override public long readQword(long p){touches.add(new Touch("R8",p));return m.readQword(p);}
        @Override public Bits128 read128(long p){touches.add(new Touch("R16",p));return m.read128(p);}
        @Override public void writeByte(long p,int x){touches.add(new Touch("W1",p));m.writeByte(p,x);}
        @Override public void writeDword(long p,int x){touches.add(new Touch("W4",p));m.writeDword(p,x);}
        @Override public void writeQword(long p,long x){touches.add(new Touch("W8",p));m.writeQword(p,x);}
        @Override public void write128(long p,Bits128 x){touches.add(new Touch("W16",p));m.write128(p,x);}
        @Override public int lockedXaddDword(long p,int x){throw new AssertionError("unused atomic");}
    }
    static VolatileBits regs(long seed,long rax,long first,long middle,long last,long left) {
        var v=v(seed,rax,first,middle);
        return new VolatileBits(rax,first,middle,last,left,v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static VolatileBits bits(VolatileBits v,long a,long c,long d,long e,long f,
            Bits128 x0,Bits128 x1,Bits128 x2,Bits128 x3,Bits128 x4) {
        return new VolatileBits(a,c,d,e,f,v.r10Bits(),v.r11Bits(),x0,x1,x2,x3,x4,v.xmm5());
    }
    static NonvolatileBits nv(NonvolatileBits n,long bx,long di,long r14,long r15) {
        return new NonvolatileBits(bx,n.rbpBits(),n.rsiBits(),di,n.r12Bits(),n.r13Bits(),r14,r15,n.xmm6());
    }
    static void frame(Observed m,long right,long scratch,long capacity) {
        m.m.put(S,RIP);m.m.put(S+0x28L,right);m.m.put(S+0x30L,scratch);m.m.put(S+0x38L,capacity);
    }
    static void words(Map<Long,Byte> m,long at,long...values) {
        for(int i=0;i<values.length;i++)qword(m,at+8L*i,values[i]);
    }
    static void initialWords(Observed m,long at,long...values){words(m.m.data,at,values);}
    static void prologue(Map<Long,Byte> expected,NonvolatileBits n,boolean main) {
        qword(expected,S+0x18L,n.r14Bits());qword(expected,S-8L,n.r15Bits());
        if(main){qword(expected,S+8L,n.rbxBits());qword(expected,S+0x10L,n.rdiBits());}
    }
    static GovernmentCrtBoundary185Api.Calls noCalls(){return new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected call "+c);}};}
    static void suffix(Observed m) {
        assertEquals(List.of(new Touch("R8",S+8L),new Touch("R8",S+0x10L),new Touch("R8",S+0x18L),
                new Touch("R8",S-8L),new Touch("R8",S)),m.touches.subList(m.touches.size()-5,m.touches.size()));
    }

    @Test void zeroCountPrecedencePreservesFullStateAndExactFrameTouches() {
        var n=n(700);
        var left0=new Observed();left0.m.put(S,RIP);
        var a=regs(100,0x123,P,0x3333L,Long.MIN_VALUE+3L,0);
        var exp=new HashMap<>(left0.m.snapshot());prologue(exp,n,false);
        var out=RotateFullState292.execute(new Entry(I,S,a,n),left0,noCalls(),(site,guard)->{throw new AssertionError("early budget");});
        assertEquals(new NormalReturn(bits(a,a.r8Bits(),a.rcxBits(),a.rdxBits(),a.r8Bits(),0,a.xmm0(),a.xmm1(),a.xmm2(),a.xmm3(),a.xmm4()),RIP,S+8,n),out);
        assertEquals(exp,left0.m.snapshot());
        assertEquals(List.of(new Touch("W8",S+0x18L),new Touch("W8",S-8L),new Touch("R8",S+0x18L),new Touch("R8",S-8L),new Touch("R8",S)),left0.touches);
        var right0=new Observed();right0.m.put(S,RIP);right0.m.put(S+0x28L,0);
        var b=regs(200,-1,P,P+40,P+80,3);exp=new HashMap<>(right0.m.snapshot());prologue(exp,n,false);
        var result=RotateFullState292.execute(new Entry(I,S,b,n),right0,noCalls(),(site,guard)->{throw new AssertionError("early budget");});
        assertEquals(new NormalReturn(bits(b,P,P,P+40,P+80,3,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4()),RIP,S+8,n),result);
        assertEquals(exp,right0.m.snapshot());
        assertEquals(List.of(new Touch("W8",S+0x18L),new Touch("W8",S-8L),new Touch("R8",S+0x28L),new Touch("R8",S+0x18L),new Touch("R8",S-8L),new Touch("R8",S)),right0.touches);
    }

    @Test void leftScratchConsumesReal291AndFullOpaquePostsThenFreshStackRestores() {
        var m=new Observed();frame(m,2,T,1);initialWords(m,P,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15);
        var n=n(700);var in=regs(100,-1,P,P+40,P+120,1);
        var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);words(expected,T,1,2,3,4,5);
        long newRip=0x12345678L;qword(expected,S+8,0xABCL);qword(expected,S+0x10,0xDEFL);qword(expected,S+0x18,0x888L);qword(expected,S-8,0x999L);qword(expected,S,newRip);
        qword(expected,S-0x30L,I+0xF0F1EEL);
        var p1=regs(300,123,456,789,900,901);var p2=regs(500,1001,1002,1003,1004,1005);
        var offered1=bits(in,T+40,P,P+40,80,1,new Bits128(5,0),new Bits128(3,4),in.xmm2(),in.xmm3(),in.xmm4());
        var offered2=bits(p1,123,P+80,T,40,901,p1.xmm0(),p1.xmm1(),p1.xmm2(),p1.xmm3(),p1.xmm4());
        var expectedCalls=List.of(new Call(0xF0F1D0L,TargetKind.DIRECT_RVA,0x4226860L,S-0x28L,offered1,nv(n,n.rbxBits(),T+40,80,P)),
                new Call(0xF0F1E9L,TargetKind.DIRECT_RVA,0x4226860L,S-0x28L,offered2,nv(n,P+80,40,80,P)));
        var seen=new ArrayList<Call>();var budget=new ArrayList<Long>();
        var actual=RotateFullState292.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c) {
                int k=seen.size();assertEquals(expectedCalls.get(k),c);seen.add(c);
                assertEquals(I+c.callSiteRva()+5,m.m.readQword(S-0x30L));
                if(k==0){m.m.put(S+8,0xABCL);m.m.put(S+0x10,0xDEFL);m.m.put(S+0x18,0x888L);m.m.put(S-8,0x999L);m.m.put(S,newRip);return p1;}
                return p2;
            }
        },(site,guard)->{assertEquals(0xF0ABA0L,site);budget.add(guard);});
        assertEquals(expectedCalls,seen);assertEquals(List.of(P),budget);
        assertEquals(new NormalReturn(bits(p2,P+80,p2.rcxBits(),p2.rdxBits(),p2.r8Bits(),p2.r9Bits(),p2.xmm0(),p2.xmm1(),p2.xmm2(),p2.xmm3(),p2.xmm4()),newRip,S+8,nv(n,0xABC,0xDEF,0x888,0x999)),actual);
        assertEquals(expected,m.m.snapshot());suffix(m);
        assertTrue(m.touches.contains(new Touch("R8",S-0x30L))); // actual child291 freshRET
        assertEquals(3,m.touches.stream().filter(t->t.equals(new Touch("W8",S-0x30L))).count());
    }

    @Test void rightScratchOverlapsThroughInterleavedLoadsAndAllPortPosts() {
        long scratch=P+88;var m=new Observed();frame(m,1,scratch,1);
        initialWords(m,P,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16);
        var n=n(700);var in=regs(100,-1,P,P+80,P+120,2);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);
        words(expected,P+80,11,11,12,12,14,14);qword(expected,S-0x30L,I+0xF0F25AL);
        var p1=regs(300,123,456,789,900,901);var p2=regs(500,1001,1002,1003,1004,1005);
        var o1=bits(in,P+120,P+40,P,80,2,new Bits128(14,0),new Bits128(12,14),in.xmm2(),in.xmm3(),in.xmm4());
        var o2=bits(p1,123,P,scratch,40,901,p1.xmm0(),p1.xmm1(),p1.xmm2(),p1.xmm3(),p1.xmm4());
        var expectedCalls=List.of(new Call(0xF0F244L,TargetKind.DIRECT_RVA,0x4226860L,S-0x28L,o1,nv(n,scratch+40,scratch,P+40,P)),
                new Call(0xF0F255L,TargetKind.DIRECT_RVA,0x4226860L,S-0x28L,o2,nv(n,40,scratch,P+40,P)));
        var seen=new ArrayList<Call>();var guards=new ArrayList<Long>();
        var out=RotateFullState292.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){int k=seen.size();assertEquals(expectedCalls.get(k),c);seen.add(c);assertEquals(I+c.callSiteRva()+5,m.m.readQword(S-0x30L));return k==0?p1:p2;}},
                (site,guard)->{assertEquals(0xF0F210L,site);guards.add(guard);});
        assertEquals(expectedCalls,seen);assertEquals(List.of(P+80),guards);assertEquals(expected,m.m.snapshot());suffix(m);
        assertEquals(new NormalReturn(bits(p2,P+40,p2.rcxBits(),p2.rdxBits(),p2.r8Bits(),p2.r9Bits(),p2.xmm0(),p2.xmm1(),p2.xmm2(),p2.xmm3(),p2.xmm4()),RIP,S+8,n),out);
    }

    @Test void noScratchOddEvenReversalsKeepAllDataAndActualFinalXmmDivisionState() {
        // Literal after-row identities and last swapped row identities from the held three reversal loops.
        int[][] input={{1,1},{2,1},{1,2},{2,2}};
        int[][] after={{2,1},{3,1,2},{2,3,1},{3,4,1,2}};
        int[] lastLow={1,2,1,1},lastHigh={2,3,2,4};
        for(int k=0;k<input.length;k++) {
            int left=input[k][0],right=input[k][1],total=left+right;
            var m=new Observed();frame(m,right,T,0);var n=n(700);var in=regs(100,-1,P,P+left*40L,P+total*40L,left);
            for(int row=1;row<=total;row++)initialWords(m,P+(row-1)*40L,row*100L,row*100L+1,row*100L+2,row*100L+3,row*100L+4);
            var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);
            for(int j=0;j<after[k].length;j++){long x=after[k][j]*100L;words(expected,P+j*40L,x,x+1,x+2,x+3,x+4);}
            var sites=new ArrayList<Long>();
            var out=RotateFullState292.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->{sites.add(site);assertTrue(sites.size()<12);});
            long lo=lastLow[k]*100L,hi=lastHigh[k]*100L;
            var expectedV=bits(in,P+right*40L,P+(total/2)*40L,right,P+total*40L,left,
                    new Bits128(hi+4,0),new Bits128(hi+2,hi+3),new Bits128(lo+4,0),new Bits128(lo,lo+1),new Bits128(lo+2,lo+3));
            assertEquals(new NormalReturn(expectedV,RIP,S+8,n),out,"matrix "+k);
            assertEquals(expected,m.m.snapshot(),"matrix "+k);suffix(m);
            assertTrue(sites.containsAll(List.of(0xF0F280L,0xF0F2D0L,0xF0F320L)));
        }
    }

    @Test void signedCountAdmissionAndRawPointerEqualityAreNotArrayRangeNormalization() {
        var n=n(700);
        for(boolean firstEqualsMiddle:new boolean[]{true,false}) {
            long middle=firstEqualsMiddle?P:P+80,last=P+80;
            var m=new Observed();frame(m,1,T,-1);var in=regs(100,-1,P,middle,last,2);
            var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);
            var out=RotateFullState292.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->{throw new AssertionError("pointer equality skip");});
            assertEquals(new NormalReturn(bits(in,firstEqualsMiddle?last:P,-1,middle,last,2,in.xmm0(),in.xmm1(),in.xmm2(),in.xmm3(),in.xmm4()),RIP,S+8,n),out);
            assertEquals(expected,m.m.snapshot());suffix(m);
        }
        var m=new Observed();frame(m,1,T,0);var in=regs(100,-1,P,P,P,-1);var count=new ArrayList<Long>();
        var out=RotateFullState292.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){count.add(c.callSiteRva());assertEquals(0,c.volatileBits().r8Bits());assertEquals(S-0x28L,c.rspBits());return c.volatileBits();}},
                (site,guard)->{throw new AssertionError("empty copy no loop");});
        assertEquals(List.of(0xF0F1D0L,0xF0F1E9L),count);assertEquals(P,out.volatileBits().raxBits());assertEquals(n,out.nonvolatileBits());
    }

    @Test void scratchAliasingChildReturnCannotBecomeSuccessfulNormalContinuation() {
        var m=new Observed();frame(m,1,S-0x30L,1);initialWords(m,P,0x123,2,3,4,5);
        var n=n(700);var in=regs(100,-1,P,P+40,P+80,1);var expected=new HashMap<>(m.m.snapshot());prologue(expected,n,true);
        words(expected,S-0x30L,0x123,2,3,4,5);
        assertThrows(UnsupportedOperationException.class,()->RotateFullState292.execute(new Entry(I,S,in,n),m,noCalls(),(site,guard)->{}));
        assertEquals(expected,m.m.snapshot());assertEquals(new Touch("R8",S-0x30L),m.touches.getLast());
        assertFalse(m.touches.contains(new Touch("R8",S)));
    }

    @Test void swapBlockOverlapAndMissingLaterLoadPreserveActualXmmAndWritePrefixes() {
        var m=new Observed();initialWords(m,P,1,2,3,4,5,6);
        var expected=new HashMap<>(m.m.snapshot());words(expected,P,2,3,4,5,6,4);
        var out=RotateSwap40Block292.transfer(m,P+8,P);
        assertEquals(new RotateSwap40Block292.Result(P+48,new Bits128(4,0),new Bits128(2,4),new Bits128(6,0),new Bits128(2,3),new Bits128(4,5)),out);
        assertEquals(expected,m.m.snapshot());
        assertEquals(List.of(new Touch("R16",P),new Touch("R16",P+8),new Touch("R16",P+24),new Touch("R8",P+40),new Touch("W16",P+8),
                new Touch("R16",P+16),new Touch("W16",P+24),new Touch("R8",P+32),new Touch("W8",P+40),new Touch("W16",P),new Touch("W16",P+16),new Touch("W8",P+32)),m.touches);
        var missing=new Observed();initialWords(missing,P,11,12);initialWords(missing,T,21,22,23,24,25);
        expected=new HashMap<>(missing.m.snapshot());words(expected,T,11,12);
        assertThrows(UnsupportedOperationException.class,()->RotateSwap40Block292.transfer(missing,T,P));
        assertEquals(expected,missing.m.snapshot());assertEquals(new Touch("R16",P+16),missing.touches.getLast());assertEquals(2,missing.m.writes.size());
    }

    @Test void budgetAndOpaqueExceptionsDoNotInventNormalReturnOrErasePriorEffects() {
        var n=n(700);var malformed=new Observed();frame(malformed,1,T,1);initialWords(malformed,P,1,2,3,4,5);
        var in=regs(100,-1,P,P+41,P+80,1);var expected=new HashMap<>(malformed.m.snapshot());prologue(expected,n,true);words(expected,T,1,2,3,4,5);qword(expected,S-0x30L,I+0xF0F1C4L);
        var guards=new ArrayList<Long>();var stop=new IllegalArgumentException("finite row stop");
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->RotateFullState292.execute(new Entry(I,S,in,n),malformed,noCalls(),(site,guard)->{assertEquals(0xF0ABA0L,site);guards.add(guard);if(guards.size()==2)throw stop;})));
        assertEquals(List.of(P,P+40),guards);assertEquals(expected,malformed.m.snapshot());assertFalse(malformed.touches.contains(new Touch("R8",S-0x30L)));
        var aborted=new Observed();frame(aborted,1,T,1);initialWords(aborted,P,1,2,3,4,5);
        var error=new IllegalStateException("actual normal port rejected");
        assertSame(error,assertThrows(IllegalStateException.class,()->RotateFullState292.execute(new Entry(I,S,regs(100,-1,P,P+40,P+80,1),n),aborted,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){assertEquals(0xF0F1D0L,c.callSiteRva());throw error;}},(site,guard)->{})));
        assertEquals(I+0xF0F1D5L,aborted.m.readQword(S-0x30L));assertEquals(new Touch("W8",S-0x30L),aborted.touches.getLast());
        assertFalse(aborted.touches.contains(new Touch("R8",S)));
    }
}
