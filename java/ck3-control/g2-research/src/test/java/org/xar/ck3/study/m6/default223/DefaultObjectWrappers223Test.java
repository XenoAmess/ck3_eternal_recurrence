package org.xar.ck3.study.m6.default223;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.ToLongFunction;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Calls;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Input;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Invocation;
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Memory;

/** Manual logical-GPR/object-RAM checks. Opaque children do not stand in for full185 or Native execution. */
public final class DefaultObjectWrappers223Test {
    private static final long IMAGE = 0x140000000L;
    private static final long OBJECT = IMAGE + 0x54DE260;
    private static final long TABLE = IMAGE + 0x448A1E8;
    private static final long SLOT08 = IMAGE + 0x8571D0;
    private static final long SLOT10 = IMAGE + 0x8571C0;
    private static int checks;
    private static int scenes;
    private DefaultObjectWrappers223Test() { }

    private record Event(String kind, Invocation actual) { }
    private static final class Ports implements Calls {
        final List<Event> events = new ArrayList<>();
        ToLongFunction<Invocation> call = actual -> { throw new AssertionError("Unexpected CALL"); };
        ToLongFunction<Invocation> tail = actual -> { throw new AssertionError("Unexpected TAIL"); };
        @Override public long call(Invocation actual) { events.add(new Event("call", actual)); return call.applyAsLong(actual); }
        @Override public long tailJump(Invocation actual) { events.add(new Event("tailJump", actual)); return tail.applyAsLong(actual); }
    }
    private static final class Ram implements Memory {
        final Map<Long, Long> words = new HashMap<>();
        final List<Long> reads = new ArrayList<>();
        Ram seed(long address, long value) { words.put(address, value); return this; }
        @Override public long read64(long address) {
            reads.add(address);
            Long value = words.get(address);
            if (value == null) { throw new AssertionError("Unexpected read64 " + Long.toHexString(address)); }
            return value.longValue();
        }
        @Override public int read32(long address) { throw new AssertionError("read32"); }
        @Override public int read8(long address) { throw new AssertionError("read8"); }
        @Override public void write32(long address, int value) { throw new AssertionError("write32"); }
        @Override public void write64(long address, long value) { throw new AssertionError("write64"); }
        @Override public void write8(long address, int value) { throw new AssertionError("write8"); }
    }
    private static void same(Object expected, Object actual) {
        checks++;
        if (!expected.equals(actual)) { throw new AssertionError("Expected " + expected + " but got " + actual); }
    }
    private static void sameLong(long expected, long actual) { same(Long.valueOf(expected), Long.valueOf(actual)); }
    private static void scene(String name, Runnable body) {
        int previous = checks;
        body.run(); scenes++;
        System.out.println("PASS " + name + " checks=" + (checks - previous));
    }
    private static Invocation entry08(long rax, long rcx, long rdx, long r8, long r9) {
        return new Invocation(0x8558A0, SLOT08, rax, rcx, rdx, r8, r9);
    }
    private static Invocation entry10(long rax, long rcx, long rdx, long r8, long r9) {
        return new Invocation(0x85585B, SLOT10, rax, rcx, rdx, r8, r9);
    }
    private static void direct08() {
        Invocation entry = entry08(0xF000000000000001L, 0x2222, 0x8000000000000030L,
                0xFFFFFFFF00000008L, 0x9000000000000040L);
        Ports ports = new Ports(); ports.call = actual -> 0x8000000000000050L;
        sameLong(0x8000000000000050L, DefaultObjectWrappers223.fromSlot08(entry, IMAGE, ports));
        same(List.of(new Event("call", new Invocation(0x8571D7, IMAGE + 0x4223B94,
                0xF000000000000001L, 0x8000000000000030L, 0x8000000000000030L,
                0xFFFFFFFF00000008L, 0x9000000000000040L))), ports.events);
    }
    private static void direct10Zero() {
        sameLong(0xF000000000000011L, DefaultObjectWrappers223.fromSlot10(
                entry10(0xF000000000000011L, 0x3333, 0, 0x28, 0x39), IMAGE, null));
    }
    private static void direct10Nonzero() {
        Invocation entry = entry10(0x8000000000000012L, 0x4444, 0xF000000000000050L, 0x48, 0x59);
        Ports ports = new Ports(); ports.tail = actual -> 0x9000000000000060L;
        sameLong(0x9000000000000060L, DefaultObjectWrappers223.fromSlot10(entry, IMAGE, ports));
        same(List.of(new Event("tailJump", new Invocation(0x8571C8, IMAGE + 0x40EC530,
                0x8000000000000012L, 0xF000000000000050L, 0xF000000000000050L, 0x48, 0x59))), ports.events);
    }
    private static Ram seeded(long original, long originalTable, long slotOffset, long slotTarget) {
        return new Ram().seed(original, originalTable).seed(originalTable + 0x38, IMAGE + 0x86E140)
                .seed(original + 0x408, OBJECT).seed(OBJECT, TABLE).seed(TABLE + slotOffset, slotTarget);
    }
    private static void whole08() {
        Ram ram = seeded(0x3800, 0x4800, 8, SLOT08);
        Ports ports = new Ports(); ports.call = actual -> 0x8000000000000070L;
        sameLong(0x8000000000000070L, StaticVirtualForwardWithDefaultObject223.fromSlot08(
                new Input(0x3800, 0x30, 8, 0xA000000000000001L), IMAGE, ram, ports));
        same(List.of(0x3800L, 0x4838L, 0x3C08L, OBJECT, TABLE + 8), ram.reads);
        same(List.of(new Event("call", new Invocation(0x8571D7, IMAGE + 0x4223B94,
                OBJECT, 0x30, 0x30, 8, SLOT08))), ports.events);
    }
    private static void whole10Null() {
        Ram ram = seeded(0x3900, 0x4900, 0x10, SLOT10);
        Ports ports = new Ports();
        sameLong(OBJECT, StaticVirtualForwardWithDefaultObject223.fromSlot10(
                new Input(0x3900, 0, 8, 0xA000000000000002L), IMAGE, ram, ports));
        same(List.of(0x3900L, 0x4938L, 0x3D08L, OBJECT, TABLE + 0x10), ram.reads);
        same(List.of(), ports.events);
    }
    private static void whole10Pointer() {
        Ram ram = seeded(0x3A00, 0x4A00, 0x10, SLOT10);
        Ports ports = new Ports(); ports.tail = actual -> 0x8000000000000080L;
        sameLong(0x8000000000000080L, StaticVirtualForwardWithDefaultObject223.fromSlot10(
                new Input(0x3A00, 0xF000000000000060L, 8, 0xA000000000000003L), IMAGE, ram, ports));
        same(List.of(0x3A00L, 0x4A38L, 0x3E08L, OBJECT, TABLE + 0x10), ram.reads);
        same(List.of(new Event("tailJump", new Invocation(0x8571C8, IMAGE + 0x40EC530,
                OBJECT, 0xF000000000000060L, 0xF000000000000060L, 8, TABLE))), ports.events);
    }
    private static void wrongSlotTargetDelegated() {
        Ram ram = seeded(0x3B00, 0x4B00, 8, SLOT10);
        Ports ports = new Ports(); ports.tail = actual -> 0x8000000000000090L;
        sameLong(0x8000000000000090L, StaticVirtualForwardWithDefaultObject223.fromSlot08(
                new Input(0x3B00, 0x50, 8, 0xA000000000000004L), IMAGE, ram, ports));
        same(List.of(0x3B00L, 0x4B38L, 0x3F08L, OBJECT, TABLE + 8), ram.reads);
        same(List.of(new Event("tailJump", new Invocation(0x8558A0, SLOT10,
                OBJECT, OBJECT, 0x50, 8, SLOT10))), ports.events);
    }
    private static void direct08Throws() {
        Invocation entry = entry08(0x99, 0x333, 0x90, 8, 0xAA);
        RuntimeException sentinel = new IllegalStateException("owner-direct-sentinel");
        Ports ports = new Ports(); ports.call = actual -> { throw sentinel; };
        try {
            DefaultObjectWrappers223.fromSlot08(entry, IMAGE, ports);
            throw new AssertionError("Expected exact controlled child failure");
        } catch (IllegalStateException actual) {
            checks++;
            if (actual != sentinel) { throw new AssertionError("Fault identity changed"); }
        }
        same(List.of(new Event("call", new Invocation(0x8571D7, IMAGE + 0x4223B94,
                0x99, 0x90, 0x90, 8, 0xAA))), ports.events);
    }
    public static void main(String[] args) {
        scene("direct08", DefaultObjectWrappers223Test::direct08);
        scene("direct10-zero", DefaultObjectWrappers223Test::direct10Zero);
        scene("direct10-nonzero", DefaultObjectWrappers223Test::direct10Nonzero);
        scene("whole08", DefaultObjectWrappers223Test::whole08);
        scene("whole10-null", DefaultObjectWrappers223Test::whole10Null);
        scene("whole10-pointer", DefaultObjectWrappers223Test::whole10Pointer);
        scene("wrong-slot-target-delegated", DefaultObjectWrappers223Test::wrongSlotTargetDelegated);
        scene("direct08-throws", DefaultObjectWrappers223Test::direct08Throws);
        System.out.println("PASS scenes=" + scenes + " checks=" + checks
                + " logicalFiveGprOnly=true noFull185ChildBinding=true noNativeOrGame=true");
    }
}
