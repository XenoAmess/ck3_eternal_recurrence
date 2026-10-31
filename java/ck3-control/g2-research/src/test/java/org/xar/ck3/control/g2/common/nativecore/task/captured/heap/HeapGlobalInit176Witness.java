package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs.HeapCell64;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;

/** Owner-written JDK-only host. Expectations are literals from the held normal body. */
public final class HeapGlobalInit176Witness {
    private static final long BASE = 0x140000000L;
    private static final long SLOT = BASE + 0x5c5de30L;
    private static int checks;

    private HeapGlobalInit176Witness() { }

    public static void main(String[] args) {
        require(args.length == 0, "no arguments");
        direct("heap176-0000", 0L, 0L);
        direct("heap176-0001", 0x123456789abcdef0L, 0x123456789abcde01L);
        direct("heap176-0002", 0x8000000000000000L, 0x8000000000000001L);
        direct("heap176-0003", -1L, 0xffffffffffffff01L);
        allocatorRetry();
        allocatorOverflow();
        System.out.println("{\"summary\":\"heap176-java\",\"direct_cases\":4,"
                + "\"owned_m4_cases\":2,\"checks\":" + checks + ",\"Game\":0}");
    }

    private static void direct(String id, long handle, long expectedRax) {
        List<String> actual = new ArrayList<>();
        long[] heapAndNeighbor = {0x1122334455667788L, 0x99aabbccddeeff00L};
        int[] calls = {0, 0};
        NativeTaskMemory memory = new NativeTaskMemory() {
            @Override public long readPointer(long address) {
                require(address == SLOT, "direct pointer address");
                return heapAndNeighbor[0];
            }
            @Override public void writeInt64(long address, long value) {
                require(address == SLOT, "direct QWORD write address");
                require(++calls[1] == 1, "one QWORD write");
                actual.add("W:" + hex(value));
                heapAndNeighbor[0] = value;
            }
            @Override public int readInt32(long address) {
                throw new IllegalStateException("unexpected DWORD read " + hex(address));
            }
            @Override public void writeInt32(long address, int value) {
                throw new IllegalStateException("unexpected DWORD write " + hex(address));
            }
        };
        long returned = HeapGlobalInit176Candidate.init(BASE, memory, () -> {
            require(++calls[0] == 1, "one GetProcessHeap callback");
            actual.add("H:" + hex(handle));
            return handle;
        });
        require(returned == expectedRax, id + " full RAX");
        require(heapAndNeighbor[0] == handle, id + " raw stored QWORD");
        require(heapAndNeighbor[1] == 0x99aabbccddeeff00L, id + " neighbor unchanged");
        require(calls[0] == 1 && calls[1] == 1, id + " exact counts");
        require(actual.equals(List.of("H:" + hex(handle), "W:" + hex(handle))), id + " call order");
        System.out.println("{\"case_id\":\"" + id + "\",\"handle_hex64\":\"" + hex(handle)
                + "\",\"returned_rax_hex64\":\"" + hex(returned)
                + "\",\"stored_heap_hex64\":\"" + hex(heapAndNeighbor[0])
                + "\",\"callback_calls\":" + calls[0] + ",\"write_calls\":" + calls[1] + "}");
    }

    private static void allocatorRetry() {
        HeapCell64 heap = new HeapCell64(0x5555555555555555L);
        Cell32 selected = new Cell32(73);
        Cell32 neighbor = new Cell32(91);
        List<String> events = new ArrayList<>();
        int[] counts = new int[5];
        Allocator117Inputs.Calls allocation = new Allocator117Inputs.Calls() {
            @Override public long allocateImported(long handle, int flags, long bytes) {
                int ordinal = counts[1]++;
                require(ordinal < 2, "M4 allocation script exhausted");
                require(flags == 8 && bytes == 24L, "M4 exact flags and count product");
                long expectedHandle = ordinal == 0 ? 0x123456789abcdef0L : 0x8000000000000000L;
                require(handle == expectedHandle, "M4 reads same mutable heap per attempt");
                events.add("A:" + hex(handle) + ":8:24");
                heap.value = 0x8000000000000000L;
                return ordinal == 0 ? 0L : 0x7000L;
            }
            @Override public int retryGate() {
                require(++counts[2] == 1, "M4 gate script exhausted");
                events.add("G:1");
                return 1;
            }
            @Override public int retryCall(long bytes) {
                require(++counts[3] == 1 && bytes == 24L, "M4 retry exact argument/count");
                events.add("T:24:1");
                return 1;
            }
            @Override public Cell32 failureCell() {
                counts[4]++;
                throw new IllegalStateException("unexpected M4 failure-cell callback");
            }
        };
        HeapGlobalInitAllocator117Consumer.Outcome out = HeapGlobalInitAllocator117Consumer.run(
                BASE, 3L, 8L, heap, () -> {
                    require(++counts[0] == 1, "M4 init callback once");
                    events.add("H:123456789abcdef0");
                    return 0x123456789abcdef0L;
                }, allocation);
        require(out.initializationRaxBits() == 0x123456789abcde01L, "M4 initializer raw RAX");
        require(out.allocationRaxBits() == 0x7000L, "M4 allocation raw RAX");
        require(heap.value == 0x8000000000000000L, "M4 mutated heap remains actual");
        require(selected.value == 73 && neighbor.value == 91, "M4 success no failure-cell writes");
        require(counts[0] == 1 && counts[1] == 2 && counts[2] == 1 && counts[3] == 1 && counts[4] == 0,
                "M4 complete script consumption");
        require(events.equals(List.of("H:123456789abcdef0", "A:123456789abcdef0:8:24",
                "G:1", "T:24:1", "A:8000000000000000:8:24")), "M4 retry full order");
        printOwned("heap176-m4-retry", out, heap, selected, neighbor, events.size());
    }

    private static void allocatorOverflow() {
        HeapCell64 heap = new HeapCell64(0x2222222222222222L);
        Cell32 selected = new Cell32(73);
        Cell32 neighbor = new Cell32(91);
        List<String> events = new ArrayList<>();
        int[] counts = new int[2];
        Allocator117Inputs.Calls allocation = new Allocator117Inputs.Calls() {
            @Override public long allocateImported(long handle, int flags, long bytes) {
                throw new IllegalStateException("overflow must precede allocation");
            }
            @Override public int retryGate() { throw new IllegalStateException("overflow gate"); }
            @Override public int retryCall(long bytes) { throw new IllegalStateException("overflow retry"); }
            @Override public Cell32 failureCell() {
                require(++counts[1] == 1, "one M4 overflow failure cell");
                events.add("C");
                return selected;
            }
        };
        HeapGlobalInitAllocator117Consumer.Outcome out = HeapGlobalInitAllocator117Consumer.run(
                BASE, -1L, 2L, heap, () -> {
                    require(++counts[0] == 1, "M4 overflow init callback once");
                    events.add("H:ffffffffffffffff");
                    return -1L;
                }, allocation);
        require(out.initializationRaxBits() == 0xffffffffffffff01L, "M4 overflow initializer raw RAX");
        require(out.allocationRaxBits() == 0L, "M4 unsigned DIV overflow return");
        require(heap.value == -1L, "M4 init stores complete raw handle before overflow");
        require(selected.value == 12 && neighbor.value == 91, "M4 selected DWORD only");
        require(counts[0] == 1 && counts[1] == 1, "M4 overflow complete callback counts");
        require(events.equals(List.of("H:ffffffffffffffff", "C")), "M4 overflow full order");
        printOwned("heap176-m4-overflow", out, heap, selected, neighbor, events.size());
    }

    private static void printOwned(String id, HeapGlobalInitAllocator117Consumer.Outcome out,
            HeapCell64 heap, Cell32 selected, Cell32 neighbor, int eventCount) {
        System.out.println("{\"case_id\":\"" + id + "\",\"scope\":\"owned_software_sequence\","
                + "\"initialization_rax_hex64\":\"" + hex(out.initializationRaxBits())
                + "\",\"allocation_rax_hex64\":\"" + hex(out.allocationRaxBits())
                + "\",\"final_heap_hex64\":\"" + hex(heap.value) + "\",\"selected_cell\":"
                + selected.value + ",\"neighbor_cell\":" + neighbor.value + ",\"event_count\":" + eventCount + "}");
    }

    private static String hex(long bits) { return String.format(Locale.ROOT, "%016x", bits); }
    private static void require(boolean condition, String message) {
        checks++;
        if (!condition) { throw new IllegalStateException(message); }
    }
}
