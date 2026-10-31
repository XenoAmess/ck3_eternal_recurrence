package org.xar.ck3.study.m6.element150;

public final class Element150Candidate {
    public static long copy(Element150Inputs.Input input, Element150Inputs.Memory mem, Element150Inputs.Calls calls) {
        long d = input.destinationRaw64();
        long s = input.sourceRaw64();
        long img = input.imageBaseRaw64();

        mem.write64(d, img + 0x45648A0L);

        int val8 = mem.read32(s + 8);
        mem.write32(d + 8, val8);

        long h1 = d + 0x10;
        mem.write64(h1, 0L);
        mem.write64(h1 + 8, 0L);
        mem.write64(h1 + 16, img + 0x54DE260L);

        calls.copy16_21a5050(h1, s + 0x10);

        long h2 = d + 0x28;
        mem.write64(h2, 0L);
        mem.write64(h2 + 8, 0L);
        mem.write64(h2 + 16, img + 0x54DE268L);

        calls.copy4_b2eee0(h2, s + 0x28);

        int val40 = mem.read32(s + 0x40);
        mem.write32(d + 0x40, val40);

        int val44 = mem.read8(s + 0x44);
        mem.write8(d + 0x44, val44);

        return d;
    }
}