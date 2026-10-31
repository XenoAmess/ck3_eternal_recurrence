package org.xar.ck3.research.m3;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;

public final class MapInsertMoveSlotBindingValidation193 {
    private MapInsertMoveSlotBindingValidation193() { }

    private record Step(String kind, long address, long low, long high) { }

    private static int topChecks;
    private static void check(boolean condition, String message) {
        topChecks++;
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        topChecks = 0;
        testSuccessfulInsert();
        testDelegatedRoles();
        testForeignMemoryRejection();
        System.out.println("BIND193 topChecks=" + topChecks + " groups=3 boundEvents=10 delegatedRoles=8 intReturns=2 foreignRejections=1");
    }

    private static void testSuccessfulInsert() {
        SharedMemoryImpl memory = new SharedMemoryImpl(List.of(
            new Step("I32", 0x5100, 0x13579BDF, 0),
            new Step("BYTE", 0x5104, 165, 0),
            new Step("CLEANUP", 0x5108, 0, 0),
            new Step("R128", 0x6200, 0x1122334455667788L, 0x99AABBCCDDEEFF00L),
            new Step("W128", 0x5108, 0x1122334455667788L, 0x99AABBCCDDEEFF00L),
            new Step("R128", 0x6210, 0x0102030405060708L, 0x8070605040302010L),
            new Step("W128", 0x5118, 0x0102030405060708L, 0x8070605040302010L),
            new Step("I64", 0x6210, 0, 0),
            new Step("I64", 0x6218, 15, 0),
            new Step("BYTE", 0x6200, 0, 0)
        ));
        memory.put(0x6200, 8, 0x1122334455667788L);
        memory.put(0x6208, 8, 0x99AABBCCDDEEFF00L);
        memory.put(0x6210, 8, 0x0102030405060708L);
        memory.put(0x6218, 8, 0x8070605040302010L);
        CleanupPortImpl cleanup = new CleanupPortImpl(memory);
        DelegatePortImpl delegate = new DelegatePortImpl();
        MapInsertMoveSlotBinding193 binder = new MapInsertMoveSlotBinding193(delegate, cleanup);
        check(!(delegate.calls != 0 || cleanup.calls != 0 || memory.cursor != 0), "constructor touched collaborators");
        binder.insertSlotC3cf10(memory, 0xC3BAB8L, 0x5100, 165, 0x13579BDF, 0x6200);
        check(!(memory.cursor != 10), "bound script not exhausted");
        check(!(cleanup.calls != 1), "cleanup count");
        check(!(delegate.calls != 0 || delegate.insertSlotCalled), "bound edge delegated");
    }

    private static void testDelegatedRoles() {
        ForeignMemoryImpl memory = new ForeignMemoryImpl();
        CleanupPortImpl cleanup = new CleanupPortImpl(null);
        DelegatePortImpl delegate = new DelegatePortImpl();
        MapInsertMoveSlotBinding193 binder = new MapInsertMoveSlotBinding193(delegate, cleanup);

        int eqResult = binder.equal3f6d2b0(memory, 0xC3B990L, 0x1111L, 0x2222L);
        check(!(eqResult != 42), "equal3f6d2b0 return mismatch");
        check(!(delegate.equalMemory != memory), "equal3f6d2b0 memory identity mismatch");
        check(!(delegate.equalSiteRva != 0xC3B990L), "equal3f6d2b0 site mismatch");
        check(!(delegate.equalRcx != 0x1111L || delegate.equalRdx != 0x2222L), "equal3f6d2b0 args mismatch");

        binder.rehashC3a400(memory, 0xC3A400L, 0x3333L);
        check(!(delegate.rehashMemory != memory), "rehashC3a400 memory identity mismatch");
        check(!(delegate.rehashSiteRva != 0xC3A400L || delegate.rehashMap != 0x3333L), "rehashC3a400 args mismatch");

        binder.insertC3a5f0(memory, 0xC3A5F0L, 0x4444L, 0x5555L, 0x6666, 0x7777L);
        check(!(delegate.insertMemory != memory), "insertC3a5f0 memory identity mismatch");
        check(!(delegate.insertSiteRva != 0xC3A5F0L || delegate.insertMap != 0x4444L || delegate.insertResult != 0x5555L), "insertC3a5f0 args mismatch");
        check(!(delegate.insertHash != 0x6666 || delegate.insertDescriptor != 0x7777L), "insertC3a5f0 hash/descriptor mismatch");

        binder.destroy856050(memory, 0x856050L, 0x8888L);
        check(!(delegate.destroyMemory != memory), "destroy856050 memory identity mismatch");
        check(!(delegate.destroySiteRva != 0x856050L || delegate.destroyDescriptor != 0x8888L), "destroy856050 args mismatch");

        int capResult = binder.capacity86e160(memory, 0x86E160L, 0x9999, 0xAAAA);
        check(!(capResult != 99), "capacity86e160 return mismatch");
        check(!(delegate.capacityMemory != memory), "capacity86e160 memory identity mismatch");
        check(!(delegate.capacitySiteRva != 0x86E160L || delegate.capacityEcx != 0x9999 || delegate.capacityEdx != 0xAAAA), "capacity86e160 args mismatch");

        binder.reserveC3b700(memory, 0xC3B700L, 0xBBBB, 0xCCCC);
        check(!(delegate.reserveMemory != memory), "reserveC3b700 memory identity mismatch");
        check(!(delegate.reserveSiteRva != 0xC3B700L || delegate.reserveMap != 0xBBBB || delegate.reserveEdx != 0xCCCC), "reserveC3b700 args mismatch");

        binder.overflow86f210(memory, 0x86F210L, 0xDDDD, 0xEEEE);
        check(!(delegate.overflowMemory != memory), "overflow86f210 memory identity mismatch");
        check(!(delegate.overflowSiteRva != 0x86F210L || delegate.overflowRcx != 0xDDDD || delegate.overflowRdx != 0xEEEE), "overflow86f210 args mismatch");

        binder.terminal4232cf4(memory, 0x4232CF4L);
        check(!(delegate.terminalMemory != memory), "terminal4232cf4 memory identity mismatch");
        check(!(delegate.terminalSiteRva != 0x4232CF4L), "terminal4232cf4 site mismatch");

        check(!(cleanup.wasCalled), "Cleanup should not be called for delegated roles");
        check(!(delegate.calls != 8), "exactly eight delegate calls");
        check(!(memory.touches != 0), "delegation touched foreign storage");
    }

    private static void testForeignMemoryRejection() {
        ForeignMemoryImpl memory = new ForeignMemoryImpl();
        CleanupPortImpl cleanup = new CleanupPortImpl(null);
        DelegatePortImpl delegate = new DelegatePortImpl();
        MapInsertMoveSlotBinding193 binder = new MapInsertMoveSlotBinding193(delegate, cleanup);
        check(!(delegate.calls != 0 || cleanup.calls != 0 || memory.touches != 0), "constructor touched foreign witnesses");
        boolean rejected = false;
        try {
            binder.insertSlotC3cf10(memory, 0xC3BAF7L, 0x7100, 3, 0x2468ACE, 0x7200);
        } catch (IllegalArgumentException expected) {
            rejected = true;
        }
        check(!(!rejected), "foreign Memory accepted");
        check(!(memory.touches != 0 || cleanup.calls != 0 || delegate.calls != 0 || delegate.insertSlotCalled), "foreign Memory touched before rejection");
    }

    private static final class SharedMemoryImpl implements MapInsertMoveSlotBinding193.SharedMemory {
        private final Map<Long, Byte> storage = new HashMap<>();
        private final List<Step> script;
        private int cursor;

        SharedMemoryImpl(List<Step> script) { this.script = script; }

        private void step(String kind, long address, long low, long high) {
            if (cursor >= script.size()) throw new AssertionError("extra operation " + kind);
            Step expected = script.get(cursor++);
            if (!expected.kind().equals(kind) || expected.address() != address
                    || expected.low() != low || expected.high() != high)
                throw new AssertionError("script mismatch at " + (cursor - 1) + ": " + kind);
        }

        private long load(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte b = storage.get(address + i);
                if (b == null) throw new AssertionError("unseeded address " + (address + i));
                value |= (long) Byte.toUnsignedInt(b) << (i * 8);
            }
            return value;
        }

        private void put(long address, int width, long value) {
            for (int i = 0; i < width; i++) storage.put(address + i, (byte) (value >>> (i * 8)));
        }

        @Override public int readUnsigned8(long address) {
            int value = (int) load(address, 1);
            step("RBYTE", address, value, 0);
            return value;
        }
        @Override public int readUnsignedByte(long address) { return readUnsigned8(address); }
        @Override public void write8(long address, int value) {
            step("BYTE", address, value & 255, 0);
            put(address, 1, value);
        }
        @Override public void writeByte(long address, byte value) { write8(address, value); }
        @Override public void writeInt16(long address, short value) {
            step("I16", address, value, 0);
            put(address, 2, value);
        }
        @Override public long readPointer(long address) {
            long value = load(address, 8);
            step("POINTER", address, value, 0);
            return value;
        }
        @Override public int readInt32(long address) {
            int value = (int) load(address, 4);
            step("R32", address, value, 0);
            return value;
        }
        @Override public void writeInt32(long address, int value) {
            step("I32", address, value, 0);
            put(address, 4, value);
        }
        @Override public void writeInt64(long address, long value) {
            step("I64", address, value, 0);
            put(address, 8, value);
        }
        @Override public MapInsert191Api.Bytes16 read128(long address) {
            long low = load(address, 8), high = load(address + 8, 8);
            step("R128", address, low, high);
            return new MapInsert191Api.Bytes16(low, high);
        }
        @Override public void write128(long address, MapInsert191Api.Bytes16 value) {
            step("W128", address, value.low(), value.high());
            put(address, 8, value.low());
            put(address + 8, 8, value.high());
        }
        @Override public RequestE92780.Raw128 readRaw128(long address) {
            long low = load(address, 8), high = load(address + 8, 8);
            step("R128", address, low, high);
            return new RequestE92780.Raw128(low, high);
        }
        @Override public void writeRaw128(long address, RequestE92780.Raw128 value) {
            step("W128", address, value.low(), value.high());
            put(address, 8, value.low());
            put(address + 8, 8, value.high());
        }
    }

    private static final class ForeignMemoryImpl implements MapInsert191Api.Memory {
        private int touches;
        private AssertionError touched() { touches++; return new AssertionError("foreign storage touched"); }
        @Override public int readUnsigned8(long address) { throw touched(); }
        @Override public void write8(long address, int value) { throw touched(); }
        @Override public MapInsert191Api.Bytes16 read128(long address) { throw touched(); }
        @Override public void write128(long address, MapInsert191Api.Bytes16 value) { throw touched(); }
        @Override public long readPointer(long address) { throw touched(); }
        @Override public int readInt32(long address) { throw touched(); }
        @Override public void writeInt32(long address, int value) { throw touched(); }
        @Override public void writeInt64(long address, long value) { throw touched(); }
    }

    private static final class CleanupPortImpl implements MoveSlotApi193.Ports {
        private final SharedMemoryImpl expectedMemory;
        private boolean wasCalled;
        private int calls;
        CleanupPortImpl(SharedMemoryImpl expectedMemory) { this.expectedMemory = expectedMemory; }
        @Override public void call856050(RequestE92780.Memory memory, long descriptor) {
            calls++;
            wasCalled = true;
            check(expectedMemory != null && memory == expectedMemory,
                "cleanup Memory identity or unexpected cleanup");
            expectedMemory.step("CLEANUP", descriptor, 0, 0);
        }
    }

    private static final class DelegatePortImpl implements MapInsert191Api.Ports {
        int calls;
        boolean insertSlotCalled = false;

        MapInsert191Api.Memory equalMemory = null;
        long equalSiteRva = 0;
        long equalRcx = 0;
        long equalRdx = 0;
        @Override public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
            calls++;
            equalMemory = memory;
            equalSiteRva = siteRva;
            equalRcx = rcx;
            equalRdx = rdx;
            return 42;
        }

        @Override public void insertSlotC3cf10(MapInsert191Api.Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
            calls++;
            insertSlotCalled = true;
            throw new AssertionError("replaced slot must not delegate");
        }

        MapInsert191Api.Memory rehashMemory = null;
        long rehashSiteRva = 0;
        long rehashMap = 0;
        @Override public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map) {
            calls++;
            rehashMemory = memory;
            rehashSiteRva = siteRva;
            rehashMap = map;
        }

        MapInsert191Api.Memory insertMemory = null;
        long insertSiteRva = 0;
        long insertMap = 0;
        long insertResult = 0;
        int insertHash = 0;
        long insertDescriptor = 0;
        @Override public void insertC3a5f0(MapInsert191Api.Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
            calls++;
            insertMemory = memory;
            insertSiteRva = siteRva;
            insertMap = map;
            insertResult = result;
            insertHash = hash;
            insertDescriptor = descriptor;
        }

        MapInsert191Api.Memory destroyMemory = null;
        long destroySiteRva = 0;
        long destroyDescriptor = 0;
        @Override public void destroy856050(MapInsert191Api.Memory memory, long siteRva, long descriptor) {
            calls++;
            destroyMemory = memory;
            destroySiteRva = siteRva;
            destroyDescriptor = descriptor;
        }

        MapInsert191Api.Memory capacityMemory = null;
        long capacitySiteRva = 0;
        int capacityEcx = 0;
        int capacityEdx = 0;
        @Override public int capacity86e160(MapInsert191Api.Memory memory, long siteRva, int ecx, int edx) {
            calls++;
            capacityMemory = memory;
            capacitySiteRva = siteRva;
            capacityEcx = ecx;
            capacityEdx = edx;
            return 99;
        }

        MapInsert191Api.Memory reserveMemory = null;
        long reserveSiteRva = 0;
        long reserveMap = 0;
        int reserveEdx = 0;
        @Override public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx) {
            calls++;
            reserveMemory = memory;
            reserveSiteRva = siteRva;
            reserveMap = map;
            reserveEdx = edx;
        }

        MapInsert191Api.Memory overflowMemory = null;
        long overflowSiteRva = 0;
        long overflowRcx = 0;
        long overflowRdx = 0;
        @Override public void overflow86f210(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
            calls++;
            overflowMemory = memory;
            overflowSiteRva = siteRva;
            overflowRcx = rcx;
            overflowRdx = rdx;
        }

        MapInsert191Api.Memory terminalMemory = null;
        long terminalSiteRva = 0;
        @Override public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva) {
            calls++;
            terminalMemory = memory;
            terminalSiteRva = siteRva;
        }
    }
}
