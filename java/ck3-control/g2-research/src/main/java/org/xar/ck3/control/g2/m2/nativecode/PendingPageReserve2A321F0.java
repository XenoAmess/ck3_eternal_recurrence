package org.xar.ck3.control.g2.m2.nativecode;

/** Complete 381-byte normal CFG 2A321F0, with opaque external calls. */
public final class PendingPageReserve2A321F0 {
    private PendingPageReserve2A321F0() { }

    public interface Memory {
        int read8(long address);
        int read32(long address);
        long read64(long address);
        void write32(long address, int value);
        void write64(long address, long value);
    }

    public interface Calls {
        void call3F7AA40(Memory memory, long rcx, int edx, long fifthStackArgument);
        void call2A32620(Memory memory, long rcx, int edx);
        void call4226F10(Memory memory, long rcx, int edx, long r8);
        void call4223F44(Memory memory, long rcx, int edx);
        long call4223B94(Memory memory, int ecx);
    }

    public record Input(long tableAddress, int requestedCount, long moduleBase,
            long entryStackSlotAddress) { }

    public static boolean ensure(Memory memory, Calls calls, Input input) {
        long table = input.tableAddress();
        int requested = input.requestedCount();
        if (memory.read8(table + 0x40) != 0) {
            return false;
        }
        if (Integer.compareUnsigned(requested, 0xFFFFFF) >= 0) {
            calls.call3F7AA40(memory, input.moduleBase() + 0x45B64C8L, requested,
                    input.moduleBase() + 0x5D1DAD9L);
            return false;
        }
        int oldCount = memory.read32(table + 0xC);
        if (Integer.compareUnsigned(requested, oldCount << 10) <= 0) {
            return true;
        }
        int desired = (requested >>> 10) + 1;
        if (desired > oldCount) {
            calls.call2A32620(memory, table, desired);
            int freshCount = memory.read32(table + 0xC);
            int difference = desired - freshCount;
            long base = memory.read64(table);
            long clearAt = base + (long) freshCount * 8;
            if (difference > 0) {
                calls.call4226F10(memory, clearAt, 0, Integer.toUnsignedLong(difference) << 3);
            }
        } else {
            long base = memory.read64(table);
            long slot = base + Integer.toUnsignedLong(desired) * 8;
            long end = base + (long) oldCount * 8;
            while (slot != end) {
                long page = memory.read64(slot);
                if (page != 0) {
                    calls.call4223F44(memory, page, 0x172000);
                }
                slot += 8;
            }
        }
        memory.write32(table + 0xC, desired);
        if (Integer.compareUnsigned(oldCount, desired) < 0) {
            long offset = Integer.toUnsignedLong(oldCount) << 3;
            long remaining = Integer.toUnsignedLong(desired - oldCount);
            do {
                long slot = memory.read64(table) + offset;
                long newPage = calls.call4223B94(memory, 0x172000);
                calls.call4226F10(memory, newPage, 0, 0x172000L);
                if (slot == input.entryStackSlotAddress()) {
                    calls.call4223F44(memory, newPage, 0x172000);
                } else {
                    long oldPage = memory.read64(slot);
                    memory.write64(slot, newPage);
                    if (oldPage != 0) {
                        calls.call4223F44(memory, oldPage, 0x172000);
                    }
                }
                long page = memory.read64(slot);
                calls.call4226F10(memory, page, 0, 0x172000L);
                long at = page + 0x10;
                for (int i = 0; i < 1024; i++) {
                    memory.write32(at, -1);
                    at += 0x5C8;
                }
                offset += 8;
                remaining--;
            } while (remaining != 0);
        }
        return true;
    }
}
