package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374;

/** Complete finite normal effects; every lower call remains an opaque effect. */
public final class B374Candidate {
    private B374Candidate() { }

    public static void execute(B374Inputs.CallInput input, B374Inputs.Memory memory,
            B374Inputs.Calls calls) {
        long object = input.objectRaw();
        long first = memory.readPointer(object + 0xf8);
        if (first != 0 && first != input.moduleBaseRaw() + 0x542f220L) {
            long e0 = memory.readPointer(object + 0xe0);
            if (e0 != 0 && memory.readInt32(e0) == 0) {
                long f0 = memory.readPointer(object + 0xf0);
                if (f0 != 0 && memory.readInt32(f0) == 0) {
                    calls.call424E364(f0);
                    calls.call42552D0(memory.readPointer(object + 0xf8));
                }
                long e8 = memory.readPointer(object + 0xe8);
                if (e8 != 0 && memory.readInt32(e8) == 0) {
                    calls.call424E364(e8);
                    calls.call4255910(memory.readPointer(object + 0xf8));
                }
                calls.call424E364(memory.readPointer(object + 0xe0));
                calls.call424E364(memory.readPointer(object + 0xf8));
            }
        }
        long at100 = memory.readPointer(object + 0x100);
        if (at100 != 0 && memory.readInt32(at100) == 0) {
            calls.call424E364(memory.readPointer(object + 0x108) - 0xfeL);
            calls.call424E364(memory.readPointer(object + 0x110) - 0x80L);
            calls.call424E364(memory.readPointer(object + 0x118) - 0x80L);
            calls.call424E364(memory.readPointer(object + 0x100));
        }
        calls.call425689C(memory.readPointer(object + 0x120));
        long element = object + 0x38;
        long parallel = object + 0x128;
        for (int index = 0; index < 6; index++) {
            if (memory.readPointer(element - 0x10) != input.moduleBaseRaw() + 0x542f498L) {
                long pointer = memory.readPointer(element);
                if (pointer != 0 && memory.readInt32(pointer) == 0) {
                    calls.call424E364(pointer);
                    calls.call424E364(memory.readPointer(parallel));
                }
            }
            if (memory.readPointer(element - 0x18) != 0) {
                long pointer = memory.readPointer(element - 8);
                if (pointer != 0 && memory.readInt32(pointer) == 0) {
                    calls.call424E364(pointer);
                }
            }
            parallel += 8;
            element += 0x20;
        }
        calls.tail424E364(object);
    }
}
