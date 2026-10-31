package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.LinkedHashMap;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentWholeCrt189WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.Event;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.TailStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentWholeCrtTail191Fixtures implements Book {
    private static final long IMG = 0x140000000L;
    private static final long A1 = IMG + 0x5C5CB48L;
    private static final long A2 = IMG + 0x43DBBA8L;
    private static final long V1 = 0x100000000L;
    private static final long V2 = 0x9999000055556666L;

    @Override public List<Witness> witnesses() {
        var base = new GovernmentWholeCrt189Fixtures().witnesses().get(0);
        var legacy = base.legacy();
        var whole = legacy.whole();
        var crtEvents = base.crtEvents();

        Map<Long, Integer> seedMap = new LinkedHashMap<>();
        for (SeedByte b : whole.memorySeed().bytes()) seedMap.put(b.addressBits(), b.byteBits());
        addQword(seedMap, A1, V1);
        addQword(seedMap, A2, V2);
        var newSeed = new MemorySeed(seedMap.entrySet().stream().map(e -> new SeedByte(e.getKey(), e.getValue())).toList());

        List<OrdinaryStep> newInitial = whole.initialCalls().stream().map(s -> overlay(s)).toList();
        List<OrdinaryStep> newOrdinary = whole.ordinaryCalls().stream().map(s -> overlay(s)).toList();
        Map<Long, Integer> newFinal = new LinkedHashMap<>(whole.expectedFinalBytes());
        addQword(newFinal, A1, V1);
        addQword(newFinal, A2, V2);

        var newWhole = new GovernmentWhole4798WitnessApi.Witness(
            "whole191-tail190",
            whole.entry(),
            newSeed,
            whole.gs58Bits(),
            newInitial,
            newOrdinary,
            whole.lookupCalls(),
            whole.cpuCalls(),
            whole.budgets(),
            whole.afterInitial(),
            whole.afterFinal(),
            whole.post153(),
            newFinal,
            whole.expectedResult(),
            whole.failure()
        );

        var newLegacy = new GovernmentWholeConcrete173WitnessApi.Witness(
            newWhole,
            legacy.m0HashMxcsrAt4FE(),
            legacy.m1HashMxcsrAt85E(),
            legacy.deepSteps(),
            legacy.atomicSteps(),
            legacy.gsSteps()
        );

        List<Event> newCrt = crtEvents.stream().map(e -> transformEvent(e)).toList();
        return List.of(new Witness(newLegacy, newCrt));
    }

    private static OrdinaryStep overlay(OrdinaryStep s) {
        Map<Long, Integer> m = new LinkedHashMap<>(s.expectedMemoryBytes());
        addQword(m, A1, V1);
        addQword(m, A2, V2);
        return new OrdinaryStep(s.expected(), m, s.mutation(), s.normalPost(), s.unsupported());
    }

    private static Event transformEvent(Event e) {
        if (e instanceof CallStep cs) {
            Map<Long, Integer> m = new LinkedHashMap<>(cs.expectedMemoryBefore());
            addQword(m, A1, V1);
            addQword(m, A2, V2);
            return new CallStep(cs.expected(), m, cs.mutation(), cs.normalPost());
        } else if (e instanceof TailStep ts) {
            Map<Long, Integer> m = new LinkedHashMap<>(ts.expectedMemoryBefore());
            addQword(m, A1, V1);
            addQword(m, A2, V2);

            if (ts.expected().jumpSiteRva() == 0x4223A7FL &&
                ts.expected().kind() == TargetKind.DIRECT_RVA &&
                ts.expected().targetBits() == 0x4223AEC) {

                Entry oldEntry = ts.expected().entry();
                VolatileBits v = oldEntry.volatileBits();

                VolatileBits newV = new VolatileBits(
                    V1,
                    IMG + 0x5C5CB08L,
                    v.rdxBits(),
                    v.r8Bits(),
                    v.r9Bits(),
                    v.r10Bits(),
                    v.r11Bits(),
                    v.xmm0(),
                    v.xmm1(),
                    v.xmm2(),
                    v.xmm3(),
                    v.xmm4(),
                    v.xmm5()
                );

                Entry newEntry = new Entry(oldEntry.imageBaseBits(), oldEntry.rspBits(), newV, oldEntry.nonvolatileBits());
                Tail newTail = new Tail(0x4223B07L, TargetKind.INDIRECT_ABSOLUTE, V2, newEntry);

                return new TailStep(newTail, m, ts.mutation(), ts.normalPost());
            }

            return new TailStep(ts.expected(), m, ts.mutation(), ts.normalPost());
        }
        return e;
    }

    private static void addQword(Map<Long, Integer> m, long addr, long val) {
        for (int i = 0; i < 8; i++) m.put(addr + i, (int)(val >>> (i * 8)) & 255);
    }
}
