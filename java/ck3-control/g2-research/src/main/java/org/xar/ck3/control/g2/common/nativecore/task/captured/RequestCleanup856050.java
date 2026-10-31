package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.StorageCleanupFree83Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls;

public final class RequestCleanup856050 {
    private RequestCleanup856050() { }

    public static StorageCleanupFree83Consumer.Outcome cleanup(
            long storage, long heapHandleRaw, RequestE92780.Memory memory, Calls calls) {
        long capacityBits = memory.readPointer(storage + 0x18L);
        OptionalLong heapPointerBits = OptionalLong.empty();
        OptionalLong backReferenceBits = OptionalLong.empty();

        if (Long.compareUnsigned(capacityBits, 16) >= 0) {
            heapPointerBits = OptionalLong.of(memory.readPointer(storage));
            long P = heapPointerBits.getAsLong();
            long S = capacityBits + 1;
            if (Long.compareUnsigned(S, 4096) >= 0) {
                backReferenceBits = OptionalLong.of(memory.readPointer(P - 8));
            }
        }

        StorageCleanupFree83Consumer.ResetSink sink = new StorageCleanupFree83Consumer.ResetSink() {
            @Override
            public void store(int offsetFromD, int byteWidth, long valueBits) {
                if (byteWidth == 8) {
                    memory.writeInt64(storage + offsetFromD, valueBits);
                } else if (byteWidth == 1) {
                    memory.writeByte(storage + offsetFromD, (byte)valueBits);
                }
            }
        };

        return StorageCleanupFree83Consumer.cleanup(capacityBits, heapPointerBits, backReferenceBits, heapHandleRaw, calls, sink);
    }
}