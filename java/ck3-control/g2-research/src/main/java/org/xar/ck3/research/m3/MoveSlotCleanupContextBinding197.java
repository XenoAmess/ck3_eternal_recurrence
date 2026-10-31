package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;

public final class MoveSlotCleanupContextBinding197 implements MoveSlotApi193.Ports {
    private final long moduleBase;
    private final CleanupContext197Api.Memory capturedMemory;
    private final Lower61Inputs.Calls lowerCalls;

    private MoveSlotCleanupContextBinding197(long moduleBase, CleanupContext197Api.Memory capturedMemory,
                                             Lower61Inputs.Calls lowerCalls) {
        this.moduleBase = moduleBase;
        this.capturedMemory = capturedMemory;
        this.lowerCalls = lowerCalls;
    }

    public static MoveSlotCleanupContextBinding197 bind(long moduleBase,
        CleanupContext197Api.Memory capturedMemory, Lower61Inputs.Calls lowerCalls) {
        return new MoveSlotCleanupContextBinding197(moduleBase, capturedMemory, lowerCalls);
    }

    @Override
    public void call856050(RequestE92780.Memory memory, long descriptor) {
        if (memory != capturedMemory) {
            throw new IllegalArgumentException("Memory identity mismatch");
        }
        CleanupContext197Api.Result result = CleanupContext197.execute(moduleBase, descriptor, capturedMemory, lowerCalls);
        if (result.completion() == CleanupContext197Api.Completion.UNSUPPORTED_ERROR_BRANCH) {
            throw new IllegalStateException("UNSUPPORTED_ERROR_BRANCH");
        }
    }
}