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
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Source literals and new composition only; owner reviewed production, no Native/whole-domain proof. */
final class GeneralFullState294Test {
    static final long I=0x180000000L,S=0x200000L,G=S-0x78L,C=S-0x80L,P=0x10000L,T=0x30000L;
    static final long RIP=0x7fff11223344L,MAGIC=0x6666666666666667L;
    static VolatileBits input(long seed,long first,long middle,long last,long left) {
        return RotateFullState292Test.regs(seed,seed+1,first,middle,last,left);
    }
    static VolatileBits post(long seed){return input(seed,seed+2,seed+3,seed+4,seed+5);}
    static VolatileBits bits(VolatileBits v,long a,long c,long d,long e,long f) {
        return new VolatileBits(a,c,d,e,f,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static VolatileBits r11(VolatileBits v,long value) {
        return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),value,v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static NonvolatileBits offered(NonvolatileBits n,long cut,long left,long middle,long last,long right) {
        return new NonvolatileBits(cut,left,P,middle,last,n.r13Bits(),right,MAGIC,n.xmm6());
    }
    static void frame(Observed m,long right,long cap,int tag) {
        m.m.put(S,RIP);m.m.put(S+0x28,right);m.m.put(S+0x30,T);m.m.put(S+0x38,cap);m.m.put(S+0x40,0x1122334455667700L|(tag&255));
    }
    static long[] row(int index,int score){return new long[]{0xAABBCCDD00000000L|Integer.toUnsignedLong(score),0x1100000000000000L+index,0x2200000000000000L+index,0x3300000000000000L+index,0x4400000000000000L+index};}
    static void words(Map<Long,Byte> map,long at,long...data){for(int i=0;i<data.length;i++)qword(map,at+8L*i,data[i]);}
    static void rows(Observed m,int...scores){for(int i=0;i<scores.length;i++)words(m.m.data,P+i*40L,row(i,scores[i]));}
    static void parentFrame(Map<Long,Byte> map,NonvolatileBits n) {
        qword(map,S+8,n.rbxBits());qword(map,S+0x10,n.rbpBits());qword(map,S+0x18,n.rsiBits());qword(map,S+0x20,n.rdiBits());
        qword(map,S-8,n.r12Bits());qword(map,S-0x10,n.r14Bits());qword(map,S-0x18,n.r15Bits());
    }
    static final class Reject extends Gate47Fixture273.Calls {
        @Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected opaque call "+c);}
    }

    @Test void rawSearchStepsDistinguishSignedTiesAndPreserveEveryUnwrittenBit() {
        int[] pivot={5,5,Integer.MIN_VALUE,Integer.MIN_VALUE,Integer.MAX_VALUE,Integer.MAX_VALUE};
        int[] probe={5,5,Integer.MAX_VALUE,Integer.MAX_VALUE,Integer.MIN_VALUE,Integer.MIN_VALUE};
        boolean[] mode={true,false,true,false,true,false},advance={false,true,true,true,false,false};
        for(int k=0;k<mode.length;k++) {
            var m=new Observed();dword(m.m.data,P+80,probe[k]);var n=n(0x5566778800000000L);
            var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,S,input(0xE000000000000000L,0x999,4,0x777,1),n));
            r.r9=P;r.r10=Integer.toUnsignedLong(pivot[k]);var in=r.volatileBits();
            GeneralSearchStep294.step(r,m,mode[k]);
            var expect=new VolatileBits(advance[k]?-3L:10L,2,advance[k]?1:2,P+80,advance[k]?P+120:P,
                    Integer.toUnsignedLong(pivot[k]),in.r11Bits(),in.xmm0(),in.xmm1(),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
            assertEquals(expect,r.volatileBits(),"step "+k);assertEquals(n,r.nonvolatileBits());assertEquals(S,r.rsp);
            assertEquals(List.of(new Touch("R4",P+80)),m.touches);assertTrue(m.m.writes.isEmpty());
        }
    }

    @Test void full472To293To292To291KeepsFramesWidePostsFreshSavedStateAndReturn() {
        var m=new Observed();frame(m,2,1,0x80);rows(m,9,5,7,3);
        var n=n(0x5566778800000000L);var in=input(0xE000000000000000L,P,P+80,P+160,2);
        var p1=post(0xA000000000000000L);var p2=post(0xB000000000000000L);var p3=post(0xC000000000000000L);var p4=post(0xD000000000000000L);
        var expected=new HashMap<>(m.m.snapshot());parentFrame(expected,n);
        qword(expected,S-0x20,1);qword(expected,S-0x28,1);qword(expected,S-0x30,P+120);qword(expected,S-0x38,P+40);
        expected.put(S-0x40,(byte)0x80);qword(expected,S-0x48,1);qword(expected,S-0x50,T);qword(expected,S-0x58,1);qword(expected,C,I+0x1A830B9L);
        qword(expected,S-0x68,P+160);qword(expected,S-0x78,P);qword(expected,S-0x88,P+40);qword(expected,S-0x90,2);
        qword(expected,S-0x98,P);qword(expected,S-0xA0,P+160);qword(expected,S-0xA8,n.r13Bits());
        qword(expected,S-0xB8,1);qword(expected,S-0xC0,T);qword(expected,S-0x60,1);qword(expected,S-0xC8,1);qword(expected,S-0xF0,I+0x1A83362L);
        qword(expected,S-0xD8,2);qword(expected,S-0xF8,MAGIC);qword(expected,S-0xE8,P+40);qword(expected,S-0xE0,P+80);qword(expected,S-0x120,I+0xF0F1EEL);
        expected.put(S-0xB0,(byte)0x80);words(expected,T,row(1,5));
        long changed=0x123456789ABC0000L,newRip=0x7fff88889999L;
        qword(expected,S+8,changed+1);qword(expected,S+0x10,changed+2);qword(expected,S+0x18,changed+3);qword(expected,S+0x20,changed+4);
        qword(expected,S-8,changed+5);qword(expected,S-0x10,changed+6);qword(expected,S-0x18,changed+7);qword(expected,S,newRip);
        var x=row(1,5);
        var firstV=new VolatileBits(T+40,P+40,P+80,40,1,5,1,new Bits128(x[4],0),new Bits128(x[2],x[3]),in.xmm2(),in.xmm3(),in.xmm4(),in.xmm5());
        var firstN=new NonvolatileBits(P+40,1,P,T+40,T,1,40,P+40,n.xmm6());
        var secondN=new NonvolatileBits(P+80,1,P,40,T,1,40,P+40,n.xmm6());
        var mergeN=new NonvolatileBits(128,1,P+80,P+80,T,1,2,MAGIC,n.xmm6());
        var expectedCalls=List.of(new Call(0xF0F1D0L,TargetKind.DIRECT_RVA,0x4226860L,S-0x118,firstV,firstN),
                new Call(0xF0F1E9L,TargetKind.DIRECT_RVA,0x4226860L,S-0x118,bits(p1,p1.raxBits(),P+80,T,40,p1.r9Bits()),secondN),
                new Call(0x1A8335DL,TargetKind.DIRECT_RVA,0x1A81AB0L,S-0xE8,bits(p2,P+80,P,P+40,P+80,1),mergeN));
        var tailFrame=new Tail(0x1A833A2L,TargetKind.DIRECT_RVA,0x1A81AB0L,
                new Entry(I,C,bits(p3,p3.raxBits(),P+80,P+120,P+160,1),offered(n,P+40,2,P+80,P+160,2)));
        var seen=new ArrayList<Call>();var guards=new ArrayList<Long>();
        var actual=GeneralFullState294.execute(new Entry(I,S,in,n),m,new GovernmentCrtBoundary185Api.Calls(){
            @Override public VolatileBits invoke(Call c){int k=seen.size();assertEquals(expectedCalls.get(k),c);seen.add(c);assertEquals(I+c.callSiteRva()+5,m.m.readQword(c.rspBits()-8));return k==0?p1:k==1?p2:p3;}
            @Override public NormalReturn tail(Tail t){
                assertEquals(tailFrame,t);assertFalse(m.touches.contains(new Touch("R8",S)));
                m.m.put(S+8,changed+1);m.m.put(S+0x10,changed+2);m.m.put(S+0x18,changed+3);m.m.put(S+0x20,changed+4);
                m.m.put(S-8,changed+5);m.m.put(S-0x10,changed+6);m.m.put(S-0x18,changed+7);m.m.put(S,newRip);
                return new NormalReturn(p4,m.readQword(t.entry().rspBits()),t.entry().rspBits()+8,t.entry().nonvolatileBits());
            }
            @Override public long readGsQword58(){throw new AssertionError("unused GS");}
        },(site,guard)->{guards.add(site);});
        assertEquals(expectedCalls,seen);assertEquals(List.of(0x1A82F80L,0x1A82F80L,0xF0ABA0L),guards);
        var finalN=new NonvolatileBits(changed+1,changed+2,changed+3,changed+4,changed+5,n.r13Bits(),changed+6,changed+7,n.xmm6());
        assertEquals(new NormalReturn(r11(p4,S-0x18),newRip,S+8,finalN),actual);assertEquals(expected,m.m.snapshot());
        assertEquals(1,m.touches.stream().filter(t->t.equals(new Touch("W8",C))).count());
        assertEquals(List.of(new Touch("R8",S+8),new Touch("R8",S+0x10),new Touch("R8",S+0x18),new Touch("R8",S+0x20),new Touch("R8",S-0x18),new Touch("R8",S-0x10),new Touch("R8",S-8),new Touch("R8",S)),m.touches.subList(m.touches.size()-8,m.touches.size()));
    }

    @Test void fullPartitionTieAndNegativeScoreCasesReachActualChildWithLiteralCuts() {
        int[][] scores={{9,5,5,5},{9,7,5,7},{Integer.MIN_VALUE,Integer.MAX_VALUE}};
        int[] left={2,3,1},right={2,1,1},firstCount={1,2,0},secondCount={0,0,1},firstIndex={1,2,0},secondIndex={2,3,2},rotIndex={1,2,1},savedRbxIndex={1,3,0};
        long[] expectedPivot={5,7,0x80000000L};int[] copies={0,0,2};
        for(int k=0;k<scores.length;k++) {
            final int j=k;var m=new Observed();frame(m,right[k],1,0xFF);rows(m,scores[k]);var n=n(700);
            long middle=P+left[k]*40L,last=P+(left[k]+right[k])*40L,firstCut=P+firstIndex[k]*40L,secondCut=P+secondIndex[k]*40L,rotated=P+rotIndex[k]*40L;
            var seen=new ArrayList<Call>();var tails=new ArrayList<Tail>();var searches=new ArrayList<Long>();
            var out=GeneralFullState294.execute(new Entry(I,S,input(100,P,middle,last,left[k]),n),m,new GovernmentCrtBoundary185Api.Calls(){
                @Override public VolatileBits invoke(Call c){seen.add(c);if(c.targetBits()==0x4226860L)return c.volatileBits();
                    assertEquals(0x1A8335DL,c.callSiteRva());assertEquals(P,c.volatileBits().rcxBits());assertEquals(firstCut,c.volatileBits().rdxBits());assertEquals(rotated,c.volatileBits().r8Bits());assertEquals(firstCount[j],c.volatileBits().r9Bits());
                    assertEquals(expectedPivot[j],c.volatileBits().r10Bits());assertEquals(secondCount[j],m.m.readQword(c.rspBits()+0x20));assertEquals(255,c.nonvolatileBits().rbxBits());return c.volatileBits();}
                @Override public NormalReturn tail(Tail t){tails.add(t);assertEquals(C,t.entry().rspBits());assertEquals(rotated,t.entry().volatileBits().rcxBits());assertEquals(secondCut,t.entry().volatileBits().rdxBits());assertEquals(last,t.entry().volatileBits().r8Bits());assertEquals(left[j]-firstCount[j],t.entry().volatileBits().r9Bits());
                    assertEquals(right[j]-secondCount[j],m.m.readQword(C+0x28));assertEquals(offered(n,P+savedRbxIndex[j]*40L,left[j],middle,last,right[j]),t.entry().nonvolatileBits());return new NormalReturn(t.entry().volatileBits(),m.readQword(C),C+8,t.entry().nonvolatileBits());}
                @Override public long readGsQword58(){throw new AssertionError("unused GS");}
            },(site,guard)->{if(site==0x1A82F80L||site==0x1A83020L)searches.add(site);else assertEquals(0xF0ABA0L,site);});
            assertEquals(copies[k]+1,seen.size());assertEquals(1,tails.size());assertEquals(n,out.nonvolatileBits());assertEquals(RIP,out.returnRipBits());assertEquals(S-0x18,out.volatileBits().r11Bits());
            assertEquals(k==1?List.of(0x1A83020L,0x1A83020L):k==2?List.of(0x1A82F80L):List.of(0x1A82F80L,0x1A82F80L),searches);
        }
    }

    @Test void zeroRawCountsSkipPivotAndProbeReadsButStillCallBothOpaqueMergePhases() {
        var m=new Observed();frame(m,0,0,0xFF);var n=n(0x3344556600000000L);var in=input(0xE000000000000000L,P,P,P,0);var seen=new ArrayList<Call>();var tails=new ArrayList<Tail>();
        var out=GeneralFullState294.execute(new Entry(I,S,in,n),m,new GovernmentCrtBoundary185Api.Calls(){
            @Override public VolatileBits invoke(Call c){seen.add(c);assertEquals(0x1A8335DL,c.callSiteRva());assertEquals(0,c.volatileBits().r9Bits());assertEquals(in.r10Bits(),c.volatileBits().r10Bits());return c.volatileBits();}
            @Override public NormalReturn tail(Tail t){tails.add(t);assertEquals(0,t.entry().volatileBits().r9Bits());return new NormalReturn(t.entry().volatileBits(),m.readQword(C),C+8,t.entry().nonvolatileBits());}
            @Override public long readGsQword58(){throw new AssertionError("unused GS");}
        },(site,guard)->{throw new AssertionError("zero no loop");});
        assertEquals(1,seen.size());assertEquals(1,tails.size());assertFalse(m.touches.stream().anyMatch(t->t.op().equals("R4")));
        assertEquals(in.r10Bits(),out.volatileBits().r10Bits());assertEquals(n,out.nonvolatileBits());assertEquals(RIP,out.returnRipBits());assertEquals(S-0x18,out.volatileBits().r11Bits());
    }

    @Test void actualChildReturnOrSavedNonvolatileCorruptionStopsParentEpilogue() {
        for(boolean corruptRip:new boolean[]{true,false}) {
            var m=new Observed();frame(m,0,0,0xFF);var n=n(700);var in=input(100,P,P,P,0);
            assertThrows(UnsupportedOperationException.class,()->GeneralFullState294.execute(new Entry(I,S,in,n),m,new GovernmentCrtBoundary185Api.Calls(){
                @Override public VolatileBits invoke(Call c){assertEquals(0x1A8335DL,c.callSiteRva());if(!corruptRip)m.m.put(C-8,0xBAD);return c.volatileBits();}
                @Override public NormalReturn tail(Tail t){if(corruptRip)m.writeQword(C,0x123);return new NormalReturn(t.entry().volatileBits(),m.readQword(C),C+8,t.entry().nonvolatileBits());}
                @Override public long readGsQword58(){throw new AssertionError("unused GS");}
            },(site,guard)->{throw new AssertionError("zero loop");}));
            assertFalse(m.touches.contains(new Touch("R8",S+8)));assertFalse(m.touches.contains(new Touch("R8",S)));assertEquals(new Touch("R8",C),m.touches.getLast());
            assertEquals(corruptRip?0x123:I+0x1A830B9L,m.m.readQword(C));
        }
    }

    @Test void budgetAndMissingProbeAbortAtActualReadBoundaryWithPriorFrameIntact() {
        var m=new Observed();frame(m,2,1,0x80);rows(m,9,5,7,3);var n=n(700);var in=input(100,P,P+80,P+160,2);var stop=new IllegalArgumentException("finite search");
        assertSame(stop,assertThrows(IllegalArgumentException.class,()->GeneralFullState294.execute(new Entry(I,S,in,n),m,new Reject(),(site,guard)->{assertEquals(0x1A82F80L,site);throw stop;})));
        assertEquals(7,m.m.writes.size());assertEquals(List.of(new Touch("R4",P+40)),m.touches.stream().filter(t->t.op().equals("R4")).toList());assertFalse(m.touches.contains(new Touch("W8",C)));
        var missing=new Observed();frame(missing,2,1,0x80);dword(missing.m.data,P+40,5);
        assertThrows(UnsupportedOperationException.class,()->GeneralFullState294.execute(new Entry(I,S,in,n),missing,new Reject(),(site,guard)->{assertEquals(0x1A82F80L,site);}));
        assertEquals(7,missing.m.writes.size());assertEquals(List.of(new Touch("R4",P+40),new Touch("R4",P+120)),missing.touches.stream().filter(t->t.op().equals("R4")).toList());assertFalse(missing.touches.contains(new Touch("W8",C)));
    }

    @Test void downstreamOpaqueExceptionKeepsActualNestedPushesAndNoParentReturn() {
        var m=new Observed();frame(m,0,0,0xFF);var error=new IllegalStateException("normal port refusal");
        assertSame(error,assertThrows(IllegalStateException.class,()->GeneralFullState294.execute(new Entry(I,S,input(100,P,P,P,0),n(700)),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(0x1A8335DL,c.callSiteRva());throw error;}
        },(site,guard)->{throw new AssertionError("zero loop");})));
        assertEquals(I+0x1A830B9L,m.m.readQword(C));assertEquals(I+0x1A83362L,m.m.readQword(S-0xF0));assertEquals(new Touch("W8",S-0xF0),m.touches.getLast());
        assertFalse(m.touches.contains(new Touch("R8",S+8)));assertFalse(m.touches.contains(new Touch("R8",S)));
    }
}
