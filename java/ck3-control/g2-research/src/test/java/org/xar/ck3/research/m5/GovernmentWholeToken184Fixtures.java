package org.xar.ck3.research.m5;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.OrdinaryStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.Witness;

/** New whole174->182 replacement data; old181 supplies independent literal data.
 * Both model rounds were rejected. No target Java was read or run for this Book. */
public final class GovernmentWholeToken184Fixtures implements GovernmentWholeConcrete173WitnessApi.Book {
    private static final long IMAGE=0x140000000L,LOCK=0xe00000L,TABLE=0xe10000L;

    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentWholeRoot181Fixtures().witnesses().get(0);
        var old=base.whole();var oldPorts=old.ordinaryCalls();
        Map<Long,Integer> delta=new LinkedHashMap<>();
        qword(delta,IMAGE+0x5cbede8L,LOCK);dword(delta,LOCK,0);
        qword(delta,LOCK+0x48L,TABLE);dword(delta,LOCK+0x54L,0x165);
        qword(delta,TABLE+0x165L*8L,0x330000L);
        Map<Long,Integer> seed=map(old.memorySeed());seed.putAll(delta);
        Map<Long,Integer> end=new LinkedHashMap<>(old.expectedFinalBytes());end.putAll(delta);
        List<OrdinaryStep> calls=List.of(diag(oldPorts.get(1),oldPorts.get(0),delta),
                diag(oldPorts.get(3),oldPorts.get(2),delta));
        List<AtomicStep> atomics=new ArrayList<>(base.atomicSteps().subList(0,8));
        atomics.addAll(List.of(new AtomicStep(32,LOCK,2,0,2),new AtomicStep(32,LOCK,-2,2,0),
                base.atomicSteps().get(8),new AtomicStep(32,LOCK,2,0,2),
                new AtomicStep(32,LOCK,-2,2,0),base.atomicSteps().get(9)));
        var whole=new GovernmentWhole4798WitnessApi.Witness("whole184-two-real-token165-hits",
                old.entry(),memory(seed),old.gs58Bits(),old.initialCalls(),calls,old.lookupCalls(),old.cpuCalls(),
                old.budgets(),old.afterInitial(),old.afterFinal(),old.post153(),end,old.expectedResult(),old.failure());
        return List.of(new Witness(whole,base.m0HashMxcsrAt4FE(),base.m1HashMxcsrAt85E(),
                base.deepSteps(),atomics,base.gsSteps()));
    }
    private static OrdinaryStep diag(OrdinaryStep prior,OrdinaryStep lookup,Map<Long,Integer> delta) {
        Map<Long,Integer> before=new LinkedHashMap<>(prior.expectedMemoryBytes());before.putAll(delta);
        VolatileBits p=prior.expected().volatileBits(),incoming=lookup.expected().volatileBits();
        VolatileBits pre=new VolatileBits(p.raxBits(),p.rcxBits(),p.rdxBits(),p.r8Bits(),p.r9Bits(),p.r10Bits(),
                incoming.r11Bits(),incoming.xmm0(),incoming.xmm1(),incoming.xmm2(),
                incoming.xmm3(),incoming.xmm4(),incoming.xmm5());
        OpaqueCall call=new OpaqueCall(prior.expected().callSiteRva(),prior.expected().targetRva(),
                prior.expected().rspBits(),pre,prior.expected().nonvolatileBits());
        return new OrdinaryStep(call,before,prior.mutation(),prior.normalPost(),prior.unsupported());
    }
    private static Map<Long,Integer> map(MemorySeed seed) {
        Map<Long,Integer> out=new LinkedHashMap<>();
        for(SeedByte b:seed.bytes()) out.put(b.addressBits(),b.byteBits());return out;
    }
    private static MemorySeed memory(Map<Long,Integer> image) {
        return new MemorySeed(image.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList());
    }
    private static void qword(Map<Long,Integer> image,long address,long value) {
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(8*i))&255);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(8*i))&255);
    }
}
