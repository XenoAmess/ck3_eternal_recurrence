package org.xar.ck3.research.m3;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;
public final class MoveSlot193 {
    private MoveSlot193() { }
    public static void move(RequestE92780.Memory memory, MoveSlotApi193.Ports ports,
                            long bucket, int probe, int hash, long descriptor) {
        long destination = bucket + 8L;
        memory.writeInt32(bucket, hash);
        memory.writeByte(bucket + 4L, (byte)probe);
        if (destination != descriptor) {
            ports.call856050(memory, destination);
            RequestE92780.Raw128 r0 = memory.readRaw128(descriptor);
            memory.writeRaw128(destination, r0);
            RequestE92780.Raw128 r1 = memory.readRaw128(descriptor + 16L);
            memory.writeRaw128(destination + 16L, r1);
            memory.writeInt64(descriptor + 16L, 0L);
            memory.writeInt64(descriptor + 24L, 15L);
            memory.writeByte(descriptor, (byte)0);
        }
    }
}