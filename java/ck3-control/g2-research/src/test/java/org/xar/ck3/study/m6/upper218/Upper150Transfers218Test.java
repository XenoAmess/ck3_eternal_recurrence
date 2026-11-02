package org.xar.ck3.study.m6.upper218;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.study.m6.element150.Element150Inputs;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.transfer216.Transfer216Api;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217;

/** Two new same-RAM upper executions. Opaque release scripts only; manual main, not Native/Game. */
public final class Upper150Transfers218Test {
    private static final long D = 0x8000000100001000L, S = 0x8000000100001100L;
    private static final long IMAGE = 0x10000000, FRAME = 0x9000;
    private static final long A16 = IMAGE + 0x54de260, A4 = IMAGE + 0x54de268;
    private static final long TABLE16 = 0x6000, TABLE4 = 0x6100, POINTER16 = 0x2000, POINTER4 = 0x3000;
    private static int checks;
    private Upper150Transfers218Test() { }

    private static final class Mem extends RawMemory190 implements Upper150Inputs218.Memory {
        final List<Access> accesses = new ArrayList<>();
        @Override protected void observed(Access access) { accesses.add(access); }
    }
    private record Release(String lane, long function, long allocator, long pointer, int alignment, int site) { }
    private static final class Limit implements Transfer216Api.Budget, Transfer4Api217.Budget {
        int steps;
        @Override public void step() { if (++steps > 16) throw new AssertionError("software entry bound"); }
    }
    private static final class Ports16 implements Transfer216Api.Calls {
        final Mem memory; final long source; final boolean callbacks; final List<Release> events;
        Ports16(Mem memory, long source, boolean callbacks, List<Release> events) {
            this.memory = memory; this.source = source; this.callbacks = callbacks; this.events = events;
        }
        @Override public long allocate08(long function, long allocator, long bytes, int alignment, int site) {
            throw new AssertionError("unexpected allocate16");
        }
        @Override public void release16(long function, long allocator, long pointer, int alignment, int site) {
            events.add(new Release("16", function, allocator, pointer, alignment, site));
            if (callbacks) memory.put32(source + 8, 0x77889900);
        }
    }
    private static final class Ports4 implements Transfer4Api217.Calls {
        final Mem memory; final long source; final boolean callbacks; final List<Release> events;
        Ports4(Mem memory, long source, boolean callbacks, List<Release> events) {
            this.memory = memory; this.source = source; this.callbacks = callbacks; this.events = events;
        }
        @Override public long allocate08(long function, long allocator, long bytes, int alignment, int site) {
            throw new AssertionError("unexpected allocate4");
        }
        @Override public void release16(long function, long allocator, long pointer, int alignment, int site) {
            events.add(new Release("4", function, allocator, pointer, alignment, site));
            if (callbacks) { memory.put32(source + 0x40, 0x33445566); memory.put8(source + 0x44, 0xe7); }
        }
        @Override public void copy4226860(long destination, long source, long bytes, int site) {
            throw new AssertionError("unexpected COPY");
        }
        @Override public void reverse4220aa4(long begin, long end, int site) {
            throw new AssertionError("unexpected reverse");
        }
    }
    private static void eq(long expected, long actual) {
        checks++;
        if (expected != actual) throw new AssertionError("expected=" + Long.toUnsignedString(expected, 16)
                + " actual=" + Long.toUnsignedString(actual, 16));
    }
    private static void truth(boolean value) { checks++; if (!value) throw new AssertionError("expected true"); }
    private static void header(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        memory.put64(address, pointer); memory.put32(address + 8, capacity);
        memory.put32(address + 12, count); memory.put64(address + 16, allocator);
    }
    private static void headerEquals(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        eq(pointer, memory.peek64(address)); eq(capacity, memory.peek32(address + 8));
        eq(count, memory.peek32(address + 12)); eq(allocator, memory.peek64(address + 16));
    }
    private static void checkReleases(List<Release> events) {
        eq(2, events.size());
        truth(events.get(0).equals(new Release("16", 0xaaa16, A16, 0, 8, 0x21a508f)));
        truth(events.get(1).equals(new Release("4", 0xbbb16, A4, 0, 4, 0xb2ef06)));
    }
    private static Mem seed(long source) {
        Mem memory = new Mem();
        memory.put32(source + 8, 0x12345678);
        memory.put32(source + 0xc, 0x55667788);
        memory.put32(source + 0x40, 0x11223344);
        memory.put8(source + 0x44, 0xa5);
        header(memory, source + 0x10, POINTER16, 5, 2, A16);
        header(memory, source + 0x28, POINTER4, 7, 1, A4);
        memory.put32(D + 0xc, 0x55667788);
        memory.put64(A16, TABLE16); memory.put64(A4, TABLE4);
        memory.put64(TABLE16 + 16, 0xaaa16); memory.put64(TABLE4 + 16, 0xbbb16);
        return memory;
    }
    private static long execute(Mem memory, long source, boolean callbacks, List<Release> events, Limit budget) {
        return Upper150Transfers218.copy(new Upper150Inputs218.Input(new Element150Inputs.Input(D, source, IMAGE), FRAME),
                memory, new Ports16(memory, source, callbacks, events), new Ports4(memory, source, callbacks, events), budget, budget);
    }
    private static void separateHeadersCallbackTiming() {
        Mem memory = seed(S); List<Release> events = new ArrayList<>(); Limit budget = new Limit();
        eq(D, execute(memory, S, true, events, budget));
        eq(IMAGE + 0x45648a0, memory.peek64(D));
        eq(0x12345678, memory.peek32(D + 8)); eq(0x77889900, memory.peek32(S + 8));
        eq(0x55667788, memory.peek32(D + 0xc));
        eq(0x33445566, memory.peek32(D + 0x40)); eq(0xe7, memory.peek8(D + 0x44));
        headerEquals(memory, D + 0x10, POINTER16, 5, 2, A16);
        headerEquals(memory, D + 0x28, POINTER4, 7, 1, A4);
        headerEquals(memory, S + 0x10, 0, 0, 0, A16);
        headerEquals(memory, S + 0x28, 0, 0, 0, A4);
        checkReleases(events); eq(3, budget.steps);
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= POINTER16 && value.address() < POINTER4 + 4));
        eq(0x12345678, memory.accesses.stream().filter(value -> value.operation().equals("r32")
                && value.address() == S + 8).findFirst().orElseThrow().bits());
    }
    private static void selfAliasClearsBothHeaders() {
        Mem memory = seed(D); List<Release> events = new ArrayList<>(); Limit budget = new Limit();
        eq(D, execute(memory, D, false, events, budget));
        eq(IMAGE + 0x45648a0, memory.peek64(D));
        eq(0x12345678, memory.peek32(D + 8)); eq(0x55667788, memory.peek32(D + 0xc));
        eq(0x11223344, memory.peek32(D + 0x40)); eq(0xa5, memory.peek8(D + 0x44));
        headerEquals(memory, D + 0x10, 0, 0, 0, A16); headerEquals(memory, D + 0x28, 0, 0, 0, A4);
        checkReleases(events); eq(3, budget.steps);
    }
    public static void main(String[] arguments) {
        String selected = arguments.length == 0 ? "all" : arguments[0]; int completed = 0;
        if (selected.equals("all") || selected.equals("separateHeadersCallbackTiming")) {
            int before = checks; separateHeadersCallbackTiming(); completed++;
            System.out.println("PASS separateHeadersCallbackTiming checks=" + (checks - before));
        }
        if (selected.equals("all") || selected.equals("selfAliasClearsBothHeaders")) {
            int before = checks; selfAliasClearsBothHeaders(); completed++;
            System.out.println("PASS selfAliasClearsBothHeaders checks=" + (checks - before));
        }
        if (completed == 0) throw new IllegalArgumentException("unknown case " + selected);
        System.out.println("DONE cases=" + completed + " checks=" + checks
                + " scope=sameRAM-parent150-known216217 no-recursive-frame-branch-coverage native=0 Game=0");
    }
}
