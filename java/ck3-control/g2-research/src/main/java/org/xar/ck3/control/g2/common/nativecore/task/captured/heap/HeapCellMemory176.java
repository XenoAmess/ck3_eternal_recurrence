package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs.HeapCell64;

/** Exact-width address operations for supplied storage; no process attachment. */
public final class HeapCellMemory176 implements NativeTaskMemory {
    private final long moduleBase;
    private final HeapCell64 heap;

    public HeapCellMemory176(long moduleBase, HeapCell64 heap) {
        this.moduleBase = moduleBase;
        this.heap = heap;
    }

    @Override
    public long readPointer(long address) {
        if (address == moduleBase + 0x5C5DE30L) {
            return heap.value;
        }
        throw new UnsupportedOperationException("Unsupported readPointer address");
    }

    @Override
    public int readInt32(long address) {
        throw new UnsupportedOperationException("Unsupported readInt32 operation");
    }

    @Override
    public void writeInt32(long address, int value) {
        throw new UnsupportedOperationException("Unsupported writeInt32 operation");
    }

    @Override
    public void writeInt64(long address, long value) {
        if (address == moduleBase + 0x5C5DE30L) {
            heap.value = value;
            return;
        }
        throw new UnsupportedOperationException("Unsupported writeInt64 address");
    }
}