package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Source855F00 normal-flow projection over supplied storage and opaque calls. */
public final class RequestConstruct855f00 {
    private RequestConstruct855f00() { }

    public interface Ports {
        long call856db0(long rcx);
        void call4226860(long rcx, long rdx, long r8);
    }

    public static long construct(long destination, long source, RequestE92780.Memory memory, Ports ports) {
        memory.writeInt64(destination, 0L);
        memory.writeInt64(destination + 0x10L, 0L);
        memory.writeInt64(destination + 0x18L, 0L);
        long sourceCapacity = memory.readPointer(source + 0x18L);
        long length = memory.readPointer(source + 0x10L);
        long data = source;
        if (Long.compareUnsigned(sourceCapacity, 16L) >= 0) {
            data = memory.readPointer(source);
        }
        long capacity;
        if (Long.compareUnsigned(length, 16L) < 0) {
            RequestE92780.Raw128 raw = memory.readRaw128(data);
            capacity = 15L;
            memory.writeRaw128(destination, raw);
        } else {
            capacity = length | 15L;
            if (Long.compareUnsigned(capacity, Long.MAX_VALUE) > 0) {
                capacity = Long.MAX_VALUE;
            }
            long allocated = ports.call856db0(capacity + 1L);
            memory.writeInt64(destination, allocated);
            ports.call4226860(allocated, data, length + 1L);
        }
        memory.writeInt64(destination + 0x10L, length);
        memory.writeInt64(destination + 0x18L, capacity);
        return destination;
    }
}
