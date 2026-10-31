package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.LoopStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentWholeRep208WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeRep208WitnessApi.ExpectedAdmission;

/** Independent realREP240/domain admission data; no target208/Rep207 implementation read. */
public final class GovernmentWholeRep208Fixtures implements Book {
    private static final long I=0x140000000L,DEST=0x72000010L;
    @Override public List<GovernmentWholeRep208WitnessApi.Witness> witnesses() {
        Witness old=new GovernmentWholeFill207Fixtures().witnesses().get(0);
        Map<Long,Integer> feature=Map.of(I+0x5c5cbb0L,0xa3);
        List<LoopStep> rep=new ArrayList<>();for(int j=0;j<240;j++)rep.add(new LoopStep(0x4226ef9L,DEST+j));
        Witness context=build(old,rep,feature);
        return List.of(new GovernmentWholeRep208WitnessApi.Witness("whole208-forward240",context,false,ExpectedAdmission.NORMAL),
                new GovernmentWholeRep208WitnessApi.Witness("whole208-dfset-admission",context,true,ExpectedAdmission.DF_SET_UNSUPPORTED));
    }
    private static boolean cached(Event e) {return e instanceof LoopStep s
            &&(s.loopHeaderRva()==0x4226f80L || s.loopHeaderRva()==0x4226fc0L);}
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
        Map<Long,Integer> bytes=new LinkedHashMap<>();for(SeedByte b:old.bytes())bytes.put(b.addressBits(),b.byteBits());
        bytes.putAll(state);return new MemorySeed(bytes.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList());
    }
    private static Witness build(Witness base, List<LoopStep> rep, Map<Long, Integer> feature) {
        List<Event> newCrt = new ArrayList<>();
        boolean inserted = false;
        for (Event e : base.crtEvents()) {
            if (cached(e)) {
                if (!inserted) {
                    newCrt.addAll(rep);
                    inserted = true;
                }
            } else {
                newCrt.add(crt(e, feature));
            }
        }
        var oldWhole = base.legacy().whole();
        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole208-actual-rep240",
            oldWhole.entry(),
            seed(oldWhole.memorySeed(), feature),
            oldWhole.gs58Bits(),
            oldWhole.initialCalls().stream().map(p -> ordinary(p, feature)).toList(),
            oldWhole.ordinaryCalls().stream().map(p -> ordinary(p, feature)).toList(),
            oldWhole.lookupCalls(),
            oldWhole.cpuCalls(),
            oldWhole.budgets(),
            oldWhole.afterInitial(),
            oldWhole.afterFinal(),
            oldWhole.post153(),
            overlay(oldWhole.expectedFinalBytes(), feature),
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
