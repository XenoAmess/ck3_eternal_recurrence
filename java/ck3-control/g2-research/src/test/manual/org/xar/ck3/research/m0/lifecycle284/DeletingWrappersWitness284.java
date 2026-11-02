package org.xar.ck3.research.m0.lifecycle284;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m0.manager283.ManagerWitnessSupport283;
import static org.xar.ck3.research.m0.manager283.ManagerWitnessSupport283.*;

/** Four finite original-code-derived DATA cases; no native memory or allocation. */
public final class DeletingWrappersWitness284 {
    private static final long BASE=0x140000000L,SP=0x8000L,RIP=0x777766665555L,ROW=0x1200L;
    private static final NonvolatileBits N=n();
    private static final VolatileBits FIRST=v(0x101,0x102,0x103,0x104,0x105,0x106,0x107);
    private static final VolatileBits SECOND=new VolatileBits(0x201,0x202,0x203,0x204,0x205,0x206,0x207,
        new Bits128(31,32),new Bits128(33,34),new Bits128(35,36),new Bits128(37,38),new Bits128(39,40),new Bits128(41,42));
    private DeletingWrappersWitness284() { }
    private static VolatileBits withRax(VolatileBits v,long a){return new VolatileBits(a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static void variant(boolean manager,long flags,boolean mutateHomes){
        Image m=new Image();m.seedQ(SP,RIP);List<Call> seen=new ArrayList<>();
        Entry entry=new Entry(BASE,SP,v(0xAA,ROW,flags,0xBB,0xCC,0xDD,0xEE),N);
        long firstSite=manager?0x28EE5DFL:0x23DA68FL,firstTarget=manager?0x28EE610L:0x23D9E40L;
        long secondSite=manager?0x28EE5F1L:0x23DA6A1L,size=manager?0xA0L:0x390L;
        Calls calls=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            seen.add(c);eq(TargetKind.DIRECT_RVA,c.kind(),"direct kind");eq(SP-0x28,c.rspBits(),"pre-CALL SP");
            if(seen.size()==1){
                eq(firstSite,c.callSiteRva(),"first site");eq(firstTarget,c.targetBits(),"actual destructor target");eq(BASE+firstSite+5,m.peekQ(SP-0x30),"first pushed return");
                eq(ROW,c.volatileBits().rcxBits(),"original receiver");eq(flags,c.volatileBits().rdxBits(),"MOV EBX leaves incoming RDX");eq(Integer.toUnsignedLong((int)flags),c.nonvolatileBits().rbxBits(),"DWORD flags zero extension");eq(ROW,c.nonvolatileBits().rdiBits(),"retained receiver");
                if(mutateHomes){m.seedQ(SP+8,0x55);m.seedQ(SP-8,0x66);}return FIRST;
            }
            eq(secondSite,c.callSiteRva(),"free site");eq(0x4223F44L,c.targetBits(),"opaque free target");eq(BASE+secondSite+5,m.peekQ(SP-0x30),"second pushed return");eq(size,c.volatileBits().rdxBits(),"exact sized EDX");eq(ROW,c.volatileBits().rcxBits(),"reset original receiver");eq(FIRST.raxBits(),c.volatileBits().raxBits(),"RAX stays first return before free");eq(FIRST.xmm3(),c.volatileBits().xmm3(),"opaque XMM preserved");return SECOND;
        }};
        NormalReturn out=manager?DeletingWrappers284.executeManager(entry,m,calls):DeletingWrappers284.executePlayerInfo(entry,m,calls);
        boolean free=(flags&1L)!=0;eq(free?2:1,seen.size(),"saved BL low-bit branch");eq(withRax(free?SECOND:FIRST,ROW),out.volatileBits(),"only final MOV RAX overrides opaque V");
        NonvolatileBits expected=mutateHomes?new NonvolatileBits(0x55,N.rbpBits(),N.rsiBits(),0x66,N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6()):N;
        eq(expected,out.nonvolatileBits(),"actual epilogue loads");eq(RIP,out.returnRipBits(),"RET reads QWORD");eq(SP+8,out.callerRspBits(),"restored caller SP");eq(false,m.events.contains("rq@1200"),"no row dereference after opaque free");
    }
    private static void binding(){
        Image m=new Image();long pre=0xA000L;m.seedQ(pre-8,BASE+0xA07B33L);final Call[] last={null};final Tail[] tail={null};
        Calls fallback=new RejectCalls(){@Override public VolatileBits invoke(Call c){last[0]=c;return FIRST;}
            @Override public NormalReturn tail(Tail t){tail[0]=t;return new NormalReturn(SECOND,RIP,SP,N);}
            @Override public long readGsQword58(){return 0x8811;}};
        Calls bound=PlayerInfoDeletingCalls284.bind(BASE,m,fallback);
        Call exact=new Call(0xA07B31,TargetKind.INDIRECT_ABSOLUTE,BASE+0x23DA680,pre,v(0x99,ROW,0x100,1,2,3,4),N);
        eq(withRax(FIRST,ROW),bound.invoke(exact),"exact virtual-site binding");eq(0x23DA68FL,last[0].callSiteRva(),"only target inner destructor opaque");eq(BASE+0xA07B33L,m.peekQ(pre-8),"caller return not overwritten");
        for(Call c:List.of(new Call(0xA07B32,exact.kind(),exact.targetBits(),pre,exact.volatileBits(),N),new Call(exact.callSiteRva(),TargetKind.DIRECT_RVA,exact.targetBits(),pre,exact.volatileBits(),N),new Call(exact.callSiteRva(),exact.kind(),BASE+0x23DA681,pre,exact.volatileBits(),N))){eq(FIRST,bound.invoke(c),"unmatched result");same(c,last[0],"same unmatched call");}
        Tail t=new Tail(0xA07B31,TargetKind.INDIRECT_ABSOLUTE,BASE+0x23DA680,new Entry(BASE,SP,exact.volatileBits(),N));bound.tail(t);same(t,tail[0],"tail unchanged");eq(0x8811,bound.readGsQword58(),"GS unchanged");
        m.seedQ(pre-8,0xBAD);m.events.clear();boolean refused=false;try{bound.invoke(exact);}catch(RuntimeException expected){refused=true;}
        eq(true,refused,"bad continuation rejected");eq(List.of("rq@9ff8"),m.events,"precondition before target stores");
    }
    public static void main(String[] args){
        variant(false,0xFFFF000000000100L,true);variant(false,0xAABBCCDD80000001L,false);variant(true,1L,false);binding();
        System.out.println("PASS deleting-wrappers284 cases=4 checks="+ManagerWitnessSupport283.checks);
    }
}
