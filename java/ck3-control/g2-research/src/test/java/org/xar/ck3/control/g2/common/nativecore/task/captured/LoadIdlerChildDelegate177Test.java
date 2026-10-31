package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Invocation;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Ports;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Queue;
import java.util.ArrayDeque;

public class LoadIdlerChildDelegate177Test {

    @Test
    void testNullChild() {
        long self = 0x100000000L;
        long addr = self + 0x10L;
        long val = 0L;

        Queue<Object> expected = new ArrayDeque<>();
        expected.add(addr);

        LoadIdlerChildDelegate177.Memory mem = (long a) -> {
            assertEquals(expected.poll(), a);
            return val;
        };

        Ports ports = (Invocation inv) -> {
            fail("Unexpected invoke");
        };

        LoadIdlerChildDelegate177.forward383e4c0(self, mem, ports);
        assertTrue(expected.isEmpty());
    }

    @Test
    void testNonnullChild() {
        long self = 0x100000000L;
        long addr = self + 0x10L;
        long child = 0x200000000L;
        long vptr = 0x300000000L;
        long target = 0x400000000L;

        Queue<Object> expected = new ArrayDeque<>();
        expected.add(addr);
        expected.add(child);
        expected.add(vptr + 0x38L);
        expected.add(new Invocation(0x383e4ccL, target, child, OptionalLong.empty(), true));

        LoadIdlerChildDelegate177.Memory mem = (long a) -> {
            Object exp = expected.poll();
            assertEquals(exp, a);
            if (a == addr) return child;
            if (a == child) return vptr;
            if (a == vptr + 0x38L) return target;
            fail("Unexpected read");
            return 0L;
        };

        Ports ports = (Invocation inv) -> {
            Object exp = expected.poll();
            assertEquals(exp, inv);
        };

        LoadIdlerChildDelegate177.forward383e4c0(self, mem, ports);
        assertTrue(expected.isEmpty());
    }
}