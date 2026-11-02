package org.xar.ck3.research.m0.lifecycle286;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m0.manager283.ManagerWitnessSupport283;
import static org.xar.ck3.research.m0.manager283.ManagerWitnessSupport283.*;

/** Two new owned-DATA composition cases; no native allocation or old case execution. */
public final class ManagerLifecycleWitness286 {
    private static final long BASE=0x140000000L,SP=0x9000L,RIP=0x777788889999L,M=0x1000L;
    private static final long BUCKET=0x6000L,DATA=0x2000L,ROW=0x3000L,ALLOC=0x4000L;
    private static final NonvolatileBits N=n();
    private static final VolatileBits LAST=v(0xA1,0xA2,0xA3,0xA4,0xA5,0xA6,0xA7);
    private ManagerLifecycleWitness286() { }
    private static VolatileBits withRax(VolatileBits v,long a){return new VolatileBits(a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static Entry entry(long flags){return new Entry(BASE,SP,v(0x77,M,flags,0x99,0xAA,0xBB,0xCC),N);}
    private static Image image(){
        Image m=new Image();m.seedQ(SP,RIP);m.seedQ(M+0x20,BUCKET);
        for(long off:new long[]{0x88,0x70,0x58,0x40}){m.seedQ(M+off,0);m.seedD(M+off+8,0xABCD);m.seedD(M+off+12,7);}return m;
    }
    private static void result(NormalReturn out,VolatileBits actual){
        eq(withRax(actual,M),out.volatileBits(),"outer wrapper overrides only RAX");eq(N,out.nonvolatileBits(),"all original NV");eq(RIP,out.returnRipBits(),"outer original RET");eq(SP+8,out.callerRspBits(),"outer caller SP");
    }
    private static void empty(){
        Image m=image();List<Long> sites=new ArrayList<>();VolatileBits supplier=withRax(LAST,BUCKET);
        Calls ports=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            sites.add(c.callSiteRva());eq(0x28EE6AFL,c.callSiteRva(),"only residual supplier");eq(TargetKind.DIRECT_RVA,c.kind(),"supplier kind");eq(0xB15000,c.targetBits(),"supplier target");eq(SP-0x58,c.rspBits(),"nested manager call SP");eq(BASE+0x28EE6B4,m.peekQ(SP-0x60),"supplier actual push");return supplier;
        }};
        LoopBudget budget=(site,cursor)->{throw new AssertionError("empty array cannot loop");};
        NormalReturn out=ManagerLifecycle286.execute(entry(0),m,ports,budget);result(out,supplier);
        eq(List.of(0x28EE6AFL),sites,"all internal calls bound");eq(BASE+0x28EE5E4,m.peekQ(SP-0x30),"outer wrapper caller owns push");eq(true,m.events.contains("wq@8fa0=1428ee688"),"actual child continuation written before supplier reuses slot");
    }
    private static void rowAndDeletes(){
        Image m=image();m.seedQ(M+0x58,DATA);m.seedD(M+0x64,1);m.seedQ(M+0x68,ALLOC);
        m.seedQ(DATA,ROW);m.seedQ(ROW,0x3100);m.seedQ(0x3100,BASE+0x23DA680);
        m.seedQ(ALLOC,0x4100);m.seedQ(0x4110,0x5151);
        List<Long> sites=new ArrayList<>();int[] steps={0};
        Calls ports=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            long site=c.callSiteRva();sites.add(site);
            if(site==0x23DA68FL || site==0x23DA6A1L){
                eq(TargetKind.DIRECT_RVA,c.kind(),"row direct kind");eq(SP-0xB8,c.rspBits(),"row own preSP");eq(BASE+site+5,m.peekQ(SP-0xC0),"row continuation");eq(ROW,c.volatileBits().rcxBits(),"row original receiver");
                eq(site==0x23DA68FL?0x23D9E40:0x4223F44,c.targetBits(),"row actual residual callee");eq(site==0x23DA68FL?1:0x390,c.volatileBits().rdxBits(),"row flags or size");return LAST;
            }
            if(site==0xA07B53L){
                eq(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"backing allocator kind");eq(0x5151,c.targetBits(),"actual backing slot");eq(ALLOC,c.volatileBits().rcxBits(),"backing receiver");eq(DATA,c.volatileBits().rdxBits(),"backing data");eq(8,c.volatileBits().r8Bits(),"backing element size");eq(SP-0x88,c.rspBits(),"array own preSP");eq(BASE+0xA07B56,m.peekQ(SP-0x90),"backing continuation");eq(0,m.peekD(M+0x64),"count cleared before allocator");return LAST;
            }
            if(site==0x28EE6AFL){eq(TargetKind.DIRECT_RVA,c.kind(),"supplier kind");eq(0xB15000,c.targetBits(),"supplier target");eq(SP-0x58,c.rspBits(),"supplier nested SP");eq(BASE+0x28EE6B4,m.peekQ(SP-0x60),"supplier continuation");eq(0,m.peekQ(M+0x58),"child data cleared before supplier");return withRax(LAST,BUCKET);}
            eq(0x28EE5F1L,site,"only outer delete remains");eq(TargetKind.DIRECT_RVA,c.kind(),"outer delete direct");eq(0x4223F44,c.targetBits(),"outer cleanup target");eq(M,c.volatileBits().rcxBits(),"outer delete receiver");eq(0xA0,c.volatileBits().rdxBits(),"outer exact size");eq(SP-0x28,c.rspBits(),"outer own preSP");eq(BASE+0x28EE5F6,m.peekQ(SP-0x30),"outer delete continuation");return LAST;
        }};
        LoopBudget budget=(site,cursor)->{steps[0]++;eq(0xA07B21,site,"actual array loop site");eq(DATA,cursor,"actual array cursor");};
        result(ManagerLifecycle286.execute(entry(1),m,ports,budget),LAST);
        eq(List.of(0x23DA68FL,0x23DA6A1L,0xA07B53L,0x28EE6AFL,0x28EE5F1L),sites,"actual residual graph order");eq(1,steps[0],"one real loop step");eq(0,m.peekQ(M+0x58),"data cleared");eq(0,m.peekD(M+0x60),"capacity cleared");eq(0,m.peekD(M+0x64),"count cleared");eq(BUCKET,m.peekQ(M+0x20),"captured shared bucket unchanged");
    }
    public static void main(String[] args){empty();rowAndDeletes();System.out.println("PASS manager-lifecycle286 cases=2 checks="+ManagerWitnessSupport283.checks);}
}
