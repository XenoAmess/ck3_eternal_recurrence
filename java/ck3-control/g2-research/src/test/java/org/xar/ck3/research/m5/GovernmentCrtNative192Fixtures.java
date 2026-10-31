package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentCrtNative192WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentCrtNative192WitnessApi.Kind;
import org.xar.ck3.research.m5.GovernmentCrtNative192WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New 185 protocol-bridge literals from complete M1 ASM, with explicit external
 * scripts. Two model rounds rejected; owner source, no subject Java read/run. */
public final class GovernmentCrtNative192Fixtures implements Book {
    private static final long I=0x140000000L,S=0x800008L,W=0x7fffe0L,SLOT=0x7fffd8L;
    private static final long GLOBAL=0x145c5cb10L,CRIT=0x145c5cb18L,WAIT_RIP=0x144223aaeL;
    private static final long T1=0x7777000011112222L,T2=0x8888000033334444L,T3=0x9999000055556666L;
    private static final long FRESH_GLOBAL=0x5555666677778888L,FRESH_BX=0xcafebabe10203040L;
    private static final long FRESH_TARGET=0xaaaa000066667777L;
    @Override public List<Witness> witnesses() {return List.of(notifyHigh(),notifyZero(),waitZero());}

    private static Witness notifyHigh() {
        Map<Long,Integer> seed=notifySeed(0x100000000L);
        VolatileBits pre=v(0x100000000L,I+0x5c5cb08L,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L);
        TailStep tail=new TailStep(new Tail(0x4223b07L,TargetKind.INDIRECT_ABSOLUTE,T3,new Entry(I,S,pre,nv())),
                seed,Map.of(),notifyReturn());
        return new Witness("notify192-high64-terminal-fullReturn",Kind.NOTIFY_TAIL,notifyEntry(),seed,List.of(tail),seed,notifyReturn());
    }
    private static Witness notifyZero() {
        Map<Long,Integer> seed=notifySeed(0),before=new LinkedHashMap<>(seed);qword(before,SLOT,I+0x4223b1bL);
        Map<Long,Integer> mutation=new LinkedHashMap<>();qword(mutation,GLOBAL,FRESH_GLOBAL);qword(mutation,S,0xfedcba9876543210L);
        CallStep call=new CallStep(new Call(0x4223b15L,TargetKind.INDIRECT_ABSOLUTE,T1,W,
                v(0,0x1111222233334444L,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L),nv()),before,mutation,postC());
        Map<Long,Integer> end=new LinkedHashMap<>(before);end.putAll(mutation);
        TailStep tail=new TailStep(new Tail(0x4223b26L,TargetKind.INDIRECT_ABSOLUTE,T2,
                new Entry(I,S,v(0xc000L,FRESH_GLOBAL,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L),nv())),
                end,Map.of(),notifyReturn());
        return new Witness("notify192-zero-mutatedRET-terminal-fullReturn",Kind.NOTIFY_TAIL,notifyEntry(),seed,
                List.of(call,tail),end,notifyReturn());
    }
    private static Witness waitZero() {
        Map<Long,Integer> seed=stack(WAIT_RIP);qword(seed,I+0x5c5cb40L,0);qword(seed,GLOBAL,0x1111222233334444L);
        qword(seed,I+0x43da4f0L,T1);qword(seed,I+0x43da518L,T2);qword(seed,I+0x43da500L,T3);
        Entry entry=new Entry(I,S,v(0xa000L,0x1122334480000001L,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L),nv());
        Map<Long,Integer> before1=new LinkedHashMap<>(seed);qword(before1,S-8,0xb000L);qword(before1,SLOT,I+0x4223b6eL);
        Map<Long,Integer> mutation1=new LinkedHashMap<>();qword(mutation1,GLOBAL,FRESH_GLOBAL);
        qword(mutation1,S-8,FRESH_BX);qword(mutation1,S,0xfedcba9876543210L);
        CallStep call1=new CallStep(new Call(0x4223b68L,TargetKind.INDIRECT_ABSOLUTE,T1,W,
                v(0,CRIT,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L),bx(0x80000001L)),
                before1,mutation1,postC());
        Map<Long,Integer> before2=new LinkedHashMap<>(before1);before2.putAll(mutation1);qword(before2,SLOT,I+0x4223b80L);
        Map<Long,Integer> mutation2=new LinkedHashMap<>();qword(mutation2,I+0x43da500L,FRESH_TARGET);
        CallStep call2=new CallStep(new Call(0x4223b7aL,TargetKind.INDIRECT_ABSOLUTE,T2,W,
                v(0xc000L,FRESH_GLOBAL,0x80000001L,0,0xc444L,0xc555L,0xc666L,0xd000L),bx(0x80000001L)),
                before2,mutation2,postD());
        Map<Long,Integer> end=new LinkedHashMap<>(before2);end.putAll(mutation2);
        NormalReturn fullReturn=new NormalReturn(fullF(),WAIT_RIP,S+8,nv());
        TailStep tail=new TailStep(new Tail(0x4223b8cL,TargetKind.INDIRECT_ABSOLUTE,FRESH_TARGET,
                new Entry(I,S,v(0xd000L,CRIT,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L),bx(FRESH_BX))),
                end,Map.of(),fullReturn);
        return new Witness("wait192-zero-twoCALL-freshsavedRBX-globalRCX-IAT",Kind.WAIT_CALL,entry,seed,
                List.of(call1,call2,tail),end,fullReturn);
    }
    private static Map<Long,Integer> stack(long ret) {
        Map<Long,Integer> m=new LinkedHashMap<>();for(long a=0x7fff80L;a<0x800040L;a++)m.put(a,0xa5);qword(m,S,ret);return m;
    }
    private static Map<Long,Integer> notifySeed(long flag) {
        Map<Long,Integer> m=stack(0x123456789abcdef0L);qword(m,I+0x5c5cb48L,flag);qword(m,GLOBAL,0x1111222233334444L);
        qword(m,I+0x43da5b0L,T1);qword(m,I+0x43da4a8L,T2);qword(m,I+0x43dbba8L,T3);return m;
    }
    private static Entry notifyEntry() {return new Entry(I,S,v(0xa000L,0xa111L,0xa222L,0xa333L,0xa444L,0xa555L,0xa666L,0xb000L),nv());}
    private static VolatileBits postC() {return v(0xc000L,0xc111L,0xc222L,0xc333L,0xc444L,0xc555L,0xc666L,0xd000L);}
    private static VolatileBits postD() {return v(0xd000L,0xd111L,0xd222L,0xd333L,0xd444L,0xd555L,0xd666L,0xe000L);}
    private static VolatileBits fullF() {return v(0xf000L,0xf111L,0xf222L,0xf333L,0xf444L,0xf555L,0xf666L,0x10000L);}
    private static NonvolatileBits nv() {return bx(0xb000L);}
    private static NonvolatileBits bx(long bx) {return new NonvolatileBits(bx,0xb111L,0xb222L,0xb333L,0xb444L,0xb555L,0xb666L,0xb777L,new Bits128(0xb100L,0xb101L));}
    private static NormalReturn notifyReturn() {
        return new NormalReturn(fullF(),0x1111222233334444L,0x880010L,new NonvolatileBits(0x11000L,0x11111L,0x11222L,
                0x11333L,0x11444L,0x11555L,0x11666L,0x11777L,new Bits128(0x11800L,0x11801L)));
    }
    private static VolatileBits v(long a,long c,long d,long r8,long r9,long r10,long r11,long x) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,new Bits128(x,x+1),new Bits128(x+2,x+3),new Bits128(x+4,x+5),
                new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static void qword(Map<Long,Integer> m,long a,long value) {for(int j=0;j<8;j++)m.put(a+j,(int)(value>>>(j*8))&255);}
}
