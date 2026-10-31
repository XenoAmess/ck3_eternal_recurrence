package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.ArrayList;
public final class StaticObjectB15000Test {
    @Test
    public void signedGuardFreshHeaderAndInitializedFooterPaths() {
        Sparse177TestMemory memory = new Sparse177TestMemory();
        Idler79eRegressionHost.Memory bytes = memory.bytes();
        long moduleBase = 0x140000000L;
        long object = moduleBase + 0x5D1EAF0L;
        long guard = object + 0x18;
        long vector = bytes.allocate(8);
        long tls = bytes.allocate(20);
        bytes.map(object, 28);
        for (int offset = 0; offset < 28; offset++) bytes.seedByte(object + offset, 0xAA);
        bytes.seedInt64(vector, tls);
        bytes.seedInt32(tls + 0x10, 2);
        bytes.seedInt32(guard, -7);
        int[] mode = {0};
        int[] gsCalls = {0};
        int[] headerCalls = {0};
        int[] footerCalls = {0};
        List<String> order = new ArrayList<>();
        RuntimeException footerFailure = new RuntimeException("controlled-footer");
        StaticObjectB15000.Ports ports = new StaticObjectB15000.Ports() {
            @Override
            public long readGs58() {
                gsCalls[0]++;
                order.add("gs");
                return vector;
            }
            @Override
            public void call4223a84(long rcx) {
                assertEquals(guard, rcx);
                assertTrue(mode[0] == 1 || mode[0] == 2);
                headerCalls[0]++;
                order.add("header");
                assertEquals(mode[0] == 1 ? 200 : 300, bytes.peekInt32(guard));
                bytes.seedInt32(guard, mode[0] == 1 ? 201 : -1);
            }
            @Override
            public void call4223a24(long rcx) {
                assertEquals(guard, rcx);
                assertEquals(2, mode[0]);
                footerCalls[0]++;
                order.add("footer");
                assertEquals(-1, bytes.peekInt32(guard));
                assertEquals(0, bytes.peekUnsignedByte(object));
                assertEquals(0xFF, bytes.peekUnsignedByte(object + 12));
                assertEquals(List.of(
                        new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, vector, 8, tls),
                        new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, tls + 0x10, 4, 200),
                        new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, 300),
                        new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, -1),
                        new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, object, 1, 0),
                        new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, object + 12, 1, 0xFF)
                ), bytes.trace());
                for (int offset = 0; offset < 28; offset++) {
                    int expected = offset >= 24 ? 0xFF : offset == 0 ? 0 : offset == 12 ? 0xFF : 0xAA;
                    assertEquals(expected, bytes.peekUnsignedByte(object + offset), "footer byte " + offset);
                }
                throw footerFailure;
            }
        };

        bytes.clearTrace();
        assertEquals(object, StaticObjectB15000.get(moduleBase, memory, ports));
        assertEquals(1, gsCalls[0]);
        assertEquals(0, headerCalls[0]);
        assertEquals(0, footerCalls[0]);
        assertEquals(List.of("gs"), order);
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, vector, 8, tls),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, tls + 0x10, 4, 2),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, -7)
        ), bytes.trace());
        for (int offset = 0; offset < 28; offset++) {
            int expected = offset >= 24 ? (-7 >>> ((offset - 24) * 8)) & 0xFF : 0xAA;
            assertEquals(expected, bytes.peekUnsignedByte(object + offset), "fast byte " + offset);
        }

        mode[0] = 1;
        bytes.seedInt32(tls + 0x10, 100);
        bytes.seedInt32(guard, 200);
        bytes.clearTrace();
        assertEquals(object, StaticObjectB15000.get(moduleBase, memory, ports));
        assertEquals(2, gsCalls[0]);
        assertEquals(1, headerCalls[0]);
        assertEquals(0, footerCalls[0]);
        assertEquals(List.of("gs", "gs", "header"), order);
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, vector, 8, tls),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, tls + 0x10, 4, 100),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, 200),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, 201)
        ), bytes.trace());
        for (int offset = 0; offset < 28; offset++) {
            int expected = offset >= 24 ? (201 >>> ((offset - 24) * 8)) & 0xFF : 0xAA;
            assertEquals(expected, bytes.peekUnsignedByte(object + offset), "slow byte " + offset);
        }

        mode[0] = 2;
        bytes.seedInt32(tls + 0x10, 200);
        bytes.seedInt32(guard, 300);
        bytes.clearTrace();
        assertSame(footerFailure, assertThrows(RuntimeException.class,
                () -> StaticObjectB15000.get(moduleBase, memory, ports)));
        assertEquals(3, gsCalls[0]);
        assertEquals(2, headerCalls[0]);
        assertEquals(1, footerCalls[0]);
        assertEquals(List.of("gs", "gs", "header", "gs", "header", "footer"), order);
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, vector, 8, tls),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, tls + 0x10, 4, 200),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, 300),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, -1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, object, 1, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, object + 12, 1, 0xFF)
        ), bytes.trace());
        for (int offset = 0; offset < 28; offset++) {
            int expected = offset >= 24 ? 0xFF : offset == 0 ? 0 : offset == 12 ? 0xFF : 0xAA;
            assertEquals(expected, bytes.peekUnsignedByte(object + offset), "initialized byte " + offset);
        }
        assertTrue(memory.effects().isEmpty());
    }
}
