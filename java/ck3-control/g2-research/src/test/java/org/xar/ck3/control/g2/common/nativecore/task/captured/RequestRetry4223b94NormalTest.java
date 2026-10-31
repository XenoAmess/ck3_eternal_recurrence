package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;

public final class RequestRetry4223b94NormalTest {

    @Test
    public void immediateAllocatorResultPreservesAllBits() {
        long size = Long.MIN_VALUE + 39L;
        long expectedReturn = -123456789012345678L;
        List<String> sequence = new ArrayList<>();
        List<Long> allocatorArgs = new ArrayList<>();
        List<Long> handlerArgs = new ArrayList<>();

        RequestRetry4223b94.Ports ports = new RequestRetry4223b94.Ports() {
            @Override
            public long call42420b8(long rcx) {
                sequence.add("allocator");
                allocatorArgs.add(rcx);
                return expectedReturn;
            }
            @Override
            public int call424cffc(long rcx) {
                sequence.add("handler");
                handlerArgs.add(rcx);
                throw new AssertionError("Unexpected handler call in immediate return path");
            }
        };

        long result = RequestRetry4223b94.execute(size, ports);

        assertEquals(List.of("allocator"), sequence);
        assertEquals(1, allocatorArgs.size());
        assertEquals(0, handlerArgs.size());
        assertEquals(size, allocatorArgs.get(0));
        assertEquals(expectedReturn, result);
    }

    @Test
    public void blockConsumerRetriesAfterNegativeNonzeroHandler() {
        long size = 1L;
        long h = 0x1234L;
        List<String> sequence = new ArrayList<>();
        List<Long> allocatorArgs = new ArrayList<>();
        List<Long> handlerArgs = new ArrayList<>();
        int[] callCount = new int[]{0};

        RequestRetry4223b94.Ports script = new RequestRetry4223b94.Ports() {
            @Override
            public long call42420b8(long rcx) {
                sequence.add("allocator");
                allocatorArgs.add(rcx);
                callCount[0]++;
                if (callCount[0] == 1) {
                    return 0L;
                } else {
                    return h;
                }
            }
            @Override
            public int call424cffc(long rcx) {
                sequence.add("handler");
                handlerArgs.add(rcx);
                callCount[0]++;
                return -1;
            }
        };

        RequestBlock856db0.Ports blockPorts = RequestBlockRetryConsumer.ports(script);
        Request140TestMemory memory = new Request140TestMemory();

        long result = RequestBlock856db0.execute(size, memory, blockPorts);

        assertEquals(List.of("allocator", "handler", "allocator"), sequence);
        assertEquals(3, callCount[0]);
        assertEquals(2, allocatorArgs.size());
        assertEquals(1, handlerArgs.size());
        assertEquals(size, allocatorArgs.get(0));
        assertEquals(size, allocatorArgs.get(1));
        assertEquals(size, handlerArgs.get(0));
        assertEquals(h, result);
        assertTrue(memory.trace().isEmpty());
    }
}
