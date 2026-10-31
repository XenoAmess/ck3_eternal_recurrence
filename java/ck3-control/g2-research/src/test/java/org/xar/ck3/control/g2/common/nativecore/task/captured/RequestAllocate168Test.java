package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** Owner tests after two rejected model classes; supplied Java roles only. */
public final class RequestAllocate168Test {
    private static final long BASE = 0x100000000L;
    private static final long HEAP_A = 0xfedcba9800001234L;
    private static final long HEAP_B = 0x8000000000005678L;
    private static final int POISON = 0x12345678;

    private static final class Fixture implements NativeTaskMemory, RequestAllocate424fda0.Ports {
        private final long selectedBytes;
        private final long[] results;
        private final Cell32 cell = new Cell32(POISON);
        private final List<String> events = new ArrayList<>();
        private final List<Long> handles = new ArrayList<>();
        private final List<Long> sizes = new ArrayList<>();
        private final List<Integer> flags = new ArrayList<>();
        private long heap = HEAP_A;
        private int attempts;
        private int queryResult = -7;
        private int gateResult = Integer.MIN_VALUE;
        private boolean changeHeapAtGate;

        private Fixture(long selectedBytes, long... results) {
            this.selectedBytes = selectedBytes;
            this.results = results;
        }

        @Override
        public long readPointer(long address) {
            assertEquals(BASE + 0x5c5de30L, address);
            events.add("ReadHeap");
            return heap;
        }

        @Override
        public int readInt32(long address) { throw new AssertionError("Unexpected DWORD read"); }
        @Override
        public void writeInt32(long address, int value) { throw new AssertionError("Unexpected memory DWORD write"); }
        @Override
        public void writeInt64(long address, long value) { throw new AssertionError("Unexpected QWORD write"); }

        @Override
        public int call424e250() {
            events.add("Query");
            return queryResult;
        }

        @Override
        public int call424cffc(long knownRcx) {
            assertEquals(selectedBytes, knownRcx);
            events.add("Gate");
            if (changeHeapAtGate) { heap = HEAP_B; }
            return gateResult;
        }

        @Override
        public long heapAlloc(long heapHandleBits, int flagsBits, long bytesBits) {
            events.add("Heap");
            assertEquals(heap, heapHandleBits);
            assertEquals(0, flagsBits);
            assertEquals(selectedBytes, bytesBits);
            handles.add(heapHandleBits);
            flags.add(flagsBits);
            sizes.add(bytesBits);
            if (attempts >= results.length) { throw new AssertionError("Unexpected allocation attempt"); }
            return results[attempts++];
        }

        @Override
        public Cell32 call423b18c() {
            events.add("Cell");
            return cell;
        }
    }

    @Test
    public void unsignedBoundariesAndDirectSuccessKeepRawWidths() {
        Fixture zero = new Fixture(1L, Long.MIN_VALUE);
        assertEquals(Long.MIN_VALUE, RequestAllocate424fda0.allocate(BASE, 0L, zero, zero));
        assertEquals(List.of("ReadHeap", "Heap"), zero.events);
        assertEquals(List.of(1L), zero.sizes);
        assertEquals(List.of(0), zero.flags);
        assertEquals(POISON, zero.cell.value);

        Fixture maximum = new Fixture(-32L, 0xfedcba9876543210L);
        assertEquals(0xfedcba9876543210L,
                RequestAllocate424fda0.allocate(BASE, -32L, maximum, maximum));
        assertEquals(List.of("ReadHeap", "Heap"), maximum.events);
        assertEquals(List.of(-32L), maximum.sizes);
        assertEquals(POISON, maximum.cell.value);

        Fixture rejected = new Fixture(-31L);
        assertEquals(0L, RequestAllocate424fda0.allocate(BASE, -31L, rejected, rejected));
        assertEquals(List.of("Cell"), rejected.events);
        assertEquals(12, rejected.cell.value);
        assertEquals(0, rejected.attempts);
    }

    @Test
    public void retriesReloadHeapAndFailuresWriteOnlyTheTypedCell() {
        Fixture retry = new Fixture(8L, 0L, 0x8000000000000abcL);
        retry.changeHeapAtGate = true;
        assertEquals(0x8000000000000abcL, RequestAllocate424fda0.allocate(BASE, 8L, retry, retry));
        assertEquals(List.of("ReadHeap", "Heap", "Query", "Gate", "ReadHeap", "Heap"), retry.events);
        assertEquals(List.of(HEAP_A, HEAP_B), retry.handles);
        assertEquals(List.of(8L, 8L), retry.sizes);
        assertEquals(List.of(0, 0), retry.flags);
        assertEquals(POISON, retry.cell.value);

        Fixture queryZero = new Fixture(8L, 0L);
        queryZero.queryResult = 0;
        assertEquals(0L, RequestAllocate424fda0.allocate(BASE, 8L, queryZero, queryZero));
        assertEquals(List.of("ReadHeap", "Heap", "Query", "Cell"), queryZero.events);
        assertEquals(12, queryZero.cell.value);
        assertEquals(1, queryZero.attempts);

        Fixture gateZero = new Fixture(8L, 0L);
        gateZero.gateResult = 0;
        assertEquals(0L, RequestAllocate424fda0.allocate(BASE, 8L, gateZero, gateZero));
        assertEquals(List.of("ReadHeap", "Heap", "Query", "Gate", "Cell"), gateZero.events);
        assertEquals(12, gateZero.cell.value);
        assertEquals(1, gateZero.attempts);
    }
}
