package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadSharedGetterC45df0;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRuntime4260e74;

public final class LoadSharedRuntimeConsumer {
    public static LoadSharedGetterC45df0.Ports ports(long moduleBase, NativeTaskMemory memory, LoadRuntime4260e74.Ports runtimePorts) {
        return new LoadSharedGetterC45df0.Ports() {
            @Override
            public long call4260e74(long objectPointer, int adjustmentBits, long sourceToken, long targetToken, int failureModeBits) {
                return LoadRuntime4260e74.execute(moduleBase, objectPointer, adjustmentBits, sourceToken, targetToken, failureModeBits, memory, runtimePorts);
            }
        };
    }
}
