package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestAllocate424fda0;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;

/** Owner host; finite literals reviewed independently against the held 28B and 94B. */
public final class HeapGlobalInitRequestAllocate176Witness {
    private static final long BASE = 0x140000000L;
    private static final long SLOT = BASE + 0x5c5de30L;
    private static int checks;

    private HeapGlobalInitRequestAllocate176Witness() { }

    public static void main(String[] args) {
        require(args.length == 0, "no arguments");
        scenario("heap176-m7-0000", 0L, new long[] {1L}, new long[] {0L}, new int[0], new int[0],
                1L, 0L, 0, List.of("H:0000000000000000", "W:0000000000000000",
                        "R:0000000000000000", "A:0000000000000000:00000000:0000000000000001:0000000000000001:0000000000000000"));
        scenario("heap176-m7-0001", 16L, new long[] {0L, 2L}, new long[] {1L, 1L}, new int[] {1}, new int[] {1},
                2L, 1L, 0, List.of("H:0000000000000000", "W:0000000000000000",
                        "R:0000000000000000", "A:0000000000000000:00000000:0000000000000010:0000000000000000:0000000000000001",
                        "G:00000001", "T:0000000000000010:00000001", "R:0000000000000001",
                        "A:0000000000000001:00000000:0000000000000010:0000000000000002:0000000000000001"));
        scenario("heap176-m7-0002", 16L, new long[] {0L}, new long[] {0L}, new int[] {0}, new int[0],
                0L, 0L, 12, List.of("H:0000000000000000", "W:0000000000000000",
                        "R:0000000000000000", "A:0000000000000000:00000000:0000000000000010:0000000000000000:0000000000000000",
                        "G:00000000", "C"));
        System.out.println("{\"summary\":\"heap176-m7-java\",\"owned_cases\":3,\"checks\":" + checks + ",\"Game\":0}");
    }

    private static void scenario(String id, long size, long[] results, long[] heapsAfter,
            int[] gates, int[] retries, long expectedAllocation, long expectedFinalHeap,
            int expectedCell, List<String> expectedEvents) {
        List<String> events = new ArrayList<>();
        long[] heapAndNeighbor = {0L, 0xfedcba9876543210L};
        int[] counts = new int[7]; // init, write, read, allocate, gate, retry, failure-cell
        Cell32 selected = new Cell32(0);
        Cell32 neighbor = new Cell32(97);
        NativeTaskMemory memory = new NativeTaskMemory() {
            @Override public long readPointer(long address) {
                require(address == SLOT, id + " exact QWORD read address");
                counts[2]++;
                events.add("R:" + hex(heapAndNeighbor[0]));
                return heapAndNeighbor[0];
            }
            @Override public void writeInt64(long address, long value) {
                require(address == SLOT, id + " exact QWORD write address");
                require(++counts[1] == 1, id + " one initializer write");
                events.add("W:" + hex(value));
                heapAndNeighbor[0] = value;
            }
            @Override public int readInt32(long address) {
                throw new IllegalStateException("unexpected DWORD read " + hex(address));
            }
            @Override public void writeInt32(long address, int value) {
                throw new IllegalStateException("unexpected DWORD write " + hex(address));
            }
        };
        RequestAllocate424fda0.Ports allocation = new RequestAllocate424fda0.Ports() {
            @Override public long heapAlloc(long handle, int flags, long bytes) {
                int index = counts[3]++;
                require(index < results.length, id + " allocation script exhausted");
                require(handle == heapAndNeighbor[0], id + " actual current heap forwarded");
                require(flags == 0, id + " zero HeapAlloc flags");
                require(bytes == (size == 0L ? 1L : size), id + " exact byte count/minimum1");
                long returned = results[index];
                heapAndNeighbor[0] = heapsAfter[index];
                events.add("A:" + hex(handle) + ":" + hex32(flags) + ":" + hex(bytes)
                        + ":" + hex(returned) + ":" + hex(heapAndNeighbor[0]));
                return returned;
            }
            @Override public int call424e250() {
                int index = counts[4]++;
                require(index < gates.length, id + " gate script exhausted");
                events.add("G:" + hex32(gates[index]));
                return gates[index];
            }
            @Override public int call424cffc(long bytes) {
                int index = counts[5]++;
                require(index < retries.length, id + " retry script exhausted");
                require(bytes == (size == 0L ? 1L : size), id + " retry RCX");
                events.add("T:" + hex(bytes) + ":" + hex32(retries[index]));
                return retries[index];
            }
            @Override public Cell32 call423b18c() {
                require(++counts[6] == 1, id + " one selected failure cell");
                events.add("C");
                return selected;
            }
        };
        HeapGlobalInitRequestAllocate176Consumer.Outcome out = HeapGlobalInitRequestAllocate176Consumer.run(
                BASE, size, memory, () -> {
                    require(++counts[0] == 1, id + " init callback once");
                    events.add("H:0000000000000000");
                    return 0L;
                }, allocation);
        require(out.initializationRaxBits() == 0L, id + " actual zero initializer RAX");
        require(out.allocationRaxBits() == expectedAllocation, id + " actual allocator result");
        require(heapAndNeighbor[0] == expectedFinalHeap, id + " final heap mutation");
        require(heapAndNeighbor[1] == 0xfedcba9876543210L, id + " adjacent QWORD unchanged");
        require(selected.value == expectedCell && neighbor.value == 97, id + " selected DWORD and neighbor");
        require(counts[0] == 1 && counts[1] == 1 && counts[2] == results.length, id + " exact init/read/write counts");
        require(counts[3] == results.length && counts[4] == gates.length && counts[5] == retries.length,
                id + " complete allocation/gate/retry scripts");
        require(counts[6] == (expectedCell == 12 ? 1 : 0), id + " exact failure-cell count");
        require(events.equals(expectedEvents), id + " full actual event order");
        System.out.println("{\"case_id\":\"" + id + "\",\"scope\":\"owned_software_sequence\","
                + "\"initialization_rax_hex64\":\"" + hex(out.initializationRaxBits())
                + "\",\"allocation_rax_hex64\":\"" + hex(out.allocationRaxBits())
                + "\",\"final_heap_hex64\":\"" + hex(heapAndNeighbor[0]) + "\",\"selected_cell\":"
                + selected.value + ",\"neighbor_cell\":" + neighbor.value + ",\"read_calls\":" + counts[2]
                + ",\"write_calls\":" + counts[1] + ",\"allocation_calls\":" + counts[3]
                + ",\"gate_calls\":" + counts[4] + ",\"retry_calls\":" + counts[5]
                + ",\"failure_cell_calls\":" + counts[6] + ",\"event_count\":" + events.size() + "}");
    }

    private static String hex(long bits) { return String.format(Locale.ROOT, "%016x", bits); }
    private static String hex32(int bits) { return String.format(Locale.ROOT, "%08x", bits); }
    private static void require(boolean condition, String message) {
        checks++;
        if (!condition) { throw new IllegalStateException(message); }
    }
}
