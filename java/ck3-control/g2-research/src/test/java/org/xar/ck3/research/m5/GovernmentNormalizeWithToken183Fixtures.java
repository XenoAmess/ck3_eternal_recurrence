package org.xar.ck3.research.m5;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.Book;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentNormalizeFull174WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** New174->actual182 table-hit literal, followed by174's TLS-blocked branch.
 * The old Book supplies independent input/stack data, never a subject execution.
 * Both model rounds were rejected; owner derived this delta from the held ASM. */
public final class GovernmentNormalizeWithToken183Fixtures implements Book {
    @Override public List<Witness> witnesses() {
        Witness base=new GovernmentNormalizeFull174Fixtures().witnesses().get(1);
        Map<Long,Integer> delta=new LinkedHashMap<>();
        qword(delta,base.entry().imageBaseBits()+0x5cbede8L,0xe00000L);
        dword(delta,0xe00000L,0);
        qword(delta,0xe00048L,0xe10000L);
        dword(delta,0xe00054L,0x2807);
        qword(delta,0xe10000L+0x2807L*8L,0x330000L);

        Map<Long,Integer> seed=new LinkedHashMap<>();
        for(SeedByte b:base.memorySeed()) seed.put(b.addressBits(),b.byteBits());
        seed.putAll(delta);
        // The unchanged174 prologue and outer CALL are independently literal here.
        // Actual182 only updates lockDWORD0->2->0; it makes no further CALL or save.
        Map<Long,Integer> end=new LinkedHashMap<>(base.expectedFinalBytes());
        end.putAll(delta);

        VolatileBits incoming=base.entry().volatileBits();
        VolatileBits finalV=new VolatileBits(3L,0x500000L,0x600000L,0x158L,
                0x330000L,incoming.r10Bits(),incoming.r11Bits(),
                incoming.xmm0(),incoming.xmm1(),incoming.xmm2(),
                incoming.xmm3(),incoming.xmm4(),incoming.xmm5());
        NormalReturn expected=new NormalReturn(finalV,base.expected().returnRipBits(),
                base.expected().callerRspBits(),base.entry().nonvolatileBits());
        return List.of(new Witness("actual-token2807-hit-then-normalizer-tls-block",base.entry(),
                bytes(seed),List.of(),base.gsQword58(),
                List.of(new AtomicStep(0xe00000L,2,0,2),new AtomicStep(0xe00000L,-2,2,0)),
                end,expected));
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
