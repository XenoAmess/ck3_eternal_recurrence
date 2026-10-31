package org.xar.ck3.control.g2.common.nativecore.task.retained;
public final class InGameIdlerEventDispatch {
    public interface Memory {
        long readPointer(long address);
        int readInt32(long address);
        void writeInt32(long address, int value);
        void writeInt64(long address, long value);
    }

    public interface Calls {
        void virtualSlot10(long receiver, long eventAddress);
        int findEventBucket(long registryAddress, int copiedEventType);
        void onNullListener(long nativeCallTargetRva);
    }

    public static void dispatch(long holder, long eventAddress, Memory memory, Calls calls) {
        // 1. Process H+8 callback
        long h8 = memory.readPointer(holder + 8);
        if (h8 != 0) {
            calls.virtualSlot10(h8, eventAddress);
        }

        // 2. Process H+10 callback
        long h10 = memory.readPointer(holder + 0x10);
        if (h10 != 0) {
            calls.virtualSlot10(h10, eventAddress);
        }

        // 3. Read event type and lookup bucket
        int eventType = memory.readInt32(eventAddress);
        int bucketIndex = calls.findEventBucket(holder + 0x30, eventType);

        if (bucketIndex < 0) {
            return;
        }

        // 4. Compute entry address
        long base = memory.readPointer(holder + 0x30);
        long entry = base + 72L * bucketIndex;

        // 5. Initialize entry fields
        memory.writeInt32(entry + 0x40, 0);
        int count = memory.readInt32(entry + 0x34);
        memory.writeInt32(entry + 0x44, count);

        if (count <= 0) {
            memory.writeInt64(entry + 0x40, 0L);
            return;
        }

        // 6. Loop over listeners
        int cursor = 0;
        while (true) {
            long listeners = memory.readPointer(entry + 0x28);
            long listenerAddr = listeners + 72L * cursor + 0x40;
            long receiver = memory.readPointer(listenerAddr);

            if (receiver == 0) {
                calls.onNullListener(0x42207F8L);
                throw new IllegalStateException("Null listener terminal path");
            }

            calls.virtualSlot10(receiver, eventAddress);

            // Reload cursor and limit after callback
            int currentCursor = memory.readInt32(entry + 0x40);
            int newCursor = currentCursor + 1;
            memory.writeInt32(entry + 0x40, newCursor);
            int limit = memory.readInt32(entry + 0x44);

            if (newCursor >= limit) {
                break;
            }
            cursor = newCursor;
        }

        // 7. Clear cursor and limit
        memory.writeInt64(entry + 0x40, 0L);
    }
}
