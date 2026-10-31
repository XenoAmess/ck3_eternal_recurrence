package org.xar.ck3.research.m3.map191;
import org.xar.ck3.research.m3.map191.MapInsert191Api.*;
import java.util.List;

public final class MapInsertC3B960 {
    private MapInsertC3B960() { }

    public static long execute(Input input, Memory memory, Ports ports) {
        long map = input.map();
        long output = input.output();
        long descriptor = input.descriptor();
        long moduleBase = input.moduleBase();
        int hash = input.hash();
        long bodyRsp = input.scratch().bodyRsp();
        long rbp = bodyRsp + 0x70L;

        // Prologue: load mask, compute index, get data pointer
        int mask = memory.readInt32(map + 0x14L);
        long index = ((long) mask) & ((long) hash);
        long data = memory.readPointer(map + 8L);
        long bucket = data + (index + index * 4L) * 8L;
        int probe = 1;

        // Initial probe check
        int first = memory.readUnsigned8(bucket + 4L);
        if (first >= probe) {
            // Loop over occupied slots in the bucket chain
            long descriptorCapacity = memory.readPointer(descriptor + 0x18L);
            while (true) {
                long bucketCapacity = memory.readPointer(bucket + 0x20L);
                long right = bucket + 8L;
                if (Long.compareUnsigned(bucketCapacity, 0x10L) >= 0) {
                    right = memory.readPointer(right);
                }
                long left = descriptor;
                if (Long.compareUnsigned(descriptorCapacity, 0x10L) >= 0) {
                    left = memory.readPointer(descriptor);
                }
                int equalResult = ports.equal3f6d2b0(memory, 0xC3B9CAL, left, right, bodyRsp - 8L);
                if ((equalResult & 0xFF) != 0) {
                    // Found existing key
                    memory.writeInt64(output, bucket);
                    memory.write8(output + 8L, 0);
                    return output;
                }
                bucket += 0x28L;
                probe = (probe + 1) & 0xFF;
                int next = memory.readUnsigned8(bucket + 4L);
                if (probe > next) {
                    break;
                }
            }
            // Reload mask after loop exit
            mask = memory.readInt32(map + 0x14L);
        }

        // Check if we need to grow (probe > max probe or load factor exceeded)
        int maximum = memory.readUnsigned8(map + 0x18L);
        if (probe > maximum) {
            return grow(input, memory, ports, mask, rbp);
        }
        int nextCount = memory.readInt32(map + 0x10L) + 1;
        float ratio = ((float) nextCount) / ((float) mask);
        float limit = Float.intBitsToFloat(memory.readInt32(map + 0x1CL));
        if (ratio > limit) {
            return grow(input, memory, ports, mask, rbp);
        }

        // Insert into current bucket
        int occupied = memory.readUnsigned8(bucket + 4L);
        long destination = bucket + 8L;

        if (occupied == 0) {
            // Empty slot in bucket: write hash, probe, and move descriptor data
            memory.writeInt32(bucket, hash);
            memory.write8(bucket + 4L, probe);
            memory.writeInt64(bucket + 8L, 0L);
            memory.writeInt64(bucket + 0x18L, 0L);
            memory.writeInt64(bucket + 0x20L, 0L);
            // Actual 2x16 moves and source reset (NOT COPY855F00)
            Bytes16 low = memory.read128(descriptor);
            memory.write128(destination, low);
            Bytes16 high = memory.read128(descriptor + 0x10L);
            memory.write128(destination + 0x10L, high);
            // Source reset
            memory.writeInt64(descriptor + 0x10L, 0L);
            memory.writeInt64(descriptor + 0x18L, 0x0FL);
            memory.write8(descriptor, 0);
            return inserted(input, memory, bucket);
        }

        // Occupied slot: need to displace or chain
        int oldHash = memory.readInt32(bucket);
        int displacedProbe = (occupied + 1) & 0xFF;
        int nextOccupied = memory.readUnsigned8(bucket + 0x2CL);

        if (nextOccupied == 0) {
            // No next occupied slot: clear old slot and use insertSlotC3CF10 (NOT 855DB0)
            // Clear old slot fields
            memory.writeInt32(bucket + 0x28L, oldHash);
            memory.write8(bucket + 0x2CL, displacedProbe);
            memory.writeInt64(bucket + 0x30L, 0L);
            memory.writeInt64(bucket + 0x40L, 0L);
            memory.writeInt64(bucket + 0x48L, 0L);
            // Move descriptor data to new slot
            Bytes16 firstHalf = memory.read128(destination);
            memory.write128(bucket + 0x30L, firstHalf);
            Bytes16 secondHalf = memory.read128(destination + 0x10L);
            memory.write128(bucket + 0x40L, secondHalf);
            // Reset source
            memory.writeInt64(destination + 0x10L, 0L);
            memory.writeInt64(destination + 0x18L, 0x0FL);
            memory.write8(destination, 0);
            // Call insertSlotC3CF10
            ports.insertSlotC3cf10(memory, 0xC3BAB8L, bucket, probe, hash, descriptor);
            return inserted(input, memory, bucket);
        }

        // Long chain case: use scratch and recursive insertC3A5F0
        long scratchHash = rbp - 0x30L;
        long scratchProbe = rbp - 0x2CL;
        long scratchLow = rbp - 0x28L;
        long scratchHigh = rbp - 0x18L;

        // Save old data to scratch
        memory.writeInt32(scratchHash, oldHash);
        memory.write8(scratchProbe, displacedProbe);
        Bytes16 firstHalf = memory.read128(destination);
        memory.write128(scratchLow, firstHalf);
        Bytes16 secondHalf = memory.read128(destination + 0x10L);
        memory.write128(scratchHigh, secondHalf);

        // Clear old slot
        memory.writeInt64(destination + 0x10L, 0L);
        memory.writeInt64(destination + 0x18L, 0x0FL);
        memory.write8(destination, 0);

        // Call insertSlotC3CF10 for the new entry
        ports.insertSlotC3cf10(memory, 0xC3BAF7L, bucket, probe, hash, descriptor);

        // Now handle the displaced entry via long chain logic
        int carriedProbe = memory.readUnsigned8(scratchProbe);
        long originalBucket = bucket;

        while (true) {
            int nextProbe = memory.readUnsigned8(bucket + 0x2CL);
            bucket += 0x28L;
            if (nextProbe == 0) {
                // Found empty slot for displaced entry
                int carriedHash = memory.readInt32(scratchHash);
                memory.write8(bucket + 4L, carriedProbe);
                memory.writeInt32(bucket, carriedHash);
                memory.writeInt64(bucket + 8L, 0L);
                memory.writeInt64(bucket + 0x18L, 0L);
                memory.writeInt64(bucket + 0x20L, 0L);
                Bytes16 low = memory.read128(scratchLow);
                memory.write128(bucket + 8L, low);
                Bytes16 high = memory.read128(scratchHigh);
                Bytes16 empty = memory.read128(moduleBase + 0x49F6EE0L);
                memory.write128(bucket + 0x18L, high);
                // Reset scratch
                memory.write8(scratchLow, 0);
                memory.write128(scratchHigh, empty);
                // Destroy scratch descriptor
                ports.destroy856050(memory, 0xC3BC15L, scratchLow);
                return inserted(input, memory, originalBucket);
            }
            if (nextProbe < carriedProbe) {
                // Swap current bucket with scratch
                swap(memory, bucket, scratchHash, scratchProbe, scratchLow, scratchHigh);
                carriedProbe = (memory.readUnsigned8(scratchProbe) + 1) & 0xFF;
                memory.write8(scratchProbe, carriedProbe);
                continue;
            }
            carriedProbe = (carriedProbe + 1) & 0xFF;
            memory.write8(scratchProbe, carriedProbe);
            int currentMaximum = memory.readUnsigned8(map + 0x18L);
            if (carriedProbe <= currentMaximum) {
                continue;
            }

            // Need to rehash: swap back, call rehash, then insertC3A5F0
            swap(memory, originalBucket, scratchHash, scratchProbe, scratchLow, scratchHigh);
            ports.rehashC3a400(memory, 0xC3BBADL, map);
            int reinsertHash = memory.readInt32(scratchHash);
            long result = rbp - 0x40L;
            ports.insertC3a5f0(memory, 0xC3BBC1L, map, result, reinsertHash, scratchLow);
            ports.destroy856050(memory, 0xC3BBCAL, scratchLow);
            Bytes16 copiedResult = memory.read128(result);
            memory.write128(output, copiedResult);
            return output;
        }
    }

    private static long inserted(Input input, Memory memory, long bucket) {
        int count = memory.readInt32(input.map() + 0x10L);
        memory.writeInt32(input.map() + 0x10L, count + 1);
        memory.writeInt64(input.output(), bucket);
        memory.write8(input.output() + 8L, 1);
        return input.output();
    }

    private static long grow(Input input, Memory memory, Ports ports, int currentMask, long rbp) {
        int capacity = ports.capacity86e160(memory, 0xC3BC2FL, currentMask + 1, 1);
        if (capacity >= 0x1F) {
            ports.overflow86f210(memory, 0xC3BC83L, rbp + 0x40L, input.map());
            ports.terminal4232cf4(memory, 0xC3BC88L);
            throw new UnprojectedInt3();
        }
        ports.reserveC3b700(memory, 0xC3BC3EL, input.map(), capacity, input.scratch().bodyRsp() - 8L);
        long fifth = rbp + 0x50L;
        memory.write8(fifth, 0);
        memory.writeInt64(input.scratch().bodyRsp() + 0x20L, fifth);
        execute(new Input(input.moduleBase(), input.map(), input.output(), input.hash(), input.descriptor(),
                new Scratch(input.scratch().bodyRsp() - 0xB0L)), memory, ports);
        return input.output();
    }

    private static void swap(Memory memory, long bucket, long scratchHash, long scratchProbe,
                             long scratchLow, long scratchHigh) {
        int oldHash = memory.readInt32(bucket);
        int carriedHash = memory.readInt32(scratchHash);
        memory.writeInt32(scratchHash, oldHash);
        int oldProbe = memory.readUnsigned8(bucket + 4L);
        memory.writeInt32(bucket, carriedHash);
        int carriedProbe = memory.readUnsigned8(scratchProbe);
        memory.write8(scratchProbe, oldProbe);
        memory.write8(bucket + 4L, carriedProbe);
        Bytes16 low = memory.read128(bucket + 8L);
        Bytes16 carriedLow = memory.read128(scratchLow);
        Bytes16 carriedHigh = memory.read128(scratchHigh);
        memory.write128(scratchLow, low);
        Bytes16 high = memory.read128(bucket + 0x18L);
        memory.write128(scratchHigh, high);
        memory.write128(bucket + 8L, carriedLow);
        memory.write128(bucket + 0x18L, carriedHigh);
    }
}