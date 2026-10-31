package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower264;

public final class Lower264Candidate {
    private Lower264Candidate() { }

    public static void execute(Lower264Inputs.CallInput input, Lower264Inputs.Memory memory, Lower264Inputs.Calls calls) {
        long rbx = input.objectRaw();
        if (rbx == 0) return;
        long rbp = 7;
        long rsi = 0;
        long edx;
        long rcx;

        // 0x4256019: mov rbx, rcx (rbx already set)
        // 0x425601c: mov edx, ebp
        edx = rbp;
        // 0x425601e: call 0x4255c64
        calls.call4255C64(rbx, edx);

        // 0x4256023: lea rcx, [rbx + 0x38]
        rcx = rbx + 0x38;
        // 0x4256027: mov edx, ebp
        edx = rbp;
        // 0x4256029: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x425602e: lea esi, [rbp + 5]
        rsi = rbp + 5;
        // 0x4256031: mov edx, esi
        edx = rsi;
        // 0x4256033: lea rcx, [rbx + 0x70]
        rcx = rbx + 0x70;
        // 0x4256037: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x425603c: lea rcx, [rbx + 0xd0]
        rcx = rbx + 0xd0;
        // 0x4256043: mov edx, esi
        edx = rsi;
        // 0x4256045: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x425604a: lea rcx, [rbx + 0x130]
        rcx = rbx + 0x130;
        // 0x4256051: lea edx, [rbp - 5]
        edx = rbp - 5;
        // 0x4256054: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x4256059: mov rcx, qword ptr [rbx + 0x140]
        rcx = memory.readPointer(rbx + 0x140);
        // 0x4256060: call 0x424e364
        calls.call424E364(rcx);

        // 0x4256065: mov rcx, qword ptr [rbx + 0x148]
        rcx = memory.readPointer(rbx + 0x148);
        // 0x425606c: call 0x424e364
        calls.call424E364(rcx);

        // 0x4256071: mov rcx, qword ptr [rbx + 0x150]
        rcx = memory.readPointer(rbx + 0x150);
        // 0x4256078: call 0x424e364
        calls.call424E364(rcx);

        // 0x425607d: lea rcx, [rbx + 0x160]
        rcx = rbx + 0x160;
        // 0x4256084: mov edx, ebp
        edx = rbp;
        // 0x4256086: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x425608b: lea rcx, [rbx + 0x198]
        rcx = rbx + 0x198;
        // 0x4256092: mov edx, ebp
        edx = rbp;
        // 0x4256094: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x4256099: lea rcx, [rbx + 0x1d0]
        rcx = rbx + 0x1d0;
        // 0x42560a0: mov edx, esi
        edx = rsi;
        // 0x42560a2: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x42560a7: lea rcx, [rbx + 0x230]
        rcx = rbx + 0x230;
        // 0x42560ae: mov edx, esi
        edx = rsi;
        // 0x42560b0: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x42560b5: lea rcx, [rbx + 0x290]
        rcx = rbx + 0x290;
        // 0x42560bc: lea edx, [rbp - 5]
        edx = rbp - 5;
        // 0x42560bf: call 0x4255c64
        calls.call4255C64(rcx, edx);

        // 0x42560c4: mov rcx, qword ptr [rbx + 0x2a0]
        rcx = memory.readPointer(rbx + 0x2a0);
        // 0x42560cb: call 0x424e364
        calls.call424E364(rcx);

        // 0x42560d0: mov rcx, qword ptr [rbx + 0x2a8]
        rcx = memory.readPointer(rbx + 0x2a8);
        // 0x42560d7: call 0x424e364
        calls.call424E364(rcx);

        // 0x42560dc: mov rcx, qword ptr [rbx + 0x2b0]
        rcx = memory.readPointer(rbx + 0x2b0);
        // 0x42560e3: call 0x424e364
        calls.call424E364(rcx);

        // 0x42560e8: mov rcx, qword ptr [rbx + 0x2b8]
        rcx = memory.readPointer(rbx + 0x2b8);
        // 0x42560ef: call 0x424e364
        calls.call424E364(rcx);
    }
}