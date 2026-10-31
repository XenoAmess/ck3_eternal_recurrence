package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Owner supplied-memory composition; no Windows call or native ownership claim. */
public final class RequestRetryAllocation168Test {
    private static final long BASE = 0x100000000L;
    private static final long HEAP_A = 0x1234567887654321L;
    private static final long HEAP_B = 0x8000000000000123L;
    private static final long RESULT = 0xabcdef0123456789L;

    private static final class Fixture implements NativeTaskMemory, RequestRetryAllocationConsumer.Remainder {
        private final Cell32 cell = new Cell32(0x76543210);
        private final List<String> events = new ArrayList<>();
        private final List<Long> handles = new ArrayList<>();
        private final List<Long> sizes = new ArrayList<>();
        private long heap = HEAP_A;
        private int attempts;
        private int queries;
        private int cells;
        private int transfers;
        private boolean rejectSize;

        @Override
        public long readPointer(long address) {
            if (address == BASE + 0x5c5de30L) {
                events.add("HeapHandle");
                return heap;
            }
            if (address == BASE + 0x542f0b8L) {
                events.add("Encoded");
                return 1L;
            }
            if (address == BASE + 0x5c5d568L) {
                events.add("Key");
                return 0L;
            }
            throw new AssertionError("Unexpected QWORD address");
        }

        @Override
        public int readInt32(long address) { throw new AssertionError("Unexpected DWORD read"); }
        @Override
        public void writeInt32(long address, int value) { throw new AssertionError("Unexpected memory DWORD write"); }
        @Override
        public void writeInt64(long address, long value) { throw new AssertionError("Unexpected QWORD write"); }

        @Override
        public int call424e250() {
            if (rejectSize) { throw new AssertionError("Rejected size queried retry flag"); }
            queries++;
            events.add("Query");
            return 0;
        }

        @Override
        public long heapAlloc(long heapHandleBits, int flagsBits, long bytesBits) {
            if (rejectSize) { throw new AssertionError("Rejected size attempted allocation"); }
            events.add("HeapAlloc");
            assertEquals(0, flagsBits);
            assertEquals(1L, bytesBits);
            assertEquals(heap, heapHandleBits);
            handles.add(heapHandleBits);
            sizes.add(bytesBits);
            attempts++;
            if (attempts == 1) { return 0L; }
            if (attempts == 2) { return RESULT; }
            throw new AssertionError("Unexpected third allocation");
        }

        @Override
        public Cell32 call423b18c() {
            cells++;
            events.add("Cell");
            return cell;
        }

        private RequestGate424cffc.Ports gate(int targetEax, long outerSize) {
            RequestCriticalSectionImportBinding.WindowsApiPorts api = new RequestCriticalSectionImportBinding.WindowsApiPorts() {
                @Override
                public void enterCriticalSection(long criticalSectionPtr) {
                    assertEquals(0x105c5d330L, criticalSectionPtr);
                    assertEquals(12, cell.value);
                    events.add("Enter");
                }

                @Override
                public void leaveCriticalSection(long criticalSectionPtr) {
                    assertEquals(0x105c5d330L, criticalSectionPtr);
                    events.add("Leave");
                }
            };
            RequestStaticDispatch4267630.TailTarget target = (targetRax, knownRcx) -> {
                events.add("Target");
                assertEquals(Long.MIN_VALUE, targetRax);
                assertEquals(outerSize, knownRcx);
                transfers++;
                assertEquals(1, transfers);
                heap = HEAP_B;
                return targetEax;
            };
            return RequestGateStaticDispatchConsumer.ports(BASE, this, api, target);
        }
    }

    @Test
    public void outerRetryKeepsOriginalZeroSizeWhileInnerNormalizes() {
        Fixture fixture = new Fixture();
        RequestRetry4223b94.Ports ports = RequestRetryAllocationConsumer.ports(
                BASE, fixture, fixture, fixture.gate(-7, 0L));
        assertEquals(RESULT, RequestRetry4223b94.execute(0L, ports));
        assertEquals(2, fixture.attempts);
        assertEquals(1, fixture.queries);
        assertEquals(1, fixture.cells);
        assertEquals(1, fixture.transfers);
        assertEquals(12, fixture.cell.value);
        assertEquals(List.of(HEAP_A, HEAP_B), fixture.handles);
        assertEquals(List.of(1L, 1L), fixture.sizes);
        assertEquals(List.of("HeapHandle", "HeapAlloc", "Query", "Cell", "Enter", "Encoded", "Key", "Leave", "Target", "HeapHandle", "HeapAlloc"), fixture.events);
    }

    @Test
    public void outerRejectedSizeKeepsTypedCellAndSourceErrorBoundary() {
        Fixture fixture = new Fixture();
        fixture.rejectSize = true;
        RequestRetry4223b94.Ports ports = RequestRetryAllocationConsumer.ports(
                BASE, fixture, fixture, fixture.gate(0, -1L));
        RequestRetry4223b94.UnexecutedSourcePath boundary = assertThrows(
                RequestRetry4223b94.UnexecutedSourcePath.class,
                () -> RequestRetry4223b94.execute(-1L, ports));
        assertEquals(0x4224a58L, boundary.targetRva());
        assertEquals(0x4223bcfL, boundary.trapSiteRva());
        assertEquals(-1L, boundary.capturedSizeBits());
        assertEquals(0, fixture.attempts);
        assertEquals(0, fixture.queries);
        assertEquals(1, fixture.cells);
        assertEquals(1, fixture.transfers);
        assertEquals(12, fixture.cell.value);
        assertEquals(List.of("Cell", "Enter", "Encoded", "Key", "Leave", "Target"), fixture.events);
    }
}
