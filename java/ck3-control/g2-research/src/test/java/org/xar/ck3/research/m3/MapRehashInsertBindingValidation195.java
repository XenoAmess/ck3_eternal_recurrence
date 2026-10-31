package org.xar.ck3.research.m3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.map191.MapInsert191Api;

public final class MapRehashInsertBindingValidation195 {
    private MapRehashInsertBindingValidation195() { }

    private record Step(String kind, long address, long low, long high) { }
    private record Call(String role, Object memory, long a, long b, long c, long d) { }
    private static int topChecks;
    private static int boundEvents;
    private static int boundChildPorts;
    private static int delegatedRoles;
    private static int longReturns;
    private static int foreignRejections;

    public static void main(String[] args) {
        topChecks = boundEvents = boundChildPorts = delegatedRoles = longReturns = foreignRejections = 0;
        testBoundFrame();
        testDelegates();
        testForeign();
        System.out.println("BIND195 topChecks=" + topChecks + " groups=3 boundEvents=" + boundEvents
                + " childPorts=" + boundChildPorts + " delegatedRoles=" + delegatedRoles
                + " longReturns=" + longReturns + " foreignRejections=" + foreignRejections);
    }

    private static void check(boolean condition, String message) {
        topChecks++;
        if (!condition) throw new AssertionError(message);
    }

    private static void testBoundFrame() {
        SharedMemoryImpl memory = new SharedMemoryImpl(List.of(
                new Step("R32", 0x1014, 1, 0),
                new Step("PTR", 0x1008, 0x5000, 0),
                new Step("R8", 0x502C, 0, 0),
                new Step("R8", 0x1018, 0, 0),
                new Step("CAPACITY", 0xC3BC2F, 2, 1),
                new Step("RESERVE", 0xC3BC3E, 0x1000, 1),
                new Step("W8", 0x1018, 2, 0),
                new Step("W8", 0x6FE0, 0, 0),
                new Step("W64", 0x6F40, 0x6FE0, 0),
                new Step("R32", 0x1014, 1, 0),
                new Step("PTR", 0x1008, 0x5000, 0),
                new Step("R8", 0x502C, 0, 0),
                new Step("R8", 0x1018, 2, 0),
                new Step("R32", 0x1010, 0, 0),
                new Step("R32", 0x101C, 0x40000000, 0),
                new Step("R8", 0x502C, 0, 0),
                new Step("W32", 0x5028, 0x13579BDF, 0),
                new Step("W8", 0x502C, 1, 0),
                new Step("W64", 0x5030, 0, 0),
                new Step("W64", 0x5040, 0, 0),
                new Step("W64", 0x5048, 0, 0),
                new Step("R128", 0x3000, 0x1122334455667788L, 0x99AABBCCDDEEFF00L),
                new Step("W128", 0x5030, 0x1122334455667788L, 0x99AABBCCDDEEFF00L),
                new Step("R128", 0x3010, 0x0102030405060708L, 0x8070605040302010L),
                new Step("W128", 0x5040, 0x0102030405060708L, 0x8070605040302010L),
                new Step("W64", 0x3010, 0, 0),
                new Step("W64", 0x3018, 15, 0),
                new Step("W8", 0x3000, 0, 0),
                new Step("R32", 0x1010, 0, 0),
                new Step("W32", 0x1010, 1, 0),
                new Step("W64", 0x7000, 0x5028, 0),
                new Step("W8", 0x7008, 1, 0)));
        memory.put(0x1008, 8, 0x5000);
        memory.put(0x1010, 4, 0);
        memory.put(0x1014, 4, 1);
        memory.put(0x1018, 1, 0);
        memory.put(0x101C, 4, 0x40000000);
        memory.put(0x502C, 1, 0);
        memory.put(0x3000, 8, 0x1122334455667788L);
        memory.put(0x3008, 8, 0x99AABBCCDDEEFF00L);
        memory.put(0x3010, 8, 0x0102030405060708L);
        memory.put(0x3018, 8, 0x8070605040302010L);
        ParentPorts delegate = new ParentPorts();
        ChildPorts insertPorts = new ChildPorts(memory);
        MapRehashInsertBinding195 binder = new MapRehashInsertBinding195(0x100000L, delegate, insertPorts);
        check(memory.cursor == 0 && delegate.calls.isEmpty() && insertPorts.calls == 0,
                "constructor touched collaborators");
        binder.callc3b960(memory, 0x1000, 0x7000, 0x13579BDF, 0x3000, 0x7FFF123456789ABCL);
        check(memory.cursor == 32, "bound script not exhausted");
        check(insertPorts.calls == 2, "bound child port count");
        check(delegate.calls.isEmpty(), "bound edge invoked parent delegate");
        check(memory.load(0x6FE0, 1) == 0, "actual child frame byte");
        check(memory.load(0x6F40, 8) == 0x6FE0, "actual child frame pointer");
        check(memory.load(0x7000, 8) == 0x5028 && memory.load(0x7008, 1) == 1,
                "actual child result storage");
        boundEvents = memory.cursor;
        boundChildPorts = insertPorts.calls;
    }

    private static void expect(ParentPorts ports, int index, String role, Object memory,
                               long a, long b, long c, long d) {
        check(ports.calls.size() == index + 1, "delegate count at " + role);
        Call actual = ports.calls.get(index);
        check(actual.role().equals(role) && actual.memory() == memory && actual.a() == a
                && actual.b() == b && actual.c() == c && actual.d() == d, "delegate inputs " + role);
    }

    private static void testDelegates() {
        ForeignMemory memory = new ForeignMemory();
        ParentPorts delegate = new ParentPorts();
        ChildPorts child = new ChildPorts(null);
        MapRehashInsertBinding195 binder = new MapRehashInsertBinding195(0x23456789L, delegate, child);
        check(delegate.calls.isEmpty() && child.calls == 0 && memory.touches == 0,
                "delegate constructor touched collaborators");
        long gs = binder.gs58(memory);
        check(gs == 0x1122334455667788L, "gs58 exact long return");
        longReturns++;
        expect(delegate, 0, "gs58", memory, 0, 0, 0, 0);
        binder.call4223a84(memory, 0x123456789ABCDEF0L);
        expect(delegate, 1, "call4223a84", memory, 0x123456789ABCDEF0L, 0, 0, 0);
        binder.call4223a24(memory, 0xFEDCBA9876543210L);
        expect(delegate, 2, "call4223a24", memory, 0xFEDCBA9876543210L, 0, 0, 0);
        long allocated = binder.allocatorSlot08(memory, 0x1111, 0x2222, 0x3333444455556666L, -8);
        check(allocated == 0x8877665544332211L, "allocator exact long return");
        longReturns++;
        expect(delegate, 3, "allocatorSlot08", memory, 0x1111, 0x2222, 0x3333444455556666L, -8);
        binder.allocatorSlot10(memory, 0x7777, 0x8888, 0x9999, 16);
        expect(delegate, 4, "allocatorSlot10", memory, 0x7777, 0x8888, 0x9999, 16);
        binder.call856050(memory, 0xAAAABBBBCCCCDDDDL);
        expect(delegate, 5, "call856050", memory, 0xAAAABBBBCCCCDDDDL, 0, 0, 0);
        binder.call86f210(memory, 0x1111222233334444L, 0x5555666677778888L);
        expect(delegate, 6, "call86f210", memory, 0x1111222233334444L, 0x5555666677778888L, 0, 0);
        binder.call4232cf4(memory);
        expect(delegate, 7, "call4232cf4", memory, 0, 0, 0, 0);
        check(memory.touches == 0 && child.calls == 0, "delegation touched storage or child ports");
        delegatedRoles = delegate.calls.size();
    }

    private static void testForeign() {
        ForeignMemory memory = new ForeignMemory();
        ParentPorts delegate = new ParentPorts();
        ChildPorts child = new ChildPorts(null);
        MapRehashInsertBinding195 binder = new MapRehashInsertBinding195(0, delegate, child);
        check(memory.touches == 0 && delegate.calls.isEmpty() && child.calls == 0,
                "foreign constructor touched collaborators");
        boolean rejected = false;
        try {
            binder.callc3b960(memory, 0x2100, 0x8100, 0x2468ACE, 0x3100, 0x7FFF0BADCAFEBABEL);
        } catch (IllegalArgumentException expected) {
            rejected = true;
            foreignRejections++;
        }
        check(rejected, "foreign Memory accepted");
        check(memory.touches == 0 && delegate.calls.isEmpty() && child.calls == 0,
                "foreign rejection happened after touch");
    }

    private static final class SharedMemoryImpl implements MapRehashInsertBinding195.SharedMemory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Step> script;
        private int cursor;
        SharedMemoryImpl(List<Step> script) { this.script = script; }
        private void step(String kind, long address, long low, long high) {
            if (cursor >= script.size()) throw new AssertionError("extra " + kind);
            Step expected = script.get(cursor++);
            if (!expected.kind().equals(kind) || expected.address() != address
                    || expected.low() != low || expected.high() != high)
                throw new AssertionError("event mismatch " + (cursor - 1) + " " + kind);
        }
        private void put(long address, int width, long value) {
            for (int i = 0; i < width; i++) bytes.put(address + i, (byte) (value >>> (8 * i)));
        }
        private long load(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) throw new AssertionError("unseeded " + (address + i));
                value |= (long) Byte.toUnsignedInt(b) << (8 * i);
            }
            return value;
        }
        @Override public long readPointer(long address) {
            long value = load(address, 8); step("PTR", address, value, 0); return value;
        }
        @Override public int readInt32(long address) {
            int value = (int) load(address, 4); step("R32", address, value, 0); return value;
        }
        @Override public void writeInt32(long address, int value) {
            step("W32", address, value, 0); put(address, 4, value);
        }
        @Override public void writeInt64(long address, long value) {
            step("W64", address, value, 0); put(address, 8, value);
        }
        @Override public int readUnsigned8(long address) {
            int value = (int) load(address, 1); step("R8", address, value, 0); return value;
        }
        @Override public void write8(long address, int value) {
            step("W8", address, value & 255, 0); put(address, 1, value);
        }
        @Override public MapInsert191Api.Bytes16 read128(long address) {
            long low = load(address, 8), high = load(address + 8, 8);
            step("R128", address, low, high); return new MapInsert191Api.Bytes16(low, high);
        }
        @Override public void write128(long address, MapInsert191Api.Bytes16 value) {
            step("W128", address, value.low(), value.high());
            put(address, 8, value.low()); put(address + 8, 8, value.high());
        }
    }

    private static final class ForeignMemory implements MapRehashApi190.Memory {
        private int touches;
        private AssertionError touched() { touches++; return new AssertionError("foreign Memory touched"); }
        @Override public long readPointer(long address) { throw touched(); }
        @Override public int readInt32(long address) { throw touched(); }
        @Override public void writeInt32(long address, int value) { throw touched(); }
        @Override public void writeInt64(long address, long value) { throw touched(); }
        @Override public int readUnsigned8(long address) { throw touched(); }
        @Override public void write8(long address, int value) { throw touched(); }
    }

    private static final class ParentPorts implements MapRehashApi190.Ports {
        private final List<Call> calls = new ArrayList<>();
        @Override public long gs58(C3e150Api180.Memory memory) {
            calls.add(new Call("gs58", memory, 0, 0, 0, 0)); return 0x1122334455667788L;
        }
        @Override public void call4223a84(C3e150Api180.Memory memory, long guard) {
            calls.add(new Call("call4223a84", memory, guard, 0, 0, 0));
        }
        @Override public void call4223a24(C3e150Api180.Memory memory, long guard) {
            calls.add(new Call("call4223a24", memory, guard, 0, 0, 0));
        }
        @Override public long allocatorSlot08(MapRehashApi190.Memory memory, long code, long allocator,
                                            long bytes, int alignment) {
            calls.add(new Call("allocatorSlot08", memory, code, allocator, bytes, alignment));
            return 0x8877665544332211L;
        }
        @Override public void allocatorSlot10(MapRehashApi190.Memory memory, long code, long allocator,
                                             long block, int alignment) {
            calls.add(new Call("allocatorSlot10", memory, code, allocator, block, alignment));
        }
        @Override public void callc3b960(MapRehashApi190.Memory memory, long map, long output, int hash,
                                       long descriptor, long flagAddress) {
            calls.add(new Call("unexpectedBoundDelegate", memory, map, output, hash, descriptor));
            throw new AssertionError("bound edge delegated");
        }
        @Override public void call856050(MapRehashApi190.Memory memory, long descriptor) {
            calls.add(new Call("call856050", memory, descriptor, 0, 0, 0));
        }
        @Override public void call86f210(MapRehashApi190.Memory memory, long output, long map) {
            calls.add(new Call("call86f210", memory, output, map, 0, 0));
        }
        @Override public void call4232cf4(MapRehashApi190.Memory memory) {
            calls.add(new Call("call4232cf4", memory, 0, 0, 0, 0));
        }
    }

    private static final class ChildPorts implements MapInsert191Api.Ports {
        private final SharedMemoryImpl expected;
        private int calls;
        ChildPorts(SharedMemoryImpl expected) { this.expected = expected; }
        private AssertionError unexpected() { calls++; return new AssertionError("unexpected child port"); }
        @Override public int capacity86e160(MapInsert191Api.Memory memory, long site, int ecx, int edx) {
            if (expected == null) throw unexpected();
            calls++;
            check(memory == expected, "capacity Memory identity");
            expected.step("CAPACITY", site, ecx, edx);
            return 1;
        }
        @Override public void reserveC3b700(MapInsert191Api.Memory memory, long site, long map, int edx) {
            if (expected == null) throw unexpected();
            calls++;
            check(memory == expected, "reserve Memory identity");
            expected.step("RESERVE", site, map, edx);
            memory.write8(map + 0x18L, 2);
        }
        @Override public int equal3f6d2b0(MapInsert191Api.Memory m, long site, long rcx, long rdx) {
            throw unexpected();
        }
        @Override public void insertSlotC3cf10(MapInsert191Api.Memory m, long site, long bucket, int probe,
                                            int hash, long descriptor) { throw unexpected(); }
        @Override public void rehashC3a400(MapInsert191Api.Memory m, long site, long map) { throw unexpected(); }
        @Override public void insertC3a5f0(MapInsert191Api.Memory m, long site, long map, long result,
                                         int hash, long descriptor) { throw unexpected(); }
        @Override public void destroy856050(MapInsert191Api.Memory m, long site, long descriptor) { throw unexpected(); }
        @Override public void overflow86f210(MapInsert191Api.Memory m, long site, long rcx, long rdx) { throw unexpected(); }
        @Override public void terminal4232cf4(MapInsert191Api.Memory m, long site) { throw unexpected(); }
    }
}
