package org.xar.ck3.study.m6.transfer217;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.element190.RawMemory190.Access;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Budget;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Calls;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Input;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Memory;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217.Operations;

/** Manual owner oracle. Controlled COPY/reverse/virtual ports do not qualify their native internals. */
public final class Transfer4B2217Test {
    private static final long D = 0x1000, S = 0x1100, DB = 0x2000, SB = 0x3000, NEW = 0x4000;
    private static final long A = 0x5000, B = 0x5100, VA = 0x6000, VB = 0x6100;
    private static final long IMAGE = 0x10000000, FRAME = 0x8000, POISON = 0x1122334455667788L;
    private static int checks;
    private Transfer4B2217Test() { }

    private static final class Mem extends RawMemory190 implements Memory {
        final List<Access> accesses = new ArrayList<>();
        @Override protected void observed(Access access) { accesses.add(access); }
    }

    private record Event(String kind, long function, long first, long second, long third, int alignment, int site) { }

    private static final class Ports implements Calls {
        final Mem memory;
        final List<Event> events = new ArrayList<>();
        Consumer<Event> allocateHook = event -> { };
        Consumer<Event> releaseHook = event -> { };
        Consumer<Event> copyHook = event -> { };
        Ports(Mem memory) { this.memory = memory; }
        @Override public long allocate08(long function, long allocator, long bytes, int alignment, int site) {
            Event event = new Event("allocate", function, allocator, bytes, 0, alignment, site);
            events.add(event);
            allocateHook.accept(event);
            return NEW;
        }
        @Override public void release16(long function, long allocator, long pointer, int alignment, int site) {
            Event event = new Event("release", function, allocator, pointer, 0, alignment, site);
            events.add(event);
            releaseHook.accept(event);
        }
        @Override public void copy4226860(long destination, long source, long bytes, int site) {
            Event event = new Event("copy", 0x4226860, destination, source, bytes, 0, site);
            events.add(event);
            if (bytes < 0 || bytes > 32) throw new AssertionError("outside declared controlled COPY script");
            int[] values = new int[(int) bytes];
            for (int index = 0; index < values.length; index++) values[index] = memory.read8(source + index);
            for (int index = 0; index < values.length; index++) memory.write8(destination + index, values[index]);
            copyHook.accept(event);
        }
        @Override public void reverse4220aa4(long begin, long end, int site) {
            // Declared no-op port: only caller's explicit lanes/ordering are being tested here.
            events.add(new Event("reverse", 0x4220aa4, begin, end, 0, 0, site));
        }
    }

    private static final class Limit implements Budget {
        private int remaining = 64;
        @Override public void step() { if (remaining-- == 0) throw new AssertionError("software recursion bound"); }
    }

    private static Mem memory(long sourceAllocator, int capacity, int count, int sourceCount) {
        Mem memory = new Mem();
        header(memory, D, DB, capacity, count, A);
        header(memory, S, SB, 5, sourceCount, sourceAllocator);
        memory.put64(D + 0x18, POISON);
        memory.put64(S + 0x18, ~POISON);
        memory.put64(A, VA); memory.put64(B, VB);
        memory.put64(VA + 8, 0xaaa8); memory.put64(VA + 16, 0xaaa16);
        memory.put64(VB + 8, 0xbbb8); memory.put64(VB + 16, 0xbbb16);
        memory.put32(IMAGE + 0x49f64f0, 0x3fc00000);
        for (int index = 0; index < 8; index++) {
            memory.put32(DB + index * 4L, 0x101 + index);
            memory.put32(SB + index * 4L, 0x201 + index);
        }
        return memory;
    }

    private static void header(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        memory.put64(address, pointer); memory.put32(address + 8, capacity);
        memory.put32(address + 12, count); memory.put64(address + 16, allocator);
    }
    private static void eq(long expected, long actual) {
        checks++;
        if (expected != actual) throw new AssertionError("expected=" + Long.toUnsignedString(expected, 16)
                + " actual=" + Long.toUnsignedString(actual, 16));
    }
    private static void truth(boolean value) { checks++; if (!value) throw new AssertionError("expected true"); }
    private static void headerEquals(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        eq(pointer, memory.peek64(address)); eq(capacity, memory.peek32(address + 8));
        eq(count, memory.peek32(address + 12)); eq(allocator, memory.peek64(address + 16));
    }
    private static void event(Ports ports, int index, String kind, long function,
            long first, long second, long third, int alignment, int site) {
        checks++;
        Event expected = new Event(kind, function, first, second, third, alignment, site);
        if (!expected.equals(ports.events.get(index))) throw new AssertionError("event " + index + " " + ports.events);
    }
    private static int access(Mem memory, String operation, long address, int from) {
        for (int index = from; index < memory.accesses.size(); index++) {
            Access value = memory.accesses.get(index);
            if (value.operation().equals(operation) && value.address() == address) return index;
        }
        throw new AssertionError("missing access " + operation + " " + Long.toUnsignedString(address, 16));
    }
    private static long move(Mem memory, Ports ports) {
        return Transfer4Move217.execute(new Input(D, S, IMAGE, FRAME), memory, ports, new Limit());
    }

    private static void sameAllocator() {
        Mem memory = memory(A, 7, 3, 2); Ports ports = new Ports(memory);
        eq(D, move(memory, ports));
        headerEquals(memory, D, SB, 5, 2, A); headerEquals(memory, S, 0, 0, 0, A);
        eq(1, ports.events.size()); event(ports, 0, "release", 0xaaa16, A, DB, 0, 4, 0xb2ef06);
        eq(POISON, memory.peek64(D + 24)); eq(~POISON, memory.peek64(S + 24));
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= DB && value.address() < SB + 32));
    }
    private static void sameHeader() {
        Mem memory = memory(A, 7, 3, 2); Ports ports = new Ports(memory);
        eq(D, Transfer4Move217.execute(new Input(D, D, IMAGE, FRAME), memory, ports, new Limit()));
        headerEquals(memory, D, 0, 0, 0, A); eq(1, ports.events.size());
        event(ports, 0, "release", 0xaaa16, A, DB, 0, 4, 0xb2ef06);
    }
    private static void emptySource() {
        Mem memory = memory(B, 7, 3, 0); Ports ports = new Ports(memory);
        eq(D, move(memory, ports));
        headerEquals(memory, D, DB, 7, 0, A); headerEquals(memory, S, SB, 5, 0, B);
        eq(0, ports.events.size());
        int zero = access(memory, "w32", D + 12, 0);
        int sourcePointer = access(memory, "r64", S, 0);
        int sourceCount = access(memory, "r32", S + 12, 0);
        truth(zero < sourcePointer && sourcePointer < sourceCount);
        truth(access(memory, "w32", S + 12, 0) > sourceCount);
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= DB && value.address() < SB + 32));
    }
    private static void reuseCapacity() {
        Mem memory = memory(B, 4, 3, 2); Ports ports = new Ports(memory);
        eq(D, move(memory, ports));
        headerEquals(memory, D, DB, 4, 2, A); headerEquals(memory, S, SB, 5, 0, B);
        eq(0x201, memory.peek32(DB)); eq(0x202, memory.peek32(DB + 4)); eq(0x103, memory.peek32(DB + 8));
        eq(1, ports.events.size()); event(ports, 0, "copy", 0x4226860, DB, SB, 8, 0, 0xb2effe);
        truth(access(memory, "r32", D + 12, access(memory, "w8", DB + 7, 0)) > 0);
    }
    private static void growthCallbacks() {
        Mem memory = memory(B, 1, 3, 2); Ports ports = new Ports(memory);
        long old2 = DB + 0x100, old3 = DB + 0x200, old4 = DB + 0x300, old5 = DB + 0x400;
        memory.put32(old4, 0x901);
        ports.allocateHook = value -> {
            memory.put64(D, old2); memory.put32(D + 12, 1);
            memory.put64(S, 0xdead0000); memory.put32(S + 12, 9);
        };
        ports.copyHook = value -> {
            if (value.site() == 0xb2efad) { memory.put64(D, old3); memory.put32(D + 12, 2); }
            if (value.site() == 0xb2efbb) { memory.put64(D, old4); memory.put32(D + 12, 1); }
            if (value.site() == 0xb2efd2) { memory.put64(D, old5); memory.put64(D + 16, B); }
        };
        eq(D, move(memory, ports));
        headerEquals(memory, D, NEW, 2, 2, B); headerEquals(memory, S, 0xdead0000, 5, 0, B);
        eq(0x201, memory.peek32(NEW)); eq(0x202, memory.peek32(NEW + 4)); eq(0x901, memory.peek32(NEW + 8));
        eq(5, ports.events.size());
        event(ports, 0, "allocate", 0xaaa8, A, 8, 0, 4, 0xb2ef9e);
        event(ports, 1, "copy", 0x4226860, NEW, old2, 0, 0, 0xb2efad);
        event(ports, 2, "copy", 0x4226860, NEW, SB, 8, 0, 0xb2efbb);
        event(ports, 3, "copy", 0x4226860, NEW + 8, old4, 4, 0, 0xb2efd2);
        event(ports, 4, "release", 0xbbb16, B, old5, 0, 4, 0xb2efe5);
        eq(0x3fc00000, memory.accesses.get(access(memory, "r32", IMAGE + 0x49f64f0, 0)).bits());
    }
    private static void reuseReverseLanes() {
        Mem memory = memory(B, 4, 3, 2); Ports ports = new Ports(memory);
        long changed = DB + 0x100;
        ports.copyHook = value -> { memory.put64(D, changed); memory.put32(D + 12, 1); };
        eq(D, move(memory, ports));
        headerEquals(memory, D, changed, 4, 3, A); headerEquals(memory, S, SB, 5, 0, B);
        eq(4, ports.events.size()); event(ports, 0, "copy", 0x4226860, DB, SB, 8, 0, 0xb2effe);
        event(ports, 1, "reverse", 0x4220aa4, changed, changed + 4, 0, 0, 0xb2f02d);
        event(ports, 2, "reverse", 0x4220aa4, changed + 4, changed + 12, 0, 0, 0xb2f038);
        event(ports, 3, "reverse", 0x4220aa4, changed, changed + 12, 0, 0, 0xb2f043);
        int totalWrite = access(memory, "w32", D + 12, access(memory, "r32", D + 12, 0));
        truth(totalWrite < access(memory, "w32", S + 12, 0));
    }
    private static void actualMutualRecursion() {
        Mem memory = memory(A, 7, 3, 2); Ports ports = new Ports(memory);
        ports.releaseHook = value -> { if (value.site() == 0xb2ef06) memory.put64(D + 16, B); };
        eq(D, move(memory, ports));
        headerEquals(memory, D, NEW, 2, 2, B); headerEquals(memory, S, SB, 5, 0, A);
        eq(0x201, memory.peek32(NEW)); eq(0x202, memory.peek32(NEW + 4));
        eq(6, ports.events.size());
        event(ports, 0, "release", 0xaaa16, A, DB, 0, 4, 0xb2ef06);
        event(ports, 1, "allocate", 0xbbb8, B, 8, 0, 4, 0xb2ef9e);
        event(ports, 2, "copy", 0x4226860, NEW, 0, 0, 0, 0xb2efad);
        event(ports, 3, "copy", 0x4226860, NEW, SB, 8, 0, 0xb2efbb);
        event(ports, 4, "copy", 0x4226860, NEW + 8, 0, 0, 0, 0xb2efd2);
        event(ports, 5, "release", 0xbbb16, B, 0, 0, 4, 0xb2efe5);
        long helper = FRAME - 0x460;
        headerEquals(memory, helper + 0x20, 0, 0, 0, helper + 0x40);
        eq(IMAGE + 0x44bbb10, memory.peek64(helper + 0x40));
        eq(IMAGE + 0x54de268, memory.peek64(helper + 0x448));
        boolean untouched = false;
        try { memory.peek8(helper + 0x50); } catch (IllegalStateException expected) { untouched = true; }
        truth(untouched);
    }
    private static final Operations NO_RECURSION = new Operations() {
        @Override public long move(Input input, Memory memory, Calls calls, Budget budget) { throw new AssertionError("unexpected move"); }
        @Override public void swap(Input input, Memory memory, Calls calls, Budget budget) { throw new AssertionError("unexpected swap"); }
    };
    private static void helperEqualAllocator() {
        Mem memory = memory(A, 7, 3, 2); Ports ports = new Ports(memory);
        Transfer4Swap217.execute(new Input(D, S, IMAGE, FRAME), memory, ports, new Limit(), NO_RECURSION);
        headerEquals(memory, D, SB, 5, 2, A); headerEquals(memory, S, DB, 7, 3, A);
        eq(0, ports.events.size());
        truth(memory.accesses.get(0).address() == S + 16 && memory.accesses.get(1).address() == D + 16);
    }
    private static void helperSignedDispatchAndCleanup() {
        Mem memory = memory(B, 7, 0, -1); Ports ports = new Ports(memory);
        List<Input> dispatches = new ArrayList<>();
        long temporary = FRAME + 0x20;
        Operations controlled = new Operations() {
            @Override public long move(Input input, Memory ram, Calls calls, Budget budget) {
                dispatches.add(input);
                if (dispatches.size() == 3) {
                    // Explicit isolated dispatch-port script, not an execution of the move algorithm.
                    memory.put64(temporary, DB); memory.put32(temporary + 12, 9); memory.put64(temporary + 16, B);
                }
                return 0;
            }
            @Override public void swap(Input input, Memory ram, Calls calls, Budget budget) { throw new AssertionError("unexpected swap"); }
        };
        Transfer4Swap217.execute(new Input(D, S, IMAGE, FRAME), memory, ports, new Limit(), controlled);
        eq(3, dispatches.size());
        truth(dispatches.get(0).equals(new Input(temporary, S, IMAGE, FRAME - 0x50)));
        truth(dispatches.get(1).equals(new Input(S, D, IMAGE, FRAME - 0x50)));
        truth(dispatches.get(2).equals(new Input(D, temporary, IMAGE, FRAME - 0x50)));
        eq(1, ports.events.size()); event(ports, 0, "release", 0xbbb16, B, DB, 0, 4, 0xb2eebb);
        eq(0, memory.peek32(temporary + 12));
        headerEquals(memory, D, DB, 7, 0, A); headerEquals(memory, S, SB, 5, -1, B);
        int sourceCount = access(memory, "r32", S + 12, 0);
        truth(sourceCount < access(memory, "w64", FRAME + 0x40, 0));
        eq(IMAGE + 0x44bbb10, memory.peek64(FRAME + 0x40));
        eq(IMAGE + 0x54de268, memory.peek64(FRAME + 0x448));
    }

    public static void main(String[] arguments) {
        String selected = arguments.length == 0 ? "all" : arguments[0];
        String[] names = {"sameAllocator", "sameHeader", "emptySource", "reuseCapacity", "growthCallbacks",
                "reuseReverseLanes", "actualMutualRecursion", "helperEqualAllocator", "helperSignedDispatchAndCleanup"};
        List<Runnable> cases = List.of(Transfer4B2217Test::sameAllocator, Transfer4B2217Test::sameHeader,
                Transfer4B2217Test::emptySource, Transfer4B2217Test::reuseCapacity, Transfer4B2217Test::growthCallbacks,
                Transfer4B2217Test::reuseReverseLanes, Transfer4B2217Test::actualMutualRecursion,
                Transfer4B2217Test::helperEqualAllocator, Transfer4B2217Test::helperSignedDispatchAndCleanup);
        int count = 0;
        for (int index = 0; index < names.length; index++) {
            if (!selected.equals("all") && !selected.equals(names[index])) continue;
            int before = checks; cases.get(index).run(); count++;
            System.out.println("PASS " + names[index] + " checks=" + (checks - before));
        }
        if (count == 0) throw new IllegalArgumentException("unknown case " + selected);
        System.out.println("DONE cases=" + count + " checks=" + checks
                + " scope=7bound-move+1equal-helper+1controlled-helperdispatch native=0 Game=0");
    }
}
