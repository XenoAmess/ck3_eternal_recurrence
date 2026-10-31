package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower54;

public final class Lower54Candidate {
    private Lower54Candidate() { }

    public static void execute(Lower54Inputs.CallInput input, Lower54Inputs.Memory memory,
            Lower54Inputs.Calls calls) {
        long object = input.objectRaw();
        if (object == 0 || object == input.moduleBaseRaw() + 0x44271d0L) {
            return;
        }
        if (memory.readInt32(object + 0x15c) != 0) {
            return;
        }
        calls.call4255FFC(object);
        calls.call424E364(object);
    }
}
