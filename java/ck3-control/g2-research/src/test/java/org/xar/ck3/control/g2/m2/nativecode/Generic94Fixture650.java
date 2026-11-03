package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/**
 * Nine-port owned byte RAM. Byte/event mechanics descend from WholeRotateFixture651;
 * unowned bytes reject here, and no allocation or target algorithm is implemented.
 */
final class Generic94Fixture650 {
    private Generic94Fixture650() { }

    record Event(String kind, long address, long a, long b, long c, long d) { }

    static Event e(String kind, long address, long value) {
        return new Event(kind, address, value, 0, 0, 0);
    }

    static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        final List<Event> events = new ArrayList<>();

        private static void scalarWidth(int width) {
            if (width < 1 || width > 8) throw new IllegalArgumentException("scalar width");
        }

        private void requireOwned(long address, int width) {
            for (int i = 0; i < width; i++) {
                if (!bytes.containsKey(address + i)) {
                    throw new UnsupportedOperationException("unowned software RAM byte");
                }
            }
        }

        /** Input seeding only; it admits keys and records no target Memory event. */
        void seedScalar(long address, int width, long value) {
            scalarWidth(width);
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte)(value >>> (8 * i)));
        }

        void seedFill(long address, int count, int unsignedByte) {
            if (count < 0 || unsignedByte < 0 || unsignedByte > 255) {
                throw new IllegalArgumentException("seed fill");
            }
            for (int i = 0; i < count; i++) bytes.put(address + i, (byte)unsignedByte);
        }

        /** Pure inspection of admitted bytes; no represented Memory event. */
        long peek(long address, int width) {
            scalarWidth(width);
            requireOwned(address, width);
            long value = 0;
            for (int i = 0; i < width; i++) value |= (bytes.get(address + i) & 255L) << (8 * i);
            return value;
        }

        Map<Long, Byte> fullBytes() {
            return Map.copyOf(bytes);
        }

        void step(long pc, long guard) {
            events.add(e("BUDGET", pc, guard));
        }

        @Override public int readDword(long address) {
            int value = (int)peek(address, 4);
            events.add(e("R32", address, value));
            return value;
        }

        @Override public long readQword(long address) {
            long value = peek(address, 8);
            events.add(e("R64", address, value));
            return value;
        }

        @Override public int readUnsignedByte(long address) {
            int value = (int)peek(address, 1);
            events.add(e("R8", address, value));
            return value;
        }

        @Override public void writeDword(long address, int value) {
            requireOwned(address, 4);
            events.add(e("W32", address, value));
            seedScalar(address, 4, value);
        }

        /** One represented operation; no concurrent or CPU atomicity is inferred. */
        @Override public int lockedXaddDword(long address, int addend) {
            int old = (int)peek(address, 4);
            int sum = old + addend;
            events.add(new Event("LOCK_XADD32", address, addend, old, sum, 0));
            seedScalar(address, 4, sum);
            return old;
        }

        @Override public void writeQword(long address, long value) {
            requireOwned(address, 8);
            events.add(e("W64", address, value));
            seedScalar(address, 8, value);
        }

        @Override public void writeByte(long address, int value) {
            requireOwned(address, 1);
            events.add(e("W8", address, value & 255L));
            seedScalar(address, 1, value);
        }

        @Override public Bits128 read128(long address) {
            requireOwned(address, 16);
            Bits128 value = new Bits128(peek(address, 8), peek(address + 8, 8));
            events.add(new Event("R128", address, value.lowBits(), value.highBits(), 0, 0));
            return value;
        }

        @Override public void write128(long address, Bits128 value) {
            java.util.Objects.requireNonNull(value);
            requireOwned(address, 16);
            events.add(new Event("W128", address, value.lowBits(), value.highBits(), 0, 0));
            seedScalar(address, 8, value.lowBits());
            seedScalar(address + 8, 8, value.highBits());
        }
    }
}
