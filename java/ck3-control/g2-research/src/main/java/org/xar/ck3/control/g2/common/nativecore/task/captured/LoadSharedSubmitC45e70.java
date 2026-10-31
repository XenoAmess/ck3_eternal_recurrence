package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** C45E70 normal source projection. scratchHolderAddress is explicit caller-owned8B storage,
 * not a fabricated address of the original native RSP+30 local.
 * This is a normal-effects sub-contract, not a complete Native return ABI. */
public final class LoadSharedSubmitC45e70 {
    private LoadSharedSubmitC45e70() { }
    public interface Ports {
        void callC45ee0(long containerAddress, long holderAddress);
        /** Boundary owns vptr resolution plus invocation; caller doesn't add unused vptr reads. */
        void virtual0(long receiver, int flags);
    }
    public static void submit(long moduleBase, long holderAddress, long scratchHolderAddress, NativeTaskMemory memory, LoadSharedGetterC45df0.Ports getterPorts, Ports ports) {
        long m = LoadSharedGetterC45df0.get(moduleBase, memory, getterPorts);
        if (m != 0) {
            long o = memory.readPointer(holderAddress);
            memory.writeInt64(holderAddress, 0L);
            memory.writeInt64(scratchHolderAddress, o);
            ports.callC45ee0(m + 0x18L, scratchHolderAddress);
            long freshScratch = memory.readPointer(scratchHolderAddress);
            if (freshScratch != 0) {
                ports.virtual0(freshScratch, 1);
            }
        }
        long freshHolder = memory.readPointer(holderAddress);
        if (freshHolder != 0) {
            ports.virtual0(freshHolder, 1);
        }
    }
}
