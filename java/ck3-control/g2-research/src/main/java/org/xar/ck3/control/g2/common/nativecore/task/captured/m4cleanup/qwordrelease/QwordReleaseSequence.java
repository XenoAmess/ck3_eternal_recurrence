package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.qwordrelease;

import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;
import java.util.List;

public final class QwordReleaseSequence {
    public record Slot(long fieldOffset, long globalRva) { }

    @FunctionalInterface
    public interface Calls {
        void call424E364(long knownRcxRaw);
    }

    private QwordReleaseSequence() { }

    public static void execute(long moduleBaseRaw, long objectRaw, B374Inputs.Memory memory, Calls calls, List<Slot> slots) {
        if (objectRaw == 0) {
            return;
        }
        for (Slot slot : slots) {
            long fieldAddr = objectRaw + slot.fieldOffset();
            long fieldVal = memory.readPointer(fieldAddr);
            long globalAddr = moduleBaseRaw + slot.globalRva();
            long globalVal = memory.readPointer(globalAddr);
            if (fieldVal != globalVal) {
                calls.call424E364(fieldVal);
            }
        }
    }
}
