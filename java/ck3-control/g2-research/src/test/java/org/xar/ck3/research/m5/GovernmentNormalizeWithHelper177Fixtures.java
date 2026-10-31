package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * ONE new nested174->176 literal software witness. Two rejected model rounds preceded
 * owner takeover. Neither target Java core was read or run to derive this oracle.
 * Existing lookup/diag post vectors remain explicit artificial owned inputs.
 */
public final class GovernmentNormalizeWithHelper177Fixtures implements Book {
    @Override public List<Witness> witnesses() {
        Witness old=new GovernmentNormalizeFull174Fixtures().witnesses().get(2);
        CallStep oldLookup=old.calls().get(0),oldHelper=old.calls().get(1),oldDiag=old.calls().get(2);
        Map<Long,Integer> context=context();
        Map<Long,Integer> seed=new LinkedHashMap<>();
        for(SeedByte value:old.memorySeed()) seed.put(value.addressBits(),value.byteBits());
        seed.putAll(context);

        CallStep lookup=new CallStep(oldLookup.expected(),merge(oldLookup.expectedMemoryBefore(),context),
                oldLookup.mutation(),oldLookup.normalPost());
        NonvolatileBits parent=oldHelper.expected().nonvolatileBits();
        NonvolatileBits innerNv=new NonvolatileBits(0x10000L,parent.rbpBits(),parent.rsiBits(),
                parent.rdiBits(),parent.r12Bits(),parent.r13Bits(),parent.r14Bits(),parent.r15Bits(),parent.xmm6());
        VolatileBits supplied=oldHelper.normalPost();
        VolatileBits innerPost=new VolatileBits(0x900000L,supplied.rcxBits(),supplied.rdxBits(),
                supplied.r8Bits(),supplied.r9Bits(),supplied.r10Bits(),supplied.r11Bits(),
                supplied.xmm0(),supplied.xmm1(),supplied.xmm2(),supplied.xmm3(),supplied.xmm4(),supplied.xmm5());
        Map<Long,Integer> innerBefore=merge(oldHelper.expectedMemoryBefore(),context);
        helperWrites(innerBefore);
        CallStep inner=new CallStep(new OpaqueCall(0x3f5f97bL,0x3f5c090L,0x6fff90L,
                oldHelper.expected().volatileBits(),innerNv),innerBefore,List.of(),innerPost);

        VolatileBits oldPre=oldDiag.expected().volatileBits();
        VolatileBits diagPre=new VolatileBits(oldPre.raxBits(),oldPre.rcxBits(),oldPre.rdxBits(),
                oldPre.r8Bits(),0x900000L,0x100000001b3L,oldPre.r11Bits(),
                oldPre.xmm0(),oldPre.xmm1(),oldPre.xmm2(),oldPre.xmm3(),oldPre.xmm4(),oldPre.xmm5());
        Map<Long,Integer> diagBefore=merge(oldDiag.expectedMemoryBefore(),context);
        helperWrites(diagBefore);
        OpaqueCall oldCall=oldDiag.expected();
        CallStep diag=new CallStep(new OpaqueCall(oldCall.callSiteRva(),oldCall.targetRva(),oldCall.rspBits(),
                diagPre,oldCall.nonvolatileBits()),diagBefore,oldDiag.mutation(),oldDiag.normalPost());
        Map<Long,Integer> end=merge(old.expectedFinalBytes(),context);
        helperWrites(end);
        return List.of(new Witness("normalize177-real-helper-first-key-hit",old.entry(),bytes(seed),
                List.of(lookup,inner,diag),old.gsQword58(),old.atomics(),end,old.expected()));
    }

    private static Map<Long,Integer> context() {
        Map<Long,Integer> out=new LinkedHashMap<>();
        qword(out,0x900008L,0xb00000L);
        qword(out,0x900018L,0xa00000L);
        qword(out,0x900030L,3L);
        for(int bucket=0;bucket<4;bucket++) {
            qword(out,0xa00000L+bucket*16L,0xb30000L);
            qword(out,0xa00008L+bucket*16L,0x43ffe8L);
        }
        dword(out,0x43fff8L,0x10000);
        return out;
    }
    private static void helperWrites(Map<Long,Integer> image) {
        dword(image,0x6fffc0L,0x10000);
        qword(image,0x6fffb0L,0x100018L);
        qword(image,0x6fff88L,0x143f5f980L);
    }
    private static Map<Long,Integer> merge(Map<Long,Integer> base,Map<Long,Integer> additions) {
        Map<Long,Integer> out=new LinkedHashMap<>(base);out.putAll(additions);return out;
    }
    private static List<SeedByte> bytes(Map<Long,Integer> image) {
        return image.entrySet().stream().map(e->new SeedByte(e.getKey(),e.getValue())).toList();
    }
    private static void qword(Map<Long,Integer> image,long address,long value) {
        for(int i=0;i<8;i++) image.put(address+i,(int)(value>>>(8*i))&255);
    }
    private static void dword(Map<Long,Integer> image,long address,int value) {
        for(int i=0;i<4;i++) image.put(address+i,(value>>>(8*i))&255);
    }
}
