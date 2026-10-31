package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Supplied normal 392B and 537B reads only; no loaded type or runtime identity. */
public final class LoadHierarchySearch173 {
    private LoadHierarchySearch173() { }
    public interface Memory extends NativeTaskMemory, LoadSearch4260af0.ReadMemory { }

    public static long find968(LoadRuntime4260e74.SearchCall call, Memory memory) {
        long complete = call.rcx();
        long base = call.stack28().getAsLong();
        long target = call.stack20().getAsLong();
        long header = base + memory.readInt32(call.rdx() + 0x10L);
        long list = base + memory.readInt32(header + 0xCL);
        int count = memory.readInt32(header + 8L);
        int index = 0;
        int selectedIndex = -1;
        int selectedSpan = 0;
        long selectedTarget = 0L;
        long selectedSource = 0L;
        while (Integer.compareUnsigned(index, count) < 0) {
            long descriptor = base + memory.readInt32(list);
            if (Integer.compareUnsigned(index - selectedIndex, selectedSpan) > 0) {
                long type = base + memory.readInt32(descriptor);
                if (type == target || LoadByteNames4260b67.compare(
                        type + 0x10L, target + 0x10L, memory) == 0) {
                    if (selectedSource != 0L) {
                        if ((memory.readUnsigned8(descriptor + 0x14L) & 3) != 0) {
                            return 0L;
                        }
                        if ((memory.readUnsigned8(selectedSource + 0x14L) & 1) != 0) {
                            return 0L;
                        }
                        return descriptor;
                    }
                    selectedSpan = memory.readInt32(descriptor + 4L);
                    selectedTarget = descriptor;
                    selectedIndex = index;
                }
            }
            long type = base + memory.readInt32(descriptor);
            if (type == call.r8() || LoadByteNames4260b67.compare(
                    type + 0x10L, call.r8() + 0x10L, memory) == 0) {
                long offset = LoadResultAdjustment4260f6b.adjust(complete, descriptor, memory) - complete;
                if (offset == call.r9()) {
                    if (selectedTarget != 0L) {
                        int delta = index - selectedIndex;
                        if (Integer.compareUnsigned(delta, selectedSpan) <= 0) {
                            if ((memory.readUnsigned8(selectedTarget + 0x14L) & 0x40) == 0) {
                                if (selectedIndex == 0 && (memory.readUnsigned8(descriptor + 0x14L) & 1) != 0) {
                                    return 0L;
                                }
                            } else {
                                long nestedHeader = base + memory.readInt32(selectedTarget + 0x18L);
                                long nestedList = base + memory.readInt32(nestedHeader + 0xCL);
                                long nested = base + memory.readInt32(nestedList + Integer.toUnsignedLong(delta) * 4L);
                                if ((memory.readUnsigned8(nested + 0x14L) & 1) != 0) {
                                    return 0L;
                                }
                            }
                        } else {
                            if ((memory.readUnsigned8(selectedTarget + 0x14L) & 3) != 0) {
                                return 0L;
                            }
                            if ((memory.readUnsigned8(descriptor + 0x14L) & 1) != 0) {
                                return 0L;
                            }
                        }
                        return selectedTarget;
                    }
                    selectedSource = descriptor;
                }
            }
            index++;
            list += 4L;
        }
        return 0L;
    }

    public static long findC28(LoadRuntime4260e74.SearchCall call, Memory memory) {
        long complete = call.rcx();
        long base = call.stack28().getAsLong();
        long target = call.stack20().getAsLong();
        long header = base + memory.readInt32(call.rdx() + 0x10L);
        long list = base + memory.readInt32(header + 0xCL);
        int count = memory.readInt32(header + 8L);
        int index = 0;
        int selectedIndex = -1;
        int selectedSpan = 0;
        long targetAny = 0L;
        long cleanTarget = 0L;
        long selectedSource = 0L;
        long outsideSource = 0L;
        long resultOffset = -1L;
        boolean viable = true;
        while (Integer.compareUnsigned(index, count) < 0) {
            long descriptor = base + memory.readInt32(list);
            if (Integer.compareUnsigned(index - selectedIndex, selectedSpan) > 0) {
                long type = base + memory.readInt32(descriptor);
                if (type == target || LoadByteNames4260b67.compare(
                        type + 0x10L, target + 0x10L, memory) == 0) {
                    int flags = memory.readUnsigned8(descriptor + 0x14L);
                    targetAny = descriptor;
                    selectedSpan = memory.readInt32(descriptor + 4L);
                    selectedIndex = index;
                    if ((flags & 3) == 0) {
                        cleanTarget = descriptor;
                    }
                }
            }
            long type = base + memory.readInt32(descriptor);
            if (type == call.r8() || LoadByteNames4260b67.compare(
                    type + 0x10L, call.r8() + 0x10L, memory) == 0) {
                long offset = LoadResultAdjustment4260f6b.adjust(complete, descriptor, memory) - complete;
                if (offset == call.r9()) {
                    int delta = index - selectedIndex;
                    if (Integer.compareUnsigned(delta, selectedSpan) > 0) {
                        if ((memory.readUnsigned8(descriptor + 0x14L) & 5) == 0) {
                            outsideSource = descriptor;
                        }
                    } else if (viable) {
                        boolean usable;
                        if ((memory.readUnsigned8(targetAny + 0x14L) & 0x40) == 0) {
                            if (selectedIndex == 0 && (memory.readUnsigned8(descriptor + 0x14L) & 1) != 0) {
                                viable = false;
                            }
                            usable = true;
                        } else {
                            long nestedHeader = base + memory.readInt32(targetAny + 0x18L);
                            long nestedList = base + memory.readInt32(nestedHeader + 0xCL);
                            long nested = base + memory.readInt32(nestedList + Integer.toUnsignedLong(delta) * 4L);
                            int flags = memory.readInt32(nested + 0x14L);
                            usable = ((~(flags >>> 2)) & 1) != 0;
                            if ((memory.readUnsigned8(nested + 0x14L) & 1) != 0) {
                                viable = false;
                            }
                        }
                        if (viable && usable) {
                            long targetOffset = LoadResultAdjustment4260f6b.adjust(complete, targetAny, memory) - complete;
                            if (selectedSource != 0L && resultOffset != targetOffset) {
                                return 0L;
                            }
                            selectedSource = targetAny;
                            resultOffset = targetOffset;
                        }
                    }
                }
            }
            index++;
            list += 4L;
        }
        if (viable && selectedSource != 0L) {
            return selectedSource;
        }
        if (outsideSource != 0L && cleanTarget != 0L) {
            return cleanTarget;
        }
        return 0L;
    }
}
