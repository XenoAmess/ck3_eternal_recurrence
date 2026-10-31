package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;

/** Owner-derived independent CPU transcript; only build overlay is model task. */
public final class GovernmentWholeRegistry196Fixtures implements Book {
    private static final long I=0x140000000L,S=0xbfecd0L,E=S-0x138L,W=S-0x160L,SLOT=S-0x168L;
    private record Transcript(List<CallStep> calls,Map<Long,Integer> carry) {
        private Transcript {calls=List.copyOf(calls);carry=Map.copyOf(carry);}
    }
    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeCrtTail191Fixtures().witnesses().get(0);
        CallStep old=base.crtEvents().stream().filter(e->e instanceof CallStep c&&isDb38(c))
                .map(e->(CallStep)e).findFirst().orElseThrow();
        return List.of(build(base,transcript(old)));
    }
    private static boolean isDb38(CallStep c) {
        return c.expected().kind()==TargetKind.DIRECT_RVA&&c.expected().callSiteRva()==0x424df29L
                &&c.expected().targetBits()==0x424db38L;
    }
    private static Transcript transcript(CallStep old) {
        VolatileBits in=old.expected().volatileBits();NonvolatileBits original=old.expected().nonvolatileBits();
        Map<Long,Integer> prologue=new LinkedHashMap<>();qword(prologue,E+8,original.rbxBits());
        qword(prologue,E+0x20,in.r9Bits());qword(prologue,E-8,original.rdiBits());
        Map<Long,Integer> before1=new LinkedHashMap<>(old.expectedMemoryBefore());before1.putAll(prologue);
        qword(before1,SLOT,I+0x424db54L);
        VolatileBits p1=post(0x1111111100000000L,0x1111111100000001L,0xd100L);
        VolatileBits p2=post(0x2222222200000000L,0xdeadbeef00000000L,0xe100L);
        VolatileBits p3=old.normalPost();
        NonvolatileBits n12=working(original,in.r9Bits(),in.r8Bits());
        CallStep c1=step(0x424db4fL,0x4247ffcL,fields(in,in.raxBits(),2L),n12,before1,Map.of(),p1);
        Map<Long,Integer> before2=new LinkedHashMap<>(before1);qword(before2,SLOT,I+0x424db5dL);
        Map<Long,Integer> mutation=new LinkedHashMap<>(old.mutation());dword(mutation,S-0xc8L,0x89abcdef);
        CallStep c2=step(0x424db58L,0x424dbb0L,fields(p1,p1.raxBits(),in.r8Bits()),n12,before2,mutation,p2);
        Map<Long,Integer> before3=new LinkedHashMap<>(before2);before3.putAll(mutation);qword(before3,SLOT,I+0x424db66L);
        CallStep c3=step(0x424db61L,0x4248050L,fields(p2,p2.raxBits(),0x89abcdefL),
                working(original,in.r9Bits(),0L),before3,Map.of(),p3);
        Map<Long,Integer> carry=new LinkedHashMap<>(prologue);carry.putAll(mutation);qword(carry,SLOT,I+0x424db66L);
        return new Transcript(List.of(c1,c2,c3),carry);
    }
    private static CallStep step(long site,long target,VolatileBits v,NonvolatileBits n,
            Map<Long,Integer> before,Map<Long,Integer> mutation,VolatileBits post) {
        return new CallStep(new Call(site,TargetKind.DIRECT_RVA,target,W,v,n),before,mutation,post);
    }
    private static NonvolatileBits working(NonvolatileBits n,long bx,long di) {
        return new NonvolatileBits(bx,n.rbpBits(),n.rsiBits(),di,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static VolatileBits fields(VolatileBits p,long a,long c) {
        return new VolatileBits(a,c,p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),p.r11Bits(),
                p.xmm0(),p.xmm1(),p.xmm2(),p.xmm3(),p.xmm4(),p.xmm5());
    }
    private static VolatileBits post(long h,long a,long x) {
        return new VolatileBits(a,h+2,h+3,h+4,h+5,h+6,h+7,new Bits128(x,x+1),new Bits128(x+2,x+3),
                new Bits128(x+4,x+5),new Bits128(x+6,x+7),new Bits128(x+8,x+9),new Bits128(x+10,x+11));
    }
    private static Map<Long,Integer> overlay(Map<Long,Integer> old,Map<Long,Integer> carry) {
        Map<Long,Integer> m=new LinkedHashMap<>(old);m.putAll(carry);return m;
    }
    private static OrdinaryStep overlayOrdinary(OrdinaryStep p,Map<Long,Integer> carry) {
        return new OrdinaryStep(p.expected(),overlay(p.expectedMemoryBytes(),carry),p.mutation(),p.normalPost(),p.unsupported());
    }
    private static Event overlayCrt(Event p,Map<Long,Integer> carry) {
        if(p instanceof CallStep c)return new CallStep(c.expected(),overlay(c.expectedMemoryBefore(),carry),c.mutation(),c.normalPost());
        if(p instanceof TailStep t)return new TailStep(t.expected(),overlay(t.expectedMemoryBefore(),carry),t.mutation(),t.normalPost());
        return p;
    }
    private static void qword(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++)m.put(a+j,(int)(v>>>(j*8))&255);}
    private static void dword(Map<Long,Integer> m,long a,int v) {for(int j=0;j<4;j++)m.put(a+j,(v>>>(j*8))&255);}

    private static Witness build(Witness base, Transcript t) {
        List<Event> newCrt = new ArrayList<>();
        boolean replaced = false;
        for (Event e : base.crtEvents()) {
            if (e instanceof CallStep c && isDb38(c)) {
                newCrt.addAll(t.calls());
                replaced = true;
            } else if (replaced) {
                newCrt.add(overlayCrt(e, t.carry()));
            } else {
                newCrt.add(e);
            }
        }
        var oldWhole = base.legacy().whole();
        List<OrdinaryStep> newOrdinary = oldWhole.ordinaryCalls().stream().map(s -> overlayOrdinary(s, t.carry())).toList();
        Map<Long, Integer> newFinal = overlay(oldWhole.expectedFinalBytes(), t.carry());
        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole196-registry",
            oldWhole.entry(),
            oldWhole.memorySeed(),
            oldWhole.gs58Bits(),
            oldWhole.initialCalls(),
            newOrdinary,
            oldWhole.lookupCalls(),
            oldWhole.cpuCalls(),
            oldWhole.budgets(),
            oldWhole.afterInitial(),
            oldWhole.afterFinal(),
            oldWhole.post153(),
            newFinal,
            oldWhole.expectedResult(),
            oldWhole.failure()
        );
        var oldLegacy = base.legacy();
        var newLegacy = new GovernmentWholeConcrete173WitnessApi.Witness(
            newWhole,
            oldLegacy.m0HashMxcsrAt4FE(),
            oldLegacy.m1HashMxcsrAt85E(),
            oldLegacy.deepSteps(),
            oldLegacy.atomicSteps(),
            oldLegacy.gsSteps()
        );
        return new Witness(newLegacy, newCrt);
    }
}
