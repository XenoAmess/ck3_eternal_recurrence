package org.xar.ck3.research.m0.manager283;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m0.manager283.ManagerWitnessSupport283.*;

/** Six new owner-derived literal cases; no native execution, JUnit or old-case run. */
public final class ManagerDeleteArrayWitness283 {
    private static final long BASE=0x140000000L, SP=0x8000L, RIP=0x7FFF12345678L;
    private static final long H=0x1000L,D=0x2000L,A=0x3000L,VT=0x4000L,T=0x5000L;
    private static final NonvolatileBits N=n();
    private static final VolatileBits FINAL=new VolatileBits(0xF1,0xF2,0xF3,0xF4,0xF5,0xF6,0xF7,
        new Bits128(1,2),new Bits128(3,4),new Bits128(5,6),new Bits128(7,8),new Bits128(9,10),new Bits128(11,12));
    private ManagerDeleteArrayWitness283() { }
    private static Entry entry(){return new Entry(BASE,SP,v(0xAA,H,0xFF00000000000000L,0xBB,0xCC,0xDD,0xEE),N);}
    private static Image image(long data,int count){
        Image m=new Image();m.seedQ(SP,RIP);m.seedQ(H,data);m.seedD(H+8,0xAABBCCDD);
        m.seedD(H+12,count);m.seedQ(H+16,A);m.seedQ(A,VT);m.seedQ(VT+16,T);return m;
    }
    private static void returned(NormalReturn r,NonvolatileBits expected){
        eq(RIP,r.returnRipBits(),"RET source");eq(SP+8,r.callerRspBits(),"caller SP");eq(expected,r.nonvolatileBits(),"restored NV");
    }
    private static void nullData(){
        Image m=new Image();m.seedQ(SP,RIP);m.seedQ(H,0);
        NormalReturn out=ManagerDeleteArrayA07b00.execute(entry(),m,new RejectCalls(),(site,cursor)->{throw new AssertionError("no loop");});
        returned(out,N);eq(entry().volatileBits(),out.volatileBits(),"null preserves V");
        eq(List.of("wq@8010=1111222233334444","wq@7ff8=9999aaaabbbbcccc","rq@1000","rq@8010","rq@7ff8","rq@8000"),m.events,"null exact access order");
    }
    private static void nonpositive(int count,boolean mutateHomes){
        Image m=image(D,count);List<Call> calls=new ArrayList<>();
        Calls ports=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            calls.add(c);eq(0xA07B53L,c.callSiteRva(),"allocator site");eq(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"indirect kind");eq(T,c.targetBits(),"actual allocator target");
            eq(SP-0x28,c.rspBits(),"pre-call SP");eq(BASE+0xA07B56L,m.peekQ(SP-0x30),"3-byte CALL return");
            eq(A,c.volatileBits().rcxBits(),"allocator receiver");eq(D,c.volatileBits().rdxBits(),"initial data for signed <=0");eq(8,c.volatileBits().r8Bits(),"alignment DWORD");eq(VT,c.volatileBits().raxBits(),"loaded vtable");
            eq(0,c.nonvolatileBits().rdiBits(),"XOR EDI zero-extends");eq(H,c.nonvolatileBits().rsiBits(),"retained header");eq(D,c.nonvolatileBits().rbxBits(),"data RBX");
            eq(0,m.peekD(H+12),"count cleared before call");eq(D,m.peekQ(H),"data cleared after call");eq(0xAABBCCDDL,Integer.toUnsignedLong(m.peekD(H+8)),"capacity still original at call");
            if(mutateHomes){m.seedQ(SP+16,0x111L);m.seedQ(SP-8,0x222L);m.seedQ(SP+8,0x333L);}return FINAL;
        }};
        NormalReturn out=ManagerDeleteArrayA07b00.execute(entry(),m,ports,(site,cursor)->{throw new AssertionError("signed count cannot iterate");});
        NonvolatileBits expected=mutateHomes?new NonvolatileBits(0x111L,N.rbpBits(),0x222L,0x333L,N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6()):N;
        returned(out,expected);eq(1,calls.size(),"one backing-array call");eq(FINAL,out.volatileBits(),"full opaque V propagation");eq(0,m.peekQ(H),"data zero");eq(0,m.peekD(H+8),"capacity zero");eq(A,m.peekQ(H+16),"allocator field untouched");
    }
    private static void positive(){
        Image m=image(D,3);long r1=0x6000L,r2=0x6100L,replacement=0x6200L;
        long rvt1=0x7000L,rvt2=0x7100L,newData=0x9000L,newAlloc=0xA000L,newVt=0xB000L;
        m.seedQ(D,r1);m.seedQ(D+8,0);m.seedQ(D+16,r2);m.seedQ(r1,rvt1);m.seedQ(rvt1,0xC001L);m.seedQ(replacement,rvt2);m.seedQ(rvt2,0xC002L);m.seedQ(newAlloc,newVt);m.seedQ(newVt+16,0xC003L);
        List<Call> calls=new ArrayList<>();List<Long> cursors=new ArrayList<>();
        VolatileBits rowResult=v(0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xD7);
        Calls ports=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            calls.add(c);eq(SP-0x28,c.rspBits(),"stable pre-call SP");
            if(calls.size()<=2){
                eq(0xA07B31L,c.callSiteRva(),"row site");eq(BASE+0xA07B33L,m.peekQ(SP-0x30),"2-byte row CALL return");eq(1,c.volatileBits().rdxBits(),"row EDX=1");
                if(calls.size()==1){eq(r1,c.volatileBits().rcxBits(),"first row");eq(rvt1,c.volatileBits().raxBits(),"first vptr");eq(3,c.nonvolatileBits().rdiBits(),"fixed initial count");eq(0xC001L,c.targetBits(),"first slot0");m.seedQ(D+16,replacement);m.seedQ(H,newData);m.seedD(H+12,17);m.seedQ(H+16,newAlloc);}
                else{eq(replacement,c.volatileBits().rcxBits(),"reload future old-array element");eq(rvt2,c.volatileBits().raxBits(),"replacement vptr");eq(1,c.nonvolatileBits().rdiBits(),"count stays loaded");eq(D+16,c.nonvolatileBits().rbxBits(),"old array cursor");eq(0xC002L,c.targetBits(),"replacement slot0");eq(rowResult.r8Bits(),c.volatileBits().r8Bits(),"opaque prior volatile survives");}
                return rowResult;
            }
            eq(0xA07B53L,c.callSiteRva(),"array call last");eq(newData,c.volatileBits().rdxBits(),"header data reloaded after positive loop");eq(newAlloc,c.volatileBits().rcxBits(),"allocator pointer reloaded");eq(newVt,c.volatileBits().raxBits(),"allocator vtable");eq(0xC003L,c.targetBits(),"actual new slot10");eq(8,c.volatileBits().r8Bits(),"R8D=8");eq(0,m.peekD(H+12),"count clears after mutations");eq(newData,m.peekQ(H),"data not yet cleared");return FINAL;
        }};
        NormalReturn out=ManagerDeleteArrayA07b00.execute(entry(),m,ports,(site,cursor)->{eq(0xA07B21L,site,"loop header");cursors.add(cursor);});
        returned(out,N);eq(List.of(D,D+8,D+16),cursors,"three fixed-count visits");eq(3,calls.size(),"two rows + array");eq(FINAL,out.volatileBits(),"final all volatile bits");eq(0,m.peekQ(H),"data cleared");eq(0,m.peekD(H+8),"capacity cleared");eq(0,m.peekD(H+12),"count cleared");
    }
    private static void boundedStop(){
        Image m=image(D,1);UnsupportedOperationException sentinel=new UnsupportedOperationException("owned finite stop");
        try{ManagerDeleteArrayA07b00.execute(entry(),m,new RejectCalls(),(site,cursor)->{eq(0xA07B21L,site,"budget header");eq(D,cursor,"budget cursor");throw sentinel;});throw new AssertionError("must stop");}
        catch(UnsupportedOperationException expected){same(sentinel,expected,"no wrapped budget failure");}
        eq(D,m.peekQ(H),"no fake clearing");eq(1,m.peekD(H+12),"count remains");eq(false,m.events.contains("rq@2000"),"stop before row read");
    }
    private static void binding(){
        Image m=new Image();long callerSp=0x9800L,entrySp=callerSp-8;m.seedQ(entrySp,BASE+0x28EE688L);m.seedQ(H,0);
        final Call[] last={null};final Tail[] lastTail={null};
        Calls fallback=new RejectCalls(){@Override public VolatileBits invoke(Call c){last[0]=c;return FINAL;}
            @Override public NormalReturn tail(Tail t){lastTail[0]=t;return new NormalReturn(FINAL,RIP,SP,N);}
            @Override public long readGsQword58(){return 0xABC;}};
        LoopBudget budget=(site,cursor)->{throw new AssertionError("null cannot iterate");};
        Calls bound=ManagerDeleteArrayA07b00Calls.bind(BASE,m,fallback,budget);
        Call exact=new Call(0x28EE683L,TargetKind.DIRECT_RVA,0xA07B00L,callerSp,entry().volatileBits(),N);
        eq(exact.volatileBits(),bound.invoke(exact),"exact binding full V");eq(null,last[0],"matched call not opaque fallback");eq(BASE+0x28EE688L,m.peekQ(entrySp),"binding never rewrites return");
        for(Call other:List.of(new Call(0x28EE684L,exact.kind(),exact.targetBits(),callerSp,exact.volatileBits(),N),new Call(exact.callSiteRva(),TargetKind.INDIRECT_ABSOLUTE,exact.targetBits(),callerSp,exact.volatileBits(),N),new Call(exact.callSiteRva(),exact.kind(),0xA07B01L,callerSp,exact.volatileBits(),N))){eq(FINAL,bound.invoke(other),"unmatched delegates");same(other,last[0],"original call object");}
        Tail t=new Tail(0x123,TargetKind.DIRECT_RVA,0xA07B00L,entry());bound.tail(t);same(t,lastTail[0],"original tail");eq(0xABC,bound.readGsQword58(),"GS delegates");
        m.seedQ(entrySp,0xBAD);m.events.clear();
        try{bound.invoke(exact);throw new AssertionError("bad return slot must reject");}catch(IllegalStateException expected){eq(List.of("rq@97f8"),m.events,"bad binding before target writes");}
    }
    public static void main(String[] args){
        nullData();nonpositive(0,true);nonpositive(-1,false);positive();boundedStop();binding();
        System.out.println("PASS manager-delete283 cases=6 checks="+ManagerWitnessSupport283.checks);
    }
}
