package org.xar.ck3.research.m0.lifecycle285;

import java.util.ArrayList;
import java.util.List;
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
import org.xar.ck3.research.m0.manager283.ManagerWitnessSupport283;
import static org.xar.ck3.research.m0.manager283.ManagerWitnessSupport283.*;

/** Four new caller/composition DATA paths, no old283 cases or native execution. */
public final class ManagerDestructorWitness285 {
    private static final long BASE=0x140000000L,SP=0x9000L,RIP=0x777788889999L,M=0x1000L,BUCKET=0x6000L;
    private static final NonvolatileBits N=n();
    private static final LoopBudget NO_LOOP=(site,cursor)->{throw new AssertionError("count0 or null child cannot loop");};
    private static final VolatileBits LAST=new VolatileBits(0xA1,0xA2,0xA3,0xA4,0xA5,0xA6,0xA7,
        new Bits128(1,2),new Bits128(3,4),new Bits128(5,6),new Bits128(7,8),new Bits128(9,10),new Bits128(11,12));
    private ManagerDestructorWitness285() { }
    private static VolatileBits withRax(VolatileBits v,long a){return new VolatileBits(a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static Entry entry(){return new Entry(BASE,SP,v(0x77,M,0x88,0x99,0xAA,0xBB,0xCC),N);}
    private static Image image(){
        Image m=new Image();m.seedQ(SP,RIP);m.seedQ(M+0x20,BUCKET);
        for(long offset:new long[]{0x88,0x70,0x58,0x40}){m.seedQ(M+offset,0);m.seedD(M+offset+8,0xABCD);m.seedD(M+offset+12,7);}return m;
    }
    private static void result(NormalReturn out,VolatileBits v){eq(v,out.volatileBits(),"actual final V");eq(N,out.nonvolatileBits(),"NV restored");eq(RIP,out.returnRipBits(),"RET QWORD");eq(SP+8,out.callerRspBits(),"caller SP");}
    private static void empty(boolean mutate){
        Image m=image();List<Call> seen=new ArrayList<>();VolatileBits supplier=withRax(LAST,BUCKET);
        Calls ports=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            seen.add(c);eq(0x28EE6AFL,c.callSiteRva(),"only opaque supplier");eq(TargetKind.DIRECT_RVA,c.kind(),"supplier direct");eq(0xB15000,c.targetBits(),"supplier target");eq(SP-0x28,c.rspBits(),"supplier preSP");eq(BASE+0x28EE6B4L,m.peekQ(SP-0x30),"supplier pushed continuation");
            eq(BASE+0x4763EE0L,m.peekQ(M),"actual RIP-relative vptr constant");eq(M+0x58,c.volatileBits().rcxBits(),"empty child RCX survives");eq(0,c.volatileBits().rdxBits(),"last pointer read overwrites RDX");eq(BUCKET,c.nonvolatileBits().rdiBits(),"bucket captured before supplier");
            if(mutate)m.seedQ(M+0x20,BUCKET+8);return supplier;
        }};
        NormalReturn out=ManagerDestructor28ee610.execute(entry(),m,ports,NO_LOOP);result(out,supplier);eq(1,seen.size(),"no array or bucket free");eq(mutate?BUCKET+8:BUCKET,m.peekQ(M+0x20),"no bucket reread/clear");
        eq(0xABCD,m.peekD(M+0x60),"null child capacity untouched");eq(7,m.peekD(M+0x64),"null child count untouched");
        eq(true,m.events.contains("wq@8fd0=1428ee688"),"actual283 child continuation pushed by caller");
    }
    private static void ordered(){
        Image m=image();long d88=0x2100,d70=0x2300,d58=0x2400,d40=0x2500;
        long a88=0x3100,a70=0x3300,a58=0x3400,a40=0x3500,aBucket=0x3800;
        m.seedQ(M+0x88,d88);m.seedQ(M+0x98,a88);m.seedQ(a88,0x4100);m.seedQ(0x4110,0x5100);
        m.seedQ(M+0x70,0xDEAD);m.seedQ(M+0x80,0xBEEF);m.seedQ(a70,0x4300);m.seedQ(0x4310,0x5300);
        m.seedQ(M+0x58,d58);m.seedD(M+0x64,0);m.seedQ(M+0x68,a58);m.seedQ(a58,0x4400);m.seedQ(0x4410,0x5400);
        m.seedQ(M+0x50,a40);m.seedQ(a40,0x4500);m.seedQ(0x4510,0x5500);
        m.seedQ(M+0x38,aBucket);m.seedQ(aBucket,0x4800);m.seedQ(0x4810,0x5800);
        List<Long> sites=new ArrayList<>();VolatileBits interim=v(1,2,3,4,5,6,7);
        Calls ports=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            sites.add(c.callSiteRva());long site=c.callSiteRva();
            if(site==0x28EE6AFL){eq(BUCKET,c.nonvolatileBits().rdiBits(),"old bucket captured");return withRax(interim,BUCKET+0x10);}
            eq(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"actual vtable target kind");
            if(site==0xA07B53L){
                eq(a58,c.volatileBits().rcxBits(),"nested allocator");eq(d58,c.volatileBits().rdxBits(),"nested data");eq(8,c.volatileBits().r8Bits(),"nested actualR8=8");eq(0x5400,c.targetBits(),"nested slot target");eq(SP-0x58,c.rspBits(),"nested283 own frame");eq(BASE+0xA07B56L,m.peekQ(SP-0x60),"nested actual continuation");eq(0,m.peekD(M+0x64),"nested count cleared");m.seedQ(M+0x40,d40);return interim;
            }
            eq(SP-0x28,c.rspBits(),"outer preSP");eq(4,c.volatileBits().r8Bits(),"outer R8D=4");eq(BASE+site+3,m.peekQ(SP-0x30),"3-byte virtual continuation");
            if(site==0x28EE649L){eq(a88,c.volatileBits().rcxBits(),"first receiver");eq(d88,c.volatileBits().rdxBits(),"first data");eq(0,m.peekD(M+0x94),"first count before call");eq(d88,m.peekQ(M+0x88),"first data not yet cleared");eq(0x5100,c.targetBits(),"first target");m.seedQ(M+0x70,d70);m.seedQ(M+0x80,a70);return interim;}
            if(site==0x28EE675L){eq(a70,c.volatileBits().rcxBits(),"later allocator fresh read");eq(d70,c.volatileBits().rdxBits(),"later data fresh read");eq(0,m.peekD(M+0x7C),"second count before call");eq(0,m.peekQ(M+0x88),"first data cleared before second");eq(0x5300,c.targetBits(),"second target");return interim;}
            if(site==0x28EE6A1L){eq(a40,c.volatileBits().rcxBits(),"postchild receiver");eq(d40,c.volatileBits().rdxBits(),"postchild mutation consumed");eq(0,m.peekD(M+0x4C),"third count before call");eq(0,m.peekQ(M+0x58),"mature child data already cleared");eq(0x5500,c.targetBits(),"third target");return interim;}
            eq(0x28EE6C9L,site,"last bucket free");eq(aBucket,c.volatileBits().rcxBits(),"bucket receiver");eq(BUCKET,c.volatileBits().rdxBits(),"captured old bucket");eq(0x5800,c.targetBits(),"bucket target");return LAST;
        }};
        NormalReturn out=ManagerDestructor28ee610.execute(entry(),m,ports,NO_LOOP);result(out,LAST);
        eq(List.of(0x28EE649L,0x28EE675L,0xA07B53L,0x28EE6A1L,0x28EE6AFL,0x28EE6C9L),sites,"actual port order with child reuse");
        for(long offset:new long[]{0x88,0x70,0x58,0x40}){eq(0,m.peekQ(M+offset),"data cleared "+offset);eq(0,m.peekD(M+offset+8),"capacity cleared "+offset);eq(0,m.peekD(M+offset+12),"count cleared "+offset);}eq(BUCKET,m.peekQ(M+0x20),"no fabricated final bucket clear");
    }
    private static void binding(){
        Image m=image();long pre=0xA000;m.seedQ(pre-8,BASE+0x28EE5E4);final Call[] last={null};final Tail[] tail={null};VolatileBits supplier=withRax(LAST,BUCKET);
        Calls fallback=new RejectCalls(){@Override public VolatileBits invoke(Call c){last[0]=c;return c.targetBits()==0xB15000L?supplier:LAST;}
            @Override public NormalReturn tail(Tail t){tail[0]=t;return new NormalReturn(LAST,RIP,SP,N);}
            @Override public long readGsQword58(){return 0x1234;}};
        Calls bound=ManagerDestructorCalls285.bind(BASE,m,fallback,NO_LOOP);
        Call exact=new Call(0x28EE5DF,TargetKind.DIRECT_RVA,0x28EE610,pre,entry().volatileBits(),N);
        eq(supplier,bound.invoke(exact),"actual wrapper binding");eq(0x28EE6AFL,last[0].callSiteRva(),"target actually executed");eq(BASE+0x28EE5E4,m.peekQ(pre-8),"no duplicate outer push");
        for(Call c:List.of(new Call(0x28EE5E0,exact.kind(),exact.targetBits(),pre,exact.volatileBits(),N),new Call(exact.callSiteRva(),TargetKind.INDIRECT_ABSOLUTE,exact.targetBits(),pre,exact.volatileBits(),N),new Call(exact.callSiteRva(),exact.kind(),0x28EE611,pre,exact.volatileBits(),N))){eq(LAST,bound.invoke(c),"unmatched result");same(c,last[0],"same original call");}
        Tail t=new Tail(0x28EE5DF,TargetKind.DIRECT_RVA,0x28EE610,entry());bound.tail(t);same(t,tail[0],"same tail");eq(0x1234,bound.readGsQword58(),"GS fallback");
        m.seedQ(pre-8,0xBAD);m.events.clear();boolean refused=false;try{bound.invoke(exact);}catch(RuntimeException expected){refused=true;}eq(true,refused,"bad continuation rejected");eq(List.of("rq@9ff8"),m.events,"before target stores");
    }
    public static void main(String[] args){empty(false);ordered();empty(true);binding();System.out.println("PASS manager-destructor285 cases=4 checks="+ManagerWitnessSupport283.checks);}
}
