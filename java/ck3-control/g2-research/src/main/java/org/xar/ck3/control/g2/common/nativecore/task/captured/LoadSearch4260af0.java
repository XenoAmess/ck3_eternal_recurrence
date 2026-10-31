package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Supplied reads used by held normal312B source; no native/type identity. */
public final class LoadSearch4260af0 {
    private LoadSearch4260af0() { }
    public interface ReadMemory {
        int readInt32(long address);
        /** Returns the actual unsigned8 bits, 0..255. */
        int readUnsigned8(long address);
    }
    public static long find(LoadRuntime4260e74.SearchCall call, ReadMemory memory) {
        long base = call.r9();
        long headerOffset = (long) memory.readInt32(call.rcx() + 0x10L);
        long list = base + (long) memory.readInt32(base + headerOffset + 0xCL);
        int count = memory.readInt32(base + headerOffset + 0x8L);
        if (count == 0) { return 0L; }
        int index = 0;
        long cursor = list;
        do {
            long targetDescriptor = base + (long) memory.readInt32(cursor);
            index++;
            long type = base + (long) memory.readInt32(targetDescriptor);
            if (type == call.r8()) {
                if (Integer.compareUnsigned(index, count) >= 0) { return 0L; }
                cursor = list + Integer.toUnsignedLong(index) * 4L;
                do {
                    long descriptorOffset = (long) memory.readInt32(cursor);
                    if ((memory.readUnsigned8(base + descriptorOffset + 0x14L) & 4) != 0) { return 0L; }
                    long sourceType = base + (long) memory.readInt32(base + descriptorOffset);
                    if (sourceType == call.rdx()) { return targetDescriptor; }
                    index++;
                    cursor += 4L;
                } while (Integer.compareUnsigned(index, count) < 0);
                return 0L;
            }
            cursor += 4L;
        } while (Integer.compareUnsigned(index, count) < 0);
        index = 0;
        cursor = list;
        do {
            long targetDescriptor = base + (long) memory.readInt32(cursor);
            index++;
            long candidateName = base + 0x10L + (long) memory.readInt32(targetDescriptor);
            if (LoadByteNames4260b67.compare(candidateName, call.r8() + 0x10L, memory) == 0) {
                if (Integer.compareUnsigned(index, count) >= 0) { return 0L; }
                cursor = list + Integer.toUnsignedLong(index) * 4L;
                do {
                    long descriptorOffset = (long) memory.readInt32(cursor);
                    if ((memory.readUnsigned8(base + descriptorOffset + 0x14L) & 4) != 0) { return 0L; }
                    long sourceName = base + 0x10L + (long) memory.readInt32(base + descriptorOffset);
                    if (LoadByteNames4260b67.compare(sourceName, call.rdx() + 0x10L, memory) == 0) {
                        return targetDescriptor;
                    }
                    index++;
                    cursor += 4L;
                } while (Integer.compareUnsigned(index, count) < 0);
                return 0L;
            }
            cursor += 4L;
        } while (Integer.compareUnsigned(index, count) < 0);
        return 0L;
    }
}
