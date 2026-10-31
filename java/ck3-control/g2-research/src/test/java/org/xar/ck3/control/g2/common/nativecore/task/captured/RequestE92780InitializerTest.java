package org.xar.ck3.control.g2.common.nativecore.task.captured;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;

public final class RequestE92780InitializerTest {
    private static List<Request140TestMemory.Access> defaults(long base, long u) {
        return List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE16, u + 0x08L, 2, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0x0AL, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, u + 0x0CL, 4, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x10L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x18L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0x20L, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x28L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x38L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x40L, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x48L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x58L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x60L, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE16, u + 0x68L, 2, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0x6AL, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u, 8, base + 0x44FC2A8L, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x70L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x80L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x88L, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0x70L, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, u + 0x90L, 4, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, u + 0x94L, 4, 0x029C77F8L, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, u + 0x98L, 8, -1L, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0xA0L, 1, 3, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, u + 0xA4L, 4, 0xFFFFFFFFL, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE16, u + 0xA8L, 2, 0x0100, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0xD8L, 1, 0, 0)
        );
    }

    private static int[] defaultImage(long base, long u) {
        final int[] image = new int[224];
        Arrays.fill(image, 0xA5);
        for (Request140TestMemory.Access effect : defaults(base, u)) {
            final int offset = (int) (effect.address() - u);
            for (int i = 0; i < effect.width(); i++) {
                image[offset + i] = (int) (effect.low() >>> (8 * i)) & 0xFF;
            }
        }
        return image;
    }

    private static void assertImage(Idler79eRegressionHost.Memory bytes, long address, int[] expected) {
        for (int i = 0; i < expected.length; i++) {
            assertEquals(expected[i], bytes.peekUnsignedByte(address + i), "byte at offset " + i);
        }
    }

    @Test
    public void absentDescriptorPreservesPoisonHolesAndPublishesHolderAfterExactDefaults() {
        final Request140TestMemory memory = new Request140TestMemory();
        final Idler79eRegressionHost.Memory bytes = memory.bytes();
        final long base = 0x0000000110000000L;
        final long u = bytes.allocate(224);
        final long holder = bytes.allocate(8);
        final long descriptor = bytes.allocate(41);
        final long scratch = bytes.allocate(41);
        for (int i = 0; i < 224; i++) bytes.seedByte(u + i, 0xA5);
        for (int i = 0; i < 41; i++) {
            bytes.seedByte(descriptor + i, 0xB6);
            bytes.seedByte(scratch + i, 0xC7);
        }
        bytes.seedByte(descriptor + 0x28L, 0);
        bytes.seedInt64(holder, 0x123456789ABCDEF0L);
        final List<String> calls = new ArrayList<>();
        final RequestE92780.Ports ports = new RequestE92780.Ports() {
            @Override public long call4223b94(int ecx) {
                assertEquals(224, ecx);
                assertEquals(List.of(), memory.trace());
                calls.add("allocate");
                return u;
            }
            @Override public void call855f00(long rcx, long rdx) {
                throw new AssertionError("Absent descriptor must not transfer a string");
            }
            @Override public void call856050(long rcx) {
                throw new AssertionError("Absent descriptor must not clean scratch");
            }
        };

        final long returned = RequestE92780.initialize(base, holder, descriptor, scratch, memory, ports);
        final List<Request140TestMemory.Access> actual = memory.trace();

        final List<Request140TestMemory.Access> expected = new ArrayList<>();
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, scratch + 0x28L, 1, 0, 0));
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.READ8, descriptor + 0x28L, 1, 0, 0));
        final List<Request140TestMemory.Access> defaultEffects = defaults(base, u);
        assertEquals(26, defaultEffects.size());
        expected.addAll(defaultEffects);
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.READ8, scratch + 0x28L, 1, 0, 0));
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, holder, 8, u, 0));
        assertEquals(expected, actual);
        assertEquals(List.of("allocate"), calls);
        assertEquals(holder, returned);
        assertEquals(u, bytes.peekInt64(holder));
        assertImage(bytes, u, defaultImage(base, u));
        final int[] expectedDescriptor = new int[41];
        final int[] expectedScratch = new int[41];
        Arrays.fill(expectedDescriptor, 0xB6);
        Arrays.fill(expectedScratch, 0xC7);
        expectedDescriptor[40] = 0;
        expectedScratch[40] = 0;
        assertImage(bytes, descriptor, expectedDescriptor);
        assertImage(bytes, scratch, expectedScratch);
    }

    @Test
    public void nonOneFlagCopiesRawBitsAndFreshScratchThenPropagatesCleanupException() {
        final Request140TestMemory memory = new Request140TestMemory();
        final Idler79eRegressionHost.Memory bytes = memory.bytes();
        final long base = 0x0000000220000000L;
        final long u = bytes.allocate(224);
        final long holder = bytes.allocate(8);
        final long descriptor = bytes.allocate(41);
        final long scratch = bytes.allocate(41);
        final long holderPoison = 0x5566778899AABBCCL;
        final long[] captured = {
                0xFEDCBA9876543210L, 0x0123456789ABCDEFL,
                0x8877665544332211L, 0x1020304050607080L
        };
        final int changedScalar = 0xE2468ACE;
        for (int i = 0; i < 224; i++) bytes.seedByte(u + i, 0xA5);
        for (int i = 0; i < 41; i++) {
            bytes.seedByte(descriptor + i, 0xB6);
            bytes.seedByte(scratch + i, 0xC7);
        }
        for (int i = 0; i < captured.length; i++) bytes.seedInt64(descriptor + 8L * i, captured[i]);
        bytes.seedInt32(descriptor + 0x20L, 0x89ABCDEF);
        bytes.seedByte(descriptor + 0x28L, 0x80);
        bytes.seedInt64(holder, holderPoison);
        final int[] descriptorBefore = new int[41];
        for (int i = 0; i < descriptorBefore.length; i++) descriptorBefore[i] = bytes.peekUnsignedByte(descriptor + i);
        final List<String> calls = new ArrayList<>();
        final IllegalStateException sentinel = new IllegalStateException("opaque cleanup failure");
        final RequestE92780.Ports ports = new RequestE92780.Ports() {
            @Override public long call4223b94(int ecx) {
                assertEquals(224, ecx);
                assertEquals(List.of(), memory.trace());
                calls.add("allocate");
                return u;
            }
            @Override public void call855f00(long rcx, long rdx) {
                assertEquals(u + 0xB0L, rcx);
                assertEquals(scratch, rdx);
                assertEquals(List.of("allocate"), calls);
                for (int i = 0; i < captured.length; i++) assertEquals(captured[i], bytes.peekInt64(scratch + 8L * i));
                assertEquals(0, bytes.peekInt64(descriptor + 0x10L));
                assertEquals(15, bytes.peekInt64(descriptor + 0x18L));
                assertEquals(0, bytes.peekUnsignedByte(descriptor));
                assertEquals(0x89ABCDEF, bytes.peekInt32(scratch + 0x20L));
                assertEquals(1, bytes.peekUnsignedByte(scratch + 0x28L));
                assertImage(bytes, u, defaultImage(base, u));
                assertEquals(holderPoison, bytes.peekInt64(holder));
                calls.add("transfer");
                bytes.seedInt32(scratch + 0x20L, changedScalar);
                bytes.seedByte(scratch + 0x28L, 0x80);
            }
            @Override public void call856050(long rcx) {
                assertEquals(scratch, rcx);
                assertEquals(List.of("allocate", "transfer"), calls);
                assertEquals(changedScalar, bytes.peekInt32(u + 0xD0L));
                assertEquals(1, bytes.peekUnsignedByte(u + 0xD8L));
                assertEquals(0x80, bytes.peekUnsignedByte(scratch + 0x28L));
                assertEquals(holderPoison, bytes.peekInt64(holder));
                calls.add("cleanup");
                throw sentinel;
            }
        };

        assertSame(sentinel, assertThrows(IllegalStateException.class,
                () -> RequestE92780.initialize(base, holder, descriptor, scratch, memory, ports)));
        final List<Request140TestMemory.Access> actual = memory.trace();

        final List<Request140TestMemory.Access> expected = new ArrayList<>(List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, scratch + 0x28L, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ8, descriptor + 0x28L, 1, 0x80, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ128, descriptor, 16, captured[0], captured[1]),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, scratch, 16, captured[0], captured[1]),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ128, descriptor + 0x10L, 16, captured[2], captured[3]),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, scratch + 0x10L, 16, captured[2], captured[3]),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, descriptor + 0x10L, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, descriptor + 0x18L, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, descriptor, 1, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ32, descriptor + 0x20L, 4, 0x89ABCDEFL, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, scratch + 0x20L, 4, 0x89ABCDEFL, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, scratch + 0x28L, 1, 1, 0)
        ));
        expected.addAll(defaults(base, u));
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.READ8, scratch + 0x28L, 1, 1, 0));
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.READ32, scratch + 0x20L, 4, 0xE2468ACEL, 0));
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.WRITE32, u + 0xD0L, 4, 0xE2468ACEL, 0));
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, u + 0xD8L, 1, 1, 0));
        expected.add(new Request140TestMemory.Access(Request140TestMemory.Op.READ8, scratch + 0x28L, 1, 0x80, 0));
        assertEquals(expected, actual);
        assertEquals(List.of("allocate", "transfer", "cleanup"), calls);
        assertEquals(holderPoison, bytes.peekInt64(holder));
        final int[] expectedU = defaultImage(base, u);
        for (int i = 0; i < 4; i++) expectedU[0xD0 + i] = (changedScalar >>> (8 * i)) & 0xFF;
        expectedU[0xD8] = 1;
        assertImage(bytes, u, expectedU);
        final int[] expectedDescriptor = descriptorBefore.clone();
        for (int i = 0x10; i < 0x20; i++) expectedDescriptor[i] = 0;
        expectedDescriptor[0x18] = 15;
        expectedDescriptor[0] = 0;
        assertImage(bytes, descriptor, expectedDescriptor);
        final int[] expectedScratch = new int[41];
        Arrays.fill(expectedScratch, 0xC7);
        for (int q = 0; q < captured.length; q++) {
            for (int i = 0; i < 8; i++) expectedScratch[q * 8 + i] = (int) (captured[q] >>> (8 * i)) & 0xFF;
        }
        for (int i = 0; i < 4; i++) expectedScratch[0x20 + i] = (changedScalar >>> (8 * i)) & 0xFF;
        expectedScratch[0x28] = 0x80;
        assertImage(bytes, scratch, expectedScratch);
    }
}
