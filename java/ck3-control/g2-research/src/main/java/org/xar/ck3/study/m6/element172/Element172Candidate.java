package org.xar.ck3.study.m6.element172;

public final class Element172Candidate {
    private Element172Candidate() { }
    public static long assign(Element172Inputs.Input input,Element172Inputs.Memory memory,Element172Inputs.Calls calls) {
        long d=input.destinationRaw64(),s=input.sourceRaw64(),image=input.imageBaseRaw64();
        memory.write64(d,image+0x45648a0L);
        memory.write32(d+0x08,memory.read32(s+0x08));
        memory.write64(d+0x18,0L);
        memory.write64(d+0x20,0L);
        memory.write64(d+0x10,0L);
        memory.write64(d+0x18,0L);
        memory.write64(d+0x20,image+0x54de260L);
        int count16=memory.read32(s+0x1c);
        long begin16=memory.read64(s+0x10);
        calls.copy16_8c70b0(d+0x10,0L,begin16,begin16+(long)count16*16L);
        memory.write64(d+0x30,0L);
        memory.write64(d+0x38,0L);
        memory.write64(d+0x28,0L);
        memory.write64(d+0x30,0L);
        memory.write64(d+0x38,image+0x54de268L);
        long begin4=memory.read64(s+0x28);
        int count4=memory.read32(s+0x34);
        calls.copy4_add0d0(d+0x28,0L,begin4,begin4+(long)count4*4L);
        memory.write32(d+0x40,memory.read32(s+0x40));
        memory.write8(d+0x44,memory.read8(s+0x44)&255);
        return d;
    }
}
