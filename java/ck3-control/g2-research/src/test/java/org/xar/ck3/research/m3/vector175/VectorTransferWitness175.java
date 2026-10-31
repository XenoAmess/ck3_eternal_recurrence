package org.xar.ck3.research.m3.vector175;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Five fixed source-derived scripted inputs, not original native or unknown allocator implementation. */
public final class VectorTransferWitness175 {
    private static final long D = 0x8100000000001000L, S = 0x8200000000002000L;
    private static final long A = 0x8400000000003000L, B = 0x8400000000004000L;
    private static final long VA = 0x8500000000005000L, VB = 0x8500000000006000L;
    private static final long ALLOC = 0x8600000000007000L, FREE = 0x8600000000008000L, FREE_B = 0x8600000000009000L;
    private static final long OLD = 0x870000000000A000L, SRC = 0x880000000000B000L;
    private static final long NEW = 0x890000000000C000L, CHANGED = 0x8A0000000000D000L;
    private static final long LATEST = 0x8B0000000000E000L, BODY = 0x8C00000000010000L, IMAGE = 0x140000000L;
    private record Event(String kind, long[] args, long returned, Runnable controlledEffect) { }
    private static final class Fixture implements NativeTaskMemory, VectorTransfer37690D0.Ports {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final ArrayDeque<Event> events = new ArrayDeque<>();
        private int consumed;
        private void initialize(long address, int width, long value) {
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (i * 8)));
        }
        private long peek(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) throw new AssertionError("uninitialized byte " + Long.toUnsignedString(address + i, 16));
                value |= (b & 255L) << (8 * i);
            }
            return value;
        }
        private Event take(String kind, long... args) {
            Event event = events.pollFirst();
            if (event == null || !event.kind().equals(kind) || !Arrays.equals(event.args(), args))
                throw new AssertionError("event " + consumed + " expected " + (event == null ? "END" : event.kind() + Arrays.toString(event.args()))
                        + " got " + kind + Arrays.toString(args));
            consumed++; if (event.controlledEffect() != null) event.controlledEffect().run(); return event;
        }
        private void event(String kind, long... args) { events.add(new Event(kind, args, 0, null)); }
        private void callback(String kind, long returned, Runnable effect, long... args) { events.add(new Event(kind, args, returned, effect)); }
        private void r64(long a, long v) { event("R64", a, v); }
        private void r32(long a, int v) { event("R32", a, Integer.toUnsignedLong(v)); }
        private void w64(long a, long v) { event("W64", a, v); }
        private void w32(long a, int v) { event("W32", a, Integer.toUnsignedLong(v)); }
        private void header(long a, long data, int cap, int count, long allocator) {
            initialize(a, 8, data); initialize(a + 8, 4, cap); initialize(a + 0xC, 4, count); initialize(a + 0x10, 8, allocator);
        }
        private void allocator(long a, long vt, long alloc, long free) {
            initialize(a, 8, vt); initialize(vt + 8, 8, alloc); initialize(vt + 0x10, 8, free);
        }
        private void finished(long destination, long source) {
            long actual = VectorTransfer37690D0.execute(destination, source, BODY, IMAGE, this, this);
            if (actual != destination || !events.isEmpty()) throw new AssertionError("return/unconsumed events");
        }
        private void finalHeader(long a, long data, int cap, int count, long allocator) {
            if (peek(a, 8) != data || peek(a + 8, 4) != Integer.toUnsignedLong(cap)
                    || peek(a + 0xC, 4) != Integer.toUnsignedLong(count) || peek(a + 0x10, 8) != allocator)
                throw new AssertionError("final header " + Long.toUnsignedString(a, 16));
        }
        @Override public long readPointer(long address) { long v = peek(address, 8); take("R64", address, v); return v; }
        @Override public int readInt32(long address) { int v = (int) peek(address, 4); take("R32", address, Integer.toUnsignedLong(v)); return v; }
        @Override public void writeInt32(long address, int value) { take("W32", address, Integer.toUnsignedLong(value)); initialize(address, 4, value); }
        @Override public void writeInt64(long address, long value) { take("W64", address, value); initialize(address, 8, value); }
        @Override public long allocate(long site, long target, long allocator, long size, int alignment) {
            return take("ALLOC", site, target, allocator, size, Integer.toUnsignedLong(alignment)).returned();
        }
        @Override public void release(long site, long target, long allocator, long data, int alignment) {
            take("FREE", site, target, allocator, data, Integer.toUnsignedLong(alignment));
        }
        @Override public void copy(long site, long destination, long source, long size) { take("COPY", site, destination, source, size); }
        @Override public void range(long site, long first, long last) { take("RANGE", site, first, last); }
        @Override public int capacityGrowth(int oldCapacity, int factorBits) {
            return (int) take("SCALAR", Integer.toUnsignedLong(oldCapacity), Integer.toUnsignedLong(factorBits)).returned();
        }
    }
    private static void equalSteal() {
        Fixture f = new Fixture(); f.header(D, OLD, 5, 2, A); f.header(S, SRC, 9, 3, A); f.allocator(A, VA, ALLOC, FREE);
        f.r64(D + 0x10, A); f.r64(S + 0x10, A); f.r64(A, VA); f.r64(D, OLD); f.r64(VA + 0x10, FREE);
        f.callback("FREE", 0, () -> { f.initialize(D + 0x10, 8, B); f.initialize(S + 0x10, 8, B);
            f.initialize(S, 8, CHANGED); f.initialize(S + 8, 4, 11); f.initialize(S + 0xC, 4, 7); }, 0x376910F, FREE, A, OLD, 8);
        f.w64(D, 0); f.w64(D + 8, 0); f.r64(S + 0x10, B); f.r64(D + 0x10, B);
        f.r64(S, CHANGED); f.w64(D, CHANGED); f.w64(S, 0);
        f.r32(D + 0xC, 0); f.r32(S + 0xC, 7); f.w32(D + 0xC, 7); f.w32(S + 0xC, 0);
        f.r32(D + 8, 0); f.r32(S + 8, 11); f.w32(D + 8, 11); f.w32(S + 8, 0);
        f.finished(D, S); f.finalHeader(D, CHANGED, 11, 7, B); f.finalHeader(S, 0, 0, 0, B);
    }
    private static void selfAlias() {
        Fixture f = new Fixture(); f.header(D, OLD, 5, 2, A); f.allocator(A, VA, ALLOC, FREE);
        f.r64(D + 0x10, A); f.r64(D + 0x10, A); f.r64(A, VA); f.r64(D, OLD); f.r64(VA + 0x10, FREE);
        f.event("FREE", 0x376910F, FREE, A, OLD, 8); f.w64(D, 0); f.w64(D + 8, 0);
        f.r64(D + 0x10, A); f.r64(D + 0x10, A); f.r64(D, 0); f.w64(D, 0); f.w64(D, 0);
        f.r32(D + 0xC, 0); f.r32(D + 0xC, 0); f.w32(D + 0xC, 0); f.w32(D + 0xC, 0);
        f.r32(D + 8, 0); f.r32(D + 8, 0); f.w32(D + 8, 0); f.w32(D + 8, 0);
        f.finished(D, D); f.finalHeader(D, 0, 0, 0, A);
    }
    private static void mismatchNoGrow() {
        Fixture f = new Fixture(); f.header(D, OLD, 4, 9, A); f.header(S, SRC, 8, 2, B);
        f.r64(D + 0x10, A); f.r64(S + 0x10, B); f.w32(D + 0xC, 0); f.r32(S + 0xC, 2); f.r64(S, SRC); f.r32(D + 8, 4); f.r64(D, OLD);
        f.callback("COPY", 0, () -> { f.initialize(D, 8, CHANGED); f.initialize(D + 0xC, 4, 1); }, 0x37692A0, OLD, SRC, 16);
        f.r32(D + 0xC, 1); f.w32(D + 0xC, 3); f.r64(D, CHANGED);
        f.event("RANGE", 0x37692CF, CHANGED, CHANGED + 8); f.event("RANGE", 0x37692DA, CHANGED + 8, CHANGED + 24);
        f.event("RANGE", 0x37692E5, CHANGED, CHANGED + 24); f.w32(S + 0xC, 0);
        f.finished(D, S); f.finalHeader(D, CHANGED, 4, 3, A); f.finalHeader(S, SRC, 8, 0, B);
    }
    private static void mismatchGrow() {
        Fixture f = new Fixture(); f.header(D, OLD, 1, 6, A); f.header(S, SRC, 7, 3, B);
        f.allocator(A, VA, ALLOC, FREE); f.allocator(B, VB, ALLOC, FREE_B); f.initialize(IMAGE + 0x49F64F0, 4, 0x3FC00000);
        f.r64(D + 0x10, A); f.r64(S + 0x10, B); f.w32(D + 0xC, 0); f.r32(S + 0xC, 3); f.r64(S, SRC); f.r32(D + 8, 1);
        f.r32(IMAGE + 0x49F64F0, 0x3FC00000); f.callback("SCALAR", 1, null, 1, 0x3FC00000);
        f.r64(A, VA); f.r64(VA + 8, ALLOC); f.callback("ALLOC", NEW, null, 0x3769240, ALLOC, A, 24, 8);
        f.r64(D, OLD); f.callback("COPY", 0, () -> { f.initialize(D, 8, CHANGED); f.initialize(D + 0xC, 4, 2); }, 0x376924F, NEW, OLD, 0);
        f.event("COPY", 0x376925D, NEW, SRC, 24); f.r64(D, CHANGED); f.r32(D + 0xC, 2);
        f.callback("COPY", 0, () -> { f.initialize(D, 8, LATEST); f.initialize(D + 0x10, 8, B); }, 0x3769274, NEW + 24, CHANGED, 16);
        f.r64(D + 0x10, B); f.r64(B, VB); f.r64(D, LATEST); f.r64(VB + 0x10, FREE_B);
        f.event("FREE", 0x3769287, FREE_B, B, LATEST, 8); f.w64(D, NEW); f.w32(D + 0xC, 3); f.w32(D + 8, 3); f.w32(S + 0xC, 0);
        f.finished(D, S); f.finalHeader(D, NEW, 3, 3, B); f.finalHeader(S, SRC, 7, 0, B);
    }
    private static void recomparedRecursive() {
        Fixture f = new Fixture(); f.header(D, OLD, 5, 2, A); f.header(S, SRC, 7, 0, A); f.allocator(A, VA, ALLOC, FREE);
        long temporary = BODY + 0x20, temporaryAllocator = BODY + 0x40;
        f.r64(D + 0x10, A); f.r64(S + 0x10, A); f.r64(A, VA); f.r64(D, OLD); f.r64(VA + 0x10, FREE);
        f.callback("FREE", 0, () -> f.initialize(D + 0x10, 8, B), 0x376910F, FREE, A, OLD, 8);
        f.w64(D, 0); f.w64(D + 8, 0); f.r64(S + 0x10, A); f.r64(D + 0x10, B); f.r32(S + 0xC, 0);
        f.w64(BODY + 0x40, IMAGE + 0x492E730); f.w64(BODY + 0x448, IMAGE + 0x54F2A78);
        f.w64(temporary, 0); f.w64(temporary + 8, 0); f.w64(temporary + 0x10, temporaryAllocator);
        f.r64(temporary + 0x10, temporaryAllocator); f.r64(D + 0x10, B);
        f.w32(temporary + 0xC, 0); f.r32(D + 0xC, 0); f.r64(D, 0); f.w32(D + 0xC, 0);
        f.r64(D + 0x10, B); f.r64(S + 0x10, A); f.w32(D + 0xC, 0); f.r32(S + 0xC, 0); f.r64(S, SRC); f.w32(S + 0xC, 0);
        f.r64(S + 0x10, A); f.r64(temporary + 0x10, temporaryAllocator);
        f.w32(S + 0xC, 0); f.r32(temporary + 0xC, 0); f.r64(temporary, 0); f.w32(temporary + 0xC, 0); f.r64(temporary, 0);
        f.finished(D, S); f.finalHeader(D, 0, 0, 0, B); f.finalHeader(S, SRC, 7, 0, A);
        f.finalHeader(temporary, 0, 0, 0, temporaryAllocator);
        if (f.peek(BODY + 0x40, 8) != IMAGE + 0x492E730 || f.peek(BODY + 0x448, 8) != IMAGE + 0x54F2A78)
            throw new AssertionError("temporary allocator markers");
    }
    public static void main(String[] args) {
        equalSteal(); selfAlias(); mismatchNoGrow(); mismatchGrow(); recomparedRecursive(); System.out.println("5 source-scripted scenes passed");
    }
}
