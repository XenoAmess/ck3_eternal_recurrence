package org.xar.ck3.research.m5;

import java.util.ArrayList;
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

public final class GovernmentNormalizeWithRoot180Fixtures implements Book {
    @Override public List<Witness> witnesses() {
        Witness old = new GovernmentNormalizeWithHelper177Fixtures().witnesses().get(0);
        Map<Long, Integer> additions = new LinkedHashMap<>();
        dword(additions, 0x145dc11c0L, 0xffffffff);
        qword(additions, 0x145dc11d8L, 0xb00000L);
        qword(additions, 0x145dc11e8L, 0xa00000L);
        qword(additions, 0x145dc1200L, 0x3L);
        qword(additions, 0xc00000L, 0xc10000L);
        dword(additions, 0xc10010L, 0x7fffffff);

        Map<Long, Integer> seed = new LinkedHashMap<>();
        for (SeedByte value : old.memorySeed()) seed.put(value.addressBits(), value.byteBits());
        seed.putAll(additions);

        CallStep oldLookup = old.calls().get(0);
        Map<Long, Integer> lookupBefore = new LinkedHashMap<>(oldLookup.expectedMemoryBefore());
        lookupBefore.putAll(additions);
        CallStep lookup = new CallStep(oldLookup.expected(), lookupBefore, oldLookup.mutation(), oldLookup.normalPost());

        CallStep oldDiag = old.calls().get(2);
        VolatileBits lookupPost = oldLookup.normalPost();
        VolatileBits oldDiagPre = oldDiag.expected().volatileBits();
        VolatileBits diagPre = new VolatileBits(
            0x440000L, 0x440000L, 0x1448b7a48L, 0x12cL,
            0x145dc11d0L, 0x100000001b3L, lookupPost.r11Bits(),
            lookupPost.xmm0(), lookupPost.xmm1(), lookupPost.xmm2(),
            lookupPost.xmm3(), lookupPost.xmm4(), lookupPost.xmm5()
        );
        Map<Long, Integer> diagBefore = new LinkedHashMap<>(oldDiag.expectedMemoryBefore());
        diagBefore.putAll(additions);
        CallStep diag = new CallStep(new OpaqueCall(oldDiag.expected().callSiteRva(), oldDiag.expected().targetRva(), oldDiag.expected().rspBits(), diagPre, oldDiag.expected().nonvolatileBits()), diagBefore, oldDiag.mutation(), oldDiag.normalPost());

        Map<Long, Integer> end = new LinkedHashMap<>(old.expectedFinalBytes());
        end.putAll(additions);

        List<Long> gs = new ArrayList<>(old.gsQword58());
        gs.add(0xc00000L);

        return List.of(new Witness("normalize180-real-root-hot", old.entry(), bytes(seed), List.of(lookup, diag), gs, old.atomics(), end, old.expected()));
    }

    private static Map<Long, Integer> merge(Map<Long, Integer> base, Map<Long, Integer> additions) {
        Map<Long, Integer> out = new LinkedHashMap<>(base);
        out.putAll(additions);
        return out;
    }

    private static List<SeedByte> bytes(Map<Long, Integer> image) {
        return image.entrySet().stream().map(e -> new SeedByte(e.getKey(), e.getValue())).toList();
    }

    private static void qword(Map<Long, Integer> image, long address, long value) {
        for (int i = 0; i < 8; i++) image.put(address + i, (int)(value >>> (8 * i)) & 255);
    }
    private static void dword(Map<Long, Integer> image, long address, int value) {
        for (int i = 0; i < 4; i++) image.put(address + i, (value >>> (8 * i)) & 255);
    }

}
