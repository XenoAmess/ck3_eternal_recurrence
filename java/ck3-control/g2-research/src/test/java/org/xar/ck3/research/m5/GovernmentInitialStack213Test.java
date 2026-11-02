package org.xar.ck3.research.m5;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.StackProbe78FullState290;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New whole Initial162/probe composition: literal normal DATA and failure prefixes, no hardware proof. */
final class GovernmentInitialStack213Test {
    static final long I=0x140000000L,S=0x200038L,G=0x300000L,A=0x310000L,TAG=0x320000L;
    static final long F=0x1fed00L,BP=0x1fee00L,PAT=0x8877665544332211L;
    static final Bits128 X6=new Bits128(0x6162636465666768L,0x7172737475767778L);
    static final NonvolatileBits N=new NonvolatileBits(0xb1,0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,0xb8,X6);
    static VolatileBits v(long seed,long rcx) {
        return new VolatileBits(seed+1,rcx,seed+3,seed+4,seed+5,seed+6,seed+7,
                new Bits128(seed+10,seed+11),new Bits128(seed+12,seed+13),
                new Bits128(seed+14,seed+15),new Bits128(seed+16,seed+17),
                new Bits128(seed+18,seed+19),new Bits128(seed+20,seed+21));
    }
    static final VolatileBits IN=v(0x1000,G),OUT=v(0x5000,0x5555);
    record Write(long address,int size,long low,long high) { }
    static Write q(long p,long x){return new Write(p,8,x,0);}
    static Write d(long p,int x){return new Write(p,4,Integer.toUnsignedLong(x),0);}
    static Write one(long p){return new Write(p,1,0,0);}
    static Write x(long p,Bits128 x){return new Write(p,16,x.lowBits(),x.highBits());}
    static void apply(Map<Long,Byte> data,Write w) {
        for(int j=0;j<w.size;j++)data.put(w.address+j,(byte)((j<8?w.low:w.high)>>>((j%8)*8)));
    }
    static final class Ram implements GovernmentInitialFrame162Api.Memory {
        final Map<Long,Byte> data=new HashMap<>();
        final List<Write> writes=new ArrayList<>();
        void seed(Write w){apply(data,w);}
        void store(Write w){writes.add(w);apply(data,w);}
        @Override public int readUnsignedByte(long p){Byte b=data.get(p);if(b==null)throw new AssertionError("unmapped owned read "+Long.toHexString(p));return Byte.toUnsignedInt(b);}
        @Override public int readDword(long p){int n=0;for(int j=0;j<4;j++)n|=readUnsignedByte(p+j)<<(8*j);return n;}
        @Override public long readQword(long p){long n=0;for(int j=0;j<8;j++)n|=(long)readUnsignedByte(p+j)<<(8*j);return n;}
        @Override public Bits128 read128(long p){return new Bits128(readQword(p),readQword(p+8));}
        @Override public void writeDword(long p,int n){store(d(p,n));}
        @Override public void writeQword(long p,long n){store(q(p,n));}
        @Override public void writeByte(long p,int n){store(new Write(p,1,n&255,0));}
        @Override public void write128(long p,Bits128 n){store(x(p,n));}
        @Override public int lockedXaddDword(long p,int n){throw new AssertionError("no atomic operation in these paths");}
    }
    static Ram seeded(int count,boolean tagMagic,int diagnostic) {
        Ram m=new Ram();
        m.seed(q(F+0x50,PAT));m.seed(d(G+0x48,count==0?-7:9));m.seed(q(G+0x418,TAG));
        m.seed(d(TAG+0x38,tagMagic?0x4744624f:0));m.seed(q(G+0x420,A));m.seed(d(G+0x42c,count));m.seed(d(G+0x4bc,diagnostic));
        return m;
    }
    static GovernmentInitialFrame162Api.Entry entry(){return new GovernmentInitialFrame162Api.Entry(I,S,IN,N);}
    static List<Write> probePrefix(boolean pages) {
        var w=new ArrayList<>(List.of(q(S-8,N.rbpBits()),q(S-16,N.rbxBits()),q(S-24,N.rsiBits()),q(S-32,N.rdiBits()),
                q(S-40,N.r12Bits()),q(S-48,N.r13Bits()),q(S-56,N.r14Bits()),q(S-64,N.r15Bits()),
                q(S-72,I+0x30a2f2fL),q(S-88,IN.r10Bits()),q(S-80,IN.r11Bits())));
        if(pages){w.add(one(0x1ff000L));w.add(one(0x1fe000L));}
        return w;
    }
    static void assertImage(Map<Long,Byte> before,Ram actual,List<Write> writes) {
        var expected=new HashMap<>(before);for(Write w:writes)apply(expected,w);
        assertEquals(writes,actual.writes);assertEquals(expected,actual.data);
    }
    static List<Write> commonAfterProbe(boolean pages,int field) {
        var w=new ArrayList<>(probePrefix(pages));
        w.add(x(F+0x12e0,X6));w.add(d(S+8,0));w.add(d(G+0x48,field));
        w.add(q(F+0x40,I+0x9d09e0L));w.add(q(F+0x48,0));w.add(x(BP+0xe0,new Bits128(I+0x9d09e0L,0)));w.add(q(BP+0xf0,PAT));
        return w;
    }
    static VolatileBits scalar(VolatileBits a,long rax,long rcx) {
        return new VolatileBits(rax,rcx,a.rdxBits(),a.r8Bits(),a.r9Bits(),a.r10Bits(),a.r11Bits(),a.xmm0(),a.xmm1(),a.xmm2(),a.xmm3(),a.xmm4(),a.xmm5());
    }

    @Test void wholeInitialUsesRealProbeThenSmallBranchAndReturnsLiteralJoinAndImage() {
        Ram m=seeded(0,false,0);var before=new HashMap<>(m.data);var seen=new ArrayList<OpaqueCall>();var pages=new ArrayList<Long>();int[] gs={0};
        var wantedCall=new OpaqueCall(0x30a2fe7L,0x2be3690L,F,
                new VolatileBits(I+0x9d09e0L,A,A,BP+0xe0,IN.r9Bits(),IN.r10Bits(),IN.r11Bits(),
                        new Bits128(I+0x9d09e0L,0),new Bits128(PAT,0),IN.xmm2(),IN.xmm3(),IN.xmm4(),IN.xmm5()),
                new NonvolatileBits(N.rbxBits(),BP,0,G,N.r12Bits(),0,A,A,X6));
        var outer=new GovernmentInitialFrame162Api.Calls(){
            @Override public VolatileBits invoke(OpaqueCall c){seen.add(c);assertEquals(wantedCall,c);assertEquals(probePrefix(true),m.writes.subList(0,13));return OUT;}
            @Override public long readGsQword58(){throw new AssertionError("no GS58 in this path");}
        };
        var actual=GovernmentInitialStack213.execute(entry(),m,outer,(site,capacity)->{throw new AssertionError("no allocation attempt");},
                ()->{gs[0]++;assertEquals(probePrefix(false),m.writes);return 0x200000L;},
                (site,page)->{assertEquals(0x42247e0L,site);pages.add(page);});
        assertEquals(List.of(0x1ff000L,0x1fe000L),pages);assertEquals(1,gs[0]);assertEquals(List.of(wantedCall),seen);
        assertEquals(new GovernmentInitialFrame162Api.Join(0x30a3162L,I,F,scalar(OUT,0,OUT.rcxBits()),
                new NonvolatileBits(N.rbxBits(),BP,0,G,0x158,0,A,1,X6)),actual);
        assertImage(before,m,commonAfterProbe(true,0));
    }

    @Test void wholeInitialKeepsForeignLocalBranchAndGs58DistinctFromGs10() {
        Ram m=seeded(64,true,3);m.seed(d(I+0x5450fa4L,2));m.seed(q(0x330000L,0x340000L));m.seed(new Write(0x340158L,1,1,0));
        var before=new HashMap<>(m.data);var seen=new ArrayList<OpaqueCall>();int[] gs={0,0};
        var mid1=scalar(v(0x6000,0x6666),0,0x6666);var mid2=v(0x7000,0x7777);
        var nEarly=new NonvolatileBits(N.rbxBits(),BP,N.rsiBits(),G,N.r12Bits(),0,N.r14Bits(),N.r15Bits(),X6);
        var c1=new OpaqueCall(0x30a2f7bL,0xa11cc0L,F,
                new VolatileBits(TAG,G+0x420,G+0x418,IN.r8Bits(),IN.r9Bits(),IN.r10Bits(),IN.r11Bits(),IN.xmm0(),IN.xmm1(),IN.xmm2(),IN.xmm3(),IN.xmm4(),IN.xmm5()),nEarly);
        var c2=new OpaqueCall(0x30a2f92L,0x880340L,F,
                new VolatileBits(0,G+0x420,G+0x418,mid1.r8Bits(),mid1.r9Bits(),mid1.r10Bits(),mid1.r11Bits(),mid1.xmm0(),mid1.xmm1(),mid1.xmm2(),mid1.xmm3(),mid1.xmm4(),mid1.xmm5()),nEarly);
        var c3=new OpaqueCall(0x30a30a4L,0x30abbb0L,F,
                new VolatileBits(BP+0x1e0,A,A+512,64,BP+0x1e0,mid2.r10Bits(),mid2.r11Bits(),new Bits128(I+0x9d09e0L,0),new Bits128(PAT,0),mid2.xmm2(),mid2.xmm3(),mid2.xmm4(),mid2.xmm5()),
                new NonvolatileBits(32,BP,64,G,N.r12Bits(),0,A,A+512,X6));
        var wanted=List.of(c1,c2,c3);
        var outer=new GovernmentInitialFrame162Api.Calls(){
            @Override public VolatileBits invoke(OpaqueCall c){assertTrue(seen.size()<3);assertEquals(wanted.get(seen.size()),c);seen.add(c);return seen.size()==1?mid1:seen.size()==2?mid2:OUT;}
            @Override public long readGsQword58(){gs[1]++;assertEquals(wanted,seen);return 0x330000L;}
        };
        var actual=GovernmentInitialStack213.execute(entry(),m,outer,(site,capacity)->{throw new AssertionError("local branch has no allocation attempt");},
                ()->{gs[0]++;return 0;},(site,page)->{throw new AssertionError("no probe page expected");});
        assertEquals(wanted,seen);assertArrayEquals(new int[]{1,1},gs);
        assertEquals(new GovernmentInitialFrame162Api.Join(0x30a3162L,I,F,scalar(OUT,0x330000L,0x340000L),
                new NonvolatileBits(32,BP,64,G,0x158,0,A,1,X6)),actual);
        var writes=new ArrayList<>(commonAfterProbe(false,9));writes.add(q(BP+0x1d0,BP+0x1e0));writes.add(q(BP+0x1d8,32));
        writes.add(q(F+0x28,BP+0xe0));writes.add(q(F+0x20,32));writes.add(d(S+16,2));assertImage(before,m,writes);
    }

    @Test void probeFailuresAndNullInputsNeverMintInitialContinuationOrRepeatEffects() {
        var noForeign=new GovernmentInitialFrame162Api.Calls(){
            @Override public VolatileBits invoke(OpaqueCall c){throw new AssertionError("no foreign callback after failed probe");}
            @Override public long readGsQword58(){throw new AssertionError("no GS58 after failed probe");}
        };
        var noInitial=(GovernmentInitialFrame162Api.LoopBudget)(site,capacity)->{throw new AssertionError("no allocation attempt");};
        var noPages=(GovernmentCrtBoundary185Api.LoopBudget)(site,page)->{throw new AssertionError("no probe page");};
        Ram m=new Ram();var before=new HashMap<>(m.data);var gsError=new IllegalStateException("explicit GS10 unavailable");
        assertSame(gsError,assertThrows(IllegalStateException.class,()->GovernmentInitialStack213.execute(entry(),m,noForeign,noInitial,()->{throw gsError;},noPages)));
        assertImage(before,m,probePrefix(false));
        Ram stopped=new Ram();var stoppedBefore=new HashMap<>(stopped.data);var budgetError=new UnsupportedOperationException("finite probe work");var pages=new ArrayList<Long>();
        assertSame(budgetError,assertThrows(UnsupportedOperationException.class,()->GovernmentInitialStack213.execute(entry(),stopped,noForeign,noInitial,()->0x200000L,(site,page)->{
            assertEquals(0x42247e0L,site);pages.add(page);if(pages.size()==2)throw budgetError;
        })));
        assertEquals(List.of(0x1ff000L,0x1fe000L),pages);var partial=new ArrayList<>(probePrefix(false));partial.add(one(0x1ff000L));assertImage(stoppedBefore,stopped,partial);
        Ram untouched=new Ram();StackProbe78FullState290.Gs10 noGs=()->{throw new AssertionError("null preflight must not call GS10");};
        assertThrows(NullPointerException.class,()->GovernmentInitialStack213.execute(null,untouched,noForeign,noInitial,noGs,noPages));
        assertThrows(NullPointerException.class,()->GovernmentInitialStack213.execute(entry(),null,noForeign,noInitial,noGs,noPages));
        assertThrows(NullPointerException.class,()->GovernmentInitialStack213.execute(entry(),untouched,null,noInitial,noGs,noPages));
        assertThrows(NullPointerException.class,()->GovernmentInitialStack213.execute(entry(),untouched,noForeign,null,noGs,noPages));
        assertThrows(NullPointerException.class,()->GovernmentInitialStack213.execute(entry(),untouched,noForeign,noInitial,null,noPages));
        assertThrows(NullPointerException.class,()->GovernmentInitialStack213.execute(entry(),untouched,noForeign,noInitial,noGs,null));
        assertTrue(untouched.data.isEmpty());assertTrue(untouched.writes.isEmpty());
    }
}
