package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentLookupHelper176Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentLookupHelper176WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * ONE new176->real178 hot-root literal witness. Owner takeover after two rejected
 * model rounds. Neither target Java core was read or run to construct this oracle.
 * The old176 Book contributes independent input/hash constants, never a subject run.
 */
public final class GovernmentLookupWithRoot179Fixtures implements Book {
    @Override public List<Witness> witnesses() {
        Witness old=new GovernmentLookupHelper176Fixtures().witnesses().get(1);
        Map<Long,Integer> seed=new LinkedHashMap<>();
        for(SeedByte value:old.memorySeed()) seed.put(value.addressBits(),value.byteBits());
        dword(seed,0x145dc11c0L,0xffffffff);
        qword(seed,0x145dc11d8L,0xb00000L);
        qword(seed,0x145dc11e8L,0xa00000L);
        qword(seed,0x145dc1200L,3L);
        qword(seed,0xc00000L,0xc10000L);
        dword(seed,0xc10010L,0x7fffffff);

        // Root178 signed hot branch changes onlyRAX/RCX/RDX and performs no CALL
        // or Memory write. Helper176 then executes the unchanged fixed-key hash/hit.
        VolatileBits entryV=old.entry().volatileBits();
        VolatileBits finalV=new VolatileBits(0xb10018L,0xb30000L,0xb00000L,
                0x8381a92307066c15L,0x145dc11d0L,0x100000001b3L,entryV.r11Bits(),
                entryV.xmm0(),entryV.xmm1(),entryV.xmm2(),entryV.xmm3(),entryV.xmm4(),entryV.xmm5());
        Map<Long,Integer> end=new LinkedHashMap<>(seed);
        dword(end,0x800010L,0xa1b2c3d4);
        qword(end,0x800000L,0xb000L);
        qword(end,0x7fffd8L,0x143f5f980L);
        NormalReturn expected=new NormalReturn(finalV,0x123456789abcdef0L,0x800010L,
                old.entry().nonvolatileBits());
        return List.of(new Witness("lookup179-real-root-hot-first-key-hit",old.entry(),bytes(seed),
                List.of(),List.of(0xc00000L),List.of(),List.of(),end,expected));
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
