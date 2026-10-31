package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.RegistryConsumerApi176.Completion;
import org.xar.ck3.research.m3.RegistryConsumerApi176.Memory;
import org.xar.ck3.research.m3.RegistryConsumerApi176.Ports;
import org.xar.ck3.research.m3.RegistryConsumerApi176.Scratch;

/** Normal memory/call projection of held 914B 3763730; no native execution. */
public final class RegistryConsumer176 {
    private RegistryConsumer176() { }

    /**
     * sourceRsp maps the caller-owned scratch for this frame; sourceRbp=sourceRsp+100h.
     * Scratch retains its supplied initial bits, including unwritten descriptor halves.
     * The finite normal domain requires terminating occupied scans/equality loops.
     * No C++ EH, concurrent SIMD atomicity, or unused raw Win64 scalar is projected.
     */
    public static Completion consume(Memory memory, Ports ports, long moduleBase,
            long manager, long incomingVector, Scratch scratch) {
        long sourceRsp = scratch.sourceRsp();
        long sourceRbp = scratch.sourceRbp();
        // This parameter home is later reloaded after the first phase (3763903).
        memory.writeInt64(sourceRbp + 0x98L, incomingVector);
        int cleanupMask = 0;
        memory.writeInt32(sourceRbp + 0x90L, cleanupMask);

        long tableBase = memory.readPointer(manager + 0x30L);
        long row = tableBase;
        while ((memory.readUnsigned8(row + 4L) & 0xff) == 0) {
            row += 0x18L;
        }
        int extraByte = memory.readUnsigned8(manager + 0x40L) & 0xff;
        int tableCount = memory.readInt32(manager + 0x3cL);
        int slotCount = tableCount + (extraByte + 1);
        long tableEnd = tableBase + (long) slotCount * 0x18L;
        long vectorRegister = incomingVector;

        if (row != tableEnd) {
            do {
                long handlerObject = memory.readPointer(moduleBase + 0x5c6a4b8L);
                int key = memory.readInt32(row + 8L);
                memory.writeInt32(sourceRsp + 0x40L, 0);
                memory.write8(sourceRsp + 0x44L, 0);
                ports.call9ce3f0(memory, sourceRsp + 0x48L);
                memory.writeInt64(sourceRbp - 0x78L, 0L);
                memory.write8(sourceRsp + 0x44L, 0);
                memory.writeInt32(sourceRsp + 0x40L, key);
                if (memory.readInt32(sourceRsp + 0x54L) < 1) {
                    ports.callca6190(memory, sourceRsp + 0x48L, 1);
                }
                memory.writeInt32(sourceRsp + 0x54L, 1);
                long byteStorage = memory.readPointer(sourceRsp + 0x48L);
                memory.write8(byteStorage, 0);
                memory.writeInt64(sourceRbp - 0x78L, 0L);
                cleanupMask |= 1;
                memory.writeInt32(sourceRbp + 0x90L, cleanupMask);
                long handlerCode = memory.readPointer(handlerObject);
                int handlerResult = ports.handlerAl(memory, handlerCode, sourceRsp + 0x40L);
                if ((handlerResult & 0xff) != 0) {
                    memory.writeInt64(sourceRsp + 0x20L, moduleBase + 0x5d37f00L);
                    // sourceRsp supplies stack+20; other unused volatile args remain opaque.
                    ports.call3f7aa40(memory, moduleBase + 0x492ed30L, sourceRsp);
                }
                if ((cleanupMask & 1) != 0) {
                    cleanupMask &= ~1;
                    long block = memory.readPointer(sourceRsp + 0x48L);
                    if (block != 0) {
                        memory.writeInt32(sourceRsp + 0x54L, 0);
                        long allocator = memory.readPointer(sourceRsp + 0x58L);
                        long code = virtualCode(memory, allocator, 0x10L);
                        ports.allocatorSlot10(memory, code, allocator, block, 1);
                    }
                }

                long tableObject = memory.readPointer(row + 0x10L);
                long object = ports.objectSlot08(memory, virtualCode(memory, tableObject, 8L), tableObject);
                memory.writeInt64(sourceRbp + 0xa0L, object);
                int handled = ports.objectSlotA8Al(memory, virtualCode(memory, object, 0xa8L), object);
                if ((handled & 0xff) != 0) {
                    ports.objectSlot00(memory, virtualCode(memory, object, 0L), object, 1);
                } else {
                    long descriptor = lookupDescriptor(memory, ports, object);
                    int length = memory.readInt32(descriptor + 0x10L);
                    long data = descriptorData(memory, descriptor);
                    memory.writeInt64(sourceRsp + 0x30L, data);
                    memory.writeInt32(sourceRsp + 0x38L, length);
                    memory.write8(sourceRsp + 0x3cL, 0);
                    long copied = ports.objectSlot30(memory, virtualCode(memory, object, 0x30L),
                            object, sourceRbp + 0x30L);
                    copy16(memory, sourceRbp - 0x50L, copied);
                    ports.call3795e30(memory, sourceRbp - 0x50L, 2, sourceRsp + 0x30L);
                    ports.objectSlot00(memory, virtualCode(memory, object, 0L), object, 1);
                }
                do {
                    row += 0x18L;
                } while ((memory.readUnsigned8(row + 4L) & 0xff) == 0);
            } while (row != tableEnd);
            vectorRegister = memory.readPointer(sourceRbp + 0x98L);
        }

        long cursor = memory.readPointer(vectorRegister);
        int vectorCount = memory.readInt32(vectorRegister + 0x0cL);
        long vectorEnd = cursor + (long) vectorCount * 8L;
        while (cursor != vectorEnd) {
            long incomingObject = memory.readPointer(cursor);
            int alreadyHandled = ports.incomingSlot48Al(memory,
                    virtualCode(memory, incomingObject, 0x48L), incomingObject);
            if ((alreadyHandled & 0xff) == 0) {
                long outputDescriptor = ports.call3f95fd0(memory, incomingObject + 0x10L,
                        sourceRbp + 0x40L);
                long descriptor = lookupDescriptor(memory, ports, incomingObject);
                long secondData;
                if ((memory.readUnsigned8(outputDescriptor + 0x0cL) & 0xff) == 0) {
                    secondData = memory.readPointer(outputDescriptor);
                } else {
                    secondData = descriptorData(memory, ports.call864a20(memory));
                }
                long firstData = descriptorData(memory, descriptor);
                memory.writeInt64(sourceRbp - 0x40L, firstData);
                memory.writeInt64(sourceRbp - 0x30L, secondData);
                copy16(memory, sourceRbp + 0x10L, sourceRbp - 0x40L);
                copy16(memory, sourceRbp + 0x20L, sourceRbp - 0x30L);
                memory.writeInt64(sourceRbp - 0x70L, 0xccL);
                memory.writeInt64(sourceRbp - 0x68L, sourceRbp + 0x10L);
                memory.writeInt64(sourceRbp - 0x60L, moduleBase + 0x492ec88L);
                memory.writeInt64(sourceRbp - 0x58L, 0x30L);
                copy16(memory, sourceRbp - 0x20L, sourceRbp - 0x70L);
                ports.call857a70(memory, sourceRbp - 0x10L, sourceRbp - 0x60L, sourceRbp - 0x20L);
                cleanupMask |= 2;
                memory.writeInt32(sourceRbp + 0x90L, cleanupMask);

                long tlsVector = ports.gs58(memory);
                long tlsModule = memory.readPointer(tlsVector);
                if ((memory.readUnsigned8(tlsModule + 0x158L) & 0xff) == 0) {
                    int counter = memory.readInt32(moduleBase + 0x5c6a9dcL);
                    if (counter < 0x186a0) {
                        long logger = ports.call3f5f970(memory, 1);
                        if (logger != 0) {
                            memory.writeInt64(sourceRsp + 0x28L, sourceRbp - 0x10L);
                            // The port can observe retained stack+20 and written stack+28.
                            ports.call857b60(memory, logger, moduleBase + 0x492ece0L,
                                    0x8b, 4, sourceRsp);
                            ports.atomicXadd32(memory, moduleBase + 0x5c6a9dcL, 1);
                        }
                    }
                    cleanupMask = memory.readInt32(sourceRbp + 0x90L);
                }

                long capacity = memory.readPointer(sourceRbp + 8L);
                if (Long.compareUnsigned(capacity, 0x10L) >= 0) {
                    long bytes = capacity + 1L;
                    long base = memory.readPointer(sourceRbp - 0x10L);
                    long originalBase = base;
                    if (Long.compareUnsigned(bytes, 0x1000L) >= 0) {
                        bytes += 0x27L;
                        base = memory.readPointer(base - 8L);
                        long gap = originalBase - base - 8L;
                        if (Long.compareUnsigned(gap, 0x1fL) > 0) {
                            ports.call4232a70(memory);
                            // The original next instruction is INT3, never normal continuation.
                            return Completion.UNSUPPORTED_INT3_AFTER_ERROR_CALL_RETURNED;
                        }
                    }
                    ports.call4223f44(memory, base, bytes);
                }
            }
            cursor += 8L;
        }
        return Completion.RETURNED;
    }

    private static long virtualCode(Memory memory, long receiver, long slot) {
        long vptr = memory.readPointer(receiver);
        return memory.readPointer(vptr + slot);
    }

    private static long lookupDescriptor(Memory memory, Ports ports, long object) {
        long context = ports.call3768260(memory);
        int indirect = memory.readUnsigned8(object + 0x0cL) & 0xff;
        int key = memory.readInt32(object + 8L);
        return indirect != 0 ? ports.call3f8a6d0(memory, context, key)
                : ports.call3f4f8e0(memory, key);
    }

    private static long descriptorData(Memory memory, long descriptor) {
        long capacity = memory.readPointer(descriptor + 0x18L);
        return Long.compareUnsigned(capacity, 0x10L) >= 0
                ? memory.readPointer(descriptor) : descriptor;
    }

    private static void copy16(Memory memory, long destination, long source) {
        long low = memory.readPointer(source);
        long high = memory.readPointer(source + 8L);
        memory.writeInt64(destination, low);
        memory.writeInt64(destination + 8L, high);
    }
}
