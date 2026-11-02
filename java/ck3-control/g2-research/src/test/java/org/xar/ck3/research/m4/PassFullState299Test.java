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
import org.xar.ck3.research.m4.RotateFullState292Test.Observed;
import org.xar.ck3.research.m4.RotateFullState292Test.Touch;

/** Owner held-source literals; model adapter and source counter do not receive this book. */
final class PassFullState299Test {
    static final long I=0x180000000L,S=0x90000L,P=0x2000L,T=0x5000L,RIP=0x77112233L;
    static VolatileBits input(long end,long out,long width) {
        return RotateFullState292Test.regs(100,0x123,P,end,out,width);
    }
    static VolatileBits vpost(VolatileBits v,long a,long c,long d,long r8,long r9,long r10) {
        return new VolatileBits(a,c,d,r8,r9,r10,v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    static NonvolatileBits npost(NonvolatileBits n,long bx,long bp,long si,long di,long r12,long r14,long r15) {
        return new NonvolatileBits(bx,bp,si,di,r12,n.r13Bits(),r14,r15,n.xmm6());
    }
    static Observed memory(long count) {
        var m=new Observed();m.m.put(S,RIP);m.m.put(S+0x28,count);return m;
    }
    static void words(Map<Long,Byte> m,long at,long...x){RotateFullState292Test.words(m,at,x);}
    static void rows(Observed m,int...scores) {
        for(int i=0;i<scores.length;i++)words(m.m.data,P+40L*i,SmallRangeFullState295Test.row(i+1,scores[i]));
    }
    static void frame(Map<Long,Byte> e,NonvolatileBits n,boolean main) {
        qword(e,S-8,n.rbpBits());qword(e,S-16,n.r14Bits());qword(e,S-24,n.r15Bits());
        if(main){qword(e,S+8,n.rbxBits());qword(e,S+16,n.rsiBits());qword(e,S+24,n.rdiBits());qword(e,S+32,n.r12Bits());}
    }
    static GovernmentCrtBoundary185Api.LoopBudget noLoop(){return (s,g)->{throw new AssertionError("unexpected loop");};}

    @Test void signedEarlyEntryUsesOnlyThreeSavesAndExactTailIdentityWithoutRetRead() {
        for(long count:new long[]{-1,1,Long.MIN_VALUE}) {
            var m=memory(count);var n=n(700);var v=input(P+80,T,1);var exp=new HashMap<>(m.m.snapshot());frame(exp,n,false);
            var nr=new NormalReturn(v,0xABCD,-17,n);var seen=new ArrayList<Tail>();
            var out=PassFullState299.execute(new Entry(I,S,v,n),m,new Gate47Fixture273.Calls(){
                @Override public VolatileBits invoke(Call c){throw new AssertionError("no normal copy");}
                @Override public NormalReturn tail(Tail t){seen.add(t);return nr;}
            },noLoop());
            assertSame(nr,out);assertEquals(List.of(new Tail(0x1A82449L,TargetKind.DIRECT_RVA,0x4226860L,
                    new Entry(I,S,vpost(v,T,T,P,80,1,P),n))),seen);
            assertEquals(exp,m.m.snapshot());assertEquals(List.of(new Touch("W8",S-8),new Touch("W8",S-16),new Touch("W8",S-24),
                    new Touch("R8",S+40),new Touch("R8",S-24),new Touch("R8",S-16),new Touch("R8",S-8)),m.touches);
        }
    }

    @Test void rightWinsActualNormalPortKeepsFullPostThenFreshSevenRestoresAndTailIdentity() {
        var m=memory(2);rows(m,5,10);var n=n(700);var v=input(P+80,T,1);
        var expected=new HashMap<>(m.m.snapshot());frame(expected,n,true);words(expected,T,SmallRangeFullState295Test.row(2,10));
        qword(expected,S-64,I+0x1A82410L);
        long[] slots={S+8,S-8,S+16,S+24,S+32,S-16,S-24};
        long[] values={0xAAA,0xBBB,0xCCC,0xDDD,0xEEE,0xFFF,0x999};
        for(int k=0;k<slots.length;k++)qword(expected,slots[k],values[k]);
        var post=RotateFullState292Test.regs(900,101,102,103,104,105);
        var expectedV=new VolatileBits(T,T+40,P,40,1,P,v.r11Bits(),new Bits128(0x4400000000000002L,0),
                new Bits128(0x2200000000000002L,0x3300000000000002L),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
        var expectedN=npost(n,40,0,P+80,T+40,40,1,P+80);
        var nr=new NormalReturn(post,7,9,n);var calls=new ArrayList<Call>();var tails=new ArrayList<Tail>();var guards=new ArrayList<Long>();
        var out=PassFullState299.execute(new Entry(I,S,v,n),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){
                assertEquals(new Call(0x1A8240BL,TargetKind.DIRECT_RVA,0x4226860L,S-56,expectedV,expectedN),c);calls.add(c);
                assertEquals(I+0x1A82410L,m.m.readQword(S-64));
                for(int k=0;k<slots.length;k++)m.m.put(slots[k],values[k]);return post;
            }
            @Override public NormalReturn tail(Tail t){tails.add(t);return nr;}
        },(s,g)->{assertTrue(s==0x1A82380L||s==0x1A823A2L);guards.add(s);});
        assertSame(nr,out);assertEquals(1,calls.size());
        assertEquals(List.of(new Tail(0x1A82449L,TargetKind.DIRECT_RVA,0x4226860L,new Entry(I,S,
                vpost(post,T+80,T+80,P+80,0,post.r9Bits(),P+80),npost(n,0xAAA,0xBBB,0xCCC,0xDDD,0xEEE,0xFFF,0x999)))),tails);
        assertEquals(List.of(0x1A82380L,0x1A823A2L),guards);assertEquals(expected,m.m.snapshot());
        assertFalse(m.touches.contains(new Touch("R8",S))); // tail itself owns any real RET
    }

    @Test void tiedAndSignedScoresChooseLeftAndRemainderSourceStaysFresh() {
        for(int[] scores:new int[][]{{7,7},{Integer.MAX_VALUE,Integer.MIN_VALUE}}) {
            var m=memory(2);rows(m,scores);var n=n(700);var v=input(P+80,T,1);var selected=new ArrayList<Call>();
            PassFullState299.execute(new Entry(I,S,v,n),m,new Gate47Fixture273.Calls(){
                @Override public VolatileBits invoke(Call c){selected.add(c);assertEquals(P+40,c.volatileBits().rdxBits());
                    assertEquals(T+40,c.volatileBits().rcxBits());assertEquals(40,c.volatileBits().r8Bits());
                    return c.volatileBits();}
                @Override public NormalReturn tail(Tail t){return new NormalReturn(t.entry().volatileBits(),RIP,S+8,t.entry().nonvolatileBits());}
            },(s,g)->{});
            assertEquals(1,selected.size());
            var row=SmallRangeFullState295Test.row(1,scores[0]);for(int k=0;k<5;k++)assertEquals(row[k],m.m.readQword(T+8L*k));
            assertEquals(List.of(new Touch("R4",P),new Touch("R4",P+40)),m.touches.stream().filter(t->t.op().equals("R4")).toList());
        }
    }

    @Test void overlappingDestinationKeepsInterleavedRowLoadsInsteadOfSnapshotCopy() {
        var m=memory(2);words(m.m.data,P,100,2,3,4,5,0,7,8,9,10);var v=input(P+80,P+8,1);var n=n(700);
        PassFullState299.execute(new Entry(I,S,v,n),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){assertEquals(P+40,c.volatileBits().rdxBits());return c.volatileBits();}
            @Override public NormalReturn tail(Tail t){return new NormalReturn(t.entry().volatileBits(),RIP,S+8,t.entry().nonvolatileBits());}
        },(s,g)->{});
        long[] after={100,100,2,2,4,4,7,8,9,10};for(int k=0;k<after.length;k++)assertEquals(after[k],m.m.readQword(P+8L*k));
        int begin=m.touches.indexOf(new Touch("R16",P));
        assertEquals(List.of(new Touch("R16",P),new Touch("W16",P+8),new Touch("R16",P+16),new Touch("W16",P+24),
                new Touch("R8",P+32),new Touch("W8",P+40)),m.touches.subList(begin,begin+6));
    }

    @Test void partialSecondGroupConsumesArbitraryCallbackPostsAndLiveSourceRows() {
        var m=memory(5);rows(m,1,3,2,4,5);var n=n(700);var in=input(P+200,T,1);var seen=new ArrayList<Call>();
        var posts=new VolatileBits[]{RotateFullState292Test.regs(300,11,12,13,14,15),RotateFullState292Test.regs(400,21,22,23,24,25)};
        var tails=new ArrayList<Tail>();
        PassFullState299.execute(new Entry(I,S,in,n),m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){int k=seen.size();seen.add(c);assertEquals(40,c.volatileBits().r8Bits());
                assertEquals(k==0?P:P+120,c.volatileBits().rdxBits());assertEquals(k==0?T+40:T+120,c.volatileBits().rcxBits());
                if(k==0){words(m.m.data,P+80,SmallRangeFullState295Test.row(3,100));return posts[0];}return posts[1];}
            @Override public NormalReturn tail(Tail t){tails.add(t);return new NormalReturn(t.entry().volatileBits(),RIP,S+8,t.entry().nonvolatileBits());}
        },(s,g)->{});
        assertEquals(2,seen.size());assertEquals(posts[0].r9Bits(),seen.get(1).volatileBits().r9Bits());
        assertEquals(SmallRangeFullState295Test.row(3,100)[0],m.m.readQword(T+80));
        assertEquals(vpost(posts[1],T+160,T+160,P+160,40,posts[1].r9Bits(),P+160),tails.getFirst().entry().volatileBits());
        assertEquals(n,tails.getFirst().entry().nonvolatileBits());
    }

    @Test void budgetAndOpaqueFailuresKeepWrittenPrefixAndNeverFabricateTailCompletion() {
        var n=n(700);var m=memory(2);rows(m,5,10);var stop=new IllegalStateException("budget actual");var sites=new ArrayList<Long>();
        assertSame(stop,assertThrows(IllegalStateException.class,()->PassFullState299.execute(new Entry(I,S,input(P+80,T,1),n),m,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unused normal port");}},
                (s,g)->{sites.add(s);if(s==0x1A823A2L)throw stop;})));
        assertEquals(List.of(0x1A82380L,0x1A823A2L),sites);assertFalse(m.touches.contains(new Touch("W8",S-64)));
        var failed=memory(2);rows(failed,5,10);var opaque=new UnsupportedOperationException("COPY depends on unsupported state");
        assertSame(opaque,assertThrows(UnsupportedOperationException.class,()->PassFullState299.execute(new Entry(I,S,input(P+80,T,1),n),failed,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){throw opaque;}
        },(s,g)->{})));
        assertEquals(I+0x1A82410L,failed.m.readQword(S-64));assertFalse(failed.touches.contains(new Touch("R8",S-24)));
    }

    @Test void threeActualCallerSitesBindWithoutExtraPushAndRejectRealBadChildFrames() {
        for(long site:new long[]{0x1A81A39L,0x1A81A65L,0x1A81A82L}) {
            var m=memory(0);m.m.put(S,I+site+5);var n=n(700);var v=input(P+80,T,1);
            var adapter=PassCalls299.bind(I,m,new Gate47Fixture273.Calls(){
                @Override public VolatileBits invoke(Call c){throw new AssertionError("unused normal port");}
                @Override public NormalReturn tail(Tail t){assertEquals(0x1A82449L,t.jumpSiteRva());
                    return new NormalReturn(t.entry().volatileBits(),m.readQword(S),S+8,t.entry().nonvolatileBits());}
            },noLoop());
            assertEquals(vpost(v,T,T,P,80,1,P),adapter.invoke(new Call(site,TargetKind.DIRECT_RVA,0x1A82330L,S+8,v,n)));
            assertEquals(new Touch("W8",S-8),m.touches.getFirst());
            assertEquals(3,m.touches.stream().filter(t->t.op().equals("W8")).count());
            for(int wrong=0;wrong<3;wrong++) {
                final int mode=wrong;var bad=memory(0);var corrupt=npost(n,n.rbxBits()+1,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r14Bits(),n.r15Bits());
                var binding=PassCalls299.bind(I,bad,new Gate47Fixture273.Calls(){@Override public VolatileBits invoke(Call c){throw new AssertionError("unused normal port");}
                @Override public NormalReturn tail(Tail t){
                    return new NormalReturn(v,mode==0?0:I+site+5,mode==1?0:S+8,mode==2?corrupt:n);}},noLoop());
                assertThrows(UnsupportedOperationException.class,()->binding.invoke(new Call(site,TargetKind.DIRECT_RVA,0x1A82330L,S+8,v,n)));
            }
        }
    }

    @Test void foreignNormalTailAndGsForwardOriginalObjectsWithoutMemoryOrBudgetUse() {
        var m=memory(0);var v=input(P+80,T,1);var n=n(700);var normal=new ArrayList<Call>();var tail=new ArrayList<Tail>();var nr=new NormalReturn(v,77,88,n);
        var binding=PassCalls299.bind(I,m,new Gate47Fixture273.Calls(){
            @Override public VolatileBits invoke(Call c){normal.add(c);return v;}
            @Override public NormalReturn tail(Tail t){tail.add(t);return nr;}
            @Override public long readGsQword58(){return 0xABCD;}
        },noLoop());
        for(Call c:List.of(new Call(0x1A81A3AL,TargetKind.DIRECT_RVA,0x1A82330L,S,v,n),new Call(0x1A81A39L,TargetKind.DIRECT_RVA,1,S,v,n),
                new Call(0x1A81A39L,TargetKind.INDIRECT_ABSOLUTE,0x1A82330L,S,v,n))){assertSame(v,binding.invoke(c));assertSame(c,normal.getLast());}
        var t=new Tail(0x1A81A39L,TargetKind.DIRECT_RVA,0x1A82330L,new Entry(I+99,S,v,n));assertSame(nr,binding.tail(t));assertSame(t,tail.getFirst());
        assertEquals(0xABCD,binding.readGsQword58());assertTrue(m.touches.isEmpty());
    }
}
