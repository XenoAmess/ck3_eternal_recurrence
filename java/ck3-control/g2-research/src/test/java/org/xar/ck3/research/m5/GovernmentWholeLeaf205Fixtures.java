package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;

/** Owner-independent original57/122B CPU transcript; model only supplies thin build. */
public final class GovernmentWholeLeaf205Fixtures implements Book {
    private static final long I=0x140000000L,S=0xbfecd0L,W=S-0x1d0L,E=S-0x1d8L;
    private static final long GLOBAL=I+0x5c5de30L,SIZE_IAT=I+0x43da7c8L,ALLOC_IAT=I+0x43da388L;
    private static final long GLOBAL_FIRST=0x1111222233334444L,GLOBAL_NEXT=0x2222333344445555L;
    private static final long SIZE_TARGET=0x5555666677778888L,ALLOC_FIRST=0x9999aaaabbbbccccL,ALLOC_NEXT=0xaaaabbbbccccddddL;
    private record Transcript(TailStep size,CallStep allocation,Map<Long,Integer> initial,
            Map<Long,Integer> afterSize,Map<Long,Integer> carry) {
        private Transcript {initial=Map.copyOf(initial);afterSize=Map.copyOf(afterSize);carry=Map.copyOf(carry);}
    }
    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeResizeFree202Fixtures().witnesses().get(0);
        return List.of(build(base,transcript(base)));
    }
    private static boolean size(CallStep c) {return c.expected().kind()==TargetKind.DIRECT_RVA
            &&c.expected().callSiteRva()==0x425b848L&&c.expected().targetBits()==0x4259250L;}
    private static boolean allocation(CallStep c) {return c.expected().kind()==TargetKind.DIRECT_RVA
            &&c.expected().callSiteRva()==0x425b85eL&&c.expected().targetBits()==0x4251f4cL;}
    private static CallStep find(Witness base,boolean wantSize) {
        return base.crtEvents().stream().filter(e->e instanceof CallStep c&&(wantSize?size(c):allocation(c)))
                .map(e->(CallStep)e).findFirst().orElseThrow();
    }
    private static Transcript transcript(Witness base) {
        CallStep oldSize=find(base,true),oldAlloc=find(base,false);
        Map<Long,Integer> initial=new LinkedHashMap<>();qword(initial,GLOBAL,GLOBAL_FIRST);
        qword(initial,SIZE_IAT,SIZE_TARGET);qword(initial,ALLOC_IAT,ALLOC_FIRST);
        Map<Long,Integer> sizeMutation=new LinkedHashMap<>(oldSize.mutation());
        qword(sizeMutation,GLOBAL,GLOBAL_NEXT);qword(sizeMutation,ALLOC_IAT,ALLOC_NEXT);
        Map<Long,Integer> afterSize=overlay(initial,sizeMutation);
        VolatileBits sv=oldSize.expected().volatileBits();NonvolatileBits sn=oldSize.expected().nonvolatileBits();
        VolatileBits tailV=values(sv.raxBits(),GLOBAL_FIRST,0L,sv.rcxBits(),sv.r9Bits(),sv.r10Bits(),sv.r11Bits(),sv);
        TailStep actualSize=new TailStep(new Tail(0x4259282L,TargetKind.INDIRECT_ABSOLUTE,SIZE_TARGET,
                new Entry(I,E,tailV,sn)),overlay(oldSize.expectedMemoryBefore(),initial),sizeMutation,
                new NormalReturn(oldSize.normalPost(),I+0x425b84dL,W,sn));

        VolatileBits av=oldAlloc.expected().volatileBits();NonvolatileBits an=oldAlloc.expected().nonvolatileBits();
        Map<Long,Integer> stack=new LinkedHashMap<>();qword(stack,E+8,an.rbxBits());qword(stack,E-8,an.rdiBits());
        qword(stack,E-0x30,I+0x4251fbfL);
        Map<Long,Integer> beforeAlloc=overlay(oldAlloc.expectedMemoryBefore(),afterSize);beforeAlloc.putAll(stack);
        VolatileBits allocV=values(av.raxBits(),GLOBAL_NEXT,0L,av.rcxBits(),av.rdxBits(),av.r10Bits(),av.r11Bits(),av);
        NonvolatileBits allocN=new NonvolatileBits(av.rdxBits(),an.rbpBits(),an.rsiBits(),av.rcxBits(),
                an.r12Bits(),an.r13Bits(),an.r14Bits(),an.r15Bits(),an.xmm6());
        CallStep actualAlloc=new CallStep(new Call(0x4251fb9L,TargetKind.INDIRECT_ABSOLUTE,ALLOC_NEXT,
                E-0x28,allocV,allocN),beforeAlloc,oldAlloc.mutation(),oldAlloc.normalPost());
        Map<Long,Integer> carry=overlay(afterSize,stack);
        return new Transcript(actualSize,actualAlloc,initial,afterSize,carry);
    }
    private static VolatileBits values(long a,long c,long d,long r8,long r9,long r10,long r11,VolatileBits x) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,x.xmm0(),x.xmm1(),x.xmm2(),x.xmm3(),x.xmm4(),x.xmm5());
    }
    private static Map<Long,Integer> overlay(Map<Long,Integer> old,Map<Long,Integer> state) {
        Map<Long,Integer> m=new LinkedHashMap<>(old);m.putAll(state);return m;
    }
    private static OrdinaryStep ordinary(OrdinaryStep p,Map<Long,Integer> state) {
        return new OrdinaryStep(p.expected(),overlay(p.expectedMemoryBytes(),state),p.mutation(),p.normalPost(),p.unsupported());
    }
    private static Event crt(Event p,Map<Long,Integer> state) {
        if(p instanceof CallStep c)return new CallStep(c.expected(),overlay(c.expectedMemoryBefore(),state),c.mutation(),c.normalPost());
        if(p instanceof TailStep t)return new TailStep(t.expected(),overlay(t.expectedMemoryBefore(),state),t.mutation(),t.normalPost());
        return p;
    }
    private static MemorySeed seed(MemorySeed old,Map<Long,Integer> state) {
        Map<Long,Integer> bytes=new LinkedHashMap<>();for(SeedByte b:old.bytes()) bytes.put(b.addressBits(),b.byteBits());
        bytes.putAll(state);return new MemorySeed(bytes.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList());
    }
    private static void qword(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++)m.put(a+j,(int)(v>>>(j*8))&255);}
    private static Witness build(Witness base, Transcript t) {
        List<Event> newCrt = new ArrayList<>();
        int phase = 0;
        for (Event e : base.crtEvents()) {
            if (e instanceof CallStep c && size(c)) {
                newCrt.add(t.size());
                phase = 1;
            } else if (e instanceof CallStep c && allocation(c)) {
                newCrt.add(t.allocation());
                phase = 2;
            } else {
                Map<Long,Integer> state = phase == 0 ? t.initial() : phase == 1 ? t.afterSize() : t.carry();
                newCrt.add(crt(e, state));
            }
        }
        var oldWhole = base.legacy().whole();
        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole205-leaf-nonnull",
            oldWhole.entry(),
            seed(oldWhole.memorySeed(), t.initial()),
            oldWhole.gs58Bits(),
            oldWhole.initialCalls().stream().map(p -> ordinary(p, t.initial())).toList(),
            oldWhole.ordinaryCalls().stream().map(p -> ordinary(p, t.carry())).toList(),
            oldWhole.lookupCalls(),
            oldWhole.cpuCalls(),
            oldWhole.budgets(),
            oldWhole.afterInitial(),
            oldWhole.afterFinal(),
            oldWhole.post153(),
            overlay(oldWhole.expectedFinalBytes(), t.carry()),
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
