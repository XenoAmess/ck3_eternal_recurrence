package org.xar.ck3.research.m3;

import org.xar.ck3.research.m3.PostRegistrationApi178.CallerOwnedScratch;
import org.xar.ck3.research.m3.PostRegistrationApi178.Memory;
import org.xar.ck3.research.m3.PostRegistrationApi178.Ports;
import org.xar.ck3.research.m3.PostRegistrationApi178.ScalarObservation;

/** Finite normal memory/call projection of held1295B3790510; not native execution. */
public final class PostRegistration178 {
    private PostRegistration178() { }

    public static void apply(Memory memory, Ports ports, ScalarObservation scalar,
            long moduleBase, long incomingVector, CallerOwnedScratch scratch) {
        long sp = scratch.sourceRsp();
        long bp = scratch.sourceRbp();
        long entryReceiver = memory.readPointer(moduleBase + 0x5cbeed8L);
        if (ports.call3f542c0(memory, entryReceiver, moduleBase + 0x4448998L) == -1) {
            return;
        }

        long initialTable = ports.callc3e150(memory);
        memory.writeInt64(sp + 0x38L, initialTable);
        memory.writeInt64(sp + 0x40L, 0L);
        memory.write8(sp + 0x48L, 0);
        int initialScalarBits = memory.readInt32(moduleBase + 0x49f6430L);
        memory.writeInt32(bp - 0x7dL, initialScalarBits);
        memory.writeInt64(bp - 0x79L, moduleBase + 0x54de200L);

        int sourceCount = memory.readInt32(incomingVector + 0x0cL);
        long product = 0x51eb851fL * (long) sourceCount;
        int shiftedHigh = ((int) (product >> 32)) >> 5;
        int quotient = shiftedHigh + (shiftedHigh >>> 31);
        if (quotient > 0) {
            int multiplier = memory.readInt32(moduleBase + 0x49f65b8L);
            int addend = memory.readInt32(moduleBase + 0x49f6464L);
            int requested = scalar.cvtdq2psMulssAddssCvttss2si(quotient, multiplier, addend);
            int exponent = ports.call86e160(memory, requested, 0);
            int countPlusOne = memory.readInt32(sp + 0x44L) + 1;
            int shiftedOne = 1 << exponent;
            if (shiftedOne > countPlusOne) {
                ports.callc3b700(memory, sp + 0x30L, exponent);
            }
        }

        memory.writeInt64(bp - 0x71L, 0L);
        memory.writeInt64(bp - 0x69L, 0L);
        memory.writeInt64(bp - 0x61L, moduleBase + 0x54f2ac8L);
        long manager = memory.readPointer(moduleBase + 0x5c6a4d0L);
        ports.call3763f90(memory, manager, bp - 0x71L);

        long incomingBegin = memory.readPointer(incomingVector);
        int incomingCount = memory.readInt32(incomingVector + 0x0cL);
        long incomingEnd = incomingBegin + (long) incomingCount * 8L;
        collect(memory, ports, sp + 0x30L, bp + 0x17L, incomingBegin, incomingEnd);

        int temporaryCount = memory.readInt32(bp - 0x65L);
        long temporaryRows = memory.readPointer(bp - 0x71L);
        long temporaryEnd = temporaryRows + (long) temporaryCount * 8L;
        collect(memory, ports, sp + 0x30L, bp + 0x27L, temporaryRows, temporaryEnd);

        long context = ports.calla92eb0(memory);
        long table = memory.readPointer(sp + 0x38L);
        long row = table;
        while ((memory.readUnsigned8(row + 4L) & 0xff) == 0) {
            row += 0x28L;
        }
        int extra = memory.readUnsigned8(sp + 0x48L) & 0xff;
        int capturedCount = memory.readInt32(sp + 0x44L);
        int slotCount = capturedCount + (extra + 1);
        long tableEnd = table + (long) slotCount * 0x28L;
        boolean tableEntered = row != tableEnd;
        boolean errorReturnedToTls = false;

        occupiedTable:
        while (row != tableEnd) {
            long rowDescriptor = row + 8L;
            long descriptorLength = memory.readPointer(rowDescriptor + 0x10L);
            if (descriptorLength != 0) {
                long data = descriptorData(memory, rowDescriptor);
                int hash = ports.call3f7e220(memory, data, (int) descriptorLength);
                long groupHolder = ports.call3793900(memory, context, hash);
                long group = memory.readPointer(groupHolder + 0x60L);
                int groupCount = memory.readInt32(groupHolder + 0x6cL);
                long groupEnd = group + (long) groupCount * 0x38L;
                long selected = 0L;
                while (group != groupEnd) {
                    long groupData = descriptorData(memory, group);
                    int matched = ports.call3f6d2b0Al(memory, moduleBase + 0x44ccee0L, groupData);
                    if ((matched & 0xff) != 0) {
                        long candidates = memory.readPointer(group + 0x20L);
                        int candidateCount = memory.readInt32(group + 0x2cL);
                        long candidateEnd = candidates + (long) candidateCount * 0x28L;
                        selected = RegistryCandidateSelect178.select(memory, candidates, candidateEnd);
                        break;
                    }
                    group += 0x38L;
                }
                if (selected == 0) {
                    long freshData = descriptorData(memory, rowDescriptor);
                    memory.writeInt64(bp - 0x39L, freshData);
                    copy16(memory, bp - 0x29L, bp - 0x39L);
                    memory.writeInt64(bp - 0x59L, 0x0cL);
                    memory.writeInt64(bp - 0x51L, bp - 0x29L);
                    memory.writeInt64(bp - 0x49L, moduleBase + 0x4937c40L);
                    memory.writeInt64(bp - 0x41L, 0x1eL);
                    copy16(memory, bp - 0x19L, bp - 0x59L);
                    ports.call857a70(memory, bp - 9L, bp - 0x49L, bp - 0x19L);

                    long tlsSlots = ports.gs58(memory);
                    long tlsModule = memory.readPointer(tlsSlots);
                    if ((memory.readUnsigned8(tlsModule + 0x158L) & 0xff) == 0) {
                        int counter = memory.readInt32(moduleBase + 0x5c6a9dcL);
                        if (counter < 0x186a0) {
                            long logger = ports.call3f5f970(memory, 1);
                            if (logger != 0) {
                                memory.writeInt64(sp + 0x28L, bp - 9L);
                                ports.call857b60(memory, logger, moduleBase + 0x4937e10L,
                                        0x15c, 4, sp);
                                ports.atomicXadd32(memory, moduleBase + 0x5c6a9dcL, 1);
                            }
                        }
                    }

                    long capacity = memory.readPointer(bp + 0x0fL);
                    if (Long.compareUnsigned(capacity, 0x10L) >= 0) {
                        long bytes = capacity + 1L;
                        long base = memory.readPointer(bp - 9L);
                        long originalBase = base;
                        if (Long.compareUnsigned(bytes, 0x1000L) >= 0) {
                            bytes += 0x27L;
                            base = memory.readPointer(base - 8L);
                            long gap = originalBase - base - 8L;
                            if (Long.compareUnsigned(gap, 0x1fL) > 0) {
                                ports.call4232a70(memory);
                                // Source09DF returns to09E5, skipping temp-vector cleanup.
                                errorReturnedToTls = true;
                                break occupiedTable;
                            }
                        }
                        ports.call4223f44(memory, base, bytes);
                    }
                }
            }
            do {
                row += 0x28L;
            } while ((memory.readUnsigned8(row + 4L) & 0xff) == 0);
        }

        boolean initializeGuard = errorReturnedToTls;
        if (!errorReturnedToTls) {
            if (tableEntered) {
                table = memory.readPointer(sp + 0x38L);
                temporaryCount = memory.readInt32(bp - 0x65L);
                temporaryRows = memory.readPointer(bp - 0x71L);
            }
            if (temporaryRows != 0) {
                if (temporaryCount > 0) {
                    long current = temporaryRows;
                    int remaining = temporaryCount;
                    do {
                        long object = memory.readPointer(current);
                        if (object != 0) {
                            ports.objectSlot00(memory, virtualCode(memory, object, 0L), object, 1);
                        }
                        remaining--;
                        current += 8L;
                    } while (remaining > 0);
                }
                long allocator = memory.readPointer(bp - 0x61L);
                ports.allocatorSlot10(memory, virtualCode(memory, allocator, 0x10L),
                        allocator, temporaryRows, 8);
                table = memory.readPointer(sp + 0x38L);
            }
            long tlsSlots = ports.gs58(memory);
            long tlsModule = memory.readPointer(tlsSlots);
            int tlsEpoch = memory.readInt32(tlsModule + 0x10L);
            int guardEpoch = memory.readInt32(moduleBase + 0x5d1f630L);
            initializeGuard = guardEpoch > tlsEpoch;
        }
        if (initializeGuard) {
            long guard = moduleBase + 0x5d1f630L;
            ports.call4223a84(memory, guard);
            if (memory.readInt32(guard) == -1) {
                memory.write8(moduleBase + 0x5d1f5e4L, 0);
                memory.write8(moduleBase + 0x5d1f60cL, 0xff);
                ports.call4223a24(memory, guard);
            }
            table = memory.readPointer(sp + 0x38L);
        }

        if (table != moduleBase + 0x5d1f5e0L) {
            int remaining = memory.readInt32(sp + 0x40L);
            if (remaining > 0) {
                long field = table + 8L;
                do {
                    if ((memory.readUnsigned8(field - 4L) & 0xff) != 0) {
                        ports.call856050(memory, field);
                        remaining--;
                    }
                    field += 0x28L;
                } while (remaining > 0);
                table = memory.readPointer(sp + 0x38L);
            }
            long allocator = memory.readPointer(bp - 0x79L);
            ports.allocatorSlot10(memory, virtualCode(memory, allocator, 0x10L), allocator, table, 8);
        }
    }

    private static void collect(Memory memory, Ports ports, long tableHeader, long output,
            long begin, long end) {
        long cursor = begin;
        while (cursor != end) {
            long object = memory.readPointer(cursor);
            int indirect = memory.readUnsigned8(object + 0x0cL) & 0xff;
            int key = memory.readInt32(object + 8L);
            boolean valid = indirect != 0 ? key != -1 : key != 0;
            if (valid) {
                long descriptor = ports.objectSlot80(memory, virtualCode(memory, object, 0x80L), object);
                long data = descriptorData(memory, descriptor);
                int length = memory.readInt32(descriptor + 0x10L);
                int hash = ports.call3f7e220(memory, data, length);
                ports.callc39c60(memory, tableHeader, output, hash, descriptor);
            }
            cursor += 8L;
        }
    }

    private static long descriptorData(Memory memory, long descriptor) {
        long capacity = memory.readPointer(descriptor + 0x18L);
        return Long.compareUnsigned(capacity, 0x10L) >= 0
                ? memory.readPointer(descriptor) : descriptor;
    }

    private static long virtualCode(Memory memory, long receiver, long slot) {
        long vptr = memory.readPointer(receiver);
        return memory.readPointer(vptr + slot);
    }

    private static void copy16(Memory memory, long destination, long source) {
        long low = memory.readPointer(source);
        long high = memory.readPointer(source + 8L);
        memory.writeInt64(destination, low);
        memory.writeInt64(destination + 8L, high);
    }
}
