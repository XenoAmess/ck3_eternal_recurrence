package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentLookupLoop580WitnessApi.CallExpectation;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;

/** Owner-only source-derived indexed tail transcript; model owns only build overlay. */
public final class GovernmentWholeIndexed197Fixtures implements Book {
    private static final long I=0x140000000L,A=I+0x43da500L,L=I+0x43da4f0L,INDEX=I+0x5c5d330L;
    private static final long ENTER=0x7777000011112222L,LEAVE=0x8888000033334444L,FRESH=0xaaaa000066667777L;
    private record Transcript(TailStep first,CallStep middle,TailStep third,
            Map<Long,Integer> initial,Map<Long,Integer> after) {
        private Transcript {initial=Map.copyOf(initial);after=Map.copyOf(after);}
    }
    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeRegistry196Fixtures().witnesses().get(0);
        return List.of(build(base,transcript(base)));
    }
    private static boolean direct(CallStep c,long site,long target) {
        return c.expected().kind()==TargetKind.DIRECT_RVA&&c.expected().callSiteRva()==site&&c.expected().targetBits()==target;
    }
    private static CallStep find(Witness base,long site,long target) {
        return base.crtEvents().stream().filter(e->e instanceof CallStep c&&direct(c,site,target))
                .map(e->(CallStep)e).findFirst().orElseThrow();
    }
    private static Transcript transcript(Witness base) {
        Map<Long,Integer> initial=new LinkedHashMap<>();qword(initial,A,ENTER);qword(initial,L,LEAVE);
        Map<Long,Integer> after=new LinkedHashMap<>(initial);qword(after,L,FRESH);
        CallStep first=find(base,0x424db4fL,0x4247ffcL),middle=find(base,0x424db58L,0x424dbb0L),third=find(base,0x424db61L,0x4248050L);
        Map<Long,Integer> mutation=new LinkedHashMap<>(middle.mutation());qword(mutation,L,FRESH);
        CallStep mid=new CallStep(middle.expected(),overlay(middle.expectedMemoryBefore(),initial),mutation,middle.normalPost());
        return new Transcript(indexed(first,0x424800eL,ENTER,I+0x424db54L,initial),mid,
                indexed(third,0x4248062L,FRESH,I+0x424db66L,after),initial,after);
    }
    private static TailStep indexed(CallStep old,long jump,long target,long returnRip,Map<Long,Integer> state) {
        Call c=old.expected();VolatileBits v=c.volatileBits();long rcx=INDEX+(long)(int)v.rcxBits()*40L;
        VolatileBits pre=new VolatileBits(INDEX,rcx,v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
        return new TailStep(new Tail(jump,TargetKind.INDIRECT_ABSOLUTE,target,
                new Entry(I,c.rspBits()-8,pre,c.nonvolatileBits())),overlay(old.expectedMemoryBefore(),state),old.mutation(),
                new NormalReturn(old.normalPost(),returnRip,c.rspBits(),c.nonvolatileBits()));
    }
    private static Map<Long,Integer> overlay(Map<Long,Integer> old,Map<Long,Integer> state) {
        Map<Long,Integer> m=new LinkedHashMap<>(old);m.putAll(state);return m;
    }
    private static MemorySeed seed(MemorySeed old,Map<Long,Integer> state) {
        Map<Long,Integer> m=new LinkedHashMap<>();for(SeedByte b:old.bytes())m.put(b.addressBits(),b.byteBits());m.putAll(state);
        return new MemorySeed(m.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList());
    }
    private static OrdinaryStep ordinary(OrdinaryStep p,Map<Long,Integer> state) {
        return new OrdinaryStep(p.expected(),overlay(p.expectedMemoryBytes(),state),p.mutation(),p.normalPost(),p.unsupported());
    }
    private static CallExpectation lookup(CallExpectation p,Map<Long,Integer> state) {
        return new CallExpectation(p.expected(),overlay(p.expectedMemoryBytes(),state),p.memoryMutation(),p.normalPost(),p.unsupported());
    }
    private static Event crt(Event p,Map<Long,Integer> state,boolean after) {
        if(p instanceof CallStep c) {
            Call e=c.expected();
            if(after&&e.kind()==TargetKind.INDIRECT_ABSOLUTE&&e.callSiteRva()==0x4223a74L)
                e=new Call(e.callSiteRva(),e.kind(),FRESH,e.rspBits(),e.volatileBits(),e.nonvolatileBits());
            return new CallStep(e,overlay(c.expectedMemoryBefore(),state),c.mutation(),c.normalPost());
        }
        if(p instanceof TailStep t)return new TailStep(t.expected(),overlay(t.expectedMemoryBefore(),state),t.mutation(),t.normalPost());
        return p;
    }
    private static void qword(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++)m.put(a+j,(int)(v>>>(j*8))&255);}

    private static Witness build(Witness base, Transcript t) {
        List<Event> newCrt = new ArrayList<>();
        boolean after = false;
        for (Event e : base.crtEvents()) {
            if (e instanceof CallStep c) {
                if (direct(c, 0x424db4fL, 0x4247ffcL)) {
                    newCrt.add(t.first());
                } else if (direct(c, 0x424db58L, 0x424dbb0L)) {
                    newCrt.add(t.middle());
                    after = true;
                } else if (direct(c, 0x424db61L, 0x4248050L)) {
                    newCrt.add(t.third());
                } else {
                    newCrt.add(crt(e, after ? t.after() : t.initial(), after));
                }
            } else {
                newCrt.add(crt(e, after ? t.after() : t.initial(), after));
            }
        }
        var oldWhole = base.legacy().whole();
        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole197-indexed-two-tail",
            oldWhole.entry(),
            seed(oldWhole.memorySeed(), t.initial()),
            oldWhole.gs58Bits(),
            oldWhole.initialCalls().stream().map(p -> ordinary(p, t.initial())).toList(),
            oldWhole.ordinaryCalls().stream().map(p -> ordinary(p, t.after())).toList(),
            oldWhole.lookupCalls().stream().map(p -> lookup(p, t.initial())).toList(),
            oldWhole.cpuCalls(),
            oldWhole.budgets(),
            oldWhole.afterInitial(),
            oldWhole.afterFinal(),
            oldWhole.post153(),
            overlay(oldWhole.expectedFinalBytes(), t.after()),
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
