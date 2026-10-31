package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRuntime4260e74.SearchCall;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadHierarchySearch173;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRuntime4260e74;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadSearch4260af0;
import java.util.OptionalLong;
import java.util.Queue;
import java.util.ArrayDeque;
import static org.junit.jupiter.api.Assertions.*;

public class LoadHierarchy173Test {

    private static final long BASE = 0x100000000L;
    private static final long COL = 0x7000L;
    private static final long COMPLETE = 0x8000L;
    private static final long SOURCE = 0x9000L;
    private static final long OFFSET = -7L;
    private static final long LIVE_RAX = 0x1234L;

    private static final SearchCall call = new SearchCall(
            COMPLETE, COL, SOURCE, OFFSET, LIVE_RAX,
            OptionalLong.of(0xA000L), OptionalLong.of(BASE)
    );

    private static final Queue<Long> readQueue = new ArrayDeque<>();
    private static final Queue<Integer> valueQueue = new ArrayDeque<>();

    private static void enqueueRead(long address, int value) {
        readQueue.add(address);
        valueQueue.add(value);
    }

    private static void resetQueues() {
        readQueue.clear();
        valueQueue.clear();
    }

    private static class TestMemory implements LoadHierarchySearch173.Memory {
        @Override
        public long readPointer(long address) {
            throw new AssertionError("Unexpected pointer read");
        }

        @Override
        public int readInt32(long address) {
            if (readQueue.isEmpty() || valueQueue.isEmpty()) {
                throw new AssertionError("Unexpected readInt32");
            }
            long expectedAddr = readQueue.poll();
            int expectedVal = valueQueue.poll();
            assertEquals(expectedAddr, address, "Address mismatch");
            return expectedVal;
        }

        @Override
        public void writeInt32(long address, int value) {
            throw new AssertionError("Unexpected writeInt32");
        }

        @Override
        public void writeInt64(long address, long value) {
            throw new AssertionError("Unexpected writeInt64");
        }

        @Override
        public int readUnsigned8(long address) {
            throw new AssertionError("Unexpected readUnsigned8");
        }
    }

    @Test
    public void testFind968Count0() {
        resetQueues();
        enqueueRead(COL + 0x10L, 0x100);
        enqueueRead(BASE + 0x10C, 0x200);
        enqueueRead(BASE + 0x108, 0);

        TestMemory memory = new TestMemory();
        long result = LoadHierarchySearch173.find968(call, memory);
        assertEquals(0L, result);
        assertTrue(readQueue.isEmpty());
        assertTrue(valueQueue.isEmpty());
    }

    @Test
    public void testFindC28Count0() {
        resetQueues();
        enqueueRead(COL + 0x10L, 0x100);
        enqueueRead(BASE + 0x10C, 0x200);
        enqueueRead(BASE + 0x108, 0);

        TestMemory memory = new TestMemory();
        long result = LoadHierarchySearch173.findC28(call, memory);
        assertEquals(0L, result);
        assertTrue(readQueue.isEmpty());
        assertTrue(valueQueue.isEmpty());
    }
}