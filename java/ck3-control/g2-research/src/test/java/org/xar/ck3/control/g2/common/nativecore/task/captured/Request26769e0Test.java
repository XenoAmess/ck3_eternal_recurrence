package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory.Op.*;

public final class Request26769e0Test {
    @Test
    public void emptyStringPublishesConcreteInitializedRequestWithoutLookup() {
        Request140TestMemory memory = new Request140TestMemory();
        Idler79eRegressionHost.Memory bytes = memory.bytes();
        long moduleBase = 0x140000000L;
        long output = bytes.allocate(8);
        long descriptor = bytes.allocate(0x29);
        long sourceString = bytes.allocate(0x18);
        long u = bytes.allocate(0xE0);
        Request26769e0.Scratch scratch = new Request26769e0.Scratch(
                bytes.allocate(8), bytes.allocate(8), bytes.allocate(16),
                bytes.allocate(16), bytes.allocate(16), bytes.allocate(0x29));
        for (int offset = 0; offset < 0xE0; offset++) bytes.seedByte(u + offset, 0xA5);
        for (int offset = 0; offset < 0x29; offset++) {
            bytes.seedByte(descriptor + offset, 0xB6);
            bytes.seedByte(scratch.initializerScratch() + offset, 0xC7);
        }
        for (long view : new long[]{scratch.view70(), scratch.view50(), scratch.viewC()}) {
            for (int offset = 0; offset < 16; offset++) bytes.seedByte(view + offset, 0xD8);
        }
        bytes.seedByte(descriptor + 0x28, 0);
        bytes.seedInt64(sourceString + 0x10, 0);
        bytes.seedInt64(output, 0x1111222233334444L);
        List<String> calls = new ArrayList<>();
        RequestE92780.Ports initializer = new RequestE92780.Ports() {
            @Override public long call4223b94(int ecx) {
                assertEquals(0xE0, ecx);
                calls.add("allocate");
                return u;
            }
            @Override public void call855f00(long rcx, long rdx) {
                throw new AssertionError("Unexpected initializer string copy");
            }
            @Override public void call856050(long rcx) {
                throw new AssertionError("Unexpected initializer cleanup");
            }
        };
        Request26769e0.Ports ports = new Request26769e0.Ports() {
            @Override public void call3852500(Request26769e0.Known3852500 known) {
                throw new AssertionError("Unexpected lookup");
            }
            @Override public void call855db0(long rcx, long rdx, long r8) {
                throw new AssertionError("Unexpected producer string copy");
            }
            @Override public void callVirtual0(long target, long rcx, int edx) {
                throw new AssertionError("Unexpected virtual callback");
            }
            @Override public void call856050(long rcx) {
                throw new AssertionError("Unexpected producer cleanup");
            }
        };
        memory.clearTrace();
        assertEquals(output, Request26769e0.create(moduleBase, output, descriptor,
                sourceString, scratch, memory, initializer, ports));
        assertEquals(List.of("allocate"), calls);
        assertEquals(u, bytes.peekInt64(output));
        assertEquals(u, bytes.peekInt64(scratch.initializerHolder()));
        long[][] defaultWrites = {
                {0x08, 2, 0}, {0x0A, 1, 0}, {0x0C, 4, 0}, {0x10, 8, 0},
                {0x18, 8, 0}, {0x20, 1, 0}, {0x28, 8, 0}, {0x38, 8, 0},
                {0x40, 8, 15}, {0x48, 8, 0}, {0x58, 8, 0}, {0x60, 8, 15},
                {0x68, 2, 0}, {0x6A, 1, 0}, {0x00, 8, moduleBase + 0x44FC2A8L},
                {0x70, 8, 0}, {0x80, 8, 0}, {0x88, 8, 15}, {0x70, 1, 0},
                {0x90, 4, 0}, {0x94, 4, 0x029C77F8L}, {0x98, 8, -1L},
                {0xA0, 1, 3}, {0xA4, 4, 0xFFFFFFFFL}, {0xA8, 2, 0x100}, {0xD8, 1, 0}
        };
        byte[] expected = new byte[0xE0];
        Arrays.fill(expected, (byte) 0xA5);
        List<Request140TestMemory.Access> expectedWrites = new ArrayList<>();
        expectedWrites.add(new Request140TestMemory.Access(WRITE8,
                scratch.initializerScratch() + 0x28, 1, 0, 0));
        for (long[] write : defaultWrites) {
            int offset = (int) write[0];
            int width = (int) write[1];
            long value = write[2];
            Request140TestMemory.Op op = switch (width) {
                case 1 -> WRITE8;
                case 2 -> WRITE16;
                case 4 -> WRITE32;
                case 8 -> WRITE64;
                default -> throw new AssertionError("Unexpected expected width");
            };
            expectedWrites.add(new Request140TestMemory.Access(op, u + offset, width, value, 0));
            for (int index = 0; index < width; index++) {
                expected[offset + index] = (byte) (value >>> (index * 8));
            }
        }
        expectedWrites.add(new Request140TestMemory.Access(WRITE64,
                scratch.initializerHolder(), 8, u, 0));
        expectedWrites.add(new Request140TestMemory.Access(WRITE8, u + 0xA9, 1, 1, 0));
        expectedWrites.add(new Request140TestMemory.Access(WRITE64, output, 8, u, 0));
        expected[0xA9] = 1;
        assertEquals(expectedWrites, memory.trace().stream()
                .filter(access -> access.op() == WRITE8 || access.op() == WRITE16
                        || access.op() == WRITE32 || access.op() == WRITE64
                        || access.op() == WRITE128).toList());
        for (int offset = 0; offset < expected.length; offset++) {
            assertEquals(expected[offset] & 0xFF, bytes.peekUnsignedByte(u + offset), "U byte " + offset);
        }
        for (int offset = 0; offset < 0x29; offset++) {
            assertEquals(offset == 0x28 ? 0 : 0xB6,
                    bytes.peekUnsignedByte(descriptor + offset), "descriptor byte " + offset);
            assertEquals(offset == 0x28 ? 0 : 0xC7,
                    bytes.peekUnsignedByte(scratch.initializerScratch() + offset), "scratch byte " + offset);
        }
        for (long view : new long[]{scratch.view70(), scratch.view50(), scratch.viewC()}) {
            for (int offset = 0; offset < 16; offset++) assertEquals(0xD8, bytes.peekUnsignedByte(view + offset));
        }
        assertEquals(List.of(new Request140TestMemory.Access(READ64,
                sourceString + 0x10, 8, 0, 0)), memory.trace().stream()
                .filter(access -> access.address() >= sourceString
                        && access.address() < sourceString + 0x18).toList());
        assertEquals(2L, memory.trace().stream().filter(access ->
                access.op() == READ8 && access.address() == descriptor + 0x28).count());
    }

    @Test
    public void sourceViewsAndPostCopyHolderReloadControlPublicationAndCleanup() {
        for (boolean indirect : new boolean[]{false, true}) {
            Request140TestMemory memory = new Request140TestMemory();
            Idler79eRegressionHost.Memory bytes = memory.bytes();
            long moduleBase = 0x140000000L;
            long global = moduleBase + 0x5CB87F8L;
            bytes.map(global, 8);
            long output = bytes.allocate(8);
            long descriptor = bytes.allocate(0x29);
            long sourceString = bytes.allocate(0x20);
            long sourceData = bytes.allocate(8);
            long root = bytes.allocate(0x1C8);
            long receiver = bytes.allocate(0x90);
            long data50 = bytes.allocate(8);
            long p1 = bytes.allocate(0x178);
            long p2 = bytes.allocate(0x178);
            long p1CopyData = bytes.allocate(8);
            long vtable1 = bytes.allocate(8);
            long vtable2 = bytes.allocate(8);
            long target1 = 0x1111222233334444L;
            long target2 = 0x5555666677778888L;
            long u = bytes.allocate(0xE0);
            Request26769e0.Scratch scratch = new Request26769e0.Scratch(
                    bytes.allocate(8), bytes.allocate(8), bytes.allocate(16),
                    bytes.allocate(16), bytes.allocate(16), bytes.allocate(0x29));
            for (int offset = 0; offset < 0xE0; offset++) bytes.seedByte(u + offset, 0xA5);
            for (long view : new long[]{scratch.view70(), scratch.view50(), scratch.viewC()}) {
                for (int offset = 0; offset < 16; offset++) bytes.seedByte(view + offset, 0xC7);
            }
            bytes.seedInt64(output, 0x3333444455556666L);
            bytes.seedByte(descriptor + 0x28, 0);
            bytes.seedInt64(global, root);
            bytes.seedInt64(root + 0x1C0, receiver);
            bytes.seedInt64(sourceString, sourceData);
            bytes.seedInt64(sourceString + 0x10, 0x180000005L);
            bytes.seedInt64(sourceString + 0x18, indirect ? Long.MIN_VALUE : 15);
            bytes.seedInt64(receiver + 0x70, 0xDEAD000011112222L);
            bytes.seedInt32(receiver + 0x80, 0x89ABCDEF);
            bytes.seedInt64(receiver + 0x88, 15);
            bytes.seedInt64(receiver + 0x50, data50);
            bytes.seedInt32(receiver + 0x60, 0x12345678);
            bytes.seedInt64(receiver + 0x68, Long.MIN_VALUE);
            bytes.seedInt64(p1, vtable1);
            bytes.seedInt64(vtable1, target1);
            bytes.seedInt64(p2, vtable2);
            bytes.seedInt64(vtable2, target2);
            bytes.seedByte(p1 + 0x170, 0);
            bytes.seedByte(p2 + 0x170, 0x80);
            bytes.seedInt64(p1 + 0x140, p1CopyData);
            bytes.seedInt64(p1 + 0x150, 0x100000007L);
            bytes.seedInt64(p1 + 0x158, indirect ? Long.MIN_VALUE : 15);
            List<String> calls = new ArrayList<>();
            RequestE92780.Ports initializer = new RequestE92780.Ports() {
                @Override public long call4223b94(int ecx) {
                    assertEquals(0xE0, ecx);
                    calls.add("allocate");
                    return u;
                }
                @Override public void call855f00(long rcx, long rdx) {
                    throw new AssertionError("Unexpected initializer string copy");
                }
                @Override public void call856050(long rcx) {
                    throw new AssertionError("Unexpected initializer cleanup");
                }
            };
            Request26769e0.Ports ports = new Request26769e0.Ports() {
                @Override public void call3852500(Request26769e0.Known3852500 known) {
                    calls.add("lookup");
                    assertEquals(new Request26769e0.Known3852500(receiver,
                            scratch.lookupHolder(), scratch.viewC(), scratch.view50(), scratch.view70()), known);
                    assertEquals(indirect ? sourceData : sourceString, bytes.peekInt64(scratch.viewC()));
                    assertEquals(0x80000005, bytes.peekInt32(scratch.viewC() + 8));
                    assertEquals(receiver + 0x70, bytes.peekInt64(scratch.view70()));
                    assertEquals(0x89ABCDEF, bytes.peekInt32(scratch.view70() + 8));
                    assertEquals(data50, bytes.peekInt64(scratch.view50()));
                    assertEquals(0x12345678, bytes.peekInt32(scratch.view50() + 8));
                    for (long view : new long[]{scratch.view70(), scratch.view50(), scratch.viewC()}) {
                        assertEquals(0, bytes.peekUnsignedByte(view + 12));
                        for (int offset = 13; offset < 16; offset++) assertEquals(0xC7, bytes.peekUnsignedByte(view + offset));
                    }
                    List<Request140TestMemory.Access> expectedViewWrites = List.of(
                            new Request140TestMemory.Access(WRITE64, scratch.viewC(), 8, indirect ? sourceData : sourceString, 0),
                            new Request140TestMemory.Access(WRITE32, scratch.viewC() + 8, 4, 0x80000005L, 0),
                            new Request140TestMemory.Access(WRITE8, scratch.viewC() + 12, 1, 0, 0),
                            new Request140TestMemory.Access(WRITE64, scratch.view70(), 8, receiver + 0x70, 0),
                            new Request140TestMemory.Access(WRITE32, scratch.view70() + 8, 4, 0x89ABCDEFL, 0),
                            new Request140TestMemory.Access(WRITE8, scratch.view70() + 12, 1, 0, 0),
                            new Request140TestMemory.Access(WRITE64, scratch.view50(), 8, data50, 0),
                            new Request140TestMemory.Access(WRITE32, scratch.view50() + 8, 4, 0x12345678L, 0),
                            new Request140TestMemory.Access(WRITE8, scratch.view50() + 12, 1, 0, 0));
                    assertEquals(expectedViewWrites, memory.trace().stream().filter(access ->
                            (access.address() >= scratch.viewC() && access.address() < scratch.viewC() + 16)
                            || (access.address() >= scratch.view70() && access.address() < scratch.view70() + 16)
                            || (access.address() >= scratch.view50() && access.address() < scratch.view50() + 16)).toList());
                    assertTrue(memory.trace().contains(new Request140TestMemory.Access(
                            READ64, sourceString + 0x10, 8, 0x180000005L, 0)));
                    assertTrue(memory.trace().contains(new Request140TestMemory.Access(
                            READ32, receiver + 0x80, 4, 0x89ABCDEFL, 0)));
                    assertTrue(memory.trace().contains(new Request140TestMemory.Access(
                            READ32, receiver + 0x60, 4, 0x12345678L, 0)));
                    assertEquals(indirect ? 1L : 0L, memory.trace().stream().filter(access ->
                            access.op() == READ64 && access.address() == sourceString).count());
                    assertEquals(0L, memory.trace().stream().filter(access ->
                            access.op() == READ64 && access.address() == receiver + 0x70).count());
                    bytes.seedInt64(scratch.lookupHolder(), p1);
                }
                @Override public void call855db0(long rcx, long rdx, long r8) {
                    calls.add("copy");
                    assertEquals(u + 0x70, rcx);
                    assertEquals(indirect ? p1CopyData : p1 + 0x140, rdx);
                    assertEquals(0x100000007L, r8);
                    assertEquals(0x3333444455556666L, bytes.peekInt64(output));
                    bytes.seedInt64(scratch.lookupHolder(), p2);
                }
                @Override public void callVirtual0(long target, long rcx, int edx) {
                    calls.add("virtual");
                    assertEquals(target2, target);
                    assertEquals(p2, rcx);
                    assertEquals(1, edx);
                    assertEquals(u, bytes.peekInt64(output));
                    assertEquals(1, bytes.peekInt32(u + 0x90));
                    bytes.seedByte(descriptor + 0x28, 1);
                }
                @Override public void call856050(long rcx) {
                    calls.add("cleanup");
                    assertEquals(descriptor, rcx);
                    assertEquals(u, bytes.peekInt64(output));
                }
            };
            memory.clearTrace();
            assertEquals(output, Request26769e0.create(moduleBase, output, descriptor,
                    sourceString, scratch, memory, initializer, ports));
            assertEquals(List.of("allocate", "lookup", "copy", "virtual", "cleanup"), calls);
            assertEquals(u, bytes.peekInt64(output));
            assertEquals(u, bytes.peekInt64(scratch.initializerHolder()));
            assertEquals(1, bytes.peekInt32(u + 0x90));
            assertEquals(1, bytes.peekUnsignedByte(u + 0xA9));
            assertEquals(p2, bytes.peekInt64(scratch.lookupHolder()));
            assertTrue(memory.trace().contains(new Request140TestMemory.Access(READ8, p2 + 0x170, 1, 0x80, 0)));
            assertFalse(memory.trace().stream().anyMatch(access -> access.address() == p1 + 0x170));
            assertEquals(new Request140TestMemory.Access(READ8, descriptor + 0x28, 1, 1, 0),
                    memory.trace().get(memory.trace().size() - 1));
        }
    }
}
