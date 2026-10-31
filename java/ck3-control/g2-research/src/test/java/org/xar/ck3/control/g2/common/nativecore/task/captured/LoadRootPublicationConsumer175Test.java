package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Supplied strict publisher/actual-consumer composition; no Win32/current-world/Save claim. */
public final class LoadRootPublicationConsumer175Test {
    private static final long B = 0x100000000L;
    private static final long GLOBAL = B + 0x5C6A520L;
    private static final long SELF = B + 0x18000L;
    private static final long OBJECT = B + 0x10000L;
    private static final long VPTR = B + 0x2000L;
    private static final long COL = B + 0x3000L;
    private static final long SOURCE = B + 0x5514438L;
    private static final long TARGET = B + 0x5514460L;
    private static final long DT = B + 0x4000L;
    private static final long DS = B + 0x4100L;
    private static final long FIRST_TARGET = 0x9000000000005301L;
    private static final long SECOND_TARGET = 0x8000000000005501L;

    private static Fixture scenario(boolean legacyC28, long returnedPayload) {
        Fixture f = new Fixture(GLOBAL).w(GLOBAL, SELF);
        if (legacyC28) {
            f.q(SELF + 8L, B + 0x1A000L).q(B + 0x1A000L, B + 0x1B000L)
                    .q(B + 0x1B028L, FIRST_TARGET)
                    .call(new LoadIdlerRootPublication175.Invocation(0x383E53CL,
                            FIRST_TARGET, B + 0x1A000L, OptionalLong.empty(), false));
        } else {
            f.q(SELF + 8L, 0L);
        }
        f.q(SELF + 0x10L, OBJECT).q(OBJECT, VPTR).q(VPTR + 0x28L, SECOND_TARGET)
                .call(new LoadIdlerRootPublication175.Invocation(0x383E550L,
                        SECOND_TARGET, OBJECT, OptionalLong.empty(), true));
        f.q(GLOBAL, SELF).q(SELF + 0x10L, OBJECT)
                .q(OBJECT, VPTR).q(VPTR - 8L, COL)
                .d(COL + 4L, 0x20).d(COL + 8L, 0).d(OBJECT, 0x2000)
                .d(COL, legacyC28 ? 0 : 1);
        if (legacyC28) {
            f.api(COL, B);
        } else {
            f.d(COL + 0x14L, 0x3000);
        }
        f.d(COL + 0x10L, 0x100).d(B + 0x104L, legacyC28 ? 3 : 1)
                .d(COL + 0x10L, 0x100).d(B + 0x10CL, 0x200).d(B + 0x108L, 2)
                .d(B + 0x200L, 0x4000).d(DT, 0x5514460);
        if (legacyC28) {
            f.b(DT + 0x14L, 0);
        }
        f.d(DT + 4L, 1).d(DT, 0x5514460)
                .b(TARGET + 0x10L, 'T').b(SOURCE + 0x10L, 'S')
                .d(B + 0x204L, 0x4100).d(DS, 0x5514438)
                .d(DS + 0xCL, -1).d(DS + 8L, 0x20)
                .b(DT + 0x14L, 0).b(DS + 0x14L, 0);
        if (legacyC28) {
            // C28 records target offset-16 before returning its final RSI descriptor.
            f.d(DT + 0xCL, -1).d(DT + 8L, -16);
        }
        // Runtime computes complete=OBJECT-0x20, then target mdisp=-16; getter reads +0x28.
        return f.d(DT + 0xCL, -1).d(DT + 8L, -16).q(B + 0xFFF8L, returnedPayload);
    }

    private static long run(Fixture memory) {
        LoadIdlerRootPublication175.publish383e520(B, SELF, memory, memory);
        return LoadSharedGetterC45df0.get(B, memory,
                LoadSharedRuntimeConsumer.ports(B, memory,
                        LoadHierarchyRuntimeConsumer.ports(memory, memory)));
    }

    @Test public void publishedRootFeedsActualGetterAndBothActualHierarchyRoutes() {
        Fixture first = scenario(false, 0x8000000000ABCDEFL);
        assertEquals(0x8000000000ABCDEFL, run(first));
        first.done();
        Fixture second = scenario(true, 0xFEDCBA9876543210L);
        assertEquals(0xFEDCBA9876543210L, run(second));
        second.done();
    }

private static final class Fixture implements LoadIdlerRootPublication175.Memory, LoadHierarchySearch173.Memory, LoadIdlerRootPublication175.Ports, LoadRuntimeImportBinding.WindowsApiPorts {
    private final long globalAddress;
    private final ArrayDeque<Object> events = new ArrayDeque<>();
    private final Map<Long, Long> storage = new HashMap<>();
    private LoadRuntime4260e74.LocalSlot64 rememberedSlot = null;
    private long expectedReturnedBase = 0L;

    private Fixture(long globalAddress) { this.globalAddress = globalAddress; }

    private record ReadEvent(int width, long address, int value) { }
    private record ReadPointerEvent(long address, long value) { }
    private record WriteEvent(long address, long value) { }
    private record ApiEvent(long pcValue, long returnedBase) { }

    Fixture d(long address, int value) { events.add(new ReadEvent(32, address, value)); return this; }
    Fixture q(long address, long value) { events.add(new ReadPointerEvent(address, value)); return this; }
    Fixture b(long address, int value) { events.add(new ReadEvent(8, address, value)); return this; }
    Fixture w(long address, long value) { events.add(new WriteEvent(address, value)); return this; }
    Fixture call(LoadIdlerRootPublication175.Invocation expected) { events.add(expected); return this; }
    Fixture api(long pcValue, long returnedBase) { events.add(new ApiEvent(pcValue, returnedBase)); return this; }

    void done() { assertTrue(events.isEmpty()); }

    private void checkSlot() {
        if (rememberedSlot != null) {
            assertEquals(OptionalLong.of(expectedReturnedBase), rememberedSlot.value());
        }
    }

    @Override
    public long readPointer(long address) {
        checkSlot();
        if (address == globalAddress) {
            Long actual = storage.get(address);
            if (actual == null) throw new IllegalStateException("Missing write for global");
            if (events.isEmpty()) throw new IllegalStateException("Missing read event");
            Object obj = events.removeFirst();
            if (!(obj instanceof ReadPointerEvent)) throw new IllegalStateException("Wrong event type");
            ReadPointerEvent e = (ReadPointerEvent) obj;
            assertEquals(address, e.address());
            assertEquals(actual.longValue(), e.value());
            return actual;
        }
        if (events.isEmpty()) throw new IllegalStateException("Missing read event");
        Object obj = events.removeFirst();
        if (!(obj instanceof ReadPointerEvent)) throw new IllegalStateException("Wrong event type");
        ReadPointerEvent e = (ReadPointerEvent) obj;
        assertEquals(address, e.address());
        return e.value();
    }

    @Override
    public int readInt32(long address) {
        checkSlot();
        if (events.isEmpty()) throw new IllegalStateException("Missing read event");
        Object obj = events.removeFirst();
        if (!(obj instanceof ReadEvent)) throw new IllegalStateException("Wrong event type");
        ReadEvent e = (ReadEvent) obj;
        assertEquals(32, e.width());
        assertEquals(address, e.address());
        return e.value();
    }

    @Override
    public int readUnsigned8(long address) {
        checkSlot();
        if (events.isEmpty()) throw new IllegalStateException("Missing read event");
        Object obj = events.removeFirst();
        if (!(obj instanceof ReadEvent)) throw new IllegalStateException("Wrong event type");
        ReadEvent e = (ReadEvent) obj;
        assertEquals(8, e.width());
        assertEquals(address, e.address());
        return e.value();
    }

    @Override
    public void writeInt32(long address, int value) { throw new UnsupportedOperationException(); }

    @Override
    public void writeInt64(long address, long value) {
        if (events.isEmpty()) throw new IllegalStateException("Missing write event");
        Object obj = events.removeFirst();
        if (!(obj instanceof WriteEvent)) throw new IllegalStateException("Wrong event type");
        WriteEvent e = (WriteEvent) obj;
        assertEquals(address, e.address());
        assertEquals(value, e.value());
        if (address != globalAddress) throw new IllegalStateException("Write address mismatch");
        storage.put(address, value);
    }

    @Override
    public void invoke(LoadIdlerRootPublication175.Invocation actual) {
        if (events.isEmpty()) throw new IllegalStateException("Missing invocation event");
        Object obj = events.removeFirst();
        if (!(obj instanceof LoadIdlerRootPublication175.Invocation)) throw new IllegalStateException("Wrong event type");
        LoadIdlerRootPublication175.Invocation expected = (LoadIdlerRootPublication175.Invocation) obj;
        assertEquals(expected.siteRva(), actual.siteRva());
        assertEquals(expected.targetBits(), actual.targetBits());
        assertEquals(expected.rcx(), actual.rcx());
        assertEquals(expected.rdxBits(), actual.rdxBits());
        assertEquals(expected.tail(), actual.tail());
    }

    @Override
    public long rtlPcToFileHeader(long pcValue, LoadRuntime4260e74.LocalSlot64 baseOfImage) {
        if (events.isEmpty()) throw new IllegalStateException("Missing api event");
        Object obj = events.removeFirst();
        if (!(obj instanceof ApiEvent)) throw new IllegalStateException("Wrong event type");
        ApiEvent e = (ApiEvent) obj;
        assertEquals(pcValue, e.pcValue());
        assertEquals(OptionalLong.empty(), baseOfImage.value());
        baseOfImage.store(0xBADL);
        rememberedSlot = baseOfImage;
        expectedReturnedBase = e.returnedBase();
        return e.returnedBase();
    }
}
}
