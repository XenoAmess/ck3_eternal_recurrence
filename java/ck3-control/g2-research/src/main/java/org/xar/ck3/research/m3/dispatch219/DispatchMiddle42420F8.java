package org.xar.ck3.research.m3.dispatch219;

import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;

/** Normal 187B supplied-storage effects only; no CPU/stack/RET/NV/DF/EH projection. */
public final class DispatchMiddle42420F8 {
    private DispatchMiddle42420F8() { }

    public static void execute(DispatchMiddle219Api.Memory memory, DispatchMiddle219Api.Ports ports, DispatchMiddle219Api.Input input) {
        long base = input.moduleBase();
        long p = input.rcxAddress();

        // 4242101: freshR8(base+5C5D2E8); if nonzero, ordinary voidreturn with no further effects.
        int flag = memory.readUnsigned8(base + 0x5C5D2E8L);
        if (flag != 0) {
            return;
        }

        // 4242113: exchange32(base+5C5D2DC,1).
        memory.exchangeInt32(base + 0x5C5D2DCL, 1);

        // 4242119: freshR64(P), then 424211C freshR32(observedptr)=firstDWORD.
        long observedPtr = memory.readPointer(p);
        int firstDWORD = memory.readInt32(observedPtr);

        if (firstDWORD == 0) {
            // 4242122: freshR64(base+542F0B8)=A; 424212E: freshR64(base+5C5D2E0)=B.
            long a = memory.readPointer(base + 0x542F0B8L);
            long b = memory.readPointer(base + 0x5C5D2E0L);

            // 4242138: JE 424214D. If B==A, skip decode/IAT-read/CALL entirely.
            if (b != a) {
                // 424213A: xor rax,rdx
                long xor = a ^ b;
                // 424213D: ror rax,cl (count = A low6)
                int count = (int) (a & 0x3FL);
                long decoded = (xor >>> count) | (xor << (64 - count));

                // 4242147: freshR64(base+43DBBA8) is ACTUAL indirectcode target.
                long actualTarget = memory.readPointer(base + 0x43DBBA8L);

                // Invoke typed call43dbba8(memory, site4242147, actualTarget, decoded, 0, 0, 0).
                ports.call43dbba8(memory, 0x4242147L, actualTarget, decoded, 0, 0, 0);
            }

            // Regardless B==A or callback returned, call424de88(memory, site4242162, base+5C5D698).
            ports.call424de88(memory, 0x4242162L, base + 0x5C5D698L);
        } else if (firstDWORD == 1) {
            // call424de88(memory, site4242162, base+5C5D6B0).
            ports.call424de88(memory, 0x4242162L, base + 0x5C5D6B0L);
        }
        // Otherwise no DE88.

        // 4242168: freshR64(P) AGAIN after callbacks, then 424216B freshR32(observedptr).
        long observedPtr2 = memory.readPointer(p);
        int secondDWORD = memory.readInt32(observedPtr2);

        if (secondDWORD == 0) {
            // call424e1ac(memory, site424217E, base+441ED48, base+441ED70).
            ports.call424e1ac(memory, 0x424217EL, base + 0x441ED48L, base + 0x441ED70L);
        }

        // 4242191: unconditional call424e1ac(memory, site4242191, base+441ED78, base+441ED80) on every path that reached 4242168.
        ports.call424e1ac(memory, 0x4242191L, base + 0x441ED78L, base + 0x441ED80L);

        // 4242196: freshR64(P+8), 424219A freshR32(observedptr); if nonzero voidreturn.
        long observedPtr3 = memory.readPointer(p + 8L);
        int thirdDWORD = memory.readInt32(observedPtr3);
        if (thirdDWORD != 0) {
            return;
        }

        // 424219F: W8(base+5C5D2E8, 1).
        memory.write8(base + 0x5C5D2E8L, 1);

        // 42421A6: freshR64(P+0x10).
        long observedPtr4 = memory.readPointer(p + 0x10L);

        // 42421AA: W8(observedptr, 1).
        memory.write8(observedPtr4, 1);
    }
}