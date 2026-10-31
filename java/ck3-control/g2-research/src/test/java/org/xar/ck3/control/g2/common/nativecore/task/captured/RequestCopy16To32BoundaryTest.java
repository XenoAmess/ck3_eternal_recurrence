package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Supplied-storage oracle for only the held unsigned16..32 branch. */
public final class RequestCopy16To32BoundaryTest {
    private static final long HEAD_LOW = 0x1716151413121110L;
    private static final long HEAD_HIGH = 0x1f1e1d1c1b1a1918L;

    private record Fixture(long lengthBits, int destinationOffset,
            int tailReadOffset, int tailWriteOffset, long tailLow, long tailHigh,
            boolean throughWrapper, String expectedImage) { }

    @Test
    public void testBoundaryAndUnsupported() {
        for (long lengthBits : new long[] {0L, 15L, 33L, Long.MIN_VALUE}) {
            Request140TestMemory memory = new Request140TestMemory();
            long destination = 0x1000L;
            long source = 0x2000L;
            assertFalse(RequestCopy16To32.tryCopy(destination, source, lengthBits, memory));
            assertEquals(List.of(), memory.trace());

            final int[] calls = {0};
            final long[] arguments = new long[3];
            RequestCopy16To32.copyOrDelegate(destination, source, lengthBits, memory,
                    (d, s, n) -> {
                        calls[0]++;
                        arguments[0] = d;
                        arguments[1] = s;
                        arguments[2] = n;
                    });
            assertEquals(1, calls[0]);
            assertArrayEquals(new long[] {destination, source, lengthBits}, arguments);
            assertEquals(List.of(), memory.trace());
        }

        // Explicit positions/raw snapshots and complete final images are literal
        // source oracles. No expected image is computed by performing a copy.
        List<Fixture> fixtures = List.of(
            new Fixture(16L, 16, 16, 16, HEAD_LOW, HEAD_HIGH, false,
                "000102030405060708090a0b0c0d0e0f"
              + "101112131415161718191a1b1c1d1e1f"
              + "202122232425262728292a2b2c2d2e2f"
              + "303132333435363738393a3b3c3d3e3f"),
            new Fixture(17L, 17, 17, 18,
                0x1817161514131211L, 0x201f1e1d1c1b1a19L, false,
                "000102030405060708090a0b0c0d0e0f"
              + "10101112131415161718191a1b1c1d1e"
              + "1f2022232425262728292a2b2c2d2e2f"
              + "303132333435363738393a3b3c3d3e3f"),
            new Fixture(32L, 15, 32, 31,
                0x2726252423222120L, 0x2f2e2d2c2b2a2928L, true,
                "000102030405060708090a0b0c0d0e10"
              + "1112131415161718191a1b1c1d1e1f20"
              + "2122232425262728292a2b2c2d2e2f2f"
              + "303132333435363738393a3b3c3d3e3f")
        );

        for (Fixture fixture : fixtures) {
            Request140TestMemory memory = new Request140TestMemory();
            Idler79eRegressionHost.Memory backing = memory.bytes();
            long base = backing.allocate(64);
            for (int i = 0; i < 64; i++) {
                backing.seedByte(base + i, i);
            }
            long destination = base + fixture.destinationOffset();
            long source = base + 16;
            if (fixture.throughWrapper()) {
                RequestCopy16To32.copyOrDelegate(destination, source,
                        fixture.lengthBits(), memory, (d, s, n) -> {
                            throw new AssertionError("selected branch reached remainder");
                        });
            } else {
                assertTrue(RequestCopy16To32.tryCopy(destination, source,
                        fixture.lengthBits(), memory));
            }

            assertEquals(List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.READ128,
                    base + 16, 16, HEAD_LOW, HEAD_HIGH),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ128,
                    base + fixture.tailReadOffset(), 16, fixture.tailLow(), fixture.tailHigh()),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128,
                    base + fixture.destinationOffset(), 16, HEAD_LOW, HEAD_HIGH),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128,
                    base + fixture.tailWriteOffset(), 16, fixture.tailLow(), fixture.tailHigh())
            ), memory.trace(), "literal4Access n=" + fixture.lengthBits());

            byte[] expected = HexFormat.of().parseHex(fixture.expectedImage());
            assertEquals(64, expected.length);
            byte[] actual = new byte[64];
            for (int i = 0; i < 64; i++) {
                actual[i] = (byte) backing.peekUnsignedByte(base + i);
            }
            assertArrayEquals(expected, actual, "complete64B image n=" + fixture.lengthBits());
        }
    }
}
