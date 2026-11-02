package org.xar.ck3.study.m6.transfer216;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.element190.RawMemory190.Access;
import org.xar.ck3.study.m6.transfer216.Transfer216Api.Input;
import org.xar.ck3.study.m6.transfer216.Transfer216Api.Operation;

/** Owner-frozen finite plain-RAM witnesses. Manual main; no native/Game/authority assertion. */
public final class Transfer21a216Test {
    private static final long D = 0x1000, S = 0x1100, DB = 0x2000, SB = 0x3000, NEW = 0x4000;
    private static final long A = 0x5000, B = 0x5100, VA = 0x6000, VB = 0x6100;
    private static final long IMAGE = 0x10000000, FRAME = 0x8000, POISON = 0x1122334455667788L;
    private static int totalChecks;

    private Transfer21a216Test() { }

    private static final class Mem extends RawMemory190 implements Transfer216Api.Memory {
        final List<Access> accesses = new ArrayList<>();
        @Override protected void observed(Access access) { accesses.add(access); }
    }

    private record Port(String kind, long function, long allocator, long argument, int alignment, int site) { }

    private static final class Ports implements Transfer216Api.Calls {
        final List<Port> events = new ArrayList<>();
        Consumer<Port> allocateHook = event -> { };
        Consumer<Port> releaseHook = event -> { };
        @Override public long allocate08(long function, long allocator, long bytes, int alignment, int site) {
            Port event = new Port("allocate", function, allocator, bytes, alignment, site);
            events.add(event);
            allocateHook.accept(event);
            return NEW;
        }
        @Override public void release16(long function, long allocator, long pointer, int alignment, int site) {
            Port event = new Port("release", function, allocator, pointer, alignment, site);
            events.add(event);
            releaseHook.accept(event);
        }
    }

    private static final class Exhausted extends RuntimeException {
        private static final long serialVersionUID = 1L;
    }

    private static final class Limit implements Transfer216Api.Budget {
        private int left;
        int steps;
        Limit(int left) { this.left = left; }
        @Override public void step() {
            if (left-- == 0) throw new Exhausted();
            steps++;
        }
    }

    private static Mem memory(long sourceAllocator, int destinationCapacity, int destinationCount, int sourceCount) {
        Mem memory = new Mem();
        header(memory, D, DB, destinationCapacity, destinationCount, A);
        header(memory, S, SB, 5, sourceCount, sourceAllocator);
        memory.put64(D + 0x18, POISON);
        memory.put64(S + 0x18, ~POISON);
        memory.put64(A, VA);
        memory.put64(B, VB);
        memory.put64(VA + 8, 0xaaa8);
        memory.put64(VA + 16, 0xaaa16);
        memory.put64(VB + 8, 0xbbb8);
        memory.put64(VB + 16, 0xbbb16);
        memory.put32(IMAGE + 0x49f64f0, 0x3fc00000);
        block(memory, DB, 0x101, 0x102);
        block(memory, DB + 16, 0x103, 0x104);
        block(memory, DB + 32, 0x105, 0x106);
        block(memory, SB, 0x201, 0x202);
        block(memory, SB + 16, 0x203, 0x204);
        return memory;
    }

    private static void header(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        memory.put64(address, pointer);
        memory.put32(address + 8, capacity);
        memory.put32(address + 12, count);
        memory.put64(address + 16, allocator);
    }

    private static void block(Mem memory, long address, long low, long high) {
        memory.put64(address, low);
        memory.put64(address + 8, high);
    }

    private static void eq(long expected, long actual) {
        totalChecks++;
        if (expected != actual) throw new AssertionError("expected=" + Long.toUnsignedString(expected, 16)
                + " actual=" + Long.toUnsignedString(actual, 16));
    }

    private static void truth(boolean value) {
        totalChecks++;
        if (!value) throw new AssertionError("expected true");
    }

    private static void headerEquals(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        eq(pointer, memory.peek64(address));
        eq(capacity, memory.peek32(address + 8));
        eq(count, memory.peek32(address + 12));
        eq(allocator, memory.peek64(address + 16));
    }

    private static void payloadEquals(Mem memory, long address, long low, long high) {
        eq(low, memory.peek64(address));
        eq(high, memory.peek64(address + 8));
    }

    private static void port(Ports ports, int index, String kind, long function, long allocator, long argument, int site) {
        totalChecks++;
        Port expected = new Port(kind, function, allocator, argument, 8, site);
        if (!expected.equals(ports.events.get(index))) throw new AssertionError("port " + index + " " + ports.events);
    }

    private static long invoke(Operation operation, Mem memory, Ports ports, Limit limit) {
        return operation.run(new Input(D, S, IMAGE, FRAME), memory, ports, limit);
    }

    private static int access(Mem memory, String operation, long address, int from) {
        for (int index = from; index < memory.accesses.size(); index++) {
            Access value = memory.accesses.get(index);
            if (value.operation().equals(operation) && value.address() == address) return index;
        }
        throw new AssertionError("missing " + operation + " " + Long.toUnsignedString(address, 16));
    }

    private static void sameAllocator(Operation operation) {
        Mem memory = memory(A, 7, 3, 2);
        Ports ports = new Ports();
        eq(D, invoke(operation, memory, ports, new Limit(32)));
        headerEquals(memory, D, SB, 5, 2, A);
        headerEquals(memory, S, 0, 0, 0, A);
        eq(1, ports.events.size());
        port(ports, 0, "release", 0xaaa16, A, DB, 0x21a508f);
        eq(POISON, memory.peek64(D + 24));
        eq(~POISON, memory.peek64(S + 24));
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= DB && value.address() < SB + 32));
    }

    private static void sameHeader(Operation operation) {
        Mem memory = memory(A, 7, 3, 2);
        Ports ports = new Ports();
        eq(D, operation.run(new Input(D, D, IMAGE, FRAME), memory, ports, new Limit(32)));
        headerEquals(memory, D, 0, 0, 0, A);
        eq(1, ports.events.size());
        port(ports, 0, "release", 0xaaa16, A, DB, 0x21a508f);
    }

    private static void emptySource(Operation operation) {
        Mem memory = memory(B, 7, 3, 0);
        Ports ports = new Ports();
        eq(D, invoke(operation, memory, ports, new Limit(32)));
        headerEquals(memory, D, DB, 7, 0, A);
        headerEquals(memory, S, SB, 5, 0, B);
        eq(0, ports.events.size());
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= DB && value.address() < SB + 32));
    }

    private static void reuseCapacity(Operation operation) {
        Mem memory = memory(B, 4, 3, 2);
        Ports ports = new Ports();
        eq(D, invoke(operation, memory, ports, new Limit(32)));
        headerEquals(memory, D, DB, 4, 2, A);
        headerEquals(memory, S, SB, 5, 0, B);
        payloadEquals(memory, DB, 0x201, 0x202);
        payloadEquals(memory, DB + 16, 0x203, 0x204);
        payloadEquals(memory, DB + 32, 0x105, 0x106);
        eq(0, ports.events.size());
        int zeroCount = access(memory, "w32", D + 12, 0);
        int firstPayload = access(memory, "r64", SB, 0);
        truth(zeroCount < firstPayload);
        int firstStore = access(memory, "w64", DB, firstPayload);
        truth(access(memory, "r64", SB + 8, firstPayload) < firstStore);
        truth(access(memory, "r32", D + 12, firstStore) > access(memory, "w64", DB + 24, firstStore));
    }

    private static void growth(Operation operation) {
        Mem memory = memory(B, 1, 3, 2);
        Ports ports = new Ports();
        eq(D, invoke(operation, memory, ports, new Limit(32)));
        headerEquals(memory, D, NEW, 2, 2, A);
        headerEquals(memory, S, SB, 5, 0, B);
        payloadEquals(memory, NEW, 0x201, 0x202);
        payloadEquals(memory, NEW + 16, 0x203, 0x204);
        eq(2, ports.events.size());
        port(ports, 0, "allocate", 0xaaa8, A, 32, 0x21a51b9);
        port(ports, 1, "release", 0xaaa16, A, DB, 0x21a5223);
        truth(access(memory, "r64", D, access(memory, "w64", NEW + 24, 0)) > 0);
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= DB && value.address() < DB + 48));
    }

    private static void allocationCallback(Operation operation) {
        Mem memory = memory(B, 1, 3, 2);
        Ports ports = new Ports();
        long changed = DB + 0x100;
        block(memory, changed, 0x901, 0x902);
        ports.allocateHook = event -> {
            memory.put64(D, changed);
            memory.put32(D + 12, 1);
            memory.put64(S, 0xdead0000);
            memory.put32(S + 12, 0);
        };
        eq(D, invoke(operation, memory, ports, new Limit(32)));
        headerEquals(memory, D, NEW, 2, 2, A);
        payloadEquals(memory, NEW, 0x201, 0x202);
        payloadEquals(memory, NEW + 16, 0x203, 0x204);
        payloadEquals(memory, NEW + 32, 0x901, 0x902);
        headerEquals(memory, S, 0xdead0000, 5, 0, B);
        eq(2, ports.events.size());
        port(ports, 0, "allocate", 0xaaa8, A, 32, 0x21a51b9);
        port(ports, 1, "release", 0xaaa16, A, changed, 0x21a5223);
        int lastSourceWrite = access(memory, "w64", NEW + 24, 0);
        int oldPointer = access(memory, "r64", D, lastSourceWrite);
        truth(oldPointer > lastSourceWrite);
        int oldPayload = access(memory, "r64", changed, oldPointer);
        truth(access(memory, "r64", D, oldPayload) > access(memory, "w64", NEW + 40, oldPayload));
    }

    private static void recursiveRecheck(Operation operation) {
        Mem memory = memory(A, 7, 3, 2);
        Ports ports = new Ports();
        ports.releaseHook = event -> {
            if (event.site() == 0x21a508f) memory.put64(D + 16, B);
        };
        eq(D, invoke(operation, memory, ports, new Limit(64)));
        headerEquals(memory, D, NEW, 2, 2, B);
        headerEquals(memory, S, SB, 5, 0, A);
        payloadEquals(memory, NEW, 0x201, 0x202);
        payloadEquals(memory, NEW + 16, 0x203, 0x204);
        eq(3, ports.events.size());
        port(ports, 0, "release", 0xaaa16, A, DB, 0x21a508f);
        port(ports, 1, "allocate", 0xbbb8, B, 32, 0x21a51b9);
        port(ports, 2, "release", 0xbbb16, B, 0, 0x21a5223);
        headerEquals(memory, FRAME + 0x20, 0, 0, 0, FRAME + 0x40);
        eq(IMAGE + 0x46b3a90, memory.peek64(FRAME + 0x40));
        eq(IMAGE + 0x54de260, memory.peek64(FRAME + 0x448));
        boolean untouched = false;
        try { memory.peek8(FRAME + 0x50); } catch (IllegalStateException expected) { untouched = true; }
        truth(untouched);
        long entryReads = memory.accesses.stream().filter(value -> value.operation().equals("r64")
                && (value.address() == D + 16 || value.address() == S + 16 || value.address() == FRAME + 0x30)).count();
        truth(entryReads >= 8);
    }

    private static void headerAlias(Operation operation) {
        Mem memory = memory(B, 4, 3, 1);
        memory.put64(D, D);
        block(memory, SB, D, (1L << 32) | 4);
        Ports ports = new Ports();
        eq(D, invoke(operation, memory, ports, new Limit(32)));
        eq(A, memory.peek64(D));
        eq(POISON, memory.peek64(D + 8));
        eq(D, memory.peek64(D + 16));
        eq((2L << 32) | 4, memory.peek64(D + 24));
        eq(0, memory.peek32(S + 12));
        eq(0, ports.events.size());
        int copied = access(memory, "w64", D + 8, 0);
        truth(access(memory, "r32", D + 12, copied) > copied);
        truth(access(memory, "r64", D + 16, copied) > copied);
    }

    private static void floatOverflowPrefix(Operation operation) {
        Mem memory = memory(B, 0x60000000, 3, Integer.MAX_VALUE);
        Ports ports = new Ports();
        boolean exhausted = false;
        try { invoke(operation, memory, ports, new Limit(1)); } catch (Exhausted expected) { exhausted = true; }
        truth(exhausted);
        eq(1, ports.events.size());
        port(ports, 0, "allocate", 0xaaa8, A, 0x7fffffff0L, 0x21a51b9);
        headerEquals(memory, D, DB, 0x60000000, 0, A);
        headerEquals(memory, S, SB, 5, Integer.MAX_VALUE, B);
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= DB && value.address() < SB + 32));
    }

    public static void main(String[] arguments) {
        String selected = arguments.length == 0 ? "all" : arguments[0];
        String[] names = {"sameAllocator", "sameHeader", "emptySource", "reuseCapacity", "growth",
                "allocationCallback", "recursiveRecheck", "headerAlias", "floatOverflowPrefix"};
        List<Consumer<Operation>> cases = List.of(Transfer21a216Test::sameAllocator,
                Transfer21a216Test::sameHeader, Transfer21a216Test::emptySource,
                Transfer21a216Test::reuseCapacity, Transfer21a216Test::growth,
                Transfer21a216Test::allocationCallback, Transfer21a216Test::recursiveRecheck,
                Transfer21a216Test::headerAlias, Transfer21a216Test::floatOverflowPrefix);
        int completed = 0;
        for (int index = 0; index < names.length; index++) {
            if (!selected.equals("all") && !selected.equals(names[index])) continue;
            int before = totalChecks;
            cases.get(index).accept(Transfer21a216::execute);
            System.out.println("PASS " + names[index] + " checks=" + (totalChecks - before));
            completed++;
        }
        if (completed == 0) throw new IllegalArgumentException("unknown case " + selected);
        System.out.println("DONE cases=" + completed + " checks=" + totalChecks
                + " scope=owner-normalRAM-8-returning-plus-1-boundedprefix native=0 Game=0");
    }
}
