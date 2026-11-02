package org.xar.ck3.study.m6.embedded219;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedElements37282B0;
import org.xar.ck3.study.m6.element190.RawMemory190;
import org.xar.ck3.study.m6.range8c194.Range8c194Inputs;
import org.xar.ck3.study.m6.transfer216.Transfer216Api;
import org.xar.ck3.study.m6.transfer217.Transfer4Api217;

/** Two new caller-layer software cases. Unknown delegate implementations are explicit scripts. */
public final class EmbeddedKnownTransfers219Test {
    private static final long D = 0x1000, S = 0x1100, OLD = 0x2000, SRC = 0x3000, NEW = 0x4000;
    private static final long A = 0x5000, VA = 0x6000, V16 = 0x6100, V4 = 0x6200;
    private static final long IMAGE = 0x10000000, FRAME = 0xa000;
    private static final long A16 = IMAGE + 0x54de260, A4 = IMAGE + 0x54de268;
    private static int checks;
    private EmbeddedKnownTransfers219Test() { }

    private static final class Mem extends RawMemory190 implements EmbeddedInputs219.Memory {
        final List<Access> accesses = new ArrayList<>();
        @Override protected void observed(Access access) { accesses.add(access); }
        @Override public Range8c194Inputs.Word16 read16(long address) {
            return new Range8c194Inputs.Word16(read64(address), read64(address + 8));
        }
        @Override public void write16(long address, Range8c194Inputs.Word16 value) {
            write64(address, value.lowRaw64()); write64(address + 8, value.highRaw64());
        }
    }
    private record Event(String name, List<Long> arguments) { }
    private static final class Limit implements Transfer216Api.Budget, Transfer4Api217.Budget {
        int count;
        @Override public void step() { if (++count > 16) throw new AssertionError("software entry budget"); }
    }
    private static void eq(long expected, long actual) {
        checks++;
        if (expected != actual) throw new AssertionError("expected=" + Long.toUnsignedString(expected, 16)
                + " actual=" + Long.toUnsignedString(actual, 16));
    }
    private static void truth(boolean value) { checks++; if (!value) throw new AssertionError("expected true"); }
    private static Event event(String name, long... arguments) {
        List<Long> values = new ArrayList<>(); for (long value : arguments) values.add(value);
        return new Event(name, List.copyOf(values));
    }
    private static void header(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        memory.put64(address, pointer); memory.put32(address + 8, capacity);
        memory.put32(address + 12, count); memory.put64(address + 16, allocator);
    }
    private static void headerEquals(Mem memory, long address, long pointer, int capacity, int count, long allocator) {
        eq(pointer, memory.peek64(address)); eq(capacity, memory.peek32(address + 8));
        eq(count, memory.peek32(address + 12)); eq(allocator, memory.peek64(address + 16));
    }
    private static void element(Mem memory, long address, int scalar, int tail, int flag, boolean old) {
        memory.put32(address + 8, scalar);
        header(memory, address + 0x10, old ? 0x7000 : 0, old ? 5 : 0, old ? 2 : 0, A16);
        header(memory, address + 0x28, old ? 0x7100 : 0, old ? 7 : 0, old ? 1 : 0, A4);
        memory.put32(address + 0x40, tail); memory.put8(address + 0x44, flag);
    }
    private static Mem seeded() {
        Mem memory = new Mem(); header(memory, D, OLD, 1, 1, A);
        memory.put64(S, SRC); memory.put32(S + 8, 2); memory.put32(S + 12, 2);
        memory.put64(A, VA); memory.put64(VA + 8, 0xf008);
        memory.put64(A16, V16); memory.put64(A4, V4);
        memory.put64(V16 + 16, 0xf016); memory.put64(V4 + 16, 0xf004);
        element(memory, OLD, 0x81, 0x91, 0xa1, true);
        element(memory, SRC, 0x101, 0x901, 0x21, false);
        element(memory, SRC + 0x48, 0x102, 0x902, 0x22, false);
        return memory;
    }
    private static void finalElement(Mem memory, long address, int scalar, int tail, int flag) {
        eq(IMAGE + 0x45648a0, memory.peek64(address)); eq(scalar, memory.peek32(address + 8));
        headerEquals(memory, address + 0x10, 0, 0, 0, A16); headerEquals(memory, address + 0x28, 0, 0, 0, A4);
        eq(tail, memory.peek32(address + 0x40)); eq(flag, memory.peek8(address + 0x44));
    }
    private static final class Delegate implements PendingEmbeddedElements37282B0.Calls {
        final Mem memory; final List<Event> events;
        int snapshots;
        Delegate(Mem memory, List<Event> events) { this.memory = memory; this.events = events; }
        private void same(PendingEmbeddedElements37282B0.Memory actual) { truth(actual == memory); }
        @Override public void call889780(PendingEmbeddedElements37282B0.Memory actual, long rcx, long rdx) {
            same(actual); events.add(event("889780", rcx, rdx));
        }
        @Override public long allocate(PendingEmbeddedElements37282B0.Memory actual, long target, long rcx, long rdx, int r8d) {
            same(actual); events.add(event("allocate", target, rcx, rdx, r8d)); return NEW;
        }
        @Override public void callDBDB80(PendingEmbeddedElements37282B0.Memory actual, long rcx, long rdx, int r8d, int r9d) {
            same(actual); events.add(event("DBDB80", rcx, rdx, r8d, r9d)); snapshots++;
            // Literal expectations frozen before any candidate: observe BEFORE the declared replacement script.
            headerEquals(memory, D, OLD, 1, 1, A);
            eq(IMAGE + 0x45648a0, memory.peek64(NEW)); eq(0x81, memory.peek32(NEW + 8));
            headerEquals(memory, NEW + 0x10, 0x7000, 5, 2, A16);
            headerEquals(memory, NEW + 0x28, 0x7100, 7, 1, A4);
            headerEquals(memory, OLD + 0x10, 0, 0, 0, A16);
            headerEquals(memory, OLD + 0x28, 0, 0, 0, A4);
            eq(0x91, memory.peek32(NEW + 0x40)); eq(0xa1, memory.peek8(NEW + 0x44));
            memory.put64(D, NEW); memory.put32(D + 8, 2);
        }
        @Override public void virtualDestroy(PendingEmbeddedElements37282B0.Memory actual, long target, long rcx, long rdx) {
            throw new AssertionError("unexpected destroy");
        }
        @Override public void copy16_21A5050(PendingEmbeddedElements37282B0.Memory actual, long destination, long source) {
            throw new AssertionError("known16 incorrectly delegated");
        }
        @Override public void copy4_B2EEE0(PendingEmbeddedElements37282B0.Memory actual, long destination, long source) {
            throw new AssertionError("known4 incorrectly delegated");
        }
        @Override public void copy16_8C70B0(PendingEmbeddedElements37282B0.Memory actual, long destination, long zero, long begin, long end) {
            throw new AssertionError("current194 should own empty range");
        }
        @Override public void copy4_ADD0D0(PendingEmbeddedElements37282B0.Memory actual, long destination, long zero, long begin, long end) {
            same(actual); events.add(event("ADD", destination, zero, begin, end));
        }
        @Override public long range16Virtual8(PendingEmbeddedElements37282B0.Memory actual, long target, long rcx, long rdx, long r8, long r9) {
            throw new AssertionError("unexpected range allocate");
        }
        @Override public void range16Virtual16(PendingEmbeddedElements37282B0.Memory actual, long target, long rcx, long rdx, long r8, long r9) {
            throw new AssertionError("unexpected range release");
        }
        @Override public void range16Direct8F8550(PendingEmbeddedElements37282B0.Memory actual, long rcx, long rdx, long r8, long r9) {
            throw new AssertionError("unexpected unreachable8F");
        }
    }
    private static final class Ports16 implements Transfer216Api.Calls {
        final List<Event> events; Ports16(List<Event> events) { this.events = events; }
        @Override public long allocate08(long function, long allocator, long bytes, int alignment, int site) {
            throw new AssertionError("unexpected nested16 allocate");
        }
        @Override public void release16(long function, long allocator, long pointer, int alignment, int site) {
            events.add(event("known16", function, allocator, pointer, alignment, site));
        }
    }
    private static final class Ports4 implements Transfer4Api217.Calls {
        final List<Event> events; Ports4(List<Event> events) { this.events = events; }
        @Override public long allocate08(long function, long allocator, long bytes, int alignment, int site) {
            throw new AssertionError("unexpected nested4 allocate");
        }
        @Override public void release16(long function, long allocator, long pointer, int alignment, int site) {
            events.add(event("known4", function, allocator, pointer, alignment, site));
        }
        @Override public void copy4226860(long destination, long source, long bytes, int site) { throw new AssertionError("unexpected COPY"); }
        @Override public void reverse4220aa4(long begin, long end, int site) { throw new AssertionError("unexpected reverse"); }
    }
    private static long execute(Mem memory, Delegate delegate, List<Event> events, Limit budget, long destination, long source) {
        return EmbeddedKnownTransfers219.copy(new EmbeddedInputs219.Input(destination, source, IMAGE, FRAME),
                memory, delegate, new Ports16(events), new Ports4(events), budget, budget);
    }
    private static void growthOneConstructorTwoAssignments() {
        Mem memory = seeded(); List<Event> events = new ArrayList<>(); Delegate delegate = new Delegate(memory, events); Limit budget = new Limit();
        eq(D, execute(memory, delegate, events, budget, D, S));
        List<Event> expected = List.of(event("889780", D, S), event("allocate", 0xf008, A, 144, 8),
                event("known16", 0xf016, A16, 0, 8, 0x21a508f), event("known4", 0xf004, A4, 0, 4, 0xb2ef06),
                event("DBDB80", D, NEW, 1, 2), event("ADD", NEW + 0x28, 0, 0, 0), event("ADD", NEW + 0x48 + 0x28, 0, 0, 0));
        truth(expected.equals(events)); eq(1, delegate.snapshots); eq(3, budget.count);
        headerEquals(memory, D, NEW, 2, 2, A);
        eq(SRC, memory.peek64(S)); eq(2, memory.peek32(S + 8)); eq(2, memory.peek32(S + 12));
        finalElement(memory, NEW, 0x101, 0x901, 0x21); finalElement(memory, NEW + 0x48, 0x102, 0x902, 0x22);
        headerEquals(memory, OLD + 0x10, 0, 0, 0, A16); headerEquals(memory, OLD + 0x28, 0, 0, 0, A4);
        truth(memory.accesses.stream().noneMatch(value -> value.address() >= 0x7000 && value.address() < 0x7104));
    }
    private static void selfGuardHasNoRamOrPortEffects() {
        Mem memory = new Mem(); List<Event> events = new ArrayList<>(); Delegate delegate = new Delegate(memory, events); Limit budget = new Limit();
        long same = 0x1234567800001000L;
        eq(same, execute(memory, delegate, events, budget, same, same));
        eq(0, memory.accesses.size()); eq(0, events.size()); eq(0, budget.count); eq(0, delegate.snapshots);
    }
    public static void main(String[] arguments) {
        String selected = arguments.length == 0 ? "all" : arguments[0]; int completed = 0;
        if (selected.equals("all") || selected.equals("growthOneConstructorTwoAssignments")) {
            int before = checks; growthOneConstructorTwoAssignments(); completed++;
            System.out.println("PASS growthOneConstructorTwoAssignments checks=" + (checks - before));
        }
        if (selected.equals("all") || selected.equals("selfGuardHasNoRamOrPortEffects")) {
            int before = checks; selfGuardHasNoRamOrPortEffects(); completed++;
            System.out.println("PASS selfGuardHasNoRamOrPortEffects checks=" + (checks - before));
        }
        if (completed == 0) throw new IllegalArgumentException("unknown case " + selected);
        System.out.println("DONE cases=" + completed + " checks=" + checks
                + " scope=new-pointer322-known-150-deepports logicalRAM-only noRecursiveFrameDynamicCredit native=0 Game=0");
    }
}
