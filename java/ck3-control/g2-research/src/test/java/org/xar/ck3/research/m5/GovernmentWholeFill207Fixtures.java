package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.LoopStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;

/** Independent cached240 originalfill state; model only builds the new whole overlay. */
public final class GovernmentWholeFill207Fixtures implements Book {
    private static final long I=0x140000000L,HEAP=0x72000000L,DEST=HEAP+0x10;
    private record Transcript(List<LoopStep> fill,TailStep third,Map<Long,Integer> additions) {
        private Transcript {fill=List.copyOf(fill);additions=Map.copyOf(additions);}
    }
    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeLeaf205Fixtures().witnesses().get(0);
        return List.of(build(base,transcript(base)));
    }
    private static boolean fill(CallStep c) {return c.expected().kind()==TargetKind.DIRECT_RVA
            &&c.expected().callSiteRva()==0x425b87cL&&c.expected().targetBits()==0x4226f10L;}
    private static Transcript transcript(Witness base) {
        CallStep input=base.crtEvents().stream().filter(e->e instanceof CallStep c&&fill(c)).map(e->(CallStep)e).findFirst().orElseThrow();
        TailStep oldThird=base.crtEvents().stream().filter(e->e instanceof TailStep t&&t.expected().jumpSiteRva()==0x4248062L)
                .map(e->(TailStep)e).findFirst().orElseThrow();
        Map<Long,Integer> additions=new LinkedHashMap<>();additions.put(I+0x5c5cbb0L,0xa1);
        qword(additions,I+0x542f0a8L,1L);
        List<LoopStep> fillLoops=new ArrayList<>();fillLoops.add(new LoopStep(0x4226f80L,HEAP+0x20));
        for(int j=0;j<6;j++)fillLoops.add(new LoopStep(0x4226fc0L,HEAP+0xa0+j*0x10L));
        VolatileBits entering=input.expected().volatileBits();
        // Originalfill: R11=DEST/RDX=0/XMM0zero; R10 and XMM1..5 retain the actual6000allocation post.
        // The later199 body rewrites allother representedGPR; thirdindexedbody rewrites RAX/RCX.
        Entry e=oldThird.expected().entry();VolatileBits ov=e.volatileBits();
        VolatileBits next=new VolatileBits(ov.raxBits(),ov.rcxBits(),0L,0x40L,HEAP,0L,DEST,
                new Bits128(0L,0L),entering.xmm1(),entering.xmm2(),entering.xmm3(),entering.xmm4(),entering.xmm5());
        TailStep third=new TailStep(new Tail(oldThird.expected().jumpSiteRva(),oldThird.expected().kind(),oldThird.expected().targetBits(),
                new Entry(e.imageBaseBits(),e.rspBits(),next,e.nonvolatileBits())),
                overlay(oldThird.expectedMemoryBefore(),additions),oldThird.mutation(),oldThird.normalPost());
        return new Transcript(fillLoops,third,additions);
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
        Map<Long,Integer> m=new LinkedHashMap<>();for(SeedByte b:old.bytes())m.put(b.addressBits(),b.byteBits());
        m.putAll(state);return new MemorySeed(m.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList());
    }
    private static void qword(Map<Long,Integer> m,long a,long v) {for(int j=0;j<8;j++)m.put(a+j,(int)(v>>>(j*8))&255);}
    private static Witness build(Witness base, Transcript t) {
        List<Event> newCrt = new ArrayList<>();
        for (Event e : base.crtEvents()) {
            if (e instanceof CallStep c && fill(c)) {
                newCrt.addAll(t.fill());
            } else if (e instanceof TailStep ts && ts.expected().jumpSiteRva() == 0x4248062L) {
                newCrt.add(t.third());
            } else {
                newCrt.add(crt(e, t.additions()));
            }
        }
        var oldWhole = base.legacy().whole();
        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole207-actualfill240",
            oldWhole.entry(),
            seed(oldWhole.memorySeed(), t.additions()),
            oldWhole.gs58Bits(),
            oldWhole.initialCalls().stream().map(p -> ordinary(p, t.additions())).toList(),
            oldWhole.ordinaryCalls().stream().map(p -> ordinary(p, t.additions())).toList(),
            oldWhole.lookupCalls(),
            oldWhole.cpuCalls(),
            oldWhole.budgets(),
            oldWhole.afterInitial(),
            oldWhole.afterFinal(),
            oldWhole.post153(),
            overlay(oldWhole.expectedFinalBytes(), t.additions()),
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
