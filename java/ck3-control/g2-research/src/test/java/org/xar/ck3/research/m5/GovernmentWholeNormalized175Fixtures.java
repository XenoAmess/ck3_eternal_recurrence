package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.Witness;

/**
 * One NEW concrete-normalizer path over the independent173 front oracle. Two rejected
 * model rounds preceded owner takeover. No target implementation was read or executed
 * to derive this Book. Opaque post153 remains an explicitly supplied observation.
 */
public final class GovernmentWholeNormalized175Fixtures implements GovernmentWholeConcrete173WitnessApi.Book {
    private static final long I=0x140000000L,G=0x600000L,S=0xbfecd0L,B=0xbfedd0L;

    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeConcrete173Fixtures().witnesses().get(0);
        GovernmentWhole4798WitnessApi.Witness old=base.whole();

        Map<Long,Integer> seed=new LinkedHashMap<>();
        for(SeedByte value:old.memorySeed().bytes()) seed.put(value.addressBits(),value.byteBits());
        seed.put(G+0x4d6L,5);
        dword(seed,G+0x4ccL,0x2d);
        dword(seed,G+0x4c8L,0x2e);
        MemorySeed newSeed=new MemorySeed(seed.entrySet().stream()
                .map(e->new SeedByte(e.getKey(),e.getValue())).toList());

        // Both reachable tag5 bodies take30A2CE9->30A2EB5. The second real return
        // preserves carried R9/R10/R11/XMM1..5 instead of applying removed mockN2.
        VolatileBits joinedV=new VolatileBits(0x2eL,G,B+0x1b0L,0x2eL,0L,0x780000L,0xfffffffeL,
                new Bits128(0x1446d97e8L,0xc6c6c6000000001bL),
                new Bits128(0x110L,0x111L),new Bits128(0x120L,0x121L),
                new Bits128(0x130L,0x131L),new Bits128(0x140L,0x141L),new Bits128(0x150L,0x151L));
        GovernmentMiddle166Api.Result oldMiddle=old.expectedResult().middleResult();
        GovernmentPreprefix159Api.Join oldJoin=oldMiddle.joinedResult().actualJoin();
        GovernmentPreprefix159Api.Join newJoin=new GovernmentPreprefix159Api.Join(
                oldJoin.nextRva(),oldJoin.imageBaseBits(),oldJoin.frameRspBits(),joinedV,
                oldJoin.nonvolatileBits());
        GovernmentJoined159Api.Result joined=new GovernmentJoined159Api.Result(newJoin,
                oldMiddle.joinedResult().suffixResult());
        GovernmentMiddle166Api.Result middle=new GovernmentMiddle166Api.Result(
                oldMiddle.compactionJoin(),oldMiddle.preludeEntry(),joined);
        GovernmentWhole4798Api.Result oldResult=old.expectedResult();
        GovernmentWhole4798Api.Result result=new GovernmentWhole4798Api.Result(
                oldResult.initialJoin(),oldResult.afterInitialMxcsr(),oldResult.lookupJoin(),
                oldResult.earlierJoin(),oldResult.rowsJoin(),middle,oldResult.finalMxcsr());
        GovernmentWhole4798WitnessApi.FinalMxcsrStep afterFinal=
                new GovernmentWhole4798WitnessApi.FinalMxcsrStep(middle,old.afterFinal().observation());

        Map<Long,Integer> end=new LinkedHashMap<>(old.expectedFinalBytes());
        end.put(G+0x4d6L,5);
        dword(end,G+0x4ccL,0x2d);
        dword(end,G+0x4c8L,0x2e);
        // Outer CALL pushes and both full-normalizer prologues share these bytes.
        qword(end,S-8L,I+0x30a3eaaL);
        qword(end,S,0L);
        qword(end,S+8L,G+0x18L);
        qword(end,S-0x10L,G);

        GovernmentWhole4798WitnessApi.Witness whole=new GovernmentWhole4798WitnessApi.Witness(
                "whole175-real-normalizers-tag5-pass2d-pass2e",old.entry(),newSeed,old.gs58Bits(),
                old.initialCalls(),List.of(),old.lookupCalls(),old.cpuCalls(),old.budgets(),
                old.afterInitial(),afterFinal,old.post153(),end,result,old.failure());
        return List.of(new Witness(whole,base.m0HashMxcsrAt4FE(),base.m1HashMxcsrAt85E(),
                base.deepSteps(),base.atomicSteps(),base.gsSteps()));
    }

    private static void qword(Map<Long,Integer> image,long address,long value) {
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(8*i))&255);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(8*i))&255);
    }
}
